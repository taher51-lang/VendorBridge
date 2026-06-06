"""
VendorBridge ERP – Approval Schemas
=====================================
Marshmallow schemas for ApprovalWorkflow and ApprovalStep.
"""

from marshmallow import Schema, fields, validate


class ApprovalStepSchema(Schema):
    """
    Validates / serializes an individual approval step.

    Fields to define:
        - id: Dump only
        - step_number: Required, positive SmallInteger
        - approver_id: Required, UUID
        - action: Dump only (pending/approved/rejected)
        - remarks: Optional
        - acted_at: Dump only
        - due_at: Optional, DateTime
    """
    # TODO: Define fields
    pass


class ApprovalWorkflowCreateSchema(Schema):
    """
    Validates the initiation of a new approval workflow.

    Fields to define:
        - quotation_id: Required, UUID
        - steps: Required, Nested list of ApprovalStepSchema (min 1)
            Each step needs approver_id and optional due_at.
    """
    # TODO: Define fields with nested steps
    pass


class ApprovalActionSchema(Schema):
    """
    Validates an approver's action on a step.

    Fields to define:
        - action: Required, one of 'approved' / 'rejected'
        - remarks: Optional, text
    """
    # TODO: Define fields
    pass


class ApprovalWorkflowResponseSchema(Schema):
    """
    Serializes a full workflow with its steps for API output.

    Fields to define:
        - id, quotation_id, initiated_by
        - current_step, total_steps, status, completed_at
        - steps: Nested list of ApprovalStepSchema
        - created_at, updated_at
    """
    # TODO: Define output fields with nested steps
    pass
