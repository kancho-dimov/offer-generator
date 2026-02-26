"""
Cascading discount calculator for the offer generation system.

Applies compound discounts in this order:
1. Best non-stackable rule (highest discount)
2. All matching stackable rules
3. Customer tier discount
4. Custom per-offer discounts

Each discount compounds on the remaining amount (multiplicative stacking).

Usage:
    from tools.discount_engine import load_customer, load_discount_rules, calculate_offer_lines
"""

from __future__ import annotations

from datetime import date, datetime
from tools.sheets_api import read_sheet


def _norm(code: str) -> str:
    """Normalize a product code by removing all internal and surrounding spaces."""
    return code.replace(" ", "").strip() if code else ""


MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"
PRICELIST_ID = "1gx6xQoGtH1KCPRq7ZSJe1ZmD2kvIQh8g3nzm8eFzXLk"
VAT_RATE = 0.20


def load_discount_rules() -> list[dict]:
    """Read active discount rules from Discount_Rules sheet."""
    rows = read_sheet(MASTER_CATALOG_ID, "'Discount_Rules'!A1:L")
    if not rows or len(rows) < 2:
        return []
    header = rows[0]
    rules = []
    for row in rows[1:]:
        # Pad row to header length
        row += [""] * (len(header) - len(row))
        rule = dict(zip(header, row))
        rules.append(rule)
    return rules


def load_customer(customer_id: str) -> dict:
    """Read a specific customer from Customers sheet."""
    rows = read_sheet(MASTER_CATALOG_ID, "'Customers'!A1:N")
    if not rows or len(rows) < 2:
        raise ValueError("Customers sheet is empty")
    header = rows[0]
    for row in rows[1:]:
        row += [""] * (len(header) - len(row))
        customer = dict(zip(header, row))
        if customer.get("customer_id") == customer_id:
            return customer
    raise ValueError(f"Customer '{customer_id}' not found")


def _load_pricelist_map() -> dict[str, dict]:
    """Load live prices from synced pricelist, keyed by material code."""
    rows = read_sheet(PRICELIST_ID, "'Sheet1'!A:K")
    if not rows or len(rows) < 2:
        return {}
    data = {}
    for row in rows[1:]:
        if len(row) < 5:
            continue
        code = _norm(row[2])  # Материал (col C)
        data[code] = {
            "base_price": row[4] if len(row) > 4 else "",     # Сума без ДДС
            "currency": row[5] if len(row) > 5 else "",        # Ед-ца (EUR)
        }
    return data


def load_products(product_codes: list[str]) -> dict[str, dict]:
    """Read products from Master_Database + live prices from pricelist."""
    rows = read_sheet(MASTER_CATALOG_ID, "'Master_Database'!A1:O")
    if not rows or len(rows) < 2:
        return {}
    header = rows[0]
    products = {}
    for row in rows[1:]:
        row += [""] * (len(header) - len(row))
        product = dict(zip(header, row))
        code = product.get("product_code", "")
        if code in product_codes:
            products[code] = product

    # Merge live prices from pricelist
    pricelist = _load_pricelist_map()
    for code, product in products.items():
        pl = pricelist.get(_norm(code))
        if pl:
            product["base_price"] = pl.get("base_price", "")
            product["currency"] = pl.get("currency", "")
        else:
            product.setdefault("base_price", "")
            product.setdefault("currency", "")

    return products


def _parse_date(date_str: str) -> date | None:
    """Parse a date string (YYYY-MM-DD) or return None if empty/invalid."""
    if not date_str or not date_str.strip():
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def _is_rule_active(rule: dict, today: date) -> bool:
    """Check if a rule is currently active based on its dates and active flag."""
    if rule.get("active", "").upper() != "TRUE":
        return False
    valid_from = _parse_date(rule.get("valid_from", ""))
    valid_until = _parse_date(rule.get("valid_until", ""))
    if valid_from and today < valid_from:
        return False
    if valid_until and today > valid_until:
        return False
    return True


def get_applicable_rules(
    product: dict, quantity: int, rules: list[dict], today: date | None = None
) -> tuple[list[dict], list[dict]]:
    """
    Filter rules that apply to a product at a given quantity.

    Returns:
        (non_stackable_rules, stackable_rules) — both sorted by priority.
    """
    if today is None:
        today = date.today()

    non_stackable = []
    stackable = []

    for rule in rules:
        if not _is_rule_active(rule, today):
            continue

        # Check minimum quantity
        min_qty = int(rule.get("min_quantity", "1") or "1")
        if quantity < min_qty:
            continue

        # Check target match
        rule_type = rule.get("rule_type", "").lower()
        target = rule.get("target_value", "").strip()

        matched = False
        if rule_type == "brand" and product.get("brand", "").strip().lower() == target.lower():
            matched = True
        elif rule_type == "category" and product.get("category", "").strip().lower() == target.lower():
            matched = True
        elif rule_type == "subcategory" and product.get("subcategory", "").strip().lower() == target.lower():
            matched = True
        elif rule_type == "product" and _norm(product.get("product_code", "")) == _norm(target):
            matched = True

        if not matched:
            continue

        is_stackable = rule.get("stackable", "").upper() == "TRUE"
        if is_stackable:
            stackable.append(rule)
        else:
            non_stackable.append(rule)

    # Sort by priority (lower number = higher priority = applied first)
    key = lambda r: int(r.get("priority", "99") or "99")
    non_stackable.sort(key=key)
    stackable.sort(key=key)

    return non_stackable, stackable


def calculate_price(
    base_price: float,
    customer: dict,
    non_stackable_rules: list[dict],
    stackable_rules: list[dict],
    custom_discounts: list[dict] | None = None,
) -> dict:
    """
    Calculate the final price after compound discounts + VAT.

    Discount order:
    1. Best non-stackable rule (highest discount value)
    2. All stackable rules (compounded)
    3. Customer tier discount
    4. Custom offer-level discounts

    Returns dict with full price breakdown.
    """
    discounts_applied = []
    price = base_price

    # 1. Best non-stackable rule
    if non_stackable_rules:
        best = max(non_stackable_rules, key=lambda r: float(r.get("discount_value", "0") or "0"))
        pct = float(best.get("discount_value", "0") or "0")
        if pct > 0:
            price *= (1 - pct / 100)
            discounts_applied.append({
                "name": best.get("rule_name", "Rule"),
                "type": best.get("rule_type", ""),
                "pct": pct,
            })

    # 2. All stackable rules
    for rule in stackable_rules:
        pct = float(rule.get("discount_value", "0") or "0")
        if pct > 0:
            price *= (1 - pct / 100)
            discounts_applied.append({
                "name": rule.get("rule_name", "Rule"),
                "type": rule.get("rule_type", ""),
                "pct": pct,
            })

    # 3. Customer tier discount
    customer_pct = float(customer.get("default_discount_pct", "0") or "0")
    if customer_pct > 0:
        price *= (1 - customer_pct / 100)
        discounts_applied.append({
            "name": f"{customer.get('discount_tier', '').capitalize()} tier",
            "type": "customer",
            "pct": customer_pct,
        })

    # 4. Custom discounts
    if custom_discounts:
        for cd in custom_discounts:
            pct = float(cd.get("percentage", 0))
            if pct > 0:
                price *= (1 - pct / 100)
                discounts_applied.append({
                    "name": cd.get("name", "Custom"),
                    "type": "custom",
                    "pct": pct,
                })

    net_excl_vat = round(price, 2)
    vat_amount = round(net_excl_vat * VAT_RATE, 2)
    net_incl_vat = round(net_excl_vat + vat_amount, 2)

    # Effective compound discount — use exact formula to avoid rounding artifacts
    if discounts_applied:
        compound = 1.0
        for d in discounts_applied:
            compound *= (1 - d["pct"] / 100)
        total_discount_pct = round((1 - compound) * 100, 2)
    else:
        total_discount_pct = 0

    return {
        "base_price": base_price,
        "discounts_applied": discounts_applied,
        "total_discount_pct": total_discount_pct,
        "net_price_excl_vat": net_excl_vat,
        "vat_amount": vat_amount,
        "net_price_incl_vat": net_incl_vat,
    }


def calculate_offer_lines(
    items: list[dict],
    customer: dict,
    rules: list[dict],
    custom_discounts: list[dict] | None = None,
    products: dict[str, dict] | None = None,
) -> dict:
    """
    Calculate all line items and totals for an offer.

    Args:
        items: list of {"product_code": "...", "quantity": N}
        customer: customer dict from load_customer()
        rules: all rules from load_discount_rules()
        custom_discounts: optional per-offer custom discounts
        products: pre-loaded products dict (if None, loads from sheet)

    Returns:
        {
            "lines": [ { product info + price breakdown + line totals } ],
            "subtotal_excl_vat": ...,
            "total_vat": ...,
            "grand_total_incl_vat": ...,
        }
    """
    if products is None:
        codes = [item["product_code"] for item in items]
        products = load_products(codes)

    lines = []
    subtotal_excl = 0
    total_vat = 0

    for item in items:
        code = item["product_code"]
        qty = int(item.get("quantity", 1))
        product = products.get(code)

        if not product:
            lines.append({
                "product_code": code,
                "error": f"Product '{code}' not found in Master_Database",
            })
            continue

        base_price = float(str(product.get("base_price", "0") or "0").replace(",", ""))

        # Per-product discount override: skip rules + customer tier, apply fixed %
        # Custom offer-level discounts still compound on top
        discount_override = item.get("discount_override")
        if discount_override is not None and float(discount_override) > 0:
            override_pct = float(discount_override)
            price = base_price * (1 - override_pct / 100)
            discounts_applied = [{"name": "Ръчна отстъпка", "type": "override", "pct": override_pct}]

            # Apply custom offer-level discounts on top of override
            if custom_discounts:
                for cd in custom_discounts:
                    pct = float(cd.get("percentage", 0))
                    if pct > 0:
                        price *= (1 - pct / 100)
                        discounts_applied.append({
                            "name": cd.get("name", "Custom"),
                            "type": "custom",
                            "pct": pct,
                        })

            net_excl = round(price, 2)
            vat_amt = round(net_excl * VAT_RATE, 2)
            # Use exact compound formula to avoid rounding artifacts
            compound = 1.0
            for d in discounts_applied:
                compound *= (1 - d["pct"] / 100)
            total_disc = round((1 - compound) * 100, 2)
            pricing = {
                "base_price": base_price,
                "discounts_applied": discounts_applied,
                "total_discount_pct": total_disc,
                "net_price_excl_vat": net_excl,
                "vat_amount": vat_amt,
                "net_price_incl_vat": round(net_excl + vat_amt, 2),
            }
        else:
            non_stack, stack = get_applicable_rules(product, qty, rules)
            pricing = calculate_price(base_price, customer, non_stack, stack, custom_discounts)

        line_total_excl = round(pricing["net_price_excl_vat"] * qty, 2)
        line_vat = round(pricing["vat_amount"] * qty, 2)
        line_total_incl = round(pricing["net_price_incl_vat"] * qty, 2)

        subtotal_excl += line_total_excl
        total_vat += line_vat

        lines.append({
            "product_code": code,
            "name": product.get("name", ""),
            "brand": product.get("brand", ""),
            "category": product.get("category", ""),
            "subcategory": product.get("subcategory", ""),
            "image_url": product.get("image_url", ""),
            "quantity": qty,
            **pricing,
            "line_total_excl_vat": line_total_excl,
            "line_vat": line_vat,
            "line_total_incl_vat": line_total_incl,
        })

    return {
        "lines": lines,
        "subtotal_excl_vat": round(subtotal_excl, 2),
        "total_vat": round(total_vat, 2),
        "grand_total_incl_vat": round(subtotal_excl + total_vat, 2),
    }


if __name__ == "__main__":
    import json
    import sys
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("=== Discount Engine Test ===\n")

    customer = load_customer("CUST-001")
    print(f"Customer: {customer['company_name']} ({customer['discount_tier']} tier, {customer['default_discount_pct']}%)")

    rules = load_discount_rules()
    print(f"Loaded {len(rules)} discount rules\n")

    test_items = [
        {"product_code": "32FR8050", "quantity": 10},
        {"product_code": "44NP0003", "quantity": 5},
        {"product_code": "34HR6918", "quantity": 1},
    ]

    result = calculate_offer_lines(
        items=test_items,
        customer=customer,
        rules=rules,
        custom_discounts=[{"name": "Project discount", "percentage": 3}],
    )

    for line in result["lines"]:
        if "error" in line:
            print(f"  ERROR: {line['error']}")
            continue
        print(f"  {line['product_code']} - {line['name']}")
        print(f"    Base: {line['base_price']:.2f} EUR x {line['quantity']}")
        for d in line["discounts_applied"]:
            print(f"    Discount: {d['name']} ({d['type']}) -{d['pct']}%")
        print(f"    Total discount: {line['total_discount_pct']:.2f}%")
        print(f"    Net unit: {line['net_price_excl_vat']:.2f} / incl VAT: {line['net_price_incl_vat']:.2f}")
        print(f"    Line total: {line['line_total_excl_vat']:.2f} / incl VAT: {line['line_total_incl_vat']:.2f}")
        print()

    print(f"  Subtotal (excl VAT): {result['subtotal_excl_vat']:.2f} EUR")
    print(f"  VAT (20%):           {result['total_vat']:.2f} EUR")
    print(f"  Grand Total:         {result['grand_total_incl_vat']:.2f} EUR")
