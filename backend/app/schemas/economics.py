# File: backend/app/schemas/economics.py
# Description: Pydantic v2 schemas for economics API — budget allocations, expenditures,
#              purchase orders, and monthly/district summary responses

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import date, datetime


# ──────────────────────────────────────────────────────────────────
# Budget Allocation schemas
# ──────────────────────────────────────────────────────────────────

class BudgetAllocationBase(BaseModel):
    facility_id: str
    fiscal_year: int = Field(..., ge=2020, le=2100, description="Fiscal year start, e.g. 2025 = FY2025-26")
    # Valid categories: MEDICINES, EQUIPMENT, STAFF_SALARIES, UTILITIES,
    #                   MAINTENANCE, CONSUMABLES, DIAGNOSTICS
    category: str
    allocated_amount: float = Field(..., ge=0)
    currency: str = "INR"


class BudgetAllocationCreate(BudgetAllocationBase):
    pass


class BudgetAllocationResponse(BudgetAllocationBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────────────────────────
# Expenditure schemas
# ──────────────────────────────────────────────────────────────────

class ExpenditureBase(BaseModel):
    facility_id: str
    category: str
    amount: float = Field(..., ge=0)
    description: Optional[str] = None
    invoice_number: Optional[str] = None
    vendor: Optional[str] = None
    date: date
    approved_by: Optional[str] = None
    payment_status: str = "PENDING"  # PENDING | PAID | DISPUTED


class ExpenditureCreate(ExpenditureBase):
    pass


class ExpenditureResponse(ExpenditureBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────────────────────────
# Purchase Order schemas
# ──────────────────────────────────────────────────────────────────

class PurchaseOrderBase(BaseModel):
    facility_id: str
    item_type: str          # MEDICINE | EQUIPMENT | CONSUMABLE
    item_name: str
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., ge=0)
    total_amount: float = Field(..., ge=0)
    vendor: Optional[str] = None
    expected_delivery_date: Optional[date] = None
    status: str = "DRAFT"   # DRAFT | SUBMITTED | APPROVED | DELIVERED | CANCELLED


class PurchaseOrderCreate(PurchaseOrderBase):
    pass


class PurchaseOrderStatusUpdate(BaseModel):
    """Payload to update a PO status (e.g. APPROVED → DELIVERED)"""
    status: str
    actual_delivery_date: Optional[date] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    id: str
    actual_delivery_date: Optional[date] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────────────────────────
# Monthly Budget Summary schemas
# ──────────────────────────────────────────────────────────────────

class MonthlyBudgetSummaryResponse(BaseModel):
    id: str
    facility_id: str
    year: int
    month: int
    total_budget: float
    total_spent: float
    budget_utilization_pct: float
    variance: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ──────────────────────────────────────────────────────────────────
# Aggregate / dashboard response shapes
# ──────────────────────────────────────────────────────────────────

class CategoryBudgetItem(BaseModel):
    """One row in the budget-vs-actual table per category"""
    category: str
    allocated: float
    spent: float
    utilization_pct: float
    variance: float


class FacilitySummaryResponse(BaseModel):
    """High-level economics KPI card data for a single facility"""
    facility_id: str
    fiscal_year: int
    total_budget: float
    total_spent: float
    remaining: float
    utilization_pct: float
    by_category: List[CategoryBudgetItem] = []
    monthly_trend: List[MonthlyBudgetSummaryResponse] = []


class DistrictAggregateSummary(BaseModel):
    """Cross-facility aggregate for district admin view"""
    year: int
    month: Optional[int] = None
    total_budget: float
    total_spent: float
    utilization_pct: float
    facility_breakdown: List[dict] = []
