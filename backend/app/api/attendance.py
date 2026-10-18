# File: backend/app/api/attendance.py
# Description: REST API router for doctor and clinical staff attendance, biometric punch logs, and specialty coverage

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import get_db
from backend.app.models.staff_attendance import DoctorStaff
from backend.app.schemas.staff_attendance import (
    DoctorStaffCreate, PunchInRequest, DoctorStaffResponse
)
from backend.app.utils.websocket_manager import ws_manager

router = APIRouter(prefix="/attendance", tags=["Doctor & Staff Attendance"])

@router.get("", response_model=List[DoctorStaffResponse])
async def list_staff_attendance(
    facility_id: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(DoctorStaff)
    if facility_id:
        stmt = stmt.where(DoctorStaff.facility_id == facility_id)
    if role:
        stmt = stmt.where(DoctorStaff.role.ilike(f"%{role}%"))
    if status:
        stmt = stmt.where(DoctorStaff.attendance_status == status)
        
    stmt = stmt.order_by(DoctorStaff.role, DoctorStaff.full_name)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/punch", response_model=DoctorStaffResponse)
async def record_biometric_punch(
    payload: PunchInRequest,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(DoctorStaff).where(DoctorStaff.id == payload.staff_id))
    staff = res.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff record not found")
        
    staff.attendance_status = payload.status
    if payload.status == "Present":
        staff.is_on_duty_today = True
        staff.biometric_punch_in = datetime.utcnow()
    else:
        staff.is_on_duty_today = False
        
    await db.commit()
    await db.refresh(staff)
    
    await ws_manager.broadcast_json({
        "event": "STAFF_ATTENDANCE_PUNCH",
        "staff_id": staff.id,
        "name": staff.full_name,
        "role": staff.role,
        "status": staff.attendance_status
    })
    
    return staff

