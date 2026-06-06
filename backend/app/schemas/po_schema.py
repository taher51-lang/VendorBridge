"""
VendorBridge ERP – Purchase Order Schemas
==========================================
Marshmallow schemas for PurchaseOrder CRUD and responses.
"""

from marshmallow import Schema, fields, validate


class POCreateSchema(Schema):
    """
    Validates the issuance of a new Purchase Order.

    Fields to define:
        - quotation_id: Required, UUID of the approved quotation
        - delivery_address: Optional, text
        - expected_delivery: Optional, Date
        - terms_conditions: Optional, text
    """
    # TODO: Define fields
    # Note: subtotal, tax_amount, total_amount, vendor_id, and currency
    #       are copied from the approved Quotation by the service layer.
    pass


class POUpdateSchema(Schema):
    """
    Validates PO updates (limited fields: status, delivery info).

    Fields to define:
        - delivery_address: Optional
        - expected_delivery: Optional, Date
        - terms_conditions: Optional
        - status: Optional, one of 'acknowledged' / 'fulfilled' / 'cancelled'
    """
    # TODO: Define partial fields with status transition validation
    pass


class POResponseSchema(Schema):
    """
    Serializes a PurchaseOrder for API output.

    Fields to define:
        - id, po_number, quotation_id, vendor_id, created_by
        - delivery_address, expected_delivery
        - subtotal, tax_amount, total_amount, currency
        - terms_conditions, status, issued_at
        - vendor: Nested VendorResponseSchema
        - quotation: Nested QuotationResponseSchema (summary)
        - created_at, updated_at
    """
    # TODO: Define output fields with nested vendor and quotation
    pass
