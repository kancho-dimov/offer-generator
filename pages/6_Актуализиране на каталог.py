"""Enrichment page — run the master catalog enrichment pipeline from the UI."""

import streamlit as st

from i18n import setup_page, t

setup_page("Актуализиране на каталог", "🔄")
st.title(t("enrich_title"))

MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"

# ── Section 1: Input SAP codes ──────────────────────────────────────────────
st.subheader(t("enrich_input_codes"))

col_input, col_upload = st.columns([2, 1])

with col_input:
    raw_codes = st.text_area(
        t("enrich_codes_placeholder"),
        height=200,
        key="enrich_codes_input",
    )

with col_upload:
    uploaded = st.file_uploader(
        t("enrich_or_upload"),
        type=["txt", "csv"],
        key="enrich_file_upload",
    )
    if uploaded is not None:
        file_text = uploaded.read().decode("utf-8", errors="replace")
        raw_codes = file_text
        st.info(f"Loaded {uploaded.name}")

# Parse and deduplicate codes
codes = []
if raw_codes:
    for line in raw_codes.strip().splitlines():
        code = line.strip().strip(",").strip(";").strip('"').strip("'")
        if code:
            codes.append(code)
    codes = list(dict.fromkeys(codes))  # deduplicate preserving order

if codes:
    st.caption(t("enrich_codes_count", n=len(codes)))
    with st.expander(f"Codes ({len(codes)})"):
        st.code("\n".join(codes), language=None)

force = st.checkbox(t("enrich_force"), value=False)

# Estimated cost preview
if codes:
    est_cost = len(codes) * 2 * 0.003
    st.caption(t("enrich_est_cost", cost=est_cost))

# ── Section 2: Quick Sync (baseline registration, no API) ───────────────────
st.divider()

st.caption(t("enrich_quick_sync_hint"))
if st.button("⚡ " + t("enrich_quick_sync"), disabled=not codes, use_container_width=True):
    from tools.update_master_catalog import ensure_baseline_entries, load_pricelist_raw
    with st.spinner(t("enrich_step0")):
        qs_result = ensure_baseline_entries(codes, load_pricelist_raw())
    if qs_result["written"]:
        st.success(f"✅ Регистрирани {qs_result['written']} нови продукта")
    if qs_result["already_present"]:
        st.info(f"ℹ️ {qs_result['already_present']} вече са в каталога")
    if qs_result["not_in_pricelist"]:
        st.error(f"❌ Не са намерени в ценовата листа: {', '.join(qs_result['not_in_pricelist'])}")
    from tools.product_search import invalidate_cache
    invalidate_cache()
    st.cache_data.clear()

st.divider()

# ── Section 3: Full enrichment pipeline ─────────────────────────────────────
if st.button(t("enrich_start"), type="primary", disabled=not codes, use_container_width=True):
    if not codes:
        st.warning(t("enrich_no_codes"))
        st.stop()

    st.subheader(t("enrich_progress"))

    step_labels = {
        0: t("enrich_step0"),
        1: t("enrich_step1"),
        2: t("enrich_step2"),
        3: t("enrich_step3"),
        4: t("enrich_step4"),
    }

    progress_bar = st.progress(0)
    status_container = st.status(t("enrich_running"), expanded=True)

    log_lines = []

    def on_step(step: int, label: str):
        progress_bar.progress(step / 4)
        status_container.update(label=f"({step}/4) {step_labels.get(step, label)}")

    def on_log(message: str):
        log_lines.append(message)
        status_container.write(message)

    try:
        from tools.run_enrichment import run_pipeline

        result = run_pipeline(
            codes=codes,
            force=force,
            on_step=on_step,
            on_log=on_log,
        )

        progress_bar.progress(1.0)
        status_container.update(label=t("enrich_done"), state="complete", expanded=False)

        # Invalidate product caches so search page picks up new data
        from tools.product_search import invalidate_cache
        invalidate_cache()
        st.cache_data.clear()

        # ── Section 4: Results summary ───────────────────────────────────────
        st.subheader(t("enrich_results"))

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric(t("enrich_total"), result["total"])
        c2.metric(t("enrich_baseline"), result["baseline_written"])
        c3.metric(t("enrich_mapped"), result["mapped"])
        c4.metric(t("enrich_basic"), result["basic"])
        c5.metric(t("enrich_translated"), result["translated"])

        # Product-level results table
        products = result["products"]
        table_data = []
        for p in products:
            status_icon = {
                "full": "🟢",
                "pricelist_only": "🟡",
                "nomenclature_only": "🟡",
                "none": "🔴",
            }.get(p.get("match_status", "none"), "⚪")

            scrape_icon = {
                "success": "🟢",
                "partial": "🟡",
                "failed": "🔴",
                "no_description": "⚪",
            }.get(p.get("scrape_status", ""), "⚪")

            enrich_icon = {
                "success": "🟢",
                "basic": "🔵",
                "failed": "🔴",
                "skipped": "⚪",
            }.get(p.get("enrich_status", ""), "⚪")

            err = p.get("enrich_error", "")
            translate_cell = f"{enrich_icon} {p.get('enrich_status', '')}"
            if err:
                translate_cell += f" — {err[:80]}"
            table_data.append({
                "Code": p.get("product_code", ""),
                "Name": p.get("name_bg", p.get("short_name_ro", "")),
                "Match": f"{status_icon} {p.get('match_status', '')}",
                "Scrape": f"{scrape_icon} {p.get('scrape_status', '')}",
                "Translate": translate_cell,
            })

        # Add error rows for codes not found in pricelist
        for code in result.get("not_in_pricelist", []):
            table_data.append({
                "Code": code,
                "Name": "— не е в ценовата листа —",
                "Match": "🔴 не е в ценовата листа",
                "Scrape": "⚪",
                "Translate": "⚪ —",
            })

        st.dataframe(table_data, use_container_width=True)

        st.link_button(
            t("enrich_open_catalog"),
            f"https://docs.google.com/spreadsheets/d/{MASTER_CATALOG_ID}",
            type="primary",
        )

    except Exception as e:
        progress_bar.progress(1.0)
        status_container.update(label=t("enrich_error", error=""), state="error", expanded=True)
        st.error(f"{t('enrich_error')} {e}")
