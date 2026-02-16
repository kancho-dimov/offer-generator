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

import sys
import io

if "streamlit" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from tools.data_mapper import run as run_mapper
from tools.scrape_product import scrape_products
from tools.translate_and_enrich import enrich_products
from tools.update_master_catalog import update_catalog


def main():
    force = "--force" in sys.argv

    print("=" * 60)
    print("  ENRICHMENT PIPELINE")
    print("=" * 60)

    # Step 1: Map data
    print("\n📋 STEP 1: Mapping pricelist + nomenclature data...")
    print("-" * 40)
    products = run_mapper()

    # Step 2: Scrape
    print("\n🌐 STEP 2: Scraping product pages from romstal.ro...")
    print("-" * 40)
    products = scrape_products(products)

    # Step 3: Translate
    print("\n🔤 STEP 3: Translating to Bulgarian...")
    print("-" * 40)
    products = enrich_products(products)

    # Step 4: Write to Master Catalog
    print("\n📊 STEP 4: Writing to Master Catalog...")
    print("-" * 40)
    # Save intermediate results first (in case catalog update fails)
    import json
    from pathlib import Path
    tmp = Path(__file__).resolve().parent.parent / ".tmp"
    with open(tmp / "enriched_products.json", "w", encoding="utf-8") as f:
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
