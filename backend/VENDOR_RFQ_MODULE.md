# Vendor & RFQ Module — PR Description

**Branch:** `vendor-and-rfq-module`
**Author:** Dev 1
**Date:** 2026-06-06
**Base Branch:** `main`

---

## What Was Built

This PR implements the complete **Vendor Module** and **RFQ (Request for Quotation) Module**
for the VendorBridge ERP backend, along with all shared infrastructure those modules depend on.

---

## Files Changed

### New Implementations (previously all `pass` stubs)

| File | What Was Implemented |
|---|---|
| `app/exceptions/handlers.py` | All 6 custom exception classes + Flask global error handlers |
| `app/utils/number_generator.py` | Sequential RFQ/PO/Quote/Invoice number generation |
| `app/services/notification_service.py` | In-app notifications, audit logging, RFQ invite notifications |
| `app/schemas/vendor_schema.py` | Marshmallow schemas with GST + PAN regex validators |
| `app/schemas/rfq_schema.py` | RFQ schemas with future-deadline validator |
| `app/repositories/vendor_repo.py` | Vendor, Category, Rating DB queries |
| `app/repositories/rfq_repo.py` | RFQ, RFQItem, VendorAssignment DB queries |
| `app/services/vendor_service.py` | All vendor business logic |
| `app/services/rfq_service.py` | All RFQ business logic + state machine |
| `app/routes/vendor_routes.py` | 13 vendor API endpoints |
| `app/routes/rfq_routes.py` | 8 RFQ API endpoints |

### Other Changes
| File | Change |
|---|---|
| `backend/.gitignore` | Added `__pycache__/`, `*.pyc`, `.DS_Store`, etc. |

---

## API Endpoints Added

### Vendor Endpoints
```
POST   /api/v1/vendors/                    Register new vendor
GET    /api/v1/vendors/                    List vendors (search, filter, paginate)
GET    /api/v1/vendors/<id>                Get single vendor
PUT    /api/v1/vendors/<id>                Update vendor profile
DELETE /api/v1/vendors/<id>                Soft delete vendor
PATCH  /api/v1/vendors/<id>/status         Change vendor status
POST   /api/v1/vendors/<id>/approve        Approve pending vendor
POST   /api/v1/vendors/<id>/suspend        Suspend active vendor
POST   /api/v1/vendors/<id>/blacklist      Blacklist vendor permanently
GET    /api/v1/vendors/<id>/ratings        List vendor ratings
POST   /api/v1/vendors/<id>/ratings        Submit vendor rating
GET    /api/v1/vendors/categories          List all categories (hierarchical)
POST   /api/v1/vendors/categories          Create a category
```

### RFQ Endpoints
```
POST   /api/v1/rfqs/                       Create RFQ with line items
GET    /api/v1/rfqs/                       List RFQs (role-aware)
GET    /api/v1/rfqs/<id>                   Get RFQ with items + vendor assignments
PUT    /api/v1/rfqs/<id>                   Update draft RFQ
POST   /api/v1/rfqs/<id>/publish           Publish RFQ (draft → open)
POST   /api/v1/rfqs/<id>/close             Close RFQ (open → closed)
POST   /api/v1/rfqs/<id>/cancel            Cancel RFQ
POST   /api/v1/rfqs/<id>/invite-vendors    Invite additional vendors
```

---

## State Machines Implemented

### Vendor Status
```
pending ──→ active ──→ suspended ──→ active (reactivate)
   │            │           │
   └────────────┴───────────┴──→ blacklisted (terminal, also deactivates user)
```

### RFQ Status
```
draft ──→ open ──→ closed   (terminal)
  │         │
  └─────────┴──→ cancelled  (terminal)
```

> Invalid transitions return `400 Bad Request` with a descriptive message.

---

## ⚠️ Schema Adaptations — IMPORTANT FOR MERGE

The original requirements described a simpler schema. The actual DB models
(set up by the team lead) are richer. These adaptations were made:

### 1. Vendor Registration Creates a User Account
**Requirement:** `POST /vendors/` accepts `name`, `email`, `phone`

**Reality:** `email` and `phone` live on the `User` model, not `Vendor`. The
`Vendor` model has a `user_id` FK to `users`.

**What the code does:** `POST /vendors/` now creates:
- A `User` record with `role='vendor'`
- A linked `Vendor` profile

**What the caller must send:**
```json
{
  "name": "Company Name",
  "email": "vendor@email.com",
  "phone": "9876543210",
  "password": "optional_password"   ← defaults to "Vendor@123!" if not sent
}
```

---

### 2. `name` Field Maps to `company_name`
**Requirement:** `vendors.name`

**Reality:** Column is `vendors.company_name`

**Adaptation:** API accepts `name` → stored internally as `company_name`.
No column was renamed in the DB.

---

### 3. Vendor Status Enum — No `inactive`
**Requirement:** `active`, `inactive`, `blacklisted`

**Reality (DB enum):** `pending`, `active`, `suspended`, `blacklisted`

**Adaptation:** `inactive` is represented as `suspended` in this system.
The `PATCH /status` endpoint accepts: `active`, `suspended`, `blacklisted`, `pending`.

---

### 4. Soft Delete Uses `deleted_at`, Not `is_deleted`
**Requirement:** `is_deleted = True`

**Reality:** `BaseModel` uses `deleted_at` (DateTime, nullable) for soft delete.
A non-null `deleted_at` means the record is deleted.

**No change needed** — functionally identical, just a different column name.

---

### 5. Notification Fields — `title` + `body`, Not `message`
**Requirement:** `notifications.message`

**Reality:** `Notification` model has `title` (String) + `body` (Text)

**Adaptation:** Notifications are created with both `title` and `body` set.

---

### 6. `rfq_vendors` Is a Richer Junction Table
**Requirement:** Simple `rfq_vendors` with just `rfq_id` + `vendor_id`

**Reality:** `rfq_vendor_assignments` table with extra columns:
`invited_at`, `viewed_at`, `status` (invited/acknowledged/declined)

**Benefit:** Tracks when vendors viewed the RFQ and their response status.

---

## Role Permissions Summary

| Action | Required Role |
|---|---|
| Register vendor | `admin` |
| List / Get vendors | Any authenticated user |
| Update vendor | Vendor (own profile) or `admin` / `manager` |
| Delete / Approve / Suspend / Blacklist vendor | `admin` only |
| Change vendor status | `admin` only |
| Create / Update / Publish / Close / Cancel RFQ | `procurement_officer`, `admin`, `manager` |
| List RFQs | Any authenticated user (vendors see only assigned RFQs) |
| Rate a vendor | `procurement_officer`, `manager`, `admin` |
| Create vendor category | `admin` only |

---

## Notification Behaviour

When `POST /rfqs/<id>/publish` is called:
1. RFQ status changes `draft → open`
2. All assigned vendor IDs are fetched
3. For each vendor → their linked `user_id` is looked up
4. A `Notification` row is inserted for each vendor user
5. Notification type: `rfq_invite`

> This is **non-fatal** — if one vendor lookup fails, the rest still get notified
> and the publish still succeeds.

---

## No Database Migrations Needed

All tables and columns used by this PR were already created by the team lead's
initial migration. No new columns or tables were added.

**Tables used:**
- `users` — existing
- `vendors` — existing
- `vendor_categories` — existing
- `vendor_ratings` — existing
- `rfqs` — existing
- `rfq_items` — existing
- `rfq_vendor_assignments` — existing
- `notifications` — existing
- `activity_logs` — existing

---

## Testing Done

All endpoints tested manually via Postman:

- [x] `POST /auth/register` + `POST /auth/login` → JWT token received
- [x] `POST /vendors/` → vendor + user created, status `pending`
- [x] `GET /vendors/` → paginated list returned with meta
- [x] `POST /vendors/<id>/approve` → status changed to `active`
- [x] `DELETE /vendors/<id>` → 403 when non-admin, 200 when admin
- [x] Invalid state transition → 400 with descriptive message
- [x] Missing JWT → 401 Unauthorized
- [x] Wrong role → 403 Forbidden with message
- [x] Python syntax check → all 11 files pass `py_compile`

---

## How to Test Locally

```bash
# 1. Start the server
cd backend
python run.py

# 2. Register admin
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"password123","role":"admin","full_name":"Admin"}'

# 3. Login → copy access_token
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"password123"}'

# 4. Register vendor (use token from step 3)
curl -X POST http://localhost:5000/api/v1/vendors/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"ABC Supplies","email":"abc@vendor.com","phone":"9876543210","gst_number":"22AAAAA0000A1Z5"}'

# 5. Register officer and login
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"officer@test.com","password":"password123","role":"procurement_officer"}'

# 6. Create RFQ (use officer token)
curl -X POST http://localhost:5000/api/v1/rfqs/ \
  -H "Authorization: Bearer <officer_token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Laptop Chargers","description":"Need 500 units","deadline":"2027-12-31T00:00:00","vendor_ids":["<vendor_id>"],"items":[{"item_name":"Charger 65W","quantity":500,"unit":"pcs"}]}'

# 7. Publish RFQ
curl -X POST http://localhost:5000/api/v1/rfqs/<rfq_id>/publish \
  -H "Authorization: Bearer <officer_token>"
```

---

## Checklist Before Merge

- [x] All endpoints return `{"success": true/false, "message": "...", "data": {...}}`
- [x] Invalid state transitions return `400` with descriptive message
- [x] JWT required on all routes — missing token returns `401`
- [x] Role guards enforced on all mutating endpoints — wrong role returns `403`
- [x] No hard deletes anywhere — all deletes use `deleted_at` timestamp
- [x] RFQ publish fires notifications to all assigned vendor users
- [x] All activity is logged to `activity_logs` table
- [x] Paginated list responses include `meta` (page, total, has_next, has_prev)
- [x] GST number validated with regex before saving
- [x] Deadline validated to be a future date before creating/publishing RFQ
- [x] Python syntax check passed on all 11 modified files
- [x] No model files were modified — no migrations required
- [x] Branch: `vendor-and-rfq-module` — ready to PR against `main`

---

## Known Limitations / Future Improvements

1. **Email notifications not sent** — `NotificationService` creates DB notification rows
   but email sending via Flask-Mail is not wired up (SMTP not configured).
   In-app notifications work fully.

2. **Number generator is not thread-safe** under extreme concurrent load —
   uses MAX query. For high traffic, replace with a PostgreSQL sequence.

3. **Vendor registration password** — defaults to `Vendor@123!` if not provided.
   In production, send a "set your password" email to the vendor instead.

4. **Category lookup by name** — if you pass `"category": "IT"` but the "IT"
   category doesn't exist in DB yet, `category_id` will be `null`.
   Create categories first via `POST /api/v1/vendors/categories`.
