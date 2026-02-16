"""
One-time setup: create new tabs in the Master Catalog for Phase 3.

Creates:
  - Offers_Log: chronological record of all generated offers
  - Orders: order tracking with full lifecycle
  - Delivery_Terms: predefined delivery options
  - Payment_Terms: predefined payment options
  - Logistics: product packaging/measure units

Also adds sales_agent_sap_code to Company_Branding.

Usage:
    python -m tools.setup_phase3_tabs
"""

import io
import sys

from tools.google_auth import get_sheets_service
from tools.sheets_api import read_sheet, write_sheet, append_sheet

if "streamlit" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"


def _get_existing_tabs(service) -> set[str]:
    """Get all existing tab names."""
    meta = service.spreadsheets().get(spreadsheetId=MASTER_CATALOG_ID).execute()
    return {s["properties"]["title"] for s in meta.get("sheets", [])}


def _create_tab(service, title: str):
    """Create a new tab if it doesn't exist."""
    service.spreadsheets().batchUpdate(
        spreadsheetId=MASTER_CATALOG_ID,
        body={"requests": [{
            "addSheet": {"properties": {"title": title}}
        }]},
    ).execute()


def setup_offers_log(service, existing_tabs: set[str]):
    """Create and populate Offers_Log tab."""
    tab = "Offers_Log"
    if tab in existing_tabs:
        print(f"  {tab} already exists, skipping creation")
        return

    _create_tab(service, tab)
    headers = [
        "offer_number", "mode", "customer_id", "customer_name",
        "created_date", "total_excl_vat", "total_incl_vat",
        "spreadsheet_url", "pdf_url", "status", "order_number",
    ]
    write_sheet(MASTER_CATALOG_ID, f"'{tab}'!A1", [headers])
    print(f"  Created {tab} with headers")


def setup_orders(service, existing_tabs: set[str]):
    """Create and populate Orders tab."""
    tab = "Orders"
    if tab in existing_tabs:
        print(f"  {tab} already exists, skipping creation")
        return

    _create_tab(service, tab)
    headers = [
        "order_number", "offer_number", "sales_agent_code",
        "customer_id", "customer_name",
        "created_date", "delivery_date",
        "delivery_terms", "payment_terms",
        "total_excl_vat", "total_incl_vat",
        "status", "submitted_date", "notes", "spreadsheet_url",
    ]
    write_sheet(MASTER_CATALOG_ID, f"'{tab}'!A1", [headers])
    print(f"  Created {tab} with headers")


def setup_delivery_terms(service, existing_tabs: set[str]):
    """Create and populate Delivery_Terms tab with common options."""
    tab = "Delivery_Terms"
    if tab in existing_tabs:
        print(f"  {tab} already exists, skipping creation")
        return

    _create_tab(service, tab)
    data = [
        ["term_id", "name_bg", "name_en", "description"],
        ["DEL-001", "До обект (на адрес)", "Door delivery", "Доставка до адрес на клиента"],
        ["DEL-002", "EXW (от склад)", "EXW (ex-works)", "Клиентът взима стоката от нашия склад"],
        ["DEL-003", "FCA (франко превозвач)", "FCA (free carrier)", "Стоката се предава на превозвача"],
        ["DEL-004", "DAP (до обект, без разтоварване)", "DAP (delivered at place)", "Доставка до обект без разтоварване"],
        ["DEL-005", "DDP (доставено, мито платено)", "DDP (delivered duty paid)", "Пълна доставка включително мито"],
    ]
    write_sheet(MASTER_CATALOG_ID, f"'{tab}'!A1", data)
    print(f"  Created {tab} with {len(data) - 1} terms")


def setup_payment_terms(service, existing_tabs: set[str]):
    """Create and populate Payment_Terms tab with common options."""
    tab = "Payment_Terms"
    if tab in existing_tabs:
        print(f"  {tab} already exists, skipping creation")
        return

    _create_tab(service, tab)
    data = [
        ["term_id", "name_bg", "name_en", "description"],
        ["PAY-001", "Банков превод 14 дни", "Bank transfer 14 days", "Плащане по банков път до 14 дни от фактура"],
        ["PAY-002", "Банков превод 30 дни", "Bank transfer 30 days", "Плащане по банков път до 30 дни от фактура"],
        ["PAY-003", "Банков превод 60 дни", "Bank transfer 60 days", "Плащане по банков път до 60 дни от фактура"],
        ["PAY-004", "Авансово плащане", "Prepayment", "100% предплата преди доставка"],
        ["PAY-005", "50% аванс + 50% при доставка", "50% advance + 50% on delivery", "Половин предплата, половин при получаване"],
        ["PAY-006", "При доставка (наложен платеж)", "Cash on delivery", "Плащане при получаване на стоката"],
        ["PAY-007", "Кредитна линия", "Credit line", "Съгласно договорена кредитна линия"],
    ]
    write_sheet(MASTER_CATALOG_ID, f"'{tab}'!A1", data)
    print(f"  Created {tab} with {len(data) - 1} terms")


def setup_logistics(service, existing_tabs: set[str]):
    """Create Logistics tab (headers only — data comes from Excel import)."""
    tab = "Logistics"
    if tab in existing_tabs:
        print(f"  {tab} already exists, skipping creation")
        return

    _create_tab(service, tab)
    headers = [
        "product_code", "measure_unit", "pcs_per_unit",
        "weight_kg", "dimensions",
    ]
    write_sheet(MASTER_CATALOG_ID, f"'{tab}'!A1", [headers])
    print(f"  Created {tab} with headers (populate via import_logistics.py)")


def add_branding_keys(service):
    """Add new branding keys if they don't exist."""
    rows = read_sheet(MASTER_CATALOG_ID, "'Company_Branding'!A:B")
    existing_keys = {row[0] for row in rows if row}

    new_keys = [
        ["sales_agent_sap_code", "12104"],
        ["cs_email", "orders@romstal.bg"],
        ["next_order_number", "0"],
    ]

    to_add = [row for row in new_keys if row[0] not in existing_keys]
    if to_add:
        append_sheet(MASTER_CATALOG_ID, "'Company_Branding'!A:B", to_add)
        print(f"  Added {len(to_add)} new branding keys: {[r[0] for r in to_add]}")
    else:
        print("  All branding keys already exist")


def main():
    print("=== Phase 3: Setting up new sheet tabs ===\n")
    service = get_sheets_service()
    existing = _get_existing_tabs(service)
    print(f"Existing tabs: {sorted(existing)}\n")

    setup_offers_log(service, existing)
    setup_orders(service, existing)
    setup_delivery_terms(service, existing)
    setup_payment_terms(service, existing)
    setup_logistics(service, existing)

    print()
    add_branding_keys(service)

    print("\nDone! New tabs ready in Master Catalog.")


if __name__ == "__main__":
    main()
