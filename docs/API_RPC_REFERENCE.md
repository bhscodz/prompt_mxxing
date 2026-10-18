<!--
  File: docs/API_RPC_REFERENCE.md
  Description: Complete REST API, JSON-RPC 2.0, and WebSocket protocol reference for SwasthyaGrid AI
-->

# SwasthyaGrid AI — API & High-Speed RPC Protocol Reference

## 1. Protocol Architecture Overview

SwasthyaGrid AI provides three complementary data communication protocols:
1. **RESTful HTTP API** (`/api/v1/*`): Clean, standard CRUD for web dashboards and external integrations.
2. **High-Speed JSON-RPC 2.0** (`/api/rpc/v1`): Optimized sub-millisecond execution for remote edge PHCs, atomic batch operations, and accelerated AI model inferences.
3. **Real-Time WebSockets** (`/ws/live-district`): Push event stream for instant UI updates when stock burns, patients queue, or alerts trigger.

---

## 2. High-Speed JSON-RPC 2.0 Specification

**Endpoint**: `POST /api/rpc/v1`  
**Headers**: `Content-Type: application/json`

### Supported RPC Methods:

#### 1. `telemetry.ping`
Heartbeat check returning server timestamp.
```json
{
  "jsonrpc": "2.0",
  "method": "telemetry.ping",
  "params": {},
  "id": 1
}
```
**Response**:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "ok",
    "timestamp": 1792304409.93,
    "message": "Fast RPC Engine Online"
  },
  "error": null,
  "id": 1,
  "execution_time_ms": 0.11
}
```

#### 2. `telemetry.syncHealthCenterMetrics`
Atomic edge synchronization of telemetry, footfall, and bed occupancies in a single round-trip.
```json
{
  "jsonrpc": "2.0",
  "method": "telemetry.syncHealthCenterMetrics",
  "params": {
    "facility_id": "FAC-UUID-123",
    "footfall_count": 84,
    "occupied_beds_delta": 2
  },
  "id": 2
}
```

#### 3. `inventory.reportDispensation`
Sub-millisecond inventory dispensation deduction for busy pharmacy queues.
```json
{
  "jsonrpc": "2.0",
  "method": "inventory.reportDispensation",
  "params": {
    "stock_id": "STOCK-UUID-456",
    "quantity": 10,
    "notes": "OPD Dispense"
  },
  "id": 3
}
```
**Response**:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "stock_id": "STOCK-UUID-456",
    "medicine_name": "Paracetamol 500mg",
    "remaining_quantity": 230,
    "days_of_supply": 1.9,
    "is_critical": true
  },
  "id": 3,
  "execution_time_ms": 0.85
}
```

#### 4. `patient.quickRegisterTriage`
Rapid batch token generation for mass OPD camps and camps.
```json
{
  "jsonrpc": "2.0",
  "method": "patient.quickRegisterTriage",
  "params": {
    "facility_id": "FAC-UUID-123",
    "full_name": "Ramesh Pawar",
    "age": 42,
    "gender": "Male",
    "chief_complaint": "Acute febrile illness",
    "triage_category": "urgent_yellow",
    "systolic_bp": 130,
    "diastolic_bp": 85,
    "spo2": 97
  },
  "id": 4
}
```

#### 5. `ai.getDemandForecast`
Accelerated PyTorch Time Series Transformer forward pass via RPC.
```json
{
  "jsonrpc": "2.0",
  "method": "ai.getDemandForecast",
  "params": {
    "facility_id": "FAC-UUID-123",
    "facility_name": "PHC Khed Shivapur",
    "metric_type": "patient_footfall",
    "daily_burn_rate": 75.0
  },
  "id": 5
}
```

### Atomic Batch RPC Support
Send an array of RPC calls to execute concurrently in one round-trip:
```json
[
  { "jsonrpc": "2.0", "method": "telemetry.ping", "params": {}, "id": 101 },
  { "jsonrpc": "2.0", "method": "inventory.reportDispensation", "params": { "stock_id": "...", "quantity": 5 }, "id": 102 }
]
```

---

## 3. RESTful API Endpoints (`/api/v1`)

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/facilities` | GET | List all facilities with HFDI scores |
| `/api/v1/facilities/summary` | GET | Aggregated district operational KPIs |
| `/api/v1/facilities` | POST | Register a new health facility |
| `/api/v1/inventory` | GET | List medicine inventory and stockout risk |
| `/api/v1/inventory/warnings` | GET | AI-generated early stockout hazard alerts |
| `/api/v1/inventory/transaction` | POST | Inbound stock or dispensation ledger entry |
| `/api/v1/crm/patients` | GET | Search registered patients by ABHA / Name |
| `/api/v1/crm/opd-visits` | GET | Real-time digital OPD triage queue |
| `/api/v1/crm/opd-visits` | POST | Register OPD patient & issue token |
| `/api/v1/crm/opd-visits/{id}` | PATCH | Doctor clinical consultation & prescription |
| `/api/v1/beds` | GET | Live bed matrix with ward filters |
| `/api/v1/beds/{id}/allocate` | POST | 1-click bed admission |
| `/api/v1/beds/{id}/discharge` | POST | 1-click patient discharge |
| `/api/v1/attendance` | GET | Doctor and staff roster & punch logs |
| `/api/v1/attendance/punch` | POST | Record biometric punch in/out |
| `/api/v1/diagnostic-tests` | GET | Laboratory diagnostic test audits |
| `/api/v1/diagnostic-tests/{id}` | PATCH | Update reagent stock or equipment health |
| `/api/v1/ai/forecast` | GET | 14-day Time Series Transformer projection |
| `/api/v1/redistribution/recommendations` | GET | Compute intra-district transfer plan |
| `/api/v1/redistribution/transfers` | GET / POST | List or create inter-PHC transfer order |
| `/api/v1/redistribution/transfers/{id}/action` | POST | Approve, dispatch, or confirm receipt |
| `/api/v1/interventions` | GET / POST | Administrative distress alerts |
| `/api/v1/interventions/{id}/dispatch` | POST | Dispatch CMO administrative intervention |

---

## 4. Real-Time WebSocket Protocol

**Endpoint**: `ws://localhost:8000/ws/live-district`

### Broadcast Event Types:
- `NEW_OPD_VISIT`: Emitted when a new patient enters the triage queue.
- `OPD_VISIT_STATUS_CHANGED`: Emitted when a doctor completes a consultation.
- `STOCK_UPDATED`: Emitted when pharmacy dispenses drugs or receives stock.
- `BED_OCCUPIED` / `BED_VACATED`: Emitted on admission or discharge.
- `STAFF_ATTENDANCE_PUNCH`: Emitted on biometric punch in/out.
- `DIAGNOSTIC_AUDIT_UPDATED`: Emitted when reagent stocks or machines change.
- `NEW_DISTRICT_ALERT`: Emitted when HFDI exceeds threshold.
- `TRANSFER_STATUS_CHANGED`: Emitted on inter-facility consignment status updates.

