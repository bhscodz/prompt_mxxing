# File: backend/app/api/redistribution.py
# Description: REST API router for AI-driven intra-district resource redistribution and transfer orders

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import get_db
from backend.app.models.facility import Facility
from backend.app.models.inventory import MedicineStock
from backend.app.models.alerts_interventions import RedistributionTransfer
from backend.app.schemas.alerts_interventions import (
    RedistributionTransferCreate, TransferActionRequest, RedistributionTransferResponse
)
from backend.app.ml.redistribution_engine import redistribution_engine
from backend.app.utils.websocket_manager import ws_manager

router = APIRouter(prefix="/redistribution", tags=["Intra-District Redistribution"])

@router.get("/recommendations")
async def generate_recommendations(db: AsyncSession = Depends(get_db)):
    """
    Runs district-wide balancing algorithm to identify supply deficits and
    propose transfers from the closest surplus health centres.
    """
    f_res = await db.execute(select(Facility))
    facilities = [{
        "id": f.id,
        "name": f.name,
        "latitude": f.latitude,
        "longitude": f.longitude,
        "facility_type": f.facility_type
    } for f in f_res.scalars().all()]
    
    s_res = await db.execute(select(MedicineStock))
    stocks = [{
        "id": s.id,
        "facility_id": s.facility_id,
        "medicine_name": s.medicine_name,
        "current_quantity": s.current_quantity,
        "reorder_level": s.reorder_level,
        "daily_burn_rate": s.daily_burn_rate,
        "unit": s.unit
    } for s in s_res.scalars().all()]
    
    plan = redistribution_engine.calculate_redistribution_plan(facilities, stocks)
    return plan

@router.get("/transfers", response_model=List[RedistributionTransferResponse])
async def list_transfers(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(RedistributionTransfer)
    if status:
        stmt = stmt.where(RedistributionTransfer.status == status)
    stmt = stmt.order_by(RedistributionTransfer.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/transfers", response_model=RedistributionTransferResponse)
async def create_transfer(payload: RedistributionTransferCreate, db: AsyncSession = Depends(get_db)):
    transfer = RedistributionTransfer(**payload.model_dump())
    db.add(transfer)
    await db.commit()
    await db.refresh(transfer)
    
    await ws_manager.broadcast_json({
        "event": "NEW_TRANSFER_SUGGESTED",
        "transfer_id": transfer.id,
        "item_name": transfer.item_name,
        "quantity": transfer.quantity
    })
    
    return transfer

@router.post("/transfers/{transfer_id}/action", response_model=RedistributionTransferResponse)
async def execute_transfer_action(
    transfer_id: str,
    payload: TransferActionRequest,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(RedistributionTransfer).where(RedistributionTransfer.id == transfer_id))
    transfer = res.scalar_one_or_none()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer order not found")
        
    action_map = {
        "approve": "approved_by_admin",
        "dispatch": "in_transit",
        "receive": "received",
        "cancel": "cancelled"
    }
    
    if payload.action not in action_map:
        raise HTTPException(status_code=400, detail=f"Invalid action: {payload.action}")
        
    transfer.status = action_map[payload.action]
    transfer.approved_by = payload.actor_name
    transfer.updated_at = datetime.utcnow()
    
    # If received, deduct from source and credit target
    if payload.action == "receive":
        # Deduct from source
        src_res = await db.execute(
            select(MedicineStock)
            .where(MedicineStock.facility_id == transfer.source_facility_id)
            .where(MedicineStock.medicine_name == transfer.item_name)
        )
        src_stock = src_res.scalar_one_or_none()
        if src_stock:
            src_stock.current_quantity = max(0, src_stock.current_quantity - transfer.quantity)
            src_stock.days_of_supply = round(src_stock.current_quantity / max(1.0, src_stock.daily_burn_rate), 1)

        # Credit target
        tgt_res = await db.execute(
            select(MedicineStock)
            .where(MedicineStock.facility_id == transfer.target_facility_id)
            .where(MedicineStock.medicine_name == transfer.item_name)
        )
        tgt_stock = tgt_res.scalar_one_or_none()
        if tgt_stock:
            tgt_stock.current_quantity += transfer.quantity
            tgt_stock.days_of_supply = round(tgt_stock.current_quantity / max(1.0, tgt_stock.daily_burn_rate), 1)

    await db.commit()
    await db.refresh(transfer)
    
    await ws_manager.broadcast_json({
        "event": "TRANSFER_STATUS_CHANGED",
        "transfer_id": transfer.id,
        "status": transfer.status,
        "action": payload.action
    })
    
    return transfer

