# File: backend/app/models/alerts_interventions.py
# Description: SQLAlchemy ORM models for district administrator interventions and intra-district resource redistribution

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text
from app.database import Base

class InterventionAlert(Base):
    __tablename__ = "intervention_alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(String(36), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Alert Category: critical_stockout, doctor_absenteeism, bed_saturation, footfall_surge, diagnostic_failure
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default="critical") # critical, high, moderate, info
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    suggested_action = Column(Text, nullable=True)
    
    # Administrative lifecycle: pending_review, dispatched, in_progress, resolved
    status = Column(String(30), default="pending_review", index=True)
    admin_notes = Column(Text, nullable=True)
    dispatched_by = Column(String(100), nullable=True) # e.g. "Dr. R. Deshmukh (CMO Pune)"
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)

class RedistributionTransfer(Base):
    __tablename__ = "redistribution_transfers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_facility_id = Column(String(36), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False)
    target_facility_id = Column(String(36), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False)
    
    item_type = Column(String(40), default="medicine") # medicine, reagent, bed_equipment
    item_name = Column(String(150), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit = Column(String(30), default="tablets")
    
    haversine_distance_km = Column(Float, nullable=False, default=12.5)
    estimated_transit_hours = Column(Float, nullable=False, default=0.5)
    urgency_reason = Column(String(255), nullable=True)
    
    # Lifecycle: suggested_by_ai, approved_by_admin, in_transit, received, cancelled
    status = Column(String(40), default="suggested_by_ai", index=True)
    approved_by = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

