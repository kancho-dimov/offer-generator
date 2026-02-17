"""Settings page — manage customers, terms, branding, and logistics import."""

import streamlit as st
from datetime import date

from i18n import setup_page, t
from tools.sheets_api import append_sheet, delete_rows, read_sheet, write_sheet

MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"

setup_page("Настройки", "⚙️")
st.title(t("settings_title"))


@st.cache_data(ttl=300)
def load_tab(tab_name: str, range_str: str) -> tuple[list[str], list[dict]]:
    """Load a tab as (headers, list_of_dicts)."""
    rows = read_sheet(MASTER_CATALOG_ID, range_str)
    if not rows or len(rows) < 2:
        return [], []
    headers = rows[0]
    items = []
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        row += [""] * (len(headers) - len(row))
        items.append(dict(zip(headers, row)))
    return headers, items


# --- Customers ---
st.subheader(t("customers"))
cust_headers, customers = load_tab("Customers", "'Customers'!A:N")

# Friendly column names for the table
_col_labels = {
    "customer_id": "ID", "company_name": t("company_name"),
    "contact_name": t("contact_name"), "email": "Email",
    "phone": t("phone_field"), "address": t("address_field"),
    "delivery_address": t("delivery_address_field"),
    "default_discount_pct": t("default_discount_field"),
    "notes": t("notes"),
}
_show_cols = ["company_name", "contact_name", "email", "phone", "address", "delivery_address"]

if customers:
    import pandas as pd

    df_display = pd.DataFrame([
        {_col_labels.get(k, k): c.get(k, "") for k in _show_cols}
        for c in customers
    ])
    event = st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="cust_table",
    )
    st.caption(f"{len(customers)} {t('customers_count')}")

    # Determine selected customer from table click
    selected_rows = event.selection.rows if event and event.selection else []
    if selected_rows:
        st.session_state._cust_selected_idx = selected_rows[0]
else:
    st.info(t("no_customers"))

# --- Customer management: Add / Edit / View ---
if customers:
    selected_idx = st.session_state.get("_cust_selected_idx")

    if selected_idx is not None and 0 <= selected_idx < len(customers):
        # Show selected customer details with edit form
        ec = customers[selected_idx]
        cust_label = f"{ec.get('company_name', '')} ({ec.get('customer_id', '')})"
        st.subheader(f"{cust_label}")

        _k = f"_e{selected_idx}"
        fc1, fc2 = st.columns(2)
        with fc1:
            e_company = st.text_input(t("company_name"), value=ec.get("company_name", ""), key=f"cust_company{_k}")
            e_eik = st.text_input(t("company_reg_id"), value=ec.get("company_reg_id", ""), key=f"cust_eik{_k}")
            e_vat = st.text_input(
                t("vat_number"), value=ec.get("vat_number", ""), key=f"cust_vat{_k}",
                placeholder=f"BG{e_eik}" if e_eik else "",
                help=t("vat_auto_hint"),
            )
            e_contact = st.text_input(t("contact_name"), value=ec.get("contact_name", ""), key=f"cust_contact{_k}")
            e_email = st.text_input(t("email_field"), value=ec.get("email", ""), key=f"cust_email{_k}")
        with fc2:
            e_phone = st.text_input(t("phone_field"), value=ec.get("phone", ""), key=f"cust_phone{_k}")
            e_address = st.text_input(t("address_field"), value=ec.get("address", ""), key=f"cust_address{_k}")
            e_delivery_addr = st.text_input(t("delivery_address_field"), value=ec.get("delivery_address", ""), key=f"cust_del_addr{_k}")
            e_sap = st.text_input(t("sap_number"), value=ec.get("customer_id", ""), key=f"cust_sap{_k}")
            disc_val = float(ec.get("default_discount_pct", 0) or 0)
            e_discount = st.number_input(t("default_discount_field"), min_value=0.0, max_value=99.0, value=disc_val, step=0.5, key=f"cust_disc{_k}")
        e_notes = st.text_input(t("notes"), value=ec.get("notes", ""), key=f"cust_notes{_k}")

        btn_c1, btn_c2, btn_c3 = st.columns(3)
        with btn_c1:
            if st.button(t("update_customer"), type="primary", use_container_width=True, key="btn_update_cust"):
                if not e_company.strip():
                    st.error(t("company_name_required"))
                else:
                    try:
                        customer_id = e_sap.strip() or e_company.strip()[:20]
                        vat_value = e_vat.strip() or (f"BG{e_eik.strip()}" if e_eik.strip() else "")
                        phone = f"'{e_phone.strip()}" if e_phone.strip().startswith("+") else e_phone.strip()
                        row = [
                            customer_id, e_company.strip(), e_contact.strip(), e_email.strip(),
                            phone, e_address.strip(),
                            ec.get("discount_tier", ""),
                            str(e_discount) if e_discount > 0 else "",
                            ec.get("payment_terms", ""),
                            e_notes.strip(),
                            ec.get("created_date", "") or date.today().strftime("%Y-%m-%d"),
                            vat_value, e_eik.strip(), e_delivery_addr.strip(),
                        ]
                        sheet_row = selected_idx + 2  # 1-indexed, skip header
                        write_sheet(MASTER_CATALOG_ID, f"'Customers'!A{sheet_row}:N{sheet_row}", [row])
                        st.success(t("customer_updated"))
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"{t('customer_save_error')} {e}")

        with btn_c2:
            if st.button(t("delete_customer"), use_container_width=True, key="btn_del_cust"):
                st.session_state._confirm_delete_customer = selected_idx

        with btn_c3:
            if st.button(t("close"), use_container_width=True, key="btn_close_cust"):
                st.session_state._cust_selected_idx = None
                st.rerun()

        # Delete confirmation
        if st.session_state.get("_confirm_delete_customer") is not None and st.session_state._confirm_delete_customer == selected_idx:
            st.warning(f"{t('customer_delete_confirm')} **{ec.get('company_name', '')}**")
            dc1, dc2, _ = st.columns(3)
            with dc1:
                if st.button(t("delete_customer"), type="primary", key="btn_confirm_del"):
                    try:
                        delete_rows(MASTER_CATALOG_ID, "Customers", selected_idx + 1, selected_idx + 2)
                        st.session_state._confirm_delete_customer = None
                        st.session_state._cust_selected_idx = None
                        st.success(t("customer_deleted"))
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"{t('customer_save_error')} {e}")
            with dc2:
                if st.button(t("cancel"), key="btn_cancel_del"):
                    st.session_state._confirm_delete_customer = None
                    st.rerun()
    else:
        st.info(t("click_customer_hint"))

    # --- Add new customer (always available in expander) ---
    with st.expander(t("add_new_option")):
        _k = "_new"
        fc1, fc2 = st.columns(2)
        with fc1:
            f_company = st.text_input(t("company_name"), key=f"cust_company{_k}")
            f_eik = st.text_input(t("company_reg_id"), key=f"cust_eik{_k}", placeholder="напр. 123456789")
            f_vat = st.text_input(
                t("vat_number"), key=f"cust_vat{_k}",
                placeholder=f"BG{f_eik}" if f_eik else "напр. BG123456789",
                help=t("vat_auto_hint"),
            )
            f_contact = st.text_input(t("contact_name"), key=f"cust_contact{_k}")
            f_email = st.text_input(t("email_field"), key=f"cust_email{_k}")
        with fc2:
            f_phone = st.text_input(t("phone_field"), key=f"cust_phone{_k}")
            f_address = st.text_input(t("address_field"), key=f"cust_address{_k}")
            f_delivery_addr = st.text_input(t("delivery_address_field"), key=f"cust_del_addr{_k}")
            f_sap = st.text_input(t("sap_number"), key=f"cust_sap{_k}", placeholder="напр. 100234")
            f_discount = st.number_input(t("default_discount_field"), min_value=0.0, max_value=99.0, value=0.0, step=0.5, key=f"cust_disc{_k}")
        f_notes = st.text_input(t("notes"), key=f"cust_notes{_k}")

        if st.button(t("save_customer"), type="primary", use_container_width=True, key="btn_save_new"):
            if not f_company.strip():
                st.error(t("company_name_required"))
            else:
                try:
                    customer_id = f_sap.strip() or f_company.strip()[:20]
                    existing_ids = {c.get("customer_id", "") for c in customers}
                    if customer_id in existing_ids:
                        st.error(t("customer_id_exists"))
                        st.stop()
                    vat_value = f_vat.strip() or (f"BG{f_eik.strip()}" if f_eik.strip() else "")
                    phone = f"'{f_phone.strip()}" if f_phone.strip().startswith("+") else f_phone.strip()
                    new_row = [
                        customer_id, f_company.strip(), f_contact.strip(), f_email.strip(),
                        phone, f_address.strip(), "",  # discount_tier
                        str(f_discount) if f_discount > 0 else "", "",  # payment_terms
                        f_notes.strip(), date.today().strftime("%Y-%m-%d"),
                        vat_value, f_eik.strip(), f_delivery_addr.strip(),
                    ]
                    append_sheet(MASTER_CATALOG_ID, "'Customers'!A:N", [new_row])
                    st.success(t("customer_saved"))
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"{t('customer_save_error')} {e}")

st.markdown("---")

# --- Delivery Terms ---
st.subheader(t("delivery_terms_title"))
del_headers, del_terms = load_tab("Delivery_Terms", "'Delivery_Terms'!A:D")
if del_terms:
    for i, dt in enumerate(del_terms):
        dc1, dc2, dc3, dc4 = st.columns([1, 3, 3, 1])
        with dc1:
            st.text_input("ID", value=dt.get("term_id", ""), disabled=True, key=f"del_id_{i}")
        with dc2:
            st.text_input(t("term_name_bg"), value=dt.get("name_bg", ""), disabled=True, key=f"del_bg_{i}")
        with dc3:
            st.text_input(t("term_name_en"), value=dt.get("name_en", ""), disabled=True, key=f"del_en_{i}")
        with dc4:
            if st.button(t("delete_term"), key=f"del_term_del_{i}"):
                try:
                    delete_rows(MASTER_CATALOG_ID, "Delivery_Terms", i + 1, i + 2)
                    st.success(t("term_deleted"))
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"{t('save_error')} {e}")
else:
    st.info(t("no_delivery_terms"))

with st.expander(t("add_term")):
    nd1, nd2, nd3 = st.columns(3)
    with nd1:
        new_del_bg = st.text_input(t("term_name_bg"), key="new_del_bg")
    with nd2:
        new_del_en = st.text_input(t("term_name_en"), key="new_del_en")
    with nd3:
        new_del_desc = st.text_input(t("term_description"), key="new_del_desc")
    if st.button(t("add_term"), key="btn_add_del_term", type="primary"):
        if new_del_bg.strip():
            try:
                new_id = f"DEL-{len(del_terms) + 1:03d}"
                append_sheet(MASTER_CATALOG_ID, "'Delivery_Terms'!A:D",
                             [[new_id, new_del_bg.strip(), new_del_en.strip(), new_del_desc.strip()]])
                st.success(t("term_added"))
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"{t('save_error')} {e}")

st.markdown("---")

# --- Payment Terms ---
st.subheader(t("payment_terms_title"))
pay_headers, pay_terms = load_tab("Payment_Terms", "'Payment_Terms'!A:D")
if pay_terms:
    for i, pt in enumerate(pay_terms):
        pc1, pc2, pc3, pc4 = st.columns([1, 3, 3, 1])
        with pc1:
            st.text_input("ID", value=pt.get("term_id", ""), disabled=True, key=f"pay_id_{i}")
        with pc2:
            st.text_input(t("term_name_bg"), value=pt.get("name_bg", ""), disabled=True, key=f"pay_bg_{i}")
        with pc3:
            st.text_input(t("term_name_en"), value=pt.get("name_en", ""), disabled=True, key=f"pay_en_{i}")
        with pc4:
            if st.button(t("delete_term"), key=f"pay_term_del_{i}"):
                try:
                    delete_rows(MASTER_CATALOG_ID, "Payment_Terms", i + 1, i + 2)
                    st.success(t("term_deleted"))
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"{t('save_error')} {e}")
else:
    st.info(t("no_payment_terms"))

with st.expander(t("add_term")):
    np1, np2, np3 = st.columns(3)
    with np1:
        new_pay_bg = st.text_input(t("term_name_bg"), key="new_pay_bg")
    with np2:
        new_pay_en = st.text_input(t("term_name_en"), key="new_pay_en")
    with np3:
        new_pay_desc = st.text_input(t("term_description"), key="new_pay_desc")
    if st.button(t("add_term"), key="btn_add_pay_term", type="primary"):
        if new_pay_bg.strip():
            try:
                new_id = f"PAY-{len(pay_terms) + 1:03d}"
                append_sheet(MASTER_CATALOG_ID, "'Payment_Terms'!A:D",
                             [[new_id, new_pay_bg.strip(), new_pay_en.strip(), new_pay_desc.strip()]])
                st.success(t("term_added"))
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"{t('save_error')} {e}")

st.markdown("---")

# --- Company Branding ---
st.subheader(t("branding_title"))
brand_rows = read_sheet(MASTER_CATALOG_ID, "'Company_Branding'!A:C")
if brand_rows and len(brand_rows) >= 2:
    # Editable branding fields (skip counters)
    EDITABLE_KEYS = {
        "company_name", "company_address", "company_phone", "company_email",
        "company_website", "company_vat_id", "company_logo_url",
        "brand_color_primary", "brand_color_secondary",
        "offer_terms", "offer_disclaimer", "offer_footer",
        "sales_agent_sap_code", "cs_email",
        "email_offer_template", "email_order_template",
    }
    TEXTAREA_KEYS = {
        "offer_terms", "offer_disclaimer", "offer_footer",
        "email_offer_template", "email_order_template",
    }
    brand_values = {}
    brand_row_map = {}  # key → sheet row index (1-based)
    for i, row in enumerate(brand_rows[1:], start=2):
        if not row:
            continue
        key = row[0]
        val = row[1] if len(row) > 1 else ""
        brand_values[key] = val
        brand_row_map[key] = i

    edited = {}
    for key, val in brand_values.items():
        if key in EDITABLE_KEYS:
            if key in TEXTAREA_KEYS:
                help_text = None
                if key in ("email_offer_template", "email_order_template"):
                    help_text = t("email_template_help")
                edited[key] = st.text_area(key, value=val, key=f"brand_{key}", help=help_text)
            else:
                edited[key] = st.text_input(key, value=val, key=f"brand_{key}")
        else:
            st.text_input(key, value=val, disabled=True, key=f"brand_{key}")

    if st.button(t("save_changes"), type="primary", key="btn_save_branding"):
        try:
            for key, new_val in edited.items():
                old_val = brand_values.get(key, "")
                if new_val != old_val and key in brand_row_map:
                    row_num = brand_row_map[key]
                    # Prefix phone values with ' to prevent +number formula errors
                    val_to_write = new_val
                    if key == "company_phone" and new_val.strip().startswith("+"):
                        val_to_write = f"'{new_val.strip()}"
                    write_sheet(MASTER_CATALOG_ID, f"'Company_Branding'!B{row_num}", [[val_to_write]])
            st.success(t("branding_saved"))
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"{t('save_error')} {e}")
else:
    st.info(t("no_branding"))

st.markdown("---")

# --- Logistics Import ---
st.subheader(t("logistics_title"))

_, logistics = load_tab("Logistics", "'Logistics'!A:G")
st.write(f"{t('logistics_count')} **{len(logistics)}**")

uploaded = st.file_uploader(t("upload_logistics"), type=["xlsx"])
if uploaded:
    import tempfile
    import os

    # Validate file size (max 50 MB)
    max_size = 50 * 1024 * 1024
    if uploaded.size > max_size:
        st.error(f"File too large ({uploaded.size / 1024 / 1024:.1f} MB). Maximum: 50 MB.")
    else:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        if st.button(t("import_btn"), type="primary"):
            with st.spinner("..."):
                try:
                    from tools.import_logistics import import_logistics
                    import_logistics(tmp_path)
                    st.success(t("import_success"))
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"{t('import_error')} {e}")
                finally:
                    # Clean up temp file
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass

st.markdown("---")

if st.button(t("refresh_all")):
    st.cache_data.clear()
    st.rerun()
