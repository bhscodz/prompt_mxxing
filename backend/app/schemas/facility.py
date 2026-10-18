# File: backend/app/schemas/facility.py
# Description: Pydantic schemas for health facility creation, update, and API responses

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class FacilityBase(BaseModel):
    name: str
    code: str
    facility_type: str
    block_name: str
    latitude: float
    longitude: float
    catchment_population: int = 30000
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None

class FacilityCreate(FacilityBase):
    pass

class FacilityUpdate(BaseModel):
    name: Optional[str] = None
    facility_type: Optional[str] = None
    block_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    distress_score: Optional[float] = None
    operational_status: Optional[str] = None

class FacilityResponse(FacilityBase):
    id: str
    distress_score: float
    operational_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

