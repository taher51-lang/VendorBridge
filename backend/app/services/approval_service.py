"""
VendorBridge ERP – Approval Service
=====================================
Business logic for multi-step approval workflows.
"""

from sqlalchemy.orm import Session

from app.repositories.approval_repo import ApprovalWorkflowRepository, ApprovalStepRepository
from app.repositories.quotation_repo import QuotationRepository
from app.models.approval import ApprovalWorkflow, ApprovalStep
from app.services.notification_service import NotificationService


class ApprovalService:
    """
    Orchestrates the approval pipeline for selected quotations.
    """

    def __init__(self, db: Session):
        """
        Initialize repositories and helpers.
        """
        self.db = db
        self.workflow_repo = ApprovalWorkflowRepository(db)
        self.step_repo = ApprovalStepRepository(db)
        self.quotation_repo = QuotationRepository(db)
        self.notification_svc = NotificationService(db)

    def initiate_workflow(self, data: dict, initiator_id: str):
        """
        Create an approval workflow for a selected quotation.
        """
        from app.exceptions import NotFoundError, ConflictError, BusinessLogicError

        # 1. Verify quotation exists and status == 'selected'
        quotation = self.quotation_repo.get_by_id(data['quotation_id'])
        if not quotation:
            raise NotFoundError("Quotation not found")
        if quotation.status != 'selected':
            raise BusinessLogicError("Quotation must be selected first")

        # 2. Check no existing workflow for this quotation
        existing = self.workflow_repo.get_by_quotation(quotation.id)
        if existing:
            raise ConflictError("Quotation already has an approval workflow")

        # 3. Create ApprovalWorkflow with total_steps = len(steps)
        workflow = ApprovalWorkflow(
            quotation_id=quotation.id,
            initiated_by=initiator_id,
            current_step=1,
            total_steps=len(data['steps']),
            status='pending'
        )

        # 4. Create ApprovalStep instances for each step
        for step_data in data['steps']:
            step = ApprovalStep(
                step_number=step_data['step_number'],
                approver_id=step_data['approver_id'],
                action='pending',
                due_at=step_data.get('due_at')
            )
            workflow.steps.append(step)

        # 5. Persist
        self.workflow_repo.create(workflow)

        # 6. Notify the first step's approver
        first_step = next((s for s in workflow.steps if s.step_number == 1), None)
        if first_step:
            self.notification_svc.notify_approval_required(workflow, first_step.approver_id)

        # 7. Log activity
        self.notification_svc.log_activity(
            actor_id=initiator_id,
            entity_type='approval_workflow',
            entity_id=workflow.id,
            action='initiated'
        )

        # 8. Return workflow
        return workflow

    def get_workflow(self, workflow_id: str):
        """Fetch a workflow with all its steps."""
        from app.exceptions import NotFoundError
        workflow = self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise NotFoundError("Workflow not found")
        return workflow

    def get_workflow_by_quotation(self, quotation_id: str):
        """Fetch the workflow for a given quotation."""
        return self.workflow_repo.get_by_quotation(quotation_id)

    def process_step(self, workflow_id: str, approver_id: str, action: str, remarks: str = None):
        """
        Record an approver's decision on the current step.
        """
        from datetime import datetime, timezone
        from app.exceptions import NotFoundError, ForbiddenError, BusinessLogicError

        # 1. Fetch workflow → validate status == 'pending'
        workflow = self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise NotFoundError("Workflow not found")
        if workflow.status != 'pending':
            raise BusinessLogicError("Workflow is not pending")

        # 2. Fetch current step via step_repo.get_current_step()
        step = self.step_repo.get_current_step(workflow_id)
        if not step:
            raise NotFoundError("Current step not found")

        # 3. Validate step.approver_id == approver_id
        if step.approver_id != approver_id:
            raise ForbiddenError("You are not the assigned approver for the current step")

        # 4. Set step.action = action, step.acted_at = utcnow
        step.action = action
        step.acted_at = datetime.now(timezone.utc)
        if remarks:
            step.remarks = remarks

        # 5. If action == 'approved':
        if action == 'approved':
            # a. Call workflow.advance_step()
            workflow.advance_step()
            
            # b. If workflow.is_complete() → trigger PO creation
            if workflow.is_complete():
                # Notify vendor
                self.notification_svc.create_notification(
                    user_id=workflow.quotation.vendor.user_id,
                    type='quotation_approved',
                    title=f"Quotation Fully Approved: {workflow.quotation.quote_number}",
                    body=f"Your quotation {workflow.quotation.quote_number} has been fully approved.",
                    entity_type='quotation',
                    entity_id=workflow.quotation_id
                )
                
                # Trigger PO creation
                try:
                    from app.services.po_service import PurchaseOrderService
                    po_service = PurchaseOrderService(self.db)
                    po_service.create_po(
                        quotation_id=workflow.quotation_id,
                        data={},
                        created_by=workflow.initiated_by
                    )
                except Exception as e:
                    import logging
                    logging.exception("Failed to automatically create PO upon approval workflow completion:")
            else:
                # c. Else → notify next step's approver
                next_step = self.step_repo.get_current_step(workflow_id)
                if next_step:
                    self.notification_svc.notify_approval_required(workflow, next_step.approver_id)

        # 6. If action == 'rejected':
        elif action == 'rejected':
            # a. Set workflow.status = 'rejected', workflow.completed_at = utcnow
            workflow.status = 'rejected'
            workflow.completed_at = datetime.now(timezone.utc)
            
            # Reject the quotation
            workflow.quotation.status = 'rejected'
            
            # b. Notify initiator of rejection
            self.notification_svc.create_notification(
                user_id=workflow.initiated_by,
                type='workflow_rejected',
                title=f"Workflow Rejected: {workflow.quotation.quote_number}",
                body=f"The approval workflow for quotation {workflow.quotation.quote_number} was rejected by approver.",
                entity_type='approval_workflow',
                entity_id=workflow.id
            )

        # 8. Persist
        self.workflow_repo.update(workflow)

        # 9. Log activity
        self.notification_svc.log_activity(
            actor_id=approver_id,
            entity_type='approval_workflow',
            entity_id=workflow.id,
            action=action,
            metadata={'remarks': remarks}
        )
        return workflow

    def cancel_workflow(self, workflow_id: str, user_id: str):
        """
        Cancel an in-progress workflow.
        """
        from datetime import datetime, timezone
        from app.exceptions import NotFoundError, ForbiddenError, BusinessLogicError

        # 1. Fetch workflow → validate status == 'pending'
        workflow = self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise NotFoundError("Workflow not found")
        if workflow.status != 'pending':
            raise BusinessLogicError("Workflow is not pending")

        # Check authorization: initiator or admin
        from app.models.user import User
        user = self.db.query(User).filter(User.id == user_id).first()
        is_admin = user.role == 'admin' if user else False
        if workflow.initiated_by != user_id and not is_admin:
            raise ForbiddenError("You are not authorized to cancel this workflow")

        # 2. Set status = 'cancelled', completed_at = utcnow
        workflow.status = 'cancelled'
        workflow.completed_at = datetime.now(timezone.utc)

        # 3. Persist, notify, log
        self.workflow_repo.update(workflow)

        # Notify current step's approver
        current_step = self.step_repo.get_current_step(workflow_id)
        if current_step:
            self.notification_svc.create_notification(
                user_id=current_step.approver_id,
                type='workflow_cancelled',
                title=f"Workflow Cancelled: {workflow.quotation.quote_number}",
                body=f"Approval workflow for quotation {workflow.quotation.quote_number} was cancelled.",
                entity_type='approval_workflow',
                entity_id=workflow.id
            )

        self.notification_svc.log_activity(
            actor_id=user_id,
            entity_type='approval_workflow',
            entity_id=workflow.id,
            action='cancelled'
        )
        return workflow

    def list_pending_approvals(self, approver_id: str, page: int = 1, per_page: int = 20):
        """
        List workflows awaiting this approver's action.
        """
        results, total = self.workflow_repo.get_pending_for_approver(approver_id, page, per_page)
        return results, total

