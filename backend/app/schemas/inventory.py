# File: backend/app/schemas/inventory.py
# Description: Pydantic schemas for medicine stock, batch transactions, and early stockout warning alerts

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime

class MedicineStockBase(BaseModel):
    facility_id: str
    medicine_name: str
    category: str
    batch_number: str
    expiry_date: date
    current_quantity: int
    reorder_level: int = 100
    daily_burn_rate: float = 10.0
    unit: str = "tablets"

class MedicineStockCreate(MedicineStockBase):
    pass

class MedicineStockUpdate(BaseModel):
    current_quantity: Optional[int] = None
    reorder_level: Optional[int] = None
    daily_burn_rate: Optional[float] = None
    expiry_date: Optional[date] = None

class MedicineStockResponse(MedicineStockBase):
    id: str
    stockout_risk_score: float
    days_of_supply: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class StockTransactionCreate(BaseModel):
    facility_id: str
    medicine_stock_id: str
    transaction_type: str # inbound, dispensation, transfer_in, transfer_out, expired_writeoff
    quantity: int
    notes: Optional[str] = None

class StockTransactionResponse(StockTransactionCreate):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

