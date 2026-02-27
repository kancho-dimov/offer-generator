"""
Scrapes product data from romstal.ro for enrichment.

Uses direct HTTP requests + BeautifulSoup (no Firecrawl credits needed).

Strategy:
1. Construct URL from Romanian product description (slugify)
2. Fetch and parse the product page
3. Extract: description, specifications, image URLs

Usage:
    python -m tools.scrape_product
"""

import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

TMP_DIR = Path(__file__).resolve().parent.parent / ".tmp"

# Change to "www.romstal.bg" when it's fixed and BG content is stable
SCRAPE_DOMAIN = "www.romstal.ro"

# Browser-like headers to avoid blocks
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
}


def slugify(text: str) -> str:
    """Convert a Romanian product description into a romstal.ro URL slug."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = text.replace(",", "")
    text = text.replace("(", "").replace(")", "")
    text = text.replace("/", "-")
    text = text.replace("'", "").replace('"', "")
    text = text.replace(".", "-")
    text = text.replace("+", "")
    text = re.sub(r"[^a-z0-9-]", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    return text


def construct_product_url(long_desc_ro: str) -> str:
    """Construct a product URL from the Romanian description."""
    slug = slugify(long_desc_ro)
    return f"https://{SCRAPE_DOMAIN}/{slug}.html"


def fetch_page(url: str) -> str | None:
    """Fetch a URL and return the HTML content, or None on failure."""
    try:
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=20.0) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                return resp.text
            else:
                print(f"  HTTP {resp.status_code} for {url}")
                return None
    except Exception as e:
        print(f"  Fetch error: {e}")
        return None


def parse_product_page(html: str, url: str) -> dict:
    """Parse a romstal.ro product page HTML into structured data."""
    soup = BeautifulSoup(html, "lxml")
    result = {
        "description_long": "",
        "specifications": {},
        "image_url_main": "",
        "image_urls": [],
        "brand": "",
        "romstal_code": "",
        "supplier_code_web": "",
        "source_url": url,
    }

    # Extract brand from meta tag
    brand_meta = soup.find("meta", property="product:brand")
    if brand_meta:
        result["brand"] = brand_meta.get("content", "")

    # Extract main image from og:image
    og_image = soup.find("meta", property="og:image")
    if og_image:
        result["image_url_main"] = og_image.get("content", "")

    # Extract product images from gallery
    gallery_images = []
    for img in soup.select("a.cs-product-gallery__image img, .cs-product-gallery img"):
        src = img.get("src", "") or img.get("data-src", "")
        if src and "contentspeed.ro" in src:
            # Get original quality version
            original_src = re.sub(r"/slir/w\d+/", "/", src)
            if original_src not in gallery_images:
                gallery_images.append(original_src)

    # Also find images from links to original quality
    for a_tag in soup.select("a.cs-product-gallery__image"):
        href = a_tag.get("href", "")
        if href and "contentspeed.ro" in href and href not in gallery_images:
            gallery_images.append(href)

    if gallery_images:
        result["image_urls"] = gallery_images[:5]
    elif result["image_url_main"]:
        result["image_urls"] = [result["image_url_main"]]

    # Extract product codes
    page_text = soup.get_text()
    code_match = re.search(r"Cod produs Romstal:\s*(\S+)", page_text)
    if code_match:
        result["romstal_code"] = code_match.group(1)

    supplier_match = re.search(r"Cod furnizor:\s*(\S+)", page_text)
    if supplier_match:
        result["supplier_code_web"] = supplier_match.group(1)

    # Extract description - find the description tab content
    desc_section = None
    for heading in soup.find_all(["h2", "h3"]):
        if "Descriere" in heading.get_text():
            desc_section = heading.find_parent("div", class_=True)
            break

    if desc_section:
        # Get text content, preserving paragraphs
        desc_parts = []
        for elem in desc_section.find_all(["p", "div", "li"]):
            text = elem.get_text(strip=True)
            if text and len(text) > 10:
                desc_parts.append(text)
        result["description_long"] = "\n\n".join(desc_parts)

    # If no structured description found, try og:description
    if not result["description_long"]:
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            result["description_long"] = og_desc.get("content", "")

    # Extract specifications from characteristics table
    specs_table = None
    for heading in soup.find_all(["h2", "h3"]):
        if "Caracteristici" in heading.get_text():
            parent = heading.find_parent("div", class_=True)
            if parent:
                specs_table = parent.find("table")
            break

    if not specs_table:
        # Try finding any table with spec-like content
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if rows and len(rows) > 2:
                first_cell = rows[0].find("td")
                if first_cell:
                    specs_table = table
                    break

    if specs_table:
        for row in specs_table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                if key and value:
                    result["specifications"][key] = value

    return result


def scrape_products(products: list[dict]) -> list[dict]:
    """
    Scrape romstal.ro for each product using its Romanian description.

    Args:
        products: List of mapped product dicts (from data_mapper)

    Returns:
        Same products list with scraped_data added to each.
    """
    for i, product in enumerate(products):
        code = product["product_code"]
        desc_ro = product.get("long_desc_ro", "")

        print(f"\n[{i+1}/{len(products)}] Scraping {code}...")

        if not desc_ro:
            print("  No Romanian description - skipping scrape")
            product["scraped_data"] = None
            product["scrape_status"] = "no_description"
            continue

        # Construct URL from description
        url = construct_product_url(desc_ro)
        print(f"  URL: {url}")

        # Fetch the page
        html = fetch_page(url)

        if html:
            parsed = parse_product_page(html, url)
            if parsed["description_long"] or parsed["specifications"]:
                product["scraped_data"] = parsed
                product["scrape_status"] = "success"
                print(f"  OK: {len(parsed['description_long'])} chars description, "
                      f"{len(parsed['specifications'])} specs, "
                      f"{len(parsed['image_urls'])} images")
            else:
                # Page loaded but no product content - might be wrong URL
                product["scraped_data"] = parsed
                product["scrape_status"] = "partial"
                print(f"  PARTIAL: Page loaded but limited content extracted")
        else:
            product["scraped_data"] = None
            product["scrape_status"] = "failed"
            print(f"  FAILED: Could not fetch {url}")

        # Rate limiting - be polite to romstal.ro
        if i < len(products) - 1:
            time.sleep(2)

    return products


def run():
    """Main entry: load mapped products, scrape, save results."""
    mapped_path = TMP_DIR / "mapped_products.json"
    if not mapped_path.exists():
        raise FileNotFoundError("Run data_mapper first to generate mapped_products.json")

    with open(mapped_path, encoding="utf-8") as f:
        products = json.load(f)

    print(f"Loaded {len(products)} mapped products")
    products = scrape_products(products)

    # Save enriched data
    output_path = TMP_DIR / "scraped_products.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"\nSaved scraped data to {output_path}")

    # Summary
    success = sum(1 for p in products if p.get("scrape_status") == "success")
    partial = sum(1 for p in products if p.get("scrape_status") == "partial")
    failed = sum(1 for p in products if p.get("scrape_status") == "failed")
    skipped = sum(1 for p in products if p.get("scrape_status") == "no_description")
    print(f"Summary: {success} scraped, {partial} partial, {failed} failed, {skipped} skipped")


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    run()
