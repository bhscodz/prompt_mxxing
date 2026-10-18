# File: backend/app/api/beds.py
# Description: REST API router for real-time bed inventory, ward management, oxygen support, and admissions/discharges

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.beds import Bed
from app.schemas.beds import BedCreate, BedUpdate, BedAllocateRequest, BedResponse
from app.utils.websocket_manager import ws_manager

router = APIRouter(prefix="/beds", tags=["Bed Management"])

@router.get("", response_model=List[BedResponse])
async def list_beds(
    facility_id: Optional[str] = None,
    ward_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Bed)
    if facility_id:
        stmt = stmt.where(Bed.facility_id == facility_id)
    if ward_type:
        stmt = stmt.where(Bed.ward_type == ward_type)
    if status:
        stmt = stmt.where(Bed.status == status)
        
    stmt = stmt.order_by(Bed.ward_type, Bed.bed_number)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/{bed_id}/allocate", response_model=BedResponse)
async def allocate_bed(
    bed_id: str,
    payload: BedAllocateRequest,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Bed).where(Bed.id == bed_id))
    bed = res.scalar_one_or_none()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
        
    if bed.status == "occupied":
        raise HTTPException(status_code=400, detail="Bed is already occupied")
        
    bed.status = "occupied"
    bed.allocated_patient_name = payload.patient_name
    bed.allocated_patient_id = payload.patient_id
    bed.admission_timestamp = datetime.utcnow()
    
    await db.commit()
    await db.refresh(bed)
    
    await ws_manager.broadcast_json({
        "event": "BED_OCCUPIED",
        "bed_id": bed.id,
        "bed_number": bed.bed_number,
        "ward_type": bed.ward_type,
        "patient_name": payload.patient_name
    })
    
    return bed

@router.post("/{bed_id}/discharge", response_model=BedResponse)
async def discharge_bed(
    bed_id: str,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Bed).where(Bed.id == bed_id))
    bed = res.scalar_one_or_none()
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
        
    bed.status = "available"
    bed.allocated_patient_name = None
    bed.allocated_patient_id = None
    bed.admission_timestamp = None
    
    await db.commit()
    await db.refresh(bed)
    
    await ws_manager.broadcast_json({
        "event": "BED_VACATED",
        "bed_id": bed.id,
        "bed_number": bed.bed_number,
        "ward_type": bed.ward_type
    })
    
    return bed

