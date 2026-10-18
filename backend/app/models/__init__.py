# File: backend/app/models/__init__.py
# Description: Aggregate export for all SQLAlchemy ORM models - Phase 2 complete

from app.models.facility import Facility
from app.models.inventory import MedicineStock, StockTransaction
from app.models.patient_crm import Patient, OPDVisit
from app.models.beds import Bed
from app.models.staff_attendance import DoctorStaff
from app.models.diagnostic_tests import DiagnosticTest
from app.models.alerts_interventions import InterventionAlert, RedistributionTransfer
from app.models.auth import User, UserSession, AuditLog
from app.models.leave_management import LeaveType, LeaveRequest, LeaveApproval, LeaveBalance, ShiftCoverage
from app.models.economics import BudgetAllocation, Expenditure, PurchaseOrder, MonthlyBudgetSummary

__all__ = [
    "Facility", "MedicineStock", "StockTransaction", "Patient", "OPDVisit",
    "Bed", "DoctorStaff", "DiagnosticTest", "InterventionAlert", "RedistributionTransfer",
    "User", "UserSession", "AuditLog",
    "LeaveType", "LeaveRequest", "LeaveApproval", "LeaveBalance", "ShiftCoverage",
    "BudgetAllocation", "Expenditure", "PurchaseOrder", "MonthlyBudgetSummary"
]
