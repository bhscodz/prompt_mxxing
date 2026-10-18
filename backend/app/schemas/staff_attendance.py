# File: backend/app/schemas/staff_attendance.py
# Description: Pydantic schemas for doctor and staff duty shifts, biometric punches, and specialty coverage

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class DoctorStaffBase(BaseModel):
    facility_id: str
    full_name: str
    role: str
    registration_number: str
    phone: Optional[str] = None
    shift_timing: str = "Morning (08:00 - 14:00)"
    is_on_duty_today: bool = True
    attendance_status: str = "Present"

class DoctorStaffCreate(DoctorStaffBase):
    pass

class PunchInRequest(BaseModel):
    staff_id: str
    status: str = "Present" # Present, On Emergency Call, On Leave, Absent

class DoctorStaffResponse(DoctorStaffBase):
    id: str
    biometric_punch_in: Optional[datetime] = None
    biometric_punch_out: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

