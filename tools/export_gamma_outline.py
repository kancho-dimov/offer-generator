"""
Export offer data as a markdown outline for presentation tools (gamma.app, Google Slides, etc.)

Reads the saved offer data from .tmp/{offer_number}_data.json and generates a clean
markdown outline suitable for AI presentation generators.

Usage:
    python -m tools.export_gamma_outline OFR-2026-001
    python -m tools.export_gamma_outline             # exports the most recent offer
"""

import io
import json
import sys
from pathlib import Path

if "streamlit" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TMP_DIR = Path(__file__).resolve().parent.parent / ".tmp"


def find_latest_offer_data() -> Path:
    """Find the most recent offer data file in .tmp/."""
    files = sorted(TMP_DIR.glob("*_data.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError("No offer data files found in .tmp/")
    return files[0]


def export_outline(offer_number: str | None = None) -> str:
    """
    Generate a markdown outline from offer data.

    Args:
        offer_number: e.g. "OFR-2026-001". If None, uses the most recent offer.

    Returns:
        Path to the generated markdown file.
    """
    # Find the data file
    if offer_number:
        data_file = TMP_DIR / f"{offer_number}_data.json"
        if not data_file.exists():
            raise FileNotFoundError(f"Offer data not found: {data_file}")
    else:
        data_file = find_latest_offer_data()

    with open(data_file, encoding="utf-8") as f:
        data = json.load(f)

    offer_num = data["offer_number"]
    mode = data["mode"]
    customer = data["customer"]
    branding = data["branding"]
    result = data["result"]
    request = data["request"]

    lines = result["lines"]
    company_name = branding.get("company_name", "")
    customer_name = customer.get("company_name", "")

    md = []

    # Title
    if mode == "offer":
        md.append(f"# Оферта {offer_num} | {customer_name}\n")
    else:
        md.append(f"# Ценова листа {offer_num} | {customer_name}\n")

    # Company intro
    md.append(f"## {company_name}\n")
    md.append(f"- {branding.get('company_address', '')}")
    md.append(f"- Тел: {branding.get('company_phone', '')} | Email: {branding.get('company_email', '')}")
    md.append(f"- {branding.get('company_website', '')}")
    md.append(f"- ЕИК/ДДС: {branding.get('company_vat_id', '')}")
    md.append("")

    # Customer
    md.append(f"## Клиент: {customer_name}\n")
    md.append(f"- Лице за контакт: {customer.get('contact_name', '')}")
    md.append(f"- Адрес: {customer.get('address', '')}")
    md.append(f"- Тел: {customer.get('phone', '')} | Email: {customer.get('email', '')}")
    md.append("")

    notes = request.get("notes", "")
    if notes:
        md.append(f"*{notes}*\n")

    # Products
    md.append("## Продукти\n")

    for line in lines:
        if "error" in line:
            md.append(f"- **{line['product_code']}**: {line['error']}\n")
            continue

        md.append(f"### {line['name']}")
        md.append(f"- **Марка:** {line['brand']}")
        if line.get("category"):
            md.append(f"- **Категория:** {line['category']}")

        if mode == "offer":
            md.append(f"- **Количество:** {line['quantity']}")
            md.append(f"- **Единична цена:** {line['net_price_excl_vat']:.2f} EUR (без ДДС)")
            md.append(f"- **Общо:** {line['line_total_excl_vat']:.2f} EUR (без ДДС)")
        else:
            md.append(f"- **Цена:** {line['net_price_excl_vat']:.2f} EUR (без ДДС)")

        md.append("")

    # Pricing summary (offer mode only)
    if mode == "offer":
        md.append("## Ценова справка\n")

        # Table
        md.append("| Продукт | К-во | Ед. цена (EUR) | Общо (EUR) |")
        md.append("|---------|------|----------------|------------|")
        for line in lines:
            if "error" in line:
                continue
            md.append(
                f"| {line['name'][:40]} | {line['quantity']} | "
                f"{line['net_price_excl_vat']:.2f} | {line['line_total_excl_vat']:.2f} |"
            )
        md.append("")
        md.append(f"- **Междинна сума (без ДДС):** {result['subtotal_excl_vat']:.2f} EUR")
        md.append(f"- **ДДС (20%):** {result['total_vat']:.2f} EUR")
        md.append(f"- **ОБЩА СУМА (с ДДС):** {result['grand_total_incl_vat']:.2f} EUR")
        md.append("")

    # Terms
    md.append("## Условия\n")
    terms = branding.get("offer_terms", "")
    if terms:
        for sentence in terms.split(". "):
            sentence = sentence.strip().rstrip(".")
            if sentence:
                md.append(f"- {sentence}")
    md.append("")

    disclaimer = branding.get("offer_disclaimer", "")
    if disclaimer:
        md.append(f"*{disclaimer}*\n")

    # Contact
    md.append("## Контакт\n")
    md.append(f"- {company_name}")
    md.append(f"- {branding.get('company_address', '')}")
    md.append(f"- Тел: {branding.get('company_phone', '')} | Email: {branding.get('company_email', '')}")
    md.append(f"- {branding.get('company_website', '')}")

    # Write file
    content = "\n".join(md)
    output_file = TMP_DIR / f"{offer_num}_gamma.md"
    output_file.write_text(content, encoding="utf-8")

    print(f"Exported: {output_file}")
    print(f"  Mode: {mode}")
    print(f"  Products: {len([l for l in lines if 'error' not in l])}")
    if mode == "offer":
        print(f"  Grand total: {result['grand_total_incl_vat']:.2f} EUR")

    return str(output_file)


if __name__ == "__main__":
    offer_num = sys.argv[1] if len(sys.argv) > 1 else None
    export_outline(offer_num)
