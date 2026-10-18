# File: backend/app/api/ai_forecasts.py
# Description: REST API router for PyTorch Time Series Transformer demand, footfall, and bed occupancy forecasts

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import get_db
from backend.app.models.facility import Facility
from backend.app.models.inventory import MedicineStock
from backend.app.schemas.ml_forecasts import ForecastSeries, StockoutEarlyWarning
from backend.app.ml.demand_forecaster import forecaster_service

router = APIRouter(prefix="/ai", tags=["AI Demand Forecasting"])

@router.get("/forecast", response_model=ForecastSeries)
async def get_transformer_forecast(
    facility_id: str,
    metric_type: str = Query("patient_footfall", description="patient_footfall, medicine_demand, bed_occupancy"),
    item_name: Optional[str] = None,
    daily_rate: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Executes multi-head attention Transformer to project 14-day forecasts with 90% confidence bands.
    """
    res = await db.execute(select(Facility).where(Facility.id == facility_id))
    facility = res.scalar_one_or_none()
    facility_name = facility.name if facility else "Health Center"
    
    # If daily_rate not provided, derive baseline from data
    if daily_rate is None:
        if metric_type == "patient_footfall":
            daily_rate = 75.0 if (facility and facility.facility_type == "PHC") else 180.0
        elif metric_type == "medicine_demand":
            if item_name:
                s_res = await db.execute(
                    select(MedicineStock)
                    .where(MedicineStock.facility_id == facility_id)
                    .where(MedicineStock.medicine_name == item_name)
                )
                stock = s_res.scalar_one_or_none()
                daily_rate = stock.daily_burn_rate if stock else 25.0
            else:
                daily_rate = 30.0
        elif metric_type == "bed_occupancy":
            daily_rate = 14.0
        else:
            daily_rate = 50.0

    forecast = forecaster_service.forecast_metric(
        facility_id=facility_id,
        facility_name=facility_name,
        metric_type=metric_type,
        current_daily_rate=daily_rate,
        item_name=item_name
    )
    return ForecastSeries(**forecast)

