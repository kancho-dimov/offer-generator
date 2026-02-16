"""
Import logistics/packaging data from the AMB Excel file into the Logistics tab.

Keeps only pcs (base unit) and carton (AMB2 = next packaging tier above pcs).
Orders can be placed in pcs or cartons; carton qty = pcs_per_carton × number_of_cartons.

Usage:
    python -m tools.import_logistics                              # default path
    python -m tools.import_logistics path/to/logistics.xlsx       # custom path
"""

import io
import sys
from pathlib import Path

import openpyxl

from tools.google_auth import get_sheets_service
from tools.sheets_api import clear_sheet, write_sheet

if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"
DEFAULT_FILE = Path(__file__).resolve().parent.parent / "resources" / "AMB_24.04.2023.xlsx"

HEADERS = [
    "product_code",     # SAP Material number
    "description",      # Romanian product name (for reference)
    "division",         # HIDRO, TERMO, etc.
    "base_unit",        # buc (pcs), m, kg, etc.
    "supplier",         # Manufacturer/supplier
    "pcs_per_carton",   # AMB2: pieces per carton/box
    "min_order_qty",    # Minimum order qty for direct import
]


def _parse_int(val) -> int:
    """Parse a value to int, handling comma decimals like '14,5'."""
    if not val:
        return 0
    s = str(val).replace(",", ".")
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return 0


def import_logistics(file_path: str | Path | None = None):
    """Read Excel and write to Logistics tab."""
    path = Path(file_path) if file_path else DEFAULT_FILE
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        sys.exit(1)

    print(f"Reading logistics file: {path.name}")
    wb = openpyxl.load_workbook(str(path))
    ws = wb.active

    rows = []
    skipped = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        # Cols: Material, Denumire, Divizia, UM, DistPol, StocPol, Categ, Furnizor,
        #       AMB1, AMB2, AMB3, AMB4, CANT_minima
        if not row or not row[0]:
            skipped += 1
            continue

        material = str(row[0]).strip()
        description = str(row[1] or "").strip()
        division = str(row[2] or "").strip()
        base_unit = str(row[3] or "").strip()
        supplier = str(row[7] or "").strip()
        pcs_per_carton = _parse_int(row[9])   # AMB2 = carton/box tier
        min_order_qty = _parse_int(row[12])

        rows.append([
            material, description, division, base_unit, supplier,
            pcs_per_carton, min_order_qty,
        ])

    wb.close()
    print(f"  Parsed {len(rows)} products ({skipped} empty rows skipped)")

    # Write to Logistics tab (clear first for idempotency)
    print("Writing to Logistics tab...")
    all_data = [HEADERS] + rows
    CHUNK = 5000

    # Expand grid to fit all rows
    service = get_sheets_service()
    meta = service.spreadsheets().get(spreadsheetId=MASTER_CATALOG_ID).execute()
    logistics_sheet_id = None
    for s in meta.get("sheets", []):
        if s["properties"]["title"] == "Logistics":
            logistics_sheet_id = s["properties"]["sheetId"]
            break

    if logistics_sheet_id is not None:
        needed_rows = len(all_data) + 100
        service.spreadsheets().batchUpdate(
            spreadsheetId=MASTER_CATALOG_ID,
            body={"requests": [{
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": logistics_sheet_id,
                        "gridProperties": {"rowCount": needed_rows},
                    },
                    "fields": "gridProperties.rowCount",
                }
            }]},
        ).execute()
        print(f"  Expanded grid to {needed_rows} rows")

    clear_sheet(MASTER_CATALOG_ID, "'Logistics'!A:G")

    for start in range(0, len(all_data), CHUNK):
        chunk = all_data[start:start + CHUNK]
        row_start = start + 1
        write_sheet(MASTER_CATALOG_ID, f"'Logistics'!A{row_start}", chunk)
        end_row = start + len(chunk)
        print(f"  Written rows {start + 1}-{end_row} of {len(all_data)}")

    print(f"Done! {len(rows)} products imported to Logistics tab.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import logistics Excel to Sheets")
    parser.add_argument("file", nargs="?", default=None, help="Path to Excel file")
    args = parser.parse_args()

    import_logistics(args.file)
