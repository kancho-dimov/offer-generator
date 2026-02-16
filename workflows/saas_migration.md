# SaaS Migration Plan — Offer Generator

## Context

Convert the current Streamlit + Google Sheets app into a multi-tenant SaaS product for selling to other HVAC/distribution companies. Hosted on GCP, MVP-first approach.

**Current state:** Streamlit + Google Sheets (single user, local)
**Target state:** FastAPI + PostgreSQL + React (multi-tenant, cloud)

---

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│  React Frontend │────▶│  FastAPI Backend  │────▶│  PostgreSQL  │
│  (Vite + TS)    │     │  (Python 3.13)   │     │  (Cloud SQL) │
└─────────────────┘     └──────┬───────────┘     └──────────────┘
                               │
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
              Cloud Storage  SendGrid   WeasyPrint
              (images/PDFs)  (emails)   (PDF gen)
```

**Key decisions:**
- **FastAPI** (not Django) — lightweight, async, Python (reuse business logic)
- **PostgreSQL** — proper relational DB, replaces Google Sheets
- **React + Vite** — modern frontend, replaces Streamlit
- **WeasyPrint** — HTML to PDF, replaces Google Sheets document generation
- **SendGrid** — email delivery, replaces Gmail API (works per-tenant without OAuth)
- **Firebase Auth** — user auth + multi-tenancy (free tier, fast to implement)

---

## Database Schema (PostgreSQL)

### Core tables

```sql
-- Multi-tenancy: every row belongs to an organization
organizations (
  id UUID PK,
  name TEXT,            -- "Romstal BG", "ABC Heating"
  slug TEXT UNIQUE,     -- URL-friendly name
  logo_url TEXT,
  primary_color TEXT,   -- brand color hex
  vat_rate DECIMAL,     -- 0.20 for BG
  currency TEXT,        -- "BGN", "EUR"
  address TEXT,
  phone TEXT,
  email TEXT,
  created_at TIMESTAMP
)

users (
  id UUID PK,
  org_id UUID FK → organizations,
  email TEXT UNIQUE,
  firebase_uid TEXT UNIQUE,
  name TEXT,
  role TEXT,            -- "admin", "sales", "viewer"
  sap_agent_code TEXT,
  created_at TIMESTAMP
)

products (
  id UUID PK,
  org_id UUID FK → organizations,
  product_code TEXT,
  supplier_code TEXT,
  name TEXT,
  brand TEXT,
  category TEXT,
  subcategory TEXT,
  short_description TEXT,
  long_description TEXT,
  features TEXT,
  specifications JSONB,
  base_price DECIMAL,
  currency TEXT,
  image_url TEXT,
  thumbnail_url TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP,
  UNIQUE(org_id, product_code)
)

customers (
  id UUID PK,
  org_id UUID FK → organizations,
  customer_code TEXT,   -- SAP number
  company_name TEXT,
  company_reg_id TEXT,  -- EIK
  vat_number TEXT,
  contact_name TEXT,
  email TEXT,
  phone TEXT,
  address TEXT,
  delivery_address TEXT,
  discount_tier TEXT,
  default_discount_pct DECIMAL,
  payment_terms TEXT,
  notes TEXT,
  created_at TIMESTAMP,
  UNIQUE(org_id, customer_code)
)

discount_rules (
  id UUID PK,
  org_id UUID FK → organizations,
  rule_name TEXT,
  brand TEXT,
  category TEXT,
  customer_tier TEXT,
  discount_pct DECIMAL,
  is_stackable BOOLEAN,
  valid_from DATE,
  valid_to DATE,
  is_active BOOLEAN DEFAULT true
)

offers (
  id UUID PK,
  org_id UUID FK → organizations,
  user_id UUID FK → users,
  offer_number TEXT,    -- "OFR-2026-001"
  mode TEXT,            -- "offer" or "pricelist"
  customer_id UUID FK → customers,
  status TEXT,          -- "draft", "sent", "accepted", "expired", "converted"
  validity_days INT,
  notes TEXT,
  subtotal_excl_vat DECIMAL,
  vat_amount DECIMAL,
  total_incl_vat DECIMAL,
  pdf_url TEXT,
  created_at TIMESTAMP,
  sent_at TIMESTAMP
)

offer_lines (
  id UUID PK,
  offer_id UUID FK → offers,
  line_number INT,
  product_id UUID FK → products,
  quantity INT,
  base_price DECIMAL,
  discount_pct DECIMAL,
  net_price DECIMAL,
  total DECIMAL,
  group_label TEXT      -- brand/category grouping header
)

orders (
  id UUID PK,
  org_id UUID FK → organizations,
  user_id UUID FK → users,
  order_number TEXT,
  offer_id UUID FK → offers NULL,
  customer_id UUID FK → customers,
  status TEXT,          -- "draft", "submitted", "confirmed", "shipped", "completed"
  delivery_date DATE,
  delivery_terms TEXT,
  delivery_address TEXT,
  payment_terms TEXT,
  sales_agent_code TEXT,
  subtotal_excl_vat DECIMAL,
  vat_amount DECIMAL,
  total_incl_vat DECIMAL,
  notes TEXT,
  pdf_url TEXT,
  created_at TIMESTAMP,
  submitted_at TIMESTAMP
)

order_lines (
  id UUID PK,
  order_id UUID FK → orders,
  line_number INT,
  product_id UUID FK → products,
  measure_unit TEXT,    -- "pcs" or "carton"
  pcs_per_unit INT,
  quantity INT,
  total_pcs INT,
  unit_price DECIMAL,
  discount_pct DECIMAL,
  net_excl_vat DECIMAL,
  total_excl_vat DECIMAL
)

logistics (
  id UUID PK,
  org_id UUID FK → organizations,
  product_code TEXT,
  description TEXT,
  division TEXT,
  base_unit TEXT,
  supplier TEXT,
  pcs_per_carton INT,
  min_order_qty INT,
  UNIQUE(org_id, product_code)
)

-- Config: delivery terms, payment terms, branding (per org)
org_settings (
  id UUID PK,
  org_id UUID FK → organizations,
  setting_key TEXT,     -- "delivery_terms", "payment_terms", "offer_counter", etc.
  setting_value JSONB,
  UNIQUE(org_id, setting_key)
)
```

---

## MVP Phases (Implementation Order)

### Phase A: Project Scaffold + Auth (Week 1)

**New directory structure:**
```
saas/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings (env vars)
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── api/                 # Route handlers
│   │   ├── services/            # Business logic (migrated from tools/)
│   │   └── middleware/          # Auth, tenant isolation, CORS
│   ├── alembic/                 # DB migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/            # API client
│   │   └── i18n/                # Translations (migrate from i18n.py)
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml           # Local dev (API + DB + frontend)
└── cloudbuild.yaml              # GCP deployment
```

### Phase B: Core API Endpoints (Week 2)

**Migrate business logic from tools/ to backend/app/services/:**

| Current tool | New service | What changes |
|---|---|---|
| `tools/discount_engine.py` | `services/discount_engine.py` | Reads from PostgreSQL instead of Sheets |
| `tools/product_search.py` | `api/products.py` | Full-text search via PostgreSQL ILIKE |
| `tools/generate_offer.py` | `services/offer_generator.py` | Creates DB records + generates PDF |
| `tools/generate_order.py` | `services/order_generator.py` | Creates DB records + generates PDF |
| `tools/send_email.py` | `services/email_service.py` | SendGrid API instead of Gmail |
| `tools/format_offer_sheet.py` | `services/pdf_generator.py` | WeasyPrint HTML to PDF |
| `tools/offer_log.py` | Replaced by DB queries | Offers table IS the log |
| `tools/import_logistics.py` | `api/logistics.py` upload endpoint | Parses Excel, inserts to DB |

**API endpoints:**
```
POST   /api/auth/register
POST   /api/auth/login
GET    /api/products              # List (search, filter)
POST   /api/products/import       # Bulk import CSV/Excel
GET    /api/customers
POST   /api/customers
PUT    /api/customers/:id
DELETE /api/customers/:id
POST   /api/offers
GET    /api/offers
GET    /api/offers/:id
GET    /api/offers/:id/pdf
POST   /api/offers/:id/send
POST   /api/orders
GET    /api/orders
GET    /api/orders/:id/pdf
POST   /api/orders/:id/send
GET    /api/analytics/summary
GET    /api/settings
PUT    /api/settings
```

### Phase C: PDF Generation (Week 2-3)

Jinja2 HTML template + WeasyPrint. Per-tenant branding (logo, color) via template variables.

### Phase D: React Frontend (Week 3-4)

| Streamlit page | React page | Route |
|---|---|---|
| `app.py` | Landing/Home | `/` |
| `pages/1_Основен_панел.py` | Dashboard | `/dashboard` |
| `pages/2_Нова_Оферта.py` | New Offer | `/offers/new` |
| `pages/3_Нова_Поръчка.py` | New Order | `/orders/new` |
| `pages/4_Търсене.py` | Product Search | `/products` |
| `pages/5_Настройки.py` | Settings | `/settings` |
| (new) | Login/Register | `/login`, `/register` |

UI: Tailwind CSS + shadcn/ui

### Phase E: Deploy to GCP (Week 4-5)

- Cloud SQL (PostgreSQL 15, db-f1-micro, ~$8/mo)
- Cloud Run (backend + frontend, auto-scales to 0, ~$5-15/mo)
- Cloud Storage (PDFs + product images)
- Cloud Build (CI/CD from GitHub)
- Custom domain

**Estimated MVP hosting: $20-40/month**

### Phase F: SaaS Features (Week 5-6)

- Stripe billing (Free trial → Paid)
- Onboarding wizard (logo, color, import products)
- Role-based access (admin / sales / viewer)
- Data migration tool (Google Sheets/Excel import)

---

## What Gets Dropped (MVP)

- Google Sheets as document output (replaced by native PDF)
- Google Slides export
- Gamma outline export
- Web scraping enrichment
- Master catalog update pipeline

These can be re-added as premium features later.

---

## What Gets Reused

| Current file | Reused as | Changes |
|---|---|---|
| `tools/discount_engine.py` | `services/discount_engine.py` | Replace Sheets reads with DB queries |
| `tools/generate_offer.py` (logic) | `services/offer_generator.py` | Numbering, line calculations, grouping |
| `tools/generate_order.py` (logic) | `services/order_generator.py` | Numbering, line calculations |
| `tools/import_logistics.py` (parsing) | `api/logistics.py` | Same openpyxl parsing, write to DB |
| `i18n.py` (translations) | `frontend/src/i18n/` | Convert to JSON files |
