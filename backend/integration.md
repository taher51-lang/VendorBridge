## 🔗 Integration Requirements

### Dependency on Dev 2

Dev 3 modules depend on the Quotation and Approval modules.

Requirements:

* Quotation must exist
* Quotation must have status = "selected"
* Vendor must be linked to the selected quotation
* Financial totals must already be calculated by Dev 2

Before creating a Purchase Order:

```python
quotation.status == "selected"
```

Purchase Orders cannot be created from:

```text
draft
submitted
rejected
```

---

### Integration with Dev 4 (React Frontend)

The React frontend will consume all Dev 3 APIs.

Requirements:

* Consistent JSON responses
* Proper HTTP status codes
* JWT protected routes
* Pagination support
* Validation error responses

Response format:

```json
{
  "success": true,
  "message": "Success",
  "data": {}
}
```

---

### Database Dependencies

Reads From:

```text
quotations
quotation_items
vendors
users
```

Creates:

```text
purchase_orders
purchase_order_items

invoices
invoice_items

invoice_emails
```

---

### PDF Integration

Generated PDFs must be downloadable by:

* Procurement Officer
* Manager
* Vendor
* Admin

Templates:

```text
invoice_template.html

po_template.html
```

---

### Email Integration

SMTP configuration required:

```env
MAIL_SERVER
MAIL_PORT
MAIL_USERNAME
MAIL_PASSWORD
```

Invoice emails must automatically attach the generated PDF.

---

### End-to-End Integration Flow

```text
Dev 2
Quotation Selected
        ↓

Dev 3
Create Purchase Order
        ↓
Generate PO PDF
        ↓
Create Invoice
        ↓
Generate Invoice PDF
        ↓
Send Email
        ↓
Mark Paid

        ↓

Dev 4
Display Data
Download PDFs
Trigger Email Actions
Track Status
```
