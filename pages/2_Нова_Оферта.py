"""Create Offer page — compact single-screen layout."""

import base64

import streamlit as st

from i18n import setup_page, t
from tools.discount_engine import load_customer
from tools.generate_offer import generate_offer
from tools.product_search import load_all_products, search_products
from tools.send_email import prepare_offer_email, send_offer_to_customer
from tools.sheets_api import read_sheet

MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"

setup_page("Нова Оферта", "📋")

# ── Extra CSS for compact layout ──────────────────────────────────
st.markdown("""
<style>
/* Tighter page padding */
.block-container { padding-top: 1rem !important; padding-bottom: 0.5rem !important; }

/* Hide label on collapsed inputs */
.compact-label > label { font-size: 0.72rem !important; color: #666 !important; margin-bottom: 2px !important; }

/* Panel header strip */
.panel-hdr {
    font-size: 0.7rem; font-weight: 700; color: #0086CE;
    text-transform: uppercase; letter-spacing: 0.08em;
    border-bottom: 2px solid #0086CE; padding-bottom: 4px; margin-bottom: 6px;
}

/* Search result row */
.sr-row {
    padding: 5px 8px; border-bottom: 1px solid #f0f2f6;
    font-size: 0.82rem;
}
.sr-row:hover { background: #f4f8ff; }
.sr-name { font-weight: 600; color: #1a1a2e; }
.sr-meta { color: #888; font-size: 0.74rem; }
.sr-price { color: #0086CE; font-weight: 700; }

/* Selected item row */
.sel-row {
    padding: 5px 8px; border-bottom: 1px solid #eef2ff;
    background: #fafbff; font-size: 0.82rem;
}
.sel-name { font-weight: 600; color: #1a1a2e; }

/* Compact number inputs */
div[data-testid="stNumberInput"] { margin-bottom: 0 !important; }
div[data-testid="stNumberInput"] input { padding: 3px 6px !important; font-size: 0.82rem !important; }

/* Compact selectbox */
div[data-baseweb="select"] > div { min-height: 36px !important; }

/* Compact radio (horizontal) */
div[data-testid="stRadio"] > div { flex-direction: row !important; gap: 16px; align-items: center; }
div[data-testid="stRadio"] label { font-size: 0.85rem !important; }

/* Compact checkbox */
div[data-testid="stCheckbox"] label { font-size: 0.82rem !important; }

/* Generate button — full width, prominent */
div[data-testid="stButton"]:has(button[kind="primary"]) button {
    font-size: 1rem !important; font-weight: 700 !important; letter-spacing: 0.04em;
    padding: 10px 0 !important;
}

/* Popover compact */
div[data-testid="stPopover"] button { font-size: 0.82rem !important; }

/* Divider tighter */
hr { margin: 6px 0 !important; }

/* Title row tighter */
h1 { margin-bottom: 0.3rem !important; padding-bottom: 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────
for _k, _d in [
    ("offer_items", []), ("offer_result", None),
    ("offer_email_preview", None), ("offer_form_ver", 0),
    ("current_offer_number", None), ("current_spreadsheet_id", None),
    ("current_offer_status", "draft"), ("current_offer_version", 1),
    ("current_offer_base_id", None), ("current_offer_customer_id", None),
]:
    if _k not in st.session_state:
        st.session_state[_k] = _d

# ── Edit bootstrap (triggered by dashboard Edit button) ────────────
_edit = st.session_state.pop("editing_offer", None)
if _edit:
    _surl = _edit.get("spreadsheet_url", "")
    _sid = _surl.split("/d/")[1].split("/")[0] if "/d/" in _surl else ""
    st.session_state.current_offer_number = _edit["offer_number"]
    st.session_state.current_spreadsheet_id = _sid
    st.session_state.current_offer_status = _edit.get("status", "draft")
    st.session_state.current_offer_version = _edit.get("version", 1)
    st.session_state.current_offer_base_id = _edit.get("base_id", _edit["offer_number"])
    st.session_state.current_offer_customer_id = _edit.get("customer_id", "")
    st.session_state.offer_result = None
    st.session_state.offer_email_preview = None
    # Load items from existing offer spreadsheet
    st.session_state.offer_items = []
    if _sid:
        _edit_mode = _edit.get("mode", "offer")
        _tab = "Оферта" if _edit_mode == "offer" else "Ценова листа"
        try:
            _rows = read_sheet(_sid, f"'{_tab}'!A13:J100")
            for _row in (_rows or []):
                if not _row or not str(_row[0]).strip().isdigit():
                    continue
                _row = list(_row) + [""] * (10 - len(_row))
                _code = str(_row[2]).strip()
                _name = str(_row[3]).strip()
                if _edit_mode == "offer":
                    try:
                        _qty = int(float(_row[5])) if _row[5] else 1
                    except (ValueError, TypeError):
                        _qty = 1
                else:
                    _qty = 1  # pricelist has no quantity column
                _disc_raw = str(_row[7]).replace("%", "").strip()
                try:
                    _disc = float(_disc_raw) if _disc_raw else None
                except (ValueError, TypeError):
                    _disc = None
                if _code:
                    st.session_state.offer_items.append({
                        "product_code": _code,
                        "supplier_code": "",
                        "name": _name,
                        "quantity": _qty,
                        "discount_override": _disc if _disc and _disc > 0 else None,
                    })
        except Exception:
            pass
    st.session_state.offer_form_ver += 1

_v = st.session_state.offer_form_ver

if st.session_state.get("_offer_reset") and st.session_state.get("offer_items"):
    st.session_state.offer_items = []
    st.session_state._offer_reset = False


# ── Data loaders ──────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_customers():
    rows = read_sheet(MASTER_CATALOG_ID, "'Customers'!A:N")
    if not rows or len(rows) < 2:
        return []
    headers = rows[0]
    out = []
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        row += [""] * (len(headers) - len(row))
        out.append(dict(zip(headers, row)))
    return out


@st.cache_data(ttl=300)
def get_filter_options():
    products = load_all_products()
    categories = sorted({p.get("category", "") for p in products if p.get("category", "").strip()})
    brands = sorted({p.get("brand", "") for p in products if p.get("brand", "").strip()})
    return categories, brands


# ── Header row ────────────────────────────────────────────────────
hc1, hc2 = st.columns([6, 1])
with hc1:
    st.title(t("new_offer_title"))
with hc2:
    st.write("")
    if st.button(t("new_offer_reset"), use_container_width=True):
        st.session_state.offer_form_ver += 1
        st.session_state.offer_items = []
        st.session_state.offer_result = None
        st.session_state.offer_email_preview = None
        st.session_state._offer_reset = True
        st.session_state.current_offer_number = None
        st.session_state.current_spreadsheet_id = None
        st.session_state.current_offer_status = "draft"
        st.session_state.current_offer_version = 1
        st.session_state.current_offer_base_id = None
        st.session_state.current_offer_customer_id = None
        if "offer_pdf_bytes" in st.session_state:
            del st.session_state.offer_pdf_bytes
        st.rerun()

# ── Edit mode banner ──────────────────────────────────────────────
_cur_ofr_num = st.session_state.get("current_offer_number")
_cur_ofr_status = st.session_state.get("current_offer_status", "draft")
_cur_ofr_ver = st.session_state.get("current_offer_version", 1)
if _cur_ofr_num:
    if _cur_ofr_status == "draft":
        st.info(t("edit_offer_banner", num=_cur_ofr_num))
    else:
        st.warning(t("edit_offer_revision_banner", num=_cur_ofr_num, ver=_cur_ofr_ver + 1))

# ── Controls bar ──────────────────────────────────────────────────
customers = load_customers()
customer_names = {c["company_name"]: c["customer_id"] for c in customers}

bar1, bar2, bar3, bar4, bar5, bar6 = st.columns([3, 2, 0.8, 1, 1, 0.8])

with bar1:
    _edit_cust_idx = None
    _edit_cust_id = st.session_state.get("current_offer_customer_id", "")
    if _edit_cust_id:
        _cust_name_list = list(customer_names.keys())
        for _ci, (_cn, _cid) in enumerate(customer_names.items()):
            if _cid == _edit_cust_id:
                _edit_cust_idx = _ci
                break
    selected_name = st.selectbox(
        t("customer"),
        options=list(customer_names.keys()),
        key=f"ofr_cust_{_v}",
        index=_edit_cust_idx,
        placeholder=t("select_customer_placeholder"),
    )

with bar2:
    mode = st.radio(
        t("type"), ["offer", "pricelist"],
        format_func=lambda x: t("offer_label") if x == "offer" else t("pricelist_label"),
        key=f"ofr_mode_{_v}",
        horizontal=True,
    )

with bar3:
    validity = st.number_input(
        t("validity_days"), min_value=1, value=30, key=f"ofr_validity_{_v}",
    )

with bar4:
    show_discount = st.checkbox(t("show_discounts"), value=True, key=f"ofr_show_disc_{_v}")

with bar5:
    show_vat = st.checkbox(t("show_vat"), value=True, key=f"ofr_show_vat_{_v}")

with bar6:
    st.write("")
    with st.popover("⚙️", use_container_width=True):

        def _disc_label(x):
            return {
                "line": t("per_product"),
                "group": t("per_brand"),
                "category": t("per_category"),
            }.get(x, x)

        discount_level = st.selectbox(
            t("discount_level"), ["line", "group", "category"],
            format_func=_disc_label, key=f"ofr_disc_level_{_v}",
        )
        custom_discount_pct = st.number_input(
            t("extra_discount"), min_value=0.0, max_value=50.0,
            value=0.0, step=0.5, key=f"ofr_extra_disc_{_v}",
        )
        notes = st.text_area(
            t("notes"), placeholder=t("notes_placeholder"),
            key=f"ofr_notes_{_v}", height=80,
        )

selected_customer_id = customer_names.get(selected_name, "")

# ── Generate button — always visible above panels ─────────────────
ready = bool(st.session_state.offer_items and selected_customer_id)

if ready:
    if st.button(
        f"🚀  {t('generate_offer')} — {selected_name}",
        type="primary", use_container_width=True,
    ):
        request = {
            "customer_id": selected_customer_id,
            "mode": mode,
            "items": [
                {
                    "product_code": i["product_code"],
                    "quantity": i["quantity"],
                    **({"discount_override": i["discount_override"]} if i.get("discount_override") else {}),
                }
                for i in st.session_state.offer_items
            ],
            "show_discount": show_discount,
            "show_vat": show_vat,
            "discount_level": discount_level,
            "validity_days": validity,
            "notes": notes,
        }
        if custom_discount_pct > 0:
            request["custom_discounts"] = [
                {"name": "Специална отстъпка", "percentage": custom_discount_pct}
            ]
        # Attach edit context so generate_offer knows it's an overwrite/revision
        if st.session_state.get("current_offer_number"):
            request["editing_offer_number"] = st.session_state.current_offer_number
            request["editing_spreadsheet_id"] = st.session_state.current_spreadsheet_id or ""
            request["editing_status"] = st.session_state.current_offer_status
            request["editing_base_id"] = st.session_state.current_offer_base_id or st.session_state.current_offer_number
            request["editing_version"] = st.session_state.current_offer_version

        with st.spinner(t("generating")):
            try:
                import json
                from pathlib import Path

                gen_result = generate_offer(request)
                url = gen_result["url"]
                offer_number = gen_result["offer_number"]
                spreadsheet_id = gen_result["spreadsheet_id"]
                pdf_url = gen_result["pdf_url"]

                # Update current edit context for subsequent regenerations
                st.session_state.current_offer_number = offer_number
                st.session_state.current_spreadsheet_id = spreadsheet_id
                # Status stays "draft" until explicitly sent

                # Read pdf_path from tmp file (not returned by generate_offer)
                tmp_dir = Path(__file__).resolve().parent.parent / ".tmp"
                offer_file = tmp_dir / f"{offer_number.replace('/', '-')}_data.json"
                pdf_path = ""
                if offer_file.exists():
                    with open(offer_file, encoding="utf-8") as f:
                        saved = json.load(f)
                    pdf_path = saved.get("pdf_path", "")

                st.session_state.offer_result = {
                    "url": url,
                    "pdf_path": pdf_path,
                    "pdf_url": pdf_url,
                    "offer_number": offer_number,
                    "customer_id": selected_customer_id,
                    "mode": mode,
                }
                st.session_state.offer_email_preview = None
                st.success(f"✅ {t('offer_ready')} — **{offer_number}**")
            except Exception as e:
                st.error(f"{t('error')}: {e}")
else:
    st.caption(f"⚠️ {t('select_customer_add_product')}")

st.markdown("<hr>", unsafe_allow_html=True)

# ── Main two-panel layout ─────────────────────────────────────────
col_search, col_selected = st.columns([1, 1], gap="medium")

# ── LEFT: Search ──────────────────────────────────────────────────
with col_search:
    st.markdown('<div class="panel-hdr">🔍 ' + t("step2_products") + '</div>', unsafe_allow_html=True)

    categories, brands = get_filter_options()
    fc1, fc2 = st.columns(2)
    with fc1:
        sel_cat = st.selectbox(
            t("filter_category"), [t("filter_all")] + categories,
            key=f"ofr_cat_{_v}", label_visibility="collapsed",
        )
    with fc2:
        sel_brand = st.selectbox(
            t("filter_brand"), [t("filter_all")] + brands,
            key=f"ofr_brand_{_v}", label_visibility="collapsed",
        )

    query = st.text_input(
        "search", placeholder=t("search"),
        key=f"ofr_search_{_v}", label_visibility="collapsed",
    )

    show_results = query or sel_cat != t("filter_all") or sel_brand != t("filter_all")

    with st.container(height=370, border=False):
        if show_results:
            results = search_products(query, limit=50) if query else load_all_products()
            if sel_cat != t("filter_all"):
                results = [p for p in results if p.get("category", "") == sel_cat]
            if sel_brand != t("filter_all"):
                results = [p for p in results if p.get("brand", "") == sel_brand]

            if results:
                added_codes = {i["product_code"] for i in st.session_state.offer_items}
                for p in results[:30]:
                    code = p.get("product_code", "")
                    sup_code = p.get("supplier_code", "")
                    name = p.get("name", "")
                    price = p.get("base_price", "")
                    brand = p.get("brand", "")

                    rc1, rc2 = st.columns([5, 1])
                    with rc1:
                        code_str = f"**{code}** ({sup_code})" if sup_code else f"**{code}**"
                        st.markdown(f"{code_str} — {name}")
                        st.caption(f"{brand} · {price} EUR")
                    with rc2:
                        if code in added_codes:
                            st.markdown("✅")
                        elif st.button("➕", key=f"add_{code}_{_v}", use_container_width=True):
                            st.session_state.offer_items.append({
                                "product_code": code,
                                "supplier_code": sup_code,
                                "name": name,
                                "quantity": 1,
                            })
                            st.rerun()
            else:
                st.info(t("no_results"))
        else:
            st.caption("👆 " + t("search_add_products"))

# ── RIGHT: Selected items ─────────────────────────────────────────
with col_selected:
    n_items = len(st.session_state.offer_items)
    label = f"🛒 {t('selected_products')} ({n_items})" if n_items else f"🛒 {t('selected_products')}"
    st.markdown(f'<div class="panel-hdr">{label}</div>', unsafe_allow_html=True)

    # Column header labels
    lh1, lh2, lh3, lh4 = st.columns([4, 1, 1, 0.6])
    with lh1:
        st.caption("Продукт")
    with lh2:
        st.caption(t("qty"))
    with lh3:
        st.caption(t("discount_pct"))

    with st.container(height=395, border=False):
        if st.session_state.offer_items:
            items_to_remove = []
            for idx, item in enumerate(st.session_state.offer_items):
                sc1, sc2, sc3, sc4 = st.columns([4, 1, 1, 0.6])
                with sc1:
                    sup = item.get("supplier_code", "")
                    code_label = f"**{item['product_code']}**" + (f" ({sup})" if sup else "")
                    name_short = item.get("name", "")[:45]
                    st.markdown(f"{code_label}  \n{name_short}")
                with sc2:
                    new_qty = st.number_input(
                        "q", min_value=1, value=item["quantity"],
                        key=f"qty_{idx}_{_v}", label_visibility="collapsed",
                    )
                    st.session_state.offer_items[idx]["quantity"] = new_qty
                with sc3:
                    new_disc = st.number_input(
                        "d", min_value=0.0, max_value=99.0,
                        value=float(item.get("discount_override") or 0.0),
                        step=0.5, key=f"disc_{idx}_{_v}",
                        label_visibility="collapsed",
                    )
                    st.session_state.offer_items[idx]["discount_override"] = new_disc if new_disc > 0 else None
                with sc4:
                    if st.button("🗑", key=f"rm_{idx}_{_v}", use_container_width=True):
                        items_to_remove.append(idx)

            for idx in reversed(items_to_remove):
                st.session_state.offer_items.pop(idx)
                st.rerun()
        else:
            st.info(t("search_add_left"))

# ── Result ────────────────────────────────────────────────────────
if st.session_state.offer_result:
    result = st.session_state.offer_result
    st.markdown("---")

    r1, r2, r3 = st.columns(3)
    with r1:
        st.link_button(
            f"📊 {t('open_sheets')}", result["url"], use_container_width=True,
        )
    with r2:
        if result.get("pdf_path"):
            if st.button(f"📄 {t('preview_pdf')}", use_container_width=True):
                from pathlib import Path as _Path
                p = _Path(result["pdf_path"])
                if p.exists():
                    st.session_state.offer_pdf_bytes = p.read_bytes()
                    cust = load_customer(result["customer_id"])
                    cust_name = cust.get("company_name", "") if cust else ""
                    doc_label = "Оферта" if result.get("mode") == "offer" else "Ценова листа"
                    st.session_state.offer_pdf_name = (
                        f"{result.get('offer_number', 'offer')} _ {cust_name} - {doc_label}.pdf"
                    )
                    st.rerun()
                else:
                    st.error(t("error"))
    with r3:
        if st.button(f"✉️ {t('send_to_customer')}", use_container_width=True):
            with st.spinner(t("preparing_preview")):
                try:
                    customer = load_customer(result["customer_id"])
                    offer_num = result.get("offer_number", "")
                    prepared = prepare_offer_email(offer_num, customer, result.get("mode", "offer"))
                    st.session_state.offer_email_preview = {
                        **prepared,
                        "customer": customer,
                        "offer_number": offer_num,
                        "pdf_path": result.get("pdf_path", ""),
                        "pdf_url": result.get("pdf_url", result["url"] + "/export?format=pdf"),
                        "spreadsheet_url": result["url"],
                        "mode": result.get("mode", "offer"),
                    }
                    st.rerun()
                except Exception as e:
                    st.error(f"{t('send_error')}: {e}")

    # PDF preview
    if st.session_state.get("offer_pdf_bytes"):
        try:
            pc1, pc2 = st.columns([5, 1])
            with pc2:
                if st.button(t("close_pdf"), key="ofr_pdf_close"):
                    del st.session_state.offer_pdf_bytes
                    st.rerun()
            pdf_b64 = base64.b64encode(st.session_state.offer_pdf_bytes).decode()
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{pdf_b64}" '
                f'width="100%" height="780" '
                f'style="border: 1px solid #ddd; border-radius: 6px;"></iframe>',
                unsafe_allow_html=True,
            )
            st.download_button(
                f"⬇️ {t('download_pdf')}",
                data=st.session_state.offer_pdf_bytes,
                file_name=st.session_state.get("offer_pdf_name", "offer.pdf"),
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception:
            del st.session_state.offer_pdf_bytes
            st.rerun()

    # Email preview
    if st.session_state.offer_email_preview:
        preview = st.session_state.offer_email_preview
        st.markdown("---")
        st.subheader(t("email_preview"))

        edited_to = st.text_input(t("email_to"), value=preview["to"], key="ofr_email_to")
        edited_subject = st.text_input(t("email_subject"), value=preview["subject"], key="ofr_email_subj")
        st.caption(t("available_vars", vars=", ".join(f"{{{v}}}" for v in preview["available_variables"])))
        edited_body = st.text_area(t("email_body"), value=preview["body"], height=220, key="ofr_email_body")

        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button(t("approve_send"), type="primary", use_container_width=True, key="ofr_approve"):
                with st.spinner(t("sending_email")):
                    try:
                        send_offer_to_customer(
                            preview["offer_number"], preview["customer"],
                            preview["spreadsheet_url"], preview["pdf_url"],
                            preview["mode"],
                            subject_override=edited_subject,
                            body_text_override=edited_body,
                            email_override=edited_to,
                            pdf_path=preview.get("pdf_path", ""),
                        )
                        st.session_state.offer_email_preview = None
                        st.success(f"✅ {t('sent_to')} {preview['to']}")
                    except Exception as e:
                        st.error(f"{t('send_error')}: {e}")
        with bc2:
            if st.button(t("cancel"), use_container_width=True, key="ofr_cancel"):
                st.session_state.offer_email_preview = None
                st.rerun()
