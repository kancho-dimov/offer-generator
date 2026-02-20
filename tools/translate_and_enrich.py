"""
Translates scraped Romanian product data to Bulgarian using Claude API.
Uses proper HVAC/plumbing terminology.

Usage:
    python -m tools.translate_and_enrich
"""

import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

TMP_DIR = Path(__file__).resolve().parent.parent / ".tmp"

_ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
_ANTHROPIC_MODEL = "claude-sonnet-4-6"
_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


def _claude(system: str, user: str, max_tokens: int = 1500) -> str:
    """Call Anthropic REST API directly via httpx (avoids SDK connection issues)."""
    with httpx.Client(timeout=120.0) as c:
        resp = c.post(
            _ANTHROPIC_URL,
            headers={
                "x-api-key": _ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": _ANTHROPIC_MODEL,
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

SYSTEM_PROMPT = """You are a professional translator specializing in HVAC, plumbing, and heating
equipment terminology. You translate from Romanian to Bulgarian for a B2B product catalog.

## GLOSSARY (RO → BG) — ALWAYS use these exact terms:

### Products
- Calorifer / Radiator → Радиатор
- Element calorifer → Радиаторен елемент
- Centrală termică → Газов котел
- Centrală în condensare → Кондензен котел
- Boiler → Бойлер
- Pompă de căldură → Термопомпа
- Baterie (baie/bucătărie) → Смесител
- Aerator → Аератор
- Portprosop → Лира за баня
- Panou solar → Слънчев колектор
- Consolă → Конзола
- Reducție → Редукция

### Technical terms
- Agent termic → Топлоносител
- Putere termică / Randament termic → Топлинна мощност / Топлоотдаване (НЕ "топлоотдача")
- Presiune de lucru → Работно налягане
- Presiune de probă → Изпитвателно налягане
- Distanță între axe → Междуосие
- Racord → Присъединяване
- Debit → Дебит
- Încălzire în pardoseală → Подово отопление
- Vas de expansiune → Разширителен съд
- Aerisitor / Dezaerisitor → Обезвъздушител
- Supapă de siguranță → Предпазен клапан
- Cap termostatat → Термостатична глава
- Conductă / Țeavă → Тръба
- Fitinguri → Фитинги
- Robinet → Кран / Вентил
- Vopsea în pulbere → Прахово боядисване
- Rezistent la coroziune → Устойчив на корозия
- Oțel → Стомана (adj: стоманен/стоманена)
- Aluminiu → Алуминий (adj: алуминиев/алуминиева)
- Alamă → Месинг

### Categories (RO → BG)
- RADIATOARE → Радиатори
- CENTRALE MURALE → Стенни котли
- BATERII → Смесители
- POMPE, VASE DE EXPANSIUNE → Помпи и разширителни съдове
- SISTEME DE INCALZIRE IN PARDOSEALA → Подово отопление
- CANALIZARI SI SCURGERI → Канализация и отводняване
- ROBINETI, RACORDURI, ACCESORII → Кранове, фитинги, аксесоари
- FILTRE, CONTOARE, REZERVOARE → Филтри, водомери, резервоари
- KLIMA → Климатизация
- COSURI DE FUM SI TUBULATURA → Комини и димоотводи
- IZOLATIE → Изолация
- PREPARARE ACM → Подгряване на БГВ

## STRICT RULES:
- NEVER use "топлоотдача" — ALWAYS use "топлоотдаване"
- NEVER use "висококвалитетна" or mixed-language words — use "висококачествен/а"
- NEVER mix Cyrillic and Latin in one word (e.g. "леснаdemонтаж" is WRONG — write "лесен демонтаж")
- ALL output text MUST be 100% in Bulgarian Cyrillic. No Latin characters except brand names and units.
- Keep brand names UNCHANGED: Vaillant, Kermi, Vision, Cordivari, NEOPERL, ECCORAD, etc.
- Keep units and numbers as-is: W, kW, bar, mm, °C, л/мин
- Use natural, professional Bulgarian — no direct word-for-word translation"""


def translate_product(product: dict) -> dict:
    """
    Use Claude to generate Bulgarian translations and enriched content for a product.

    Args:
        product: Product dict with scraped_data

    Returns:
        Dict with translated/enriched fields ready for master catalog.
    """
    scraped = product.get("scraped_data") or {}
    desc_ro = scraped.get("description_long", "")
    specs = scraped.get("specifications", {})
    name_bg_existing = product.get("name_bg", "")

    # Truncate very long descriptions to save tokens
    if len(desc_ro) > 3000:
        desc_ro = desc_ro[:3000] + "..."

    specs_text = "\n".join(f"- {k}: {v}" for k, v in specs.items()) if specs else "N/A"

    # Brand and categories from nomenclature (Romanian)
    brand_raw = scraped.get("brand", "") or product.get("supplier_name", "")
    category_ro = product.get("category", "")
    class_ro = product.get("class_name", "")
    subclass_ro = product.get("subclass", "")

    prompt = f"""Translate and enrich the following HVAC product for a Bulgarian B2B catalog.

**Existing Bulgarian name:** {name_bg_existing}
**Brand (keep unchanged if international, translate if Romanian):** {brand_raw}
**Category (Romanian):** {category_ro}
**Class (Romanian):** {class_ro}
**Subclass (Romanian):** {subclass_ro}

**Romanian description from website:**
{desc_ro}

**Technical specifications (Romanian):**
{specs_text}

Return a JSON object with these fields:

1. "brand" - Brand name. Keep international brands as-is (Kermi, Vaillant, Vision, etc.). Only translate if it's a generic Romanian term.
2. "category" - Translate the category to Bulgarian (e.g. RADIATOARE → Радиатори, CENTRALE MURALE → Стенни котли, BATERII → Смесители)
3. "subcategory" - Translate class/subclass to Bulgarian (e.g. ALUMINIU → Алуминиеви, OTEL → Стоманени)
4. "short_description" - One sentence, max 150 chars, what the product IS. No fluff.
5. "long_description" - 2-3 focused paragraphs. Key benefits, applications, why a professional would choose this.
6. "features" - Exactly 3-4 most distinctive features. Each under 10 words. Each on a new line starting with •. Example: "• Двупанелна конструкция с 2 конвектора\n• Работно налягане 10 bar\n• RAL 9016 бяло прахово покритие"
7. "specifications" - Only essential technical specs. Each on a new line starting with •, format "• Ключ: Стойност". Include ONLY: dimensions, power/wattage, pressure, material, connections, weight. Skip marketing data. Example: "• Размери: 600x1000 мм\n• Мощност: 2093W\n• Работно налягане: 10 bar\n• Материал: Стомана"

Return ONLY valid JSON, no other text."""

    text = ""
    try:
        text = _claude(SYSTEM_PROMPT, prompt, max_tokens=1500)
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        result = json.loads(text)
        validated = validate_translation(result)
        return validated
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e} | Raw: {text[:300]}")
        return {"_error": f"JSON parse error: {e}"}
    except Exception as e:
        print(f"  Translation error: {type(e).__name__}: {e}")
        return {"_error": f"{type(e).__name__}: {e}"}


def validate_translation(data: dict) -> dict:
    """
    Second-pass review: send the translated JSON to Claude for quality check.
    Catches mixed-language words, wrong terminology, grammar issues.
    """
    fields_to_check = json.dumps(data, ensure_ascii=False, indent=2)

    review_prompt = f"""Review and fix this Bulgarian product catalog translation. Return corrected JSON.

{fields_to_check}

CHECK FOR AND FIX:
1. Mixed Cyrillic/Latin words (e.g. "леснаdemонтаж" → "лесен демонтаж")
2. Wrong HVAC terms: "топлоотдача" → "топлоотдаване", "висококвалитетна" → "висококачествена"
3. Grammar errors, awkward phrasing, unnatural word order
4. Any remaining Romanian words that weren't translated
5. Overly long features (each should be under 10 words)
6. Specs that include marketing fluff instead of technical data

If everything is correct, return the JSON unchanged.
Return ONLY valid JSON, no other text."""

    try:
        review_system = "You are a Bulgarian language quality reviewer for a B2B HVAC catalog. Fix any errors and return clean JSON."
        text = _claude(review_system, review_prompt, max_tokens=1500).strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except Exception:
        return data


def translate_from_nomenclature(product: dict) -> dict | None:
    """
    Lightweight enrichment using only nomenclature data (no web scraping).
    Used as fallback when scraping fails but we have Romanian name/subcategory.
    Produces brand, category, subcategory, and a short description in Bulgarian.
    """
    name_bg = product.get("name_bg", "")
    short_name_ro = product.get("short_name_ro", "")
    supplier_name = product.get("supplier_name", "")
    category_ro = product.get("category", "")
    class_ro = product.get("class_name", "")
    subclass_ro = product.get("subclass", "")

    if not (short_name_ro or name_bg):
        return None

    prompt = f"""Clean and translate the following HVAC product data for a Bulgarian B2B catalog.

**Existing Bulgarian name:** {name_bg}
**Romanian short name:** {short_name_ro}
**Brand/Supplier:** {supplier_name}
**Category (Romanian):** {category_ro}
**Class (Romanian):** {class_ro}
**Subclass (Romanian):** {subclass_ro}

Return a JSON object with ONLY these fields:
1. "brand" - Clean brand name. Keep international brands as-is (Ecosoft, Grundfos, Kermi, etc.). Strip legal suffixes (SRL, SA, INDUSTRIE, INDUSTRIES, SPA, GmbH, etc.).
2. "category" - Translate category to Bulgarian (e.g. FILTRE, CONTOARE, REZERVOARE → Филтри, водомери, резервоари; RADIATOARE → Радиатори).
3. "subcategory" - Translate class/subclass to Bulgarian (e.g. FILTRE PENTRU APA → Филтри за вода, OSMOЗА → Обратна осмоза).
4. "short_description" - One sentence in Bulgarian describing what the product is, max 120 chars.

Return ONLY valid JSON, no other text."""

    try:
        text = _claude(SYSTEM_PROMPT, prompt, max_tokens=400).strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
    except Exception as e:
        print(f"  Nomenclature translation error: {e}")
        return None


def enrich_products(products: list[dict]) -> list[dict]:
    """
    Translate and enrich all scraped products.

    Args:
        products: List of product dicts with scraped_data

    Returns:
        Same list with enriched_data added to each.
    """
    for i, product in enumerate(products):
        code = product["product_code"]
        name = product.get("name_bg", product.get("short_name_ro", code))

        print(f"\n[{i+1}/{len(products)}] Translating {code}: {name}...")

        if product.get("scrape_status") != "success":
            # Fallback: translate from nomenclature data alone (no web content)
            has_nom = bool(product.get("short_name_ro") or product.get("long_desc_ro"))
            if has_nom and product.get("match_status", "none") != "none":
                print("  No scraped data — translating from nomenclature...")
                result = translate_from_nomenclature(product)
                if result:
                    product["enriched_data"] = result
                    product["enrich_status"] = "success"
                    print(f"  OK (nomenclature): {result.get('brand', '')} | {result.get('subcategory', '')}")
                else:
                    product["enriched_data"] = None
                    product["enrich_status"] = "failed"
                    print("  FAILED")
            else:
                print("  Skipping - no scraped data and no nomenclature data")
                product["enriched_data"] = None
                product["enrich_status"] = "skipped"
            continue

        result = translate_product(product)

        if result and "_error" not in result:
            product["enriched_data"] = result
            product["enrich_status"] = "success"
            short = result.get("short_description", "")[:80]
            print(f"  OK: \"{short}...\"")
        else:
            err = (result or {}).get("_error", "unknown error")
            product["enriched_data"] = None
            product["enrich_status"] = "failed"
            product["enrich_error"] = err
            print(f"  FAILED: {err}")

        # Rate limiting for Claude API
        if i < len(products) - 1:
            time.sleep(1)

    return products


def run():
    """Main entry: load scraped products, translate, save results."""
    scraped_path = TMP_DIR / "scraped_products.json"
    if not scraped_path.exists():
        raise FileNotFoundError("Run scrape_product first to generate scraped_products.json")

    with open(scraped_path, encoding="utf-8") as f:
        products = json.load(f)

    print(f"Loaded {len(products)} scraped products")
    products = enrich_products(products)

    # Save enriched data
    output_path = TMP_DIR / "enriched_products.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"\nSaved enriched data to {output_path}")

    # Summary
    success = sum(1 for p in products if p.get("enrich_status") == "success")
    failed = sum(1 for p in products if p.get("enrich_status") == "failed")
    skipped = sum(1 for p in products if p.get("enrich_status") == "skipped")
    print(f"Summary: {success} translated, {failed} failed, {skipped} skipped")


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    run()
