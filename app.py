"""
Romstal Offer & Order Generator — Streamlit Frontend.

Run with:
    streamlit run app.py
"""

import os
import streamlit as st

from i18n import BRAND_CSS, render_navbar, t

st.set_page_config(
    page_title="Romstal | Offers & Orders",
    page_icon="resources/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Authentication gate (requires .streamlit/secrets.toml with [auth.google])
# Skipped when DISABLE_AUTH=1 (local dev without OAuth Web client)
# ---------------------------------------------------------------------------
_auth_enabled = (
    os.environ.get("DISABLE_AUTH", "0") != "1"
    and hasattr(st, "login")
    and st.secrets.get("auth", {}).get("google", None) is not None
)

if _auth_enabled:
    # Allowed emails — loaded from env var (comma-separated) or secrets
    _allowed_raw = os.environ.get(
        "ALLOWED_EMAILS",
        st.secrets.get("auth", {}).get("allowed_emails", ""),
    )
    ALLOWED_EMAILS = [e.strip().lower() for e in _allowed_raw.split(",") if e.strip()]

    if not st.user.is_logged_in:
        st.image("resources/logo.png", width=200)
        st.title("Romstal Offer & Order Generator")
        st.write("Please log in to continue.")
        if st.button("Log in with Google"):
            st.login("google")
        st.stop()

    user_email = (st.user.email or "").lower()
    if ALLOWED_EMAILS and user_email not in ALLOWED_EMAILS:
        st.error(f"Access denied for {st.user.email}")
        st.write("Contact your administrator to request access.")
        if st.button("Log out"):
            st.logout()
        st.stop()

# ---------------------------------------------------------------------------
# Main app (authenticated or auth disabled)
# ---------------------------------------------------------------------------
st.markdown(BRAND_CSS, unsafe_allow_html=True)
render_navbar(current_page="")

# Show logged-in user + logout button when auth is active
if _auth_enabled and st.user.is_logged_in:
    st.markdown(
        f"<p style='font-size:0.8rem;color:#64748B;margin-bottom:0'>"
        f"Влезли сте като {st.user.name or st.user.email}</p>",
        unsafe_allow_html=True,
    )
    if st.button("Излез", key="home_logout"):
        st.logout()

st.title(t("home_title"))
st.markdown(t("home_welcome"))
