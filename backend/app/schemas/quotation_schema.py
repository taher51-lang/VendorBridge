"""
VendorBridge ERP – Quotation Schemas
======================================
Marshmallow schemas for Quotation and QuotationItem.
"""

from marshmallow import Schema, fields, validate


class QuotationItemSchema(Schema):
    """Validates / serializes a quotation line item."""
    id           = fields.Str(dump_only=True)
    rfq_item_id  = fields.Str(load_default=None)
    unit_price   = fields.Decimal(required=True, places=4, as_string=True)
    quantity     = fields.Decimal(required=True, places=3, as_string=True)
    tax_rate     = fields.Decimal(load_default=0, places=2, as_string=True)
    line_total   = fields.Decimal(dump_only=True, places=2, as_string=True)
    notes        = fields.Str(load_default=None)


class QuotationCreateSchema(Schema):
    """Validates the creation of a new quotation."""
    rfq_id        = fields.Str(required=True)
    delivery_days = fields.Int(required=True, validate=validate.Range(min=1))
    validity_days = fields.Int(load_default=None, validate=validate.Range(min=1))
    currency      = fields.Str(load_default="INR", validate=validate.Length(max=3))
    is_interstate = fields.Bool(load_default=False)
    notes         = fields.Str(load_default=None)
    items         = fields.List(
        fields.Nested(QuotationItemSchema),
        required=True,
        validate=validate.Length(min=1)
    )


class QuotationUpdateSchema(Schema):
    """Validates partial updates on a draft quotation."""
    delivery_days = fields.Int(validate=validate.Range(min=1))
    validity_days = fields.Int(validate=validate.Range(min=1))
    currency      = fields.Str(validate=validate.Length(max=3))
    is_interstate = fields.Bool()
    notes         = fields.Str()
    items         = fields.List(fields.Nested(QuotationItemSchema))


class QuotationResponseSchema(Schema):
    """Serializes a Quotation for API output."""
    id             = fields.Str()
    quote_number   = fields.Str()
    rfq_id         = fields.Str()
    vendor_id      = fields.Str()
    revision_no    = fields.Int()
    subtotal       = fields.Decimal(places=2, as_string=True)
    tax_amount     = fields.Decimal(places=2, as_string=True)
    cgst_amount    = fields.Decimal(places=2, as_string=True)
    sgst_amount    = fields.Decimal(places=2, as_string=True)
    igst_amount    = fields.Decimal(places=2, as_string=True)
    total_amount   = fields.Decimal(places=2, as_string=True)
    currency       = fields.Str()
    is_interstate  = fields.Bool()
    delivery_days  = fields.Int()
    validity_days  = fields.Int()
    notes          = fields.Str()
    status         = fields.Str()
    submitted_at   = fields.DateTime(allow_none=True)
    created_at     = fields.DateTime()
    updated_at     = fields.DateTime()
    items          = fields.List(fields.Nested(QuotationItemSchema), dump_default=[])


class QuotationCompareSchema(Schema):
    """Response schema for the quotation comparison view."""
    rfq_id                    = fields.Str()
    rfq_title                 = fields.Str()
    rfq_number                = fields.Str()
    quotations                = fields.List(fields.Nested(QuotationResponseSchema))
    recommended_quotation_id  = fields.Str(allow_none=True)
