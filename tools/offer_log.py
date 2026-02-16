"""
Log offers to the Offers_Log tab in the Master Catalog.

Usage:
    from tools.offer_log import log_offer, update_offer_status
"""

from datetime import date

from tools.sheets_api import append_sheet, delete_rows, read_sheet, write_sheet

MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"
OFFERS_LOG_TAB = "Offers_Log"


def log_offer(
    offer_number: str,
    mode: str,
    customer: dict,
    result: dict,
    spreadsheet_url: str,
    pdf_url: str,
) -> None:
    """Append an offer entry to the Offers_Log tab."""
    row = [
        offer_number,
        mode,
        customer.get("customer_id", ""),
        customer.get("company_name", ""),
        date.today().strftime("%Y-%m-%d"),
        f"{result.get('subtotal_excl_vat', 0):.2f}",
        f"{result.get('grand_total_incl_vat', 0):.2f}",
        spreadsheet_url,
        pdf_url,
        "draft",   # initial status
        "",         # order_number (empty until converted)
    ]
    append_sheet(MASTER_CATALOG_ID, f"'{OFFERS_LOG_TAB}'!A:K", [row])


def update_offer_status(offer_number: str, status: str, order_number: str = "") -> bool:
    """Update the status of an offer in the Offers_Log.

    Returns True if the offer was found and updated.
    """
    rows = read_sheet(MASTER_CATALOG_ID, f"'{OFFERS_LOG_TAB}'!A:K")
    if not rows or len(rows) < 2:
        return False

    for i, row in enumerate(rows[1:], start=2):  # 1-based, skip header
        if row and row[0] == offer_number:
            # Update status (col J = index 10 in 1-based = col K)
            write_sheet(MASTER_CATALOG_ID, f"'{OFFERS_LOG_TAB}'!J{i}", [[status]])
            if order_number:
                write_sheet(MASTER_CATALOG_ID, f"'{OFFERS_LOG_TAB}'!K{i}", [[order_number]])
            return True

    return False


def delete_offer(offer_number: str) -> bool:
    """Delete an offer from the Offers_Log by offer number.

    Returns True if the offer was found and deleted.
    """
    rows = read_sheet(MASTER_CATALOG_ID, f"'{OFFERS_LOG_TAB}'!A:K")
    if not rows or len(rows) < 2:
        return False

    for i, row in enumerate(rows[1:], start=1):  # 0-indexed for delete_rows (skip header)
        if row and row[0] == offer_number:
            delete_rows(MASTER_CATALOG_ID, OFFERS_LOG_TAB, i, i + 1)
            return True
    return False


def delete_order(order_number: str) -> bool:
    """Delete an order from the Orders tab by order number.

    Returns True if the order was found and deleted.
    """
    rows = read_sheet(MASTER_CATALOG_ID, "'Orders'!A:O")
    if not rows or len(rows) < 2:
        return False

    for i, row in enumerate(rows[1:], start=1):  # 0-indexed for delete_rows (skip header)
        if row and row[0] == order_number:
            delete_rows(MASTER_CATALOG_ID, "Orders", i, i + 1)
            return True
    return False


def get_offer_log() -> list[dict]:
    """Read all offers from the Offers_Log as a list of dicts."""
    rows = read_sheet(MASTER_CATALOG_ID, f"'{OFFERS_LOG_TAB}'!A:K")
    if not rows or len(rows) < 2:
        return []

    headers = rows[0]
    offers = []
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        row += [""] * (len(headers) - len(row))
        offers.append(dict(zip(headers, row)))
    return offers
