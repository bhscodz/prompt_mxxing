# File: backend/app/utils/seed_data.py
# Description: Realistic database seeder for Indian PHCs, CHCs, medicine stocks, patients, beds, doctors, and lab audits

import sys
import os
import asyncio
from datetime import datetime, date, timedelta

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models.facility import Facility
from app.models.inventory import MedicineStock, StockTransaction
from app.models.patient_crm import Patient, OPDVisit
from app.models.beds import Bed
from app.models.staff_attendance import DoctorStaff
from app.models.diagnostic_tests import DiagnosticTest
from app.models.alerts_interventions import InterventionAlert, RedistributionTransfer

SEED_FACILITIES = [
    {
        "name": "PHC Khed Shivapur",
        "code": "PHC-KHD-01",
        "facility_type": "PHC",
        "block_name": "Haveli",
        "latitude": 18.3541,
        "longitude": 73.8542,
        "catchment_population": 32000,
        "contact_person": "Dr. Sunita Kulkarni (Medical Officer)",
        "contact_phone": "+91 98230 11421",
        "distress_score": 72.5, # Red flagged!
        "operational_status": "critical_distress"
    },
    {
        "name": "CHC Bhor District Hub",
        "code": "CHC-BHR-01",
        "facility_type": "CHC",
        "block_name": "Bhor",
        "latitude": 18.1500,
        "longitude": 73.8400,
        "catchment_population": 125000,
        "contact_person": "Dr. Anand Joshi (Medical Superintendent)",
        "contact_phone": "+91 98220 88712",
        "distress_score": 18.0, # Healthy surplus hub
        "operational_status": "nominal"
    },
    {
        "name": "PHC Paud Valley",
        "code": "PHC-PAU-02",
        "facility_type": "PHC",
        "block_name": "Mulshi",
        "latitude": 18.5312,
        "longitude": 73.6120,
        "catchment_population": 28000,
        "contact_person": "Dr. Ramesh Patil (MO)",
        "contact_phone": "+91 98233 44521",
        "distress_score": 45.0, # Strained
        "operational_status": "strained"
    },
    {
        "name": "CHC Saswad Central",
        "code": "CHC-SSW-02",
        "facility_type": "CHC",
        "block_name": "Purandar",
        "latitude": 18.3444,
        "longitude": 74.0305,
        "catchment_population": 98000,
        "contact_person": "Dr. Pradeep Ghorpade (Surgeon)",
        "contact_phone": "+91 98224 55901",
        "distress_score": 24.0,
        "operational_status": "nominal"
    },
    {
        "name": "PHC Shirur Ghat",
        "code": "PHC-SHR-03",
        "facility_type": "PHC",
        "block_name": "Shirur",
        "latitude": 18.8258,
        "longitude": 74.3789,
        "catchment_population": 36000,
        "contact_person": "Dr. Meena Deshmukh (MO)",
        "contact_phone": "+91 98235 66789",
        "distress_score": 68.0, # Red flagged!
        "operational_status": "critical_distress"
    },
    {
        "name": "Sub-District Hospital Baramati",
        "code": "SDH-BRM-01",
        "facility_type": "Sub-District Hospital",
        "block_name": "Baramati",
        "latitude": 18.1517,
        "longitude": 74.5775,
        "catchment_population": 210000,
        "contact_person": "Dr. Vikas Jadhav (Chief Medical Officer)",
        "contact_phone": "+91 98221 33456",
        "distress_score": 12.0,
        "operational_status": "nominal"
    }
]

MEDICINES_CATALOG = [
    {"name": "Paracetamol 500mg", "category": "Analgesic", "unit": "tablets", "reorder": 1200, "burn": 180.0},
    {"name": "Amoxicillin 250mg", "category": "Antibiotic", "unit": "capsules", "reorder": 600, "burn": 75.0},
    {"name": "Oral Rehydration Salts (ORS)", "category": "Maternal & Child Care", "unit": "packets", "reorder": 500, "burn": 60.0},
    {"name": "Anti-Snake Venom (ASV) 10ml", "category": "Emergency Antidote", "unit": "vials", "reorder": 40, "burn": 3.0},
    {"name": "Oxytocin Injection 5 IU", "category": "Maternal Care", "unit": "ampoules", "reorder": 80, "burn": 8.0},
    {"name": "Metformin 500mg", "category": "Chronic / NCD", "unit": "tablets", "reorder": 1500, "burn": 110.0},
    {"name": "Rabies Vaccine", "category": "Vaccine", "unit": "vials", "reorder": 50, "burn": 5.0},
    {"name": "Iron & Folic Acid (IFA)", "category": "Maternal & Child Care", "unit": "tablets", "reorder": 2000, "burn": 150.0},
    {"name": "Ciprofloxacin 500mg", "category": "Antibiotic", "unit": "tablets", "reorder": 400, "burn": 40.0},
    {"name": "Artemether-Lumefantrine", "category": "Infectious Disease", "unit": "tablets", "reorder": 300, "burn": 25.0}
]

DIAGNOSTIC_TESTS_CATALOG = [
    {"name": "Complete Blood Count (CBC)", "category": "Hematology"},
    {"name": "Malaria Rapid Antigen (RDT)", "category": "Infectious Disease"},
    {"name": "Dengue NS1 Antigen", "category": "Infectious Disease"},
    {"name": "Blood Glucose (Fasting/PP)", "category": "Biochemistry"},
    {"name": "Sputum Smear for AFB (TB)", "category": "Pathology"},
    {"name": "Rapid Urine Pregnancy Test (UPT)", "category": "Point of Care"},
    {"name": "Lipid Profile", "category": "Biochemistry"},
    {"name": "Hemoglobin (Hb Estimator)", "category": "Hematology"},
    {"name": "Liver Function Test (LFT)", "category": "Biochemistry"},
    {"name": "Urine Routine & Microscopic", "category": "Pathology"}
]

async def seed_database():
    await init_db()
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        fac_check = await session.execute(select(Facility))
        if fac_check.scalars().first():
            print("[Seed] Database already populated with records.")
            return

        print("[Seed] Populating SwasthyaGrid AI facilities and health data...")
        facility_objs = []
        for fac_data in SEED_FACILITIES:
            f = Facility(**fac_data)
            session.add(f)
            facility_objs.append(f)
        await session.flush()

        # Seed Stocks for each facility
        # Make PHC Khed Shivapur and PHC Shirur intentionally low in some drugs, CHC Bhor surplus
        for fac in facility_objs:
            for med in MEDICINES_CATALOG:
                burn = med["burn"]
                reorder = med["reorder"]
                
                if fac.name == "PHC Khed Shivapur" and med["name"] in ["Anti-Snake Venom (ASV) 10ml", "Amoxicillin 250mg", "Oxytocin Injection 5 IU"]:
                    # Critical Deficit!
                    current_qty = int(burn * 1.5) # Only 1.5 days left!
                    risk_score = 0.95
                elif fac.name == "PHC Shirur Ghat" and med["name"] in ["Paracetamol 500mg", "Oral Rehydration Salts (ORS)"]:
                    # Critical Deficit!
                    current_qty = int(burn * 1.2)
                    risk_score = 0.90
                elif "CHC" in fac.name or "Hospital" in fac.name:
                    # Surplus Hub!
                    current_qty = int(reorder * 3.5)
                    risk_score = 0.05
                else:
                    current_qty = int(reorder * 1.8)
                    risk_score = 0.20

                days_supply = round(current_qty / max(1.0, burn), 1)
                
                stock = MedicineStock(
                    facility_id=fac.id,
                    medicine_name=med["name"],
                    category=med["category"],
                    batch_number=f"BAT-2026-{fac.code[:3]}-{med['name'][:3].upper()}",
                    expiry_date=date.today() + timedelta(days=365),
                    current_quantity=current_qty,
                    reorder_level=reorder,
                    daily_burn_rate=burn,
                    unit=med["unit"],
                    stockout_risk_score=risk_score,
                    days_of_supply=days_supply
                )
                session.add(stock)

        # Seed Beds for each facility
        wards = [
            ("General Male", 4),
            ("General Female", 4),
            ("Maternity / Labor", 4),
            ("Pediatric", 2),
            ("Emergency / Triage", 2),
            ("ICU / High Dependency", 2)
        ]
        
        for fac in facility_objs:
            bed_idx = 1
            for ward_name, count in wards:
                # PHCs have fewer beds than CHCs
                multiplier = 2 if "CHC" in fac.name or "Hospital" in fac.name else 1
                for _ in range(count * multiplier):
                    # Higher occupancy in Khed Shivapur
                    is_occupied = (bed_idx % 2 == 0) if "Khed" in fac.name else (bed_idx % 3 == 0)
                    bed = Bed(
                        facility_id=fac.id,
                        bed_number=f"B-{ward_name[:3].upper()}-{bed_idx:02d}",
                        ward_type=ward_name,
                        status="occupied" if is_occupied else "available",
                        oxygen_supported=(bed_idx % 2 == 1),
                        allocated_patient_name="Admitted Patient" if is_occupied else None,
                        admission_timestamp=datetime.utcnow() - timedelta(hours=bed_idx*3) if is_occupied else None
                    )
                    session.add(bed)
                    bed_idx += 1

        # Seed Doctors and Medical Staff
        roles = [
            ("Dr. Rajesh Gite", "Medical Officer"),
            ("Dr. Kavita Salunke", "Gynecologist / OBGYN"),
            ("Dr. Nitin More", "Pediatrician"),
            ("Sister Sunita Shinde", "Staff Nurse (In-Charge)"),
            ("Shri Nilesh Jagtap", "Pharmacist"),
            ("Dr. Yogesh Shinde", "AYUSH Medical Officer")
        ]
        for fac in facility_objs:
            for idx, (doc_name, doc_role) in enumerate(roles):
                # Simulated absenteeism at PHC Khed Shivapur
                is_absent = (fac.name == "PHC Khed Shivapur" and "Gynecologist" in doc_role)
                staff = DoctorStaff(
                    facility_id=fac.id,
                    full_name=f"{doc_name} ({fac.name.split()[1]})",
                    role=doc_role,
                    registration_number=f"MMC-2024-{8000 + idx}",
                    phone=f"+91 98220 {10000 + idx}",
                    shift_timing="Morning (08:00 - 14:00)" if idx < 3 else "Evening (14:00 - 20:00)",
                    is_on_duty_today=not is_absent,
                    biometric_punch_in=datetime.utcnow() - timedelta(hours=3) if not is_absent else None,
                    attendance_status="Absent" if is_absent else "Present"
                )
                session.add(staff)

        # Seed Diagnostic Test Audits
        for fac in facility_objs:
            for test_item in DIAGNOSTIC_TESTS_CATALOG:
                # Break Dengue & CBC in Khed Shivapur for realistic distress flag
                has_reagent = not (fac.name == "PHC Khed Shivapur" and test_item["name"].startswith("Dengue"))
                is_functional = not (fac.name == "PHC Shirur Ghat" and "CBC" in test_item["name"])
                
                compliance = "compliant"
                if not has_reagent:
                    compliance = "reagent_deficit"
                elif not is_functional:
                    compliance = "equipment_breakdown"
                    
                audit = DiagnosticTest(
                    facility_id=fac.id,
                    test_name=test_item["name"],
                    category=test_item["category"],
                    reagents_available=has_reagent,
                    reagents_stock_units=0 if not has_reagent else 180,
                    equipment_functional=is_functional,
                    tests_conducted_today=24 if compliance == "compliant" else 0,
                    average_turnaround_mins=25,
                    audit_compliance_status=compliance,
                    last_audited_at=datetime.utcnow()
                )
                session.add(audit)

        # Seed Sample Patients and OPD Visits
        sample_patients = [
            ("Aarav Suresh Pawar", 34, "Male", "+91 98231 11001", "Khed Village", "Viral fever with high temperature (102°F)", "immediate_red", 130, 85, 98, 102.1, 97),
            ("Savitri Baburao Shinde", 28, "Female", "+91 98231 11002", "Shivapur Hamlet", "Antenatal 3rd Trimester Checkup & anemia", "urgent_yellow", 110, 70, 78, 98.4, 99),
            ("Ganesh Tukaram More", 58, "Male", "+91 98231 11003", "Khed Village", "Uncontrolled Type-2 Diabetes & chest tightness", "immediate_red", 155, 95, 104, 98.6, 95),
            ("Pooja Santosh Jadhav", 6, "Female", "+91 98231 11004", "Saswad Outskirts", "Severe diarrhea, dehydration & vomiting", "urgent_yellow", 90, 60, 115, 99.1, 98),
            ("Ramchandra Shripati Patil", 67, "Male", "+91 98231 11005", "Bhor Rural", "Chronic Joint pain and osteoarthritis refill", "standard_green", 125, 80, 72, 98.2, 98)
        ]
        
        for idx, (p_name, p_age, p_gender, p_phone, p_vil, complaint, triage, s_bp, d_bp, pulse, temp, spo2) in enumerate(sample_patients):
            patient = Patient(
                abha_id=f"91-4829-1092-{1001 + idx}",
                full_name=p_name,
                age=p_age,
                gender=p_gender,
                phone=p_phone,
                village=p_vil,
                blood_group="B+" if idx % 2 == 0 else "O+"
            )
            session.add(patient)
            await session.flush()
            
            visit = OPDVisit(
                patient_id=patient.id,
                facility_id=facility_objs[idx % len(facility_objs)].id,
                token_number=f"T-{101 + idx:03d}",
                triage_category=triage,
                chief_complaint=complaint,
                systolic_bp=s_bp,
                diastolic_bp=d_bp,
                pulse_rate=pulse,
                temperature_f=temp,
                spo2=spo2,
                assigned_doctor_name="Dr. Sunita Kulkarni" if idx % 2 == 0 else "Dr. Anand Joshi",
                status="in_consultation" if idx == 0 else "waiting" if idx < 3 else "completed",
                diagnosis_notes="Acute febrile illness. Prescribed Paracetamol and fluids." if idx == 0 else None,
                prescribed_medicines="Tab Paracetamol 500mg TDS, ORS sachets" if idx == 0 else None
            )
            session.add(visit)

        # Seed Administrative Intervention Alert
        alert1 = InterventionAlert(
            facility_id=facility_objs[0].id, # Khed Shivapur
            alert_type="critical_stockout",
            severity="critical",
            title="CRITICAL: Emergency Antidote Stock Depletion at PHC Khed Shivapur",
            description="Anti-Snake Venom (ASV) and Oxytocin are below 48-hour safety thresholds with zero local buffer. Urgent inter-facility transfer required.",
            suggested_action="Approve emergency transfer of 30 vials ASV from CHC Bhor District Hub.",
            status="pending_review"
        )
        session.add(alert1)

        # Seed AI-Suggested Intra-District Transfer
        transfer1 = RedistributionTransfer(
            source_facility_id=facility_objs[1].id, # CHC Bhor (Surplus)
            target_facility_id=facility_objs[0].id, # PHC Khed Shivapur (Deficit)
            item_type="medicine",
            item_name="Anti-Snake Venom (ASV) 10ml",
            quantity=30,
            unit="vials",
            haversine_distance_km=23.4,
            estimated_transit_hours=0.7,
            urgency_reason="Target has < 1.5 days supply. Bhor CHC has 140 vials buffer.",
            status="suggested_by_ai"
        )
        session.add(transfer1)

        await session.commit()
        print("[Seed] Successfully seeded all facilities, stocks, beds, staff, and clinical data!")

if __name__ == "__main__":
    asyncio.run(seed_database())


# ────────────────────────────────────────────────────────────────────────────────
# Phase 2 Seeder: Users, Leave Types, Budget Allocations, Purchase Orders
# ────────────────────────────────────────────────────────────────────────────────

async def seed_phase2(session, facility_objs):
    """Seed Phase 2 models: users, leave types, budgets, purchase orders."""
    from app.models.auth import User, UserRole, SupportedLanguage
    from app.models.leave_management import LeaveType
    from app.models.economics import BudgetAllocation, PurchaseOrder
    from app.core.security import hash_password

    # Check if already seeded
    user_check = await session.execute(select(User))
    if user_check.scalars().first():
        print("[Seed] Phase 2 users already seeded.")
        return

    print("[Seed] Seeding Phase 2: users, leave types, budgets, purchase orders...")

    # ── Default Users ───────────────────────────────────────────────────────────
    default_users = [
        ("admin",       "admin@swasthya.gov.in",  "Admin User",      UserRole.SUPER_ADMIN,     "Admin1234",    None),
        ("dist_admin",  "district@swasthya.gov.in","District Admin",  UserRole.DISTRICT_ADMIN,  "District123",  None),
        ("dr_kulkarni", "kulkarni@khed.gov.in",   "Dr. Sunita Kulkarni", UserRole.MEDICAL_OFFICER, "Doctor1234", None),
        ("pharmacist1", "pharmacy@khed.gov.in",   "Nilesh Jagtap",   UserRole.PHARMACIST,      "Pharma1234",   None),
        ("receptionist","reception@khed.gov.in",  "Reception Staff", UserRole.RECEPTIONIST,    "Recept1234",   None),
        ("nurse1",      "nurse@bhor.gov.in",      "Sister Sunita Shinde", UserRole.NURSE,       "Nurse12345",   None),
    ]
    for username, email, full_name, role, password, fac in default_users:
        u = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            role=role,
            facility_id=fac,
            is_active=True,
            is_verified=True,
            preferred_language=SupportedLanguage.EN,
        )
        session.add(u)

    # ── Leave Types ─────────────────────────────────────────────────────────────
    leave_type_names = [
        ("Casual Leave",     12,  ["Medical Officer", "Facility Admin"]),
        ("Earned Leave",     30,  ["Medical Officer", "District Admin"]),
        ("Medical Leave",    20,  ["Medical Officer"]),
        ("Emergency Leave",   5,  ["Medical Officer"]),
        ("Maternity Leave",  180, ["District Admin"]),
        ("Study Leave",      15,  ["Facility Admin", "District Admin"]),
    ]
    for name, max_d, stages in leave_type_names:
        lt = LeaveType(
            name=name,
            max_days_per_year=max_d,
            requires_approval_stages=stages,
            is_active=True,
        )
        session.add(lt)

    # ── Budget Allocations ───────────────────────────────────────────────────────
    categories = [
        ("MEDICINES", 2000000),
        ("EQUIPMENT", 800000),
        ("STAFF_SALARIES", 5000000),
        ("UTILITIES", 300000),
        ("MAINTENANCE", 400000),
        ("CONSUMABLES", 600000),
        ("DIAGNOSTICS", 700000),
    ]
    year = datetime.utcnow().year
    for fac in facility_objs:
        multiplier = 2.5 if ("CHC" in fac.name or "Hospital" in fac.name) else 1.0
        for cat, base_amount in categories:
            ba = BudgetAllocation(
                facility_id=fac.id,
                fiscal_year=year,
                category=cat,
                allocated_amount=base_amount * multiplier,
                currency="INR",
            )
            session.add(ba)

    # ── Sample Purchase Orders ───────────────────────────────────────────────────
    sample_pos = [
        ("PHC Khed Shivapur", "Anti-Snake Venom (ASV) 10ml",  "MEDICINE", 50,  450.0),
        ("PHC Khed Shivapur", "Amoxicillin 250mg capsules",   "MEDICINE", 500, 12.0),
        ("CHC Bhor District Hub", "Digital X-Ray System",     "EQUIPMENT", 1,  350000.0),
        ("PHC Paud Valley",   "ORS Sachets",                  "MEDICINE", 1000, 8.0),
        ("PHC Shirur Ghat",   "CBC Analyser Reagent Kit",     "CONSUMABLE", 5,  12000.0),
    ]
    fac_map = {f.name: f.id for f in facility_objs}
    for fac_name, item_name, item_type, qty, unit_price in sample_pos:
        fac_id = fac_map.get(fac_name)
        if not fac_id:
            continue
        po = PurchaseOrder(
            facility_id=fac_id,
            item_type=item_type,
            item_name=item_name,
            quantity=qty,
            unit_price=unit_price,
            total_amount=qty * unit_price,
            vendor="Pune District Medical Stores Depot",
            expected_delivery_date=date.today() + timedelta(days=7),
            status="SUBMITTED",
        )
        session.add(po)

    print("[Seed] Phase 2 data seeded successfully.")


# ── Patch original seed_database to include Phase 2 ─────────────────────────────
_original_seed_database = seed_database

async def seed_database():  # type: ignore[misc]
    await init_db()
    async with AsyncSessionLocal() as session:
        # Check if already seeded (Phase 1)
        fac_check = await session.execute(select(Facility))
        if fac_check.scalars().first():
            # Phase 1 done; try Phase 2
            try:
                await seed_phase2(session, (await session.execute(select(Facility))).scalars().all())
                await session.commit()
            except Exception as e:
                print(f"[Seed] Phase 2 seed note: {e}")
            return

        # Run Phase 1 + Phase 2 fresh
        await _original_seed_database()

        # Re-open session for Phase 2 since Phase 1 committed
        async with AsyncSessionLocal() as session2:
            fac_objs = (await session2.execute(select(Facility))).scalars().all()
            await seed_phase2(session2, fac_objs)
            await session2.commit()
