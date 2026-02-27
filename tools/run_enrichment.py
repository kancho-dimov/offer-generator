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
from tools.translate_and_enrich import enrich_products, enrich_from_bg_name
from tools.update_master_catalog import (
    update_catalog,
    ensure_baseline_entries,
    load_pricelist_raw,
)

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
        Dict with keys: products, total, not_in_pricelist, baseline_written,
                        mapped, scraped, basic, translated.
    """
    _log = on_log or print
    _step = on_step or (lambda s, l: None)

    # ── Step 0: Baseline registration (no API, no scraping) ──────────────
    _step(0, "Базова регистрация от ценовата листа")
    pricelist_raw = load_pricelist_raw()
    baseline = ensure_baseline_entries(codes, pricelist_raw)
    not_in_pricelist = baseline["not_in_pricelist"]
    if not_in_pricelist:
        _log(f"Не са в ценовата листа: {', '.join(not_in_pricelist)}")
    _log(f"Регистрирани нови: {baseline['written']} | Вече налични: {baseline['already_present']}")
    codes_to_enrich = [c for c in codes if c not in not_in_pricelist]

    # ── Step 1: Map pricelist + nomenclature ─────────────────────────────
    _step(1, "Свързване с номенклатурата")
    products = map_codes(codes_to_enrich, progress_cb=_log)
    mapped = sum(1 for p in products if p["match_status"] != "none")
    _log(f"Намерени съответствия: {mapped}/{len(products)}")

    # ── Step 2: Scrape ────────────────────────────────────────────────────
    _step(2, "Извличане от romstal.ro")
    products = scrape_products(products)
    scraped = sum(1 for p in products if p.get("scrape_status") == "success")
    _log(f"Извлечени: {scraped}/{len(products)}")

    # ── Step 3: Translate + enrich ────────────────────────────────────────
    _step(3, "Превод и обогатяване")
    to_translate = sum(1 for p in products if p.get("scrape_status") == "success")
    est_cost = to_translate * 2 * 0.003  # 2 Claude calls per product, ~$0.003 each
    _log(f"Превеждане на {to_translate} продукта (прибл. разход: ${est_cost:.2f})")
    products = enrich_products(products)

    # Step 3b: Lightweight Claude for pricelist_only (no nomenclature data)
    for product in products:
        if (product.get("match_status") == "pricelist_only"
                and product.get("enrich_status") in ("skipped", "failed", None)):
            result = enrich_from_bg_name(product)
            if result:
                product["enriched_data"] = result
                product["enrich_status"] = "basic"
                _log(f"  Основно: {product['product_code']} → "
                     f"{result.get('brand', '?')} | {result.get('category', '?')}")

    basic = sum(1 for p in products if p.get("enrich_status") == "basic")
    translated = sum(1 for p in products if p.get("enrich_status") == "success")
    _log(f"Напълно обогатени: {translated} | Основно обогатени: {basic}")

    # Save intermediate results
    TMP_DIR.mkdir(exist_ok=True)
    with open(TMP_DIR / "enriched_products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    # ── Step 4: Write to Master Catalog ──────────────────────────────────
    _step(4, "Запис в Master Catalog")
    update_catalog(force=force)
    _log("Master Catalog updated")

    return {
        "products": products,
        "total": len(codes),
        "not_in_pricelist": not_in_pricelist,
        "baseline_written": baseline["written"],
        "mapped": mapped,
        "scraped": scraped,
        "basic": basic,
        "translated": translated,
    }


def main():
    force = "--force" in sys.argv

    print("=" * 60)
    print("  ENRICHMENT PIPELINE")
    print("=" * 60)

    # Read wishlist codes
    products_for_main = run_mapper()
    codes = [p["product_code"] for p in products_for_main]

    result = run_pipeline(codes, force=force)

    # Final summary
    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print(f"  Total codes:         {result['total']}")
    print(f"  Baseline written:    {result['baseline_written']}")
    print(f"  Matched in nom.:     {result['mapped']}")
    print(f"  Scraped:             {result['scraped']}")
    print(f"  Basic enriched:      {result['basic']}")
    print(f"  Fully translated:    {result['translated']}")
    if result["not_in_pricelist"]:
        print(f"  Not in pricelist:    {', '.join(result['not_in_pricelist'])}")
    print(f"  Master Catalog: https://docs.google.com/spreadsheets/d/1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY")


if __name__ == "__main__":
    main()
