<p align="center">
  <img src="https://img.shields.io/badge/Flask-3.0.3-000000?style=for-the-badge&logo=flask" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react" />
  <img src="https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=for-the-badge&logo=postgresql" />
  <img src="https://img.shields.io/badge/TailwindCSS-3.x-06B6D4?style=for-the-badge&logo=tailwindcss" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
</p>

<h1 align="center">⬡ VendorBridge</h1>
<p align="center"><strong>Procurement & Vendor Management ERP</strong></p>
<p align="center">
  A full-stack ERP system that streamlines the entire procurement lifecycle — from RFQ creation to GST-compliant invoice generation with PDF export and email dispatch.
</p>

---

## ✨ Core Workflow

```
RFQ Created → Vendors Invited → Quotations Submitted →
Quotations Compared → Approval Workflow → PO Generated →
Invoice Created → PDF Generated → Email Sent → Payment Recorded
```

## 🎯 Key Features

| Module | Capabilities |
|--------|-------------|
| **RFQ Management** | Create multi-item RFQs, invite vendors, set deadlines, track responses |
| **Quotation Engine** | Vendor submission, side-by-side comparison, auto-recommendation |
| **Approval Workflows** | Multi-level approval chains with manager review and audit trail |
| **Purchase Orders** | Auto-generated from approved quotes, vendor acknowledgement, fulfillment tracking |
| **GST Invoicing** | CGST/SGST/IGST calculation, professional PDF generation, email dispatch |
| **Analytics** | Spend by category, vendor performance, monthly trends, activity logs |
| **Vendor Portal** | Self-service profile, quotation submission, PO tracking |
| **Notifications** | In-app notifications for every workflow state change |

## 👥 Role-Based Access

| Role | Dashboard | Capabilities |
|------|-----------|-------------|
| `admin` | System overview | User management, vendor approvals, full system visibility |
| `procurement_officer` | Procurement hub | Create RFQs, compare quotes, issue POs, generate invoices |
| `manager` | Approval center | Review/approve/reject workflows, approval rate analytics |
| `vendor` | Vendor portal | Submit quotations, acknowledge POs, track payments |

## 🏗️ Architecture

```
VendorBridge/
├── backend/                    # Flask REST API
│   ├── app/
│   │   ├── models/             # SQLAlchemy models (User, Vendor, RFQ, PO, Invoice...)
│   │   ├── repositories/       # Data access layer (BaseRepository pattern)
│   │   ├── services/           # Business logic layer
│   │   ├── routes/             # Blueprint endpoints (/api/v1/...)
│   │   ├── schemas/            # Marshmallow validation & serialization
│   │   ├── utils/              # Helpers (PDF gen, email, number gen, security)
│   │   └── exceptions/         # Custom error handlers
│   ├── seed_dev_data.py        # Dev data seeder with JWT tokens
│   └── run.py                  # Entry point
│
├── frontend/                   # React + Vite SPA
│   └── src/
│       ├── api/                # Axios API clients
│       ├── components/         # Sidebar, Layout, UI primitives
│       ├── pages/              # Landing, Login, Dashboard(×4), RFQs, POs, Invoices...
│       │   └── dashboard/      # Role-specific dashboards
│       └── store/              # Zustand auth store
```

### Design Principles

- **Repository Pattern** — All DB access through `BaseRepository` subclasses
- **Service Layer** — Business logic isolated from routes; services raise `ValueError` / `PermissionError`
- **SessionLocal** — Pure SQLAlchemy `Session` (no Flask-SQLAlchemy `db.session`)
- **UUID Primary Keys** — All entities use UUID strings
- **Decimal Precision** — All monetary values use Python `Decimal`
- **Soft Deletes** — `deleted_at` column on all core models

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL (or Neon cloud DB)

### Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL, JWT_SECRET_KEY, MAIL_* settings

# Seed development data
python seed_dev_data.py

# Start the server
python run.py
# → Running on http://127.0.0.1:5000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
# → Running on http://localhost:5173
```

### 🔑 Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@vendorbridge.com` | `Admin@123` |
| Procurement Officer | `officer@vendorbridge.com` | `Officer@123` |
| Manager | `manager@vendorbridge.com` | `Manager@123` |
| Vendor | `vendor@vendorbridge.com` | `Vendor@123` |

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| Flask 3.0 | Web framework |
| SQLAlchemy 2.0 | ORM with `SessionLocal` pattern |
| Marshmallow | Request validation & serialization |
| Flask-JWT-Extended | Authentication & role-based access |
| Flask-Mail | Email dispatch |
| WeasyPrint | PDF invoice generation |
| PostgreSQL | Primary database (Neon compatible) |

### Frontend
| Technology | Purpose |
|-----------|---------|
| React 18 | UI framework |
| Vite | Build tool & dev server |
| TailwindCSS | Utility-first styling |
| React Router v6 | Client-side routing |
| TanStack React Query | Server state management |
| Zustand | Client auth state |
| Lucide React | Icon library |
| React Hook Form | Form handling |

## 📡 API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/register` | Register |
| POST | `/api/v1/auth/refresh` | Refresh token |

### RFQs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/rfqs/` | List RFQs |
| POST | `/api/v1/rfqs/` | Create RFQ |
| GET | `/api/v1/rfqs/:id` | Get RFQ detail |

### Quotations
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/quotations/` | Submit quotation |
| GET | `/api/v1/quotations/compare/:rfq_id` | Compare quotes |

### Purchase Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/purchase-orders/` | Create PO |
| POST | `/api/v1/purchase-orders/:id/acknowledge` | Vendor acknowledge |
| POST | `/api/v1/purchase-orders/:id/fulfill` | Mark fulfilled |
| POST | `/api/v1/purchase-orders/:id/cancel` | Cancel PO |

### Invoices
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/invoices/` | Create invoice |
| POST | `/api/v1/invoices/:id/pdf` | Generate PDF |
| POST | `/api/v1/invoices/:id/send` | Email invoice |
| POST | `/api/v1/invoices/:id/mark-paid` | Record payment |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/dashboard` | Role-based dashboard stats |
| GET | `/api/v1/analytics/activity-logs` | Audit trail |
| GET | `/api/v1/analytics/spend-by-category` | Category spend |
| GET | `/api/v1/analytics/vendor-performance` | Vendor metrics |
| GET | `/api/v1/analytics/monthly-trends` | Monthly procurement trends |

## 📄 License

MIT © VendorBridge
