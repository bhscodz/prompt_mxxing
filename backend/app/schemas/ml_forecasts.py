# File: backend/app/schemas/ml_forecasts.py
# Description: Pydantic schemas for Time Series Transformer predictions, demand forecasts, and early stockout hazard analysis

from pydantic import BaseModel
from typing import List, Optional

class DailyForecastPoint(BaseModel):
    date: str
    predicted_value: float
    lower_bound_90: float
    upper_bound_90: float
    is_historical: bool = False

class ForecastSeries(BaseModel):
    facility_id: str
    facility_name: str
    metric_type: str # patient_footfall, medicine_demand, bed_occupancy
    item_name: Optional[str] = None
    historical_points: List[DailyForecastPoint]
    forecast_points: List[DailyForecastPoint]
    model_architecture: str = "PyTorch Multi-Head Self-Attention Time Series Transformer"
    attention_weights_summary: Optional[dict] = None

class StockoutEarlyWarning(BaseModel):
    facility_id: str
    facility_name: str
    medicine_name: str
    category: str
    current_stock: int
    daily_burn_rate: float
    predicted_daily_demand: float
    days_until_stockout: float
    urgency_level: str # CRITICAL_HAZARD (< 48 hrs), WARNING (< 7 days), OPTIMAL
    confidence_interval: str
    recommended_action: str

