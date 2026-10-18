# File: backend/app/models/facility.py
# Description: SQLAlchemy ORM model for healthcare facilities (PHCs, CHCs, District Hospitals)

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime
from app.database import Base

class Facility(Base):
    __tablename__ = "facilities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(150), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    facility_type = Column(String(50), nullable=False, default="PHC")  # PHC, CHC, Sub-District Hospital, DH
    block_name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    catchment_population = Column(Integer, default=30000)
    contact_person = Column(String(100), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    
    # Health Facility Distress Index (HFDI: 0 to 100)
    distress_score = Column(Float, default=15.0)
    operational_status = Column(String(30), default="nominal")  # nominal, strained, critical_distress
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

