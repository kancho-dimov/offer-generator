"""
Master orchestrator: runs the full enrichment pipeline end-to-end.

Steps:
1. Map data from Pricelist + Nomenclature for Product_Codes wishlist
2. Scrape product pages from romstal.ro
3. Translate to Bulgarian with proper HVAC terminology
4. Write enriched data to Master_Database

Usage:
    python -m tools.run_enrichment           # Normal run (skip already-ready products)
    python -m tools.run_enrichment --force   # Force update all products
"""

import json
import sys
import io
from pathlib import Path

if "streamlit" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from tools.data_mapper import run as run_mapper, map_codes
from tools.scrape_product import scrape_products
from tools.translate_and_enrich import enrich_products
from tools.update_master_catalog import update_catalog

TMP_DIR = Path(__file__).resolve().parent.parent / ".tmp"


def run_pipeline(
    codes: list[str],
    force: bool = False,
    on_step=None,
    on_log=None,
) -> dict:
    """Run the enrichment pipeline for a given list of SAP codes.

    Args:
        codes: List of SAP material codes to process.
        force: If True, overwrite products already marked catalog_ready.
        on_step: Optional callable(step: int, label: str) called at each step start.
        on_log: Optional callable(message: str) for progress messages.

    Returns:
        Dict with keys: products, total, mapped, scraped, translated, written.
    """
    _log = on_log or print
    _step = on_step or (lambda s, l: None)

    # Step 1: Map data
    _step(1, "Mapping pricelist + nomenclature data")
    products = map_codes(codes, progress_cb=_log)
    mapped = sum(1 for p in products if p["match_status"] != "none")
    _log(f"Mapped {mapped}/{len(products)} codes")

    # Step 2: Scrape
    _step(2, "Scraping product pages from romstal.ro")
    products = scrape_products(products)
    scraped = sum(1 for p in products if p.get("scrape_status") == "success")
    _log(f"Scraped {scraped}/{len(products)} products")

    # Step 3: Translate
    _step(3, "Translating to Bulgarian")
    to_translate = sum(1 for p in products if p.get("scrape_status") == "success")
    est_cost = to_translate * 2 * 0.003  # 2 Claude calls per product, ~$0.003 each
    _log(f"Translating {to_translate} products (est. API cost: ${est_cost:.2f})")
    products = enrich_products(products)
    translated = sum(1 for p in products if p.get("enrich_status") == "success")
    _log(f"Translated {translated}/{len(products)} products")

    # Save intermediate results
    TMP_DIR.mkdir(exist_ok=True)
    with open(TMP_DIR / "enriched_products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    # Step 4: Write to Master Catalog
    _step(4, "Writing to Master Catalog")
    update_catalog(force=force)
    _log("Master Catalog updated")

    return {
        "products": products,
        "total": len(products),
        "mapped": mapped,
        "scraped": scraped,
        "translated": translated,
    }


def main():
    force = "--force" in sys.argv

    print("=" * 60)
    print("  ENRICHMENT PIPELINE")
    print("=" * 60)

    # Step 1: Map data
    print("\n STEP 1: Mapping pricelist + nomenclature data...")
    print("-" * 40)
    products = run_mapper()

    # Step 2: Scrape
    print("\n STEP 2: Scraping product pages from romstal.ro...")
    print("-" * 40)
    products = scrape_products(products)

    # Step 3: Translate
    print("\n STEP 3: Translating to Bulgarian...")
    print("-" * 40)
    products = enrich_products(products)

    # Step 4: Write to Master Catalog
    print("\n STEP 4: Writing to Master Catalog...")
    print("-" * 40)
    with open(TMP_DIR / "enriched_products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    update_catalog(force=force)

    # Final summary
    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    total = len(products)
    scraped = sum(1 for p in products if p.get("scrape_status") == "success")
    enriched = sum(1 for p in products if p.get("enrich_status") == "success")
    print(f"  Total products: {total}")
    print(f"  Scraped: {scraped}")
    print(f"  Translated: {enriched}")
    print(f"  Check your Master Catalog: https://docs.google.com/spreadsheets/d/1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY")


if __name__ == "__main__":
    main()
