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
        # TODO: Call super().__init__(db)
        pass

    def get_by_quotation(self, quotation_id: str):
        """
        Fetch the workflow attached to a specific quotation.
        """
        # TODO: Query ApprovalWorkflow where quotation_id == quotation_id
        pass

    def get_pending_for_approver(self, approver_id: str, page: int = 1, per_page: int = 20):
        """
        List workflows that have a pending step assigned to the given approver.

        Used for the approver's dashboard "Awaiting My Action" list.
        """
        # TODO: Implement:
        #   1. Join ApprovalWorkflow with ApprovalStep
        #   2. Filter step.approver_id == approver_id
        #   3. Filter step.action == 'pending'
        #   4. Filter step.step_number == workflow.current_step
        #   5. Paginate
        pass

    def get_by_status(self, status: str, page: int = 1, per_page: int = 20):
        """
        List workflows filtered by status (pending, approved, rejected, cancelled).
        """
        # TODO: Implement paginated query
        pass


class ApprovalStepRepository(BaseRepository):
    """Queries for individual approval steps."""

    model = ApprovalStep

    def __init__(self, db: Session):
        # TODO: Call super().__init__(db)
        pass

    def get_current_step(self, workflow_id: str):
        """
        Fetch the step that matches the workflow's current_step number.
        """
        # TODO: Implement:
        #   1. Fetch the parent workflow to get current_step
        #   2. Query ApprovalStep where workflow_id AND step_number == current_step
        #   3. Return the step
        pass

    def get_steps_for_workflow(self, workflow_id: str):
        """
        Return all steps for a workflow, ordered by step_number.
        """
        # TODO: Query ApprovalStep where workflow_id, order_by step_number
        pass
