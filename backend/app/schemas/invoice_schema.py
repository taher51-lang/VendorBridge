"""
VendorBridge ERP – Invoice Schemas
====================================
Marshmallow schemas for Invoice, InvoiceItem, and InvoiceEmail.
"""

from marshmallow import Schema, fields, validate


class InvoiceItemSchema(Schema):
    """
    Validates / serializes an invoice line item.

    Fields to define:
        - id: Dump only
        - quotation_item_id: Optional, FK reference
        - item_name: Required, max 200
        - quantity: Required, positive Decimal
        - unit_price: Required, positive Decimal
        - tax_rate: Required, Decimal (0-100)
        - line_total: Dump only (calculated)
        - hsn_code: Optional, max 20
    """
    # TODO: Define fields
    pass


class InvoiceCreateSchema(Schema):
    """
    Validates the creation of a new invoice from a PO.

    Fields to define:
        - po_id: Required, UUID of the fulfilled PO
        - invoice_date: Required, Date
        - due_date: Optional, Date (must be >= invoice_date)
        - is_interstate: Required, Boolean (for GST split)
        - notes: Optional
        - items: Required, Nested list of InvoiceItemSchema (min 1)
    """
    # TODO: Define fields
    # TODO: Add @validates_schema to ensure due_date >= invoice_date
    pass


class InvoiceUpdateSchema(Schema):
    """
    Validates invoice edits (only while status=draft).

    Fields to define:
        - due_date: Optional
        - notes: Optional
        - status: Optional, one of 'sent' / 'paid' / 'cancelled'
    """
    # TODO: Define partial fields
    pass


class InvoiceResponseSchema(Schema):
    """
    Serializes an Invoice for API output.

    Fields to define:
        - id, invoice_number, po_id, vendor_id, generated_by
        - invoice_date, due_date
        - subtotal, cgst_amount, sgst_amount, igst_amount, total_amount
        - pdf_url, status, paid_at, notes
        - items: Nested list of InvoiceItemSchema
        - emails: Nested list of InvoiceEmailSchema
        - created_at, updated_at
    """
    # TODO: Define output fields
    pass


class InvoiceEmailSchema(Schema):
    """
    Serializes an invoice email dispatch record.

    Fields to define:
        - id, invoice_id, sent_by, recipient_email, subject
        - status, provider_msg_id, sent_at, error_message
    """
    # TODO: Define fields
    pass


class SendInvoiceEmailSchema(Schema):
    """
    Validates a request to email an invoice.

    Fields to define:
        - recipient_email: Required, Email format
        - subject: Optional, default will be auto-generated
    """
    # TODO: Define fields
    pass
