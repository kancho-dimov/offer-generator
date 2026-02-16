"""Create Offer page — step-by-step offer/pricelist creation."""

import base64

import streamlit as st

from i18n import setup_page, t
from tools.discount_engine import load_customer
from tools.generate_offer import generate_offer
from tools.product_search import load_all_products, search_products
from tools.send_email import _download_pdf, prepare_offer_email, send_offer_to_customer
from tools.sheets_api import read_sheet

MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"

setup_page("Нова Оферта", "📋")

# Initialize session state
if "offer_items" not in st.session_state:
    st.session_state.offer_items = []
if "offer_result" not in st.session_state:
    st.session_state.offer_result = None
if "offer_email_preview" not in st.session_state:
    st.session_state.offer_email_preview = None
if "offer_form_ver" not in st.session_state:
    st.session_state.offer_form_ver = 0

# Form version suffix — forces fresh widgets after reset
_v = st.session_state.offer_form_ver

# Ensure items are cleared after reset (safeguard against stale state)
if st.session_state.get("_offer_reset") and st.session_state.get("offer_items"):
    st.session_state.offer_items = []
    st.session_state._offer_reset = False

# --- Title + Reset ---
tc1, tc2 = st.columns([4, 1])
with tc1:
    st.title(t("new_offer_title"))
with tc2:
    if st.button(t("new_offer_reset"), use_container_width=True):
        st.session_state.offer_form_ver += 1
        st.session_state.offer_items = []
        st.session_state.offer_result = None
        st.session_state.offer_email_preview = None
        st.session_state._offer_reset = True
        if "offer_pdf_bytes" in st.session_state:
            del st.session_state.offer_pdf_bytes
        st.rerun()


@st.cache_data(ttl=300)
def load_customers():
    rows = read_sheet(MASTER_CATALOG_ID, "'Customers'!A:N")
    if not rows or len(rows) < 2:
        return []
    headers = rows[0]
    customers = []
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        row += [""] * (len(headers) - len(row))
        customers.append(dict(zip(headers, row)))
    return customers


@st.cache_data(ttl=300)
def get_filter_options():
    products = load_all_products()
    categories = sorted({p.get("category", "") for p in products if p.get("category", "").strip()})
    brands = sorted({p.get("brand", "") for p in products if p.get("brand", "").strip()})
    return categories, brands


# --- Step 1: Customer ---
st.subheader(t("step1_customer"))
customers = load_customers()
customer_names = {c["company_name"]: c["customer_id"] for c in customers}
cc1, cc2 = st.columns([4, 1])
with cc1:
    selected_name = st.selectbox(
        t("customer"), options=list(customer_names.keys()), key=f"ofr_cust_{_v}",
        index=None, placeholder=t("select_customer_placeholder"),
    )
with cc2:
    if selected_name:
        st.page_link("pages/5_Настройки.py", label=t("customer_settings_link"), icon="⚙️")
selected_customer_id = customer_names.get(selected_name, "")

# --- Step 2: Add Products ---
st.subheader(t("step2_products"))

col_search, col_results = st.columns([1, 2])

with col_search:
    # Category / Brand filters
    categories, brands = get_filter_options()
    fc1, fc2 = st.columns(2)
    with fc1:
        sel_cat = st.selectbox(t("filter_category"), [t("filter_all")] + categories, key=f"ofr_cat_{_v}")
    with fc2:
        sel_brand = st.selectbox(t("filter_brand"), [t("filter_all")] + brands, key=f"ofr_brand_{_v}")

    query = st.text_input(t("search"), key=f"ofr_search_{_v}")

    # Search: text query and/or filters
    show_results = query or sel_cat != t("filter_all") or sel_brand != t("filter_all")
    if show_results:
        if query:
            results = search_products(query, limit=50)
        else:
            results = load_all_products()
        if sel_cat != t("filter_all"):
            results = [p for p in results if p.get("category", "") == sel_cat]
        if sel_brand != t("filter_all"):
            results = [p for p in results if p.get("brand", "") == sel_brand]

        if results:
            for p in results[:20]:
                code = p.get("product_code", "")
                sup_code = p.get("supplier_code", "")
                name = p.get("name", "")
                price = p.get("base_price", "")
                brand = p.get("brand", "")
                code_label = f"**{code}** ({sup_code})" if sup_code else f"**{code}**"

                with st.container():
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.write(f"{code_label} — {name}")
                        st.caption(f"{brand} | {price} EUR")
                    with c2:
                        if st.button("➕", key=f"add_{code}_{_v}"):
                            existing = [i for i in st.session_state.offer_items if i["product_code"] == code]
                            if not existing:
                                st.session_state.offer_items.append({
                                    "product_code": code,
                                    "supplier_code": sup_code,
                                    "name": name,
                                    "quantity": 1,
                                })
                                st.rerun()
        else:
            st.info(t("no_results"))

with col_results:
    st.write(f"**{t('selected_products')}**")
    if st.session_state.offer_items:
        items_to_remove = []
        for idx, item in enumerate(st.session_state.offer_items):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 0.5])
            with c1:
                sup = item.get('supplier_code', '')
                code_label = f"**{item['product_code']}** ({sup})" if sup else f"**{item['product_code']}**"
                st.write(f"{code_label} — {item.get('name', '')}")
            with c2:
                new_qty = st.number_input(
                    t("qty"), min_value=1, value=item["quantity"],
                    key=f"qty_{idx}_{_v}", label_visibility="collapsed",
                )
                st.session_state.offer_items[idx]["quantity"] = new_qty
            with c3:
                new_disc = st.number_input(
                    t("discount_pct"), min_value=0.0, max_value=99.0,
                    value=float(item.get("discount_override") or 0.0),
                    step=0.5, key=f"disc_{idx}_{_v}",
                    placeholder=t("discount_auto"),
                )
                st.session_state.offer_items[idx]["discount_override"] = new_disc if new_disc > 0 else None
            with c4:
                if st.button("🗑️", key=f"rm_{idx}_{_v}"):
                    items_to_remove.append(idx)

        for idx in reversed(items_to_remove):
            st.session_state.offer_items.pop(idx)
            st.rerun()
    else:
        st.info(t("search_add_left"))

# --- Step 3: Configure ---
st.subheader(t("step3_settings"))

col_a, col_b, col_c = st.columns(3)
with col_a:
    mode = st.radio(t("type"), ["offer", "pricelist"],
                    format_func=lambda x: t("offer_label") if x == "offer" else t("pricelist_label"),
                    key=f"ofr_mode_{_v}")
with col_b:
    show_discount = st.checkbox(t("show_discounts"), value=True, key=f"ofr_show_disc_{_v}")
    show_vat = st.checkbox(t("show_vat"), value=True, key=f"ofr_show_vat_{_v}")
with col_c:
    validity = st.number_input(t("validity_days"), min_value=1, value=30, key=f"ofr_validity_{_v}")

    def _discount_label(x):
        if x == "line":
            return t("per_product")
        if x == "group":
            return t("per_brand")
        return t("per_category")

    discount_level = st.selectbox(t("discount_level"), ["line", "group", "category"],
                                   format_func=_discount_label, key=f"ofr_disc_level_{_v}")

notes = st.text_area(t("notes"), placeholder=t("notes_placeholder"), key=f"ofr_notes_{_v}")

custom_discount_pct = st.number_input(t("extra_discount"), min_value=0.0, max_value=50.0, value=0.0, step=0.5, key=f"ofr_extra_disc_{_v}")

# --- Step 4: Generate ---
st.subheader(t("step4_generate"))

if st.session_state.offer_items and selected_customer_id:
    if st.button(t("generate_offer"), type="primary", use_container_width=True):
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
            request["custom_discounts"] = [{"name": "Специална отстъпка", "percentage": custom_discount_pct}]

        with st.spinner(t("generating")):
            try:
                url = generate_offer(request)
                # Load the saved offer data for PDF URL and offer number
                import json
                from pathlib import Path
                tmp_dir = Path(__file__).resolve().parent.parent / ".tmp"
                offer_files = sorted(tmp_dir.glob("*_data.json"), key=lambda f: f.stat().st_mtime)
                pdf_url = ""
                offer_number = ""
                if offer_files:
                    with open(offer_files[-1], encoding="utf-8") as f:
                        saved = json.load(f)
                    pdf_url = saved.get("pdf_url", "")
                    offer_number = saved.get("offer_number", "")

                st.session_state.offer_result = {
                    "url": url,
                    "pdf_url": pdf_url,
                    "offer_number": offer_number,
                    "customer_id": selected_customer_id,
                    "mode": mode,
                }
                st.session_state.offer_email_preview = None
                st.success(t("offer_ready"))
            except Exception as e:
                st.error(f"{t('error')}: {e}")
else:
    st.warning(t("select_customer_add_product"))

# Show result
if st.session_state.offer_result:
    result = st.session_state.offer_result
    st.markdown("---")
    st.subheader(t("result"))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.link_button(t("open_sheets"), result["url"], use_container_width=True)
    with col2:
        pdf_url = result.get("pdf_url", "")
        if pdf_url:
            if st.button(t("preview_pdf"), use_container_width=True):
                with st.spinner("..."):
                    pdf_bytes = _download_pdf(pdf_url)
                    if pdf_bytes:
                        st.session_state.offer_pdf_bytes = pdf_bytes
                        cust = load_customer(result["customer_id"])
                        cust_name = cust.get("company_name", "") if cust else ""
                        doc_label = "Оферта" if result.get("mode") == "offer" else "Ценова листа"
                        st.session_state.offer_pdf_name = f"{result.get('offer_number', 'offer')} _ {cust_name} - {doc_label}.pdf"
                        st.rerun()
                    else:
                        st.error(t("error"))
    with col3:
        if st.button(t("send_to_customer"), use_container_width=True):
            with st.spinner(t("preparing_preview")):
                try:
                    customer = load_customer(result["customer_id"])
                    offer_num = result.get("offer_number", "")
                    prepared = prepare_offer_email(offer_num, customer, result.get("mode", "offer"))
                    st.session_state.offer_email_preview = {
                        **prepared,
                        "customer": customer,
                        "offer_number": offer_num,
                        "pdf_url": result.get("pdf_url", result["url"] + "/export?format=pdf"),
                        "spreadsheet_url": result["url"],
                        "mode": result.get("mode", "offer"),
                    }
                    st.rerun()
                except Exception as e:
                    st.error(f"{t('send_error')}: {e}")

    # --- PDF preview + download ---
    if st.session_state.get("offer_pdf_bytes"):
        st.markdown("---")
        pc1, pc2 = st.columns([4, 1])
        with pc2:
            if st.button(t("close_pdf"), key="ofr_pdf_close"):
                del st.session_state.offer_pdf_bytes
                st.rerun()
        pdf_b64 = base64.b64encode(st.session_state.offer_pdf_bytes).decode()
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{pdf_b64}" '
            f'width="100%" height="800" style="border: 1px solid #ddd; border-radius: 4px;"></iframe>',
            unsafe_allow_html=True,
        )
        st.download_button(
            t("download_pdf"),
            data=st.session_state.offer_pdf_bytes,
            file_name=st.session_state.get("offer_pdf_name", "offer.pdf"),
            mime="application/pdf",
            use_container_width=True,
        )

    # --- Email preview / edit / approve ---
    if st.session_state.offer_email_preview:
        preview = st.session_state.offer_email_preview
        st.markdown("---")
        st.subheader(t("email_preview"))

        edited_to = st.text_input(t("email_to"), value=preview["to"], key="ofr_email_to")
        edited_subject = st.text_input(t("email_subject"), value=preview["subject"], key="ofr_email_subj")
        st.caption(t("available_vars", vars=", ".join(f"{{{v}}}" for v in preview["available_variables"])))
        edited_body = st.text_area(t("email_body"), value=preview["body"], height=250, key="ofr_email_body")

        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button(t("approve_send"), type="primary", use_container_width=True, key="ofr_approve"):
                with st.spinner(t("sending_email")):
                    try:
                        send_offer_to_customer(
                            preview["offer_number"],
                            preview["customer"],
                            preview["spreadsheet_url"],
                            preview["pdf_url"],
                            preview["mode"],
                            subject_override=edited_subject,
                            body_text_override=edited_body,
                            email_override=edited_to,
                        )
                        st.session_state.offer_email_preview = None
                        st.success(f"{t('sent_to')} {preview['to']}")
                    except Exception as e:
                        st.error(f"{t('send_error')}: {e}")
        with bc2:
            if st.button(t("cancel"), use_container_width=True, key="ofr_cancel"):
                st.session_state.offer_email_preview = None
                st.rerun()
