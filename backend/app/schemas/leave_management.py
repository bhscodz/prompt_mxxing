# File: backend/app/schemas/leave_management.py
# Description: Pydantic v2 schemas for all leave management API endpoints including requests,
# approvals, balances, calendar views, and coverage gap reporting for SwasthyaGrid AI

from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List, Any
from datetime import date, datetime


# ─────────────────────────────────────────────────
# Leave Type Schemas
# ─────────────────────────────────────────────────

class LeaveTypeBase(BaseModel):
    name: str
    max_days_per_year: int = 12
    # List of role strings required to approve in sequence
    requires_approval_stages: List[str] = []
    is_active: bool = True


class LeaveTypeCreate(LeaveTypeBase):
    pass


class LeaveTypeResponse(LeaveTypeBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────
# Leave Request Schemas
# ─────────────────────────────────────────────────

class LeaveRequestCreate(BaseModel):
    staff_id: str
    leave_type_id: str
    start_date: date
    end_date: date
    total_days: float = 1.0
    reason: str
    emergency_contact: Optional[str] = None
    cover_arrangement: Optional[str] = None

    @field_validator("total_days")
    @classmethod
    def days_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("total_days must be greater than 0")
        return v


class LeaveApprovalSummary(BaseModel):
    """Compact approval trail item for embedding in request detail"""
    id: str
    approver_user_id: str
    approver_name: Optional[str] = None
    approver_role: Optional[str] = None
    approval_stage: int
    action: str
    comments: Optional[str] = None
    acted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeaveRequestResponse(BaseModel):
    id: str
    staff_id: str
    leave_type_id: str
    start_date: date
    end_date: date
    total_days: float
    reason: str
    status: str
    emergency_contact: Optional[str] = None
    cover_arrangement: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # Populated in detail endpoint
    approvals: Optional[List[LeaveApprovalSummary]] = None
    # Staff/leave type names denormalized for frontend display
    staff_name: Optional[str] = None
    leave_type_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LeaveRequestListResponse(BaseModel):
    total: int
    items: List[LeaveRequestResponse]


# ─────────────────────────────────────────────────
# Approval / Reject / Cancel Action Schemas
# ─────────────────────────────────────────────────

class ApproveLeaveRequest(BaseModel):
    approver_user_id: str
    approver_name: Optional[str] = None
    approver_role: Optional[str] = None
    comments: Optional[str] = None


class RejectLeaveRequest(BaseModel):
    approver_user_id: str
    approver_name: Optional[str] = None
    approver_role: Optional[str] = None
    comments: str  # mandatory for rejection


class CancelLeaveRequest(BaseModel):
    cancelled_by_staff_id: str
    reason: Optional[str] = None


# ─────────────────────────────────────────────────
# Leave Balance Schemas
# ─────────────────────────────────────────────────

class LeaveBalanceResponse(BaseModel):
    id: str
    staff_id: str
    leave_type_id: str
    leave_type_name: Optional[str] = None
    year: int
    total_allocated: float
    used: float
    pending: float
    remaining: float

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────
# Calendar View Schemas
# ─────────────────────────────────────────────────

class CalendarAbsenceEntry(BaseModel):
    """Represents a staff absence on a specific date for the monthly calendar"""
    staff_id: str
    staff_name: str
    role: str
    leave_type: str
    leave_request_id: str
    facility_id: Optional[str] = None


class CalendarDayResponse(BaseModel):
    """Aggregated absence data for a single calendar day"""
    date: str               # ISO format yyyy-mm-dd
    absences: List[CalendarAbsenceEntry] = []


class CalendarResponse(BaseModel):
    facility_id: Optional[str] = None
    month: int
    year: int
    days: List[CalendarDayResponse]


# ─────────────────────────────────────────────────
# Coverage Gap Schemas
# ─────────────────────────────────────────────────

class CoverageGapEntry(BaseModel):
    """A day where minimum staffing levels are not met"""
    date: str
    facility_id: str
    facility_name: Optional[str] = None
    role: str               # e.g. "Medical Officer", "Staff Nurse"
    required_count: int
    present_count: int
    on_leave_count: int
    gap: int                # required - present


class CoverageGapResponse(BaseModel):
    facility_id: Optional[str] = None
    check_date: str
    gaps: List[CoverageGapEntry]


# ─────────────────────────────────────────────────
# Shift Coverage Schemas
# ─────────────────────────────────────────────────

class ShiftCoverageCreate(BaseModel):
    leave_request_id: str
    covering_staff_id: str
    shift_date: date
    confirmed: bool = False


class ShiftCoverageResponse(BaseModel):
    id: str
    leave_request_id: str
    covering_staff_id: str
    shift_date: date
    confirmed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
