"""
VendorBridge ERP – Approval Routes
====================================
Endpoints for initiating and processing approval workflows.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_db
from app.services.approval_service import ApprovalService
from app.schemas.approval_schema import (
    ApprovalWorkflowCreateSchema,
    ApprovalActionSchema,
)
from app.utils.response_helper import success_response, error_response
from app.utils.security import roles_required

approval_bp = Blueprint("approvals", __name__)


@approval_bp.route("/", methods=["POST"])
@jwt_required()
def initiate_workflow():
    """
    POST /api/v1/approvals
    Initiate an approval workflow for a selected quotation.
    Accessible by: procurement_officer.
    """
    # 1. Validate body with ApprovalWorkflowCreateSchema
    # 2. Call ApprovalService(db).initiate_workflow(data, initiator_id)
    # 3. Return created workflow (201)
    pass


@approval_bp.route("/", methods=["GET"])
@jwt_required()
def list_workflows():
    """
    GET /api/v1/approvals?status=pending&page=1
    List approval workflows.
    Managers see their pending approvals; officers see all.
    """
    # 1. Extract query params
    # 2. If role is manager → call service.list_pending_approvals(user_id, ...)
    # 3. Else → list all with optional status filter
    pass


@approval_bp.route("/<workflow_id>", methods=["GET"])
@jwt_required()
def get_workflow(workflow_id):
    """
    GET /api/v1/approvals/<workflow_id>
    Get workflow details with all steps.
    """
    # 1. Call ApprovalService(db).get_workflow(workflow_id)
    pass


@approval_bp.route("/<workflow_id>/action", methods=["POST"])
@jwt_required()
def process_step(workflow_id):
    """
    POST /api/v1/approvals/<workflow_id>/action
    Body: {"action": "approved|rejected", "remarks": "..."}
    Record the approver's decision on the current step.
    Accessible by: the assigned approver only.
    """
    # 1. Validate body with ApprovalActionSchema
    # 2. Call ApprovalService(db).process_step(
    #        workflow_id, approver_id, action, remarks
    #    )
    # 3. Return updated workflow
    pass


@approval_bp.route("/<workflow_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_workflow(workflow_id):
    """
    POST /api/v1/approvals/<workflow_id>/cancel
    Cancel an in-progress workflow.
    Accessible by: initiator or admin.
    """
    # 1. Call ApprovalService(db).cancel_workflow(workflow_id, user_id)
    pass


@approval_bp.route("/pending", methods=["GET"])
@jwt_required()
def my_pending_approvals():
    """
    GET /api/v1/approvals/pending
    List workflows awaiting the current user's approval.
    """
    # 1. Call ApprovalService(db).list_pending_approvals(user_id, page, per_page)
    pass
