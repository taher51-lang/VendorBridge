"""
VendorBridge ERP – Vendor Schemas
==================================
Marshmallow schemas for Vendor, VendorCategory, and VendorRating.
"""

import re

from marshmallow import Schema, fields, validate, validates, ValidationError


# ── GST / PAN format validators ──────────────────────────────────

GST_PATTERN = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
)
PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")


class VendorCategorySchema(Schema):
    """Serialization/validation for vendor categories."""

    id = fields.String(dump_only=True)
    parent_id = fields.String(load_default=None, allow_none=True)
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    description = fields.String(load_default=None, allow_none=True)
    # Recursive nested for responses
    subcategories = fields.List(fields.Nested(lambda: VendorCategorySchema()), dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class VendorCreateSchema(Schema):
    """Validates data for registering a new vendor (creates User + Vendor)."""

    # User-level fields (stored on the User model)
    name = fields.String(required=True, validate=validate.Length(min=1, max=200))
    email = fields.Email(required=True)
    phone = fields.String(load_default=None, validate=validate.Length(max=20))
    password = fields.String(load_default="Vendor@123!", validate=validate.Length(min=8))

    # Vendor profile fields
    company_name = fields.String(load_default=None, validate=validate.Length(max=200))
    category_id = fields.String(load_default=None, allow_none=True)
    # Category as plain string (alternative to category_id for simpler API)
    category = fields.String(load_default=None, allow_none=True)

    gst_number = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=20))
    pan_number = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=15))
    address = fields.String(load_default=None, allow_none=True)
    city = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=100))
    state = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=100))
    pincode = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=10))
    website = fields.Url(load_default=None, allow_none=True, require_tld=False)

    @validates("gst_number")
    def validate_gst(self, value):
        if value and not GST_PATTERN.match(value.upper()):
            raise ValidationError(
                "Invalid GST number format. Expected: 22AAAAA0000A1Z5"
            )

    @validates("pan_number")
    def validate_pan(self, value):
        if value and not PAN_PATTERN.match(value.upper()):
            raise ValidationError(
                "Invalid PAN number format. Expected: AAAAA0000A"
            )


class VendorUpdateSchema(Schema):
    """Validates partial vendor profile update (all fields optional)."""

    # User-level fields
    phone = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=20))
    full_name = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=150))

    # Vendor profile fields
    company_name = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=200))
    category_id = fields.String(load_default=None, allow_none=True)
    gst_number = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=20))
    pan_number = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=15))
    address = fields.String(load_default=None, allow_none=True)
    city = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=100))
    state = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=100))
    pincode = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=10))
    website = fields.Url(load_default=None, allow_none=True, require_tld=False)

    @validates("gst_number")
    def validate_gst(self, value):
        if value and not GST_PATTERN.match(value.upper()):
            raise ValidationError(
                "Invalid GST number format. Expected: 22AAAAA0000A1Z5"
            )

    @validates("pan_number")
    def validate_pan(self, value):
        if value and not PAN_PATTERN.match(value.upper()):
            raise ValidationError(
                "Invalid PAN number format. Expected: AAAAA0000A"
            )


class VendorStatusUpdateSchema(Schema):
    """Validates a status change request."""

    status = fields.String(
        required=True,
        validate=validate.OneOf(["active", "suspended", "blacklisted", "pending"]),
    )
    reason = fields.String(load_default=None, allow_none=True)


class VendorResponseSchema(Schema):
    """Serializes a Vendor model for API output (includes linked user fields)."""

    id = fields.String(dump_only=True)
    company_name = fields.String()
    gst_number = fields.String()
    pan_number = fields.String()
    address = fields.String()
    city = fields.String()
    state = fields.String()
    pincode = fields.String()
    website = fields.String()
    status = fields.String()
    avg_rating = fields.Float()
    category_id = fields.String()
    category = fields.Nested(VendorCategorySchema, dump_only=True)
    user_id = fields.String()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class VendorRatingCreateSchema(Schema):
    """Validates a new vendor rating submission."""

    vendor_id = fields.String(required=True)
    po_id = fields.String(required=True)
    quality_score = fields.Integer(
        required=True, validate=validate.Range(min=1, max=5)
    )
    delivery_score = fields.Integer(
        required=True, validate=validate.Range(min=1, max=5)
    )
    pricing_score = fields.Integer(
        required=True, validate=validate.Range(min=1, max=5)
    )
    comments = fields.String(load_default=None, allow_none=True)


class VendorRatingResponseSchema(Schema):
    """Serializes a VendorRating for API output."""

    id = fields.String(dump_only=True)
    vendor_id = fields.String()
    po_id = fields.String()
    rated_by = fields.String()
    quality_score = fields.Integer()
    delivery_score = fields.Integer()
    pricing_score = fields.Integer()
    overall_score = fields.Float()
    comments = fields.String()
    created_at = fields.DateTime(dump_only=True)
