# File: backend/app/models/patient_crm.py
# Description: SQLAlchemy ORM model for Patient CRM, OPD registrations, triage queues, and footfall tracking

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from backend.app.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    abha_id = Column(String(50), unique=True, nullable=True, index=True) # ABHA / Ayushman Bharat ID
    full_name = Column(String(150), nullable=False, index=True)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False) # Male, Female, Other
    phone = Column(String(20), nullable=True)
    village = Column(String(100), nullable=False)
    blood_group = Column(String(10), nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class OPDVisit(Base):
    __tablename__ = "opd_visits"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(String(36), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    
    token_number = Column(String(20), nullable=False) # e.g. "T-102"
    triage_category = Column(String(30), default="standard_green") # immediate_red, urgent_yellow, standard_green
    chief_complaint = Column(String(255), nullable=False)
    
    # Vitals
    systolic_bp = Column(Integer, nullable=True)
    diastolic_bp = Column(Integer, nullable=True)
    pulse_rate = Column(Integer, nullable=True)
    temperature_f = Column(Float, nullable=True)
    spo2 = Column(Integer, nullable=True)
    
    assigned_doctor_name = Column(String(100), nullable=True)
    status = Column(String(40), default="waiting") # waiting, in_consultation, pharmacy_pending, admitted, completed
    diagnosis_notes = Column(Text, nullable=True)
    prescribed_medicines = Column(Text, nullable=True)
    
    visit_date = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

