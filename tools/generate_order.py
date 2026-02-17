"""
Order generation tool — creates a professional Google Sheet for a customer order.

Two entry modes:
  - "from_offer": Convert an existing offer to an order (inherits products + discounts)
  - "standalone": Create an order from scratch (select customer + products)

Orders include:
  - Sales Agent SAP Code
  - Delivery terms, payment terms, delivery date
  - Measure unit per line (pcs or carton) with automatic pcs conversion
  - Line-level discounts (always visible for customer service)

Usage:
    python -m tools.generate_order                    # reads .tmp/order_request.json
"""

import io
import json
import sys
from datetime import date, datetime
from pathlib import Path

from tools.discount_engine import (
    calculate_offer_lines,
    load_customer,
    load_discount_rules,
    load_products,
)
from tools.format_offer_sheet import format_offer_sheet
from tools.generate_offer import _group_and_hide_columns
from tools.google_auth import get_sheets_service
from tools.offer_log import update_offer_status
from tools.sheets_api import append_sheet, read_sheet, write_sheet

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"
TMP_DIR = Path(__file__).resolve().parent.parent / ".tmp"


# ---------------------------------------------------------------------------
# Order numbering
# ---------------------------------------------------------------------------

def _get_next_order_number() -> str:
    """Generate the next order number like ORD-2026-001."""
    rows = read_sheet(MASTER_CATALOG_ID, "'Company_Branding'!A:C")
    row_idx = None
    current = 0
    for i, row in enumerate(rows):
        if row and row[0] == "next_order_number":
            row_idx = i
            current = int(row[1]) if len(row) > 1 and row[1] else 0
            break

    next_val = current + 1
    if row_idx is not None:
        write_sheet(MASTER_CATALOG_ID, f"'Company_Branding'!B{row_idx + 1}", [[str(next_val)]])

    year = date.today().year
    return f"ORD-{year}-{next_val:03d}"


# ---------------------------------------------------------------------------
# Load reference data
# ---------------------------------------------------------------------------

def load_delivery_terms() -> list[dict]:
    """Read delivery terms from the Delivery_Terms tab."""
    rows = read_sheet(MASTER_CATALOG_ID, "'Delivery_Terms'!A:D")
    if not rows or len(rows) < 2:
        return []
    headers = rows[0]
    return [dict(zip(headers, r + [""] * (len(headers) - len(r)))) for r in rows[1:] if r]


def load_payment_terms() -> list[dict]:
    """Read payment terms from the Payment_Terms tab."""
    rows = read_sheet(MASTER_CATALOG_ID, "'Payment_Terms'!A:D")
    if not rows or len(rows) < 2:
        return []
    headers = rows[0]
    return [dict(zip(headers, r + [""] * (len(headers) - len(r)))) for r in rows[1:] if r]


def load_logistics_for_codes(codes: list[str]) -> dict[str, dict]:
    """Load logistics data for specific product codes. Returns dict keyed by product_code."""
    rows = read_sheet(MASTER_CATALOG_ID, "'Logistics'!A:G")
    if not rows or len(rows) < 2:
        return {}
    headers = rows[0]
    result = {}
    code_set = set(codes)
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        code = str(row[0]).strip()
        if code in code_set:
            row += [""] * (len(headers) - len(row))
            result[code] = dict(zip(headers, row))
    return result


def load_branding() -> dict:
    """Read Company_Branding as key-value dict."""
    rows = read_sheet(MASTER_CATALOG_ID, "'Company_Branding'!A:B")
    return {row[0]: row[1] for row in rows[1:] if row and len(row) >= 2}


# ---------------------------------------------------------------------------
# Sheet creation
# ---------------------------------------------------------------------------

def _create_spreadsheet(service, title: str) -> str:
    """Create a new Google Spreadsheet."""
    body = {
        "properties": {"title": title},
        "sheets": [{"properties": {"title": "Поръчка", "index": 0}}],
    }
    result = service.spreadsheets().create(body=body).execute()
    return result["spreadsheetId"]


def _build_order_header(
    order_number: str,
    offer_number: str,
    customer: dict,
    branding: dict,
    request: dict,
) -> list[list]:
    """Build the header section for the order sheet.

    Uses a compact 2-column layout for customer/order info:
      Left (cols A-F):  Customer details
      Right (cols H-M): Order & delivery details
    """
    num_cols = 13
    mid = 7  # right block starts at column index 7

    # Row 0: company name left, logo right (last 5 cols merged)
    logo_url = branding.get("company_logo_url", "")
    logo_formula = f'=IMAGE("{logo_url}", 4, 60, 232)' if logo_url else ""
    row0 = [branding.get("company_name", "")] + [""] * (num_cols - 6) + [logo_formula]

    sales_agent = request.get("sales_agent_code", branding.get("sales_agent_sap_code", "12104"))
    notes = request.get("notes", "")

    def _two_col(left: str, right: str) -> list:
        """Build a row with text in left block (col 0) and right block (col mid)."""
        row = [""] * num_cols
        row[0] = left
        row[mid] = right
        return row

    rows = [
        # Row 0: Company name + logo
        row0,
        # Row 1: Address
        [branding.get("company_address", "")],
        # Row 2: Phone | Email | Website (prefix with ' to prevent +phone formula error)
        [f"'Тел: {branding.get('company_phone', '')}  |  Email: {branding.get('company_email', '')}  |  {branding.get('company_website', '')}"],
        # Row 3: VAT
        [f"ЕИК/ДДС: {branding.get('company_vat_id', '')}"],
        # Row 4: blank
        [],
        # Row 5: Order number + date + offer ref
        [f"Поръчка №: {order_number}    |    Дата: {date.today().strftime('%d.%m.%Y')}    |    Оферта: {offer_number or 'Без оферта'}"],
        # Row 6: blank
        [],
        # Row 7-12: Two-column layout — customer (left) + order details (right)
        _two_col(f"Клиент:  {customer.get('company_name', '')}",
                 f"Търговски агент SAP:  {sales_agent}"),
        _two_col(f"ЕИК: {customer.get('company_reg_id', '')}  |  ДДС №: {customer.get('vat_number', '')}",
                 f"Условия на доставка:  {request.get('delivery_terms', '')}"),
        _two_col(f"Контакт:  {customer.get('contact_name', '')}  |  Тел: {customer.get('phone', '')}",
                 f"Адрес за доставка:  {request.get('delivery_address') or customer.get('delivery_address') or customer.get('address', 'Не е посочен')}"),
        _two_col(f"Email:  {customer.get('email', '')}  |  SAP №: {customer.get('customer_id', '')}",
                 f"Условия на плащане:  {request.get('payment_terms', '')}"),
        _two_col("",
                 f"Дата на доставка:  {request.get('delivery_date', '')}  |  Бележки:  {notes}" if notes else f"Дата на доставка:  {request.get('delivery_date', '')}"),
        # Row 12: blank before table
        [],
    ]

    return rows


def _build_order_table(result: dict, request: dict, logistics: dict) -> list[list]:
    """Build order line items table with measure unit conversion."""
    header = [
        "#", "Продукт", "Код", "Наименование", "Марка",
        "Мярка", "Бр/Мярка", "К-во", "Общо бр.",
        "Ед. цена EUR", "Отстъпка %",
        "Нето ед. цена EUR\n(без ДДС)",
        "Общо EUR\n(без ДДС)",
    ]

    rows = [header]
    items_config = {item["product_code"]: item for item in request.get("items", [])}

    for i, line in enumerate(result["lines"], 1):
        if "error" in line:
            rows.append([i, "", line["product_code"], f"ГРЕШКА: {line['error']}"])
            continue

        code = line["product_code"]
        item_cfg = items_config.get(code, {})

        # Measure unit: from request or default to pcs
        measure_unit = item_cfg.get("measure_unit", "pcs")
        logi = logistics.get(code, {})
        pcs_per_unit = 1
        if measure_unit == "carton":
            pcs_per_unit = int(logi.get("pcs_per_carton", 1) or 1)
            if pcs_per_unit < 1:
                pcs_per_unit = 1

        qty_units = line["quantity"]  # quantity in measure units
        total_pcs = qty_units * pcs_per_unit

        # Recalculate line totals based on total pcs
        net_excl = line["net_price_excl_vat"]
        net_incl = line["net_price_incl_vat"]
        line_total_excl = round(net_excl * total_pcs, 2)
        line_total_incl = round(net_incl * total_pcs, 2)

        measure_label = "кашон" if measure_unit == "carton" else "бр."

        # Note: =IMAGE() formulas show #REF! until sheet is opened in browser,
        # so we skip product thumbnails for reliable PDF export.
        rows.append([
            i,
            "",  # product image column left empty for PDF reliability
            code,
            line["name"],
            line["brand"],
            measure_label,
            pcs_per_unit,
            qty_units,
            total_pcs,
            line["base_price"],
            f"{line['total_discount_pct']:.1f}%",
            net_excl,
            line_total_excl,
        ])

    return rows


def _build_order_totals(result: dict, request: dict, logistics: dict) -> list[list]:
    """Build totals section, recalculated for measure unit conversion."""
    items_config = {item["product_code"]: item for item in request.get("items", [])}

    subtotal_excl = 0
    total_vat = 0
    for line in result["lines"]:
        if "error" in line:
            continue
        code = line["product_code"]
        item_cfg = items_config.get(code, {})
        measure_unit = item_cfg.get("measure_unit", "pcs")
        logi = logistics.get(code, {})
        pcs_per_unit = 1
        if measure_unit == "carton":
            pcs_per_unit = int(logi.get("pcs_per_carton", 1) or 1)
            if pcs_per_unit < 1:
                pcs_per_unit = 1
        total_pcs = line["quantity"] * pcs_per_unit
        subtotal_excl += line["net_price_excl_vat"] * total_pcs
        total_vat += line["vat_amount"] * total_pcs

    subtotal_excl = round(subtotal_excl, 2)
    total_vat = round(total_vat, 2)
    grand_total = round(subtotal_excl + total_vat, 2)

    # 13 columns, value in col 11 (index 11)
    return [
        [],
        ["Междинна сума (без ДДС):"] + [""] * 10 + [f"{subtotal_excl:.2f} EUR", ""],
        [],
        ["ДДС (20%):"] + [""] * 10 + [f"{total_vat:.2f} EUR", ""],
        [],
        ["ОБЩА СУМА (с ДДС):"] + [""] * 10 + [f"{grand_total:.2f} EUR", ""],
    ]


def _build_order_footer(branding: dict) -> list[list]:
    """Build footer section with order-specific text."""
    return [
        [],
        ["Моля, потвърдете поръчката в рамките на 24 часа."],
        ["При въпроси се свържете с нас на посочените по-горе контакти."],
        [],
        [branding.get("offer_footer", "")],
    ]


def _log_order(
    order_number: str,
    offer_number: str,
    sales_agent_code: str,
    customer: dict,
    delivery_date: str,
    delivery_terms: str,
    payment_terms: str,
    total_excl_vat: float,
    total_incl_vat: float,
    notes: str,
    spreadsheet_url: str,
) -> None:
    """Log order to the Orders tab."""
    row = [
        order_number,
        offer_number,
        sales_agent_code,
        customer.get("customer_id", ""),
        customer.get("company_name", ""),
        date.today().strftime("%Y-%m-%d"),
        delivery_date,
        delivery_terms,
        payment_terms,
        f"{total_excl_vat:.2f}",
        f"{total_incl_vat:.2f}",
        "draft",
        "",  # submitted_date
        notes,
        spreadsheet_url,
    ]
    append_sheet(MASTER_CATALOG_ID, "'Orders'!A:O", [row])


def _get_pdf_url(spreadsheet_id: str, sheet_id: int) -> str:
    """Build direct PDF export URL (landscape for orders)."""
    return (
        f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export"
        f"?format=pdf&portrait=false&size=A4&fitw=true"
        f"&gridlines=false&sheetnames=false&printtitle=false"
        f"&pagenumbers=false&fzr=false&gid={sheet_id}"
        f"&top_margin=0.30&bottom_margin=0.30&left_margin=0.30&right_margin=0.30"
        f"&horizontal_alignment=CENTER"
    )


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def generate_order(request: dict | None = None) -> str:
    """Generate an order from a request dict or .tmp/order_request.json."""
    if request is None:
        request_file = TMP_DIR / "order_request.json"
        if not request_file.exists():
            raise FileNotFoundError(f"No order request at {request_file}")
        with open(request_file, encoding="utf-8") as f:
            request = json.load(f)

    customer_id = request["customer_id"]
    items = request["items"]
    offer_number = request.get("offer_number", "")
    custom_discounts = request.get("custom_discounts", [])

    print(f"Generating order for customer {customer_id}...")

    # Load data
    customer = load_customer(customer_id)
    rules = load_discount_rules()
    codes = [item["product_code"] for item in items]
    products = load_products(codes)
    logistics = load_logistics_for_codes(codes)
    branding = load_branding()

    print(f"  Customer: {customer['company_name']}")
    print(f"  Delivery address: {request.get('delivery_address', '')} / {customer.get('delivery_address', '')} / {customer.get('address', '')}")
    print(f"  Products: {len(products)} found / {len(items)} requested")
    print(f"  Logistics: {len(logistics)} matched")

    # Calculate prices (using pcs quantities for discount engine)
    result = calculate_offer_lines(items, customer, rules, custom_discounts, products)

    # Generate order number
    order_number = _get_next_order_number()
    print(f"  Order number: {order_number}")

    # Build sheet content
    header_rows = _build_order_header(order_number, offer_number, customer, branding, request)
    table_rows = _build_order_table(result, request, logistics)
    totals_rows = _build_order_totals(result, request, logistics)
    footer_rows = _build_order_footer(branding)

    all_rows = header_rows + table_rows + totals_rows + footer_rows

    # Create spreadsheet
    service = get_sheets_service()
    title = f"{order_number} | {customer['company_name']}"
    spreadsheet_id = _create_spreadsheet(service, title)
    print(f"  Created spreadsheet: {title}")

    # Get sheet ID
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_id = meta["sheets"][0]["properties"]["sheetId"]

    # Write data
    write_sheet(spreadsheet_id, "'Поръчка'!A1", all_rows, input_option="USER_ENTERED")
    print(f"  Written {len(all_rows)} rows")

    # Apply formatting (reuse offer formatter with order-specific params)
    # Order has 14 columns: #, Img, Code, Name, Brand, Unit, Pcs/Unit, Qty, TotalPcs,
    #                        UnitPrice, Discount%, NetExcl, TotalExcl, TotalIncl
    order_col_widths = [30, 50, 90, 220, 80, 55, 50, 40, 50, 85, 65, 95, 95]
    format_offer_sheet(
        spreadsheet_id, "offer",
        len(header_rows), len(table_rows), len(totals_rows), len(footer_rows),
        tab_name="Поръчка",
        num_cols_override=13,
        col_widths_override=order_col_widths,
        split_header_col=7,
    )

    # Hide base price (col 9) and discount% (col 10) columns for customer-facing PDF
    # CS can expand these via [+] toggle in the sheet
    _group_and_hide_columns(service, spreadsheet_id, sheet_id, [
        (9, 11, True),  # cols 9-10 (base price + discount%), collapsed
    ])
    print("  Column groups added (base price + discount hidden for customer PDF)")

    # Generate URLs
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
    pdf_url = _get_pdf_url(spreadsheet_id, sheet_id)

    # Calculate actual totals with measure unit conversion
    items_config = {item["product_code"]: item for item in items}
    actual_excl = 0
    actual_vat = 0
    for line in result["lines"]:
        if "error" in line:
            continue
        code = line["product_code"]
        item_cfg = items_config.get(code, {})
        mu = item_cfg.get("measure_unit", "pcs")
        ppc = 1
        if mu == "carton":
            ppc = int(logistics.get(code, {}).get("pcs_per_carton", 1) or 1)
            if ppc < 1:
                ppc = 1
        total_pcs = line["quantity"] * ppc
        actual_excl += line["net_price_excl_vat"] * total_pcs
        actual_vat += line["vat_amount"] * total_pcs

    actual_excl = round(actual_excl, 2)
    actual_incl = round(actual_excl + actual_vat, 2)

    # Log to Orders tab
    sales_agent = request.get("sales_agent_code", branding.get("sales_agent_sap_code", "12104"))
    _log_order(
        order_number, offer_number, sales_agent, customer,
        request.get("delivery_date", ""),
        request.get("delivery_terms", ""),
        request.get("payment_terms", ""),
        actual_excl, actual_incl,
        request.get("notes", ""),
        url,
    )
    print("  Logged to Orders tab")

    # Update offer status if this came from an offer
    if offer_number:
        update_offer_status(offer_number, "converted_to_order", order_number)
        print(f"  Offer {offer_number} marked as converted")

    # Save order data
    TMP_DIR.mkdir(exist_ok=True)
    order_data = {
        "order_number": order_number,
        "offer_number": offer_number,
        "customer": customer,
        "branding": branding,
        "request": request,
        "result": result,
        "spreadsheet_id": spreadsheet_id,
        "spreadsheet_url": url,
        "pdf_url": pdf_url,
        "total_excl_vat": actual_excl,
        "total_incl_vat": actual_incl,
    }
    order_file = TMP_DIR / f"{order_number.replace('/', '-')}_data.json"
    with open(order_file, "w", encoding="utf-8") as f:
        json.dump(order_data, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n  Order ready: {url}")
    print(f"  PDF export (landscape A4): {pdf_url}")

    # Auto-open sheet in browser to trigger IMAGE() formula rendering (needed for PDF export)
    import webbrowser
    webbrowser.open(url)

    return url


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    url = generate_order()
