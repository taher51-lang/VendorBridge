"""
VendorBridge ERP – Purchase Order Schemas
==========================================
Marshmallow schemas for PurchaseOrder CRUD and responses.
"""

from marshmallow import Schema, fields, validate


class POItemSchema(Schema):
    """Validates / serializes a PO line item."""
    id           = fields.Str(dump_only=True)
    rfq_item_id  = fields.Str(load_default=None)
    item_name    = fields.Str(required=True, validate=validate.Length(max=200))
    quantity     = fields.Decimal(required=True, places=3, as_string=True)
    unit_price   = fields.Decimal(required=True, places=4, as_string=True)
    tax_rate     = fields.Decimal(load_default=0, places=2, as_string=True)
    line_total   = fields.Decimal(dump_only=True, places=2, as_string=True)
    hsn_code     = fields.Str(load_default=None, validate=validate.Length(max=20))


class POCreateSchema(Schema):
    """
    Validates the issuance of a new Purchase Order.
    subtotal, tax_amount, total_amount, vendor_id, and currency
    are copied from the approved Quotation by the service layer.
    """
    quotation_id      = fields.Str(required=True)
    delivery_address  = fields.Str(load_default=None)
    expected_delivery = fields.Date(load_default=None)
    terms_conditions  = fields.Str(load_default=None)


class POUpdateSchema(Schema):
    """Validates PO updates (limited fields: delivery info, terms)."""
    delivery_address  = fields.Str()
    expected_delivery = fields.Date()
    terms_conditions  = fields.Str()


class POResponseSchema(Schema):
    """Serializes a PurchaseOrder for API output."""
    id                = fields.Str()
    po_number         = fields.Str()
    quotation_id      = fields.Str()
    vendor_id         = fields.Str()
    created_by        = fields.Str()
    workflow_id       = fields.Str(allow_none=True)
    delivery_address  = fields.Str(allow_none=True)
    expected_delivery = fields.Date(allow_none=True)
    subtotal          = fields.Decimal(places=2, as_string=True)
    tax_amount        = fields.Decimal(places=2, as_string=True)
    total_amount      = fields.Decimal(places=2, as_string=True)
    currency          = fields.Str()
    terms_conditions  = fields.Str(allow_none=True)
    status            = fields.Str()
    issued_at         = fields.DateTime()
    created_at        = fields.DateTime()
    updated_at        = fields.DateTime(allow_none=True)
    items             = fields.List(fields.Nested(POItemSchema), dump_default=[])
    # Nested summary fields
    vendor_name       = fields.Method("get_vendor_name")
    rfq_number        = fields.Method("get_rfq_number")

    def get_vendor_name(self, obj):
        if hasattr(obj, "vendor") and obj.vendor:
            return obj.vendor.company_name
        return None

    def get_rfq_number(self, obj):
        if hasattr(obj, "quotation") and obj.quotation and hasattr(obj.quotation, "rfq"):
            return obj.quotation.rfq.rfq_number if obj.quotation.rfq else None
        return None
