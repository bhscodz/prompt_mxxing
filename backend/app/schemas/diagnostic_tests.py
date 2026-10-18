# File: backend/app/schemas/diagnostic_tests.py
# Description: Pydantic schemas for lab diagnostics audit, reagent stock monitoring, and equipment operational status

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class DiagnosticTestBase(BaseModel):
    facility_id: str
    test_name: str
    category: str
    reagents_available: bool = True
    reagents_stock_units: int = 150
    equipment_functional: bool = True
    tests_conducted_today: int = 0
    average_turnaround_mins: int = 30
    audit_compliance_status: str = "compliant"

class DiagnosticTestCreate(DiagnosticTestBase):
    pass

class DiagnosticTestUpdate(BaseModel):
    reagents_available: Optional[bool] = None
    reagents_stock_units: Optional[int] = None
    equipment_functional: Optional[bool] = None
    tests_conducted_today: Optional[int] = None
    average_turnaround_mins: Optional[int] = None
    audit_compliance_status: Optional[str] = None

class DiagnosticTestResponse(DiagnosticTestBase):
    id: str
    last_audited_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

