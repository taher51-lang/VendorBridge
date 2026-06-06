# VendorBridge ERP — Dev 3 Integration Guide

> **Module Scope:** Purchase Order (PO) · Invoice · PDF Generation · Email Dispatch  
> **Backend:** Python Flask · SQLAlchemy · Marshmallow  
> **Base URL:** `http://localhost:5000/api/v1`

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Authentication](#2-authentication)
3. [Standard Response Format](#3-standard-response-format)
4. [Purchase Order APIs](#4-purchase-order-apis)
5. [Invoice APIs](#5-invoice-apis)
6. [PDF Generation & Download](#6-pdf-generation--download)
7. [Email Dispatch](#7-email-dispatch)
8. [React + Axios Integration Guide](#8-react--axios-integration-guide)
9. [Role-Based Access Control](#9-role-based-access-control)
10. [Environment Variables](#10-environment-variables)
11. [Error Reference](#11-error-reference)
12. [Full Workflow Walkthrough](#12-full-workflow-walkthrough)

---

## 1. Quick Start

### Backend Setup

```bash
# 1. Navigate to backend directory
cd VendorBridge/backend

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment (copy and fill in .env)
cp .env.example .env

# 5. Start the server
python run.py
# → Server runs at http://localhost:5000
# → "✔ Tables verified / created successfully" confirms DB is connected
```

### Frontend (React) Setup

```bash
cd VendorBridge/frontend
npm install
npm run dev
# → Runs at http://localhost:3000
```

---

## 2. Authentication

All Dev 3 endpoints require a **JWT Bearer Token** in the Authorization header.

### Login to Get Token

```
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "officer@company.com",
  "password": "yourpassword"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "user": { "id": "...", "role": "procurement_officer" }
  }
}
```

### Using the Token in Every Request

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json
```

### Setting Up Axios in React

Create `src/api/axiosConfig.js`:

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api/v1',
  headers: { 'Content-Type': 'application/json' }
});

// Attach JWT token automatically to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 globally (token expired)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## 3. Standard Response Format

All API responses follow a consistent format that the React frontend should handle uniformly.

### Success Response

```json
{
  "success": true,
  "message": "Purchase Order created successfully",
  "data": { ... }
}
```

### Success Response with HTTP 201 (Created)

```json
{
  "success": true,
  "message": "Invoice created successfully",
  "data": { "id": "...", "invoice_number": "INV-2026-0001", ... }
}
```

### Paginated Response

```json
{
  "success": true,
  "message": "Purchase Orders retrieved",
  "data": [ { ... }, { ... } ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

### Error Response

```json
{
  "success": false,
  "message": "Quotation must be in 'selected' status to create a PO.",
  "errors": {}
}
```

### Validation Error (HTTP 422)

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "recipient_email": ["Not a valid email address."],
    "due_date": ["due_date must be on or after invoice_date."]
  }
}
```

### React Axios Response Handler Pattern

```javascript
// Reusable handler for all API calls
const handleApiCall = async (apiFunction) => {
  try {
    const response = await apiFunction();
    return { data: response.data.data, meta: response.data.meta, error: null };
  } catch (error) {
    const message = error.response?.data?.message || 'Something went wrong';
    const errors  = error.response?.data?.errors  || {};
    return { data: null, meta: null, error: message, fieldErrors: errors };
  }
};
```

---

## 4. Purchase Order APIs

### 4.1 Create Purchase Order

```
POST /api/v1/purchase-orders/
```

**Roles:** `procurement_officer`, `admin`

**Request Body:**
```json
{
  "quotation_id": "uuid-of-selected-quotation",
  "delivery_address": "123 Main St, Mumbai - 400001",
  "expected_delivery": "2026-07-15",
  "terms_conditions": "Payment within 30 days of invoice."
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `quotation_id` | UUID string | ✅ Yes | Must be a quotation with status `selected` |
| `delivery_address` | string | No | Delivery location text |
| `expected_delivery` | date (YYYY-MM-DD) | No | Expected delivery date |
| `terms_conditions` | string | No | Custom T&C text |

**Response (201):**
```json
{
  "success": true,
  "message": "Purchase Order created successfully",
  "data": {
    "id": "po-uuid",
    "po_number": "PO-2026-0001",
    "quotation_id": "...",
    "vendor_id": "...",
    "status": "issued",
    "subtotal": "45000.00",
    "tax_amount": "8100.00",
    "total_amount": "53100.00",
    "currency": "INR",
    "issued_at": "2026-06-06T08:00:00",
    "items": [
      {
        "id": "...",
        "item_name": "Office Chairs",
        "quantity": "10.000",
        "unit_price": "4500.0000",
        "tax_rate": "18.00",
        "line_total": "45000.00"
      }
    ],
    "created_at": "2026-06-06T08:00:00",
    "updated_at": "2026-06-06T08:00:00"
  }
}
```

**React Usage:**
```javascript
const createPO = async (quotationId, formData) => {
  const { data, error } = await handleApiCall(() =>
    api.post('/purchase-orders/', {
      quotation_id: quotationId,
      delivery_address: formData.deliveryAddress,
      expected_delivery: formData.expectedDelivery,
      terms_conditions: formData.termsConditions
    })
  );
  if (error) toast.error(error);
  else navigate(`/purchase-orders/${data.id}`);
};
```

---

### 4.2 List Purchase Orders

```
GET /api/v1/purchase-orders/?page=1&per_page=20&status=issued
```

**Roles:** `procurement_officer`, `manager`, `admin`

**Query Parameters:**

| Param | Type | Description |
|---|---|---|
| `page` | integer | Page number (default: 1) |
| `per_page` | integer | Items per page (default: 20) |
| `status` | string | Filter by: `issued`, `acknowledged`, `fulfilled`, `cancelled` |

**Response:** Paginated list of PO objects.

**React Usage:**
```javascript
const fetchPOs = async (page = 1, status = '') => {
  const params = new URLSearchParams({ page, per_page: 20 });
  if (status) params.append('status', status);

  const { data, meta, error } = await handleApiCall(() =>
    api.get(`/purchase-orders/?${params}`)
  );
  return { pos: data, pagination: meta };
};
```

---

### 4.3 Get Single Purchase Order

```
GET /api/v1/purchase-orders/:po_id
```

**Roles:** `procurement_officer`, `manager`, `admin`, `vendor`

**Response:** Single PO object with full `items` array.

---

### 4.4 Update Purchase Order

```
PUT /api/v1/purchase-orders/:po_id
```

**Roles:** `procurement_officer`, `admin`  
**Condition:** PO must have status `issued`

**Request Body (all optional):**
```json
{
  "delivery_address": "456 New Address, Delhi",
  "expected_delivery": "2026-08-01",
  "terms_conditions": "Updated payment terms."
}
```

---

### 4.5 Acknowledge Purchase Order (Vendor Action)

```
POST /api/v1/purchase-orders/:po_id/acknowledge
```

**Roles:** `vendor` only  
**Condition:** PO must have status `issued`  
**Effect:** Status changes `issued` → `acknowledged`

**No request body needed.**

**React Usage (vendor portal):**
```javascript
const acknowledgePO = async (poId) => {
  const { data, error } = await handleApiCall(() =>
    api.post(`/purchase-orders/${poId}/acknowledge`)
  );
  if (error) toast.error(error);
  else toast.success('PO Acknowledged successfully');
};
```

---

### 4.6 Fulfill Purchase Order

```
POST /api/v1/purchase-orders/:po_id/fulfill
```

**Roles:** `procurement_officer`, `admin`  
**Condition:** PO must have status `acknowledged`  
**Effect:** Status changes `acknowledged` → `fulfilled`

> **Note:** Fulfillment is optional before creating an invoice (Option A hackathon flow).

---

### 4.7 Cancel Purchase Order

```
POST /api/v1/purchase-orders/:po_id/cancel
```

**Roles:** `procurement_officer`, `admin`  
**Condition:** Status must be `issued` or `acknowledged`

**Request Body (optional):**
```json
{
  "reason": "Vendor failed to confirm within deadline."
}
```

---

### 4.8 Generate PO PDF

```
POST /api/v1/purchase-orders/:po_id/pdf
```

**Roles:** `procurement_officer`, `admin`

**Response:**
```json
{
  "success": true,
  "message": "PO PDF generated successfully",
  "data": { "pdf_url": "/absolute/path/to/PO-2026-0001.pdf" }
}
```

---

### 4.9 Download PO PDF (Binary)

```
GET /api/v1/purchase-orders/:po_id/pdf/download
```

**Roles:** `procurement_officer`, `manager`, `admin`, `vendor`  
**Response:** Binary PDF file (`application/pdf`)

**React Usage:**
```javascript
const downloadPOPdf = async (poId, poNumber) => {
  const response = await api.get(`/purchase-orders/${poId}/pdf/download`, {
    responseType: 'blob'  // Important: must be blob for binary files
  });
  const url  = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href  = url;
  link.setAttribute('download', `${poNumber}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};
```

---

## 5. Invoice APIs

### 5.1 Create Invoice

```
POST /api/v1/invoices/
```

**Roles:** `procurement_officer`, `admin`  
**Condition:** Referenced PO must have status `issued` or `acknowledged`

**Request Body:**
```json
{
  "po_id": "uuid-of-purchase-order",
  "invoice_date": "2026-06-06",
  "due_date": "2026-07-06",
  "is_interstate": false,
  "notes": "Please make payment via NEFT.",
  "items": [
    {
      "item_name": "Office Chairs",
      "quantity": "10",
      "unit_price": "4500.00",
      "tax_rate": "18.00",
      "hsn_code": "9401",
      "quotation_item_id": null
    }
  ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `po_id` | UUID string | ✅ Yes | Must be an issued/acknowledged PO |
| `invoice_date` | date (YYYY-MM-DD) | ✅ Yes | Invoice issue date |
| `due_date` | date (YYYY-MM-DD) | No | Must be ≥ invoice_date |
| `is_interstate` | boolean | ✅ Yes | `true` = IGST only, `false` = CGST + SGST |
| `notes` | string | No | Payment notes/instructions |
| `items` | array | ✅ Yes | Min 1 item required |
| `items[].item_name` | string | ✅ Yes | |
| `items[].quantity` | decimal string | ✅ Yes | |
| `items[].unit_price` | decimal string | ✅ Yes | |
| `items[].tax_rate` | decimal string | ✅ Yes | Percentage (e.g. `"18.00"`) |
| `items[].hsn_code` | string | No | GST HSN/SAC code |

**GST Calculation Logic:**
- `line_total = quantity × unit_price`
- `tax_amount = sum(line_total × tax_rate / 100)` per item
- If `is_interstate = false`: `cgst = tax/2`, `sgst = tax/2`, `igst = 0`
- If `is_interstate = true`: `igst = tax`, `cgst = 0`, `sgst = 0`
- `total_amount = subtotal + cgst + sgst + igst`

**Response (201):**
```json
{
  "success": true,
  "message": "Invoice created successfully",
  "data": {
    "id": "invoice-uuid",
    "invoice_number": "INV-2026-0001",
    "po_id": "...",
    "vendor_id": "...",
    "status": "draft",
    "invoice_date": "2026-06-06",
    "due_date": "2026-07-06",
    "subtotal": "45000.00",
    "cgst_amount": "4050.00",
    "sgst_amount": "4050.00",
    "igst_amount": "0.00",
    "total_amount": "53100.00",
    "pdf_url": null,
    "notes": "Please make payment via NEFT.",
    "items": [ { ... } ],
    "emails": [],
    "created_at": "2026-06-06T08:00:00"
  }
}
```

---

### 5.2 List Invoices

```
GET /api/v1/invoices/?page=1&per_page=20&status=draft&vendor_id=uuid
```

**Roles:** `procurement_officer`, `manager`, `admin`

**Query Parameters:**

| Param | Type | Description |
|---|---|---|
| `page` | integer | Page number |
| `per_page` | integer | Items per page |
| `status` | string | Filter: `draft`, `sent`, `paid`, `overdue`, `cancelled` |
| `vendor_id` | UUID string | Filter by vendor |

---

### 5.3 Get Single Invoice

```
GET /api/v1/invoices/:invoice_id
```

**Roles:** `procurement_officer`, `manager`, `admin`, `vendor`  
**Response:** Full invoice with `items[]` and `emails[]` (email history).

---

### 5.4 Update Invoice

```
PUT /api/v1/invoices/:invoice_id
```

**Roles:** `procurement_officer`, `admin`  
**Condition:** Invoice must have status `draft`

**Request Body (all optional):**
```json
{
  "due_date": "2026-08-01",
  "notes": "Updated payment instructions."
}
```

---

### 5.5 Mark Invoice as Paid

```
POST /api/v1/invoices/:invoice_id/mark-paid
```

**Roles:** `procurement_officer`, `manager`, `admin`  
**Condition:** Invoice must have status `sent` or `overdue`  
**Effect:** Status → `paid`, `paid_at` timestamp recorded

**No request body needed.**

**React Usage:**
```javascript
const markInvoicePaid = async (invoiceId) => {
  const { data, error } = await handleApiCall(() =>
    api.post(`/invoices/${invoiceId}/mark-paid`)
  );
  if (error) toast.error(error);
  else toast.success(`Invoice marked as paid on ${data.paid_at}`);
};
```

---

### 5.6 Flag Overdue Invoices (Admin Batch Job)

```
POST /api/v1/invoices/flag-overdue
```

**Roles:** `admin` only  
**Effect:** All invoices with `due_date < today` and status not `paid/cancelled` → `overdue`

**Response:**
```json
{
  "success": true,
  "message": "3 invoice(s) flagged as overdue",
  "data": { "updated_count": 3 }
}
```

> Call this endpoint from a daily scheduler or admin dashboard button.

---

## 6. PDF Generation & Download

### Workflow

```
Step 1: POST /invoices/:id/pdf       → Generates PDF on server, returns file path
Step 2: GET  /invoices/:id/pdf/download → Downloads the binary PDF to browser
```

Auto-generation: The download endpoint will auto-generate the PDF if it doesn't exist yet.

### Invoice PDF Endpoint

```
POST /api/v1/invoices/:invoice_id/pdf
GET  /api/v1/invoices/:invoice_id/pdf/download
```

### PO PDF Endpoint

```
POST /api/v1/purchase-orders/:po_id/pdf
GET  /api/v1/purchase-orders/:po_id/pdf/download
```

### React PDF Download Button

```jsx
import api from '../api/axiosConfig';

const PdfDownloadButton = ({ invoiceId, invoiceNumber }) => {
  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/invoices/${invoiceId}/pdf/download`, {
        responseType: 'blob'   // ← Critical: binary response
      });

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url  = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href  = url;
      link.setAttribute('download', `${invoiceNumber}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      toast.error('Failed to download PDF');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button onClick={handleDownload} disabled={loading}>
      {loading ? 'Generating...' : '⬇ Download PDF'}
    </button>
  );
};
```

### PDF Template Variables

**Invoice Template (`invoice_template.html`)** receives:

| Variable | Type | Description |
|---|---|---|
| `invoice_number` | string | e.g. `INV-2026-0001` |
| `invoice_date` | date | Issue date |
| `due_date` | date | Payment due date |
| `status` | string | Current status |
| `vendor_name` | string | Vendor company name |
| `vendor_gst` | string | Vendor GST number |
| `vendor_address` | string | Vendor address |
| `subtotal` | Decimal | Before tax |
| `cgst_amount` | Decimal | Intra-state tax |
| `sgst_amount` | Decimal | Intra-state tax |
| `igst_amount` | Decimal | Inter-state tax |
| `total_amount` | Decimal | Grand total |
| `notes` | string | Payment notes |
| `items[]` | list | Line items with item_name, qty, price, tax_rate, line_total, hsn_code |

**PO Template (`po_template.html`)** receives:

| Variable | Type | Description |
|---|---|---|
| `po_number` | string | e.g. `PO-2026-0001` |
| `issued_at` | date | Issue date |
| `expected_delivery` | date | Expected delivery |
| `status` | string | Current status |
| `currency` | string | e.g. `INR` |
| `delivery_address` | string | Delivery location |
| `terms_conditions` | string | T&C text |
| `vendor_name` | string | |
| `subtotal` | Decimal | |
| `tax_amount` | Decimal | |
| `total_amount` | Decimal | |
| `items[]` | list | Line items |

---

## 7. Email Dispatch

### Send Invoice via Email

```
POST /api/v1/invoices/:invoice_id/send
```

**Roles:** `procurement_officer`, `admin`

**Request Body:**
```json
{
  "recipient_email": "vendor@company.com",
  "subject": "Invoice INV-2026-0001 from VendorBridge"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `recipient_email` | email string | ✅ Yes | Valid email address |
| `subject` | string | No | Defaults to `"Invoice {number} from VendorBridge"` |

**What happens automatically:**
1. PDF generated if not already done
2. Email record created with status `queued`
3. Email sent via SMTP (Flask-Mail)
4. If sent → invoice status becomes `sent`, email record status → `sent`
5. If failed → email record status → `failed` (check SMTP config in `.env`)

**Response:**
```json
{
  "success": true,
  "message": "Invoice email dispatched successfully",
  "data": {
    "id": "email-record-uuid",
    "invoice_id": "...",
    "recipient_email": "vendor@company.com",
    "subject": "Invoice INV-2026-0001 from VendorBridge",
    "status": "sent",
    "sent_at": "2026-06-06T08:30:00",
    "error_message": null
  }
}
```

**React Usage:**
```jsx
const SendInvoiceModal = ({ invoiceId, invoiceNumber }) => {
  const [email, setEmail]     = useState('');
  const [subject, setSubject] = useState(`Invoice ${invoiceNumber} from VendorBridge`);
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    setSending(true);
    const { data, error } = await handleApiCall(() =>
      api.post(`/invoices/${invoiceId}/send`, {
        recipient_email: email,
        subject: subject
      })
    );
    setSending(false);
    if (error) toast.error(error);
    else if (data.status === 'sent') toast.success('Invoice emailed successfully!');
    else toast.warning('Email queued but delivery failed — check SMTP settings');
  };

  return (
    <form onSubmit={handleSend}>
      <input type="email" value={email} onChange={e => setEmail(e.target.value)}
             placeholder="Vendor email address" required />
      <input type="text"  value={subject} onChange={e => setSubject(e.target.value)} />
      <button type="submit" disabled={sending}>
        {sending ? 'Sending...' : '✉ Send Invoice'}
      </button>
    </form>
  );
};
```

---

## 8. React + Axios Integration Guide

### Recommended File Structure

```
src/
├── api/
│   ├── axiosConfig.js        ← Base Axios instance with JWT interceptor
│   ├── poApi.js              ← All PO API calls
│   └── invoiceApi.js         ← All Invoice API calls
├── pages/
│   ├── PurchaseOrders/
│   │   ├── POList.jsx
│   │   ├── PODetail.jsx
│   │   └── CreatePO.jsx
│   └── Invoices/
│       ├── InvoiceList.jsx
│       ├── InvoiceDetail.jsx
│       └── CreateInvoice.jsx
└── components/
    ├── PdfDownloadButton.jsx
    └── SendInvoiceModal.jsx
```

### `src/api/poApi.js`

```javascript
import api from './axiosConfig';

export const poApi = {
  create:      (data)         => api.post('/purchase-orders/', data),
  list:        (params)       => api.get('/purchase-orders/', { params }),
  getById:     (id)           => api.get(`/purchase-orders/${id}`),
  update:      (id, data)     => api.put(`/purchase-orders/${id}`, data),
  acknowledge: (id)           => api.post(`/purchase-orders/${id}/acknowledge`),
  fulfill:     (id)           => api.post(`/purchase-orders/${id}/fulfill`),
  cancel:      (id, reason)   => api.post(`/purchase-orders/${id}/cancel`, { reason }),
  generatePdf: (id)           => api.post(`/purchase-orders/${id}/pdf`),
  downloadPdf: (id)           => api.get(`/purchase-orders/${id}/pdf/download`, { responseType: 'blob' }),
};
```

### `src/api/invoiceApi.js`

```javascript
import api from './axiosConfig';

export const invoiceApi = {
  create:      (data)         => api.post('/invoices/', data),
  list:        (params)       => api.get('/invoices/', { params }),
  getById:     (id)           => api.get(`/invoices/${id}`),
  update:      (id, data)     => api.put(`/invoices/${id}`, data),
  generatePdf: (id)           => api.post(`/invoices/${id}/pdf`),
  downloadPdf: (id)           => api.get(`/invoices/${id}/pdf/download`, { responseType: 'blob' }),
  sendEmail:   (id, data)     => api.post(`/invoices/${id}/send`, data),
  markPaid:    (id)           => api.post(`/invoices/${id}/mark-paid`),
  flagOverdue: ()             => api.post('/invoices/flag-overdue'),
};
```

---

## 9. Role-Based Access Control

| Role | Can Do |
|---|---|
| `admin` | Everything |
| `procurement_officer` | Create PO, Create Invoice, Generate PDF, Send Email, Mark Paid, Cancel PO |
| `manager` | View POs, View Invoices, Download PDFs, Mark Paid |
| `vendor` | Acknowledge PO, View their own PO/Invoice, Download PDFs |

### Role in JWT Token

The role is stored in the JWT `additional_claims`:

```json
{ "sub": "user-uuid", "role": "procurement_officer" }
```

### Conditional UI Based on Role

```javascript
// Get role from decoded JWT or from login response
const userRole = JSON.parse(localStorage.getItem('user'))?.role;

// Show/hide buttons based on role
const canCreatePO     = ['procurement_officer', 'admin'].includes(userRole);
const canMarkPaid     = ['procurement_officer', 'manager', 'admin'].includes(userRole);
const canAcknowledge  = userRole === 'vendor';
```

---

## 10. Environment Variables

> File location: `VendorBridge/backend/.env`

```env
# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

# JWT
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600

# CORS — Allow React dev server
CORS_ORIGINS=http://localhost:3000

# Email (SMTP via Flask-Mail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password        # Gmail: use App Password not regular password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# PDF Storage
PDF_OUTPUT_DIR=generated_pdfs          # Folder where PDFs are saved
```

> **Gmail Note:** Generate an App Password at  
> Google Account → Security → 2-Step Verification → App Passwords

---

## 11. Error Reference

| HTTP Status | Meaning | Common Cause |
|---|---|---|
| `400` | Bad Request | Wrong status for action (e.g. PO already cancelled) |
| `401` | Unauthorized | Missing or expired JWT token |
| `403` | Forbidden | User's role is not allowed for this endpoint |
| `404` | Not Found | PO/Invoice UUID does not exist |
| `409` | Conflict | PO already exists for this quotation |
| `422` | Validation Error | Invalid fields in request body |
| `500` | Server Error | Backend crash — check Flask terminal logs |

### Handling Errors in React

```javascript
const { data, error, fieldErrors } = await handleApiCall(() =>
  api.post('/purchase-orders/', formData)
);

if (fieldErrors.quotation_id) {
  setFormError('quotation_id', fieldErrors.quotation_id[0]);
}
if (error) {
  toast.error(error); // e.g. "Quotation must be in 'selected' status"
}
```

---

## 12. Full Workflow Walkthrough

This is the end-to-end procurement flow that Dev 3's modules sit in:

```
[Dev 1] Register Vendor
         ↓
[Dev 1] Create RFQ → Assign Vendors
         ↓
[Dev 2] Vendor Submits Quotation
         ↓
[Dev 2] Officer Compares Quotations → Selects Best
         ↓ (quotation.status = "selected")
[Dev 2] Approval Workflow → Manager Approves
         ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Dev 3] POST /purchase-orders/          ← Create PO from selected quotation
         ↓ (po.status = "issued")
[Dev 3] POST /purchase-orders/:id/acknowledge   ← Vendor acknowledges
         ↓ (po.status = "acknowledged")
[Dev 3] POST /purchase-orders/:id/pdf           ← Generate PO PDF (optional)
         ↓
[Dev 3] POST /invoices/                  ← Create invoice (GST calculated)
         ↓ (invoice.status = "draft")
[Dev 3] POST /invoices/:id/pdf           ← Render invoice PDF
[Dev 3] POST /invoices/:id/send          ← Email invoice to vendor
         ↓ (invoice.status = "sent")
[Dev 3] POST /invoices/:id/mark-paid     ← Record payment
         ↓ (invoice.status = "paid")
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Dev 4] All 10 screens consume the above APIs
```

---

## API Summary Table

| Method | Endpoint | Roles | Description |
|---|---|---|---|
| POST | `/purchase-orders/` | officer, admin | Create PO from approved quotation |
| GET | `/purchase-orders/` | officer, manager, admin | List POs (paginated) |
| GET | `/purchase-orders/:id` | all roles | Get PO details |
| PUT | `/purchase-orders/:id` | officer, admin | Update delivery/terms |
| POST | `/purchase-orders/:id/acknowledge` | vendor | Vendor acknowledges PO |
| POST | `/purchase-orders/:id/fulfill` | officer, admin | Mark PO fulfilled |
| POST | `/purchase-orders/:id/cancel` | officer, admin | Cancel PO |
| POST | `/purchase-orders/:id/pdf` | officer, admin | Generate PO PDF |
| GET | `/purchase-orders/:id/pdf/download` | all roles | Download PO PDF |
| POST | `/invoices/` | officer, admin | Create invoice from PO |
| GET | `/invoices/` | officer, manager, admin | List invoices (paginated) |
| GET | `/invoices/:id` | all roles | Get invoice details |
| PUT | `/invoices/:id` | officer, admin | Update draft invoice |
| POST | `/invoices/:id/pdf` | officer, admin | Generate invoice PDF |
| GET | `/invoices/:id/pdf/download` | all roles | Download invoice PDF |
| POST | `/invoices/:id/send` | officer, admin | Email invoice to vendor |
| POST | `/invoices/:id/mark-paid` | officer, manager, admin | Mark invoice as paid |
| POST | `/invoices/flag-overdue` | admin | Batch flag overdue invoices |

---

*README maintained by Dev 3 — Last updated: June 2026*
