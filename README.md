<!--
  File: README.md
  Description: Root Documentation and Overview for SwasthyaGrid AI
-->

# 🏥 SwasthyaGrid AI (ArogyaSutra AI)
### Multilingual AI Platform for Real-Time District Health Centre (PHC/CHC) Management, Time Series Transformer Analytics & Smart Resource Redistribution

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.143-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/ML-PyTorch_2.10_Transformer-EE4C2C.svg?logo=pytorch)](https://pytorch.org)
[![React](https://img.shields.io/badge/Frontend-React_18_Vite_Tailwind-61DAFB.svg?logo=react)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL_Asyncpg-336791.svg?logo=postgresql)](https://www.postgresql.org)
[![RPC](https://img.shields.io/badge/Transport-JSON--RPC_2.0_Fast_IO-4CAF50.svg)](docs/API_RPC_REFERENCE.md)
[![Multilingual](https://img.shields.io/badge/i18n-6_Indian_Languages-FF9800.svg)](docs/FEATURES_GUIDE.md)

---

## 📌 Executive Overview

Primary Health Centres (PHCs) and Community Health Centres (CHCs) in rural and semi-urban districts face recurring operational gaps:
- **Medicine Stock-Outs**: Essential antibiotics, ORS, oxytocin, and anti-snake venom run dry before replenishment orders are placed.
- **Unmanaged Footfall Surges**: Seasonal outbreaks (Dengue, Malaria, viral fever) overwhelm local clinics while adjacent PHCs remain underutilized.
- **Bed Invisibility**: Inpatient, maternity, and observation beds are occupied or blocked without central coordination.
- **Doctor Absenteeism**: Unpredictable rosters leave clinics without obstetricians or general physicians.
- **Diagnostic Test Outages**: Reagent stockouts or machine downtimes silently stall diagnostic audits.

**SwasthyaGrid AI** transforms district healthcare administration into a real-time, predictive operating system.

---

## 🚀 Key Modules & Capabilities

| Module | Description | Key Tech |
|---|---|---|
| **Real-Time District Dashboard** | Live operational KPIs, distress heat map, and center-by-center health grid. | React, WebSockets, Tailwind |
| **Patient CRM & OPD Queue** | Digital token issuance, ABHA ID linkage, vitals capture, and triage categories (Immediate Red, Urgent Yellow, Standard Green). | React CRM, REST & Fast RPC |
| **Medicine Inventory & Hazards** | Real-time burn rates, days-of-supply countdown, batch tracking, and early stockout hazard alerts. | SQLAlchemy, Asyncpg, Python |
| **Live Bed Matrix** | Ward allocation across General, Maternity, Pediatric, Emergency, and ICU beds with oxygen support flags. | WebSockets, FastAPI |
| **Doctor Attendance & Roster** | Biometric punch logs, shift timings, and automated specialty coverage audit (e.g. alerts when OBGYN is missing). | Biometric RPC, FastAPI |
| **Diagnostic Test Audits** | 20+ National Free Diagnostics Initiative tests, reagent stock audits, and equipment operational status. | SQLAlchemy ORM |
| **Time Series Transformer** | PyTorch multi-head self-attention deep learning model forecasting 14-day footfall and medicine demand with 90% confidence bands. | PyTorch 2.10, NumPy, SciPy |
| **Smart Redistribution Engine** | Algorithmic intra-district resource balancing transferring surplus stock from central hubs to deficit rural PHCs using Geodesic Haversine routing. | Haversine Optimizer |
| **District Interventions Portal** | Automated Health Facility Distress Index (HFDI) ranking and 1-click administrative order dispatch for District Collector & CMO. | FastAPI, WebSockets |
| **Multilingual Engine** | Instant seamless switching across 6 Indian languages: English, हिन्दी, मराठी, தமிழ், తెలుగు, and বাংলা. | Custom React i18n Hook |

---

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph EdgeCentres["PHCs & CHCs Edge Tier"]
        PHC1["PHC Khed Shivapur\n(OPD & Pharmacy)"]
        PHC2["PHC Shirur Ghat\n(Maternity & Labs)"]
        CHC1["CHC Bhor District Hub\n(Surplus Buffer)"]
    end

    subgraph Ingestion["Fast I/O Tier"]
        RPC["High-Speed JSON-RPC 2.0\n(/api/rpc/v1)"]
        REST["RESTful API\n(/api/v1/*)"]
        WS["Real-Time WebSocket Broker\n(/ws/live-district)"]
    end

    subgraph CoreBackend["FastAPI Core (Python 3.13)"]
        CRM["Patient CRM & OPD Queue"]
        Stock["Stock Ledger & Burn Engine"]
        Beds["Bed & Ward Orchestrator"]
        Staff["Biometric Attendance"]
        Audits["Diagnostic Compliance"]
    end

    subgraph AIEngine["AI Predictive Tier"]
        TST["PyTorch Time Series Transformer\n(Self-Attention, d=64, heads=4)"]
        Distress["Health Facility Distress Index (HFDI)"]
        Redist["Intra-District Haversine Rebalancing"]
    end

    subgraph Persistence["Storage Tier"]
        DB[("PostgreSQL / SQLite\n(Asyncpg / SQLAlchemy)")]
    end

    subgraph FrontendApp["React 18 Dashboard (Vite + Tailwind)"]
        UI["Multilingual UI (6 Indian Languages)"]
    end

    EdgeCentres -->|Fast RPC Telemetry| RPC
    EdgeCentres -->|REST API| REST
    RPC --> CoreBackend
    REST --> CoreBackend
    CoreBackend --> DB
    CoreBackend --> AIEngine
    CoreBackend --> WS
    WS --> FrontendApp
    REST <--> FrontendApp
```

---

## ⚡ Quick Start

### 1. Launch with One-Click Script (Windows)
```powershell
# In PowerShell:
.\start.ps1

# Or in Windows CMD:
start.bat
```

### 2. Manual Startup

#### Backend:
```bash
# Set PYTHONPATH
$env:PYTHONPATH="."

# Run backend with virtual environment
backend\.venv\Scripts\python.exe backend\run_backend.py
```
> Backend runs at `http://127.0.0.1:8000`  
> Interactive OpenAPI documentation: `http://127.0.0.1:8000/docs`

#### Frontend:
```bash
cd frontend
npm run dev
```
> Frontend runs at `http://localhost:3000`

### 3. Docker Compose (PostgreSQL + FastAPI + Nginx React)
```bash
docker-compose up --build -d
```

---

## 📚 Complete Documentation

- 📐 [Architectural Design Document](docs/ARCHITECTURE_DESIGN.md) — System design, Time Series Transformer math, and ER diagram.
- 📖 [User & Feature Guide](docs/FEATURES_GUIDE.md) — Complete user manual for all 9 modules and workflows.
- 🔌 [API & RPC Reference](docs/API_RPC_REFERENCE.md) — REST endpoints, JSON-RPC 2.0 methods, and WebSocket events.
- 🚀 [Deployment & Setup Guide](docs/DEPLOYMENT_AND_USAGE.md) — Local setup, PostgreSQL configuration, and Docker deployment.

---

## 🛡️ License
Built for Public Health Infrastructure Optimization under Open Source Healthcare Guidelines.

