# File: backend/app/models/__init__.py
# Description: Aggregate export for all SQLAlchemy ORM models - Phase 2 complete

from backend.app.models.facility import Facility
from backend.app.models.inventory import MedicineStock, StockTransaction
from backend.app.models.patient_crm import Patient, OPDVisit
from backend.app.models.beds import Bed
from backend.app.models.staff_attendance import DoctorStaff
from backend.app.models.diagnostic_tests import DiagnosticTest
from backend.app.models.alerts_interventions import InterventionAlert, RedistributionTransfer
from backend.app.models.auth import User, UserSession, AuditLog
from backend.app.models.leave_management import LeaveType, LeaveRequest, LeaveApproval, LeaveBalance, ShiftCoverage
from backend.app.models.economics import BudgetAllocation, Expenditure, PurchaseOrder, MonthlyBudgetSummary

__all__ = [
    "Facility", "MedicineStock", "StockTransaction", "Patient", "OPDVisit",
    "Bed", "DoctorStaff", "DiagnosticTest", "InterventionAlert", "RedistributionTransfer",
    "User", "UserSession", "AuditLog",
    "LeaveType", "LeaveRequest", "LeaveApproval", "LeaveBalance", "ShiftCoverage",
    "BudgetAllocation", "Expenditure", "PurchaseOrder", "MonthlyBudgetSummary"
]
