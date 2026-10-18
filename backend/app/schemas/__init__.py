# File: backend/app/schemas/__init__.py
# Description: Schema exports for SwasthyaGrid AI

from backend.app.schemas.facility import FacilityCreate, FacilityUpdate, FacilityResponse
from backend.app.schemas.inventory import (
    MedicineStockCreate, MedicineStockUpdate, MedicineStockResponse,
    StockTransactionCreate, StockTransactionResponse
)
from backend.app.schemas.patient_crm import (
    PatientCreate, PatientResponse, OPDVisitCreate, OPDVisitUpdate, OPDVisitResponse
)
from backend.app.schemas.beds import BedCreate, BedUpdate, BedAllocateRequest, BedResponse
from backend.app.schemas.staff_attendance import DoctorStaffCreate, PunchInRequest, DoctorStaffResponse
from backend.app.schemas.diagnostic_tests import (
    DiagnosticTestCreate, DiagnosticTestUpdate, DiagnosticTestResponse
)
from backend.app.schemas.alerts_interventions import (
    InterventionAlertCreate, InterventionActionRequest, InterventionAlertResponse,
    RedistributionTransferCreate, TransferActionRequest, RedistributionTransferResponse
)
from backend.app.schemas.ml_forecasts import (
    DailyForecastPoint, ForecastSeries, StockoutEarlyWarning
)

