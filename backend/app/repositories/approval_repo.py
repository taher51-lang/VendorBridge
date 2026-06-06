"""
VendorBridge ERP – Approval Repository
========================================
Data-access layer for ApprovalWorkflow and ApprovalStep models.
"""

from sqlalchemy.orm import Session

from app.models.approval import ApprovalWorkflow, ApprovalStep
from app.repositories.base_repo import BaseRepository


class ApprovalWorkflowRepository(BaseRepository):
    """Queries for approval workflows."""

    model = ApprovalWorkflow

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_quotation(self, quotation_id: str):
        """
        Fetch the workflow attached to a specific quotation.
        """
        return self.db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.quotation_id == quotation_id,
            ApprovalWorkflow.deleted_at.is_(None)
        ).first()

    def get_pending_for_approver(self, approver_id: str, page: int = 1, per_page: int = 20):
        """
        List workflows that have a pending step assigned to the given approver.

        Used for the approver's dashboard "Awaiting My Action" list.
        """
        query = self.db.query(ApprovalWorkflow).join(
            ApprovalStep, ApprovalStep.workflow_id == ApprovalWorkflow.id
        ).filter(
            ApprovalStep.approver_id == approver_id,
            ApprovalStep.action == 'pending',
            ApprovalStep.step_number == ApprovalWorkflow.current_step,
            ApprovalStep.deleted_at.is_(None),
            ApprovalWorkflow.deleted_at.is_(None)
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def get_by_status(self, status: str, page: int = 1, per_page: int = 20):
        """
        List workflows filtered by status (pending, approved, rejected, cancelled).
        """
        query = self.db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.status == status,
            ApprovalWorkflow.deleted_at.is_(None)
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total


class ApprovalStepRepository(BaseRepository):
    """Queries for individual approval steps."""

    model = ApprovalStep

    def __init__(self, db: Session):
        super().__init__(db)

    def get_current_step(self, workflow_id: str):
        """
        Fetch the step that matches the workflow's current_step number.
        """
        workflow = self.db.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.id == workflow_id,
            ApprovalWorkflow.deleted_at.is_(None)
        ).first()
        if not workflow:
            return None
        
        return self.db.query(ApprovalStep).filter(
            ApprovalStep.workflow_id == workflow_id,
            ApprovalStep.step_number == workflow.current_step,
            ApprovalStep.deleted_at.is_(None)
        ).first()

    def get_steps_for_workflow(self, workflow_id: str):
        """
        Return all steps for a workflow, ordered by step_number.
        """
        return self.db.query(ApprovalStep).filter(
            ApprovalStep.workflow_id == workflow_id,
            ApprovalStep.deleted_at.is_(None)
        ).order_by(ApprovalStep.step_number).all()

