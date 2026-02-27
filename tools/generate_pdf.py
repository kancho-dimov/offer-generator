"""
PDF generation for offers, pricelists, and orders.

Uses fpdf2 with DejaVu Sans (Cyrillic support) to produce PDF files directly
from offer/order data. This bypasses Google Sheets PDF export entirely, which
has a known limitation: =IMAGE() formulas (logo, product thumbnails) do not
render in PDF exports of freshly created sheets.

The generated PDF is saved to .tmp/{number}_offer.pdf and the path is stored
in the offer's _data.json file for pickup by Streamlit and email sender.

Usage:
    from tools.generate_pdf import build_offer_pdf, build_order_pdf
    pdf_path = build_offer_pdf(offer_number, mode, customer, branding, request, result)
"""

from __future__ import annotations

import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path

from fpdf import FPDF

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve().parent.parent
FONT_DIR = _HERE / "resources" / "fonts"
LOGO_PATH = _HERE / "resources" / "logo_bg.png"
TMP_DIR = _HERE / ".tmp"

# ---------------------------------------------------------------------------
# Brand colors (RGB)
# ---------------------------------------------------------------------------

BRAND_BLUE = (0, 134, 206)       # #0086CE
LIGHT_BLUE = (227, 245, 255)     # #E3F5FF
WHITE = (255, 255, 255)
DARK_TEXT = (34, 34, 34)         # #222222
DARK_GREY = (100, 100, 100)
HIGHLIGHT = (255, 248, 204)      # yellow highlight for grand total row
TABLE_BORDER = (180, 210, 230)

IMG_COL_W = 14   # mm — product thumbnail column width
ROW_H = 12       # mm — minimum row height
LINE_H = 4.5     # mm — line height inside multi_cell
HEADER_H = 6     # mm — table header row height


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

def _fetch_image_bytes(url: str, timeout: float = 4.0) -> bytes | None:
    """Download an image URL. Returns None on any failure."""
    if not url or not url.startswith("http"):
        return None
    try:
        import httpx
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
        if resp.status_code == 200 and len(resp.content) > 200:
            return resp.content
    except Exception:
        pass
    return None


def _prefetch_images(lines: list[dict]) -> dict[str, bytes]:
    """Download all product image URLs concurrently. Returns {url: bytes}."""
    urls = [line.get("image_url", "") for line in lines if line.get("image_url")]
    unique_urls = list({u for u in urls if u and u.startswith("http")})
    if not unique_urls:
        return {}

    results: dict[str, bytes] = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        future_map = {ex.submit(_fetch_image_bytes, url): url for url in unique_urls}
        for future in as_completed(future_map, timeout=20):
            url = future_map[future]
            try:
                data = future.result()
                if data:
                    results[url] = data
            except Exception:
                pass
    return results


# ---------------------------------------------------------------------------
# Base PDF class
# ---------------------------------------------------------------------------

class _RomstalPDF(FPDF):
    """Shared PDF base with Romstal branding and fonts."""

    def __init__(self, orientation: str = "L"):
        super().__init__(orientation=orientation, unit="mm", format="A4")
        self.set_margins(left=10, top=10, right=10)
        self.set_auto_page_break(auto=True, margin=12)
        self._load_fonts()

    def _load_fonts(self):
        regular = FONT_DIR / "DejaVuSans.ttf"
        bold = FONT_DIR / "DejaVuSans-Bold.ttf"
        if regular.exists():
            self.add_font("DejaVu", fname=str(regular))
        if bold.exists():
            self.add_font("DejaVu", style="B", fname=str(bold))
        self._font = "DejaVu" if regular.exists() else "Helvetica"

    def _set(self, size: int = 9, bold: bool = False, color: tuple = DARK_TEXT):
        style = "B" if bold else ""
        self.set_font(self._font, style=style, size=size)
        self.set_text_color(*color)

    def _draw_header(self, branding: dict):
        """Company name left, logo top right, address/contact rows below."""
        page_w = self.w - 20  # usable width

        # Logo
        if LOGO_PATH.exists():
            logo_w = 55
            logo_h = 14  # logo is 3.87:1 ratio → 55mm wide = 14mm tall
            logo_x = self.w - 10 - logo_w
            self.image(str(LOGO_PATH), x=logo_x, y=10, w=logo_w)
        else:
            logo_h = 0

        # Company name
        self._set(size=14, bold=True, color=BRAND_BLUE)
        self.set_xy(10, 10)
        name_w = page_w - 60  # leave room for logo
        self.cell(name_w, 7, branding.get("company_name", ""), ln=False)

        # Address / phone / VAT (below company name)
        self._set(size=8, color=DARK_GREY)
        self.set_xy(10, 18)
        self.cell(name_w, 4, branding.get("company_address", ""), ln=True)

        phone = branding.get("company_phone", "")
        email = branding.get("company_email", "")
        website = branding.get("company_website", "")
        self._set(size=8, color=DARK_GREY)
        self.set_xy(10, 22)
        self.cell(name_w, 4, f"Тел: {phone}  |  Email: {email}  |  {website}", ln=True)

        self._set(size=8, color=DARK_GREY)
        self.set_xy(10, 26)
        self.cell(name_w, 4, f"ЕИК/ДДС: {branding.get('company_vat_id', '')}", ln=False)

        # Separator line
        y = max(10 + logo_h + 2, 31)
        self.set_draw_color(*BRAND_BLUE)
        self.set_line_width(0.5)
        self.line(10, y, self.w - 10, y)
        self.set_y(y + 2)
        return y + 2  # return Y after header

    def _draw_offer_meta(self, offer_number: str, request: dict, mode: str) -> float:
        """Offer number / date / validity row."""
        validity = request.get("validity_days", 30)
        today_str = date.today().strftime("%d.%m.%Y")
        valid_until = (date.today() + timedelta(days=validity)).strftime("%d.%m.%Y")
        label = "Оферта" if "OFR" in offer_number else "Ценова листа"
        text = f"{label} №: {offer_number}    |    Дата: {today_str}    |    Валидна до: {valid_until}"
        self._set(size=10, bold=True, color=BRAND_BLUE)
        self.cell(0, 6, text, ln=True)
        self.ln(2)
        return self.get_y()

    def _draw_order_meta(self, order_number: str, offer_number: str, request: dict) -> float:
        """Order number / date / references row."""
        today_str = date.today().strftime("%d.%m.%Y")
        text = f"Поръчка №: {order_number}    |    Дата: {today_str}"
        if offer_number:
            text += f"    |    Към оферта: {offer_number}"
        self._set(size=10, bold=True, color=BRAND_BLUE)
        self.cell(0, 6, text, ln=True)
        self.ln(2)
        return self.get_y()

    def _draw_customer(self, customer: dict, request: dict) -> float:
        """Customer info block."""
        self._set(size=9, color=DARK_TEXT)
        rows = [
            f"Клиент:  {customer.get('company_name', '')}",
            f"Лице за контакт:  {customer.get('contact_name', '')}",
            f"Адрес:  {customer.get('address', '')}",
            f"Тел/Email:  {customer.get('phone', '')}  |  {customer.get('email', '')}",
        ]
        notes = request.get("notes", "")
        if notes:
            rows.append(f"Бележки:  {notes}")
        for row in rows:
            self.cell(0, 5, row, ln=True)
        self.ln(3)
        return self.get_y()

    def _draw_footer(self, branding: dict):
        """Terms and footer at the bottom of the last page."""
        self.ln(4)
        self.set_draw_color(*BRAND_BLUE)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(2)
        self._set(size=7, color=DARK_GREY)
        terms = branding.get("offer_terms", "")
        if terms:
            self.multi_cell(0, 4, terms)
            self.ln(1)
        disclaimer = branding.get("offer_disclaimer", "")
        if disclaimer:
            self.multi_cell(0, 4, disclaimer)
            self.ln(1)
        footer = branding.get("offer_footer", "")
        if footer:
            self.multi_cell(0, 4, footer)

    def _draw_table_header(self, headers: list[str], col_w: list[int]):
        """Draw a table header row with auto-wrapping text (blue background, white text)."""
        self._set(size=8, bold=True, color=WHITE)

        # Measure each header to get uniform row height
        header_h = HEADER_H
        for h, w in zip(headers, col_w):
            hh = self.multi_cell(w, LINE_H, h, dry_run=True, output="HEIGHT")
            header_h = max(header_h, hh)

        y0 = self.get_y()
        x = self.get_x()
        for h, w in zip(headers, col_w):
            # Draw uniform background + border rectangle
            self.set_fill_color(*BRAND_BLUE)
            self.set_draw_color(*TABLE_BORDER)
            self.set_line_width(0.1)
            self.rect(x, y0, w, header_h, style="FD")
            # Overlay wrapped text (no border/fill — rectangle already drawn)
            self.set_xy(x, y0)
            self._set(size=8, bold=True, color=WHITE)
            self.multi_cell(w, LINE_H, h, border=0, align="C", fill=False,
                            new_x="RIGHT", new_y="TOP")
            x += w

        self.set_y(y0 + header_h)

    def _draw_row_image(self, img_bytes: bytes | None, x: float, y: float):
        """Embed a product thumbnail at absolute (x, y) position within the image cell."""
        if not img_bytes:
            return
        try:
            self.image(
                io.BytesIO(img_bytes),
                x=x + 1,
                y=y + 1,
                w=IMG_COL_W - 2,
                h=ROW_H - 2,
                keep_aspect_ratio=True,
            )
        except Exception:
            pass  # Skip broken images silently


# ---------------------------------------------------------------------------
# Offer / Pricelist PDF
# ---------------------------------------------------------------------------

def build_offer_pdf(
    offer_number: str,
    mode: str,
    customer: dict,
    branding: dict,
    request: dict,
    result: dict,
) -> Path:
    """
    Generate an offer or pricelist PDF with product thumbnail images.

    Args:
        result: output from calculate_offer_lines() with 'lines' key

    Returns:
        Path to the generated PDF file in .tmp/
    """
    is_landscape = (mode == "offer")
    orientation = "L" if is_landscape else "P"
    show_discount = request.get("show_discount", False)
    show_vat = request.get("show_vat", True) and mode != "offer"

    pdf = _RomstalPDF(orientation=orientation)
    pdf.add_page()

    # ── Header ──────────────────────────────────────────────────────────────
    pdf._draw_header(branding)
    pdf._draw_offer_meta(offer_number, request, mode)
    pdf._draw_customer(customer, request)

    # ── Table ───────────────────────────────────────────────────────────────
    page_w = pdf.w - 20  # usable width

    if mode == "offer":
        if show_discount:
            col_w = [IMG_COL_W, 6, 23, 0, 25, 10, 24, 15, 34, 34]
            headers = ["Фото", "#", "Код", "Наименование", "Марка", "К-во",
                       "Ед. цена EUR", "Отстъпка %", "Нето EUR (без ДДС)", "Общо EUR (без ДДС)"]
        else:
            col_w = [IMG_COL_W, 6, 23, 0, 25, 10, 40, 40]
            headers = ["Фото", "#", "Код", "Наименование", "Марка", "К-во",
                       "Нето EUR (без ДДС)", "Общо EUR (без ДДС)"]
    else:  # pricelist
        if show_discount:
            col_w = [IMG_COL_W, 5, 20, 0, 22, 24, 20, 12, 24, 24]
            headers = ["Фото", "#", "Код", "Наименование", "Марка", "Категория",
                       "Ед. цена EUR", "Отстъпка %", "Нето EUR (без ДДС)", "Нето EUR (с ДДС)"]
        else:
            col_w = [IMG_COL_W, 6, 22, 0, 25, 30, 30, 30]
            headers = ["Фото", "#", "Код", "Наименование", "Марка", "Категория",
                       "Нето EUR (без ДДС)", "Нето EUR (с ДДС)"]

    # Name column (index 3) fills remaining space
    fixed_w = sum(w for i, w in enumerate(col_w) if i != 3)
    col_w[3] = max(25, page_w - fixed_w)

    NAME_COL = 3
    align_map = ["C", "R", "L", "L", "L", "C", "R", "R", "R", "R"]

    lines = result.get("lines", [])

    # Pre-fetch all product images concurrently before drawing
    img_cache = _prefetch_images(lines)

    # Table header
    pdf._draw_table_header(headers, col_w)

    # Table rows
    for idx, line in enumerate(lines, 1):
        # Ensure row fits on current page
        if pdf.get_y() + ROW_H > pdf.h - pdf.b_margin:
            pdf.add_page()
            pdf._draw_table_header(headers, col_w)

        if "error" in line:
            pdf.set_fill_color(*WHITE)
            pdf._set(size=8, color=(180, 0, 0))
            pdf.cell(sum(col_w), ROW_H,
                     f"{line['product_code']}: ГРЕШКА — {line['error']}",
                     border=1, ln=True)
            continue

        fill = (idx % 2 == 0)

        y_row = pdf.get_y()
        x_row = pdf.get_x()

        # Build row values (image cell is first — placeholder, image drawn below)
        if mode == "offer":
            if show_discount:
                row_vals = [
                    "",  # image placeholder
                    str(idx),
                    line["product_code"],
                    line["name"],
                    line["brand"],
                    str(line["quantity"]),
                    f"{line['base_price']:.2f}",
                    f"{line['total_discount_pct']:.1f}%",
                    f"{line['net_price_excl_vat']:.2f}",
                    f"{line['line_total_excl_vat']:.2f}",
                ]
            else:
                row_vals = [
                    "",
                    str(idx),
                    line["product_code"],
                    line["name"],
                    line["brand"],
                    str(line["quantity"]),
                    f"{line['net_price_excl_vat']:.2f}",
                    f"{line['line_total_excl_vat']:.2f}",
                ]
        else:  # pricelist
            if show_discount:
                row_vals = [
                    "",
                    str(idx),
                    line["product_code"],
                    line["name"],
                    line["brand"],
                    line.get("category", ""),
                    f"{line['base_price']:.2f}",
                    f"{line['total_discount_pct']:.1f}%",
                    f"{line['net_price_excl_vat']:.2f}",
                    f"{line['net_price_incl_vat']:.2f}",
                ]
            else:
                row_vals = [
                    "",
                    str(idx),
                    line["product_code"],
                    line["name"],
                    line["brand"],
                    line.get("category", ""),
                    f"{line['net_price_excl_vat']:.2f}",
                    f"{line['net_price_incl_vat']:.2f}",
                ]

        _draw_data_row(
            pdf, row_vals, col_w, align_map, fill,
            NAME_COL, line.get("image_url", ""), img_cache,
            wrap_cols={4, 5} if mode != "offer" else {4},
        )

    # ── Totals (offer mode only) ─────────────────────────────────────────────
    if mode == "offer":
        label_w = sum(col_w[:-2]) if len(col_w) >= 2 else sum(col_w) - 40
        val_w = col_w[-2] if len(col_w) >= 2 else 40
        grand_w = col_w[-1] if len(col_w) >= 1 else 40

        pdf.ln(2)
        sub = result.get("subtotal_excl_vat", 0)
        vat = result.get("total_vat", 0)
        grand = result.get("grand_total_incl_vat", 0)

        for label, val, highlight in [
            ("Междинна сума (без ДДС):", f"{sub:.2f} EUR", False),
            ("ДДС (20%):", f"{vat:.2f} EUR", False),
            ("ОБЩА СУМА (с ДДС):", f"{grand:.2f} EUR", True),
        ]:
            if highlight:
                pdf.set_fill_color(*HIGHLIGHT)
            else:
                pdf.set_fill_color(*WHITE)
            pdf._set(size=9, bold=highlight, color=DARK_TEXT)
            pdf.cell(label_w + val_w, ROW_H + 1, label, border=1, align="R", fill=True)
            pdf._set(size=9, bold=True, color=DARK_TEXT)
            pdf.cell(grand_w, ROW_H + 1, val, border=1, align="R", fill=True)
            pdf.ln()

    # ── Footer ──────────────────────────────────────────────────────────────
    pdf._draw_footer(branding)

    # ── Save ────────────────────────────────────────────────────────────────
    TMP_DIR.mkdir(exist_ok=True)
    pdf_path = TMP_DIR / f"{offer_number.replace('/', '-')}_offer.pdf"
    pdf.output(str(pdf_path))
    return pdf_path


# ---------------------------------------------------------------------------
# Order PDF
# ---------------------------------------------------------------------------

def build_order_pdf(
    order_number: str,
    offer_number: str,
    customer: dict,
    branding: dict,
    request: dict,
    result: dict,
    logistics: dict,
) -> Path:
    """
    Generate an order PDF (landscape A4) with product thumbnail images.

    Returns:
        Path to the generated PDF file in .tmp/
    """
    pdf = _RomstalPDF(orientation="L")
    pdf.add_page()

    # ── Header ──────────────────────────────────────────────────────────────
    pdf._draw_header(branding)
    pdf._draw_order_meta(order_number, offer_number, request)

    # Two-column customer / order info
    page_w = pdf.w - 20
    half = page_w / 2

    delivery_addr = request.get("delivery_address", customer.get("delivery_address", customer.get("address", "")))
    delivery_date = request.get("delivery_date", "")
    delivery_terms = request.get("delivery_terms", "")
    payment_terms = request.get("payment_terms", "")
    notes = request.get("notes", "")
    sales_agent = request.get("sales_agent_code", branding.get("sales_agent_sap_code", "12104"))

    left_rows = [
        f"Клиент:  {customer.get('company_name', '')}",
        f"Лице за контакт:  {customer.get('contact_name', '')}",
        f"Адрес на доставка:  {delivery_addr}",
        f"Тел/Email:  {customer.get('phone', '')}  |  {customer.get('email', '')}",
    ]
    right_rows = [
        f"Търговец (SAP):  {sales_agent}",
        f"Дата на доставка:  {delivery_date}",
        f"Условия доставка:  {delivery_terms}",
        f"Условия плащане:  {payment_terms}",
    ]
    if notes:
        left_rows.append(f"Бележки:  {notes}")

    pdf._set(size=9, color=DARK_TEXT)
    start_y = pdf.get_y()
    max_rows = max(len(left_rows), len(right_rows))
    for i in range(max_rows):
        if i < len(left_rows):
            pdf.set_xy(10, start_y + i * 5)
            pdf.cell(half - 5, 5, left_rows[i])
        if i < len(right_rows):
            pdf.set_xy(10 + half, start_y + i * 5)
            pdf.cell(half, 5, right_rows[i])
    pdf.set_y(start_y + max_rows * 5 + 3)

    # ── Order Table ─────────────────────────────────────────────────────────
    col_w = [IMG_COL_W, 6, 23, 0, 10, 12, 35, 35]
    headers = ["Фото", "#", "Код", "Наименование", "К-во", "МЕ",
               "Нето EUR (без ДДС)", "Общо EUR (без ДДС)"]

    # Name column (index 3) fills remaining space
    fixed_w = sum(w for i, w in enumerate(col_w) if i != 3)
    col_w[3] = max(25, page_w - fixed_w)

    align_map = ["C", "R", "L", "L", "C", "C", "R", "R"]
    NAME_COL = 3

    lines = result.get("lines", [])
    items_config = {item["product_code"]: item for item in request.get("items", [])}

    # Pre-fetch all product images concurrently
    img_cache = _prefetch_images(lines)

    # Table header
    pdf._draw_table_header(headers, col_w)

    total_excl = 0.0
    total_incl = 0.0

    for idx, line in enumerate(lines, 1):
        # Ensure row fits on current page
        if pdf.get_y() + ROW_H > pdf.h - pdf.b_margin:
            pdf.add_page()
            pdf._draw_table_header(headers, col_w)

        if "error" in line:
            pdf.set_fill_color(*WHITE)
            pdf._set(size=8, color=(180, 0, 0))
            pdf.cell(sum(col_w), ROW_H,
                     f"{line['product_code']}: ГРЕШКА — {line['error']}",
                     border=1, ln=True)
            continue

        fill = (idx % 2 == 0)

        y_row = pdf.get_y()
        x_row = pdf.get_x()

        item_cfg = items_config.get(line["product_code"], {})
        unit = item_cfg.get("measure_unit", "pcs")
        quantity = item_cfg.get("quantity", line.get("quantity", 1))
        pcs_per_unit = int(logistics.get(line["product_code"], {}).get("pcs_per_carton", 1) or 1)
        if pcs_per_unit < 1:
            pcs_per_unit = 1
        total_pcs = quantity * pcs_per_unit if unit == "carton" else quantity
        net_excl = line["net_price_excl_vat"]
        line_total_excl = net_excl * total_pcs
        line_total_incl = line_total_excl * 1.2
        total_excl += line_total_excl
        total_incl += line_total_incl

        measure_label = "кашон" if unit == "carton" else "бр."
        row_vals = [
            "",  # image placeholder
            str(idx),
            line["product_code"],
            line["name"],
            str(quantity),
            measure_label,
            f"{net_excl:.2f}",
            f"{line_total_excl:.2f}",
        ]

        _draw_data_row(
            pdf, row_vals, col_w, align_map, fill,
            NAME_COL, line.get("image_url", ""), img_cache,
        )

    # ── Totals ──────────────────────────────────────────────────────────────
    label_w = sum(col_w[:-2])
    val_w = col_w[-2]
    grand_w = col_w[-1]

    pdf.ln(2)
    vat_amount = total_incl - total_excl
    for label, val, highlight in [
        ("Междинна сума (без ДДС):", f"{total_excl:.2f} EUR", False),
        ("ДДС (20%):", f"{vat_amount:.2f} EUR", False),
        ("ОБЩА СУМА (с ДДС):", f"{total_incl:.2f} EUR", True),
    ]:
        pdf.set_fill_color(*HIGHLIGHT if highlight else WHITE)
        pdf._set(size=9, bold=highlight, color=DARK_TEXT)
        pdf.cell(label_w + val_w, ROW_H + 1, label, border=1, align="R", fill=True)
        pdf._set(size=9, bold=True, color=DARK_TEXT)
        pdf.cell(grand_w, ROW_H + 1, val, border=1, align="R", fill=True)
        pdf.ln()

    # ── Footer ──────────────────────────────────────────────────────────────
    pdf._draw_footer(branding)

    # ── Save ────────────────────────────────────────────────────────────────
    TMP_DIR.mkdir(exist_ok=True)
    pdf_path = TMP_DIR / f"{order_number.replace('/', '-')}_order.pdf"
    pdf.output(str(pdf_path))
    return pdf_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _truncate(pdf: FPDF, text: str, max_w: float) -> str:
    """Truncate text to fit within max_w mm (adds ellipsis if needed)."""
    if not text:
        return ""
    while pdf.get_string_width(text) > max_w and len(text) > 1:
        text = text[:-1]
    if pdf.get_string_width(text + "…") > max_w and len(text) > 2:
        text = text[:-2] + "…"
    return text


def _draw_data_row(
    pdf: "_RomstalPDF",
    row_vals: list[str],
    col_w: list[int],
    align_map: list[str],
    fill: bool,
    name_col: int,
    img_url: str,
    img_cache: dict,
    wrap_cols: set[int] | None = None,
) -> None:
    """Draw one table data row.

    Columns in wrap_cols (plus name_col) use multi_cell (word-wrap).
    All other columns use cell() with truncation.
    Row height expands automatically to fit the tallest wrapped column.
    """
    effective_wrap = (wrap_cols or set()) | {name_col}

    bg = LIGHT_BLUE if fill else WHITE
    y_row = pdf.get_y()
    x_row = pdf.get_x()

    pdf.set_fill_color(*bg)
    pdf._set(size=8, color=DARK_TEXT)

    # Calculate required row height from all wrapping columns (dry run — no output)
    row_h = ROW_H
    for i in effective_wrap:
        if i < len(row_vals) and i < len(col_w):
            h = pdf.multi_cell(col_w[i], LINE_H, row_vals[i], dry_run=True, output="HEIGHT")
            row_h = max(row_h, h + 1)

    # Draw all non-wrap cells with fixed row_h
    x = x_row
    for i, (val, w) in enumerate(zip(row_vals, col_w)):
        if i in effective_wrap:
            x += w
            continue
        a = align_map[i] if i < len(align_map) else "L"
        display = _truncate(pdf, val, w - 1) if val else ""
        pdf.set_xy(x, y_row)
        pdf.cell(w, row_h, display, border=1, align=a, fill=fill)
        x += w

    # Draw wrap columns with multi_cell (in column order, using absolute positioning)
    for i in sorted(effective_wrap):
        if i >= len(row_vals) or i >= len(col_w):
            continue
        pdf.set_xy(x_row + sum(col_w[:i]), y_row)
        pdf.set_fill_color(*bg)
        pdf._set(size=8, color=DARK_TEXT)
        pdf.multi_cell(
            col_w[i], LINE_H, row_vals[i],
            border=1, fill=fill, align="L",
            new_x="RIGHT", new_y="TOP",
        )

    # Advance cursor past the row
    pdf.set_y(y_row + row_h)

    # Embed product thumbnail at the image cell position
    if img_url:
        pdf._draw_row_image(img_cache.get(img_url), x=x_row, y=y_row)
