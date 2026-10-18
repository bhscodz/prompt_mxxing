# File: backend/app/schemas/beds.py
# Description: Pydantic schemas for bed matrix, ward allocation, and oxygen infrastructure tracking

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class BedBase(BaseModel):
    facility_id: str
    bed_number: str
    ward_type: str
    status: str = "available" # available, occupied, cleaning, maintenance
    oxygen_supported: bool = False
    allocated_patient_id: Optional[str] = None
    allocated_patient_name: Optional[str] = None
    admission_timestamp: Optional[datetime] = None
    expected_discharge: Optional[datetime] = None

class BedCreate(BedBase):
    pass

class BedUpdate(BaseModel):
    status: Optional[str] = None
    oxygen_supported: Optional[bool] = None
    allocated_patient_id: Optional[str] = None
    allocated_patient_name: Optional[str] = None
    admission_timestamp: Optional[datetime] = None
    expected_discharge: Optional[datetime] = None

class BedAllocateRequest(BaseModel):
    patient_name: str
    patient_id: Optional[str] = None
    oxygen_required: bool = False

class BedResponse(BedBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

