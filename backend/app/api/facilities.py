# File: backend/app/api/facilities.py
# Description: REST API router for health facilities management, geolocation, and district overview

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.app.database import get_db
from backend.app.models.facility import Facility
from backend.app.models.inventory import MedicineStock
from backend.app.models.beds import Bed
from backend.app.models.staff_attendance import DoctorStaff
from backend.app.schemas.facility import FacilityCreate, FacilityUpdate, FacilityResponse

router = APIRouter(prefix="/facilities", tags=["Facilities"])

@router.get("", response_model=List[FacilityResponse])
async def list_facilities(
    block_name: Optional[str] = None,
    facility_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Facility)
    if block_name:
        query = query.where(Facility.block_name == block_name)
    if facility_type:
        query = query.where(Facility.facility_type == facility_type)
    if status:
        query = query.where(Facility.operational_status == status)
    
    query = query.order_by(Facility.distress_score.desc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/summary")
async def get_district_summary(db: AsyncSession = Depends(get_db)):
    """Aggregates district-wide operational KPIs across all PHCs and CHCs"""
    # Total facilities
    fac_res = await db.execute(select(Facility))
    facilities = fac_res.scalars().all()
    total_facilities = len(facilities)
    
    # Bed stats
    bed_res = await db.execute(select(Bed))
    beds = bed_res.scalars().all()
    total_beds = len(beds)
    occupied_beds = len([b for b in beds if b.status == "occupied"])
    bed_occupancy_pct = round((occupied_beds / max(1, total_beds)) * 100, 1)
    
    # Staff attendance
    staff_res = await db.execute(select(DoctorStaff))
    staff_members = staff_res.scalars().all()
    total_staff = len(staff_members)
    present_staff = len([s for s in staff_members if s.attendance_status == "Present"])
    doctor_attendance_pct = round((present_staff / max(1, total_staff)) * 100, 1)
    
    # Critical stocks
    stock_res = await db.execute(select(MedicineStock))
    stocks = stock_res.scalars().all()
    critical_stocks = [s for s in stocks if s.current_quantity < s.reorder_level]
    
    # Red flagged facilities (HFDI >= 65)
    critical_distress_centres = [f for f in facilities if f.distress_score >= 65.0]

    return {
        "total_facilities": total_facilities,
        "phc_count": len([f for f in facilities if f.facility_type == "PHC"]),
        "chc_count": len([f for f in facilities if f.facility_type == "CHC"]),
        "total_beds": total_beds,
        "occupied_beds": occupied_beds,
        "bed_occupancy_pct": bed_occupancy_pct,
        "total_doctors_staff": total_staff,
        "present_doctors_staff": present_staff,
        "doctor_attendance_pct": doctor_attendance_pct,
        "critical_stockout_items": len(critical_stocks),
        "red_flagged_centres": len(critical_distress_centres)
    }

@router.get("/{facility_id}", response_model=FacilityResponse)
async def get_facility(facility_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Facility).where(Facility.id == facility_id))
    facility = res.scalar_one_or_none()
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
    return facility

@router.post("", response_model=FacilityResponse)
async def create_facility(payload: FacilityCreate, db: AsyncSession = Depends(get_db)):
    facility = Facility(**payload.model_dump())
    db.add(facility)
    await db.commit()
    await db.refresh(facility)
    return facility

