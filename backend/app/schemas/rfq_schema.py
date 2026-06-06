"""
VendorBridge ERP – RFQ Schemas
================================
Marshmallow schemas for RFQ, RFQItem, and RFQVendorAssignment.
"""

from datetime import datetime, timezone

from marshmallow import Schema, fields, validate, validates, ValidationError


from datetime import datetime, timezone
from marshmallow import Schema, fields, validate, validates, ValidationError

class RFQItemSchema(Schema):
    """
    Validates / serializes a single RFQ line item.
    """
    id = fields.Str(dump_only=True)
    item_name = fields.Str(required=True, validate=validate.Length(max=200))
    description = fields.Str(allow_none=True)
    quantity = fields.Float(required=True, validate=validate.Range(min=0.001))
    unit = fields.Str(allow_none=True, validate=validate.Length(max=20))
    specifications = fields.Str(allow_none=True)
    sort_order = fields.Int(default=0)


class RFQCreateSchema(Schema):
    """
    Validates the creation of a new RFQ.
    """
    title = fields.Str(required=True, validate=validate.Length(max=200))
    description = fields.Str(allow_none=True)
    deadline = fields.DateTime(required=True)
    notes = fields.Str(allow_none=True)
    attachment_urls = fields.List(fields.Str(), allow_none=True)
    items = fields.Nested(RFQItemSchema, many=True, required=True, validate=validate.Length(min=1))
    vendor_ids = fields.List(fields.Str(), allow_none=True)

    @validates('deadline')
    def validate_deadline(self, val):
        if val.tzinfo is None:
            # Native datetime
            if val < datetime.utcnow():
                raise ValidationError("Deadline must be in the future.")
        else:
            # Aware datetime
            if val < datetime.now(timezone.utc):
                raise ValidationError("Deadline must be in the future.")


class RFQUpdateSchema(Schema):
    """
    Validates RFQ updates (only allowed while status=draft).
    """
    title = fields.Str(validate=validate.Length(max=200))
    description = fields.Str(allow_none=True)
    deadline = fields.DateTime()
    notes = fields.Str(allow_none=True)
    attachment_urls = fields.List(fields.Str(), allow_none=True)
    items = fields.Nested(RFQItemSchema, many=True)
    vendor_ids = fields.List(fields.Str(), allow_none=True)


class RFQVendorAssignmentSchema(Schema):
    """
    Serializes an RFQ-vendor assignment record.
    """
    id = fields.Str(dump_only=True)
    rfq_id = fields.Str(dump_only=True)
    vendor_id = fields.Str(dump_only=True)
    invited_at = fields.DateTime(dump_only=True)
    viewed_at = fields.DateTime(dump_only=True)
    status = fields.Str(dump_only=True)


class RFQResponseSchema(Schema):
    """
    Serializes an RFQ for API output.
    """
    id = fields.Str(dump_only=True)
    rfq_number = fields.Str(dump_only=True)
    title = fields.Str(dump_only=True)
    description = fields.Str(dump_only=True)
    deadline = fields.DateTime(dump_only=True)
    status = fields.Str(dump_only=True)
    notes = fields.Str(dump_only=True)
    attachment_urls = fields.List(fields.Str(), dump_only=True)
    created_by = fields.Str(dump_only=True)
    items = fields.Nested(RFQItemSchema, many=True, dump_only=True)
    vendor_assignments = fields.Nested(RFQVendorAssignmentSchema, many=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

