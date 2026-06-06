"""
VendorBridge ERP – Approval Schemas
=====================================
Marshmallow schemas for ApprovalWorkflow and ApprovalStep.
"""

from marshmallow import Schema, fields, validate


class ApprovalStepSchema(Schema):
    """
    Validates / serializes an individual approval step.
    """
    id = fields.Str(dump_only=True)
    step_number = fields.Int(required=True, validate=validate.Range(min=1))
    approver_id = fields.Str(required=True)
    action = fields.Str(dump_only=True, validate=validate.OneOf(["pending", "approved", "rejected"]))
    remarks = fields.Str(allow_none=True)
    acted_at = fields.DateTime(dump_only=True)
    due_at = fields.DateTime(allow_none=True)


class ApprovalWorkflowCreateSchema(Schema):
    """
    Validates the initiation of a new approval workflow.
    """
    quotation_id = fields.Str(required=True)
    steps = fields.Nested(ApprovalStepSchema, many=True, required=True, validate=validate.Length(min=1))


class ApprovalActionSchema(Schema):
    """
    Validates an approver's action on a step.
    """
    action = fields.Str(required=True, validate=validate.OneOf(["approved", "rejected"]))
    remarks = fields.Str(allow_none=True)


class ApprovalWorkflowResponseSchema(Schema):
    """
    Serializes a full workflow with its steps for API output.
    """
    id = fields.Str(dump_only=True)
    quotation_id = fields.Str(dump_only=True)
    initiated_by = fields.Str(dump_only=True)
    current_step = fields.Int(dump_only=True)
    total_steps = fields.Int(dump_only=True)
    status = fields.Str(dump_only=True)
    completed_at = fields.DateTime(dump_only=True)
    steps = fields.Nested(ApprovalStepSchema, many=True, dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

