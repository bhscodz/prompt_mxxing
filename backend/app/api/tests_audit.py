# File: backend/app/api/tests_audit.py
# Description: REST API router for diagnostic test availability audits, reagent stocks, and machine status

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.diagnostic_tests import DiagnosticTest
from app.schemas.diagnostic_tests import (
    DiagnosticTestCreate, DiagnosticTestUpdate, DiagnosticTestResponse
)
from app.utils.websocket_manager import ws_manager

router = APIRouter(prefix="/diagnostic-tests", tags=["Diagnostic Audits"])

@router.get("", response_model=List[DiagnosticTestResponse])
async def list_diagnostic_audits(
    facility_id: Optional[str] = None,
    category: Optional[str] = None,
    compliant_only: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(DiagnosticTest)
    if facility_id:
        stmt = stmt.where(DiagnosticTest.facility_id == facility_id)
    if category:
        stmt = stmt.where(DiagnosticTest.category == category)
    if compliant_only is True:
        stmt = stmt.where(DiagnosticTest.audit_compliance_status == "compliant")
    elif compliant_only is False:
        stmt = stmt.where(DiagnosticTest.audit_compliance_status != "compliant")
        
    stmt = stmt.order_by(DiagnosticTest.audit_compliance_status.desc(), DiagnosticTest.test_name)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.patch("/{test_id}", response_model=DiagnosticTestResponse)
async def update_test_audit(
    test_id: str,
    payload: DiagnosticTestUpdate,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(DiagnosticTest).where(DiagnosticTest.id == test_id))
    test = res.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Diagnostic test record not found")
        
    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(test, field, val)
        
    # Auto-evaluate compliance
    if not test.reagents_available or test.reagents_stock_units < 10:
        test.audit_compliance_status = "reagent_deficit"
    elif not test.equipment_functional:
        test.audit_compliance_status = "equipment_breakdown"
    else:
        test.audit_compliance_status = "compliant"
        
    test.last_audited_at = datetime.utcnow()
    await db.commit()
    await db.refresh(test)
    
    await ws_manager.broadcast_json({
        "event": "DIAGNOSTIC_AUDIT_UPDATED",
        "test_id": test.id,
        "test_name": test.test_name,
        "facility_id": test.facility_id,
        "compliance_status": test.audit_compliance_status
    })
    
    return test

