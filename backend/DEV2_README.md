# Dev 2 Scope Summary & Testing Guide

This document summarizes the changes, codebase enhancements, and testing procedures for the **Quotation** and **Approval Workflow** modules, completed under the **Dev 2** scope.

---

## 🛠️ Changes Implemented (Dev 2 Scope)

### 1. Quotation Module
- **Repository** (`app/repositories/quotation_repo.py`):
  - Added eager-loading filters for quotation items.
  - Implemented revision tracking to allow multiple quotes per vendor-RFQ with sequential revision indexing.
  - Developed atomic selector logic (`mark_selected`) to pick the winning quotation and bulk-reject competitor quotes under a single transaction.
- **Serialization Schemas** (`app/schemas/quotation_schema.py`):
  - Created validation schemas for creating, updating, comparing, and returning quotations and items.
- **Service Layer** (`app/services/quotation_service.py`):
  - Enforced business validations (verifying RFQ availability, check vendor invitation/assignment).
  - Programmed automated totals calculation logic supporting CGST/SGST/IGST tax splits (intra-state vs. inter-state GST rules).
- **HTTP Routing** (`app/routes/quotation_routes.py`):
  - Implemented endpoints for quotation creation, updating, retrieval, comparison, and selection, gated with role authorization.

### 2. Approval Module
- **Repository** (`app/repositories/approval_repo.py`):
  - Implemented sequential dashboard queries to filter workflow steps and pull pending items awaiting action from the logged-in approver/manager.
- **Serialization Schemas** (`app/schemas/approval_schema.py`):
  - Created validation schemas for initiating approval pipelines and processing steps.
- **Service Layer** (`app/services/approval_service.py`):
  - Enforced approval sequences. Approving the final step transitions the workflow status to `approved`, notifies the vendor, and triggers Purchase Order creation.
- **HTTP Routing** (`app/routes/approval_routes.py`):
  - Wired routes to initiate workflows, log approval action inputs, cancel workflows, and return pending queues.

### 3. Supporting Enhancements
- **Sequential Reference Numbers** (`app/utils/number_generator.py`): Implemented thread-safe, prefix-sequential generators for Quote Numbers (e.g., `QUO-2026-0001`).
- **Activity & Auditing** (`app/services/notification_service.py`): Implemented central auditing routines to write user operations to an immutable append-only `activity_logs` table.
- **Registration Helper** (`app/services/auth_service.py`): Configured user registration so that registering with the `vendor` role automatically creates a linked profile in the `vendors` table for seamless testing.
- **Developer Seeder** (`seed_dev_data.py`): Provided a seeding utility to wipe and populate database tables with active dummy entities (open RFQ, invited vendor, manager) and output auth tokens directly to the terminal.

---

## 🚦 Verification & Testing

To test only these features, launch the server:
```cmd
python run.py
```
Run the seeder to get pre-authenticated JWT tokens and UUIDs:
```cmd
python seed_dev_data.py
```

Use the output values to test your changes in Postman:
1. **Create Draft** (`POST /api/v1/quotations/`): Submit a bid for the seeded RFQ using the Vendor token.
2. **Submit Draft** (`POST /api/v1/quotations/<id>/submit`): Finalize the quote using the Vendor token.
3. **Select Winner** (`POST /api/v1/quotations/<id>/select`): Mark the quote as selected using the Procurement Officer token.
4. **Initiate Approval** (`POST /api/v1/approvals/`): Start the workflow using the Procurement Officer token, assigning it to the seeded Manager's User ID.
5. **Manager Actions** (`GET /api/v1/approvals/pending` and `POST /api/v1/approvals/<id>/action`): Fetch pending workflow items and approve them using the Manager token.
