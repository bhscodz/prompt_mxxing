# File: backend/app/api/leave_management.py
# Description: FastAPI REST router for Staff Leave Management in SwasthyaGrid AI.
# Handles leave requests, multi-stage approvals, calendar views, balance queries,
# coverage gap detection, and leave type administration.

import uuid
import calendar
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from backend.app.database import get_db
from backend.app.models.leave_management import (
    LeaveType, LeaveRequest, LeaveApproval, LeaveBalance, ShiftCoverage
)
from backend.app.models.staff_attendance import DoctorStaff
from backend.app.schemas.leave_management import (
    LeaveTypeCreate, LeaveTypeResponse,
    LeaveRequestCreate, LeaveRequestResponse, LeaveRequestListResponse,
    LeaveApprovalSummary,
    ApproveLeaveRequest, RejectLeaveRequest, CancelLeaveRequest,
    LeaveBalanceResponse,
    CalendarResponse, CalendarDayResponse, CalendarAbsenceEntry,
    CoverageGapResponse, CoverageGapEntry
)

router = APIRouter(prefix="/leave", tags=["Staff Leave Management"])

# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────

# Minimum coverage requirements per role per facility per day
MINIMUM_COVERAGE = {
    "Medical Officer": 1,
    "Staff Nurse": 2,
}

LEAVE_STATUSES_APPROVED_COUNTS = ("FULLY_APPROVED",)
LEAVE_STATUSES_PENDING_COUNTS = ("PENDING", "APPROVED_L1", "APPROVED_L2")


async def _get_leave_request_or_404(req_id: str, db: AsyncSession) -> LeaveRequest:
    """Fetch a LeaveRequest by id or raise 404"""
    result = await db.execute(select(LeaveRequest).where(LeaveRequest.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found")
    return req


async def _recalculate_balance(
    staff_id: str, leave_type_id: str, year: int, db: AsyncSession
) -> None:
    """Recompute LeaveBalance for a staff/leave_type/year from scratch"""
    # Fetch leave type allocation
    lt_res = await db.execute(select(LeaveType).where(LeaveType.id == leave_type_id))
    leave_type = lt_res.scalar_one_or_none()
    if not leave_type:
        return

    # Count used days (fully approved)
    used_res = await db.execute(
        select(func.coalesce(func.sum(LeaveRequest.total_days), 0.0)).where(
            and_(
                LeaveRequest.staff_id == staff_id,
                LeaveRequest.leave_type_id == leave_type_id,
                LeaveRequest.status == "FULLY_APPROVED",
                func.strftime("%Y", LeaveRequest.start_date) == str(year)
            )
        )
    )
    used = float(used_res.scalar() or 0.0)

    # Count pending days
    pending_res = await db.execute(
        select(func.coalesce(func.sum(LeaveRequest.total_days), 0.0)).where(
            and_(
                LeaveRequest.staff_id == staff_id,
                LeaveRequest.leave_type_id == leave_type_id,
                LeaveRequest.status.in_(list(LEAVE_STATUSES_PENDING_COUNTS)),
                func.strftime("%Y", LeaveRequest.start_date) == str(year)
            )
        )
    )
    pending = float(pending_res.scalar() or 0.0)

    allocated = float(leave_type.max_days_per_year)
    remaining = max(0.0, allocated - used - pending)

    # Upsert balance record
    bal_res = await db.execute(
        select(LeaveBalance).where(
            and_(
                LeaveBalance.staff_id == staff_id,
                LeaveBalance.leave_type_id == leave_type_id,
                LeaveBalance.year == year
            )
        )
    )
    balance = bal_res.scalar_one_or_none()

    if balance:
        balance.total_allocated = allocated
        balance.used = used
        balance.pending = pending
        balance.remaining = remaining
    else:
        balance = LeaveBalance(
            id=str(uuid.uuid4()),
            staff_id=staff_id,
            leave_type_id=leave_type_id,
            year=year,
            total_allocated=allocated,
            used=used,
            pending=pending,
            remaining=remaining
        )
        db.add(balance)


async def _enrich_request(req: LeaveRequest, db: AsyncSession) -> dict:
    """Enrich a LeaveRequest ORM object with staff name and leave type name"""
    d = {c.name: getattr(req, c.name) for c in req.__table__.columns}

    # Fetch staff name
    staff_res = await db.execute(
        select(DoctorStaff.full_name).where(DoctorStaff.id == req.staff_id)
    )
    d["staff_name"] = staff_res.scalar_one_or_none()

    # Fetch leave type name
    lt_res = await db.execute(
        select(LeaveType.name).where(LeaveType.id == req.leave_type_id)
    )
    d["leave_type_name"] = lt_res.scalar_one_or_none()
    d["approvals"] = None
    return d


# ──────────────────────────────────────────────────────────────────
# Leave Types
# ──────────────────────────────────────────────────────────────────

@router.get("/types", response_model=List[LeaveTypeResponse], summary="List all leave types")
async def list_leave_types(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Returns all configured leave types. Filter by active status."""
    stmt = select(LeaveType)
    if active_only:
        stmt = stmt.where(LeaveType.is_active == True)
    stmt = stmt.order_by(LeaveType.name)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/types", response_model=LeaveTypeResponse, status_code=201,
             summary="Create a new leave type (DISTRICT_ADMIN only)")
async def create_leave_type(
    payload: LeaveTypeCreate,
    db: AsyncSession = Depends(get_db)
):
    """Creates a new leave type. Should be restricted to DISTRICT_ADMIN role via auth middleware."""
    # Check name uniqueness
    existing = await db.execute(
        select(LeaveType).where(LeaveType.name == payload.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Leave type '{payload.name}' already exists")

    lt = LeaveType(
        id=str(uuid.uuid4()),
        name=payload.name,
        max_days_per_year=payload.max_days_per_year,
        requires_approval_stages=payload.requires_approval_stages,
        is_active=payload.is_active
    )
    db.add(lt)
    await db.commit()
    await db.refresh(lt)
    return lt


# ──────────────────────────────────────────────────────────────────
# Leave Requests — Submit & List
# ──────────────────────────────────────────────────────────────────

@router.post("/request", response_model=LeaveRequestResponse, status_code=201,
             summary="Submit a new leave request")
async def submit_leave_request(
    payload: LeaveRequestCreate,
    db: AsyncSession = Depends(get_db)
):
    """Validates staff existence, leave type, balance, then creates a PENDING leave request."""
    # Validate staff exists
    staff_res = await db.execute(
        select(DoctorStaff).where(DoctorStaff.id == payload.staff_id)
    )
    staff = staff_res.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    # Validate leave type exists and is active
    lt_res = await db.execute(
        select(LeaveType).where(
            and_(LeaveType.id == payload.leave_type_id, LeaveType.is_active == True)
        )
    )
    leave_type = lt_res.scalar_one_or_none()
    if not leave_type:
        raise HTTPException(status_code=404, detail="Leave type not found or inactive")

    # Check dates are logical
    if payload.start_date > payload.end_date:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date")

    # Check for overlapping requests for same staff
    overlap_res = await db.execute(
        select(LeaveRequest).where(
            and_(
                LeaveRequest.staff_id == payload.staff_id,
                LeaveRequest.status.not_in(["REJECTED", "CANCELLED"]),
                LeaveRequest.start_date <= payload.end_date,
                LeaveRequest.end_date >= payload.start_date
            )
        )
    )
    if overlap_res.scalar_one_or_none():
        raise HTTPException(status_code=409,
                            detail="An overlapping leave request already exists for this period")

    # Check balance availability
    year = payload.start_date.year
    bal_res = await db.execute(
        select(LeaveBalance).where(
            and_(
                LeaveBalance.staff_id == payload.staff_id,
                LeaveBalance.leave_type_id == payload.leave_type_id,
                LeaveBalance.year == year
            )
        )
    )
    balance = bal_res.scalar_one_or_none()
    available = float(leave_type.max_days_per_year)
    if balance:
        available = balance.remaining
    if payload.total_days > available:
        raise HTTPException(
            status_code=422,
            detail=f"Insufficient leave balance. Requested: {payload.total_days} days, Available: {available} days"
        )

    # Create request
    leave_req = LeaveRequest(
        id=str(uuid.uuid4()),
        staff_id=payload.staff_id,
        leave_type_id=payload.leave_type_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        total_days=payload.total_days,
        reason=payload.reason,
        status="PENDING",
        emergency_contact=payload.emergency_contact,
        cover_arrangement=payload.cover_arrangement
    )
    db.add(leave_req)

    # Recalculate balance (pending will increase)
    await db.flush()  # ensure leave_req.id is available
    await _recalculate_balance(payload.staff_id, payload.leave_type_id, year, db)

    await db.commit()
    await db.refresh(leave_req)

    enriched = await _enrich_request(leave_req, db)
    return LeaveRequestResponse(**enriched)


@router.get("/requests", response_model=LeaveRequestListResponse,
            summary="List leave requests with filters")
async def list_leave_requests(
    status: Optional[str] = Query(None, description="Filter by status e.g. PENDING"),
    staff_id: Optional[str] = Query(None),
    facility_id: Optional[str] = Query(None, description="Filter by staff facility"),
    from_date: Optional[date] = Query(None, description="Start of date range filter"),
    to_date: Optional[date] = Query(None, description="End of date range filter"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Returns paginated list of leave requests with optional filters."""
    # Build joined query to allow facility_id filter
    stmt = select(LeaveRequest)

    if facility_id:
        # Join to DoctorStaff to filter by facility
        stmt = stmt.join(DoctorStaff, LeaveRequest.staff_id == DoctorStaff.id).where(
            DoctorStaff.facility_id == facility_id
        )

    filters = []
    if status:
        filters.append(LeaveRequest.status == status.upper())
    if staff_id:
        filters.append(LeaveRequest.staff_id == staff_id)
    if from_date:
        filters.append(LeaveRequest.start_date >= from_date)
    if to_date:
        filters.append(LeaveRequest.end_date <= to_date)

    if filters:
        stmt = stmt.where(and_(*filters))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total = total_res.scalar() or 0

    stmt = stmt.order_by(LeaveRequest.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    requests = result.scalars().all()

    items = []
    for req in requests:
        enriched = await _enrich_request(req, db)
        items.append(LeaveRequestResponse(**enriched))

    return LeaveRequestListResponse(total=total, items=items)


@router.get("/requests/{request_id}", response_model=LeaveRequestResponse,
            summary="Get leave request detail with full approval trail")
async def get_leave_request(
    request_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Returns a single leave request with all approval/rejection history."""
    req = await _get_leave_request_or_404(request_id, db)
    enriched = await _enrich_request(req, db)

    # Fetch approval trail
    approvals_res = await db.execute(
        select(LeaveApproval)
        .where(LeaveApproval.leave_request_id == request_id)
        .order_by(LeaveApproval.approval_stage, LeaveApproval.acted_at)
    )
    approvals = approvals_res.scalars().all()
    enriched["approvals"] = [LeaveApprovalSummary.model_validate(a) for a in approvals]

    return LeaveRequestResponse(**enriched)


# ──────────────────────────────────────────────────────────────────
# Approval Actions
# ──────────────────────────────────────────────────────────────────

@router.post("/requests/{request_id}/approve", response_model=LeaveRequestResponse,
             summary="Approve a leave request (multi-stage)")
async def approve_leave_request(
    request_id: str,
    payload: ApproveLeaveRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Multi-stage approval logic:
    - PENDING → APPROVED_L1 (stage 1 approval)
    - APPROVED_L1 → APPROVED_L2 (stage 2 approval)
    - APPROVED_L2 → FULLY_APPROVED or FULLY_APPROVED if only 1 stage required
    The number of required stages is determined by the leave type's requires_approval_stages list.
    """
    req = await _get_leave_request_or_404(request_id, db)

    if req.status in ("FULLY_APPROVED", "REJECTED", "CANCELLED"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve a request with status '{req.status}'"
        )

    # Fetch leave type to know total stages
    lt_res = await db.execute(select(LeaveType).where(LeaveType.id == req.leave_type_id))
    leave_type = lt_res.scalar_one_or_none()
    if not leave_type:
        raise HTTPException(status_code=404, detail="Leave type not found")

    total_stages = max(len(leave_type.requires_approval_stages), 1)

    # Determine current stage from status
    stage_map = {
        "PENDING": 1,
        "APPROVED_L1": 2,
        "APPROVED_L2": 3
    }
    current_stage = stage_map.get(req.status, 1)

    # Record the approval action
    approval = LeaveApproval(
        id=str(uuid.uuid4()),
        leave_request_id=req.id,
        approver_user_id=payload.approver_user_id,
        approver_name=payload.approver_name,
        approver_role=payload.approver_role,
        approval_stage=current_stage,
        action="APPROVED",
        comments=payload.comments
    )
    db.add(approval)

    # Advance status
    if current_stage >= total_stages:
        # All required stages done → fully approved
        req.status = "FULLY_APPROVED"
        # Recalculate balance: moves from pending → used
        year = req.start_date.year
        await _recalculate_balance(req.staff_id, req.leave_type_id, year, db)
    else:
        # Move to next stage
        next_status_map = {1: "APPROVED_L1", 2: "APPROVED_L2"}
        req.status = next_status_map.get(current_stage, "APPROVED_L1")

    req.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(req)

    enriched = await _enrich_request(req, db)
    return LeaveRequestResponse(**enriched)


@router.post("/requests/{request_id}/reject", response_model=LeaveRequestResponse,
             summary="Reject a leave request (mandatory comment)")
async def reject_leave_request(
    request_id: str,
    payload: RejectLeaveRequest,
    db: AsyncSession = Depends(get_db)
):
    """Rejects a leave request at any pending stage. Comment is mandatory."""
    req = await _get_leave_request_or_404(request_id, db)

    if req.status in ("FULLY_APPROVED", "REJECTED", "CANCELLED"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot reject a request with status '{req.status}'"
        )

    if not payload.comments or not payload.comments.strip():
        raise HTTPException(status_code=422, detail="A rejection comment is mandatory")

    stage_map = {"PENDING": 1, "APPROVED_L1": 2, "APPROVED_L2": 3}
    current_stage = stage_map.get(req.status, 1)

    approval = LeaveApproval(
        id=str(uuid.uuid4()),
        leave_request_id=req.id,
        approver_user_id=payload.approver_user_id,
        approver_name=payload.approver_name,
        approver_role=payload.approver_role,
        approval_stage=current_stage,
        action="REJECTED",
        comments=payload.comments
    )
    db.add(approval)

    req.status = "REJECTED"
    req.updated_at = datetime.utcnow()

    # Recalculate balance to release pending days
    year = req.start_date.year
    await _recalculate_balance(req.staff_id, req.leave_type_id, year, db)

    await db.commit()
    await db.refresh(req)

    enriched = await _enrich_request(req, db)
    return LeaveRequestResponse(**enriched)


@router.post("/requests/{request_id}/cancel", response_model=LeaveRequestResponse,
             summary="Cancel a leave request (by requester)")
async def cancel_leave_request(
    request_id: str,
    payload: CancelLeaveRequest,
    db: AsyncSession = Depends(get_db)
):
    """Allows the requesting staff member to cancel their own leave request."""
    req = await _get_leave_request_or_404(request_id, db)

    if req.status in ("REJECTED", "CANCELLED"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel a request with status '{req.status}'"
        )

    if req.staff_id != payload.cancelled_by_staff_id:
        raise HTTPException(status_code=403, detail="Only the requesting staff can cancel this request")

    req.status = "CANCELLED"
    req.updated_at = datetime.utcnow()

    # Release pending/used days back to balance
    year = req.start_date.year
    await _recalculate_balance(req.staff_id, req.leave_type_id, year, db)

    await db.commit()
    await db.refresh(req)

    enriched = await _enrich_request(req, db)
    return LeaveRequestResponse(**enriched)


# ──────────────────────────────────────────────────────────────────
# Calendar View
# ──────────────────────────────────────────────────────────────────

@router.get("/calendar", response_model=CalendarResponse,
            summary="Monthly calendar of approved absences")
async def get_leave_calendar(
    month: int = Query(..., ge=1, le=12, description="Month number 1-12"),
    year: int = Query(..., ge=2020, description="4-digit year"),
    facility_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns a full month view showing which staff are on approved leave each day.
    Optionally filtered by facility.
    """
    # First and last day of the month
    first_day = date(year, month, 1)
    last_day_num = calendar.monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)

    # Build base query for fully approved leaves in this month
    stmt = (
        select(LeaveRequest, DoctorStaff, LeaveType)
        .join(DoctorStaff, LeaveRequest.staff_id == DoctorStaff.id)
        .join(LeaveType, LeaveRequest.leave_type_id == LeaveType.id)
        .where(
            and_(
                LeaveRequest.status == "FULLY_APPROVED",
                LeaveRequest.start_date <= last_day,
                LeaveRequest.end_date >= first_day
            )
        )
    )

    if facility_id:
        stmt = stmt.where(DoctorStaff.facility_id == facility_id)

    result = await db.execute(stmt)
    rows = result.all()

    # Build a dict of date → list of absence entries
    day_map: dict[str, list] = {}
    current = first_day
    while current <= last_day:
        day_map[current.isoformat()] = []
        current += timedelta(days=1)

    for leave_req, staff, lt in rows:
        # Iterate each day of the leave period
        cur = max(leave_req.start_date, first_day)
        end = min(leave_req.end_date, last_day)
        while cur <= end:
            entry = CalendarAbsenceEntry(
                staff_id=staff.id,
                staff_name=staff.full_name,
                role=staff.role,
                leave_type=lt.name,
                leave_request_id=leave_req.id,
                facility_id=staff.facility_id
            )
            day_map[cur.isoformat()].append(entry)
            cur += timedelta(days=1)

    days = [
        CalendarDayResponse(date=d, absences=entries)
        for d, entries in sorted(day_map.items())
    ]

    return CalendarResponse(
        facility_id=facility_id,
        month=month,
        year=year,
        days=days
    )


# ──────────────────────────────────────────────────────────────────
# Leave Balances
# ──────────────────────────────────────────────────────────────────

@router.get("/balance/{staff_id}", response_model=List[LeaveBalanceResponse],
            summary="Get leave balances for a staff member")
async def get_staff_leave_balance(
    staff_id: str,
    year: Optional[int] = Query(None, description="Year (defaults to current year)"),
    db: AsyncSession = Depends(get_db)
):
    """Returns leave balance per leave type for a given staff member and year."""
    # Validate staff exists
    staff_res = await db.execute(select(DoctorStaff).where(DoctorStaff.id == staff_id))
    if not staff_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Staff member not found")

    target_year = year or datetime.utcnow().year

    # Ensure balance records exist for all active leave types
    lt_res = await db.execute(select(LeaveType).where(LeaveType.is_active == True))
    leave_types = lt_res.scalars().all()

    for lt in leave_types:
        await _recalculate_balance(staff_id, lt.id, target_year, db)

    await db.commit()

    # Fetch balances
    bal_res = await db.execute(
        select(LeaveBalance, LeaveType)
        .join(LeaveType, LeaveBalance.leave_type_id == LeaveType.id)
        .where(
            and_(
                LeaveBalance.staff_id == staff_id,
                LeaveBalance.year == target_year
            )
        )
        .order_by(LeaveType.name)
    )
    rows = bal_res.all()

    results = []
    for bal, lt in rows:
        d = {c.name: getattr(bal, c.name) for c in bal.__table__.columns}
        d["leave_type_name"] = lt.name
        results.append(LeaveBalanceResponse(**d))

    return results


# ──────────────────────────────────────────────────────────────────
# Coverage Gaps
# ──────────────────────────────────────────────────────────────────

@router.get("/coverage-gaps", response_model=CoverageGapResponse,
            summary="Identify days with insufficient staff coverage due to leaves")
async def get_coverage_gaps(
    facility_id: Optional[str] = Query(None),
    check_date: Optional[date] = Query(None, description="Specific date to check (defaults to today)"),
    db: AsyncSession = Depends(get_db)
):
    """
    For a given facility and date, checks if minimum required staff per role
    (Medical Officer: ≥1, Staff Nurse: ≥2) are available after accounting for approved leaves.
    """
    target_date = check_date or date.today()

    gaps: List[CoverageGapEntry] = []

    # Get total staff per role at the facility
    staff_stmt = select(DoctorStaff)
    if facility_id:
        staff_stmt = staff_stmt.where(DoctorStaff.facility_id == facility_id)
    staff_res = await db.execute(staff_stmt)
    all_staff = staff_res.scalars().all()

    # Staff IDs on approved leave on target_date
    leave_stmt = (
        select(LeaveRequest.staff_id)
        .where(
            and_(
                LeaveRequest.status == "FULLY_APPROVED",
                LeaveRequest.start_date <= target_date,
                LeaveRequest.end_date >= target_date
            )
        )
    )
    leave_res = await db.execute(leave_stmt)
    on_leave_ids = set(leave_res.scalars().all())

    # Fetch facility name if facility_id provided
    facility_name = None
    if facility_id:
        from backend.app.models.facility import Facility
        fac_res = await db.execute(
            select(Facility.name).where(Facility.id == facility_id)
        )
        facility_name = fac_res.scalar_one_or_none()

    # Check each role with a minimum coverage requirement
    for role, minimum in MINIMUM_COVERAGE.items():
        role_staff = [s for s in all_staff if role.lower() in s.role.lower()]
        total_for_role = len(role_staff)
        on_leave_for_role = len([s for s in role_staff if s.id in on_leave_ids])
        present = total_for_role - on_leave_for_role
        gap = minimum - present

        if gap > 0:
            gaps.append(CoverageGapEntry(
                date=target_date.isoformat(),
                facility_id=facility_id or "all",
                facility_name=facility_name,
                role=role,
                required_count=minimum,
                present_count=present,
                on_leave_count=on_leave_for_role,
                gap=gap
            ))

    return CoverageGapResponse(
        facility_id=facility_id,
        check_date=target_date.isoformat(),
        gaps=gaps
    )
