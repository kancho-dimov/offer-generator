"""
Professional formatting for offer Google Sheets — PDF-ready.

Applies formatting to the main offer/pricelist tab:
- Blue header bar with company name (Romstal brand #0086CE)
- Cell merges for header, customer info, totals, and footer sections
- Line items table: header row, alternating light-blue rows, borders
- Totals section (offer mode): bold, highlighted
- Terms section: smaller font, grey
- Number formatting for prices and percentages
- Mode-specific column widths (landscape for offer, portrait for pricelist)
- Row heights optimized for print/PDF

Usage:
    from tools.format_offer_sheet import format_offer_sheet
    format_offer_sheet(spreadsheet_id, mode, header_row_count, table_row_count,
                       totals_row_count, footer_row_count)
"""

from tools.google_auth import get_sheets_service


def _get_sheet_id(service, spreadsheet_id: str, tab_name: str) -> int:
    """Get the numeric sheetId for a given tab name."""
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in meta.get("sheets", []):
        if sheet["properties"]["title"] == tab_name:
            return sheet["properties"]["sheetId"]
    raise ValueError(f"Sheet '{tab_name}' not found")


# ── Romstal Brand Colors ──────────────────────────────────────────────
BRAND_BLUE = {"red": 0.0, "green": 0.525, "blue": 0.808}       # #0086CE
LIGHT_BLUE = {"red": 0.89, "green": 0.96, "blue": 1.0}         # #E3F5FF
WHITE = {"red": 1, "green": 1, "blue": 1}
LIGHT_GREY = {"red": 0.95, "green": 0.95, "blue": 0.95}
DARK_GREY_TEXT = {"red": 0.4, "green": 0.4, "blue": 0.4}
DARK_TEXT = {"red": 0.133, "green": 0.133, "blue": 0.133}       # #222222
BLACK = {"red": 0, "green": 0, "blue": 0}
HIGHLIGHT_YELLOW = {"red": 1.0, "green": 0.97, "blue": 0.80}


def _merge(sheet_id, r1, r2, c1, c2):
    """Build a mergeCells request."""
    return {
        "mergeCells": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": r1,
                "endRowIndex": r2,
                "startColumnIndex": c1,
                "endColumnIndex": c2,
            },
            "mergeType": "MERGE_ALL",
        }
    }


def format_offer_sheet(
    spreadsheet_id: str,
    mode: str,
    header_row_count: int,
    table_row_count: int,
    totals_row_count: int,
    footer_row_count: int,
    tab_name: str | None = None,
    num_cols_override: int | None = None,
    col_widths_override: list[int] | None = None,
    split_header_col: int | None = None,
):
    """
    Apply professional PDF-ready formatting to the offer/order sheet.

    Args:
        spreadsheet_id: Google Sheet ID
        mode: "offer" or "pricelist"
        header_row_count: number of rows in the company/customer header section
        table_row_count: number of rows in the line items table (including table header)
        totals_row_count: number of rows in the totals section (0 for pricelist)
        footer_row_count: number of rows in the terms/footer section
        tab_name: override the tab name (default: auto from mode)
        num_cols_override: override column count
        col_widths_override: override column widths
    """
    service = get_sheets_service()
    if tab_name is None:
        tab_name = "Оферта" if mode == "offer" else "Ценова листа"
    sheet_id = _get_sheet_id(service, spreadsheet_id, tab_name)

    table_start = header_row_count
    table_end = table_start + table_row_count
    totals_start = table_end
    totals_end = totals_start + totals_row_count
    footer_start = totals_end
    footer_end = footer_start + footer_row_count

    if num_cols_override:
        num_cols = num_cols_override
        col_widths = col_widths_override or [100] * num_cols
    elif mode == "offer":
        num_cols = 10  # A through J (no per-line VAT columns)
        col_widths = [35, 60, 100, 260, 85, 50, 95, 75, 115, 115]
    else:
        num_cols = 10  # A through J (with image col)
        col_widths = [35, 60, 100, 260, 90, 160, 95, 75, 115, 115]

    requests = []

    # ── 1. Cell Merges ─────────────────────────────────────────────────

    # Header rows: merge across columns
    # Row 0: company name left, logo right (last 5 cols merged)
    requests.append(_merge(sheet_id, 0, 1, 0, num_cols - 5))
    requests.append(_merge(sheet_id, 0, 1, num_cols - 5, num_cols))
    # Rows 1-3: address, phone/email, VAT
    for r in range(1, 4):
        requests.append(_merge(sheet_id, r, r + 1, 0, num_cols))
    # Row 5: offer number / date / validity
    requests.append(_merge(sheet_id, 5, 6, 0, num_cols))

    # Customer info rows (7 onward until header_row_count - 1)
    for r in range(7, header_row_count - 1):  # -1 to skip the blank row before table
        if split_header_col:
            # Two-column layout: left block + right block
            requests.append(_merge(sheet_id, r, r + 1, 0, split_header_col))
            requests.append(_merge(sheet_id, r, r + 1, split_header_col, num_cols))
        else:
            # Single merged string spanning all columns
            requests.append(_merge(sheet_id, r, r + 1, 0, num_cols))

    # Totals rows: merge label cells across most columns
    if mode == "offer" and totals_row_count > 0:
        for r in range(totals_start + 1, totals_end):
            # Merge A through second-to-last col for the label
            requests.append(_merge(sheet_id, r, r + 1, 0, num_cols - 2))

    # Footer rows: merge each row across all columns
    for r in range(footer_start, footer_end):
        requests.append(_merge(sheet_id, r, r + 1, 0, num_cols))

    # ── 2. Company Header (Row 0) — white bg, blue text, logo right ───

    # Row 0: white background, bold Romstal blue company name
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": num_cols,
            },
            "cell": {"userEnteredFormat": {
                "backgroundColor": WHITE,
                "textFormat": {"bold": True, "fontSize": 14, "foregroundColor": BRAND_BLUE},
                "verticalAlignment": "MIDDLE",
            }},
            "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment)",
        }
    })

    # Logo cells: centered
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": num_cols - 5,
                "endColumnIndex": num_cols,
            },
            "cell": {"userEnteredFormat": {
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
            }},
            "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment)",
        }
    })

    # Row 0 height for logo
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": 0,
                "endIndex": 1,
            },
            "properties": {"pixelSize": 100},
            "fields": "pixelSize",
        }
    })

    # Blue accent line below company info (under row 3)
    requests.append({
        "updateBorders": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 3,
                "endRowIndex": 4,
                "startColumnIndex": 0,
                "endColumnIndex": num_cols,
            },
            "bottom": {"style": "SOLID_MEDIUM", "width": 2, "color": BRAND_BLUE},
        }
    })

    # ── 3. Company Details (rows 1-3): smaller grey text ──────────────

    requests.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 4},
            "cell": {"userEnteredFormat": {
                "textFormat": {"fontSize": 9, "foregroundColor": DARK_GREY_TEXT},
            }},
            "fields": "userEnteredFormat.textFormat",
        }
    })

    # ── 4. Offer Number Row (row 5): bold, medium, brand blue ─────────

    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 5,
                "endRowIndex": 6,
                "startColumnIndex": 0,
                "endColumnIndex": num_cols,
            },
            "cell": {"userEnteredFormat": {
                "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": BRAND_BLUE},
            }},
            "fields": "userEnteredFormat.textFormat",
        }
    })

    # Row 5 height
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": 5,
                "endIndex": 6,
            },
            "properties": {"pixelSize": 35},
            "fields": "pixelSize",
        }
    })

    # ── 5. Customer Info (rows 7 to header_row_count): normal ─────────

    requests.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 7, "endRowIndex": header_row_count},
            "cell": {"userEnteredFormat": {
                "textFormat": {"fontSize": 10, "foregroundColor": DARK_TEXT},
            }},
            "fields": "userEnteredFormat.textFormat",
        }
    })

    # ── 6. Table Header Row: brand blue bg, white bold text ───────────

    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": table_start,
                "endRowIndex": table_start + 1,
                "startColumnIndex": 0,
                "endColumnIndex": num_cols,
            },
            "cell": {"userEnteredFormat": {
                "backgroundColor": BRAND_BLUE,
                "textFormat": {"bold": True, "foregroundColor": WHITE, "fontSize": 10},
                "horizontalAlignment": "CENTER",
                "verticalAlignment": "MIDDLE",
                "wrapStrategy": "WRAP",
            }},
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)",
        }
    })

    # Table header row height (taller to show full multiline column names)
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": table_start,
                "endIndex": table_start + 1,
            },
            "properties": {"pixelSize": 55},
            "fields": "pixelSize",
        }
    })

    # ── 7. Table Data Rows: alternating blue/white ────────────────────

    for row_idx in range(table_start + 1, table_end):
        bg = LIGHT_BLUE if (row_idx - table_start) % 2 == 0 else WHITE
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": row_idx,
                    "endRowIndex": row_idx + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": num_cols,
                },
                "cell": {"userEnteredFormat": {
                    "backgroundColor": bg,
                    "textFormat": {"fontSize": 10, "foregroundColor": DARK_TEXT},
                    "verticalAlignment": "MIDDLE",
                    "wrapStrategy": "WRAP",
                }},
                "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)",
            }
        })

    # Data row heights (taller to accommodate product images)
    if table_start + 1 < table_end:
        requests.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": table_start + 1,
                    "endIndex": table_end,
                },
                "properties": {"pixelSize": 45},
                "fields": "pixelSize",
            }
        })

    # ── 8. Table Borders ──────────────────────────────────────────────

    # Top and bottom thick blue borders
    requests.append({
        "updateBorders": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": table_start,
                "endRowIndex": table_end,
                "startColumnIndex": 0,
                "endColumnIndex": num_cols,
            },
            "top": {"style": "SOLID_MEDIUM", "width": 2, "color": BRAND_BLUE},
            "bottom": {"style": "SOLID_MEDIUM", "width": 2, "color": BRAND_BLUE},
            "innerHorizontal": {"style": "SOLID", "width": 1, "color": LIGHT_GREY},
            "innerVertical": {"style": "SOLID", "width": 1, "color": LIGHT_GREY},
        }
    })

    # ── 9. Totals Section (offer mode) ────────────────────────────────

    if mode == "offer" and totals_row_count > 0:
        # Subtotal and VAT rows: bold, right-aligned
        for row_idx in range(totals_start + 1, totals_end - 1):
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": row_idx,
                        "endRowIndex": row_idx + 1,
                    },
                    "cell": {"userEnteredFormat": {
                        "textFormat": {"bold": True, "fontSize": 10, "foregroundColor": DARK_TEXT},
                        "horizontalAlignment": "RIGHT",
                    }},
                    "fields": "userEnteredFormat(textFormat,horizontalAlignment)",
                }
            })

        # Grand total row: bold, larger, highlighted yellow
        grand_total_row = totals_end - 1
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": grand_total_row,
                    "endRowIndex": grand_total_row + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": num_cols,
                },
                "cell": {"userEnteredFormat": {
                    "backgroundColor": HIGHLIGHT_YELLOW,
                    "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": BLACK},
                    "horizontalAlignment": "RIGHT",
                }},
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
            }
        })

        # Border below totals
        requests.append({
            "updateBorders": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": grand_total_row,
                    "endRowIndex": grand_total_row + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": num_cols,
                },
                "top": {"style": "SOLID_MEDIUM", "width": 2, "color": BRAND_BLUE},
                "bottom": {"style": "SOLID_MEDIUM", "width": 2, "color": BRAND_BLUE},
            }
        })

    # ── 10. Footer/Terms: smaller, grey ───────────────────────────────

    if footer_row_count > 0:
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": footer_start,
                    "endRowIndex": footer_end,
                },
                "cell": {"userEnteredFormat": {
                    "textFormat": {"fontSize": 9, "foregroundColor": DARK_GREY_TEXT},
                    "wrapStrategy": "WRAP",
                }},
                "fields": "userEnteredFormat(textFormat,wrapStrategy)",
            }
        })

        # "Условия:" and "Важно:" labels in bold (footer_start+1 and footer_start+4)
        for label_offset in [1, 4]:
            label_row = footer_start + label_offset
            if label_row < footer_end:
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": label_row,
                            "endRowIndex": label_row + 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": 1,
                        },
                        "cell": {"userEnteredFormat": {
                            "textFormat": {"bold": True, "fontSize": 9, "foregroundColor": BRAND_BLUE},
                        }},
                        "fields": "userEnteredFormat.textFormat",
                    }
                })

    # ── 11. Column Widths ─────────────────────────────────────────────

    for i, width in enumerate(col_widths):
        requests.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": i,
                    "endIndex": i + 1,
                },
                "properties": {"pixelSize": width},
                "fields": "pixelSize",
            }
        })

    # ── 12. Number Formatting for Price Columns ───────────────────────

    if num_cols_override:
        # Order or custom layout: format all numeric-looking columns
        price_cols = [c for c in [9, 11, 12] if c < num_cols]
    elif mode == "offer":
        price_cols = [6, 8, 9]  # BasePrice, NetExcl, TotalExcl
    else:
        price_cols = [6, 8, 9]  # BasePrice, NetExcl, NetIncl

    for col in price_cols:
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": table_start + 1,
                    "endRowIndex": table_end,
                    "startColumnIndex": col,
                    "endColumnIndex": col + 1,
                },
                "cell": {"userEnteredFormat": {
                    "numberFormat": {"type": "NUMBER", "pattern": "#,##0.00"},
                    "horizontalAlignment": "RIGHT",
                }},
                "fields": "userEnteredFormat(numberFormat,horizontalAlignment)",
            }
        })

    # ── 13. Center-Align All Columns Except Name and Price Columns ────

    # Name column (3) stays left-aligned; price columns stay right-aligned
    # All other columns get centered
    skip_cols = {3} | set(price_cols)  # Name + price columns
    for col in range(num_cols):
        if col in skip_cols:
            continue
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": table_start + 1,
                    "endRowIndex": table_end,
                    "startColumnIndex": col,
                    "endColumnIndex": col + 1,
                },
                "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
                "fields": "userEnteredFormat.horizontalAlignment",
            }
        })

    # ── 14. Blue Separator Line Before Table ──────────────────────────

    # Thin blue top border on the row just before the table (blank separator)
    if table_start > 0:
        requests.append({
            "updateBorders": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": table_start - 1,
                    "endRowIndex": table_start,
                    "startColumnIndex": 0,
                    "endColumnIndex": num_cols,
                },
                "bottom": {"style": "SOLID_MEDIUM", "width": 2, "color": BRAND_BLUE},
            }
        })

    # ── Execute ───────────────────────────────────────────────────────

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests},
    ).execute()

    print(f"  Formatting applied to {tab_name}")
