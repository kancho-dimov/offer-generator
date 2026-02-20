"""Internationalization — bilingual BG/EN support for the Streamlit app."""

import streamlit as st

TRANSLATIONS = {
    # --- Common ---
    "lang_label": {"bg": "BG", "en": "EN"},
    "open": {"bg": "Отвори", "en": "Open"},
    "open_sheets": {"bg": "Отвори в Google Sheets", "en": "Open in Google Sheets"},
    "send_to_customer": {"bg": "Изпрати на клиента", "en": "Send to customer"},
    "send_to_cs": {"bg": "Изпрати до търг. отдел", "en": "Send to sales dept."},
    "sent_to_cs": {"bg": "Изпратено до търг. отдел!", "en": "Sent to sales dept.!"},
    "sent_to": {"bg": "Изпратено на", "en": "Sent to"},
    "error": {"bg": "Грешка", "en": "Error"},
    "send_error": {"bg": "Грешка при изпращане", "en": "Send error"},
    "result": {"bg": "Резултат", "en": "Result"},
    "notes": {"bg": "Бележки", "en": "Notes"},
    "notes_placeholder": {"bg": "Проект, допълнителна информация...", "en": "Project, additional info..."},
    "customer": {"bg": "Клиент", "en": "Customer"},
    "select_customer_placeholder": {"bg": "Изберете клиент...", "en": "Select customer..."},
    "customer_settings_link": {"bg": "Настройки", "en": "Settings"},
    "search": {"bg": "Търсене (код, име, марка)", "en": "Search (code, name, brand)"},
    "no_results": {"bg": "Няма резултати", "en": "No results"},
    "selected_products": {"bg": "Избрани продукти:", "en": "Selected products:"},
    "search_add_products": {"bg": "Търсете и добавете продукти", "en": "Search and add products"},
    "select_customer_add_product": {"bg": "Изберете клиент и добавете поне един продукт", "en": "Select a customer and add at least one product"},
    "qty": {"bg": "К-во", "en": "Qty"},
    "refresh": {"bg": "Обнови данните", "en": "Refresh data"},

    # --- Home ---
    "home_title": {"bg": "Romstal | Оферти и Поръчки", "en": "Romstal | Offers and Orders"},
    "home_welcome": {
        "bg": """Добре дошли в системата за генериране на оферти и поръчки.

Използвайте менюто вляво за навигация:
- **Основен панел** — преглед на последни оферти и поръчки
- **Нова Оферта** — създаване на оферта или ценова листа
- **Нова Поръчка** — създаване на поръчка
- **Търсене** — търсене на продукти
- **Настройки** — управление на клиенти, условия и брандинг
- **Актуализиране на каталог** — актуализиране на Master Catalog с данни от romstal.ro""",
        "en": """Welcome to the offer and order generation system.

Use the menu on the left to navigate:
- **Dashboard** — overview of recent offers and orders
- **New Offer** — create an offer or pricelist
- **New Order** — create an order
- **Search** — search products
- **Settings** — manage customers, terms and branding
- **Catalog Update** — update Master Catalog with data from romstal.ro""",
    },

    # --- Dashboard ---
    "dashboard_title": {"bg": "Основен панел", "en": "Dashboard"},
    "offers": {"bg": "Оферти", "en": "Offers"},
    "orders": {"bg": "Поръчки", "en": "Orders"},
    "active_orders": {"bg": "Активни поръчки", "en": "Active orders"},
    "recent_offers": {"bg": "Последни оферти", "en": "Recent offers"},
    "recent_orders": {"bg": "Последни поръчки", "en": "Recent orders"},
    "no_offers_yet": {"bg": "Няма оферти все още.", "en": "No offers yet."},
    "no_orders_yet": {"bg": "Няма поръчки все още.", "en": "No orders yet."},

    # --- New Offer ---
    "new_offer_title": {"bg": "Нова Оферта", "en": "New Offer"},
    "step1_customer": {"bg": "1. Изберете клиент", "en": "1. Select customer"},
    "step2_products": {"bg": "2. Добавете продукти", "en": "2. Add products"},
    "step3_settings": {"bg": "3. Настройки", "en": "3. Settings"},
    "step4_generate": {"bg": "4. Генериране", "en": "4. Generate"},
    "type": {"bg": "Тип", "en": "Type"},
    "offer_label": {"bg": "Оферта", "en": "Offer"},
    "pricelist_label": {"bg": "Ценова листа", "en": "Pricelist"},
    "show_discounts": {"bg": "Покажи отстъпки", "en": "Show discounts"},
    "show_vat": {"bg": "Покажи ДДС", "en": "Show VAT"},
    "validity_days": {"bg": "Валидност (дни)", "en": "Validity (days)"},
    "discount_level": {"bg": "Ниво отстъпки", "en": "Discount level"},
    "per_product": {"bg": "По продукт", "en": "Per product"},
    "per_brand": {"bg": "По марка", "en": "Per brand"},
    "per_category": {"bg": "По категория", "en": "Per category"},
    "extra_discount": {"bg": "Допълнителна отстъпка %", "en": "Additional discount %"},
    "generate_offer": {"bg": "Генерирай", "en": "Generate"},
    "generating": {"bg": "Генериране...", "en": "Generating..."},
    "offer_ready": {"bg": "Офертата е готова!", "en": "Offer is ready!"},
    "search_add_left": {"bg": "Търсете и добавете продукти от лявата колона", "en": "Search and add products from the left column"},

    # --- New Order ---
    "new_order_title": {"bg": "Нова Поръчка", "en": "New Order"},
    "mode": {"bg": "Режим", "en": "Mode"},
    "mode_question": {"bg": "Как искате да създадете поръчката?", "en": "How do you want to create the order?"},
    "from_offer": {"bg": "От съществуваща оферта", "en": "From existing offer"},
    "standalone": {"bg": "Нова поръчка (без оферта)", "en": "New order (without offer)"},
    "select_offer": {"bg": "Изберете оферта", "en": "Select offer"},
    "no_offers_to_convert": {"bg": "Няма налични оферти за конвертиране.", "en": "No offers available for conversion."},
    "offer_data_missing": {"bg": "Файлът с данни от офертата не е наличен. Добавете продукти ръчно.", "en": "Offer data file not available. Add products manually."},
    "products": {"bg": "2. Продукти", "en": "2. Products"},
    "measure": {"bg": "МЕ", "en": "Unit"},
    "pcs_label": {"bg": "бр.", "en": "pcs"},
    "carton_label": {"bg": "кш.", "en": "ctn"},
    "pallet_label": {"bg": "пал.", "en": "plt"},
    "terms": {"bg": "3. Условия", "en": "3. Terms"},
    "delivery_terms": {"bg": "Условия на доставка", "en": "Delivery terms"},
    "delivery_date": {"bg": "Дата на доставка", "en": "Delivery date"},
    "payment_terms": {"bg": "Условия на плащане", "en": "Payment terms"},
    "sales_agent": {"bg": "SAP код на търговски агент", "en": "Sales agent SAP code"},
    "generate_order": {"bg": "Генерирай", "en": "Generate"},
    "generating_order": {"bg": "Генериране на поръчка...", "en": "Generating order..."},
    "order_ready": {"bg": "Поръчката е готова!", "en": "Order is ready!"},

    # --- Search ---
    "search_title": {"bg": "Търсене на продукти", "en": "Product Search"},
    "search_placeholder": {"bg": "напр. радиатор, KERMI, 34KR6610...", "en": "e.g. radiator, KERMI, 34KR6610..."},
    "search_by": {"bg": "Търсете по код, име, марка или категория", "en": "Search by code, name, brand or category"},
    "category": {"bg": "Категория", "en": "Category"},
    "brand": {"bg": "Марка", "en": "Brand"},
    "all": {"bg": "Всички", "en": "All"},
    "results_count": {"bg": "резултата", "en": "results"},
    "details": {"bg": "Детайли", "en": "Details"},
    "short_desc": {"bg": "Кратко описание:", "en": "Short description:"},
    "long_desc": {"bg": "Пълно описание:", "en": "Full description:"},
    "features": {"bg": "Характеристики:", "en": "Features:"},
    "specs": {"bg": "Спецификации:", "en": "Specifications:"},
    "no_products_found": {"bg": "Няма намерени продукти.", "en": "No products found."},
    "enter_search": {"bg": "Въведете текст или изберете категория/марка за търсене.", "en": "Enter text or select category/brand to search."},
    "showing_first_50": {"bg": "Показани са първите 50 от {n} резултата. Стеснете търсенето.", "en": "Showing first 50 of {n} results. Narrow your search."},

    # --- Settings ---
    "settings_title": {"bg": "Настройки", "en": "Settings"},
    "customers": {"bg": "Клиенти", "en": "Customers"},
    "customers_count": {"bg": "клиента", "en": "customers"},
    "no_customers": {"bg": "Няма клиенти.", "en": "No customers."},
    "delivery_terms_title": {"bg": "Условия на доставка", "en": "Delivery Terms"},
    "no_delivery_terms": {"bg": "Няма условия на доставка.", "en": "No delivery terms."},
    "payment_terms_title": {"bg": "Условия на плащане", "en": "Payment Terms"},
    "no_payment_terms": {"bg": "Няма условия на плащане.", "en": "No payment terms."},
    "branding_title": {"bg": "Фирмен профил (Branding)", "en": "Company Branding"},
    "no_branding": {"bg": "Няма настройки за брандинг.", "en": "No branding settings."},
    "logistics_title": {"bg": "Логистика (импорт от Excel)", "en": "Logistics (Excel import)"},
    "logistics_count": {"bg": "Заредени продукти в Logistics:", "en": "Products loaded in Logistics:"},
    "upload_logistics": {"bg": "Качете нов логистичен файл (.xlsx)", "en": "Upload new logistics file (.xlsx)"},
    "import_btn": {"bg": "Импортирай", "en": "Import"},
    "import_success": {"bg": "Логистичните данни са импортирани успешно!", "en": "Logistics data imported successfully!"},
    "import_error": {"bg": "Грешка при импорт:", "en": "Import error:"},
    "refresh_all": {"bg": "Обнови всички данни", "en": "Refresh all data"},
    "add_customer": {"bg": "Добави нов клиент", "en": "Add new customer"},
    "company_name": {"bg": "Фирма", "en": "Company name"},
    "company_reg_id": {"bg": "ЕИК", "en": "Company Reg. ID (UCN)"},
    "vat_number": {"bg": "ДДС №", "en": "VAT Number"},
    "vat_auto_hint": {"bg": "Обикновено BG + ЕИК", "en": "Usually BG + UCN"},
    "contact_name": {"bg": "Лице за контакт", "en": "Contact person"},
    "email_field": {"bg": "Email", "en": "Email"},
    "phone_field": {"bg": "Телефон", "en": "Phone"},
    "address_field": {"bg": "Адрес", "en": "Address"},
    "sap_number": {"bg": "SAP клиентски номер", "en": "SAP customer number"},
    "discount_tier_field": {"bg": "Ниво отстъпка", "en": "Discount tier"},
    "default_discount_field": {"bg": "Отстъпка по подразбиране %", "en": "Default discount %"},
    "save_customer": {"bg": "Запази клиент", "en": "Save customer"},
    "customer_saved": {"bg": "Клиентът е записан!", "en": "Customer saved!"},
    "customer_save_error": {"bg": "Грешка при запис:", "en": "Save error:"},
    "company_name_required": {"bg": "Фирмата е задължителна", "en": "Company name is required"},

    # --- Additional (Phase 4) ---
    "download_pdf": {"bg": "Изтегли PDF", "en": "Download PDF"},
    "preview_pdf": {"bg": "Преглед PDF", "en": "Preview PDF"},
    "close_pdf": {"bg": "Затвори PDF", "en": "Close PDF"},
    "delivery_address": {"bg": "Адрес на доставка", "en": "Delivery address"},
    "custom_address": {"bg": "Друг адрес (въведете)", "en": "Other address (type)"},
    "custom_address_input": {"bg": "Въведете адрес", "en": "Enter address"},
    "filter_category": {"bg": "Категория", "en": "Category"},
    "filter_brand": {"bg": "Марка", "en": "Brand"},
    "filter_all": {"bg": "Всички", "en": "All"},
    "discount_pct": {"bg": "Отст. %", "en": "Disc. %"},
    "discount_auto": {"bg": "авто", "en": "auto"},
    "delivery_address_field": {"bg": "Адрес на доставка", "en": "Delivery address"},
    "edit_customer": {"bg": "Редактирай клиент", "en": "Edit customer"},
    "delete_customer": {"bg": "Изтрий клиент", "en": "Delete customer"},
    "update_customer": {"bg": "Обнови клиент", "en": "Update customer"},
    "customer_updated": {"bg": "Клиентът е обновен!", "en": "Customer updated!"},
    "customer_deleted": {"bg": "Клиентът е изтрит!", "en": "Customer deleted!"},
    "customer_delete_confirm": {"bg": "Сигурни ли сте, че искате да изтриете този клиент?", "en": "Are you sure you want to delete this customer?"},
    "customer_id_exists": {"bg": "Клиент с този номер вече съществува!", "en": "A customer with this number already exists!"},
    "add_new_option": {"bg": "➕ Добави нов клиент", "en": "➕ Add new customer"},

    # --- Reset buttons ---
    "new_offer_reset": {"bg": "Нова оферта", "en": "New offer"},
    "new_order_reset": {"bg": "Нова поръчка", "en": "New order"},

    # --- Dashboard delete ---
    "delete": {"bg": "Изтрий", "en": "Delete"},
    "confirm_delete_offer": {"bg": "Изтрий офертата {num}?", "en": "Delete offer {num}?"},
    "confirm_delete_order": {"bg": "Изтрий поръчката {num}?", "en": "Delete order {num}?"},
    "offer_deleted": {"bg": "Офертата е изтрита!", "en": "Offer deleted!"},
    "order_deleted": {"bg": "Поръчката е изтрита!", "en": "Order deleted!"},

    # --- Email preview ---
    "email_preview": {"bg": "Преглед на имейл", "en": "Email Preview"},
    "email_to": {"bg": "До", "en": "To"},
    "email_subject": {"bg": "Тема", "en": "Subject"},
    "email_body": {"bg": "Текст на имейла", "en": "Email body"},
    "available_vars": {
        "bg": "Налични променливи: {vars}",
        "en": "Available variables: {vars}",
    },
    "approve_send": {"bg": "Одобри и изпрати", "en": "Approve & Send"},
    "cancel": {"bg": "Отказ", "en": "Cancel"},
    "close": {"bg": "Затвори", "en": "Close"},
    "click_customer_hint": {"bg": "Кликнете на ред в таблицата, за да видите и редактирате клиент", "en": "Click a row in the table to view and edit a customer"},
    "preparing_preview": {"bg": "Подготовка на имейл...", "en": "Preparing email..."},
    "sending_email": {"bg": "Изпращане...", "en": "Sending..."},

    # --- Analytics ---
    "analytics": {"bg": "Анализи", "en": "Analytics"},
    "total_revenue": {"bg": "Общ оборот", "en": "Total Revenue"},
    "avg_offer_value": {"bg": "Средна стойност", "en": "Avg. Offer Value"},
    "conversion_rate": {"bg": "Конверсия", "en": "Conversion Rate"},
    "revenue_by_customer": {"bg": "Оборот по клиент", "en": "Revenue by Customer"},
    "offers_by_month": {"bg": "Оферти по месец", "en": "Offers by Month"},
    "orders_by_month": {"bg": "Поръчки по месец", "en": "Orders by Month"},
    "offer_status_breakdown": {"bg": "Статус на офертите", "en": "Offer Status Breakdown"},
    "offers_vs_pricelists": {"bg": "Оферти vs Ценови листи", "en": "Offers vs Pricelists"},
    "top_customers": {"bg": "Топ клиенти", "en": "Top Customers"},
    "revenue_excl_vat": {"bg": "Оборот (без ДДС)", "en": "Revenue (excl. VAT)"},
    "count": {"bg": "Брой", "en": "Count"},
    "month": {"bg": "Месец", "en": "Month"},
    "status": {"bg": "Статус", "en": "Status"},
    "total": {"bg": "Общо", "en": "Total"},

    # --- Enrichment ---
    "enrich_title": {"bg": "Актуализиране на каталог", "en": "Catalog Update"},
    "enrich_input_codes": {"bg": "1. Въведете SAP кодове", "en": "1. Enter SAP codes"},
    "enrich_codes_placeholder": {"bg": "Поставете SAP кодове (по един на ред)...", "en": "Paste SAP codes (one per line)..."},
    "enrich_or_upload": {"bg": "или качете файл (.txt / .csv)", "en": "or upload a file (.txt / .csv)"},
    "enrich_codes_count": {"bg": "{n} уникални кода", "en": "{n} unique codes"},
    "enrich_force": {"bg": "Принудително обновяване (презапис на вече готови)", "en": "Force update (overwrite catalog_ready products)"},
    "enrich_start": {"bg": "Старт на обогатяване", "en": "Start Enrichment"},
    "enrich_progress": {"bg": "2. Прогрес", "en": "2. Progress"},
    "enrich_step1": {"bg": "Свързване с ценовата листа", "en": "Mapping to pricelist"},
    "enrich_step2": {"bg": "Извличане от romstal.ro", "en": "Scraping romstal.ro"},
    "enrich_step3": {"bg": "Превод на български", "en": "Translating to Bulgarian"},
    "enrich_step4": {"bg": "Запис в Master Catalog", "en": "Writing to Master Catalog"},
    "enrich_results": {"bg": "3. Резултати", "en": "3. Results"},
    "enrich_done": {"bg": "Обогатяването завърши!", "en": "Enrichment complete!"},
    "enrich_total": {"bg": "Общо продукти", "en": "Total products"},
    "enrich_mapped": {"bg": "Намерени съвпадения", "en": "Matched"},
    "enrich_scraped": {"bg": "Извлечени от сайта", "en": "Scraped"},
    "enrich_translated": {"bg": "Преведени", "en": "Translated"},
    "enrich_open_catalog": {"bg": "Отвори Master Catalog", "en": "Open Master Catalog"},
    "enrich_running": {"bg": "Обогатяване...", "en": "Enriching..."},
    "enrich_no_codes": {"bg": "Въведете поне един SAP код", "en": "Enter at least one SAP code"},
    "enrich_error": {"bg": "Грешка при обогатяване:", "en": "Enrichment error:"},
    "enrich_est_cost": {"bg": "Прибл. цена за Claude API: ${cost:.2f}", "en": "Est. Claude API cost: ${cost:.2f}"},

    # --- Editable settings ---
    "save_changes": {"bg": "Запази промените", "en": "Save changes"},
    "changes_saved": {"bg": "Промените са запазени!", "en": "Changes saved!"},
    "save_error": {"bg": "Грешка при запис:", "en": "Save error:"},
    "add_term": {"bg": "Добави условие", "en": "Add term"},
    "delete_term": {"bg": "Изтрий", "en": "Delete"},
    "term_name_bg": {"bg": "Име (BG)", "en": "Name (BG)"},
    "term_name_en": {"bg": "Име (EN)", "en": "Name (EN)"},
    "term_description": {"bg": "Описание", "en": "Description"},
    "term_added": {"bg": "Условието е добавено!", "en": "Term added!"},
    "term_deleted": {"bg": "Условието е изтрито!", "en": "Term deleted!"},
    "branding_saved": {"bg": "Профилът е обновен!", "en": "Branding updated!"},
    "email_template_help": {
        "bg": "Налични променливи: {contact_name}, {customer_company}, {document_type}, {document_number}, {delivery_date}, {our_company}, {our_phone}, {our_email}, {signature}. Оставете празно за шаблон по подразбиране.",
        "en": "Available variables: {contact_name}, {customer_company}, {document_type}, {document_number}, {delivery_date}, {our_company}, {our_phone}, {our_email}, {signature}. Leave empty for default template.",
    },
}


def get_lang() -> str:
    """Get current language from session state."""
    if "lang" not in st.session_state:
        st.session_state.lang = "bg"
    return st.session_state.lang


def t(key: str, **kwargs) -> str:
    """Translate a key to the current language."""
    lang = get_lang()
    text = TRANSLATIONS.get(key, {}).get(lang, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


def lang_selector():
    """Render a language toggle in the sidebar."""
    lang = get_lang()
    new_lang = st.sidebar.toggle("EN", value=(lang == "en"), key="lang_toggle")
    target = "en" if new_lang else "bg"
    if target != lang:
        st.session_state.lang = target
        st.rerun()


BRAND_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Outfit:wght@300;400;500;600;700&display=swap');

    :root {
        --primary-dark: #0F1419;
        --secondary-dark: #1a1f2e;
        --accent-gold: #c9a961;
        --accent-warm: #d4af37;
        --text-primary: #f5f5f5;
        --text-secondary: #b8b8b8;
        --border-subtle: #2a2f3a;
        --success: #6fce9e;
        --error: #ff5757;
    }

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    html, body, .stApp {
        font-family: 'Outfit', 'Segoe UI', sans-serif !important;
        background-color: var(--primary-dark);
        color: var(--text-primary);
        letter-spacing: 0.3px;
    }

    /* === HEADINGS === */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'DM Serif Display', serif !important;
        color: var(--text-primary);
        font-weight: 400;
        letter-spacing: -0.5px;
        margin-bottom: 1rem;
    }

    h1 {
        font-size: 3rem;
        font-weight: 400;
        letter-spacing: -1.5px;
        background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-gold) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1.5rem;
    }

    h2 {
        font-size: 1.75rem;
        letter-spacing: -0.8px;
        border-bottom: 2px solid var(--accent-gold);
        padding-bottom: 0.75rem;
        margin-bottom: 1.5rem;
    }

    h3 {
        font-size: 1.35rem;
        color: var(--accent-gold);
        text-transform: uppercase;
        font-size: 0.95rem;
        letter-spacing: 2px;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600;
    }

    /* === SIDEBAR === */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f2e 0%, #0F1419 100%);
        border-right: 1px solid var(--border-subtle);
    }

    section[data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }

    section[data-testid="stSidebar"] svg {
        fill: var(--text-primary) !important;
    }

    .sidebar-content {
        padding: 1.5rem 0;
    }

    /* === BUTTONS === */
    .stButton > button {
        background: linear-gradient(135deg, #4a7c7e 0%, #2f5254 100%) !important;
        color: #f5f5f5 !important;
        border: none !important;
        border-left: 4px solid #7cafb1 !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.5px !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 4px !important;
        transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
        box-shadow: 0 4px 15px rgba(74, 124, 126, 0.2) !important;
        text-transform: none !important;
        cursor: pointer !important;
        text-shadow: none !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(74, 124, 126, 0.3) !important;
        background: linear-gradient(135deg, #5a8c8e 0%, #3f6264 100%) !important;
        color: #f5f5f5 !important;
        border-left-color: #a5d4d7 !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
        box-shadow: 0 2px 10px rgba(74, 124, 126, 0.2) !important;
    }

    /* === INPUT FIELDS === */
    input, textarea, [data-baseweb="input"], [data-baseweb="textarea"] {
        background-color: var(--secondary-dark) !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--text-primary) !important;
        font-family: 'Outfit', sans-serif !important;
        border-radius: 4px !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.2s ease !important;
    }

    input:focus, textarea:focus, [data-baseweb="input"]:focus, [data-baseweb="textarea"]:focus {
        border-color: var(--accent-gold) !important;
        box-shadow: 0 0 0 3px rgba(201, 169, 97, 0.1) !important;
        outline: none !important;
    }

    input::placeholder, textarea::placeholder {
        color: var(--text-secondary) !important;
    }

    /* === SELECT / DROPDOWN === */
    div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"] > input,
    [role="combobox"] {
        background-color: var(--secondary-dark) !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--text-primary) !important;
        border-radius: 4px !important;
        transition: all 0.2s ease !important;
    }

    div[data-baseweb="select"] > div:hover,
    div[data-baseweb="base-input"] > input:hover,
    [role="combobox"]:hover {
        border-color: var(--accent-gold) !important;
    }

    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="base-input"] > input:focus-within {
        border-color: var(--accent-gold) !important;
        box-shadow: 0 0 0 3px rgba(201, 169, 97, 0.1) !important;
    }

    /* === SELECTBOX DROPDOWN MENU === */
    [data-baseweb="popover"] {
        background-color: var(--secondary-dark) !important;
        border: 1px solid var(--border-subtle) !important;
    }

    [data-baseweb="menu"] {
        background-color: var(--secondary-dark) !important;
    }

    [data-baseweb="menu"] [role="option"] {
        color: var(--text-secondary) !important;
        transition: all 0.15s ease !important;
    }

    [data-baseweb="menu"] [role="option"]:hover {
        background-color: rgba(201, 169, 97, 0.1) !important;
        color: var(--accent-gold) !important;
    }

    [data-baseweb="menu"] [aria-selected="true"] {
        background-color: rgba(201, 169, 97, 0.15) !important;
        color: var(--accent-gold) !important;
        font-weight: 500 !important;
    }

    /* === TABS === */
    [data-baseweb="tab"] {
        color: var(--text-secondary) !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.25s ease !important;
    }

    [data-baseweb="tab"][aria-selected="true"] {
        color: var(--accent-gold) !important;
        border-bottom-color: var(--accent-gold) !important;
        font-weight: 600 !important;
    }

    /* === CARDS / CONTAINERS === */
    .stContainer, [data-testid="stVerticalBlockBSeriesColumnA"] {
        background-color: var(--secondary-dark) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 6px !important;
        padding: 1.5rem !important;
    }

    /* === TEXT & PARAGRAPHS === */
    p, span, label, div {
        color: var(--text-secondary);
    }

    strong, b {
        color: var(--text-primary);
        font-weight: 600;
    }

    /* === LINKS === */
    a {
        color: var(--accent-gold) !important;
        text-decoration: none;
        font-weight: 500;
        transition: all 0.2s ease !important;
    }

    a:hover {
        color: #e5c06f !important;
        text-decoration: underline !important;
    }

    /* === DIVIDERS === */
    hr, .stHorizontalBlock hr {
        border-color: var(--border-subtle) !important;
        margin: 1.5rem 0 !important;
    }

    /* === SCROLLBAR === */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background-color: var(--primary-dark);
    }

    ::-webkit-scrollbar-thumb {
        background-color: var(--border-subtle);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background-color: var(--accent-gold);
    }

    /* === TOGGLE SWITCH === */
    [data-baseweb="checkbox"] {
        color: var(--text-primary) !important;
    }

    [data-baseweb="checkbox"] label {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }

    [data-baseweb="checkbox"] input:checked + div {
        background-color: #4a7c7e !important;
        border-color: #7cafb1 !important;
    }

    [data-baseweb="checkbox"] div {
        background-color: var(--secondary-dark) !important;
        border: 1px solid var(--border-subtle) !important;
    }

    /* === MODALS / EXPANDERS === */
    [data-testid="stExpander"] {
        border: 1px solid var(--border-subtle) !important;
        border-radius: 4px !important;
        background-color: var(--secondary-dark) !important;
    }

    [data-testid="stExpander"] [role="button"] {
        color: var(--accent-gold) !important;
    }

    /* === TABLES === */
    [data-testid="stTable"] {
        background-color: transparent !important;
        color: var(--text-primary) !important;
    }

    [data-testid="stTable"] thead {
        background-color: rgba(201, 169, 97, 0.1) !important;
        border-bottom: 2px solid var(--accent-gold) !important;
    }

    [data-testid="stTable"] thead th {
        color: var(--accent-gold) !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        border: none !important;
    }

    [data-testid="stTable"] tbody tr {
        border-bottom: 1px solid var(--border-subtle) !important;
        transition: background-color 0.2s ease !important;
    }

    [data-testid="stTable"] tbody tr:hover {
        background-color: rgba(201, 169, 97, 0.05) !important;
    }

    [data-testid="stTable"] tbody td {
        color: var(--text-secondary) !important;
        padding: 0.875rem 1rem !important;
    }

    /* === METRICS === */
    [data-testid="stMetricContainer"] {
        background-color: var(--secondary-dark) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 6px !important;
        padding: 1.5rem !important;
    }

    /* === SUCCESS / ERROR / INFO MESSAGES === */
    [data-testid="stAlert"] {
        border-radius: 4px !important;
        border-left: 4px solid !important;
    }

    [data-testid="stAlert"][data-baseweb="notification"] [data-testid="stMarkdownContainer"] {
        color: var(--text-primary) !important;
    }

    /* === LOADING SPINNER === */
    [data-testid="stSpinner"] {
        color: var(--accent-gold) !important;
    }

    /* === FORM LABELS === */
    label[data-testid="stLabel"] {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
        margin-bottom: 0.5rem !important;
    }

    /* === SMOOTH ANIMATIONS === */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    [data-testid="stVerticalBlock"] > div {
        animation: fadeIn 0.4s ease-out;
    }

    /* === MAIN CONTAINER DEPTH === */
    .main {
        background-color: var(--primary-dark) !important;
    }

    /* === REFINEMENTS === */
    [data-testid="stMarkdownContainer"] {
        word-break: break-word;
    }

    code {
        background-color: rgba(201, 169, 97, 0.1) !important;
        color: var(--accent-gold) !important;
        padding: 0.2rem 0.5rem !important;
        border-radius: 3px !important;
        font-family: 'Courier New', monospace !important;
    }

    pre {
        background-color: var(--secondary-dark) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 4px !important;
        padding: 1rem !important;
        overflow-x: auto !important;
    }

    /* === USER-SPECIFIC REFINEMENTS === */
    section[data-testid="stSidebar"] [data-testid="stImage"] {
        filter: brightness(0.95) contrast(1.05);
    }

    /* === CAPTION TEXT === */
    .stCaption {
        color: var(--text-secondary) !important;
        font-size: 0.85rem !important;
    }

    /* === ADDITIONAL PREMIUM TOUCHES === */
    
    /* Metric Cards Elevation */
    [data-testid="stMetricContainer"] {
        background: linear-gradient(135deg, rgba(31, 41, 55, 0.8) 0%, rgba(15, 20, 25, 0.8) 100%) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    }

    /* Column Containers */
    [data-testid="stVerticalBlockBSeriesColumnA"],
    [data-testid="stVerticalBlockBSeriesColumnB"],
    [data-testid="stVerticalBlockBSeriesColumnC"],
    [data-testid="stVerticalBlockBSeriesColumnD"],
    [data-testid="stVerticalBlockBSeriesColumnE"] {
        background-color: transparent !important;
    }

    /* Data Editor / Dataframe Styling */
    [data-testid="glDataEditor"] {
        background-color: var(--secondary-dark) !important;
    }

    /* Multiselect */
    [data-baseweb="multi-select"] {
        background-color: var(--secondary-dark) !important;
        border: 1px solid var(--border-subtle) !important;
    }

    /* Number Input */
    [data-baseweb="number-input"] input {
        background-color: var(--secondary-dark) !important;
        color: var(--text-primary) !important;
    }

    /* Slider Track */
    [data-baseweb="slider"] [role="slider"] {
        background-color: var(--border-subtle) !important;
    }

    /* Radio & Checkbox Labels */
    [data-testid="stRadio"] label,
    [data-testid="stCheckbox"] label {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }

    /* File Uploader */
    [data-testid="stFileUploadDropzone"] {
        border: 2px dashed var(--border-subtle) !important;
        border-radius: 6px !important;
        background-color: rgba(201, 169, 97, 0.03) !important;
    }

    [data-testid="stFileUploadDropzone"]:hover {
        border-color: var(--accent-gold) !important;
        background-color: rgba(201, 169, 97, 0.08) !important;
    }

    /* Success/Error/Warning/Info Alerts */
    .stAlert {
        border-radius: 4px !important;
        border-left: 4px solid !important;
    }

    [data-testid="stNotification"][data-bg-color="rgb(240, 243, 244)"],
    [data-testid="stAlert"] {
        background-color: var(--secondary-dark) !important;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] {
        background-color: transparent !important;
    }

    /* Number Display */
    [data-testid="stMetricValue"] {
        color: var(--accent-gold) !important;
        font-weight: 700 !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    /* Icon Styling */
    [data-testid="stImage"] img {
        filter: brightness(1) contrast(1.05);
    }

    /* Sidebar Images */
    section[data-testid="stSidebar"] [data-testid="stImage"] img {
        border-radius: 2px;
    }

    /* Page Links in Sidebar */
    section[data-testid="stSidebar"] li {
        margin-bottom: 0.5rem;
    }

    section[data-testid="stSidebar"] a {
        color: var(--text-secondary) !important;
        transition: all 0.2s ease !important;
    }

    section[data-testid="stSidebar"] a:hover {
        color: var(--accent-gold) !important;
    }

    /* Active Page Link Styling */
    section[data-testid="stSidebar"] a.active {
        color: var(--accent-gold) !important;
        font-weight: 600 !important;
        border-left: 3px solid var(--accent-gold) !important;
        padding-left: 0.75rem !important;
    }

    /* Refined Gaps Between Elements */
    [data-testid="stVerticalBlock"] > div {
        margin-bottom: 1.5rem;
    }

    /* Grid Spacing */
    [data-testid="stColumns"] > div > div {
        padding: 0 0.75rem;
    }

    /* Subtle focus indication */
    button:focus, input:focus, textarea:focus {
        outline: none;
    }

    /* Streamlit Footer */
    footer {
        background-color: var(--secondary-dark) !important;
        border-top: 1px solid var(--border-subtle) !important;
    }

    footer a {
        color: var(--accent-gold) !important;
    }

    /* Responsive Typography */
    @media (max-width: 768px) {
        h1 {
            font-size: 2rem;
        }

        h2 {
            font-size: 1.5rem;
        }

        .stButton > button {
            width: 100%;
        }
    }
</style>
"""


def setup_page(page_title: str, page_icon: str):
    """Common page setup: config, sidebar logo, CSS, language toggle."""
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout="wide")
    st.sidebar.image("resources/logo.png", width=180)
    lang_selector()
    st.sidebar.markdown("---")
    st.markdown(BRAND_CSS, unsafe_allow_html=True)
