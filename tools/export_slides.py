"""
Export offer data as a compact Google Slides presentation in portrait format.

Creates a single-page portrait presentation:
- Company header + customer info + products table (with totals embedded) + terms + footer

The presentation can be downloaded as PDF from Google Slides (File > Download > PDF).

Usage:
    python -m tools.export_slides OFR-2026-001
    python -m tools.export_slides                  # exports the most recent offer
"""

import io
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from tools.google_auth import get_slides_service

if "streamlit" not in sys.modules and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TMP_DIR = Path(__file__).resolve().parent.parent / ".tmp"

# Portrait A4-ish dimensions (EMU: 1 inch = 914400)
EMU = 914400
PAGE_W = int(7.5 * EMU)   # ~190mm
PAGE_H = int(10.0 * EMU)  # ~254mm

# Romstal Brand Colors
BRAND_BLUE = {"red": 0.0, "green": 0.525, "blue": 0.808}   # #0086CE
WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}
DARK = {"red": 0.133, "green": 0.133, "blue": 0.133}       # #222222
GREY = {"red": 0.5, "green": 0.5, "blue": 0.5}
LIGHT_BG = {"red": 0.89, "green": 0.96, "blue": 1.0}       # #E3F5FF
HIGHLIGHT = {"red": 1.0, "green": 0.97, "blue": 0.80}

_counter = 0


def _id(prefix="elem"):
    global _counter
    _counter += 1
    return f"{prefix}_{_counter:04d}"


def _emu(inches):
    return int(inches * EMU)


def _textbox(page, left, top, w, h, text, size=12, bold=False, color=None, align="START"):
    """Return requests to create a styled text box."""
    eid = _id("tb")
    color = color or DARK
    return [
        {"createShape": {
            "objectId": eid,
            "shapeType": "TEXT_BOX",
            "elementProperties": {
                "pageObjectId": page,
                "size": {"width": {"magnitude": w, "unit": "EMU"}, "height": {"magnitude": h, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": left, "translateY": top, "unit": "EMU"},
            },
        }},
        {"insertText": {"objectId": eid, "text": text}},
        {"updateTextStyle": {
            "objectId": eid,
            "style": {"fontSize": {"magnitude": size, "unit": "PT"}, "bold": bold,
                       "foregroundColor": {"opaqueColor": {"rgbColor": color}}, "fontFamily": "Arial"},
            "textRange": {"type": "ALL"},
            "fields": "fontSize,bold,foregroundColor,fontFamily",
        }},
        {"updateParagraphStyle": {
            "objectId": eid, "style": {"alignment": align, "lineSpacing": 115},
            "textRange": {"type": "ALL"}, "fields": "alignment,lineSpacing",
        }},
    ]


def _rect(page, left, top, w, h, color):
    """Return requests for a colored rectangle."""
    eid = _id("rc")
    return [
        {"createShape": {
            "objectId": eid, "shapeType": "RECTANGLE",
            "elementProperties": {
                "pageObjectId": page,
                "size": {"width": {"magnitude": w, "unit": "EMU"}, "height": {"magnitude": h, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": left, "translateY": top, "unit": "EMU"},
            },
        }},
        {"updateShapeProperties": {
            "objectId": eid,
            "shapeProperties": {
                "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": color}}},
                "outline": {"outlineFill": {"solidFill": {"color": {"rgbColor": color}}}},
            },
            "fields": "shapeBackgroundFill,outline",
        }},
    ]


def _find_latest():
    files = sorted(TMP_DIR.glob("*_data.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError("No offer data files in .tmp/")
    return files[0]


def _table_cell_text(tid, ri, ci, text, size=8, bold=False, color=None, align=None):
    """Return requests to insert and style text in a table cell."""
    reqs = [
        {"insertText": {"objectId": tid, "cellLocation": {"rowIndex": ri, "columnIndex": ci}, "text": text}},
    ]
    style = {"fontSize": {"magnitude": size, "unit": "PT"}, "fontFamily": "Arial"}
    fields = "fontSize,fontFamily"
    if bold:
        style["bold"] = True
        fields += ",bold"
    if color:
        style["foregroundColor"] = {"opaqueColor": {"rgbColor": color}}
        fields += ",foregroundColor"
    reqs.append({"updateTextStyle": {
        "objectId": tid, "cellLocation": {"rowIndex": ri, "columnIndex": ci},
        "style": style, "textRange": {"type": "ALL"}, "fields": fields,
    }})
    if align:
        reqs.append({"updateParagraphStyle": {
            "objectId": tid, "cellLocation": {"rowIndex": ri, "columnIndex": ci},
            "style": {"alignment": align}, "textRange": {"type": "ALL"}, "fields": "alignment",
        }})
    return reqs


def _table_cell_bg(tid, ri, ci, color):
    """Return request to set a table cell background color."""
    return {"updateTableCellProperties": {
        "objectId": tid,
        "tableRange": {"location": {"rowIndex": ri, "columnIndex": ci}, "rowSpan": 1, "columnSpan": 1},
        "tableCellProperties": {"tableCellBackgroundFill": {"solidFill": {"color": {"rgbColor": color}}}},
        "fields": "tableCellBackgroundFill",
    }}


def export_slides(offer_number: str | None = None) -> str:
    global _counter
    _counter = 0

    # Load data
    path = TMP_DIR / f"{offer_number}_data.json" if offer_number else _find_latest()
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    offer_num = data["offer_number"]
    mode = data["mode"]
    customer = data["customer"]
    branding = data["branding"]
    result = data["result"]
    req = data.get("request", {})
    lines = [l for l in result["lines"] if "error" not in l]

    company = branding.get("company_name", "")
    cust_name = customer.get("company_name", "")
    validity = req.get("validity_days", 30)
    valid_until = (date.today() + timedelta(days=validity)).strftime("%d.%m.%Y")
    today_str = date.today().strftime("%d.%m.%Y")
    label = "ОФЕРТА" if mode == "offer" else "ЦЕНОВА ЛИСТА"

    service = get_slides_service()

    # Create presentation with portrait page size
    pres = service.presentations().create(body={
        "title": f"{offer_num} | {cust_name}",
        "pageSize": {
            "width": {"magnitude": PAGE_W, "unit": "EMU"},
            "height": {"magnitude": PAGE_H, "unit": "EMU"},
        },
    }).execute()
    pres_id = pres["presentationId"]
    default_slide = pres["slides"][0]["objectId"]

    reqs = []
    margin = _emu(0.4)
    content_w = PAGE_W - 2 * margin

    # ===== SLIDE 1: Header + Customer + Table =====
    s1 = _id("slide")
    reqs.append({"createSlide": {"objectId": s1, "slideLayoutReference": {"predefinedLayout": "BLANK"}}})

    # Green header bar
    reqs.extend(_rect(s1, 0, 0, PAGE_W, _emu(0.55), BRAND_BLUE))
    reqs.extend(_textbox(s1, margin, _emu(0.08), content_w, _emu(0.4),
                         company, size=16, bold=True, color=WHITE))

    # Offer number + date
    y = _emu(0.75)
    reqs.extend(_textbox(s1, margin, y, content_w, _emu(0.35),
                         f"{label} {offer_num}    |    Дата: {today_str}    |    Валидна до: {valid_until}",
                         size=10, bold=True, color=BRAND_BLUE))

    # Customer block
    y = _emu(1.15)
    cust_text = f"Клиент: {cust_name}\n{customer.get('contact_name', '')}  |  {customer.get('phone', '')}  |  {customer.get('email', '')}\n{customer.get('address', '')}"
    notes = req.get("notes", "")
    if notes:
        cust_text += f"\n{notes}"
    reqs.extend(_textbox(s1, margin, y, content_w, _emu(0.7), cust_text, size=9, color=DARK))

    # Separator line
    y = _emu(1.9)
    reqs.extend(_rect(s1, margin, y, content_w, _emu(0.01), BRAND_BLUE))

    # ===== Products table =====
    y = _emu(2.05)

    if mode == "offer":
        cols = 6
        headers = ["#", "Код", "Наименование", "К-во", "Цена EUR", "Общо EUR"]
        # Column widths in inches (total must equal content_w / EMU ≈ 6.7)
        col_widths = [0.45, 0.75, 2.8, 0.5, 1.05, 1.15]
        # Columns that should be right-aligned (numeric)
        right_cols = {3, 4, 5}
        # Extra rows: 1 empty separator + 3 totals
        extra_rows = 4
    else:
        cols = 5
        headers = ["#", "Код", "Наименование", "Марка", "Цена EUR"]
        col_widths = [0.45, 0.75, 2.7, 1.2, 1.6]
        right_cols = {4}
        extra_rows = 0

    n_data = len(lines)
    n_rows = 1 + n_data + extra_rows  # header + data + totals
    row_h = _emu(0.45)
    table_h = n_rows * row_h
    table_w = content_w

    tid = _id("table")
    reqs.append({"createTable": {
        "objectId": tid,
        "elementProperties": {
            "pageObjectId": s1,
            "size": {"width": {"magnitude": table_w, "unit": "EMU"}, "height": {"magnitude": table_h, "unit": "EMU"}},
            "transform": {"scaleX": 1, "scaleY": 1, "translateX": margin, "translateY": y, "unit": "EMU"},
        },
        "rows": n_rows, "columns": cols,
    }})

    # Set column widths
    for ci, w_in in enumerate(col_widths):
        reqs.append({"updateTableColumnProperties": {
            "objectId": tid,
            "columnIndices": [ci],
            "tableColumnProperties": {"columnWidth": {"magnitude": _emu(w_in), "unit": "EMU"}},
            "fields": "columnWidth",
        }})

    # Header row
    for ci, h in enumerate(headers):
        align = "END" if ci in right_cols else "START"
        reqs.extend(_table_cell_text(tid, 0, ci, h, size=8, bold=True, color=WHITE, align=align))
        reqs.append(_table_cell_bg(tid, 0, ci, BRAND_BLUE))

    # Data rows
    for ri, line in enumerate(lines, 1):
        if mode == "offer":
            cells = [str(ri), line["product_code"], line["name"][:50],
                     str(line["quantity"]), f"{line['net_price_excl_vat']:.2f}",
                     f"{line['line_total_excl_vat']:.2f}"]
        else:
            cells = [str(ri), line["product_code"], line["name"][:50],
                     line["brand"], f"{line['net_price_excl_vat']:.2f}"]

        for ci, val in enumerate(cells):
            align = "END" if ci in right_cols else None
            reqs.extend(_table_cell_text(tid, ri, ci, val, align=align))

        # Alternating row bg
        if ri % 2 == 0:
            for ci in range(cols):
                reqs.append(_table_cell_bg(tid, ri, ci, LIGHT_BG))

    # Totals rows inside the table (offer mode only)
    if mode == "offer":
        sep_ri = 1 + n_data  # empty separator row

        totals_info = [
            (sep_ri + 1, "Междинна сума (без ДДС):", f"{result['subtotal_excl_vat']:.2f} EUR", False),
            (sep_ri + 2, "ДДС (20%):", f"{result['total_vat']:.2f} EUR", False),
            (sep_ri + 3, "ОБЩА СУМА (с ДДС):", f"{result['grand_total_incl_vat']:.2f} EUR", True),
        ]

        for ri, lbl, val, highlight in totals_info:
            # Label in the "Цена EUR" column (index 4), right-aligned
            reqs.extend(_table_cell_text(tid, ri, 4, lbl, size=8, bold=True, align="END"))
            # Value in the "Общо EUR" column (index 5), right-aligned
            reqs.extend(_table_cell_text(tid, ri, 5, val, size=8, bold=True, align="END"))

            # Highlight grand total row
            if highlight:
                for ci in range(cols):
                    reqs.append(_table_cell_bg(tid, ri, ci, HIGHLIGHT))

    # Terms — at the bottom of slide 1
    terms_y = PAGE_H - _emu(1.2)
    terms = branding.get("offer_terms", "")
    disclaimer = branding.get("offer_disclaimer", "")
    terms_text = f"Условия: {terms}"
    if disclaimer:
        terms_text += f"\n{disclaimer}"
    reqs.extend(_textbox(s1, margin, terms_y, content_w, _emu(0.9),
                         terms_text, size=7, color=GREY))

    # Footer bar
    reqs.extend(_rect(s1, 0, PAGE_H - _emu(0.25), PAGE_W, _emu(0.25), BRAND_BLUE))
    footer = f"{company}  |  {branding.get('company_phone', '')}  |  {branding.get('company_email', '')}  |  {branding.get('company_website', '')}"
    reqs.extend(_textbox(s1, margin, PAGE_H - _emu(0.22), content_w, _emu(0.2),
                         footer, size=7, color=WHITE, align="CENTER"))

    # Delete default blank slide
    reqs.append({"deleteObject": {"objectId": default_slide}})

    # Execute
    service.presentations().batchUpdate(presentationId=pres_id, body={"requests": reqs}).execute()

    url = f"https://docs.google.com/presentation/d/{pres_id}"
    print(f"Presentation created: {url}")
    print(f"  Title: {offer_num} | {cust_name}")
    print(f"  Format: Portrait, 1 slide")
    print(f"  To export PDF: File > Download > PDF")
    return url


if __name__ == "__main__":
    offer_num = sys.argv[1] if len(sys.argv) > 1 else None
    export_slides(offer_num)
