# File: backend/app/api/interventions.py
# Description: REST API router for district magistrate / CMO administrative interventions and automated facility distress flags

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.facility import Facility
from app.models.alerts_interventions import InterventionAlert
from app.schemas.alerts_interventions import (
    InterventionAlertCreate, InterventionActionRequest, InterventionAlertResponse
)
from app.utils.websocket_manager import ws_manager

router = APIRouter(prefix="/interventions", tags=["District Administrative Interventions"])

@router.get("", response_model=List[InterventionAlertResponse])
async def list_interventions(
    facility_id: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(InterventionAlert)
    if facility_id:
        stmt = stmt.where(InterventionAlert.facility_id == facility_id)
    if status:
        stmt = stmt.where(InterventionAlert.status == status)
    if severity:
        stmt = stmt.where(InterventionAlert.severity == severity)
        
    stmt = stmt.order_by(InterventionAlert.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=InterventionAlertResponse)
async def create_intervention_alert(payload: InterventionAlertCreate, db: AsyncSession = Depends(get_db)):
    alert = InterventionAlert(**payload.model_dump())
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    
    await ws_manager.broadcast_json({
        "event": "NEW_DISTRICT_ALERT",
        "alert_id": alert.id,
        "facility_id": alert.facility_id,
        "severity": alert.severity,
        "title": alert.title
    })
    
    return alert

@router.post("/{alert_id}/dispatch", response_model=InterventionAlertResponse)
async def dispatch_administrative_action(
    alert_id: str,
    payload: InterventionActionRequest,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(InterventionAlert).where(InterventionAlert.id == alert_id))
    alert = res.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert record not found")
        
    alert.status = payload.status
    alert.admin_notes = payload.admin_notes
    alert.dispatched_by = payload.dispatched_by
    if payload.status == "resolved":
        alert.resolved_at = datetime.utcnow()
        
    await db.commit()
    await db.refresh(alert)
    
    await ws_manager.broadcast_json({
        "event": "ADMIN_ACTION_DISPATCHED",
        "alert_id": alert.id,
        "status": alert.status,
        "dispatched_by": alert.dispatched_by
    })
    
    return alert

