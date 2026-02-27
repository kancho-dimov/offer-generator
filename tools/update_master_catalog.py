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
PRICELIST_ID = "1gx6xQoGtH1KCPRq7ZSJe1ZmD2kvIQh8g3nzm8eFzXLk"
MASTER_DB_TAB = "Master_Database"
TMP_DIR = Path(__file__).resolve().parent.parent / ".tmp"

# Romanian → Bulgarian category translation (applied to ALL products)
CATEGORY_MAP = {
    "RADIATOARE": "Радиатори",
    "CENTRALE MURALE": "Стенни котли",
    "BATERII": "Смесители",
    "POMPE, VASE DE EXPANSIUNE": "Помпи и разширителни съдове",
    "SISTEME DE INCALZIRE IN PARDOSEALA": "Подово отопление",
    "CANALIZARI SI SCURGERI": "Канализация и отводняване",
    "ROBINETI, RACORDURI, ACCESORII": "Кранове, фитинги, аксесоари",
    "FILTRE, CONTOARE, REZERVOARE": "Филтри, водомери, резервоари",
    "KLIMA": "Климатизация",
    "COSURI DE FUM SI TUBULATURA": "Комини и димоотводи",
    "IZOLATIE": "Изолация",
    "PREPARARE ACM": "Подгряване на БГВ",
}

SUBCAT_MAP = {
    "ALUMINIU": "Алуминиеви",
    "OTEL": "Стоманени",
    "BIMETALICE": "Биметални",
    "DECORATIVE": "Дизайнерски",
    "PARDOSEALA": "Подови",
    "GAZ": "Газови",
    "CONDENSARE": "Кондензни",
    "ELECTRICE": "Електрически",
    "BATERII BUCATARIE": "Смесители за кухня",
    "BATERII BAIE": "Смесители за баня",
    "BATERII CADA": "Смесители за вана",
    "BATERII BIDEU": "Смесители за биде",
    "BATERII LAVOAR": "Смесители за умивалник",
    "TEVI SI FITINGURI DIN PP (POLIPROPILENA)": "Тръби и фитинги от полипропилен (PP)",
    "TEVI SI FITINGURI DIN PVC": "Тръби и фитинги от PVC",
    "PP _ CANALIZARE INTERIOARA": "PP - Вътрешна канализация",
    "PVC _ CANALIZARE EXTERIOARA": "PVC - Външна канализация",
    "POMPE CIRCULATIE": "Циркулационни помпи",
    "POMPE SUBMERSIBILE": "Потопяеми помпи",
    "HIDROFOARE": "Хидрофорни системи",
    "VASE DE EXPANSIUNE": "Разширителни съдове",
    "ROBINETI": "Кранове",
    "FILTRE APA": "Филтри за вода",
    "CONTOARE APA": "Водомери",
    "BOILERE": "Бойлери",
    "PANOURI SOLARE": "Слънчеви колектори",
    "POMPE CALDURA": "Термопомпи",
}


def _translate_category(raw: str) -> str:
    """Translate a Romanian category to Bulgarian using static map."""
    if not raw:
        return ""
    # Try exact match first
    if raw in CATEGORY_MAP:
        return CATEGORY_MAP[raw]
    # Try case-insensitive
    upper = raw.upper().strip()
    for ro, bg in CATEGORY_MAP.items():
        if upper == ro.upper():
            return bg
    return raw  # Return as-is if no match


def _translate_subcategory(raw: str) -> str:
    """Translate a Romanian subcategory to Bulgarian using static map."""
    if not raw:
        return ""
    # Try each part (subcategory can be "CLASS / SUBCLASS")
    parts = [p.strip() for p in raw.split("/")]
    translated = []
    for part in parts:
        matched = False
        upper = part.upper().strip()
        for ro, bg in SUBCAT_MAP.items():
            if upper == ro.upper():
                translated.append(bg)
                matched = True
                break
        if not matched:
            translated.append(part)
    return " / ".join(translated)


def load_pricelist_raw() -> dict:
    """Load pricelist keyed by SAP code → {name_bg, measure_unit}.
    Used by ensure_baseline_entries() for Step 0 registration.
    """
    rows = read_sheet(PRICELIST_ID, "'Sheet1'!A:K")
    data = {}
    for row in rows[1:]:
        if len(row) < 5:
            continue
        code = row[2].strip()
        if code:
            data[code] = {
                "name_bg":      row[3] if len(row) > 3 else "",
                "measure_unit": row[7] if len(row) > 7 else "",
            }
    return data


def ensure_baseline_entries(codes: list, pricelist_data: dict) -> dict:
    """Write Tier 0 records for requested codes that exist in the pricelist
    but are NOT already in Master_Database (any tier).
    Idempotent: never downgrades an existing record.
    """
    existing = load_existing_catalog()
    to_write = []
    not_in_pricelist = []

    for code in codes:
        if code in existing:
            continue                              # already present — don't touch
        pl = pricelist_data.get(code)
        if not pl:
            not_in_pricelist.append(code)
            continue
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        row = [
            code, code, "",                       # product_code, internal_code, supplier_code
            pl.get("name_bg", ""),                # name
            "", "", "",                           # brand, category, subcategory
            pl.get("measure_unit", ""),           # measure_unit
            "", "", "", "",                       # short_desc, long_desc, specs, features
            "",                                   # image_url
            "FALSE",                              # catalog_ready
            now,                                  # last_updated
        ]
        to_write.append(row)

    if to_write:
        raw = read_sheet(MASTER_CATALOG_ID, f"'{MASTER_DB_TAB}'!A:A")
        start_row = len(raw) + 1                  # next empty row (1-based, includes header)
        write_sheet(
            MASTER_CATALOG_ID,
            f"'{MASTER_DB_TAB}'!A{start_row}",
            to_write,
        )
        print(f"  Baseline: wrote {len(to_write)} Tier 0 records starting at row {start_row}")

    already_present = len(codes) - len(to_write) - len(not_in_pricelist)
    return {
        "written": len(to_write),
        "already_present": already_present,
        "not_in_pricelist": not_in_pricelist,
    }


# Simplified column layout - single image_url instead of 3 image columns
COLUMNS = [
    "product_code",        # A
    "internal_code",       # B
    "supplier_code",       # C
    "name",                # D
    "brand",               # E
    "category",            # F
    "subcategory",         # G
    "measure_unit",        # H
    "short_description",   # I
    "long_description",    # J
    "specifications",      # K
    "features",            # L
    "image_url",           # M - single small image
    "catalog_ready",       # N
    "last_updated",        # O
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
    rows = read_sheet(MASTER_CATALOG_ID, f"'{MASTER_DB_TAB}'!A:O")
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

    # Use translated brand/category from Claude, fallback to static map
    brand = enriched.get("brand", "") or scraped.get("brand", "") or product.get("supplier_name", "")

    raw_category = enriched.get("category", "") or product.get("category", "")
    category = _translate_category(raw_category) if raw_category else ""

    raw_subcat = enriched.get("subcategory", "")
    if not raw_subcat:
        raw_subcat = f"{product.get('class_name', '')} / {product.get('subclass', '')}".strip(" /")
    subcategory = _translate_subcategory(raw_subcat) if raw_subcat else ""

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
        product.get("measure_unit", product.get("unit", "")),  # measure_unit
        enriched.get("short_description", ""),          # short_description
        enriched.get("long_description", ""),           # long_description
        enriched.get("specifications", ""),             # specifications
        enriched.get("features", ""),                   # features
        f'=HYPERLINK("{image_url}")' if image_url else "",  # image_url (clickable link)
        "TRUE" if enriched else "FALSE",                # catalog_ready
        now,                                            # last_updated
    ]

    return row


def update_catalog(force: bool = False):
    """Main function to update the Master_Database with enriched products."""
    enriched_path = TMP_DIR / "enriched_products.json"
    if not enriched_path.exists():
        raise FileNotFoundError("Run translate_and_enrich first to generate enriched_products.json")

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

        if product.get("match_status") == "none":
            print(f"  Skipping {code} - no match in pricelist or nomenclature")
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
        raw = read_sheet(MASTER_CATALOG_ID, f"'{MASTER_DB_TAB}'!A:O")
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
