# File: backend/app/schemas/__init__.py
# Description: Schema exports for SwasthyaGrid AI

from app.schemas.facility import FacilityCreate, FacilityUpdate, FacilityResponse
from app.schemas.inventory import (
    MedicineStockCreate, MedicineStockUpdate, MedicineStockResponse,
    StockTransactionCreate, StockTransactionResponse
)
from app.schemas.patient_crm import (
    PatientCreate, PatientResponse, OPDVisitCreate, OPDVisitUpdate, OPDVisitResponse
)
from app.schemas.beds import BedCreate, BedUpdate, BedAllocateRequest, BedResponse
from app.schemas.staff_attendance import DoctorStaffCreate, PunchInRequest, DoctorStaffResponse
from app.schemas.diagnostic_tests import (
    DiagnosticTestCreate, DiagnosticTestUpdate, DiagnosticTestResponse
)
from app.schemas.alerts_interventions import (
    InterventionAlertCreate, InterventionActionRequest, InterventionAlertResponse,
    RedistributionTransferCreate, TransferActionRequest, RedistributionTransferResponse
)
from app.schemas.ml_forecasts import (
    DailyForecastPoint, ForecastSeries, StockoutEarlyWarning
)

