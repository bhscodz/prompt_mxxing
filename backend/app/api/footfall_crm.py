# File: backend/app/api/footfall_crm.py
# Description: REST API router for Patient CRM, digital OPD token queue, emergency triage, and clinical notes

import time
from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.patient_crm import Patient, OPDVisit
from app.models.facility import Facility
from app.schemas.patient_crm import (
    PatientCreate, PatientResponse, OPDVisitCreate, OPDVisitUpdate, OPDVisitResponse
)
from app.utils.websocket_manager import ws_manager

router = APIRouter(prefix="/crm", tags=["Patient CRM & Footfall"])

@router.get("/patients", response_model=List[PatientResponse])
async def search_patients(
    query: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Patient)
    if query:
        stmt = stmt.where(
            (Patient.full_name.ilike(f"%{query}%")) | 
            (Patient.abha_id.ilike(f"%{query}%")) |
            (Patient.phone.ilike(f"%{query}%"))
        )
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/patients", response_model=PatientResponse)
async def create_patient(payload: PatientCreate, db: AsyncSession = Depends(get_db)):
    patient = Patient(**payload.model_dump())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient

@router.get("/opd-visits", response_model=List[OPDVisitResponse])
async def list_opd_visits(
    facility_id: Optional[str] = None,
    status: Optional[str] = None,
    triage: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(OPDVisit)
    if facility_id:
        stmt = stmt.where(OPDVisit.facility_id == facility_id)
    if status:
        stmt = stmt.where(OPDVisit.status == status)
    if triage:
        stmt = stmt.where(OPDVisit.triage_category == triage)
        
    stmt = stmt.order_by(
        # Prioritize immediate red triage first
        OPDVisit.triage_category.desc(),
        OPDVisit.created_at.desc()
    )
    result = await db.execute(stmt)
    visits = result.scalars().all()
    
    # Attach patient models
    response_list = []
    for v in visits:
        pat_res = await db.execute(select(Patient).where(Patient.id == v.patient_id))
        pat = pat_res.scalar_one_or_none()
        v_dict = {c.name: getattr(v, c.name) for c in v.__table__.columns}
        v_dict["patient"] = pat
        response_list.append(OPDVisitResponse(**v_dict))
        
    return response_list

@router.post("/opd-visits", response_model=OPDVisitResponse)
async def register_opd_visit(payload: OPDVisitCreate, db: AsyncSession = Depends(get_db)):
    # If patient_id not provided, check if patient_data provided
    patient_id = payload.patient_id
    if not patient_id:
        if not payload.patient_data:
            raise HTTPException(status_code=400, detail="Either patient_id or patient_data must be provided")
        new_patient = Patient(**payload.patient_data.model_dump())
        db.add(new_patient)
        await db.flush()
        patient_id = new_patient.id
        
    pat_res = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = pat_res.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient record not found")
        
    # Generate sequential token number
    token_str = f"T-{int(time.time()) % 1000:03d}"
    
    visit = OPDVisit(
        patient_id=patient_id,
        facility_id=payload.facility_id,
        token_number=token_str,
        triage_category=payload.triage_category,
        chief_complaint=payload.chief_complaint,
        systolic_bp=payload.systolic_bp,
        diastolic_bp=payload.diastolic_bp,
        pulse_rate=payload.pulse_rate,
        temperature_f=payload.temperature_f,
        spo2=payload.spo2,
        assigned_doctor_name=payload.assigned_doctor_name,
        status="waiting"
    )
    db.add(visit)
    await db.commit()
    await db.refresh(visit)
    
    # WebSocket broadcast
    await ws_manager.broadcast_json({
        "event": "NEW_OPD_VISIT",
        "visit_id": visit.id,
        "token_number": token_str,
        "patient_name": patient.full_name,
        "facility_id": visit.facility_id,
        "triage_category": visit.triage_category
    })
    
    v_dict = {c.name: getattr(visit, c.name) for c in visit.__table__.columns}
    v_dict["patient"] = patient
    return OPDVisitResponse(**v_dict)

@router.patch("/opd-visits/{visit_id}", response_model=OPDVisitResponse)
async def update_opd_visit(visit_id: str, payload: OPDVisitUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(OPDVisit).where(OPDVisit.id == visit_id))
    visit = res.scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="OPD visit not found")
        
    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(visit, field, val)
        
    await db.commit()
    await db.refresh(visit)
    
    pat_res = await db.execute(select(Patient).where(Patient.id == visit.patient_id))
    patient = pat_res.scalar_one_or_none()
    
    # WebSocket broadcast
    await ws_manager.broadcast_json({
        "event": "OPD_VISIT_STATUS_CHANGED",
        "visit_id": visit.id,
        "status": visit.status,
        "patient_name": patient.full_name if patient else "Patient"
    })
    
    v_dict = {c.name: getattr(visit, c.name) for c in visit.__table__.columns}
    v_dict["patient"] = patient
    return OPDVisitResponse(**v_dict)

