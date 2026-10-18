# File: backend/app/models/economics.py
# Description: SQLAlchemy ORM models for health centre financial management —
#              budget allocations, expenditures, purchase orders, and monthly budget summaries

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Date, ForeignKey, Text
)
from app.database import Base


class BudgetAllocation(Base):
    """Annual budget allocated per category per facility"""
    __tablename__ = "budget_allocations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(
        String(36),
        ForeignKey("facilities.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    fiscal_year = Column(Integer, nullable=False)  # e.g. 2025 means FY 2025-26
    # Category must be one of: MEDICINES, EQUIPMENT, STAFF_SALARIES, UTILITIES,
    #                           MAINTENANCE, CONSUMABLES, DIAGNOSTICS
    category = Column(String(60), nullable=False)
    allocated_amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), default="INR")
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<BudgetAllocation {self.facility_id} {self.fiscal_year} {self.category}>"


class Expenditure(Base):
    """Individual expenditure transactions recorded per facility"""
    __tablename__ = "expenditures"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(
        String(36),
        ForeignKey("facilities.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # Category matches BudgetAllocation categories for easy cross-referencing
    category = Column(String(60), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    invoice_number = Column(String(100), nullable=True)
    vendor = Column(String(200), nullable=True)
    date = Column(Date, nullable=False, default=datetime.utcnow)
    approved_by = Column(String(150), nullable=True)  # Name / employee ID
    # Payment status: PENDING | PAID | DISPUTED
    payment_status = Column(String(20), nullable=False, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Expenditure {self.facility_id} {self.category} ₹{self.amount}>"


class PurchaseOrder(Base):
    """Purchase orders raised by facilities for medicines, equipment, or consumables"""
    __tablename__ = "purchase_orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(
        String(36),
        ForeignKey("facilities.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # Item type: MEDICINE | EQUIPMENT | CONSUMABLE
    item_type = Column(String(30), nullable=False)
    item_name = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False, default=0.0)
    total_amount = Column(Float, nullable=False, default=0.0)  # quantity × unit_price
    vendor = Column(String(200), nullable=True)
    expected_delivery_date = Column(Date, nullable=True)
    actual_delivery_date = Column(Date, nullable=True)
    # Status: DRAFT | SUBMITTED | APPROVED | DELIVERED | CANCELLED
    status = Column(String(20), nullable=False, default="DRAFT")
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PurchaseOrder {self.item_name} qty={self.quantity} status={self.status}>"


class MonthlyBudgetSummary(Base):
    """Pre-computed monthly rollup of budget vs. actual spend for quick dashboard reads"""
    __tablename__ = "monthly_budget_summaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(
        String(36),
        ForeignKey("facilities.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)           # 1–12
    total_budget = Column(Float, nullable=False, default=0.0)
    total_spent = Column(Float, nullable=False, default=0.0)
    budget_utilization_pct = Column(Float, nullable=False, default=0.0)  # 0–100
    variance = Column(Float, nullable=False, default=0.0)                # budget − spent
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<MonthlyBudgetSummary {self.facility_id} "
            f"{self.year}-{self.month:02d} util={self.budget_utilization_pct:.1f}%>"
        )
