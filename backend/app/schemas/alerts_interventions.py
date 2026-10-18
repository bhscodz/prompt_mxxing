# File: backend/app/schemas/alerts_interventions.py
# Description: Pydantic schemas for district administrative intervention alerts and intra-district redistribution transfers

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class InterventionAlertBase(BaseModel):
    facility_id: str
    alert_type: str # critical_stockout, doctor_absenteeism, bed_saturation, footfall_surge, diagnostic_failure
    severity: str = "critical" # critical, high, moderate, info
    title: str
    description: str
    suggested_action: Optional[str] = None
    status: str = "pending_review"

class InterventionAlertCreate(InterventionAlertBase):
    pass

class InterventionActionRequest(BaseModel):
    status: str # dispatched, in_progress, resolved
    admin_notes: str
    dispatched_by: str

class InterventionAlertResponse(InterventionAlertBase):
    id: str
    admin_notes: Optional[str] = None
    dispatched_by: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class RedistributionTransferBase(BaseModel):
    source_facility_id: str
    target_facility_id: str
    item_type: str = "medicine"
    item_name: str
    quantity: int
    unit: str = "tablets"
    haversine_distance_km: float = 12.5
    estimated_transit_hours: float = 0.5
    urgency_reason: Optional[str] = None
    status: str = "suggested_by_ai"

class RedistributionTransferCreate(RedistributionTransferBase):
    pass

class TransferActionRequest(BaseModel):
    action: str # approve, dispatch, receive, cancel
    actor_name: str

class RedistributionTransferResponse(RedistributionTransferBase):
    id: str
    approved_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

