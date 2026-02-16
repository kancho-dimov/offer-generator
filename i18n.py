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
- **Настройки** — управление на клиенти, условия и брандинг""",
        "en": """Welcome to the offer and order generation system.

Use the menu on the left to navigate:
- **Dashboard** — overview of recent offers and orders
- **New Offer** — create an offer or pricelist
- **New Order** — create an order
- **Search** — search products
- **Settings** — manage customers, terms and branding""",
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
    "measure": {"bg": "Мярка", "en": "Unit"},
    "pcs_label": {"bg": "бр.", "en": "pcs"},
    "carton_label": {"bg": "кш.", "en": "ctn"},
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
    .stApp { font-family: 'Segoe UI', Arial, sans-serif; }
    section[data-testid="stSidebar"] { background-color: #f0f8ff; }
    h1, h2, h3 { color: #0086CE; }
    .stButton>button { background-color: #0086CE; color: white; border: none; }
    .stButton>button:hover { background-color: #006ba1; color: white; }
    div[data-baseweb="select"]:hover { border-color: #0086CE; cursor: pointer; }
    div[data-baseweb="select"] > div:hover { border-color: #0086CE; }
</style>
"""


def setup_page(page_title: str, page_icon: str):
    """Common page setup: config, sidebar logo, CSS, language toggle."""
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout="wide")
    st.sidebar.image("resources/logo.png", width=180)
    lang_selector()
    st.sidebar.markdown("---")
    st.markdown(BRAND_CSS, unsafe_allow_html=True)
