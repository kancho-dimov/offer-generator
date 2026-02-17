"""
Writes enriched product data to the Master_Database sheet in Google Sheets.

Idempotent: checks which products already exist and only adds/updates as needed.
Products already marked as catalog_ready=TRUE are skipped unless --force is used.

Usage:
    python -m tools.update_master_catalog          # Only add new / update non-ready
    python -m tools.update_master_catalog --force   # Update all, including already-ready
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from tools.sheets_api import read_sheet, write_sheet, clear_sheet

MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"
MASTER_DB_TAB = "Master_Database"
TMP_DIR = Path(__file__).resolve().parent.parent / ".tmp"

# Simplified column layout - single image_url instead of 3 image columns
COLUMNS = [
    "product_code",        # A
    "internal_code",       # B
    "supplier_code",       # C
    "name",                # D
    "brand",               # E
    "category",            # F
    "subcategory",         # G
    "base_price",          # H
    "currency",            # I
    "measure_unit",        # J
    "short_description",   # K
    "long_description",    # L
    "specifications",      # M
    "features",            # N
    "image_url",           # O - single small image
    "catalog_ready",       # P
    "last_synced",         # Q
]


def get_small_image_url(scraped: dict) -> str:
    """Get a single small PNG/JPG image URL from scraped data."""
    image_main = scraped.get("image_url_main", "")
    if not image_main:
        return ""

    # Validate: URL must end with an image file extension
    if not re.search(r"\.(jpg|jpeg|png|gif|webp|svg)(\?.*)?$", image_main, re.IGNORECASE):
        return ""

    # Use the CDN's resize parameter for a small image (300px wide)
    # romstal CDN format: /slir/wNNN/domain/path
    if "contentspeed.ro" in image_main:
        # Strip any existing resize, add w300
        clean = re.sub(r"/slir/w\d+/", "/", image_main)
        # Re-insert the resize
        clean = clean.replace("contentspeed.ro/", "contentspeed.ro/slir/w300/", 1)
        return clean

    return image_main


def load_existing_catalog() -> dict[str, dict]:
    """Load existing products from Master_Database, keyed by product_code."""
    rows = read_sheet(MASTER_CATALOG_ID, f"'{MASTER_DB_TAB}'!A:Q")
    if not rows or len(rows) < 2:
        return {}

    headers = rows[0]
    existing = {}
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        product = {}
        for i, col in enumerate(headers):
            product[col] = row[i] if i < len(row) else ""
        existing[product["product_code"]] = product

    return existing


def build_row(product: dict) -> list[str]:
    """Convert an enriched product dict into a row for the Master_Database sheet."""
    scraped = product.get("scraped_data") or {}
    enriched = product.get("enriched_data") or {}

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Use translated brand/category from Claude, fallback to raw
    brand = enriched.get("brand", "") or scraped.get("brand", "") or product.get("supplier_name", "")
    category = enriched.get("category", "") or product.get("category", "")
    subcategory = enriched.get("subcategory", "") or f"{product.get('class_name', '')} / {product.get('subclass', '')}".strip(" /")

    # Single small image
    image_url = get_small_image_url(scraped)

    row = [
        product.get("product_code", ""),               # product_code
        product.get("product_code", ""),               # internal_code
        product.get("supplier_code", ""),               # supplier_code
        product.get("name_bg", ""),                     # name
        brand,                                          # brand
        category,                                       # category
        subcategory,                                    # subcategory
        product.get("base_price", ""),                  # base_price
        product.get("currency", ""),                    # currency
        product.get("measure_unit", product.get("unit", "")),  # measure_unit
        enriched.get("short_description", ""),          # short_description
        enriched.get("long_description", ""),           # long_description
        enriched.get("specifications", ""),             # specifications
        enriched.get("features", ""),                   # features
        f'=HYPERLINK("{image_url}")' if image_url else "",  # image_url (clickable link)
        "TRUE" if enriched else "FALSE",                # catalog_ready
        now,                                            # last_synced
    ]

    return row


def update_catalog(force: bool = False):
    """Main function to update the Master_Database with enriched products."""
    enriched_path = TMP_DIR / "enriched_products.json"
    if not enriched_path.exists():
        print("ERROR: Run translate_and_enrich first to generate enriched_products.json")
        sys.exit(1)

    with open(enriched_path, encoding="utf-8") as f:
        products = json.load(f)

    print(f"Loaded {len(products)} enriched products")

    print("Loading existing Master_Database...")
    existing = load_existing_catalog()
    print(f"  Found {len(existing)} existing products")

    to_write = []
    skipped = 0
    for product in products:
        code = product["product_code"]
        enriched = product.get("enriched_data")

        if not enriched and product.get("enrich_status") != "success":
            print(f"  Skipping {code} - not enriched")
            skipped += 1
            continue

        if code in existing and not force:
            ex = existing[code]
            if ex.get("catalog_ready", "").upper() == "TRUE":
                print(f"  Skipping {code} - already catalog_ready (use --force to override)")
                skipped += 1
                continue

        row = build_row(product)
        to_write.append(row)

    if not to_write:
        print("\nNo products to write. Everything is up to date.")
        return

    print(f"\nWriting {len(to_write)} products to Master_Database...")

    # Merge with existing data
    all_rows = []
    existing_codes_in_sheet = set()

    if existing:
        raw = read_sheet(MASTER_CATALOG_ID, f"'{MASTER_DB_TAB}'!A:Q")
        if raw and len(raw) > 1:
            for row in raw[1:]:
                if row and row[0].strip():
                    code = row[0].strip()
                    existing_codes_in_sheet.add(code)
                    updated = False
                    for new_row in to_write:
                        if new_row[0] == code:
                            all_rows.append(new_row)
                            updated = True
                            break
                    if not updated:
                        while len(row) < len(COLUMNS):
                            row.append("")
                        all_rows.append(row[:len(COLUMNS)])

    for new_row in to_write:
        if new_row[0] not in existing_codes_in_sheet:
            all_rows.append(new_row)

    header_row = COLUMNS
    all_data = [header_row] + all_rows

    # Clear wider range to remove old gallery/thumbnail columns
    clear_sheet(MASTER_CATALOG_ID, f"'{MASTER_DB_TAB}'!A:Z")
    result = write_sheet(MASTER_CATALOG_ID, f"'{MASTER_DB_TAB}'!A1", all_data, input_option="USER_ENTERED")
    print(f"  Written {result.get('updatedRows', 0)} rows (including header)")
    print(f"  Skipped: {skipped}")
    print("  Done!")


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    force = "--force" in sys.argv
    update_catalog(force=force)
