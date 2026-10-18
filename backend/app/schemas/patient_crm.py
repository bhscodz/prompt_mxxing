# File: backend/app/schemas/patient_crm.py
# Description: Pydantic schemas for Patient CRM, OPD triage registration, vitals, and queue consultation management

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class PatientBase(BaseModel):
    abha_id: Optional[str] = None
    full_name: str
    age: int
    gender: str
    phone: Optional[str] = None
    village: str
    blood_group: Optional[str] = None
    emergency_contact: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientResponse(PatientBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OPDVisitCreate(BaseModel):
    patient_id: Optional[str] = None
    facility_id: str
    # If patient does not exist yet, allow inline registration
    patient_data: Optional[PatientCreate] = None
    
    chief_complaint: str
    triage_category: str = "standard_green"
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    pulse_rate: Optional[int] = None
    temperature_f: Optional[float] = None
    spo2: Optional[int] = None
    assigned_doctor_name: Optional[str] = None

class OPDVisitUpdate(BaseModel):
    status: Optional[str] = None
    diagnosis_notes: Optional[str] = None
    prescribed_medicines: Optional[str] = None
    assigned_doctor_name: Optional[str] = None
    triage_category: Optional[str] = None

class OPDVisitResponse(BaseModel):
    id: str
    patient_id: str
    facility_id: str
    token_number: str
    triage_category: str
    chief_complaint: str
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    pulse_rate: Optional[int] = None
    temperature_f: Optional[float] = None
    spo2: Optional[int] = None
    assigned_doctor_name: Optional[str] = None
    status: str
    diagnosis_notes: Optional[str] = None
    prescribed_medicines: Optional[str] = None
    visit_date: datetime
    created_at: datetime
    # Expanded patient details for CRM display
    patient: Optional[PatientResponse] = None

    model_config = ConfigDict(from_attributes=True)

