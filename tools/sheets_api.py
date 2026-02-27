"""
Google Sheets read/write utility.

Usage:
    from tools.sheets_api import read_sheet, write_sheet, get_sheet_names
"""

from tools.google_auth import get_drive_service, get_sheets_service


def get_sheet_names(spreadsheet_id: str) -> list[str]:
    """Get all sheet/tab names in a spreadsheet."""
    service = get_sheets_service()
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    return [s["properties"]["title"] for s in meta.get("sheets", [])]


def read_sheet(spreadsheet_id: str, range_name: str) -> list[list[str]]:
    """
    Read data from a Google Sheet.

    Args:
        spreadsheet_id: The Google Sheet ID
        range_name: Sheet range like "Sheet1!A1:Z" or just "Sheet1"

    Returns:
        List of rows, where each row is a list of cell values.
    """
    service = get_sheets_service()
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_name)
        .execute()
    )
    return result.get("values", [])


def write_sheet(
    spreadsheet_id: str,
    range_name: str,
    values: list[list],
    input_option: str = "RAW",
) -> dict:
    """
    Write data to a Google Sheet.

    Args:
        spreadsheet_id: The Google Sheet ID
        range_name: Sheet range like "Sheet1!A1"
        values: List of rows to write
        input_option: "RAW" (default, safe) or "USER_ENTERED" (for formulas)

    Returns:
        API response dict.
    """
    service = get_sheets_service()
    body = {"values": values}
    result = (
        service.spreadsheets()
        .values()
        .update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption=input_option,
            body=body,
        )
        .execute()
    )
    return result


def append_sheet(
    spreadsheet_id: str,
    range_name: str,
    values: list[list],
    input_option: str = "RAW",
) -> dict:
    """
    Append rows to a Google Sheet (adds after existing data).

    Args:
        spreadsheet_id: The Google Sheet ID
        range_name: Sheet range like "Sheet1!A1"
        values: List of rows to append
        input_option: "RAW" (default, safe) or "USER_ENTERED" (for formulas)

    Returns:
        API response dict.
    """
    service = get_sheets_service()
    body = {"values": values}
    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption=input_option,
            body=body,
        )
        .execute()
    )
    return result


def delete_rows(spreadsheet_id: str, sheet_name: str, start_row: int, end_row: int) -> dict:
    """Delete rows from a Google Sheet (0-indexed, exclusive end).

    Args:
        spreadsheet_id: The Google Sheet ID
        sheet_name: Tab name, e.g. "Customers"
        start_row: First row to delete (0-indexed, so row 2 in UI = 1 here)
        end_row: Row after last to delete (exclusive)
    """
    service = get_sheets_service()
    # Look up sheetId by name
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_id = None
    for s in meta.get("sheets", []):
        if s["properties"]["title"] == sheet_name:
            sheet_id = s["properties"]["sheetId"]
            break
    if sheet_id is None:
        raise ValueError(f"Sheet '{sheet_name}' not found")

    request = {
        "requests": [
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": start_row,
                        "endIndex": end_row,
                    }
                }
            }
        ]
    }
    return service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body=request
    ).execute()


def delete_spreadsheet(spreadsheet_id: str) -> None:
    """Permanently delete a Google Spreadsheet file from Drive."""
    drive = get_drive_service()
    drive.files().delete(fileId=spreadsheet_id).execute()


def clear_sheet(spreadsheet_id: str, range_name: str) -> dict:
    """Clear a range in a Google Sheet."""
    service = get_sheets_service()
    return (
        service.spreadsheets()
        .values()
        .clear(spreadsheetId=spreadsheet_id, range=range_name, body={})
        .execute()
    )


if __name__ == "__main__":
    # Quick test: list sheet names from the master catalog
    MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"
    print("Sheet names in Master Catalog:")
    for name in get_sheet_names(MASTER_CATALOG_ID):
        print(f"  - {name}")
