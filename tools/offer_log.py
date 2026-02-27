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
    version: int = 1,
    base_id: str = "",
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
        "draft",              # J: initial status
        "",                   # K: order_number (empty until converted)
        str(version),         # L: version number
        base_id or offer_number,  # M: base document ID
    ]
    append_sheet(MASTER_CATALOG_ID, f"'{OFFERS_LOG_TAB}'!A:M", [row])


def update_offer_log_row(
    offer_number: str,
    result: dict,
    spreadsheet_url: str,
    pdf_url: str,
) -> bool:
    """Overwrite the mutable fields of an existing draft offer row in-place.

    Updates date, totals, spreadsheet_url, pdf_url.
    Returns True if the offer was found and updated.
    """
    rows = read_sheet(MASTER_CATALOG_ID, f"'{OFFERS_LOG_TAB}'!A:A")
    if not rows or len(rows) < 2:
        return False

    for i, row in enumerate(rows[1:], start=2):  # 1-based, skip header
        if row and row[0] == offer_number:
            updated = [
                date.today().strftime("%Y-%m-%d"),           # E
                f"{result.get('subtotal_excl_vat', 0):.2f}", # F
                f"{result.get('grand_total_incl_vat', 0):.2f}", # G
                spreadsheet_url,                              # H
                pdf_url,                                      # I
            ]
            write_sheet(MASTER_CATALOG_ID, f"'{OFFERS_LOG_TAB}'!E{i}:I{i}", [updated])
            return True

    return False


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
    rows = read_sheet(MASTER_CATALOG_ID, f"'{OFFERS_LOG_TAB}'!A:M")
    if not rows or len(rows) < 2:
        return []

    headers = rows[0]
    offers = []
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        # Pad to at least 13 cols so legacy rows (A:K only) don't crash
        row = list(row) + [""] * (13 - len(row))
        d = dict(zip(headers, row[: len(headers)]))
        # Normalize version to int; legacy rows without the column default to 1
        try:
            d["version"] = int(d.get("version") or 1)
        except (ValueError, TypeError):
            d["version"] = 1
        # Normalize base_id; legacy rows default to the offer_number itself
        if not d.get("base_id"):
            d["base_id"] = d.get("offer_number", "")
        offers.append(d)
    return offers
