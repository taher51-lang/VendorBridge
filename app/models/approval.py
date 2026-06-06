"""
VendorBridge ERP – Approval Workflow Models
=============================================
Multi-step approval pipeline for quotations.
Flow: Quotation selected → Workflow created → Steps executed → PO issued.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, SmallInteger, Text, DateTime, ForeignKey,
    Enum as SAEnum, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import BaseModel


class ApprovalWorkflow(BaseModel, Base):
    """
    Orchestrates a sequential approval process for a quotation.
    """
    __tablename__ = "approval_workflows"

    quotation_id = Column(
        String(36),
        ForeignKey("quotations.id"),
        unique=True,
        nullable=False,
    )
    initiated_by = Column(
        String(36), ForeignKey("users.id"), nullable=False,
    )
    current_step = Column(SmallInteger, default=1, nullable=False)
    total_steps = Column(SmallInteger, default=1, nullable=False)
    status = Column(
        SAEnum(
            "pending", "approved", "rejected", "cancelled",
            name="workflow_status_enum",
        ),
        default="pending",
        index=True,
        nullable=False,
    )
    completed_at = Column(DateTime, nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    quotation = relationship(
        "Quotation", back_populates="workflow",
    )
    initiator = relationship(
        "User", back_populates="initiated_workflows",
    )
    steps = relationship(
        "ApprovalStep",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="ApprovalStep.step_number",
    )
    purchase_order = relationship(
        "PurchaseOrder", back_populates="workflow", uselist=False,
    )

    # ── Methods ───────────────────────────────────────────────────

    def is_complete(self) -> bool:
        """
        Return True if the workflow has reached a terminal state:
        - current_step exceeds total_steps, OR
        - status is one of approved, rejected, cancelled.
        """
        if self.status in ("approved", "rejected", "cancelled"):
            return True
        return self.current_step > self.total_steps

    def advance_step(self) -> None:
        """
        Increment current_step by one.
        If the new current_step exceeds total_steps, mark the
        workflow as 'approved' and record completed_at.
        """
        self.current_step += 1
        if self.current_step > self.total_steps:
            self.status = "approved"
            self.completed_at = datetime.now(timezone.utc)


class ApprovalStep(BaseModel, Base):
    """
    An individual approval action within a workflow.
    """
    __tablename__ = "approval_steps"
    __table_args__ = (
        UniqueConstraint(
            "workflow_id", "step_number",
            name="uq_workflow_step",
        ),
    )

    workflow_id = Column(
        String(36),
        ForeignKey("approval_workflows.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_number = Column(SmallInteger, nullable=False)
    approver_id = Column(
        String(36), ForeignKey("users.id"), nullable=False,
    )
    action = Column(
        SAEnum(
            "pending", "approved", "rejected",
            name="step_action_enum",
        ),
        default="pending",
        nullable=False,
    )
    remarks = Column(Text, nullable=True)
    acted_at = Column(DateTime, nullable=True)
    due_at = Column(DateTime, nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    workflow = relationship(
        "ApprovalWorkflow", back_populates="steps",
    )
    approver = relationship(
        "User", back_populates="approval_steps",
    )
