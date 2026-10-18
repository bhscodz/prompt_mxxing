# File: backend/app/models/inventory.py
# Description: SQLAlchemy ORM model for medicine stock monitoring, burn rates, and inventory ledgers

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from backend.app.database import Base

class MedicineStock(Base):
    __tablename__ = "medicine_stocks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(String(36), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    medicine_name = Column(String(150), nullable=False, index=True)
    category = Column(String(100), nullable=False) # Antibiotic, Analgesic, Maternal Care, Emergency Antidote, Chronic, Vaccine
    batch_number = Column(String(50), nullable=False)
    expiry_date = Column(Date, nullable=False)
    current_quantity = Column(Integer, nullable=False, default=0)
    reorder_level = Column(Integer, nullable=False, default=100)
    daily_burn_rate = Column(Float, nullable=False, default=10.0)
    unit = Column(String(30), default="tablets") # tablets, vials, ampoules, packets
    
    # Calculated AI metrics
    stockout_risk_score = Column(Float, default=0.0) # 0.0 (safe) to 1.0 (imminent stockout)
    days_of_supply = Column(Float, default=30.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(String(36), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False)
    medicine_stock_id = Column(String(36), ForeignKey("medicine_stocks.id", ondelete="CASCADE"), nullable=False)
    transaction_type = Column(String(50), nullable=False) # inbound, dispensation, transfer_in, transfer_out, expired_writeoff
    quantity = Column(Integer, nullable=False)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

