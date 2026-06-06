"""
VendorBridge ERP – Invoice Schemas
====================================
Marshmallow schemas for Invoice, InvoiceItem, and InvoiceEmail.
"""

from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class InvoiceItemSchema(Schema):
    """Validates / serializes an invoice line item."""
    id                 = fields.Str(dump_only=True)
    quotation_item_id  = fields.Str(load_default=None)
    item_name          = fields.Str(required=True, validate=validate.Length(max=200))
    quantity           = fields.Decimal(required=True, places=3, as_string=True)
    unit_price         = fields.Decimal(required=True, places=4, as_string=True)
    tax_rate           = fields.Decimal(required=True, places=2, as_string=True)
    line_total         = fields.Decimal(dump_only=True, places=2, as_string=True)
    hsn_code           = fields.Str(load_default=None, validate=validate.Length(max=20))


class InvoiceCreateSchema(Schema):
    """
    Validates the creation of a new invoice from a PO.
    """
    po_id          = fields.Str(required=True)
    invoice_date   = fields.Date(load_default=None)
    due_date       = fields.Date(load_default=None)
    is_interstate  = fields.Bool(load_default=False)
    notes          = fields.Str(load_default=None)

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if data.get("due_date") and data.get("invoice_date"):
            if data["due_date"] < data["invoice_date"]:
                raise ValidationError(
                    "due_date must be on or after invoice_date",
                    field_name="due_date",
                )


class InvoiceUpdateSchema(Schema):
    """Validates invoice edits (only while status=draft)."""
    due_date  = fields.Date()
    notes     = fields.Str()


class InvoiceEmailSchema(Schema):
    """Serializes an invoice email dispatch record."""
    id              = fields.Str()
    invoice_id      = fields.Str()
    sent_by         = fields.Str()
    recipient_email = fields.Str()
    subject         = fields.Str()
    status          = fields.Str()
    provider_msg_id = fields.Str(allow_none=True)
    sent_at         = fields.DateTime(allow_none=True)
    error_message   = fields.Str(allow_none=True)
    created_at      = fields.DateTime()


class InvoiceResponseSchema(Schema):
    """Serializes an Invoice for API output."""
    id              = fields.Str()
    invoice_number  = fields.Str()
    po_id           = fields.Str()
    vendor_id       = fields.Str()
    generated_by    = fields.Str()
    invoice_date    = fields.Date()
    due_date        = fields.Date(allow_none=True)
    subtotal        = fields.Decimal(places=2, as_string=True)
    cgst_amount     = fields.Decimal(places=2, as_string=True)
    sgst_amount     = fields.Decimal(places=2, as_string=True)
    igst_amount     = fields.Decimal(places=2, as_string=True)
    total_amount    = fields.Decimal(places=2, as_string=True)
    pdf_url         = fields.Str(allow_none=True)
    status          = fields.Str()
    paid_at         = fields.DateTime(allow_none=True)
    notes           = fields.Str(allow_none=True)
    created_at      = fields.DateTime()
    updated_at      = fields.DateTime(allow_none=True)
    items           = fields.List(fields.Nested(InvoiceItemSchema), dump_default=[])
    emails          = fields.List(fields.Nested(InvoiceEmailSchema), dump_default=[])
    # Denormalized fields
    vendor_name     = fields.Method("get_vendor_name")
    po_number       = fields.Method("get_po_number")

    def get_vendor_name(self, obj):
        if hasattr(obj, "vendor") and obj.vendor:
            return obj.vendor.company_name
        return None

    def get_po_number(self, obj):
        if hasattr(obj, "po") and obj.po:
            return obj.po.po_number
        return None


class SendInvoiceEmailSchema(Schema):
    """Validates a request to email an invoice."""
    recipient_email = fields.Email(required=True)
    subject         = fields.Str(load_default=None)
