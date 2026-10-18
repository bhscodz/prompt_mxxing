# TODO.md — SwasthyaGrid AI: Master Context, Architecture & Implementation Roadmap

> **Target Audience**: Any AI agent or developer picking up this project.
> **Last Updated**: 2026-10-18
> **Workspace Root**: `d:\prompt_mxxing`
> **Project Goal**: Multilingual AI platform for real-time health centre (PHC/CHC) management covering stock monitoring, patient footfall, bed availability, doctor/staff attendance, planned & emergency leaves, test availability audits, early stock-out warnings, AI-driven demand forecasting (PatchTST, XGBoost, ARIMA), multi-stage CRM approvals, single-node economics/expenditure, a multi-node district graph redistribution engine, and a LangGraph-based multilingual AI assistant (6 Indian languages).

---

## 1. Complete Project Context & User Instructions

### The Problem
Primary Health Centres (PHCs) and Community Health Centres (CHCs) in Indian rural/semi-urban districts suffer from recurring operational gaps:
- Unpredicted medicine stock-outs.
- Unmanaged patient footfall and OPD surges.
- Bed unavailability with no visibility across nearby centres.
- Unpredictable doctor/staff absenteeism.
- Tracking is largely manual and siloed, leading to delayed interventions.

### The Challenge & Architecture Requirements
The platform must model each hospital/centre as an autonomous **Single Node** in a **Connected District Graph**:

#### Single Node Core Pillars (Single Source of Truth)
1. **Staff & Attendance Management**:
   - Digital punch attendance.
   - Advance planned leaves for doctors and staff.
   - Emergency leave application with a multi-stage approval CRM (Staff -> Supervisor -> Medical Officer -> Admin).
   - Role-Based Access Control (RBAC) with secure authentication (JWT).
   - Coverage gap detection (alerts when a facility has fewer doctors/nurses than mandated).

2. **Sub-Department Stock Management**:
   - Distinct departments responsible for their own supplies (Pharmacy, Lab Reagents, OT/Surgical, Maternal/Obstetrics, Pediatrics, Radiology, General Stores).
   - Manual, audit-logged stock adjustments by authorized personnel only.
   - Purchase order tracking with Estimated Time of Arrival (ETA).

3. **Patient Footfall & Bed Management**:
   - Real-time intake by receptionists so data updates live.
   - OPD queue and triage.
   - Bed occupancy tracking across General, Maternity, and ICU wards.
   - Diagnostic tests turnaround and availability auditing.

4. **Forecasting Engine & Dual-Mode Depletion Alerts**:
   - **Model Ensemble Strategy**:
     - **PatchTST (Time Series Transformer)** for rich historical data (long sequences).
     - **XGBoost Regressor** for simple/sparse series or series with exogenous features (day of week, rainfall, festival days).
     - **ARIMA / Statsmodels** as fallback for short-horizon baseline series.
     - **Pluggable Model Router** (`forecast_router.py`) to automatically select or let admin pick.
   - **Dual Warning Types**:
     - **Warning Type 1 (Real-Time Resource Depletion)**: Triggered when `current_stock / daily_consumption < threshold` (e.g., < 3 days remaining).
     - **Warning Type 2 (Forecasted Resource Depletion with ETA Awareness)**: Triggered when predicted consumption will exhaust stock before the purchase order's ETA arrives.

5. **Hospital Economics & Expected Expenditure Dashboard**:
   - Annual/Monthly budget allocations across 7 categories (Medicines, Equipment, Salaries, Utilities, Maintenance, Consumables, Diagnostics).
   - Operational expense logging, invoice tracking, vendor management.
   - Monthly burn rate, budget utilization percentage, and projected expenditure variance.

6. **Multi-Node District Graph & Smart Redistribution**:
   - Connects all PHCs and CHCs in a district graph.
   - Haversine distance-optimized stock redistribution engine to transfer surplus supplies to deficit centres before stockouts occur.
   - Healthcare Facility Distress Index (HFDI) to automatically flag red/yellow centres to district administrators (CMO / District Collector).

7. **Multilingual AI Conversational Agent (LangGraph)**:
   - Voice/chat assistant for administrative and medical staff to query status in natural language.
   - LangGraph StateGraph (detect language -> classify intent -> execute DB query -> format response).
   - Offline-capable template responses + OpenAI LLM fallback.
   - Supports 6 Indian languages: English (en), Hindi (hi), Marathi (mr), Tamil (ta), Telugu (te), Bengali (bn).

---

## 2. Technology Stack & Operational Environment

- **Backend**: FastAPI (Python 3.13), SQLAlchemy 2.0 (Asyncio), Pydantic v2.
- **Database**:
  - Primary: **PostgreSQL 16** via Docker container (`swasthya_postgres` running on port 5432).
  - Secondary/Fallback: **SQLite** via `aiosqlite` (`swasthya_grid.db`).
- **High-Speed Communication**:
  - JSON-RPC 2.0 endpoint (`/api/rpc/v1`) for low-overhead telemetry and mobile/satellite connectivity.
  - WebSockets (`/ws/live-district` and `/ws/agent-chat`) for real-time live updates.
- **Frontend**: React 18, Vite, TailwindCSS, Recharts, Lucide Icons.
- **Machine Learning**: PyTorch (`torch`), XGBoost, Statsmodels, Scikit-Learn.
- **AI Agent**: LangGraph, LangChain, LangDetect.

---

## 3. Current Progress & File Inventory Audit

### A. Infrastructure & Configuration
- [x] `d:\prompt_mxxing\docker-compose.yml` (PostgreSQL container `swasthya_postgres` on port 5432)
- [x] `d:\prompt_mxxing\.env` (DB URLs, JWT Secrets, District Defaults)
- [x] `d:\prompt_mxxing\backend\app\config.py` (Pydantic settings with dual DB support)
- [x] `d:\prompt_mxxing\backend\app\database.py` (Async engine and sessionmaker)

### B. Phase 1 Core Modules (100% Completed & Verified)
- [x] `backend/app/models/facility.py` (PHC/CHC Node model)
- [x] `backend/app/models/inventory.py` (Medicine stock and transactions)
- [x] `backend/app/models/patient_crm.py` (Patient demographic and OPD visits)
- [x] `backend/app/models/beds.py` (Bed status, wards)
- [x] `backend/app/models/staff_attendance.py` (Doctor/Staff profiles & punches)
- [x] `backend/app/models/diagnostic_tests.py` (Lab test records and audit)
- [x] `backend/app/models/alerts_interventions.py` (Distress flags and redistribution transfers)
- [x] `backend/app/ml/redistribution_engine.py` (Haversine distance optimization)
- [x] `backend/app/ml/anomaly_flagging.py` (HFDI distress index calculations)
- [x] `backend/app/rpc/jsonrpc_server.py` (JSON-RPC 2.0 batch handler)
- [x] `backend/app/utils/seed_data.py` (Seeds 6 Pune Rural facilities, 60 medicines, 162 beds, 36 staff)
- [x] `frontend/src/i18n/translations.js` & `LanguageContext.jsx` (Complete 6 languages)
- [x] Core Frontend Pages: `Dashboard.jsx`, `PatientCRM.jsx`, `InventoryStock.jsx`, `BedManagement.jsx`, `DoctorAttendance.jsx`, `DiagnosticAudits.jsx`, `RedistributionEngine.jsx`, `DistrictInterventions.jsx`.

### C. Phase 2 Elements Already Created
- [x] `backend/app/models/auth.py` (`User`, `UserSession`, `AuditLog` models)
- [x] `backend/app/schemas/auth.py` (User & Token Pydantic schemas)
- [x] `backend/app/models/leave_management.py` (`LeaveType`, `LeaveRequest`, `LeaveApproval`, `LeaveBalance`, `ShiftCoverage`)
- [x] `backend/app/schemas/leave_management.py`
- [x] `backend/app/api/leave_management.py` (Full multi-stage approval CRM, calendar view, coverage gaps)
- [x] `frontend/src/pages/LeaveManagementPage.jsx` (Complete tabbed leave UI with calendar & balance bars)
- [x] `backend/app/models/economics.py` (`BudgetAllocation`, `Expenditure`, `PurchaseOrder`, `MonthlyBudgetSummary`)
- [x] `backend/app/schemas/economics.py`
- [x] `backend/app/api/economics.py` (Budget, expense logging, purchase orders, burn rate)
- [x] `backend/app/ml/xgboost_forecaster.py` (XGBoost time series model with lag & rolling features)
- [x] `backend/app/ml/arima_forecaster.py` (Statsmodels auto-order ARIMA model)

---

## 4. Master TODO List (Remaining Tasks)

Any agent continuing this project should follow this sequence:

### Priority 1: Auth, Security & RBAC Completion
- [ ] Create `backend/app/core/security.py`:
  - Password hashing with bcrypt.
  - JWT creation & decoding (`python-jose`).
  - FastAPI dependency `get_current_user` and `require_roles(["SUPER_ADMIN", "FACILITY_ADMIN", ...])`.
- [ ] Create `backend/app/api/auth.py`:
  - `POST /api/v1/auth/login` (returns JWT + user details).
  - `POST /api/v1/auth/register` (admin only).
  - `GET /api/v1/auth/me` (profile).
  - `POST /api/v1/auth/refresh` & `POST /api/v1/auth/logout`.
- [ ] Create frontend auth services:
  - `frontend/src/services/authService.js`
  - `frontend/src/context/AuthContext.jsx`
  - `frontend/src/components/ProtectedRoute.jsx`
  - `frontend/src/pages/LoginPage.jsx`

### Priority 2: PatchTST, Model Router & Dual Alert Engine
- [ ] Create `backend/app/ml/patchtst.py`:
  - PyTorch implementation of PatchTST (Patching, Transformer Encoder, Linear Head).
  - Train/Predict wrappers with standard confidence interval output.
- [ ] Create `backend/app/ml/forecast_router.py`:
  - Analyze data length and variance.
  - Route to PatchTST (if n >= 60), XGBoost (if n >= 30), or ARIMA (if n >= 14).
- [ ] Create `backend/app/ml/alert_engine.py`:
  - **Type 1 (Real-Time Depletion)**: Evaluates current stock against daily consumption rate.
  - **Type 2 (Forecasted Depletion with ETA)**: Evaluates projected run-out date vs PurchaseOrder expected delivery date.
- [ ] Create `backend/app/api/forecasting.py`:
  - Expose medicine, footfall, and bed forecasts.
  - Expose `/api/v1/forecast/run-alerts/{facility_id}`.
- [ ] Create `frontend/src/pages/ForecastingPage.jsx`:
  - Recharts ComposedChart with confidence intervals.
  - Dual-mode alert cards (Real-time vs Forecasted ETA).

### Priority 3: LangGraph Multilingual AI Agent
- [ ] Create `backend/app/ai_agent/agent.py`:
  - LangGraph StateGraph workflow:
    - Node 1: `detect_language` (langdetect / regex fallback).
    - Node 2: `classify_intent` (Inventory, Footfall, Staff, Beds, Alerts, Economics).
    - Node 3: `query_data` (Async SQLAlchemy query to node database).
    - Node 4: `format_response` (Dictionary templates in 6 languages or OpenAI GPT-4o-mini).
- [ ] Create `backend/app/api/ai_agent.py`:
  - `POST /api/v1/agent/chat`
  - `WebSocket /ws/agent-chat`
- [ ] Create `frontend/src/pages/AIAgentChat.jsx`:
  - Conversational UI with quick prompt chips in all 6 languages.

### Priority 4: Economics Dashboard Frontend
- [ ] Create `frontend/src/pages/EconomicsDashboard.jsx`:
  - KPI Cards: Total Budget, Total Spent, Remaining, Burn Rate.
  - Recharts: Budget vs Actual by category.
  - Purchase Orders table with ETA tracking.

### Priority 5: Full Integration & Seeding
- [ ] Update `backend/app/models/__init__.py` to import and export all Phase 2 models.
- [ ] Update `backend/app/main.py` to register all new routers (`auth`, `leave_management`, `economics`, `forecasting`, `ai_agent`).
- [ ] Update `backend/app/utils/seed_data.py`:
  - Seed default users with roles (Admin, Doctor, Pharmacist, Receptionist).
  - Seed leave types, sample leave requests, budget allocations, and purchase orders.
- [ ] Update `frontend/src/App.jsx` and `Sidebar.jsx`:
  - Add navigation links for Leave Management, Forecasting, AI Assistant, and Economics.
  - Configure protected routing.

---

## 5. Helpful Commands for Continuation

### Start Backend Locally
```powershell
# From workspace root d:\prompt_mxxing
.\backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Start Frontend Locally
```powershell
cd d:\prompt_mxxing\frontend
npm run dev
```

### Verify PostgreSQL in Docker
```powershell
docker ps
# If stopped:
docker-compose up -d db
```

### Test API Health
```powershell
curl http://127.0.0.1:8000/health
```

