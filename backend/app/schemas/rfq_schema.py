"""
VendorBridge ERP – RFQ Schemas
================================
Marshmallow schemas for RFQ, RFQItem, and RFQVendorAssignment.
"""

from marshmallow import Schema, fields, validate


class RFQItemSchema(Schema):
    """
    Validates / serializes a single RFQ line item.

    Fields to define:
        - id: Dump only
        - item_name: Required, max 200
        - description: Optional
        - quantity: Required, positive number
        - unit: Optional, max 20
        - specifications: Optional
        - sort_order: Optional, default 0
    """
    # TODO: Define fields with positive-number validation for quantity
    pass


class RFQCreateSchema(Schema):
    """
    Validates the creation of a new RFQ.

    Fields to define:
        - title: Required, max 200
        - description: Optional
        - deadline: Required, DateTime (must be in the future)
        - notes: Optional
        - attachment_urls: Optional, List of URL strings
        - items: Required, Nested list of RFQItemSchema (min 1 item)
        - vendor_ids: Optional, List of vendor UUID strings to invite
    """
    # TODO: Define fields
    # TODO: Add @validates('deadline') to ensure it's in the future
    pass


class RFQUpdateSchema(Schema):
    """
    Validates RFQ updates (only allowed while status=draft).

    Same fields as create but all optional.
    """
    # TODO: Define partial fields
    pass


class RFQResponseSchema(Schema):
    """
    Serializes an RFQ for API output.

    Fields to define:
        - id, rfq_number, title, description, deadline
        - status, notes, attachment_urls
        - created_by, creator (nested UserResponseSchema)
        - items: Nested list of RFQItemSchema
        - vendor_assignments: Nested list
        - created_at, updated_at
    """
    # TODO: Define output fields with nested schemas
    pass


class RFQVendorAssignmentSchema(Schema):
    """
    Serializes an RFQ-vendor assignment record.

    Fields to define:
        - id, rfq_id, vendor_id
        - invited_at, viewed_at, status
    """
    # TODO: Define fields
    pass
