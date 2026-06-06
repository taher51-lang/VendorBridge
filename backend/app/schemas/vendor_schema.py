"""
VendorBridge ERP – Vendor Schemas
==================================
Marshmallow schemas for Vendor, VendorCategory, and VendorRating.
"""

from marshmallow import Schema, fields, validate


class VendorCategorySchema(Schema):
    """
    Serialization/validation for vendor categories.

    Fields to define:
        - id: Dump only
        - parent_id: Optional, String(36)
        - name: Required, max 100
        - description: Optional
        - subcategories: Nested list of VendorCategorySchema (dump only)
    """
    # TODO: Define fields.  Use fields.Nested('self', many=True)
    #       for hierarchical subcategories in responses.
    pass


class VendorCreateSchema(Schema):
    """
    Validates data for registering a new vendor.

    Fields to define:
        - company_name: Required, max 200
        - category_id: Optional, UUID string
        - gst_number: Optional, max 20, regex for GST format
        - pan_number: Optional, max 15
        - address, city, state, pincode: Optional strings
        - website: Optional, URL format
    """
    # TODO: Define fields with GST/PAN format validators
    pass


class VendorUpdateSchema(Schema):
    """
    Validates partial vendor profile update.

    Same fields as VendorCreateSchema but all optional.
    """
    # TODO: Define partial update fields
    pass


class VendorResponseSchema(Schema):
    """
    Serializes a Vendor model for API output.

    Fields to define:
        - id, company_name, gst_number, pan_number
        - address, city, state, pincode, website
        - status, avg_rating
        - category: Nested VendorCategorySchema
        - created_at, updated_at
    """
    # TODO: Define output fields with nested category
    pass


class VendorRatingCreateSchema(Schema):
    """
    Validates a new vendor rating submission.

    Fields to define:
        - vendor_id: Required
        - po_id: Required
        - quality_score: Required, 1-5
        - delivery_score: Required, 1-5
        - pricing_score: Required, 1-5
        - comments: Optional
    """
    # TODO: Define fields with Range(min=1, max=5) validators
    pass


class VendorRatingResponseSchema(Schema):
    """
    Serializes a VendorRating for API output.

    Fields to define:
        - id, vendor_id, po_id, rated_by
        - quality_score, delivery_score, pricing_score, overall_score
        - comments, created_at
    """
    # TODO: Define output fields
    pass
