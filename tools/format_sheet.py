"""
Formats the Master_Database sheet for readability:
- Header row: bold, dark green background, white text, frozen
- Alternating row colors (white / light grey)
- Auto-filter on all columns
- Column widths optimized for content type
- Text wrapping enabled
- Remove any manual fill colors from data cells

Usage:
    python -m tools.format_sheet
"""

import sys
from tools.google_auth import get_sheets_service

MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"


def get_sheet_id(service, spreadsheet_id: str, tab_name: str) -> int:
    """Get the numeric sheetId for a given tab name."""
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in meta.get("sheets", []):
        if sheet["properties"]["title"] == tab_name:
            return sheet["properties"]["sheetId"]
    raise ValueError(f"Sheet '{tab_name}' not found")


def format_master_database():
    """Apply professional formatting to the Master_Database sheet."""
    service = get_sheets_service()
    sheet_id = get_sheet_id(service, MASTER_CATALOG_ID, "Master_Database")

    # Get actual row/column count from sheet metadata
    meta = service.spreadsheets().get(spreadsheetId=MASTER_CATALOG_ID).execute()
    grid_props = None
    for sheet in meta.get("sheets", []):
        if sheet["properties"]["sheetId"] == sheet_id:
            grid_props = sheet["properties"]["gridProperties"]
            break
    total_rows = grid_props["rowCount"] if grid_props else 100
    total_cols = grid_props["columnCount"] if grid_props else 26

    # Column widths: [code, code, code, name, brand, cat, subcat, price, curr, unit, short, long, specs, features, image, ready, synced]
    col_widths = [100, 100, 110, 200, 100, 120, 160, 80, 60, 60, 200, 350, 250, 250, 120, 80, 120]

    # First, delete any existing Table objects (they conflict with basic filters)
    for sheet in meta.get("sheets", []):
        if sheet["properties"]["sheetId"] == sheet_id:
            for table in sheet.get("tables", []):
                table_id = table["tableId"]
                print(f"  Removing Table object: {table.get('name', table_id)}")
                service.spreadsheets().batchUpdate(
                    spreadsheetId=MASTER_CATALOG_ID,
                    body={"requests": [{"deleteTable": {"tableId": table_id}}]},
                ).execute()

    requests = []

    # 0. Clear any existing basic filter first
    requests.append({
        "clearBasicFilter": {
            "sheetId": sheet_id,
        }
    })

    # 1. Freeze header row
    requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet_id,
                "gridProperties": {"frozenRowCount": 1},
            },
            "fields": "gridProperties.frozenRowCount",
        }
    })

    # 2. Header row formatting: bold, dark green bg (#2E7D32), white text
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": 1,
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.18, "green": 0.49, "blue": 0.20, "alpha": 1},
                    "textFormat": {
                        "bold": True,
                        "foregroundColor": {"red": 1, "green": 1, "blue": 1, "alpha": 1},
                        "fontSize": 10,
                    },
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE",
                    "wrapStrategy": "WRAP",
                },
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)",
        }
    })

    # 3. Data rows: clear any manual formatting, set wrap and vertical alignment
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 1,
                "endRowIndex": 100,  # Enough for current data
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 1, "green": 1, "blue": 1, "alpha": 1},
                    "textFormat": {
                        "bold": False,
                        "foregroundColor": {"red": 0, "green": 0, "blue": 0, "alpha": 1},
                        "fontSize": 10,
                    },
                    "verticalAlignment": "TOP",
                    "wrapStrategy": "WRAP",
                },
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)",
        }
    })

    # 4. Alternating row colors — use conditional formatting per-row instead of banded ranges
    # Even rows: light green background
    for row_idx in range(2, 12, 2):  # rows 2, 4, 6, 8, 10 (0-indexed: 1, 3, 5, 7, 9)
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": row_idx,
                    "endRowIndex": row_idx + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": len(col_widths),
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.93, "green": 0.96, "blue": 0.93, "alpha": 1},
                    },
                },
                "fields": "userEnteredFormat.backgroundColor",
            }
        })

    # 5. Set column widths
    for i, width in enumerate(col_widths):
        requests.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": i,
                    "endIndex": i + 1,
                },
                "properties": {"pixelSize": width},
                "fields": "pixelSize",
            }
        })

    # 6. Set header row height
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": 0,
                "endIndex": 1,
            },
            "properties": {"pixelSize": 40},
            "fields": "pixelSize",
        }
    })

    # 7. Add auto-filter (must cover full grid to avoid partial table overlap)
    requests.append({
        "setBasicFilter": {
            "filter": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": total_rows,
                    "startColumnIndex": 0,
                    "endColumnIndex": total_cols,
                },
            }
        }
    })

    # 8. Price column: number format with 2 decimals
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 1,
                "endRowIndex": 100,
                "startColumnIndex": 7,  # base_price column (H)
                "endColumnIndex": 8,
            },
            "cell": {
                "userEnteredFormat": {
                    "numberFormat": {
                        "type": "NUMBER",
                        "pattern": "#,##0.00",
                    },
                    "horizontalAlignment": "RIGHT",
                },
            },
            "fields": "userEnteredFormat(numberFormat,horizontalAlignment)",
        }
    })

    # 9. catalog_ready column: center align
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 1,
                "endRowIndex": 100,
                "startColumnIndex": 15,  # catalog_ready (P)
                "endColumnIndex": 16,
            },
            "cell": {
                "userEnteredFormat": {
                    "horizontalAlignment": "CENTER",
                },
            },
            "fields": "userEnteredFormat(horizontalAlignment)",
        }
    })

    # Execute all formatting requests
    service.spreadsheets().batchUpdate(
        spreadsheetId=MASTER_CATALOG_ID,
        body={"requests": requests},
    ).execute()

    print("Formatting applied to Master_Database:")
    print("  - Header: frozen, bold, dark green background")
    print("  - Alternating row colors (white / light green)")
    print("  - Auto-filter enabled")
    print("  - Column widths optimized")
    print("  - Text wrapping enabled")
    print("  - Price column formatted")


if __name__ == "__main__":
    format_master_database()
