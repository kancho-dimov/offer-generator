# Workflow: Enrich Master Catalog

## Objective
Take product codes from the wishlist, merge pricelist (BG) and nomenclature (RO) data, scrape detailed product info from romstal.ro, translate to Bulgarian with proper HVAC terminology, and write enriched data to the Master Catalog Google Sheet.

## Prerequisites
- `credentials.json` in project root (Google OAuth)
- `.env` with `ANTHROPIC_API_KEY` set
- Product codes added to `Product_Codes` tab in Master Catalog
- Internet access to romstal.ro

## Data Sources
| Source | Sheet ID | Purpose |
|--------|----------|---------|
| Pricelist (BG) | `1gx6xQoGtH1KCPRq7ZSJe1ZmD2kvIQh8g3nzm8eFzXLk` | BG names, prices, currency |
| Nomenclatures (RO) | `1qfuXFqwwUGi-ovm_Wu5O1ptwZA65ARDIf2z91X-syhg` | RO descriptions, categories, supplier codes |
| Master Catalog | `1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY` | Output destination |

## Join Key
- **Cod Articol / Материал** (SAP material number) — same code in both pricelist and nomenclature
- Match rate: ~62% of pricelist codes exist in nomenclature

---

## Three-Tier Completeness Model

Products are registered and enriched progressively. Higher tiers add richer data on top of lower tiers.

```
TIER 0 — Registered (instant, zero API cost)
  Source:  BG Pricelist
  Fields:  product_code, name_bg, measure_unit, catalog_ready=FALSE, last_updated
  Value:   product is immediately findable in search and usable in offers/orders

TIER 1 — Basic (zero API cost for nomenclature products; micro Claude call for pricelist_only)
  Source:  RO Nomenclature → brand, category  OR  Claude from BG name text
  Fields:  + brand, category, subcategory, short_description
  Value:   brand/category filtering works; search is meaningful

TIER 2 — Enriched (current full pipeline)
  Source:  romstal.ro scraping + Claude translation
  Fields:  + long_description, features, specifications, image_url
  Status:  catalog_ready = TRUE
  Value:   rich catalog content
```

A product is usable in offer/order generation from Tier 0 onwards. `catalog_ready=TRUE` only applies to Tier 2.

---

## Multi-Source Scraping Strategy

### Available Sources (Waterfall Priority)

| Source | Status | URL Pattern | Language | Cost |
|--------|--------|-------------|----------|------|
| romstal.ro | Active | Slug from RO description | Romanian → Claude | Free (httpx) |
| romstal.bg | Under reconstruction | Same slug pattern | **Bulgarian — no translation!** | Free (httpx) |
| Producer sites | Future | Per-brand, needs discovery | Varies | Firecrawl credits |
| General web search | Future last resort | Dynamic search | Variable | Firecrawl credits |

### Waterfall Principle
The scraper tries sources in priority order. First success wins — no parallel fetching, no merging. This keeps results deterministic and failures isolated.

To switch the primary domain to romstal.bg when ready: change `SCRAPE_DOMAIN` in `tools/scrape_product.py` from `"www.romstal.ro"` to `"www.romstal.bg"`. No other changes needed.

---

## Pipeline Steps

### Quick Sync (UI: ⚡ button — no API cost)
Register products instantly without scraping or translation:
```
tools/update_master_catalog.py → ensure_baseline_entries()
```
Writes Tier 0 records for any codes in the pricelist that are not yet in Master_Database. Idempotent.

### Full Pipeline
```bash
python -m tools.run_enrichment
```
Runs all 5 steps automatically:

| Step | Tool | Description |
|------|------|-------------|
| 0 | `update_master_catalog.ensure_baseline_entries()` | Tier 0: register from pricelist |
| 1 | `tools/data_mapper.py` | Join pricelist + nomenclature on SAP code |
| 2 | `tools/scrape_product.py` | Scrape romstal.ro product pages |
| 3 | `tools/translate_and_enrich.py` | Claude translation (full or nomenclature fallback) |
| 3b | `translate_and_enrich.enrich_from_bg_name()` | Lightweight Claude for pricelist_only products |
| 4 | `tools/update_master_catalog.py` | Write to Master_Database |

### Individual Steps (for debugging)
```bash
python -m tools.data_mapper           # Step 1 only
python -m tools.scrape_product        # Step 2 only
python -m tools.translate_and_enrich  # Step 3 only
python -m tools.update_master_catalog # Step 4 only
```

### Force Update
To re-process products already marked as `catalog_ready=TRUE`:
```bash
python -m tools.run_enrichment --force
```

---

## Failure Modes and Fallbacks

| Product state | Behaviour |
|---|---|
| In pricelist + nomenclature, scrape OK | Tier 2 (full enrichment) |
| In pricelist + nomenclature, scrape fails | Tier 1 via `translate_from_nomenclature()` |
| Pricelist only (38%) | Tier 0 guaranteed; Tier 1 via `enrich_from_bg_name()` |
| `match_status = "none"` | Tier 0 guaranteed; UI shows clear error; no phantom record |
| Code not in pricelist at all | Hard error in UI — code is invalid |
| Enrichment never run | Tier 0 written on first Quick Sync or pipeline run |

---

## Idempotency
- `ensure_baseline_entries()` never downgrades an existing record
- Products with `catalog_ready=TRUE` are skipped unless `--force` is used
- Re-running the pipeline only processes new or incomplete products
- To refresh a specific product: set its `catalog_ready` to FALSE in the sheet, then re-run

---

## URL Construction Strategy
Product URLs are constructed by slugifying the Romanian description from the nomenclature:
- "Calorifer inalt din aluminiu, Vision, 1600x96 mm, 1436W" → `calorifer-inalt-din-aluminiu-vision-1600x96-mm-1436w.html`
- Controlled by `SCRAPE_DOMAIN` constant in `tools/scrape_product.py`

---

## Brand Source Notes
- **Nomenclature products**: brand = `supplier_name` from RO Nomenclature (structured field)
- **Pricelist-only products** (38%): brand embedded in BG product name text (e.g. "KERMI Профилна плоча 11/300/600") — Claude extracts it via `enrich_from_bg_name()`; no structured source exists

---

## Translation Approach
- Uses Claude API (Sonnet model) with a specialized HVAC terminology prompt
- Full enrichment generates: short description, long description, key features, specifications — all in Bulgarian
- Lightweight enrichment (`enrich_from_bg_name`): brand, category, short_description only — ~$0.0001/product
- Preserves brand names, dimensions, and technical values unchanged

---

## Output Fields (Master_Database)
| Column | Source |
|--------|--------|
| product_code | Wishlist |
| internal_code | SAP material number |
| supplier_code | Nomenclature |
| name | Pricelist (BG) |
| brand | Scraped from romstal.ro / nomenclature supplier_name / Claude |
| category / subcategory | Nomenclature categories |
| measure_unit | Pricelist |
| short_description | Claude translation |
| long_description | Claude translation |
| specifications | Claude translation |
| features | Claude translation |
| image_url | Scraped from romstal.ro |
| catalog_ready | TRUE when Tier 2 enrichment complete |
| last_updated | Timestamp |

**Note:** `base_price` and `currency` are NOT stored in Master_Database. They are loaded live from the pricelist at query time by `product_search.py`.

---

## Known Limitations
- ~38% of pricelist codes don't exist in nomenclature (BG-only products)
- URL construction depends on accurate Romanian descriptions
- Very long product descriptions are truncated to 3000 chars before translation

## Troubleshooting
- **No match in nomenclature**: Product only exists in BG pricelist, no RO data available → uses `enrich_from_bg_name()` fallback
- **Scrape failed**: URL might be constructed incorrectly — check the RO description; or switch `SCRAPE_DOMAIN` to romstal.bg when available
- **Translation failed**: Check Anthropic API key and credits
- **Google auth expired**: Delete `token.json` and re-run to re-authenticate
- **Product not found in app**: Check if code exists in BG Pricelist. Use Quick Sync button to register it instantly.
