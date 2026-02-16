# Workflow: Generate Offer / Price List

## Objective
Generate a professional offer or price list for a customer with cascading discounts. Primary output is a PDF-ready Google Sheet (Romstal brand colors, logo, merged headers). Optional exports: Google Slides presentation, markdown outline for gamma.app.

## Prerequisites
- Master_Database populated with enriched products (Phase 1)
- Customer exists in the Customers sheet
- Discount rules configured in Discount_Rules sheet
- Company branding configured in Company_Branding sheet
- Google OAuth token valid (Sheets + Slides + Drive scopes)

## Input

Create `.tmp/offer_request.json` with the following structure:

### Full Offer (bill of materials with quantities)
```json
{
  "customer_id": "CUST-001",
  "mode": "offer",
  "items": [
    {"product_code": "32FR8050", "quantity": 10},
    {"product_code": "44NP0003", "quantity": 5}
  ],
  "notes": "Project description or notes",
  "custom_discounts": [
    {"name": "Project discount", "percentage": 3}
  ],
  "show_discount": true,
  "discount_level": "line",
  "show_vat": true,
  "validity_days": 30
}
```

### Price List (net prices only, no quantities)
```json
{
  "customer_id": "CUST-001",
  "mode": "pricelist",
  "items": [
    {"product_code": "32FR8050"},
    {"product_code": "44NP0003"}
  ],
  "show_discount": false,
  "show_vat": true,
  "validity_days": 30
}
```

### Visibility Flags
| Flag | Values | Default | Effect |
|------|--------|---------|--------|
| `show_discount` | true/false | false | Base price + discount % columns visible |
| `discount_level` | "line"/"group" | "line" | Per-product or grouped by brand |
| `show_vat` | true/false | true | Price-with-VAT columns visible |

**Note:** All data is always written. Hidden columns can be unhidden manually in Google Sheets.

## Steps

### Step 1: Generate the offer
```bash
python -m tools.generate_offer
```

This will:
1. Load customer, products, and discount rules
2. Calculate compound cascading discounts
3. Create a new Google Spreadsheet with professional formatting:
   - Romstal blue header bar with logo (`#0086CE`)
   - Merged cells for header, customer info, totals, and footer
   - Alternating light-blue rows, branded table headers
   - Auto-orientation: portrait for pricelist, landscape for offer
4. Hide columns based on visibility flags
5. Save offer data to `.tmp/{offer_number}_data.json`

Output: Google Sheet URL + direct PDF export URL

### Step 1b: Export to PDF
The PDF URL is printed alongside the Sheet URL. Open it in a browser to download the PDF directly. The URL uses these settings:
- A4 paper size, fit-to-width
- No gridlines, no sheet names, no page numbers
- 0.3" margins all sides
- Portrait for pricelist, landscape for offer

Alternatively, open the Sheet → File → Print → set page options → Print to PDF.

### Step 2: Export to Google Slides (optional)
```bash
python -m tools.export_slides                    # latest offer
python -m tools.export_slides OFR-2026-001       # specific offer
```

Output: Google Slides URL (download as PDF from File > Download > PDF)

### Step 3: Export markdown outline (optional)
```bash
python -m tools.export_gamma_outline                    # latest offer
python -m tools.export_gamma_outline OFR-2026-001       # specific offer
```

Output: `.tmp/{offer_number}_gamma.md` — paste into gamma.app or similar

## Discount Cascade Logic

Discounts are applied in this order (compound/multiplicative):

1. **Best non-stackable rule** — highest discount among non-stackable matches
2. **All stackable rules** — each compounds on the remaining price
3. **Customer tier discount** — from Customers sheet `default_discount_pct`
4. **Custom discounts** — from `custom_discounts` in the request

Rules are matched by:
- `brand` — product brand matches rule target
- `category` — product category matches
- `subcategory` — product subcategory matches
- `product` — specific product code matches

Rules must be `active=TRUE` and within `valid_from`/`valid_until` dates.
Minimum quantity (`min_quantity`) must be met.

Example: base_price=100, Winter Sale 10% (non-stackable), SALUS Loyalty 5% (stackable), Gold tier 15%:
```
100 × 0.90 × 0.95 × 0.85 = 72.68 EUR (net excl. VAT)
72.68 × 1.20 = 87.21 EUR (incl. VAT)
```

## Offer Numbering

- Full offers: `OFR-YYYY-NNN` (e.g., OFR-2026-001)
- Price lists: `PL-YYYY-NNN` (e.g., PL-2026-001)
- Counters stored in Company_Branding sheet (`next_offer_number`, `next_pricelist_number`)

## Output Files

| File | Location |
|------|----------|
| Google Sheet | New spreadsheet (URL in console output) |
| PDF export | Direct download URL (in console output) |
| Google Slides | New presentation (optional, URL in console output) |
| Offer data | `.tmp/{offer_number}_data.json` |
| Markdown | `.tmp/{offer_number}_gamma.md` |

## Branding

- **Primary color**: Romstal blue `#0086CE`
- **Logo**: Loaded from `company_logo_url` in Company_Branding (falls back to Brandfetch CDN)
- To change the logo: update the `company_logo_url` key in the Company_Branding sheet

## Troubleshooting

- **"Product not found"**: Ensure product_code exists in Master_Database with `catalog_ready=TRUE`
- **Price parsing error**: Base prices with comma separators (e.g., "2,536.72") are handled automatically
- **OAuth error**: Delete `token.json` and re-run to re-authenticate
- **Slides API disabled**: Enable at https://console.developers.google.com/apis/api/slides.googleapis.com
