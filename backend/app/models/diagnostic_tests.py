# File: backend/app/models/diagnostic_tests.py
# Description: SQLAlchemy ORM model for diagnostic test availability audits, reagent stocks, and equipment health

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from backend.app.database import Base

class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    facility_id = Column(String(36), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    test_name = Column(String(120), nullable=False) # e.g. CBC, Malaria RDT, Dengue NS1, Sputum AFB, Blood Sugar
    category = Column(String(80), nullable=False) # Hematology, Infectious Disease, Biochemistry, Point of Care
    
    reagents_available = Column(Boolean, default=True)
    reagents_stock_units = Column(Integer, default=150)
    equipment_functional = Column(Boolean, default=True)
    tests_conducted_today = Column(Integer, default=0)
    average_turnaround_mins = Column(Integer, default=30)
    
    # Audit status: compliant, reagent_deficit, equipment_breakdown, non_compliant
    audit_compliance_status = Column(String(40), default="compliant")
    last_audited_at = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

