"""
Romstal Offer & Order Generator — Streamlit Frontend.

Run with:
    streamlit run app.py
"""

import streamlit as st

from i18n import BRAND_CSS, lang_selector, t

st.set_page_config(
    page_title="Romstal | Offers & Orders",
    page_icon="resources/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.image("resources/logo.png", width=180)
lang_selector()
st.sidebar.markdown("---")
st.markdown(BRAND_CSS, unsafe_allow_html=True)

st.title(t("home_title"))
st.markdown(t("home_welcome"))
