from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_db
from app.services.approval_service import ApprovalService
from app.schemas.approval_schema import (
    ApprovalWorkflowCreateSchema,
    ApprovalActionSchema,
    ApprovalWorkflowResponseSchema,
)
from app.utils.response_helper import success_response, error_response
from app.utils.security import roles_required, get_current_user_id, get_current_user_role

approval_bp = Blueprint("approvals", __name__)


@approval_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer")
def initiate_workflow():
    """
    POST /api/v1/approvals
    Initiate an approval workflow for a selected quotation.
    Accessible by: procurement_officer.
    """
    db = next(get_db())
    initiator_id = get_current_user_id()
    schema = ApprovalWorkflowCreateSchema()
    errors = schema.validate(request.json)
    if errors:
        return error_response(str(errors), 422)

    data = schema.load(request.json)
    service = ApprovalService(db)
    try:
        workflow = service.initiate_workflow(data, initiator_id)
        response_schema = ApprovalWorkflowResponseSchema()
        return success_response(response_schema.dump(workflow), "Approval workflow initiated successfully.", 201)
    except Exception as e:
        return error_response(str(e), 400)


@approval_bp.route("/", methods=["GET"])
@jwt_required()
def list_workflows():
    """
    GET /api/v1/approvals?status=pending&page=1
    List approval workflows.
    Managers see their pending approvals; officers see all.
    """
    db = next(get_db())
    service = ApprovalService(db)
    response_schema = ApprovalWorkflowResponseSchema(many=True)

    status = request.args.get("status")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    
    role = get_current_user_role()
    user_id = get_current_user_id()

    try:
        if role == "manager":
            results, total = service.list_pending_approvals(user_id, page, per_page)
        else:
            if status:
                results, total = service.workflow_repo.get_by_status(status, page, per_page)
            else:
                results, total = service.workflow_repo.get_all(page, per_page)

        return success_response(
            response_schema.dump(results),
            f"Found {total} workflow(s).",
            meta={"page": page, "per_page": per_page, "total": total}
        )
    except Exception as e:
        return error_response(str(e), 500)


@approval_bp.route("/<workflow_id>", methods=["GET"])
@jwt_required()
def get_workflow(workflow_id):
    """
    GET /api/v1/approvals/<workflow_id>
    Get workflow details with all steps.
    """
    db = next(get_db())
    service = ApprovalService(db)
    try:
        workflow = service.get_workflow(workflow_id)
        response_schema = ApprovalWorkflowResponseSchema()
        return success_response(response_schema.dump(workflow), "Workflow retrieved successfully.")
    except Exception as e:
        return error_response(str(e), 404)


@approval_bp.route("/<workflow_id>/action", methods=["POST"])
@jwt_required()
def process_step(workflow_id):
    """
    POST /api/v1/approvals/<workflow_id>/action
    Body: {"action": "approved|rejected", "remarks": "..."}
    Record the approver's decision on the current step.
    Accessible by: the assigned approver only.
    """
    db = next(get_db())
    approver_id = get_current_user_id()
    
    schema = ApprovalActionSchema()
    errors = schema.validate(request.json)
    if errors:
        return error_response(str(errors), 422)

    data = schema.load(request.json)
    service = ApprovalService(db)
    try:
        workflow = service.process_step(
            workflow_id=workflow_id,
            approver_id=approver_id,
            action=data['action'],
            remarks=data.get('remarks')
        )
        response_schema = ApprovalWorkflowResponseSchema()
        return success_response(response_schema.dump(workflow), "Step processed successfully.")
    except Exception as e:
        return error_response(str(e), 400)


@approval_bp.route("/<workflow_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_workflow(workflow_id):
    """
    POST /api/v1/approvals/<workflow_id>/cancel
    Cancel an in-progress workflow.
    Accessible by: initiator or admin.
    """
    db = next(get_db())
    user_id = get_current_user_id()
    service = ApprovalService(db)
    try:
        workflow = service.cancel_workflow(workflow_id, user_id)
        response_schema = ApprovalWorkflowResponseSchema()
        return success_response(response_schema.dump(workflow), "Workflow cancelled successfully.")
    except Exception as e:
        return error_response(str(e), 400)


@approval_bp.route("/pending", methods=["GET"])
@jwt_required()
def my_pending_approvals():
    """
    GET /api/v1/approvals/pending
    List workflows awaiting the current user's approval.
    """
    db = next(get_db())
    user_id = get_current_user_id()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    service = ApprovalService(db)
    try:
        results, total = service.list_pending_approvals(user_id, page, per_page)
        response_schema = ApprovalWorkflowResponseSchema(many=True)
        return success_response(
            response_schema.dump(results),
            f"Found {total} pending workflow(s).",
            meta={"page": page, "per_page": per_page, "total": total}
        )
    except Exception as e:
        return error_response(str(e), 500)

