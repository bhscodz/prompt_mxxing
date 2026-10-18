<!--
  File: docs/DEPLOYMENT_AND_USAGE.md
  Description: Deployment and operational guide for SwasthyaGrid AI across local dev, Docker, and PostgreSQL
-->

# SwasthyaGrid AI — Deployment & Setup Guide

This guide covers running SwasthyaGrid AI locally for development, configuring PostgreSQL, and deploying with Docker Compose.

---

## Prerequisites

- **Python**: 3.10+ (Tested on Python 3.13)
- **Node.js**: v18+ (Tested on Node v22.20)
- **Docker & Docker Compose**: (Optional, for containerized PostgreSQL deployment)

---

## 1. Quick Local Development Setup (One-Click)

The platform is designed to run seamlessly out of the box with zero complex external dependencies required for initial evaluation.

### Option A: Using 1-Click Launchers (Windows)
```powershell
# In PowerShell:
.\start.ps1

# Or in Windows Command Prompt:
start.bat
```

### Option B: Manual Terminal Execution

#### 1. Backend:
```bash
# Set PYTHONPATH
$env:PYTHONPATH="."  # (On Windows PowerShell)
# export PYTHONPATH=. # (On Linux/macOS)

# Activate virtualenv and run backend
backend\.venv\Scripts\python.exe backend\run_backend.py
```
Backend will start on `http://127.0.0.1:8000`.

#### 2. Frontend:
```bash
cd frontend
npm install
npm run dev
```
Frontend will be available on `http://localhost:3000`.

---

## 2. PostgreSQL Configuration

By default, the platform runs with an asynchronous SQLite database (`swasthya_grid.db`) for immediate evaluation. Switching to PostgreSQL is as simple as providing the connection string.

### Setting up PostgreSQL:
1. Ensure PostgreSQL is running on port 5432.
2. Create the target database:
   ```sql
   CREATE DATABASE swasthya_db;
   ```
3. Set the `DATABASE_URL` environment variable:
   ```bash
   # Windows PowerShell:
   $env:DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/swasthya_db"

   # Linux/macOS:
   export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/swasthya_db"
   ```
4. Run `backend\app\utils\seed_data.py` to auto-seed the schema and sample district data:
   ```bash
   backend\.venv\Scripts\python.exe backend\app\utils\seed_data.py
   ```

---

## 3. Production Deployment with Docker Compose

To run the full stack with PostgreSQL, FastAPI backend, and Nginx-proxied React frontend in containers:

```bash
docker-compose up --build -d
```

### Services launched:
- `swasthya_postgres`: PostgreSQL 16 on port `5432`.
- `swasthya_backend`: FastAPI Python 3.13 backend on port `8000`.
- `swasthya_frontend`: Production Vite React build served via Nginx on port `3000`.

To inspect logs:
```bash
docker-compose logs -f backend
```

To stop:
```bash
docker-compose down
```

---

## 4. Verifying Installation & Health

1. **Backend Health Check**:
   ```bash
   curl http://127.0.0.1:8000/health
   ```
   Expected response:
   ```json
   {
     "status": "healthy",
     "service": "SwasthyaGrid AI",
     "version": "1.0.0",
     "district": "Pune Rural & Western Ghats"
   }
   ```

2. **Interactive OpenAPI Documentation**:
   Navigate to `http://127.0.0.1:8000/docs` to test all REST endpoints interactively.

3. **Fast RPC Benchmark**:
   ```bash
   backend\.venv\Scripts\python.exe backend\app\rpc\rpc_client_demo.py
   ```

4. **Web Dashboard**:
   Open `http://localhost:3000` in any modern web browser.

