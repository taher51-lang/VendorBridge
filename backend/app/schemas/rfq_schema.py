"""
VendorBridge ERP – RFQ Schemas
================================
Marshmallow schemas for RFQ, RFQItem, and RFQVendorAssignment.
"""

from datetime import datetime, timezone

from marshmallow import Schema, fields, validate, validates, ValidationError


class RFQItemSchema(Schema):
    """Validates / serializes a single RFQ line item."""

    id = fields.String(dump_only=True)
    rfq_id = fields.String(dump_only=True)
    item_name = fields.String(required=True, validate=validate.Length(min=1, max=200))
    description = fields.String(load_default=None, allow_none=True)
    quantity = fields.Decimal(
        required=True,
        as_string=False,
        validate=validate.Range(min=0.001, error="Quantity must be greater than zero."),
    )
    unit = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=20))
    specifications = fields.String(load_default=None, allow_none=True)
    sort_order = fields.Integer(load_default=0)


class RFQCreateSchema(Schema):
    """Validates the creation of a new RFQ."""

    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    description = fields.String(load_default=None, allow_none=True)
    deadline = fields.DateTime(required=True)
    notes = fields.String(load_default=None, allow_none=True)
    attachment_urls = fields.List(fields.Url(require_tld=False), load_default=None, allow_none=True)
    items = fields.List(
        fields.Nested(RFQItemSchema),
        required=True,
        validate=validate.Length(min=1, error="At least one line item is required."),
    )
    vendor_ids = fields.List(fields.String(), load_default=None, allow_none=True)

    @validates("deadline")
    def validate_deadline(self, value: datetime):
        """Deadline must be in the future."""
        now = datetime.now(timezone.utc)
        # value may be naive or aware depending on marshmallow version
        if value.tzinfo is None:
            # treat as UTC
            value = value.replace(tzinfo=timezone.utc)
        if value <= now:
            raise ValidationError("Deadline must be a future date/time.")


class RFQUpdateSchema(Schema):
    """Validates RFQ updates (only allowed while status='draft')."""

    title = fields.String(load_default=None, allow_none=True, validate=validate.Length(min=1, max=200))
    description = fields.String(load_default=None, allow_none=True)
    deadline = fields.DateTime(load_default=None, allow_none=True)
    notes = fields.String(load_default=None, allow_none=True)
    attachment_urls = fields.List(fields.Url(require_tld=False), load_default=None, allow_none=True)
    items = fields.List(fields.Nested(RFQItemSchema), load_default=None, allow_none=True)
    vendor_ids = fields.List(fields.String(), load_default=None, allow_none=True)

    @validates("deadline")
    def validate_deadline(self, value):
        if value is None:
            return
        now = datetime.now(timezone.utc)
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        if value <= now:
            raise ValidationError("Deadline must be a future date/time.")


class RFQVendorAssignmentSchema(Schema):
    """Serializes an RFQ-vendor assignment record."""

    id = fields.String(dump_only=True)
    rfq_id = fields.String()
    vendor_id = fields.String()
    invited_at = fields.DateTime(dump_only=True)
    viewed_at = fields.DateTime(dump_only=True, allow_none=True)
    status = fields.String()


class RFQResponseSchema(Schema):
    """Serializes an RFQ for API output."""

    id = fields.String(dump_only=True)
    rfq_number = fields.String()
    title = fields.String()
    description = fields.String()
    deadline = fields.DateTime()
    status = fields.String()
    notes = fields.String()
    attachment_urls = fields.List(fields.String())
    created_by = fields.String()
    items = fields.List(fields.Nested(RFQItemSchema), dump_only=True)
    vendor_assignments = fields.List(fields.Nested(RFQVendorAssignmentSchema), dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class VendorInviteSchema(Schema):
    """Validates a vendor invite request body."""

    vendor_ids = fields.List(
        fields.String(),
        required=True,
        validate=validate.Length(min=1, error="At least one vendor_id is required."),
    )
