"""
VendorBridge ERP – Invoice Schemas
====================================
Marshmallow schemas for Invoice, InvoiceItem, and InvoiceEmail.
Used for request validation and JSON serialization.
"""

from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class InvoiceItemSchema(Schema):
    """
    Validates / serializes an invoice line item.
    Used both in create requests (load) and API responses (dump).
    """

    id                  = fields.Str(dump_only=True)
    invoice_id          = fields.Str(dump_only=True)
    quotation_item_id   = fields.Str(load_default=None, allow_none=True)
    item_name           = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    quantity            = fields.Decimal(required=True, as_string=True)
    unit_price          = fields.Decimal(required=True, as_string=True)
    tax_rate            = fields.Decimal(required=True, as_string=True)
    line_total          = fields.Decimal(dump_only=True, as_string=True, allow_none=True)
    hsn_code            = fields.Str(load_default=None, allow_none=True, validate=validate.Length(max=20))


class InvoiceCreateSchema(Schema):
    """
    Validates the creation of a new invoice from a fulfilled/issued PO.
    The service layer computes subtotal and GST from the items list.
    """

    po_id           = fields.Str(required=True, metadata={"description": "UUID of the issued/acknowledged PO"})
    invoice_date    = fields.Date(required=True)
    due_date        = fields.Date(load_default=None, allow_none=True)
    is_interstate   = fields.Bool(required=True, metadata={"description": "True = IGST, False = CGST+SGST"})
    notes           = fields.Str(load_default=None, allow_none=True)
    items           = fields.List(
        fields.Nested(InvoiceItemSchema),
        required=True,
        validate=validate.Length(min=1, error="At least one invoice item is required."),
    )

    @validates_schema
    def validate_due_date(self, data, **kwargs):
        """Ensure due_date is on or after invoice_date."""
        if data.get("due_date") and data.get("invoice_date"):
            if data["due_date"] < data["invoice_date"]:
                raise ValidationError(
                    "due_date must be on or after invoice_date.",
                    field_name="due_date",
                )


class InvoiceUpdateSchema(Schema):
    """
    Validates invoice edits.
    Only allowed while status='draft'; financials are locked after creation.
    """

    due_date    = fields.Date(load_default=None, allow_none=True)
    notes       = fields.Str(load_default=None, allow_none=True)


class InvoiceEmailSchema(Schema):
    """Serializes an InvoiceEmail dispatch record."""

    id               = fields.Str(dump_only=True)
    invoice_id       = fields.Str()
    sent_by          = fields.Str()
    recipient_email  = fields.Email()
    subject          = fields.Str()
    status           = fields.Str()
    provider_msg_id  = fields.Str(allow_none=True)
    sent_at          = fields.DateTime(allow_none=True)
    error_message    = fields.Str(allow_none=True)
    created_at       = fields.DateTime()


class InvoiceResponseSchema(Schema):
    """
    Serializes an Invoice for API output (with nested items and email history).
    Consumed by the React frontend via Axios.
    """

    id              = fields.Str(dump_only=True)
    invoice_number  = fields.Str()
    po_id           = fields.Str()
    vendor_id       = fields.Str()
    generated_by    = fields.Str()

    # Dates
    invoice_date    = fields.Date()
    due_date        = fields.Date(allow_none=True)
    paid_at         = fields.DateTime(allow_none=True)

    # Financials (all as strings for React precision safety)
    subtotal        = fields.Decimal(as_string=True)
    cgst_amount     = fields.Decimal(as_string=True)
    sgst_amount     = fields.Decimal(as_string=True)
    igst_amount     = fields.Decimal(as_string=True)
    total_amount    = fields.Decimal(as_string=True)

    # Artifacts & Status
    pdf_url         = fields.Str(allow_none=True)
    status          = fields.Str()
    notes           = fields.Str(allow_none=True)

    # Nested
    items           = fields.List(fields.Nested(InvoiceItemSchema))
    emails          = fields.List(fields.Nested(InvoiceEmailSchema))

    # Timestamps
    created_at      = fields.DateTime()
    updated_at      = fields.DateTime()


class SendInvoiceEmailSchema(Schema):
    """
    Validates a request to email an invoice PDF to a recipient.
    Used by POST /api/v1/invoices/<id>/send
    """

    recipient_email = fields.Email(required=True)
    subject         = fields.Str(load_default=None, allow_none=True)
