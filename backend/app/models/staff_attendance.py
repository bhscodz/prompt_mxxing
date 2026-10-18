# File: backend/app/models/staff_attendance.py
# Description: SQLAlchemy ORM model for doctor and medical staff biometric attendance, shifts, and specialty tracking

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from app.database import Base

class DoctorStaff(Base):
    __tablename__ = "doctor_staff"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(String(36), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    full_name = Column(String(150), nullable=False)
    role = Column(String(80), nullable=False) # Medical Officer, Gynecologist / OBGYN, Pediatrician, Staff Nurse, Pharmacist, Lab Technician, AYUSH Doctor
    registration_number = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=True)
    shift_timing = Column(String(60), default="Morning (08:00 - 14:00)")
    
    # Biometric attendance state
    is_on_duty_today = Column(Boolean, default=True)
    biometric_punch_in = Column(DateTime, nullable=True)
    biometric_punch_out = Column(DateTime, nullable=True)
    attendance_status = Column(String(40), default="Present") # Present, Absent, On Emergency Call, On Leave
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

