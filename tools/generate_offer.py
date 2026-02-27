"""
Offer generation tool — creates a professional Google Sheet from an offer request.

Supports two modes:
  - "offer":     Full offer with quantities, line totals, subtotal, VAT, grand total
  - "pricelist": Net unit prices only, no quantities or totals

Visibility flags control which columns are hidden (all data is always present):
  - show_discount: show base price + discount % columns
  - show_vat:      show price-incl-VAT columns
  - discount_level: "line" (per product) or "group" (grouped by brand/category)

Usage:
    python -m tools.generate_offer                    # reads .tmp/offer_request.json
    python -m tools.generate_offer --mode pricelist   # override mode from CLI
"""

from __future__ import annotations

import io
import json
import sys
import threading
from datetime import date, datetime
from pathlib import Path

from tools.discount_engine import (
    calculate_offer_lines,
    load_customer,
    load_discount_rules,
    load_products,
)
from tools.format_offer_sheet import format_offer_sheet
from tools.google_auth import get_sheets_service
from tools.offer_log import log_offer, update_offer_log_row
from tools.sheets_api import delete_spreadsheet, read_sheet, write_sheet

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"
LOGO_URL = "https://cdn.brandfetch.io/idIRQXv6EH/w/2500/h/700/theme/dark/logo.png"
TMP_DIR = Path(__file__).resolve().parent.parent / ".tmp"


# ---------------------------------------------------------------------------
# Offer numbering
# ---------------------------------------------------------------------------

_counter_lock = threading.Lock()


def _get_next_number(service, key: str) -> int:
    """Read and increment a counter stored in Company_Branding sheet (thread-safe)."""
    rows = read_sheet(MASTER_CATALOG_ID, "'Company_Branding'!A:C")
    row_idx = None
    current = 0
    for i, row in enumerate(rows):
        if row and row[0] == key:
            row_idx = i
            current = int(row[1]) if len(row) > 1 and row[1] else 0
            break

    next_val = current + 1

    if row_idx is not None:
        # Update existing row
        write_sheet(MASTER_CATALOG_ID, f"'Company_Branding'!B{row_idx + 1}", [[str(next_val)]])
    else:
        # Append new row
        from tools.sheets_api import append_sheet
        append_sheet(MASTER_CATALOG_ID, "'Company_Branding'!A:C", [[key, str(next_val), "counter"]])

    return next_val


def get_next_offer_number(mode: str) -> str:
    """Generate the next offer/pricelist number like OFR-2026-001 or PL-2026-001."""
    with _counter_lock:
        service = get_sheets_service()
        year = date.today().year
        if mode == "pricelist":
            key = "next_pricelist_number"
            prefix = "PL"
        else:
            key = "next_offer_number"
            prefix = "OFR"
        num = _get_next_number(service, key)
    return f"{prefix}-{year}-{num:03d}"


# ---------------------------------------------------------------------------
# Load branding
# ---------------------------------------------------------------------------

def load_branding() -> dict:
    """Read Company_Branding as a key-value dict."""
    rows = read_sheet(MASTER_CATALOG_ID, "'Company_Branding'!A:B")
    branding = {}
    for row in rows[1:]:  # skip header
        if row and len(row) >= 2:
            branding[row[0]] = row[1]
    return branding


# ---------------------------------------------------------------------------
# Sheet creation
# ---------------------------------------------------------------------------

def _create_spreadsheet(service, title: str) -> str:
    """Create a new Google Spreadsheet and return its ID."""
    body = {
        "properties": {"title": title},
        "sheets": [
            {"properties": {"title": "Offer", "index": 0}},
            {"properties": {"title": "Discount_Detail", "index": 1}},
        ],
    }
    result = service.spreadsheets().create(body=body).execute()
    return result["spreadsheetId"]


def _build_offer_header(offer_number: str, customer: dict, branding: dict, request: dict) -> list[list]:
    """Build the header rows for the offer sheet."""
    today_str = date.today().strftime("%d.%m.%Y")
    validity = request.get("validity_days", 30)
    from datetime import timedelta
    valid_until = (date.today() + timedelta(days=validity)).strftime("%d.%m.%Y")

    label = "Оферта" if "OFR" in offer_number else "Ценова листа"
    mode = request.get("mode", "offer")
    num_cols = 10

    # Row 0: company name left, logo right (last 5 cols merged)
    logo_url = branding.get("company_logo_url", "")
    logo_cell = f'=IMAGE("{logo_url}", 4, 60, 232)' if logo_url else ""
    row0 = [branding.get("company_name", "")] + [""] * (num_cols - 6) + [logo_cell] + [""] * 4

    rows = [
        row0,
        # Row 1: Address (merged across all cols)
        [branding.get("company_address", "")],
        # Row 2: Phone | Email | Website (prefix with ' to prevent +phone formula error)
        [f"'Тел: {branding.get('company_phone', '')}  |  Email: {branding.get('company_email', '')}  |  {branding.get('company_website', '')}"],
        # Row 3: VAT ID (merged)
        [f"ЕИК/ДДС: {branding.get('company_vat_id', '')}"],
        # Row 4: blank separator
        [],
        # Row 5: Offer number + date + validity (merged)
        [f"{label} №: {offer_number}    |    Дата: {today_str}    |    Валидна до: {valid_until}"],
        # Row 6: blank
        [],
        # Customer info (single merged string per row, spans all columns)
        [f"Клиент:  {customer.get('company_name', '')}"],
        [f"Лице за контакт:  {customer.get('contact_name', '')}"],
        [f"Адрес:  {customer.get('address', '')}"],
        [f"Тел/Email:  {customer.get('phone', '')}  |  {customer.get('email', '')}"],
    ]

    notes = request.get("notes", "")
    if notes:
        rows.append([f"Бележки:  {notes}"])

    rows.append([])  # blank row before table
    return rows


def _build_offer_table(result: dict, mode: str, request: dict) -> tuple[list[list], int]:
    """
    Build the line items table rows.

    Returns (rows, table_header_row_index) where table_header_row_index is
    the 0-based index within the returned rows list.
    """
    discount_level = request.get("discount_level", "line")

    if mode == "offer":
        header = [
            "#", "Продукт", "Код", "Наименование", "Марка",
            "К-во", "Ед. цена EUR", "Отстъпка %",
            "Нето ед. цена EUR\n(без ДДС)", "Общо EUR\n(без ДДС)",
        ]
    else:  # pricelist
        header = [
            "#", "Продукт", "Код", "Наименование", "Марка", "Категория",
            "Ед. цена EUR", "Отстъпка %",
            "Нето ед. цена EUR\n(без ДДС)", "Нето ед. цена EUR\n(с ДДС)",
        ]

    def _img(url):
        """Skip =IMAGE() — formulas show #REF! in PDF exports until sheet is opened."""
        return ""

    rows = [header]
    lines = result["lines"]

    if discount_level in ("group", "category"):
        # Group by brand or category
        from collections import OrderedDict
        groups = OrderedDict()
        group_field = "category" if discount_level == "category" else "brand"
        for line in lines:
            if "error" in line:
                groups.setdefault("_errors", []).append(line)
                continue
            key = line.get(group_field, "Други")
            groups.setdefault(key, []).append(line)

        line_num = 0
        for group_name, group_lines in groups.items():
            if group_name == "_errors":
                for line in group_lines:
                    rows.append(["", "", line["product_code"], f"ГРЕШКА: {line['error']}"])
                continue

            avg_discount = sum(l["total_discount_pct"] for l in group_lines) / len(group_lines)
            group_header_text = f"{group_name} — Отстъпка: {avg_discount:.1f}%"
            rows.append(["", "", "", group_header_text] + [""] * (6 if mode == "offer" else 6))

            for line in group_lines:
                line_num += 1
                if mode == "offer":
                    rows.append([
                        line_num,
                        _img(line.get("image_url", "")),
                        line["product_code"],
                        line["name"],
                        line["brand"],
                        line["quantity"],
                        line["base_price"],
                        f"{line['total_discount_pct']:.1f}%",
                        line["net_price_excl_vat"],
                        line["line_total_excl_vat"],
                    ])
                else:
                    rows.append([
                        line_num,
                        _img(line.get("image_url", "")),
                        line["product_code"],
                        line["name"],
                        line["brand"],
                        line.get("category", ""),
                        line["base_price"],
                        f"{line['total_discount_pct']:.1f}%",
                        line["net_price_excl_vat"],
                        line["net_price_incl_vat"],
                    ])
    else:
        # Line-level display
        for i, line in enumerate(lines, 1):
            if "error" in line:
                rows.append([i, "", line["product_code"], f"ГРЕШКА: {line['error']}"])
                continue

            if mode == "offer":
                rows.append([
                    i,
                    _img(line.get("image_url", "")),
                    line["product_code"],
                    line["name"],
                    line["brand"],
                    line["quantity"],
                    line["base_price"],
                    f"{line['total_discount_pct']:.1f}%",
                    line["net_price_excl_vat"],
                    line["line_total_excl_vat"],
                ])
            else:
                rows.append([
                    i,
                    _img(line.get("image_url", "")),
                    line["product_code"],
                    line["name"],
                    line["brand"],
                    line.get("category", ""),
                    line["base_price"],
                    f"{line['total_discount_pct']:.1f}%",
                    line["net_price_excl_vat"],
                    line["net_price_incl_vat"],
                ])

    return rows, 0  # header is always the first row of the table


def _build_offer_totals(result: dict, mode: str) -> list[list]:
    """Build the totals section (offer mode only).

    Totals rows: label in A (merged A-I by formatter), value in J, K empty.
    """
    if mode != "offer":
        return []

    return [
        [],
        ["Междинна сума (без ДДС):"] + [""] * 7 + [f"{result['subtotal_excl_vat']:.2f} EUR", ""],
        [],
        ["ДДС (20%):"] + [""] * 7 + [f"{result['total_vat']:.2f} EUR", ""],
        [],
        ["ОБЩА СУМА (с ДДС):"] + [""] * 7 + [f"{result['grand_total_incl_vat']:.2f} EUR", ""],
    ]


def _build_offer_footer(branding: dict) -> list[list]:
    """Build the terms and footer section."""
    return [
        [],
        ["Условия:"],
        [branding.get("offer_terms", "")],
        [],
        ["Важно:"],
        [branding.get("offer_disclaimer", "")],
        [],
        [branding.get("offer_footer", "")],
    ]


def _build_discount_detail(result: dict) -> list[list]:
    """Build the Discount_Detail tab with full per-item breakdown."""
    header = [
        "Код", "Наименование", "Марка", "К-во",
        "Базова цена", "Приложени отстъпки", "Обща отстъпка %",
        "Нето (без ДДС)", "ДДС", "Нето (с ДДС)",
        "Общо (без ДДС)", "Общо (с ДДС)",
    ]
    rows = [header]
    for line in result["lines"]:
        if "error" in line:
            rows.append([line["product_code"], f"ГРЕШКА: {line['error']}"])
            continue
        discounts_str = " → ".join(
            f"{d['name']} (-{d['pct']}%)" for d in line["discounts_applied"]
        )
        rows.append([
            line["product_code"],
            line["name"],
            line["brand"],
            line["quantity"],
            line["base_price"],
            discounts_str,
            f"{line['total_discount_pct']:.2f}%",
            line["net_price_excl_vat"],
            line["vat_amount"],
            line["net_price_incl_vat"],
            line["line_total_excl_vat"],
            line["line_total_incl_vat"],
        ])
    return rows


def _group_and_hide_columns(
    service, spreadsheet_id: str, sheet_id: int,
    groups: list[tuple[int, int, bool]],
):
    """
    Create column groups with clickable [+]/[-] toggles.

    Args:
        groups: list of (start_col, end_col_exclusive, collapsed) tuples.
                Collapsed groups show a [+] button to expand.
    """
    if not groups:
        return

    requests = []
    for start, end, collapsed in groups:
        # Create the group
        requests.append({
            "addDimensionGroup": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": start,
                    "endIndex": end,
                },
            }
        })
        # If collapsed, hide the columns so the group shows [+] toggle
        if collapsed:
            for col in range(start, end):
                requests.append({
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": col,
                            "endIndex": col + 1,
                        },
                        "properties": {"hiddenByUser": True},
                        "fields": "hiddenByUser",
                    }
                })

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests},
    ).execute()


def _hide_sheet(service, spreadsheet_id: str, sheet_id: int):
    """Hide a sheet tab."""
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [{
            "updateSheetProperties": {
                "properties": {"sheetId": sheet_id, "hidden": True},
                "fields": "hidden",
            }
        }]},
    ).execute()


def _get_column_groups(mode: str, request: dict) -> list[tuple[int, int, bool]]:
    """
    Build column groups with clickable [+]/[-] toggles.

    Returns list of (start_col, end_col_exclusive, collapsed) tuples.
    Groups allow users to expand/collapse columns with a single click.
    """
    show_discount = request.get("show_discount", False)
    show_vat = request.get("show_vat", True)

    groups = []

    if mode == "offer":
        # Cols: 0=#, 1=Img, 2=Code, 3=Name, 4=Brand, 5=Qty, 6=BasePrice, 7=Discount%,
        #       8=NetExcl, 9=TotalExcl

        # Discount group (cols 6-7): collapsed unless show_discount
        groups.append((6, 8, not show_discount))

    else:  # pricelist
        # Cols: 0=#, 1=Img, 2=Code, 3=Name, 4=Brand, 5=Category, 6=BasePrice, 7=Discount%,
        #       8=NetExcl, 9=NetIncl

        # Discount group (cols 6-7): collapsed unless show_discount
        groups.append((6, 8, not show_discount))
        # VAT column (col 9): collapsed unless show_vat
        groups.append((9, 10, not show_vat))

    return groups


# ---------------------------------------------------------------------------
# PDF export URL
# ---------------------------------------------------------------------------

def _get_pdf_url(spreadsheet_id: str, sheet_id: int, mode: str) -> str:
    """Build a direct PDF export URL with proper page settings."""
    portrait = "true" if mode == "pricelist" else "false"
    return (
        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export"
        f"?format=pdf&portrait={portrait}&size=A4&fitw=true"
        f"&gridlines=false&sheetnames=false&printtitle=false"
        f"&pagenumbers=false&fzr=false&gid={sheet_id}"
        f"&top_margin=0.30&bottom_margin=0.30&left_margin=0.30&right_margin=0.30"
        f"&horizontal_alignment=CENTER"
    )



# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def generate_offer(request: dict | None = None) -> dict:
    """
    Generate an offer from a request dict or .tmp/offer_request.json.

    Returns a dict with keys: url, offer_number, spreadsheet_id, pdf_url.

    Edit context (optional keys in request):
      editing_offer_number   — existing offer ID being edited
      editing_spreadsheet_id — old spreadsheet to delete (draft overwrite only)
      editing_status         — "draft" | "sent" (determines overwrite vs revision)
      editing_base_id        — base_id to carry forward for revisions
      editing_version        — current version number (revision will increment)
    """
    # Load request
    if request is None:
        request_file = TMP_DIR / "offer_request.json"
        if not request_file.exists():
            raise FileNotFoundError(f"No offer request found at {request_file}")
        with open(request_file, encoding="utf-8") as f:
            request = json.load(f)

    mode = request.get("mode", "offer")
    customer_id = request["customer_id"]
    items = request["items"]
    custom_discounts = request.get("custom_discounts", [])

    # Extract edit context
    editing_offer_number = request.get("editing_offer_number")
    editing_spreadsheet_id = request.get("editing_spreadsheet_id")
    editing_status = request.get("editing_status", "draft")
    editing_base_id = request.get("editing_base_id", "")
    editing_version = int(request.get("editing_version") or 1)

    print(f"Generating {mode} for customer {customer_id}...")

    # Load data
    customer = load_customer(customer_id)
    rules = load_discount_rules()
    codes = [item["product_code"] for item in items]
    products = load_products(codes)

    print(f"  Customer: {customer['company_name']}")
    print(f"  Products: {len(products)} found / {len(items)} requested")
    print(f"  Rules: {len(rules)} loaded")

    # Calculate prices
    result = calculate_offer_lines(items, customer, rules, custom_discounts, products)

    # Determine offer number and versioning
    if not editing_offer_number:
        # Fresh creation
        offer_number = get_next_offer_number(mode)
        version = 1
        base_id = offer_number
    elif editing_status == "draft":
        # Draft overwrite — reuse same ID, no new version
        offer_number = editing_offer_number
        version = 1
        base_id = editing_base_id or editing_offer_number
    else:
        # Post-send revision — new ID, incremented version, same base_id
        offer_number = get_next_offer_number(mode)
        version = editing_version + 1
        base_id = editing_base_id or editing_offer_number
    print(f"  Offer number: {offer_number} (v{version})")

    # Load branding
    branding = load_branding()

    # Build sheet content
    header_rows = _build_offer_header(offer_number, customer, branding, request)
    table_rows, _ = _build_offer_table(result, mode, request)
    totals_rows = _build_offer_totals(result, mode)
    footer_rows = _build_offer_footer(branding)

    all_rows = header_rows + table_rows + totals_rows + footer_rows

    # Build discount detail tab
    detail_rows = _build_discount_detail(result)

    # Create the spreadsheet
    service = get_sheets_service()
    title = f"{offer_number} | {customer['company_name']}"
    spreadsheet_id = _create_spreadsheet(service, title)
    print(f"  Created spreadsheet: {title}")

    # Rename first sheet based on mode
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = meta["sheets"]
    main_sheet_id = sheets[0]["properties"]["sheetId"]
    detail_sheet_id = sheets[1]["properties"]["sheetId"]

    tab_name = "Оферта" if mode == "offer" else "Ценова листа"
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [{
            "updateSheetProperties": {
                "properties": {"sheetId": main_sheet_id, "title": tab_name},
                "fields": "title",
            }
        }]},
    ).execute()

    # Write data
    write_sheet(spreadsheet_id, f"'{tab_name}'!A1", all_rows, input_option="USER_ENTERED")
    write_sheet(spreadsheet_id, "'Discount_Detail'!A1", detail_rows)
    print(f"  Written {len(all_rows)} rows to {tab_name}")
    print(f"  Written {len(detail_rows)} rows to Discount_Detail")

    # Column groups with [+]/[-] toggle buttons
    col_groups = _get_column_groups(mode, request)
    if col_groups:
        _group_and_hide_columns(service, spreadsheet_id, main_sheet_id, col_groups)
        collapsed = [f"{s}-{e-1}" for s, e, c in col_groups if c]
        if collapsed:
            print(f"  Grouped columns (collapsed): {collapsed}")

    # Hide discount detail tab by default
    _hide_sheet(service, spreadsheet_id, detail_sheet_id)
    print("  Discount_Detail tab hidden (unhide for internal review)")

    # Apply professional formatting
    header_row_count = len(header_rows)
    table_row_count = len(table_rows)
    totals_row_count = len(totals_rows)
    footer_row_count = len(footer_rows)
    format_offer_sheet(
        spreadsheet_id, mode,
        header_row_count, table_row_count, totals_row_count, footer_row_count,
    )

    # Generate URLs
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    pdf_url = _get_pdf_url(spreadsheet_id, main_sheet_id, mode)

    # Generate standalone PDF (logo + full formatting, no Google Sheets renderer)
    from tools.generate_pdf import build_offer_pdf
    try:
        pdf_path = build_offer_pdf(offer_number, mode, customer, branding, request, result)
        print(f"  PDF generated: {pdf_path.name} ({pdf_path.stat().st_size // 1024} KB)")
    except Exception as e:
        print(f"  Warning: PDF generation failed: {e}")
        pdf_path = None

    # Delete old draft spreadsheet before logging the new one
    if editing_offer_number and editing_status == "draft" and editing_spreadsheet_id:
        try:
            delete_spreadsheet(editing_spreadsheet_id)
            print(f"  Deleted old draft spreadsheet: {editing_spreadsheet_id}")
        except Exception as e:
            print(f"  Warning: could not delete old draft sheet: {e}")

    # Log to Offers_Log tab
    if editing_offer_number and editing_status == "draft":
        update_offer_log_row(offer_number, result, url, pdf_url)
    else:
        log_offer(offer_number, mode, customer, result, url, pdf_url, version=version, base_id=base_id)
    print("  Logged to Offers_Log")

    # Save offer data for downstream exports (slides, gamma)
    offer_data = {
        "offer_number": offer_number,
        "mode": mode,
        "customer": customer,
        "branding": branding,
        "request": request,
        "result": result,
        "spreadsheet_id": spreadsheet_id,
        "pdf_url": pdf_url,
        "pdf_path": str(pdf_path) if pdf_path else "",
    }
    TMP_DIR.mkdir(exist_ok=True)
    offer_file = TMP_DIR / f"{offer_number.replace('/', '-')}_data.json"
    with open(offer_file, "w", encoding="utf-8") as f:
        json.dump(offer_data, f, ensure_ascii=False, indent=2, default=str)

    orientation = "portrait" if mode == "pricelist" else "landscape"
    print(f"\n  Offer ready: {url}")
    print(f"  PDF export ({orientation} A4): {pdf_url}")

    return {
        "url": url,
        "offer_number": offer_number,
        "spreadsheet_id": spreadsheet_id,
        "pdf_url": pdf_url,
        "version": version,
        "base_id": base_id,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate offer from request JSON")
    parser.add_argument("--mode", choices=["offer", "pricelist"], help="Override mode")
    args = parser.parse_args()

    request_file = TMP_DIR / "offer_request.json"
    if request_file.exists():
        with open(request_file, encoding="utf-8") as f:
            req = json.load(f)
        if args.mode:
            req["mode"] = args.mode
    else:
        req = None

    url = generate_offer(req)
