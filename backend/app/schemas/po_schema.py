"""
VendorBridge ERP – Purchase Order Schemas
==========================================
Marshmallow schemas for PurchaseOrder CRUD and API responses.
Used for request validation and JSON serialization.
"""

from marshmallow import Schema, fields, validate


class POCreateSchema(Schema):
    """
    Validates the issuance of a new Purchase Order.
    Financial fields (subtotal, tax, total, vendor_id, currency)
    are copied from the approved Quotation by the service layer.
    """

    quotation_id       = fields.Str(required=True, metadata={"description": "UUID of the approved quotation"})
    delivery_address   = fields.Str(load_default=None)
    expected_delivery  = fields.Date(load_default=None)
    terms_conditions   = fields.Str(load_default=None)


class POUpdateSchema(Schema):
    """
    Validates PO updates.
    Only delivery/logistics fields are editable; financials are locked after issuance.
    """

    delivery_address   = fields.Str(load_default=None)
    expected_delivery  = fields.Date(load_default=None)
    terms_conditions   = fields.Str(load_default=None)


class POItemResponseSchema(Schema):
    """Serializes a single PO line item."""

    id           = fields.Str(dump_only=True)
    po_id        = fields.Str(dump_only=True)
    rfq_item_id  = fields.Str(allow_none=True)
    item_name    = fields.Str()
    quantity     = fields.Decimal(as_string=True)
    unit_price   = fields.Decimal(as_string=True)
    tax_rate     = fields.Decimal(as_string=True)
    line_total   = fields.Decimal(as_string=True, allow_none=True)
    hsn_code     = fields.Str(allow_none=True)


class POResponseSchema(Schema):
    """
    Serializes a PurchaseOrder for API output.
    Consumed by the React frontend via Axios.
    """

    id                 = fields.Str(dump_only=True)
    po_number          = fields.Str()
    quotation_id       = fields.Str()
    vendor_id          = fields.Str()
    created_by         = fields.Str()
    workflow_id        = fields.Str(allow_none=True)

    # Delivery
    delivery_address   = fields.Str(allow_none=True)
    expected_delivery  = fields.Date(allow_none=True)

    # Financial
    subtotal           = fields.Decimal(as_string=True)
    tax_amount         = fields.Decimal(as_string=True)
    total_amount       = fields.Decimal(as_string=True)
    currency           = fields.Str()

    # Terms & Status
    terms_conditions   = fields.Str(allow_none=True)
    status             = fields.Str()
    issued_at          = fields.DateTime()

    # Line items
    items              = fields.List(fields.Nested(POItemResponseSchema))

    # Timestamps
    created_at         = fields.DateTime()
    updated_at         = fields.DateTime()
