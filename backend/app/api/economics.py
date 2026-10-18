# File: backend/app/api/economics.py
# Description: FastAPI router for health centre financial management — budget allocations,
#              expenditures, purchase orders, and monthly/district aggregate summaries.
#              Prefix: /economics

import logging
from typing import Optional, List
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.database import get_db
from app.models.economics import (
    BudgetAllocation, Expenditure, PurchaseOrder, MonthlyBudgetSummary
)
from app.models.alerts_interventions import InterventionAlert
from app.schemas.economics import (
    BudgetAllocationCreate, BudgetAllocationResponse,
    ExpenditureCreate, ExpenditureResponse,
    PurchaseOrderCreate, PurchaseOrderResponse, PurchaseOrderStatusUpdate,
    FacilitySummaryResponse, CategoryBudgetItem,
    MonthlyBudgetSummaryResponse, DistrictAggregateSummary
)

logger = logging.getLogger("swasthya.economics")

router = APIRouter(prefix="/economics", tags=["Economics & Finance"])

# ─────────────────────────────────────────────────────────────────────────────
# BUDGET ALLOCATION endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/budget/{facility_id}",
    response_model=List[BudgetAllocationResponse],
    summary="Get budget allocations by facility and fiscal year"
)
async def get_budget_allocations(
    facility_id: str,
    year: Optional[int] = Query(None, description="Fiscal year (e.g. 2025)"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all budget category allocations for a facility, optionally filtered by year."""
    stmt = select(BudgetAllocation).where(BudgetAllocation.facility_id == facility_id)
    if year:
        stmt = stmt.where(BudgetAllocation.fiscal_year == year)
    stmt = stmt.order_by(BudgetAllocation.fiscal_year.desc(), BudgetAllocation.category)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post(
    "/budget",
    response_model=BudgetAllocationResponse,
    status_code=201,
    summary="Create a budget allocation (DISTRICT_ADMIN)"
)
async def create_budget_allocation(
    payload: BudgetAllocationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new budget allocation for a category in a fiscal year."""
    allocation = BudgetAllocation(**payload.model_dump())
    db.add(allocation)
    await db.flush()
    await db.refresh(allocation)
    logger.info(f"Budget allocated: {allocation.facility_id} {allocation.category} ₹{allocation.allocated_amount}")
    return allocation


# ─────────────────────────────────────────────────────────────────────────────
# EXPENDITURE endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/expenditure/{facility_id}",
    response_model=List[ExpenditureResponse],
    summary="List expenditures with optional year/month/category filters"
)
async def list_expenditures(
    facility_id: str,
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Return expenditure records for a facility, optionally filtered by period and category."""
    stmt = select(Expenditure).where(Expenditure.facility_id == facility_id)

    # Filter by year (date column is a Date type — extract year/month)
    if year:
        stmt = stmt.where(func.strftime("%Y", Expenditure.date) == str(year))
    if month:
        stmt = stmt.where(func.strftime("%m", Expenditure.date) == f"{month:02d}")
    if category:
        stmt = stmt.where(Expenditure.category == category.upper())

    stmt = stmt.order_by(Expenditure.date.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post(
    "/expenditure",
    response_model=ExpenditureResponse,
    status_code=201,
    summary="Log a new expenditure entry"
)
async def create_expenditure(
    payload: ExpenditureCreate,
    db: AsyncSession = Depends(get_db)
):
    """Record a new expenditure transaction for a facility."""
    exp = Expenditure(**payload.model_dump())
    db.add(exp)
    await db.flush()
    await db.refresh(exp)
    logger.info(f"Expenditure logged: {exp.facility_id} {exp.category} ₹{exp.amount}")
    return exp


# ─────────────────────────────────────────────────────────────────────────────
# PURCHASE ORDER endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/purchase-orders/{facility_id}",
    response_model=List[PurchaseOrderResponse],
    summary="List purchase orders for a facility"
)
async def list_purchase_orders(
    facility_id: str,
    status: Optional[str] = Query(None, description="Filter by status (DRAFT/SUBMITTED/APPROVED/DELIVERED/CANCELLED)"),
    db: AsyncSession = Depends(get_db)
):
    """Return all purchase orders for a facility, optionally filtered by status."""
    stmt = select(PurchaseOrder).where(PurchaseOrder.facility_id == facility_id)
    if status:
        stmt = stmt.where(PurchaseOrder.status == status.upper())
    stmt = stmt.order_by(PurchaseOrder.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post(
    "/purchase-orders",
    response_model=PurchaseOrderResponse,
    status_code=201,
    summary="Create a new purchase order"
)
async def create_purchase_order(
    payload: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db)
):
    """Raise a new purchase order; starts in DRAFT status."""
    po = PurchaseOrder(**payload.model_dump())
    # Auto-calculate total if not provided (guard against rounding mismatches)
    if po.total_amount == 0 and po.quantity and po.unit_price:
        po.total_amount = round(po.quantity * po.unit_price, 2)
    db.add(po)
    await db.flush()
    await db.refresh(po)
    logger.info(f"PO created: {po.item_name} qty={po.quantity} for {po.facility_id}")
    return po


@router.put(
    "/purchase-orders/{po_id}/status",
    response_model=PurchaseOrderResponse,
    summary="Update PO status (triggers ETA alert when DELIVERED)"
)
async def update_po_status(
    po_id: str,
    payload: PurchaseOrderStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update PO status. When set to DELIVERED, creates an info alert for inventory receipt."""
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    po.status = payload.status.upper()
    if payload.actual_delivery_date:
        po.actual_delivery_date = payload.actual_delivery_date

    # When goods are delivered, raise an alert for the store in-charge to confirm receipt
    if po.status == "DELIVERED":
        alert = InterventionAlert(
            facility_id=po.facility_id,
            alert_type="delivery_received",
            severity="info",
            title=f"PO Delivered: {po.item_name}",
            description=(
                f"Purchase order for {po.quantity} units of '{po.item_name}' "
                f"from vendor '{po.vendor or 'N/A'}' has been marked as delivered. "
                f"Please update inventory records."
            ),
            suggested_action="Verify quantity, update stock registers, and mark payment as PAID.",
            status="pending_review"
        )
        db.add(alert)
        logger.info(f"Delivery alert created for PO {po_id}: {po.item_name}")

    await db.flush()
    await db.refresh(po)
    return po


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY & ANALYTICS endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/summary/{facility_id}",
    response_model=FacilitySummaryResponse,
    summary="Monthly burn rate and % budget used per category"
)
async def get_facility_summary(
    facility_id: str,
    year: int = Query(..., description="Fiscal year (e.g. 2025)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Aggregate budget vs. actual per category for the fiscal year.
    Also returns per-month spending trend from MonthlyBudgetSummary.
    """
    # --- Budget allocations for the year ---
    alloc_stmt = select(BudgetAllocation).where(
        and_(
            BudgetAllocation.facility_id == facility_id,
            BudgetAllocation.fiscal_year == year
        )
    )
    alloc_result = await db.execute(alloc_stmt)
    allocations = {a.category: a.allocated_amount for a in alloc_result.scalars().all()}

    total_budget = sum(allocations.values())

    # --- Actual expenditure per category for the year ---
    exp_stmt = select(
        Expenditure.category,
        func.sum(Expenditure.amount).label("total_spent")
    ).where(
        and_(
            Expenditure.facility_id == facility_id,
            func.strftime("%Y", Expenditure.date) == str(year)
        )
    ).group_by(Expenditure.category)
    exp_result = await db.execute(exp_stmt)
    spent_by_cat = {row.category: row.total_spent for row in exp_result}

    total_spent = sum(spent_by_cat.values()) if spent_by_cat else 0.0

    # Build category breakdown
    all_categories = set(list(allocations.keys()) + list(spent_by_cat.keys()))
    by_category: List[CategoryBudgetItem] = []
    for cat in sorted(all_categories):
        alloc_amt = allocations.get(cat, 0.0)
        spent_amt = spent_by_cat.get(cat, 0.0)
        util_pct = round((spent_amt / alloc_amt * 100) if alloc_amt > 0 else 0.0, 2)
        by_category.append(CategoryBudgetItem(
            category=cat,
            allocated=alloc_amt,
            spent=spent_amt,
            utilization_pct=util_pct,
            variance=round(alloc_amt - spent_amt, 2)
        ))

    # --- Monthly trend rows ---
    trend_stmt = select(MonthlyBudgetSummary).where(
        and_(
            MonthlyBudgetSummary.facility_id == facility_id,
            MonthlyBudgetSummary.year == year
        )
    ).order_by(MonthlyBudgetSummary.month)
    trend_result = await db.execute(trend_stmt)
    monthly_trend = trend_result.scalars().all()

    utilization_pct = round((total_spent / total_budget * 100) if total_budget > 0 else 0.0, 2)

    return FacilitySummaryResponse(
        facility_id=facility_id,
        fiscal_year=year,
        total_budget=total_budget,
        total_spent=total_spent,
        remaining=round(total_budget - total_spent, 2),
        utilization_pct=utilization_pct,
        by_category=by_category,
        monthly_trend=[MonthlyBudgetSummaryResponse.model_validate(m) for m in monthly_trend]
    )


@router.get(
    "/district-summary",
    response_model=DistrictAggregateSummary,
    summary="Aggregate economics data across all facilities (district view)"
)
async def get_district_summary(
    year: int = Query(..., description="Fiscal year"),
    month: Optional[int] = Query(None, ge=1, le=12),
    db: AsyncSession = Depends(get_db)
):
    """
    District-level rollup: total budget vs. spend across all facilities
    for the given fiscal year (and optional month).
    """
    # Total budget across all facilities for the year
    budget_stmt = select(func.sum(BudgetAllocation.allocated_amount)).where(
        BudgetAllocation.fiscal_year == year
    )
    budget_result = await db.execute(budget_stmt)
    total_budget = budget_result.scalar() or 0.0

    # Build expenditure filter
    exp_conditions = [func.strftime("%Y", Expenditure.date) == str(year)]
    if month:
        exp_conditions.append(func.strftime("%m", Expenditure.date) == f"{month:02d}")

    exp_stmt = select(
        Expenditure.facility_id,
        func.sum(Expenditure.amount).label("facility_spent")
    ).where(and_(*exp_conditions)).group_by(Expenditure.facility_id)
    exp_result = await db.execute(exp_stmt)
    facility_rows = exp_result.all()

    total_spent = sum(r.facility_spent for r in facility_rows)
    utilization_pct = round((total_spent / total_budget * 100) if total_budget > 0 else 0.0, 2)

    facility_breakdown = [
        {"facility_id": r.facility_id, "spent": round(r.facility_spent, 2)}
        for r in facility_rows
    ]

    return DistrictAggregateSummary(
        year=year,
        month=month,
        total_budget=round(total_budget, 2),
        total_spent=round(total_spent, 2),
        utilization_pct=utilization_pct,
        facility_breakdown=facility_breakdown
    )
