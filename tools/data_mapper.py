"""
Maps and joins data from Pricelist (BG) and Nomenclatures (RO) for products
listed in the Product_Codes wishlist sheet.

Usage:
    python -m tools.data_mapper

Reads Product_Codes wishlist, joins pricelist + nomenclature on Cod Articol,
and returns merged product data ready for enrichment.
"""

import json
import sys
from pathlib import Path

from tools.sheets_api import read_sheet

# Sheet IDs
MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"
PRICELIST_ID = "1gx6xQoGtH1KCPRq7ZSJe1ZmD2kvIQh8g3nzm8eFzXLk"
NOMENCLATURES_ID = "1qfuXFqwwUGi-ovm_Wu5O1ptwZA65ARDIf2z91X-syhg"
NOMENCLATURES_TAB = "Compatibilitati - 2025-07-07T16"

# Output path
TMP_DIR = Path(__file__).resolve().parent.parent / ".tmp"


def load_wishlist() -> list[str]:
    """Load product codes from the Product_Codes wishlist sheet."""
    rows = read_sheet(MASTER_CATALOG_ID, "'Product_Codes'!A:A")
    codes = []
    for row in rows[1:]:  # Skip header
        if row and row[0].strip():
            codes.append(row[0].strip())
    return codes


def load_pricelist() -> dict:
    """Load pricelist into a dict keyed by material code."""
    rows = read_sheet(PRICELIST_ID, "'Sheet1'!A:K")
    if not rows:
        return {}
    headers = rows[0]
    data = {}
    for row in rows[1:]:
        if len(row) < 5:
            continue
        code = row[2].strip()  # Материал
        data[code] = {
            "sales_org": row[0] if len(row) > 0 else "",
            "material_code": code,
            "name_bg": row[3] if len(row) > 3 else "",
            "base_price": row[4] if len(row) > 4 else "",
            "currency": row[5] if len(row) > 5 else "",
            "per_qty": row[6] if len(row) > 6 else "",
            "measure_unit": row[7] if len(row) > 7 else "",
            "valid_from": row[8] if len(row) > 8 else "",
            "valid_to": row[9] if len(row) > 9 else "",
        }
    return data


def load_nomenclature() -> dict:
    """Load nomenclature into a dict keyed by Cod Articol."""
    rows = read_sheet(NOMENCLATURES_ID, f"'{NOMENCLATURES_TAB}'!A:V")
    if not rows:
        return {}
    data = {}
    for row in rows[1:]:
        if len(row) < 2:
            continue
        code = row[1].strip()  # Cod Articol
        data[code] = {
            "supplier_code": row[0].strip() if len(row) > 0 else "",
            "cod_articol": code,
            "short_name_ro": row[2] if len(row) > 2 else "",
            "long_desc_ro": (row[3] if len(row) > 3 else "").lstrip("#*@\t -"),
            "unit": row[6] if len(row) > 6 else "",
            "abc_category": row[7] if len(row) > 7 else "",
            "supplier_id": row[8] if len(row) > 8 else "",
            "supplier_name": row[9] if len(row) > 9 else "",
            "supplier_code_alt": row[10] if len(row) > 10 else "",
            "supplier_desc": row[12] if len(row) > 12 else "",
            "material_group": row[13] if len(row) > 13 else "",
            "division": row[14] if len(row) > 14 else "",
            "category": row[15] if len(row) > 15 else "",
            "class_name": row[16] if len(row) > 16 else "",
            "subclass": row[17] if len(row) > 17 else "",
            "gross_weight_kg": row[18] if len(row) > 18 else "",
            "net_weight_kg": row[19] if len(row) > 19 else "",
        }
    return data


def map_products(wishlist: list[str], pricelist: dict, nomenclature: dict) -> list[dict]:
    """
    Join pricelist and nomenclature data for each wishlist code.

    Returns a list of merged product dicts.
    """
    products = []
    for code in wishlist:
        product = {"product_code": code, "match_status": "none"}

        pl = pricelist.get(code)
        nom = nomenclature.get(code)

        if pl and nom:
            product["match_status"] = "full"
        elif pl:
            product["match_status"] = "pricelist_only"
        elif nom:
            product["match_status"] = "nomenclature_only"

        # Merge pricelist data
        if pl:
            product["name_bg"] = pl["name_bg"]
            product["base_price"] = pl["base_price"]
            product["currency"] = pl["currency"]
            product["measure_unit"] = pl["measure_unit"]

        # Merge nomenclature data
        if nom:
            product["supplier_code"] = nom["supplier_code"]
            product["short_name_ro"] = nom["short_name_ro"]
            product["long_desc_ro"] = nom["long_desc_ro"]
            product["supplier_name"] = nom["supplier_name"]
            product["division"] = nom["division"]
            product["category"] = nom["category"]
            product["class_name"] = nom["class_name"]
            product["subclass"] = nom["subclass"]
            product["unit"] = nom["unit"]

        products.append(product)

    return products


def map_codes(codes: list[str], progress_cb=None) -> list[dict]:
    """Map a list of SAP codes against pricelist + nomenclature.

    Args:
        codes: List of SAP material codes to look up.
        progress_cb: Optional callable(message: str) for progress updates.

    Returns:
        List of merged product dicts ready for enrichment.
    """
    _log = progress_cb or print

    _log("Loading pricelist...")
    pricelist = load_pricelist()
    _log(f"  Loaded {len(pricelist)} entries")

    _log("Loading nomenclature...")
    nomenclature = load_nomenclature()
    _log(f"  Loaded {len(nomenclature)} entries")

    _log("Mapping products...")
    products = map_products(codes, pricelist, nomenclature)

    full = sum(1 for p in products if p["match_status"] == "full")
    pl_only = sum(1 for p in products if p["match_status"] == "pricelist_only")
    nom_only = sum(1 for p in products if p["match_status"] == "nomenclature_only")
    none_count = sum(1 for p in products if p["match_status"] == "none")
    _log(f"  Results: {full} full, {pl_only} pricelist-only, {nom_only} nom-only, {none_count} no match")

    return products


def run() -> list[dict]:
    """Main entry point: load data, map products, save to .tmp."""
    print("Loading wishlist from Product_Codes...")
    wishlist = load_wishlist()
    print(f"  Found {len(wishlist)} product codes")

    print("Loading pricelist...")
    pricelist = load_pricelist()
    print(f"  Loaded {len(pricelist)} entries")

    print("Loading nomenclature...")
    nomenclature = load_nomenclature()
    print(f"  Loaded {len(nomenclature)} entries")

    print("Mapping products...")
    products = map_products(wishlist, pricelist, nomenclature)

    # Report match stats
    full = sum(1 for p in products if p["match_status"] == "full")
    pl_only = sum(1 for p in products if p["match_status"] == "pricelist_only")
    nom_only = sum(1 for p in products if p["match_status"] == "nomenclature_only")
    none = sum(1 for p in products if p["match_status"] == "none")
    print(f"  Results: {full} full matches, {pl_only} pricelist-only, {nom_only} nom-only, {none} no match")

    # Save to .tmp
    TMP_DIR.mkdir(exist_ok=True)
    output_path = TMP_DIR / "mapped_products.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {output_path}")

    return products


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    products = run()
    print("\n=== Mapped Products ===")
    for p in products:
        status = p["match_status"]
        code = p["product_code"]
        name = p.get("name_bg", p.get("short_name_ro", "N/A"))
        price = p.get("base_price", "N/A")
        cat = p.get("category", "N/A")
        print(f"  [{status}] {code}: {name} | {price} EUR | {cat}")
