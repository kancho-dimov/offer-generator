"""Create Order page — from existing offer or standalone."""

import base64

import streamlit as st
from datetime import date, timedelta

from i18n import get_lang, setup_page, t
from tools.discount_engine import load_customer
from tools.generate_order import (
    generate_order,
    load_delivery_terms,
    load_logistics_for_codes,
    load_payment_terms,
)
from tools.offer_log import get_offer_log
from tools.product_search import load_all_products, search_products
from tools.send_email import _download_pdf, prepare_order_email, send_order_to_cs, send_order_to_customer
from tools.sheets_api import read_sheet

MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"

setup_page("Нова Поръчка", "📦")

# --- Session state ---
if "order_items" not in st.session_state:
    st.session_state.order_items = []
if "order_result" not in st.session_state:
    st.session_state.order_result = None
if "loaded_offer" not in st.session_state:
    st.session_state.loaded_offer = None
if "order_email_preview" not in st.session_state:
    st.session_state.order_email_preview = None
if "order_form_ver" not in st.session_state:
    st.session_state.order_form_ver = 0

# Form version suffix — forces fresh widgets after reset
_v = st.session_state.order_form_ver

# Ensure items are cleared after reset (safeguard against stale state)
if st.session_state.get("loaded_offer") == "__reset__" and st.session_state.get("order_items"):
    st.session_state.order_items = []

# --- Title + Reset ---
tc1, tc2 = st.columns([4, 1])
with tc1:
    st.title(t("new_order_title"))
with tc2:
    if st.button(t("new_order_reset"), use_container_width=True):
        st.session_state.order_form_ver += 1
        st.session_state.order_items = []
        st.session_state.order_result = None
        st.session_state.loaded_offer = "__reset__"
        st.session_state.order_email_preview = None
        if "order_pdf_bytes" in st.session_state:
            del st.session_state.order_pdf_bytes
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
def cached_delivery_terms():
    return load_delivery_terms()


@st.cache_data(ttl=300)
def cached_payment_terms():
    return load_payment_terms()


@st.cache_data(ttl=300)
def cached_offers():
    return get_offer_log()


@st.cache_data(ttl=300)
def get_filter_options():
    products = load_all_products()
    categories = sorted({p.get("category", "") for p in products if p.get("category", "").strip()})
    brands = sorted({p.get("brand", "") for p in products if p.get("brand", "").strip()})
    return categories, brands


# --- Step 0: Mode selection ---
st.subheader(t("mode"))
order_mode = st.radio(
    t("mode_question"),
    ["from_offer", "standalone"],
    format_func=lambda x: t("from_offer") if x == "from_offer" else t("standalone"),
    horizontal=True,
    key=f"ord_mode_{_v}",
)

# --- Step 1: Customer / Offer ---
st.subheader(t("step1_customer"))

customers = load_customers()
customer_map = {c["company_name"]: c for c in customers}
selected_customer = None
selected_offer_number = ""

if order_mode == "from_offer":
    offers = cached_offers()
    available_offers = [
        o for o in offers
        if o.get("status") not in ("converted_to_order", "expired")
    ]

    if available_offers:
        offer_labels = {
            f"{o['offer_number']} | {o.get('customer_name', '')} | {o.get('created_date', '')} | {float(o.get('total_incl_vat', 0)):.2f} EUR": o
            for o in reversed(available_offers)
        }
        selected_label = st.selectbox(
            t("select_offer"), list(offer_labels.keys()), key=f"ord_offer_{_v}",
            index=None, placeholder=t("select_customer_placeholder"),
        )
        offer_data = offer_labels.get(selected_label) if selected_label else None

        if offer_data:
            selected_offer_number = offer_data["offer_number"]
            # Pre-select customer from offer
            offer_customer_id = offer_data.get("customer_id", "")
            pre_select_name = None
            for c in customers:
                if c.get("customer_id") == offer_customer_id:
                    pre_select_name = c["company_name"]
                    break

            # Customer selector — pre-selected from offer but overridable
            customer_names = list(customer_map.keys())
            default_idx = customer_names.index(pre_select_name) if pre_select_name in customer_names else 0
            cc1, cc2 = st.columns([4, 1])
            with cc1:
                selected_name = st.selectbox(t("customer"), customer_names, index=default_idx, key=f"ord_cust_offer_{_v}")
            with cc2:
                st.page_link("pages/5_Настройки.py", label=t("customer_settings_link"), icon="⚙️")
            selected_customer = customer_map.get(selected_name)

            # Load offer items if not already loaded for this offer (skip after reset)
            if st.session_state.loaded_offer not in (selected_offer_number, "__reset__"):
                import json
                from pathlib import Path

                tmp_dir = Path(__file__).resolve().parent.parent / ".tmp"
                offer_file = tmp_dir / f"{selected_offer_number.replace('/', '-')}_data.json"

                if offer_file.exists():
                    with open(offer_file, encoding="utf-8") as f:
                        saved = json.load(f)
                    lines = saved.get("result", {}).get("lines", [])
                    req_items = saved.get("request", {}).get("items", [])
                    qty_map = {i["product_code"]: i.get("quantity", 1) for i in req_items}

                    st.session_state.order_items = [
                        {
                            "product_code": line["product_code"],
                            "name": line.get("name", ""),
                            "brand": line.get("brand", ""),
                            "base_price": line.get("base_price", 0),
                            "quantity": qty_map.get(line["product_code"], line.get("quantity", 1)),
                            "measure_unit": "pcs",
                            "discount_override": line.get("total_discount_pct", 0) if line.get("total_discount_pct", 0) > 0 else None,
                        }
                        for line in lines
                        if "error" not in line
                    ]
                    st.session_state.loaded_offer = selected_offer_number
                else:
                    st.warning(t("offer_data_missing"))
                    st.session_state.loaded_offer = selected_offer_number
    else:
        st.warning(t("no_offers_to_convert"))
        # Still show customer selector even when no offers available
        cc1, cc2 = st.columns([4, 1])
        with cc1:
            selected_name = st.selectbox(
                t("customer"), list(customer_map.keys()), key=f"ord_cust_no_offer_{_v}",
                index=None, placeholder=t("select_customer_placeholder"),
            )
        with cc2:
            if selected_name:
                st.page_link("pages/5_Настройки.py", label=t("customer_settings_link"), icon="⚙️")
        selected_customer = customer_map.get(selected_name) if selected_name else None
        selected_offer_number = ""
else:
    # Standalone: pick customer
    cc1, cc2 = st.columns([4, 1])
    with cc1:
        selected_name = st.selectbox(
            t("customer"), list(customer_map.keys()), key=f"ord_cust_standalone_{_v}",
            index=None, placeholder=t("select_customer_placeholder"),
        )
    with cc2:
        if selected_name:
            st.page_link("pages/5_Настройки.py", label=t("customer_settings_link"), icon="⚙️")
    selected_customer = customer_map.get(selected_name) if selected_name else None
    selected_offer_number = ""
    st.session_state.loaded_offer = None

# --- Delivery address (dropdown with customer addresses + custom option) ---
if selected_customer:
    addr_options = []
    default_del = selected_customer.get("delivery_address", "").strip()
    main_addr = selected_customer.get("address", "").strip()
    if default_del:
        addr_options.append(default_del)
    if main_addr and main_addr != default_del:
        addr_options.append(main_addr)
    addr_options.append(t("custom_address"))

    ac1, ac2 = st.columns([1, 1])
    with ac1:
        selected_addr = st.selectbox(
            t("delivery_address"), addr_options,
            key=f"ord_addr_sel_{selected_customer.get('customer_id', '')}_{_v}",
        )
    with ac2:
        prefill = "" if selected_addr == t("custom_address") else selected_addr
        delivery_address = st.text_input(
            t("custom_address_input"), value=prefill,
            key=f"ord_addr_edit_{selected_addr}_{_v}",
        )
else:
    delivery_address = st.text_input(t("delivery_address"), value="", key=f"ord_delivery_addr_empty_{_v}")

# --- Step 2: Products ---
st.subheader(t("products"))

col_search, col_items = st.columns([1, 2])

with col_search:
    # Category / Brand filters
    categories, brands = get_filter_options()
    fc1, fc2 = st.columns(2)
    with fc1:
        sel_cat = st.selectbox(t("filter_category"), [t("filter_all")] + categories, key=f"ord_cat_{_v}")
    with fc2:
        sel_brand = st.selectbox(t("filter_brand"), [t("filter_all")] + brands, key=f"ord_brand_{_v}")

    query = st.text_input(t("search"), key=f"order_search_{_v}")

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
                        if st.button("➕", key=f"oadd_{code}_{_v}"):
                            existing = [i for i in st.session_state.order_items if i["product_code"] == code]
                            if not existing:
                                st.session_state.order_items.append({
                                    "product_code": code,
                                    "supplier_code": sup_code,
                                    "name": name,
                                    "brand": brand,
                                    "base_price": float(str(price).replace(",", "")) if price else 0,
                                    "quantity": 1,
                                    "measure_unit": "pcs",
                                })
                                st.rerun()
        else:
            st.info(t("no_results"))

with col_items:
    st.write(f"**{t('selected_products')}**")
    if st.session_state.order_items:
        # Load logistics for all product codes
        codes = [i["product_code"] for i in st.session_state.order_items]
        logistics = load_logistics_for_codes(codes)

        items_to_remove = []
        for idx, item in enumerate(st.session_state.order_items):
            code = item["product_code"]
            logi = logistics.get(code, {})
            ppc = int(logi.get("pcs_per_carton", 0) or 0)

            c1, c2, c3, c4, c5, c6 = st.columns([3, 0.8, 1.2, 0.8, 2, 0.4])
            with c1:
                sup = item.get("supplier_code", "")
                code_label = f"**{code}** ({sup})" if sup else f"**{code}**"
                st.write(f"{code_label} — {item.get('name', '')}")
                st.caption(f"{item.get('brand', '')} | {item.get('base_price', '')} EUR/{t('pcs_label')}")
            with c2:
                new_qty = st.number_input(
                    t("qty"), min_value=1, value=item["quantity"],
                    key=f"oqty_{idx}_{_v}",
                )
                st.session_state.order_items[idx]["quantity"] = new_qty
            with c3:
                unit_options = ["pcs"]
                if ppc > 0:
                    unit_options.append("carton")
                unit_labels = {"pcs": t("pcs_label"), "carton": f"{t('carton_label')} ({ppc} {t('pcs_label')})"}
                new_unit = st.selectbox(
                    t("measure"), options=unit_options,
                    format_func=lambda x, ul=unit_labels: ul.get(x, x),
                    index=unit_options.index(item.get("measure_unit", "pcs")) if item.get("measure_unit", "pcs") in unit_options else 0,
                    key=f"ounit_{idx}_{_v}",
                )
                st.session_state.order_items[idx]["measure_unit"] = new_unit
            with c4:
                new_disc = st.number_input(
                    t("discount_pct"), min_value=0.0, max_value=99.0,
                    value=float(item.get("discount_override", 0.0) or 0.0),
                    step=0.5, key=f"odisc_{idx}_{_v}",
                )
                st.session_state.order_items[idx]["discount_override"] = new_disc if new_disc > 0 else None
            with c5:
                # Show conversion
                eff_ppc = ppc if new_unit == "carton" and ppc > 0 else 1
                total_pcs = new_qty * eff_ppc
                unit_price = item.get("base_price", 0)
                line_total = round(total_pcs * unit_price, 2)
                st.caption(f"= {total_pcs} {t('pcs_label')} x {unit_price} = **{line_total:.2f} EUR**")
            with c6:
                if st.button("🗑️", key=f"orm_{idx}_{_v}"):
                    items_to_remove.append(idx)

        for idx in reversed(items_to_remove):
            st.session_state.order_items.pop(idx)
            st.rerun()
    else:
        st.info(t("search_add_products"))

# --- Step 3: Delivery & Payment ---
st.subheader(t("terms"))

delivery_terms_list = cached_delivery_terms()
payment_terms_list = cached_payment_terms()

lang = get_lang()
term_key = "name_en" if lang == "en" else "name_bg"

col_a, col_b, col_c = st.columns(3)

with col_a:
    del_options = [dt.get(term_key, dt.get("name_bg", "")) for dt in delivery_terms_list] if delivery_terms_list else ["Door delivery"]
    delivery_terms = st.selectbox(t("delivery_terms"), del_options, key=f"ord_del_terms_{_v}")

    default_delivery_date = date.today() + timedelta(days=14)
    delivery_date = st.date_input(t("delivery_date"), value=default_delivery_date, key=f"ord_del_date_{_v}")

with col_b:
    pay_options = [pt.get(term_key, pt.get("name_bg", "")) for pt in payment_terms_list] if payment_terms_list else ["Bank transfer 14 days"]
    payment_terms = st.selectbox(t("payment_terms"), pay_options, key=f"ord_pay_terms_{_v}")

with col_c:
    sales_agent = st.text_input(t("sales_agent"), value="12104", key=f"ord_agent_{_v}")

notes = st.text_area(t("notes"), placeholder=t("notes_placeholder"), key=f"ord_notes_{_v}")

# --- Step 4: Generate ---
st.subheader(t("step4_generate"))

if st.session_state.order_items and selected_customer:
    if st.button(t("generate_order"), type="primary", use_container_width=True):
        request = {
            "customer_id": selected_customer["customer_id"],
            "items": [
                {
                    "product_code": i["product_code"],
                    "quantity": i["quantity"],
                    "measure_unit": i.get("measure_unit", "pcs"),
                    **({"discount_override": i["discount_override"]} if i.get("discount_override") else {}),
                }
                for i in st.session_state.order_items
            ],
            "delivery_terms": delivery_terms,
            "payment_terms": payment_terms,
            "delivery_date": delivery_date.strftime("%d.%m.%Y"),
            "delivery_address": delivery_address,
            "sales_agent_code": sales_agent,
            "notes": notes,
            "show_discount": True,
            "show_vat": True,
        }
        if selected_offer_number:
            request["offer_number"] = selected_offer_number

        with st.spinner(t("generating_order")):
            try:
                url = generate_order(request)
                # Load order data for email sending
                import json
                from pathlib import Path

                tmp_dir = Path(__file__).resolve().parent.parent / ".tmp"
                order_files = sorted(tmp_dir.glob("ORD-*_data.json"))
                order_data = {}
                if order_files:
                    with open(order_files[-1], encoding="utf-8") as f:
                        order_data = json.load(f)

                st.session_state.order_result = {
                    "url": url,
                    "pdf_url": order_data.get("pdf_url", ""),
                    "order_number": order_data.get("order_number", ""),
                    "offer_number": selected_offer_number,
                    "customer": selected_customer,
                    "delivery_date": delivery_date.strftime("%d.%m.%Y"),
                    "delivery_terms": delivery_terms,
                    "payment_terms": payment_terms,
                    "delivery_address": delivery_address,
                    "sales_agent_code": sales_agent,
                    "total_excl_vat": order_data.get("total_excl_vat", 0),
                    "total_incl_vat": order_data.get("total_incl_vat", 0),
                }
                st.success(t("order_ready"))
            except Exception as e:
                st.error(f"{t('error')}: {e}")
else:
    st.warning(t("select_customer_add_product"))

# --- Result ---
if st.session_state.order_result:
    result = st.session_state.order_result
    st.markdown("---")
    st.subheader(t("result"))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.link_button(t("open_sheets"), result["url"], use_container_width=True)
    with col2:
        pdf_url = result.get("pdf_url", "")
        if pdf_url:
            if st.button(t("preview_pdf"), use_container_width=True):
                with st.spinner("..."):
                    pdf_bytes = _download_pdf(pdf_url)
                    if pdf_bytes:
                        st.session_state.order_pdf_bytes = pdf_bytes
                        cust_name = result.get("customer", {}).get("company_name", "")
                        st.session_state.order_pdf_name = f"{result.get('order_number', 'order')} _ {cust_name} - Поръчка.pdf"
                        st.rerun()
                    else:
                        st.error(t("error"))
    with col3:
        if st.button(t("send_to_cs"), use_container_width=True):
            try:
                send_order_to_cs(
                    result["order_number"],
                    result.get("offer_number", ""),
                    result["customer"],
                    result.get("sales_agent_code", "12104"),
                    result.get("delivery_terms", ""),
                    result.get("payment_terms", ""),
                    result.get("delivery_date", ""),
                    result.get("total_excl_vat", 0),
                    result.get("total_incl_vat", 0),
                    result["url"],
                    result.get("pdf_url", ""),
                    delivery_address=result.get("delivery_address", ""),
                )
                st.success(t("sent_to_cs"))
            except Exception as e:
                st.error(f"{t('send_error')}: {e}")
    with col4:
        if st.button(t("send_to_customer"), use_container_width=True):
            with st.spinner(t("preparing_preview")):
                try:
                    prepared = prepare_order_email(
                        result["order_number"],
                        result["customer"],
                        result.get("delivery_date", ""),
                    )
                    st.session_state.order_email_preview = {
                        **prepared,
                        "customer": result["customer"],
                        "order_number": result["order_number"],
                        "delivery_date": result.get("delivery_date", ""),
                        "pdf_url": result.get("pdf_url", ""),
                        "spreadsheet_url": result["url"],
                    }
                    st.rerun()
                except Exception as e:
                    st.error(f"{t('send_error')}: {e}")

    # --- PDF preview + download ---
    if st.session_state.get("order_pdf_bytes"):
        st.markdown("---")
        pc1, pc2 = st.columns([4, 1])
        with pc2:
            if st.button(t("close_pdf"), key="ord_pdf_close"):
                del st.session_state.order_pdf_bytes
                st.rerun()
        pdf_b64 = base64.b64encode(st.session_state.order_pdf_bytes).decode()
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{pdf_b64}" '
            f'width="100%" height="800" style="border: 1px solid #ddd; border-radius: 4px;"></iframe>',
            unsafe_allow_html=True,
        )
        st.download_button(
            t("download_pdf"),
            data=st.session_state.order_pdf_bytes,
            file_name=st.session_state.get("order_pdf_name", "order.pdf"),
            mime="application/pdf",
            use_container_width=True,
        )

    # --- Email preview / edit / approve ---
    if st.session_state.order_email_preview:
        preview = st.session_state.order_email_preview
        st.markdown("---")
        st.subheader(t("email_preview"))

        edited_to = st.text_input(t("email_to"), value=preview["to"], key="ord_email_to")
        edited_subject = st.text_input(t("email_subject"), value=preview["subject"], key="ord_email_subj")
        st.caption(t("available_vars", vars=", ".join(f"{{{v}}}" for v in preview["available_variables"])))
        edited_body = st.text_area(t("email_body"), value=preview["body"], height=250, key="ord_email_body")

        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button(t("approve_send"), type="primary", use_container_width=True, key="ord_approve"):
                with st.spinner(t("sending_email")):
                    try:
                        send_order_to_customer(
                            preview["order_number"],
                            preview["customer"],
                            preview["delivery_date"],
                            preview["spreadsheet_url"],
                            preview["pdf_url"],
                            subject_override=edited_subject,
                            body_text_override=edited_body,
                            email_override=edited_to,
                        )
                        st.session_state.order_email_preview = None
                        st.success(f"{t('sent_to')} {preview['to']}")
                    except Exception as e:
                        st.error(f"{t('send_error')}: {e}")
        with bc2:
            if st.button(t("cancel"), use_container_width=True, key="ord_cancel"):
                st.session_state.order_email_preview = None
                st.rerun()
