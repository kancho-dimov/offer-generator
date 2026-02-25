"""
Search products in the Master_Database by code, name, brand, or category.

Returns matching products with live prices (from synced pricelist),
image URLs, and logistics data (pack sizes).
Caches the product list for fast repeated searches within the same session.

Usage:
    from tools.product_search import search_products, load_all_products
    results = search_products("radiator")
    results = search_products("32FR8050")
"""

from tools.sheets_api import read_sheet


def _norm(code: str) -> str:
    """Normalize a product code by removing all internal and surrounding spaces."""
    return code.replace(" ", "").strip() if code else ""


MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"
PRICELIST_ID = "1gx6xQoGtH1KCPRq7ZSJe1ZmD2kvIQh8g3nzm8eFzXLk"
NOMENCLATURES_ID = "1qfuXFqwwUGi-ovm_Wu5O1ptwZA65ARDIf2z91X-syhg"
NOMENCLATURES_TAB = "Compatibilitati - 2025-07-07T16"

_product_cache: list[dict] | None = None
_logistics_cache: dict[str, dict] | None = None
_pricelist_cache: dict[str, dict] | None = None
_nomenclature_brands_cache: dict[str, str] | None = None


def _load_pricelist() -> dict[str, dict]:
    """Load live prices from the synced pricelist, keyed by material code."""
    global _pricelist_cache
    if _pricelist_cache is not None:
        return _pricelist_cache

    rows = read_sheet(PRICELIST_ID, "'Sheet1'!A:K")
    if not rows or len(rows) < 2:
        _pricelist_cache = {}
        return _pricelist_cache

    data = {}
    for row in rows[1:]:
        if len(row) < 5:
            continue
        code = _norm(row[2])  # Материал (col C)
        data[code] = {
            "base_price": row[4] if len(row) > 4 else "",     # Сума без ДДС
            "currency": row[5] if len(row) > 5 else "",        # Ед-ца (EUR)
            "measure_unit": row[7] if len(row) > 7 else "",    # МЕ
        }

    _pricelist_cache = data
    return _pricelist_cache


def _load_nomenclature_brands() -> dict[str, str]:
    """Load supplier names from nomenclature keyed by SAP code (col B → col J)."""
    global _nomenclature_brands_cache
    if _nomenclature_brands_cache is not None:
        return _nomenclature_brands_cache

    rows = read_sheet(NOMENCLATURES_ID, f"'{NOMENCLATURES_TAB}'!A:J")
    data: dict[str, str] = {}
    for row in rows[1:]:
        code = _norm(row[1]) if len(row) > 1 else ""
        name = row[9].strip() if len(row) > 9 else ""
        if code and name:
            data[code] = name

    _nomenclature_brands_cache = data
    return data


def _load_logistics() -> dict[str, dict]:
    """Load logistics data keyed by product_code."""
    global _logistics_cache
    if _logistics_cache is not None:
        return _logistics_cache

    rows = read_sheet(MASTER_CATALOG_ID, "'Logistics'!A1:H")
    if not rows or len(rows) < 2:
        _logistics_cache = {}
        return _logistics_cache

    headers = rows[0]
    data = {}
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        row += [""] * (len(headers) - len(row))
        entry = dict(zip(headers, row))
        data[_norm(entry["product_code"])] = entry

    _logistics_cache = data
    return _logistics_cache


def load_all_products(force_reload: bool = False) -> list[dict]:
    """Load all products from Master_Database + live prices + logistics."""
    global _product_cache
    if _product_cache is not None and not force_reload:
        return _product_cache

    rows = read_sheet(MASTER_CATALOG_ID, "'Master_Database'!A1:O")
    if not rows or len(rows) < 2:
        _product_cache = []
        return _product_cache

    headers = rows[0]
    pricelist = _load_pricelist()
    logistics = _load_logistics()

    products = []
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        row += [""] * (len(headers) - len(row))
        product = dict(zip(headers, row))
        norm_code = _norm(product["product_code"])

        # Prices come exclusively from the live synced pricelist
        pl = pricelist.get(norm_code)
        if pl:
            product["base_price"] = pl["base_price"]
            product["currency"] = pl["currency"]
            if not product.get("measure_unit"):
                product["measure_unit"] = pl["measure_unit"]
        else:
            product["base_price"] = ""
            product["currency"] = ""

        # Merge logistics data (pack sizes only)
        logi = logistics.get(norm_code)
        if logi:
            product["pcs_per_carton"] = logi.get("pcs_per_carton", "")
            product["pcs_per_pallet"] = logi.get("pcs_per_pallet", "")
            product["base_unit"] = logi.get("base_unit", "")
        else:
            product["pcs_per_carton"] = ""
            product["pcs_per_pallet"] = ""
            product["base_unit"] = ""

        products.append(product)

    # Deduplicate by product_code — prefer enriched entries (catalog_ready=TRUE)
    deduped: dict[str, dict] = {}
    for p in products:
        code = p["product_code"]
        if code not in deduped:
            deduped[code] = p
        elif p.get("catalog_ready", "").upper() == "TRUE":
            deduped[code] = p
    products = list(deduped.values())

    # Normalize brand names for unenriched products:
    # 1. Pull supplier_name from the nomenclature (authoritative source).
    # 2. Strip legal-entity suffixes unconditionally.
    # 3. If an enriched (Claude-cleaned) canonical form exists, use it;
    #    otherwise keep the suffix-stripped name.
    _SUFFIXES = frozenset({
        "INDUSTRIES", "INDUSTRY", "INDUSTRIE",
        "SRL", "SA", "SPA", "GMBH", "LTD", "LLC",
        "AG", "NV", "BV", "OOD", "EOOD", "AD",
    })

    def _strip_suffixes(name: str) -> str:
        parts = name.split()
        # Remove dots to handle "S.P.A", "S.R.L", "S.A." etc.
        while parts and parts[-1].upper().replace(".", "") in _SUFFIXES:
            parts.pop()
        return " ".join(parts)

    # Build canonical map from enriched products (stripped-uppercase → clean brand)
    # "First wins" — prevents later inconsistent casing from overwriting
    canonical_map: dict[str, str] = {}
    for p in products:
        if p.get("catalog_ready", "").upper() == "TRUE" and p.get("brand"):
            key = _strip_suffixes(p["brand"].strip()).upper()
            if key not in canonical_map:
                canonical_map[key] = p["brand"].strip()

    nom_brands = _load_nomenclature_brands()

    for p in products:
        if p.get("catalog_ready", "").upper() == "TRUE":
            # Unify casing across catalog_ready products (e.g. "DAB Pumps" → "DAB PUMPS")
            brand = p.get("brand", "").strip()
            if brand:
                key = _strip_suffixes(brand).upper()
                p["brand"] = canonical_map.get(key, brand)
            continue  # don't overwrite with nomenclature data
        code = p["product_code"]
        # Prefer nomenclature supplier_name; fall back to whatever is in Master_Database
        raw = nom_brands.get(_norm(code)) or p.get("brand", "")
        if not raw:
            continue
        stripped = _strip_suffixes(raw.strip())
        if not stripped:
            continue
        # Use the enriched canonical form if one exists; otherwise use stripped name
        p["brand"] = canonical_map.get(stripped.upper(), stripped)

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
        if _norm(p.get("product_code", "")) == _norm(product_code):
            return p
    return None


def invalidate_cache():
    """Clear all caches (e.g., after updating Master_Database)."""
    global _product_cache, _logistics_cache, _pricelist_cache, _nomenclature_brands_cache
    _product_cache = None
    _logistics_cache = None
    _pricelist_cache = None
    _nomenclature_brands_cache = None


if __name__ == "__main__":
    import io
    import sys

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    query = sys.argv[1] if len(sys.argv) > 1 else ""
    print(f"Searching for: '{query}'\n")

    results = search_products(query)
    for p in results:
        price = p.get("base_price", "?")
        carton = p.get("pcs_per_carton", "")
        carton_info = f"  [📦 {carton} бр/кш]" if carton and carton != "0" else ""
        print(f"  {p['product_code']}  {p.get('name', '')}  [{p.get('brand', '')}]  {price} {p.get('currency', '')}{carton_info}")

    print(f"\n{len(results)} results found")
