# File: backend/app/models/leave_management.py
# Description: SQLAlchemy ORM models for staff leave management including leave types, requests,
# multi-stage approvals, leave balances, and shift coverage tracking for SwasthyaGrid AI

import uuid
import json
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Date,
    ForeignKey, Float, Text, JSON
)
from app.database import Base


class LeaveType(Base):
    """Defines categories of leave with their rules and approval chain"""
    __tablename__ = "leave_types"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # e.g. Annual, Sick, Casual, Emergency, Maternity, Paternity, Study
    name = Column(String(80), nullable=False, unique=True)
    max_days_per_year = Column(Integer, nullable=False, default=12)
    # JSON array of role strings that must approve in order, e.g. ["Medical Officer", "HR Admin"]
    requires_approval_stages = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class LeaveRequest(Base):
    """A staff member's leave application with full lifecycle tracking"""
    __tablename__ = "leave_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # FK to DoctorStaff (staff_attendance model)
    staff_id = Column(String(36), ForeignKey("doctor_staff.id", ondelete="CASCADE"),
                      nullable=False, index=True)
    leave_type_id = Column(String(36), ForeignKey("leave_types.id", ondelete="RESTRICT"),
                           nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_days = Column(Float, nullable=False, default=1.0)  # supports half-days
    reason = Column(Text, nullable=False)

    # Status workflow: PENDING -> APPROVED_L1 -> APPROVED_L2 -> FULLY_APPROVED | REJECTED | CANCELLED
    status = Column(String(30), nullable=False, default="PENDING", index=True)

    # Emergency contact during leave
    emergency_contact = Column(String(120), nullable=True)
    # Who will cover duties
    cover_arrangement = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class LeaveApproval(Base):
    """Audit trail of each approval/rejection action per leave request stage"""
    __tablename__ = "leave_approvals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    leave_request_id = Column(String(36), ForeignKey("leave_requests.id", ondelete="CASCADE"),
                              nullable=False, index=True)
    # Approver user identifier (user_id from auth system, or staff_id)
    approver_user_id = Column(String(36), nullable=False)
    approver_name = Column(String(150), nullable=True)   # denormalized for display
    approver_role = Column(String(80), nullable=True)    # role at time of approval
    approval_stage = Column(Integer, nullable=False)      # 1, 2, or 3
    action = Column(String(20), nullable=False)           # APPROVED | REJECTED
    comments = Column(Text, nullable=True)
    acted_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class LeaveBalance(Base):
    """Per-staff per-leave-type annual balance tracking"""
    __tablename__ = "leave_balances"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    staff_id = Column(String(36), ForeignKey("doctor_staff.id", ondelete="CASCADE"),
                      nullable=False, index=True)
    leave_type_id = Column(String(36), ForeignKey("leave_types.id", ondelete="CASCADE"),
                           nullable=False)
    year = Column(Integer, nullable=False)               # e.g. 2025
    total_allocated = Column(Float, nullable=False, default=0.0)
    used = Column(Float, nullable=False, default=0.0)    # from FULLY_APPROVED requests
    pending = Column(Float, nullable=False, default=0.0) # from PENDING/APPROVED_L1/L2 requests
    remaining = Column(Float, nullable=False, default=0.0)  # allocated - used - pending


class ShiftCoverage(Base):
    """Records which staff member is covering a specific shift during a colleague's leave"""
    __tablename__ = "shift_coverage"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    leave_request_id = Column(String(36), ForeignKey("leave_requests.id", ondelete="CASCADE"),
                              nullable=False, index=True)
    # The staff member who agreed to cover
    covering_staff_id = Column(String(36), ForeignKey("doctor_staff.id", ondelete="CASCADE"),
                                nullable=False)
    shift_date = Column(Date, nullable=False)
    # Whether the covering staff confirmed the arrangement
    confirmed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
