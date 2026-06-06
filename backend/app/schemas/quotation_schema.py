"""
VendorBridge ERP – Quotation Schemas
======================================
Marshmallow schemas for Quotation and QuotationItem.
"""

from marshmallow import Schema, fields, validate


class QuotationItemSchema(Schema):
    """
    Validates / serializes a quotation line item.

    Fields to define:
        - id: Dump only
        - rfq_item_id: Required, FK reference
        - unit_price: Required, positive Decimal
        - quantity: Required, positive Decimal
        - tax_rate: Optional, Decimal (0-100)
        - line_total: Dump only (calculated)
        - notes: Optional
    """
    # TODO: Define fields with decimal precision validators
    pass


class QuotationCreateSchema(Schema):
    """
    Validates the creation / submission of a new quotation.

    Fields to define:
        - rfq_id: Required, UUID
        - delivery_days: Required, positive Integer
        - validity_days: Optional, positive Integer
        - currency: Optional, default 'INR', max 3
        - notes: Optional
        - items: Required, Nested list of QuotationItemSchema (min 1)
    """
    # TODO: Define fields
    pass


class QuotationUpdateSchema(Schema):
    """
    Validates quotation edits (only while status=draft).

    Same fields as create but all optional.
    May also include a 'submit' boolean to transition to 'submitted'.
    """
    # TODO: Define partial fields
    pass


class QuotationResponseSchema(Schema):
    """
    Serializes a Quotation for API output.

    Fields to define:
        - id, quote_number, rfq_id, vendor_id, revision_no
        - subtotal, tax_amount, total_amount, currency
        - delivery_days, validity_days, notes
        - status, submitted_at
        - items: Nested list of QuotationItemSchema
        - created_at, updated_at
    """
    # TODO: Define output fields with nested items
    pass


class QuotationCompareSchema(Schema):
    """
    Response schema for the quotation comparison view.
    Groups quotations for the same RFQ side by side.

    Fields to define:
        - rfq_id, rfq_title
        - quotations: Nested list of QuotationResponseSchema
        - recommended_quotation_id: Optional (lowest cost / best score)
    """
    # TODO: Define comparison output
    pass
