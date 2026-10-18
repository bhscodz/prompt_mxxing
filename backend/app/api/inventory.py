# File: backend/app/api/inventory.py
# Description: REST API router for medicine stock monitoring, burn rate recalculation, and stockout hazards

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import get_db
from backend.app.models.inventory import MedicineStock, StockTransaction
from backend.app.models.facility import Facility
from backend.app.schemas.inventory import (
    MedicineStockCreate, MedicineStockUpdate, MedicineStockResponse,
    StockTransactionCreate, StockTransactionResponse
)
from backend.app.schemas.ml_forecasts import StockoutEarlyWarning
from backend.app.ml.demand_forecaster import forecaster_service
from backend.app.utils.websocket_manager import ws_manager

router = APIRouter(prefix="/inventory", tags=["Inventory & Pharmacy"])

@router.get("", response_model=List[MedicineStockResponse])
async def list_stocks(
    facility_id: Optional[str] = None,
    category: Optional[str] = None,
    critical_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    query = select(MedicineStock)
    if facility_id:
        query = query.where(MedicineStock.facility_id == facility_id)
    if category:
        query = query.where(MedicineStock.category == category)
    if critical_only:
        query = query.where(MedicineStock.current_quantity <= MedicineStock.reorder_level)
        
    query = query.order_by(MedicineStock.days_of_supply.asc())
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/warnings", response_model=List[StockoutEarlyWarning])
async def get_early_stockout_warnings(
    facility_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluates dynamic consumption trajectories via Time Series Transformer
    and returns categorized early stockout alerts.
    """
    fac_query = select(Facility)
    if facility_id:
        fac_query = fac_query.where(Facility.id == facility_id)
    fac_res = await db.execute(fac_query)
    facilities = {f.id: f.name for f in fac_res.scalars().all()}
    
    stock_query = select(MedicineStock)
    if facility_id:
        stock_query = stock_query.where(MedicineStock.facility_id == facility_id)
    stock_res = await db.execute(stock_query)
    stocks = stock_res.scalars().all()
    
    warnings: List[StockoutEarlyWarning] = []
    for s in stocks:
        hazard = forecaster_service.assess_stockout_hazard(
            facility_id=s.facility_id,
            facility_name=facilities.get(s.facility_id, "Unknown PHC"),
            medicine_name=s.medicine_name,
            category=s.category,
            current_stock=s.current_quantity,
            daily_burn_rate=s.daily_burn_rate
        )
        if hazard["urgency_level"] in ["CRITICAL_HAZARD", "WARNING"]:
            warnings.append(StockoutEarlyWarning(**hazard))
            
    # Sort with critical hazards first
    warnings.sort(key=lambda w: (0 if w.urgency_level == "CRITICAL_HAZARD" else 1, w.days_until_stockout))
    return warnings

@router.post("/transaction", response_model=StockTransactionResponse)
async def record_transaction(payload: StockTransactionCreate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(MedicineStock).where(MedicineStock.id == payload.medicine_stock_id))
    stock = res.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail="Medicine stock record not found")
        
    if payload.transaction_type in ["dispensation", "transfer_out", "expired_writeoff"]:
        stock.current_quantity = max(0, stock.current_quantity - payload.quantity)
    elif payload.transaction_type in ["inbound", "transfer_in"]:
        stock.current_quantity += payload.quantity
        
    stock.days_of_supply = round(stock.current_quantity / max(1.0, stock.daily_burn_rate), 1)
    
    # Update risk score
    if stock.days_of_supply <= 2.0:
        stock.stockout_risk_score = 0.95
    elif stock.days_of_supply <= 7.0:
        stock.stockout_risk_score = 0.70
    else:
        stock.stockout_risk_score = 0.15
        
    tx = StockTransaction(**payload.model_dump())
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    
    # Broadcast live update
    await ws_manager.broadcast_json({
        "event": "STOCK_UPDATED",
        "stock_id": stock.id,
        "facility_id": stock.facility_id,
        "medicine_name": stock.medicine_name,
        "remaining_quantity": stock.current_quantity,
        "days_of_supply": stock.days_of_supply
    })
    
    return tx

