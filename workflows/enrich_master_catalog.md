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

## Pipeline Steps

### Step 1: Add Product Codes
Add desired product codes to the `Product_Codes` tab in the Master Catalog. Only codes listed here will be processed.

### Step 2: Run Full Pipeline
```bash
python -m tools.run_enrichment
```
This runs all 4 steps automatically:

1. **Data Mapper** (`tools/data_mapper.py`) — Reads wishlist, joins pricelist + nomenclature on SAP code
2. **Product Scraper** (`tools/scrape_product.py`) — Constructs romstal.ro URLs from RO descriptions, scrapes product pages via HTTP
3. **Translator** (`tools/translate_and_enrich.py`) — Uses Claude API (Sonnet) to translate RO→BG with HVAC terminology
4. **Catalog Updater** (`tools/update_master_catalog.py`) — Writes enriched data to Master_Database sheet

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

## Idempotency
- Products with `catalog_ready=TRUE` are skipped unless `--force` is used
- Re-running the pipeline only processes new or incomplete products
- To refresh a specific product: set its `catalog_ready` to FALSE in the sheet, then re-run

## URL Construction Strategy
Product URLs on romstal.ro are constructed by slugifying the Romanian description from the nomenclature:
- "Calorifer inalt din aluminiu, Vision, 1600x96 mm, 1436W" → `calorifer-inalt-din-aluminiu-vision-1600x96-mm-1436w.html`
- This works reliably for products with accurate Romanian descriptions

## Translation Approach
- Uses Claude API (Sonnet model) with a specialized HVAC terminology prompt
- Generates: short description, long description, key features, specifications — all in Bulgarian
- Preserves brand names, dimensions, and technical values unchanged

## Output Fields (Master_Database)
| Column | Source |
|--------|--------|
| product_code | Wishlist |
| internal_code | SAP material number |
| supplier_code | Nomenclature |
| name | Pricelist (BG) |
| brand | Scraped from romstal.ro |
| category / subcategory | Nomenclature categories |
| base_price / currency | Pricelist |
| short_description | Claude translation |
| long_description | Claude translation |
| specifications | Claude translation |
| features | Claude translation |
| image_url_main | Scraped from romstal.ro |
| catalog_ready | TRUE when enrichment complete |
| last_synced | Timestamp |

## Known Limitations
- ~38% of pricelist codes don't exist in nomenclature (BG-only products)
- URL construction depends on accurate Romanian descriptions
- Firecrawl MCP credits may be limited — scraper uses direct HTTP as primary method
- Very long product descriptions are truncated to 3000 chars before translation

## Troubleshooting
- **No match in nomenclature**: Product only exists in BG pricelist, no RO data available
- **Scrape failed**: URL might be constructed incorrectly — check the RO description
- **Translation failed**: Check Anthropic API key and credits
- **Google auth expired**: Delete `token.json` and re-run to re-authenticate
