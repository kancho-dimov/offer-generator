"""
Search products in the Master_Database by code, name, brand, or category.

Returns matching products with prices and image URLs.
Caches the product list for fast repeated searches within the same session.

Usage:
    from tools.product_search import search_products, load_all_products
    results = search_products("radiator")
    results = search_products("32FR8050")
"""

from tools.sheets_api import read_sheet

MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"

_product_cache: list[dict] | None = None


def load_all_products(force_reload: bool = False) -> list[dict]:
    """Load all products from Master_Database. Caches for performance."""
    global _product_cache
    if _product_cache is not None and not force_reload:
        return _product_cache

    rows = read_sheet(MASTER_CATALOG_ID, "'Master_Database'!A1:Q")
    if not rows or len(rows) < 2:
        _product_cache = []
        return _product_cache

    headers = rows[0]
    products = []
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        row += [""] * (len(headers) - len(row))
        product = dict(zip(headers, row))
        products.append(product)

    _product_cache = products
    return _product_cache


def search_products(query: str, limit: int = 50) -> list[dict]:
    """Search products by code, name, brand, or category.

    The query is case-insensitive and matches any field containing the text.
    Returns up to `limit` results.
    """
    products = load_all_products()
    if not query or not query.strip():
        return products[:limit]

    q = query.strip().lower()
    results = []

    for p in products:
        searchable = " ".join([
            p.get("product_code", ""),
            p.get("supplier_code", ""),
            p.get("name", ""),
            p.get("brand", ""),
            p.get("category", ""),
            p.get("subcategory", ""),
        ]).lower()

        if q in searchable:
            results.append(p)
            if len(results) >= limit:
                break

    return results


def get_product(product_code: str) -> dict | None:
    """Get a single product by exact code."""
    products = load_all_products()
    for p in products:
        if p.get("product_code", "").strip() == product_code.strip():
            return p
    return None


def invalidate_cache():
    """Clear the product cache (e.g., after updating Master_Database)."""
    global _product_cache
    _product_cache = None


if __name__ == "__main__":
    import io
    import sys

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    query = sys.argv[1] if len(sys.argv) > 1 else ""
    print(f"Searching for: '{query}'\n")

    results = search_products(query)
    for p in results:
        price = p.get("base_price", "?")
        print(f"  {p['product_code']}  {p.get('name', '')}  [{p.get('brand', '')}]  {price} {p.get('currency', '')}")

    print(f"\n{len(results)} results found")
