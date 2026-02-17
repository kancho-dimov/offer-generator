"""
Send emails via Gmail API for offers and orders.

Three modes:
  - send_offer_to_customer: Send offer/pricelist with PDF attachment
  - send_order_to_cs: Send order to customer service (with Sheets link)
  - send_order_to_customer: Send order confirmation with PDF attachment

Includes template system with {variable} placeholders for preview/editing.

Usage:
    from tools.send_email import (
        prepare_offer_email, prepare_order_email,
        send_offer_to_customer, send_order_to_cs,
    )
"""

import base64
import html as html_module
import re
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from tools.google_auth import get_credentials, get_drive_service, get_gmail_service

# Basic email validation — rejects control characters, newlines, missing @
_EMAIL_RE = re.compile(r"^[^@\s\r\n]+@[^@\s\r\n]+\.[^@\s\r\n]+$")


def _validate_email(email: str) -> str:
    """Validate and return a safe email address, or raise ValueError."""
    email = email.strip()
    if not email or not _EMAIL_RE.match(email):
        raise ValueError(f"Invalid email address: {email!r}")
    if any(c in email for c in ("\r", "\n", "\x00")):
        raise ValueError(f"Email contains control characters: {email!r}")
    return email
from tools.sheets_api import read_sheet

MASTER_CATALOG_ID = "1O1rD0PdKIIY8qKWkNsdElEcdsg1-JQQG1WmfuVXrUVY"

# --- Default email templates (plain text with {variables}) ---

OFFER_TEMPLATE = """\
Уважаеми {contact_name},

Изпращаме Ви {document_type} {document_number}.

Моля, вижте приложения PDF документ.
Моля, не се колебайте да се свържете с нас при въпроси.

{signature}"""

ORDER_CONFIRM_TEMPLATE = """\
Уважаеми {contact_name},

Вашата поръчка {document_number} е приета за обработка.
Очаквана дата на доставка: {delivery_date}

Моля, вижте приложения PDF документ.

{signature}"""

DEFAULT_SIGNATURE = """\
С уважение,
{our_company}
{our_phone}
{our_email}"""

# Available template variables (for UI reference)
OFFER_VARIABLES = [
    "contact_name", "customer_company", "document_type",
    "document_number", "our_company", "our_phone", "our_email",
    "signature",
]
ORDER_VARIABLES = [
    "contact_name", "customer_company", "document_number",
    "delivery_date", "our_company", "our_phone", "our_email",
    "signature",
]


def _get_branding_value(key: str) -> str:
    """Read a single value from Company_Branding."""
    rows = read_sheet(MASTER_CATALOG_ID, "'Company_Branding'!A:B")
    for row in rows:
        if row and row[0] == key and len(row) > 1:
            return row[1]
    return ""


def _get_branding_values(*keys: str) -> dict[str, str]:
    """Read multiple values from Company_Branding in one call."""
    rows = read_sheet(MASTER_CATALOG_ID, "'Company_Branding'!A:B")
    result = {k: "" for k in keys}
    for row in rows:
        if row and row[0] in result and len(row) > 1:
            result[row[0]] = row[1]
    return result


def _text_to_html(text: str) -> str:
    """Convert plain text email body to styled HTML."""
    escaped = html_module.escape(text)
    paragraphs = escaped.split("\n\n")
    html_parts = []
    for p in paragraphs:
        lines = p.split("\n")
        html_parts.append("<p>" + "<br>\n".join(lines) + "</p>")
    return (
        '<div style="font-family: Arial, sans-serif; max-width: 600px;">'
        + "".join(html_parts)
        + "</div>"
    )


def _download_pdf(pdf_url: str) -> bytes | None:
    """Download a PDF from Google Sheets export URL using OAuth credentials."""
    if not pdf_url:
        return None
    try:
        import httpx
        creds = get_credentials()
        token = creds.token
        resp = httpx.get(pdf_url, headers={"Authorization": f"Bearer {token}"}, follow_redirects=True, timeout=30)
        if resp.status_code == 200 and len(resp.content) > 100:
            return resp.content
    except Exception as e:
        print(f"  Warning: Could not download PDF: {e}")
    return None


def _share_for_viewing(spreadsheet_url: str) -> None:
    """Share the spreadsheet so anyone with the link can view it."""
    try:
        # Extract spreadsheet ID from URL
        # URL format: https://docs.google.com/spreadsheets/d/{id}
        parts = spreadsheet_url.split("/d/")
        if len(parts) < 2:
            return
        spreadsheet_id = parts[1].split("/")[0].split("?")[0]
        drive = get_drive_service()
        drive.permissions().create(
            fileId=spreadsheet_id,
            body={"type": "anyone", "role": "reader"},
            fields="id",
        ).execute()
    except Exception as e:
        print(f"  Warning: Could not share spreadsheet: {e}")


def _add_view_button(body_html: str, spreadsheet_url: str) -> str:
    """Append a styled 'View online' button to the email HTML body."""
    safe_url = spreadsheet_url if spreadsheet_url.startswith("https://") else "#"
    button_html = (
        '<br><p>'
        f'<a href="{safe_url}" style="background-color: #0086CE; color: white; '
        'padding: 10px 24px; text-decoration: none; border-radius: 4px; '
        'display: inline-block; font-family: Arial, sans-serif; font-size: 14px;">'
        'Преглед онлайн / View online</a>'
        '</p>'
    )
    # Insert before closing </div> if present, otherwise append
    if "</div>" in body_html:
        return body_html.replace("</div>", button_html + "</div>", 1)
    return body_html + button_html


def _send_plain(to: str, subject: str, body_html: str) -> dict:
    """Send a plain HTML email via Gmail API (no attachments)."""
    service = get_gmail_service()
    message = MIMEText(body_html, "html", "utf-8")
    message["to"] = to
    message["subject"] = subject

    sender = _get_branding_value("company_email")
    if sender:
        message["from"] = sender

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    return service.users().messages().send(userId="me", body={"raw": raw}).execute()


def _send_with_pdf(to: str, subject: str, body_html: str, pdf_data: bytes, filename: str) -> dict:
    """Send an HTML email with a PDF attachment via Gmail API."""
    service = get_gmail_service()

    msg = MIMEMultipart("mixed")
    msg["to"] = to
    msg["subject"] = subject

    sender = _get_branding_value("company_email")
    if sender:
        msg["from"] = sender

    # HTML body
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    # PDF attachment
    pdf_part = MIMEApplication(pdf_data, _subtype="pdf")
    pdf_part.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(pdf_part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
    return service.users().messages().send(userId="me", body={"raw": raw}).execute()


# --- Prepare functions (for preview) ---

def _build_signature(branding: dict) -> str:
    """Build email signature from Company_Branding or default."""
    custom_sig = branding.get("email_signature", "")
    if custom_sig:
        return custom_sig
    return DEFAULT_SIGNATURE.format_map({
        "our_company": branding.get("company_name", "") or "РОМСТАЛ БЪЛГАРИЯ ЕООД",
        "our_phone": branding.get("company_phone", ""),
        "our_email": branding.get("company_email", ""),
    })


def prepare_offer_email(
    offer_number: str, customer: dict, mode: str = "offer",
) -> dict:
    """Prepare offer/pricelist email for preview. Returns dict with subject, body, to, variables."""
    branding = _get_branding_values(
        "company_name", "company_phone", "company_email", "email_signature",
        "email_offer_template",
    )
    company_name = branding["company_name"] or "РОМСТАЛ БЪЛГАРИЯ ЕООД"
    label = "Оферта" if mode == "offer" else "Ценова листа"

    contact = customer.get("contact_name", "") or "партньор"
    signature = _build_signature(branding)

    variables = {
        "contact_name": contact,
        "customer_company": customer.get("company_name", ""),
        "document_type": label.lower(),
        "document_number": offer_number,
        "our_company": company_name,
        "our_phone": branding["company_phone"],
        "our_email": branding["company_email"],
        "signature": signature,
    }

    # Use custom template from branding if available, otherwise default
    template = branding.get("email_offer_template", "").strip() or OFFER_TEMPLATE

    subject = f"{label} {offer_number} | {company_name}"
    body_text = template.format_map(variables)

    return {
        "to": customer.get("email", ""),
        "subject": subject,
        "body": body_text,
        "variables": variables,
        "available_variables": OFFER_VARIABLES,
    }


def prepare_order_email(
    order_number: str, customer: dict, delivery_date: str,
) -> dict:
    """Prepare order confirmation email for preview. Returns dict with subject, body, to, variables."""
    branding = _get_branding_values(
        "company_name", "company_phone", "company_email", "email_signature",
        "email_order_template",
    )
    company_name = branding["company_name"] or "РОМСТАЛ БЪЛГАРИЯ ЕООД"

    contact = customer.get("contact_name", "") or "партньор"
    signature = _build_signature(branding)

    variables = {
        "contact_name": contact,
        "customer_company": customer.get("company_name", ""),
        "document_number": order_number,
        "delivery_date": delivery_date,
        "our_company": company_name,
        "our_phone": branding["company_phone"],
        "our_email": branding["company_email"],
        "signature": signature,
    }

    # Use custom template from branding if available, otherwise default
    template = branding.get("email_order_template", "").strip() or ORDER_CONFIRM_TEMPLATE

    subject = f"Потвърждение на поръчка {order_number} | {company_name}"
    body_text = template.format_map(variables)

    return {
        "to": customer.get("email", ""),
        "subject": subject,
        "body": body_text,
        "variables": variables,
        "available_variables": ORDER_VARIABLES,
    }


# --- Send functions ---

def send_offer_to_customer(
    offer_number: str,
    customer: dict,
    spreadsheet_url: str,
    pdf_url: str,
    mode: str = "offer",
    subject_override: str | None = None,
    body_text_override: str | None = None,
    email_override: str | None = None,
) -> dict:
    """Send an offer or pricelist to the customer with PDF attached."""
    customer_email = _validate_email(email_override or customer.get("email", ""))

    # Use overrides (from preview/edit) or generate defaults
    if subject_override and body_text_override:
        subject = subject_override
        body_html = _text_to_html(body_text_override)
    else:
        prepared = prepare_offer_email(offer_number, customer, mode)
        subject = prepared["subject"]
        body_html = _text_to_html(prepared["body"])

    # Download and attach PDF
    pdf_data = _download_pdf(pdf_url)
    if pdf_data:
        filename = f"{offer_number.replace('/', '-')}.pdf"
        result = _send_with_pdf(customer_email, subject, body_html, pdf_data, filename)
    else:
        # Fallback: send with PDF download link if download failed
        safe_pdf = pdf_url if pdf_url.startswith("https://") else "#"
        body_html += f'<p><a href="{safe_pdf}">Изтегли PDF</a></p>'
        result = _send_plain(customer_email, subject, body_html)

    print(f"  Email sent to {customer_email}: {subject}")
    return result


def send_order_to_cs(
    order_number: str,
    offer_number: str,
    customer: dict,
    sales_agent_code: str,
    delivery_terms: str,
    payment_terms: str,
    delivery_date: str,
    total_excl_vat: float,
    total_incl_vat: float,
    spreadsheet_url: str,
    pdf_url: str,
    lines_summary: list[dict] | None = None,
    delivery_address: str = "",
) -> dict:
    """Send an order to customer service for booking into SAP."""
    cs_email = _get_branding_value("cs_email")
    if not cs_email:
        raise ValueError("cs_email not set in Company_Branding")

    subject = f"Поръчка {order_number} | {customer.get('company_name', '')}"

    _e = html_module.escape  # shorthand for escaping user data

    lines_html = ""
    if lines_summary:
        lines_html = "<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse; font-size:12px;'>"
        lines_html += "<tr><th>Код</th><th>Наименование</th><th>К-во</th><th>Ед.</th><th>Нето цена</th><th>Отстъпка</th><th>Общо</th></tr>"
        for line in lines_summary:
            lines_html += f"<tr><td>{_e(str(line.get('product_code','')))}</td><td>{_e(str(line.get('name','')))}</td>"
            lines_html += f"<td>{_e(str(line.get('quantity','')))}</td><td>{_e(str(line.get('measure_unit','pcs')))}</td>"
            lines_html += f"<td>{_e(str(line.get('net_price','')))}</td><td>{_e(str(line.get('discount','')))}</td>"
            lines_html += f"<td>{_e(str(line.get('line_total','')))}</td></tr>"
        lines_html += "</table>"

    addr = delivery_address or customer.get("delivery_address", "") or customer.get("address", "")

    # Validate URLs before embedding in HTML
    safe_sheet_url = spreadsheet_url if spreadsheet_url.startswith("https://") else "#"

    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 700px;">
        <h2 style="color: #0086CE;">Поръчка {_e(order_number)}</h2>
        <table cellpadding="4" style="font-size: 13px;">
            <tr><td><strong>Оферта:</strong></td><td>{_e(offer_number or 'Без оферта')}</td></tr>
            <tr><td><strong>Клиент:</strong></td><td>{_e(customer.get('company_name', ''))} ({_e(customer.get('customer_id', ''))})</td></tr>
            <tr><td><strong>Лице за контакт:</strong></td><td>{_e(customer.get('contact_name', ''))}</td></tr>
            <tr><td><strong>Тел/Email:</strong></td><td>{_e(customer.get('phone', ''))} / {_e(customer.get('email', ''))}</td></tr>
            <tr><td><strong>Адрес на доставка:</strong></td><td>{_e(addr)}</td></tr>
            <tr><td><strong>Търговски агент SAP:</strong></td><td>{_e(sales_agent_code)}</td></tr>
            <tr><td><strong>Условия на доставка:</strong></td><td>{_e(delivery_terms)}</td></tr>
            <tr><td><strong>Условия на плащане:</strong></td><td>{_e(payment_terms)}</td></tr>
            <tr><td><strong>Дата на доставка:</strong></td><td>{_e(delivery_date)}</td></tr>
            <tr><td><strong>Сума без ДДС:</strong></td><td>{total_excl_vat:.2f} EUR</td></tr>
            <tr><td><strong>Сума с ДДС:</strong></td><td>{total_incl_vat:.2f} EUR</td></tr>
        </table>
        <br>
        {lines_html}
        <br>
        <p>
            <a href="{safe_sheet_url}" style="background-color: #0086CE; color: white;
               padding: 10px 20px; text-decoration: none; border-radius: 4px;
               display: inline-block; margin: 8px 0;">
                Отвори поръчката
            </a>
        </p>
    </div>
    """

    # Attach PDF for inline preview in email client
    pdf_data = _download_pdf(pdf_url)
    if pdf_data:
        filename = f"{order_number.replace('/', '-')}.pdf"
        result = _send_with_pdf(cs_email, subject, body, pdf_data, filename)
    else:
        result = _send_plain(cs_email, subject, body)
    print(f"  Order email sent to CS ({cs_email}): {subject}")
    return result


def send_order_to_customer(
    order_number: str,
    customer: dict,
    delivery_date: str,
    spreadsheet_url: str,
    pdf_url: str,
    subject_override: str | None = None,
    body_text_override: str | None = None,
    email_override: str | None = None,
) -> dict:
    """Send order confirmation to the customer with PDF only (no Sheet link)."""
    customer_email = _validate_email(email_override or customer.get("email", ""))

    # Use overrides (from preview/edit) or generate defaults
    if subject_override and body_text_override:
        subject = subject_override
        body_html = _text_to_html(body_text_override)
    else:
        prepared = prepare_order_email(order_number, customer, delivery_date)
        subject = prepared["subject"]
        body_html = _text_to_html(prepared["body"])

    # Download and attach PDF
    pdf_data = _download_pdf(pdf_url)
    if pdf_data:
        filename = f"{order_number.replace('/', '-')}.pdf"
        result = _send_with_pdf(customer_email, subject, body_html, pdf_data, filename)
    else:
        safe_pdf = pdf_url if pdf_url.startswith("https://") else "#"
        body_html += f'<p><a href="{safe_pdf}">Изтегли PDF</a></p>'
        result = _send_plain(customer_email, subject, body_html)

    print(f"  Order confirmation sent to {customer_email}: {subject}")
    return result
