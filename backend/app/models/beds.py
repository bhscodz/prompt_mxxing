# File: backend/app/models/beds.py
# Description: SQLAlchemy ORM model for real-time bed inventory, ward management, and bed allocation

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from app.database import Base

class Bed(Base):
    __tablename__ = "beds"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(String(36), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    bed_number = Column(String(50), nullable=False)
    ward_type = Column(String(60), nullable=False) # General Male, General Female, Maternity, Pediatric, Emergency, ICU
    status = Column(String(30), nullable=False, default="available") # available, occupied, cleaning, maintenance
    oxygen_supported = Column(Boolean, default=False)
    
    # Active allocation details
    allocated_patient_id = Column(String(36), nullable=True)
    allocated_patient_name = Column(String(150), nullable=True)
    admission_timestamp = Column(DateTime, nullable=True)
    expected_discharge = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

