"""Dashboard page — overview of recent offers/orders + analytics."""

import streamlit as st
import pandas as pd
from collections import Counter

from i18n import setup_page, t
from tools.offer_log import delete_offer, delete_order, get_offer_log
from tools.sheets_api import read_sheet

MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"

setup_page("Основен панел", "📊")
st.title(t("dashboard_title"))


@st.cache_data(ttl=60)
def load_offers():
    return get_offer_log()


@st.cache_data(ttl=60)
def load_orders():
    rows = read_sheet(MASTER_CATALOG_ID, "'Orders'!A:O")
    if not rows or len(rows) < 2:
        return []
    headers = rows[0]
    orders = []
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        row += [""] * (len(headers) - len(row))
        orders.append(dict(zip(headers, row)))
    return orders


offers = load_offers()
orders = load_orders()

# ─── KPI Metrics ───────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(t("offers"), len(offers))
with col2:
    st.metric(t("orders"), len(orders))
with col3:
    active = sum(1 for o in orders if o.get("status") in ("draft", "submitted", "confirmed"))
    st.metric(t("active_orders"), active)
with col4:
    total_rev = sum(float(o.get("total_excl_vat", 0) or 0) for o in offers)
    if total_rev >= 1000:
        st.metric(t("total_revenue"), f"{total_rev:,.0f} EUR")
    else:
        st.metric(t("total_revenue"), f"{total_rev:.2f} EUR")
with col5:
    if offers:
        avg_val = total_rev / len(offers)
        st.metric(t("avg_offer_value"), f"{avg_val:,.0f} EUR")
    else:
        st.metric(t("avg_offer_value"), "—")

st.markdown("---")

# ─── Recent Offers ─────────────────────────────────────────
st.subheader(t("recent_offers"))
if offers:
    recent_offers = list(reversed(offers[-10:]))
    for o in recent_offers:
        status_emoji = {"draft": "📝", "sent": "📨", "accepted": "✅",
                        "expired": "⏰", "converted_to_order": "📦"}.get(o.get("status", ""), "❓")
        ofr_num = o.get("offer_number", "")
        col_a, col_b, col_c, col_d, col_e = st.columns([2, 3, 2, 1.5, 0.5])
        with col_a:
            st.write(f"{status_emoji} **{ofr_num}**")
        with col_b:
            st.write(o.get("customer_name", ""))
        with col_c:
            st.write(o.get("created_date", ""))
        with col_d:
            url = o.get("spreadsheet_url", "")
            if url:
                st.link_button(t("open"), url, use_container_width=True)
        with col_e:
            if st.button("🗑️", key=f"del_ofr_{ofr_num}", help=t("delete")):
                delete_offer(ofr_num)
                st.cache_data.clear()
                st.rerun()
else:
    st.info(t("no_offers_yet"))

st.markdown("---")

# ─── Recent Orders ─────────────────────────────────────────
st.subheader(t("recent_orders"))
if orders:
    recent_orders = list(reversed(orders[-10:]))
    for o in recent_orders:
        status_emoji = {"draft": "📝", "submitted": "📨", "confirmed": "✅",
                        "shipped": "🚚", "completed": "✔️"}.get(o.get("status", ""), "❓")
        ord_num = o.get("order_number", "")
        col_a, col_b, col_c, col_d, col_e, col_f = st.columns([2, 3, 2, 1, 1, 0.5])
        with col_a:
            st.write(f"{status_emoji} **{ord_num}**")
        with col_b:
            st.write(o.get("customer_name", ""))
        with col_c:
            st.write(o.get("created_date", ""))
        with col_d:
            url = o.get("spreadsheet_url", "")
            if url:
                st.link_button(t("open"), url, use_container_width=True)
        with col_e:
            if st.button(t("edit"), key=f"edit_ord_{ord_num}"):
                st.session_state.edit_order = {
                    "order_number": ord_num,
                    "customer_id": o.get("customer_id", ""),
                    "delivery_terms": o.get("delivery_terms", ""),
                    "payment_terms": o.get("payment_terms", ""),
                    "delivery_date": o.get("delivery_date", ""),
                    "notes": o.get("notes", ""),
                    "sales_agent_code": o.get("sales_agent_code", ""),
                    "spreadsheet_url": url,
                }
                st.switch_page("pages/3_Нова_Поръчка.py")
        with col_f:
            if st.button("🗑️", key=f"del_ord_{ord_num}", help=t("delete")):
                delete_order(ord_num)
                st.cache_data.clear()
                st.rerun()
else:
    st.info(t("no_orders_yet"))

st.markdown("---")

# ─── Analytics Section ─────────────────────────────────────
st.subheader(t("analytics"))

if offers:
    # --- Revenue by Customer (bar chart) ---
    cust_revenue = {}
    for o in offers:
        name = o.get("customer_name", "N/A")
        val = float(o.get("total_excl_vat", 0) or 0)
        cust_revenue[name] = cust_revenue.get(name, 0) + val

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown(f"**{t('revenue_by_customer')}**")
        df_cust = pd.DataFrame(
            sorted(cust_revenue.items(), key=lambda x: x[1], reverse=True),
            columns=[t("customer"), t("revenue_excl_vat")],
        )
        st.bar_chart(df_cust, x=t("customer"), y=t("revenue_excl_vat"), color="#0086CE")

    # --- Offers by Month (bar chart) ---
    with chart_col2:
        st.markdown(f"**{t('offers_by_month')}**")
        month_counts = Counter()
        for o in offers:
            d = o.get("created_date", "")
            if d and len(d) >= 7:
                month_counts[d[:7]] += 1
        if month_counts:
            months_sorted = sorted(month_counts.items())
            df_months = pd.DataFrame(months_sorted, columns=[t("month"), t("count")])
            st.bar_chart(df_months, x=t("month"), y=t("count"), color="#0086CE")

    # --- Status Breakdown + Mode Breakdown ---
    stat_col1, stat_col2 = st.columns(2)

    with stat_col1:
        st.markdown(f"**{t('offer_status_breakdown')}**")
        status_labels = {
            "draft": "📝 Draft",
            "sent": "📨 Sent",
            "accepted": "✅ Accepted",
            "expired": "⏰ Expired",
            "converted_to_order": "📦 → Order",
        }
        status_counts = Counter(status_labels.get(o.get("status", ""), o.get("status", "?")) for o in offers)
        df_status = pd.DataFrame(
            sorted(status_counts.items(), key=lambda x: x[1], reverse=True),
            columns=[t("status"), t("count")],
        )
        st.dataframe(df_status, use_container_width=True, hide_index=True)

    with stat_col2:
        st.markdown(f"**{t('offers_vs_pricelists')}**")
        mode_labels = {"offer": t("offer_label"), "pricelist": t("pricelist_label")}
        mode_counts = Counter(mode_labels.get(o.get("mode", ""), o.get("mode", "")) for o in offers)
        df_mode = pd.DataFrame(
            sorted(mode_counts.items(), key=lambda x: x[1], reverse=True),
            columns=[t("type"), t("count")],
        )
        st.dataframe(df_mode, use_container_width=True, hide_index=True)

    # --- Top Customers table ---
    st.markdown(f"**{t('top_customers')}**")
    cust_stats = {}
    for o in offers:
        name = o.get("customer_name", "N/A")
        val = float(o.get("total_excl_vat", 0) or 0)
        if name not in cust_stats:
            cust_stats[name] = {"count": 0, "revenue": 0.0}
        cust_stats[name]["count"] += 1
        cust_stats[name]["revenue"] += val

    top_rows = []
    for name, stats in sorted(cust_stats.items(), key=lambda x: x[1]["revenue"], reverse=True):
        top_rows.append({
            t("customer"): name,
            t("count"): stats["count"],
            t("revenue_excl_vat"): f"{stats['revenue']:,.2f} EUR",
        })
    st.dataframe(top_rows, use_container_width=True, hide_index=True)

    # --- Conversion Rate ---
    converted = sum(1 for o in offers if o.get("order_number") and o.get("mode") == "offer")
    total_offers_only = sum(1 for o in offers if o.get("mode") == "offer")
    if total_offers_only > 0:
        rate = min((converted / total_offers_only) * 100, 100)
        st.metric(t("conversion_rate"), f"{rate:.0f}%",
                  help=f"{converted}/{total_offers_only} offers → orders")

else:
    st.info(t("no_offers_yet"))

st.markdown("---")

if st.button(t("refresh")):
    st.cache_data.clear()
    st.rerun()
