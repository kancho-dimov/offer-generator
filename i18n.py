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

    # --- Dashboard actions ---
    "edit": {"bg": "Редакция", "en": "Edit"},
    "edit_order_banner": {"bg": "Редактирате поръчка {num} — ще бъде създадена нова поръчка.", "en": "Editing order {num} — a new order will be created."},
    "edit_order_draft_banner": {"bg": "Редактирате чернова {num} — генерирането ще презапише съществуващия документ.", "en": "Editing draft {num} — generating will overwrite the existing document."},
    "edit_order_revision_banner": {"bg": "Редактирате изпратена поръчка {num} — генерирането ще създаде версия v{ver}.", "en": "Editing submitted order {num} — generating will create revision v{ver}."},
    "edit_offer_banner": {"bg": "Редактирате чернова {num} — генерирането ще презапише съществуващия документ.", "en": "Editing draft {num} — generating will overwrite the existing document."},
    "edit_offer_revision_banner": {"bg": "Редактирате изпратена оферта {num} — генерирането ще създаде версия v{ver}.", "en": "Editing sent offer {num} — generating will create revision v{ver}."},
    "version_history": {"bg": "История ({n} по-стари версии)", "en": "History ({n} older version(s))"},
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
    "enrich_quick_sync": {"bg": "Регистрирай в каталога (без API)", "en": "Register to catalog (no API)"},
    "enrich_quick_sync_hint": {"bg": "Базова регистрация от ценовата листа — без обогатяване, без разходи.", "en": "Baseline registration from pricelist — no enrichment, no API cost."},
    "enrich_step0": {"bg": "Регистриране...", "en": "Registering..."},
    "enrich_basic": {"bg": "Основно обогатени", "en": "Basic enriched"},
    "enrich_baseline": {"bg": "Регистрирани", "en": "Registered"},

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
    """No-op stub kept for backward compatibility."""
    pass


# ── Navbar configuration ───────────────────────────────────────────────────

_PAGE_NAV_KEY = {
    "Основен панел": "dashboard",
    "Нова Оферта": "offer",
    "Нова Поръчка": "order",
    "Търсене на продукти": "search",
    "Настройки": "settings",
    "Актуализиране на каталог": "catalog",
}

_NAV_ICONS = {
    "dashboard": '<path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>',
    "offer":     '<path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>',
    "order":     '<path stroke-linecap="round" stroke-linejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>',
    "search":    '<path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>',
    "settings":  '<path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>',
    "catalog":   '<path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>',
}

_NAV_LABELS = {
    "dashboard": {"bg": "Панел",     "en": "Dashboard"},
    "offer":     {"bg": "Оферта",    "en": "Offer"},
    "order":     {"bg": "Поръчка",   "en": "Order"},
    "search":    {"bg": "Търсене",   "en": "Search"},
    "settings":  {"bg": "Настройки", "en": "Settings"},
    "catalog":   {"bg": "Каталог",   "en": "Catalog"},
}

_NAV_URLS = {
    "dashboard": "/Основен_панел",
    "offer":     "/Нова_Оферта",
    "order":     "/Нова_Поръчка",
    "search":    "/Търсене",
    "settings":  "/Настройки",
    "catalog":   "/Актуализиране_на_каталог",
}


def render_navbar(current_page: str = "") -> None:
    """Inject the sticky floating navbar into the Streamlit page."""
    lang = get_lang()

    desktop_links = ""
    mobile_links = ""
    for key, url in _NAV_URLS.items():
        label = _NAV_LABELS[key][lang]
        icon_path = _NAV_ICONS[key]
        active_cls = " nav-active" if key == current_page else ""
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18"'
            ' fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">'
            + icon_path
            + "</svg>"
        )
        desktop_links += f'<a href="{url}" target="_self" class="nav-link{active_cls}">{label}</a>'
        mobile_links += (
            f'<a href="{url}" target="_self" class="mob-link{active_cls}">'
            f'<span class="mob-icon">{svg}</span>{label}</a>'
        )

    other_lang = "bg" if lang == "en" else "en"
    lang_label = "EN" if lang == "bg" else "BG"

    toggle_js = (
        "var d=document.getElementById('mobMenu');"
        "var o=document.getElementById('mobOverlay');"
        "d.classList.toggle('open');o.classList.toggle('open');"
    )
    close_js = (
        "document.getElementById('mobMenu').classList.remove('open');"
        "document.getElementById('mobOverlay').classList.remove('open');"
    )

    html = (
        '<nav id="wNavbar">'
        '<a href="/" target="_self" class="nav-logo">'
        '<span style="font-weight:700;color:#0086CE;font-size:1.1rem;letter-spacing:-0.02em">Romstal</span>'
        "</a>"
        f'<div class="nav-links">{desktop_links}</div>'
        '<div class="nav-actions">'
        f'<a href="?lang={other_lang}" target="_self" class="lang-toggle">{lang_label}</a>'
        f'<button class="burger" onclick="{toggle_js}">'
        '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="none"'
        ' viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">'
        '<path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16"/>'
        "</svg></button>"
        "</div></nav>"
        f'<div id="mobOverlay" onclick="{close_js}"></div>'
        f'<div id="mobMenu">{mobile_links}'
        f'<div class="mob-lang"><a href="?lang={other_lang}" class="lang-toggle">{lang_label}</a></div>'
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


BRAND_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Reset Streamlit chrome ───────────────────────────────────────────── */
section[data-testid="stSidebar"]  { display: none !important; }
#MainMenu                          { visibility: hidden !important; }
header[data-testid="stHeader"]    { display: none !important; }
footer                             { display: none !important; }

/* ── Base ─────────────────────────────────────────────────────────────── */
.stApp {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    background: #F8FAFC;
    color: #0F172A;
}
.block-container {
    padding-top: 80px !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 1200px;
}
h1, h2, h3 { color: #0F172A; font-weight: 700; }
a { color: #0086CE; }

/* ── Buttons ──────────────────────────────────────────────────────────── */
.stButton > button {
    background-color: #0086CE !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    min-height: 44px !important;
    padding: 0 1.25rem !important;
    transition: background 0.2s;
}
.stButton > button:hover { background-color: #006ba1 !important; }

/* ── Floating Navbar ──────────────────────────────────────────────────── */
#wNavbar {
    position: fixed;
    top: 8px;
    left: 16px;
    right: 16px;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 56px;
    padding: 0 20px;
    background: rgba(255,255,255,0.88);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.07);
}
.nav-logo { display: flex; align-items: center; text-decoration: none; flex-shrink: 0; }
.nav-links { display: flex; align-items: center; gap: 4px; }
.nav-link {
    display: inline-flex;
    align-items: center;
    padding: 6px 14px;
    border-radius: 8px;
    font-size: 0.875rem;
    font-weight: 500;
    color: #475569;
    text-decoration: none;
    transition: background 0.15s, color 0.15s;
    white-space: nowrap;
}
.nav-link:hover { background: #F1F5F9; color: #0F172A; }
.nav-active     { background: #E0F0FA !important; color: #0086CE !important; }
.nav-actions    { display: flex; align-items: center; gap: 10px; }
.lang-toggle {
    font-size: 0.8rem;
    font-weight: 600;
    color: #64748B;
    text-decoration: none;
    padding: 4px 10px;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    transition: border-color 0.15s, color 0.15s;
    letter-spacing: 0.04em;
}
.lang-toggle:hover { border-color: #0086CE; color: #0086CE; }
.burger {
    display: none;
    background: none;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    width: 40px;
    height: 40px;
    cursor: pointer;
    align-items: center;
    justify-content: center;
    color: #475569;
    padding: 0;
    transition: border-color 0.15s;
}
.burger:hover { border-color: #0086CE; color: #0086CE; }

/* ── Mobile overlay ───────────────────────────────────────────────────── */
#mobOverlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(15,23,42,0.35);
    z-index: 9990;
    backdrop-filter: blur(2px);
}
#mobOverlay.open { display: block; }

/* ── Mobile dropdown menu ─────────────────────────────────────────────── */
#mobMenu {
    position: fixed;
    top: 72px;
    left: 16px;
    right: 16px;
    z-index: 9995;
    background: rgba(255,255,255,0.97);
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    display: flex;
    flex-direction: column;
    gap: 4px;
    max-height: 0;
    overflow: hidden;
    opacity: 0;
    pointer-events: none;
    padding: 0 8px;
    transition: max-height 0.25s ease, opacity 0.2s ease, padding 0.2s;
}
#mobMenu.open {
    max-height: 520px;
    opacity: 1;
    pointer-events: auto;
    padding: 12px 8px;
}
.mob-link {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 10px;
    font-size: 0.95rem;
    font-weight: 500;
    color: #334155;
    text-decoration: none;
    transition: background 0.15s, color 0.15s;
}
.mob-link:hover, .mob-link.nav-active { background: #EFF6FF; color: #0086CE; }
.mob-icon { display: flex; align-items: center; color: inherit; flex-shrink: 0; }
.mob-lang { padding: 8px 16px 4px; border-top: 1px solid #F1F5F9; margin-top: 4px; }

/* ── Responsive breakpoints ───────────────────────────────────────────── */
@media (max-width: 820px) {
    .nav-links { display: none; }
    .burger    { display: inline-flex; }
}
@media (max-width: 768px) {
    .block-container {
        padding-top: 72px !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }
    input, textarea, select,
    input[type="text"], input[type="number"],
    input[type="email"], input[type="search"] { font-size: 16px !important; }
    div[data-baseweb="select"] > div:first-child { min-height: 44px !important; }
    h1 { font-size: 1.4rem !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1.05rem !important; }
    .main { -webkit-overflow-scrolling: touch; }
    [data-testid="metric-container"] { padding: 0.5rem 0.4rem !important; }
    p, li, .stMarkdown { font-size: 0.92rem !important; line-height: 1.5 !important; }
    .stCaption, small { font-size: 0.78rem !important; }
}
@media (max-width: 430px) {
    .block-container {
        padding-left: 0.4rem !important;
        padding-right: 0.4rem !important;
        padding-bottom: env(safe-area-inset-bottom, 1rem) !important;
    }
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        flex: 1 1 100% !important;
        min-width: 100% !important;
        width: 100% !important;
    }
    .stButton > button {
        width: 100% !important;
        min-height: 48px !important;
        font-size: 1rem !important;
    }
    .stLinkButton > a {
        width: 100% !important;
        min-height: 48px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    [data-testid="stDataFrame"] {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }
    .stApp { overflow-x: hidden; }
}
</style>
"""


def setup_page(page_title: str, page_icon: str) -> None:
    """Common page setup: config, CSS, floating navbar."""
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(BRAND_CSS, unsafe_allow_html=True)
    current_page = _PAGE_NAV_KEY.get(page_title, "")
    render_navbar(current_page=current_page)
