"""Product Search page — search and browse the product catalog."""

import streamlit as st

from i18n import setup_page, t
from tools.product_search import load_all_products, search_products

setup_page("Търсене на продукти", "🔍")
st.title(t("search_title"))


@st.cache_data(ttl=300)
def get_filter_options():
    """Extract unique categories and brands from the product catalog."""
    products = load_all_products()
    categories = sorted({p.get("category", "") for p in products if p.get("category", "").strip()})
    brands = sorted({p.get("brand", "") for p in products if p.get("brand", "").strip()})
    return categories, brands


categories, brands = get_filter_options()

query = st.text_input(
    t("search_by"),
    placeholder=t("search_placeholder"),
)

col_cat, col_brand = st.columns(2)
with col_cat:
    selected_category = st.selectbox(t("category"), [t("all")] + categories)
with col_brand:
    selected_brand = st.selectbox(t("brand"), [t("all")] + brands)

if query or selected_category != t("all") or selected_brand != t("all"):
    with st.spinner("..."):
        results = search_products(query or "", limit=200)

        # Apply filters
        if selected_category != t("all"):
            results = [p for p in results if p.get("category", "") == selected_category]
        if selected_brand != t("all"):
            results = [p for p in results if p.get("brand", "") == selected_brand]

    st.write(f"**{len(results)}** {t('results_count')}")

    if results:
        for p in results[:50]:
            code = p.get("product_code", "")
            sup_code = p.get("supplier_code", "")
            name = p.get("name", "")
            brand = p.get("brand", "")
            category = p.get("category", "")
            subcategory = p.get("subcategory", "")
            price = p.get("base_price", "")
            currency = p.get("currency", "EUR")
            image_url = p.get("image_url", "")
            code_label = f"**{code}** ({sup_code})" if sup_code else f"**{code}**"

            with st.container():
                cols = st.columns([1, 4, 2])
                with cols[0]:
                    if image_url:
                        st.image(image_url, width=80)
                    else:
                        st.write("📷")
                with cols[1]:
                    st.write(f"{code_label} — {name}")
                    st.caption(f"{brand} | {category} — {subcategory}")
                with cols[2]:
                    st.write(f"**{price} {currency}**")

                # Expandable product details
                short_desc = p.get("short_description", "").strip()
                long_desc = p.get("long_description", "").strip()
                specs = p.get("specifications", "").strip()
                features = p.get("features", "").strip()

                if short_desc or long_desc or specs or features:
                    with st.expander(t("details")):
                        if short_desc:
                            st.write(f"**{t('short_desc')}** {short_desc}")
                        if long_desc:
                            st.write(f"**{t('long_desc')}** {long_desc}")
                        if features:
                            st.write(f"**{t('features')}**")
                            st.write(features)
                        if specs:
                            st.write(f"**{t('specs')}**")
                            st.write(specs)

                st.divider()

        if len(results) > 50:
            st.info(t("showing_first_50", n=len(results)))
    else:
        st.info(t("no_products_found"))
else:
    st.info(t("enter_search"))
