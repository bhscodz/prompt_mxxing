<!--
  File: docs/FEATURES_GUIDE.md
  Description: User and Administrator Feature Guide for SwasthyaGrid AI
-->

# SwasthyaGrid AI — User & Feature Guide

This guide provides an end-to-end operational manual for District Administrators, Chief Medical Officers (CMOs), Medical Officers, Pharmacists, and Laboratory Technicians using SwasthyaGrid AI.

---

## 1. Multilingual Support & Instant Language Switching

Healthcare workers across India's states operate in regional languages. SwasthyaGrid AI provides native language support without page reloads.

### Supported Languages:
- **English** (`en`)
- **Hindi** (`hi` — हिन्दी)
- **Marathi** (`mr` — मराठी)
- **Tamil** (`ta` — தமிழ்)
- **Telugu** (`te` — తెలుగు)
- **Bengali** (`bn` — বাংলা)

### How to use:
1. In the top-right corner of the top navigation bar, click the **Globe / Language selector** dropdown.
2. Select your preferred native language.
3. All module titles, clinical triage priorities, stockout badges, bed statuses, and action buttons will dynamically switch into the chosen language.

---

## 2. Real-Time District Command Dashboard

The Command Dashboard gives district-level leadership a high-level operational overview of every Primary Health Centre (PHC) and Community Health Centre (CHC) in the district.

### Key Metrics:
- **Total Facilities**: Breakdown of PHCs, CHCs, and Sub-District Hospitals.
- **Critical Stockouts**: Total essential drugs with fewer than 48 hours of supply.
- **Bed Occupancy**: Aggregate occupancy percentage across all inpatient wards.
- **Doctor Attendance**: Percentage of rostered medical staff currently punched in.
- **Facility Health Grid**: Visual cards for each facility displaying the **Health Facility Distress Index (HFDI: 0–100)**:
  - **Red Flag (HFDI $\ge 65$)**: Immediate administrative intervention required.
  - **Amber Flag ($35 \le \text{HFDI} < 65$)**: Strained facility under elevated operational pressure.
  - **Green ($\text{HFDI} < 35$)**: Resilient, nominal operation.

---

## 3. Digital OPD & Patient Triage CRM

The CRM module automates patient queueing, Ayushman Bharat Health Account (ABHA ID) linkage, triage classification, and clinical consultation.

### Registering a New Patient:
1. Click **Register New Patient** (or use the shortcut on the Dashboard).
2. Enter:
   - Full Name, ABHA ID (optional), Age, Gender, Village, Phone.
   - Chief Complaint (e.g., "Acute chest pain", "High fever with chills").
   - **Triage Priority**:
     - **Immediate (Red)**: Life-threatening emergencies (heart attack, snakebite, severe respiratory distress). Automatically elevated to top of queue.
     - **Urgent (Yellow)**: High fever, active dehydration, fracture.
     - **Standard (Green)**: Routine checkup, chronic refill, mild cough.
   - Baseline Triage Vitals: Systolic BP, Diastolic BP, Pulse Rate, SpO2, Temperature.
3. Toggle **Fast Sub-ms RPC** if operating in a high-density OPD camp to bypass REST overhead.
4. Click **Issue OPD Token** — a digital token (e.g., `T-104`) is immediately queued and broadcast via WebSocket to the doctor's screen.

### Doctor Consultation & Prescription:
1. Click **Consult / Prescribe** on any queued patient.
2. Review patient's chief complaint and vitals.
3. Enter Clinical Diagnosis and Prescribed Medicines.
4. Click **Complete & Save Consultation** to mark the visit complete and free up the doctor's queue.

---

## 4. Medicine Inventory & Early Stockout Warning System

Tracks daily drug burn rates, batch numbers, expiration dates, and days of supply remaining.

### Understanding Stockout Hazard Badges:
- **Critical Hazard (< 48h)** *(Pulsing Red)*: Drug is estimated to deplete within 2 days based on current burn rate and Transformer projection.
- **Early Warning (< 7d)** *(Amber)*: Drug has less than 7 days of supply remaining.
- **Optimal Stock** *(Emerald)*: Stock is safely above the reorder buffer.

### Quick Dispensation (Pharmacy Counter):
1. In the stock table, click **Quick Dispense** next to any medicine.
2. Select the quantity dispensed.
3. Ensure **Use Fast Sub-ms RPC** is checked for instant stock deduction in under 1 millisecond.
4. The remaining days of supply and stockout hazard status automatically recalculate.

---

## 5. Live Bed Matrix & Ward Allocation

Provides real-time visibility into bed occupancy across all wards to eliminate avoidable patient referral delays.

### Ward Categories:
- **General Male & Female**
- **Maternity / Labor Suites**
- **Pediatric Ward**
- **Emergency / Triage Beds**
- **ICU / High Dependency Units**

### Actions:
- **Filter Ward**: Click any ward pill at the top to isolate specific beds.
- **Allocate Bed**: Click **Allocate Bed** on any green available bed $\rightarrow$ enter patient name $\rightarrow$ confirms admission.
- **Oxygen Tag**: Beds with oxygen supply display an $O_2$ wind icon.
- **Discharge Patient**: Click **Discharge** on an occupied bed $\rightarrow$ clears patient allocation and resets bed status to available.

---

## 6. Doctor & Staff Biometric Attendance

Eliminates unpredictable doctor attendance by auditing attendance in real time and flagging specialty coverage gaps.

### Features:
- **Biometric Punch Simulation**: Click **Punch In** or **Punch Out / Leave** to update duty state.
- **Specialty Gap Audit**: If critical specialists (e.g., Gynecologist / OBGYN, Pediatrician) are absent on duty today, the system raises an alert banner:
  > *"Specialist Coverage Audit Gap: No Gynecologist on duty today at PHC Khed Shivapur! District CMO notified for roving specialist dispatch."*

---

## 7. Diagnostic Test Availability Audits

Audits laboratory diagnostic testing capacity under the National Free Diagnostics Service Initiative.

### How to audit a test:
1. Locate the test (e.g., CBC, Malaria RDT, Dengue NS1, Blood Glucose).
2. Click **Audit**.
3. Update **Reagent Units in Stock** and toggle **Equipment Operational / Breakdown**.
4. If reagents drop below 10 units or equipment breaks down, the compliance badge immediately shifts to **Reagent Deficit** or **Equipment Breakdown**, raising the facility's distress index.

---

## 8. PyTorch Time Series Transformer Demand Forecasting

Leverages a custom Multi-Head Self-Attention Transformer model to predict future demand 14 days in advance.

### Using the Visualizer:
1. Navigate to **AI Transformer Forecasts**.
2. Select metric:
   - **Patient Footfall Forecast**
   - **Medicine Consumption Forecast** (select drug from dropdown)
   - **Bed Demand Projection**
3. Select the facility to inspect.
4. The interactive SVG chart renders:
   - **Blue line**: Historical 30-day recorded trajectory.
   - **Teal dashed line**: Transformer 14-day forecasted trajectory.
   - **Teal shaded envelope**: 90% Confidence Interval band.
   - **Hover tooltip**: Inspect exact values on any historical or predicted day.
5. Review the **Attention Weights breakdown**:
   - Weekly Periodicity (42%)
   - Moving Trend (38%)
   - Epidemic Outbreak Factor (20%)

---

## 9. Smart Intra-District Resource Redistribution Engine

Automatically rebalances inventory across the district by identifying deficit PHCs and matching them with the nearest surplus CHCs.

### Workflow:
1. The engine runs continuous balancing:
   - Identifies deficit facilities ($\text{Days of supply} < 7$).
   - Identifies surplus facilities ($\text{Days of supply} > 21$).
   - Calculates great-circle Geodesic Haversine distance and estimated transit time in hours.
2. In **AI Recommendations**, review the proposed transfer order:
   - e.g., *"Transfer 30 vials Anti-Snake Venom from CHC Bhor Hub (Surplus) to PHC Khed Shivapur (Deficit) • 23.4 km • ~0.7 hrs"*.
3. Click **Approve & Dispatch**.
4. In the **Dispatched Transfers** tab:
   - Click **Mark In Transit** when the ambulance or transport van departs.
   - Click **Confirm Receipt & Adjust Stocks** when the consignment arrives $\rightarrow$ the system automatically debits the donor facility and credits the recipient facility in the database!

---

## 10. District Administrative Intervention Center (CMO / Collector)

Designed specifically for District Magistrates, Collectors, and Chief Medical Officers.

### Workflow:
1. View facilities ranked from highest to lowest **Distress Score (HFDI)**.
2. Inspect active alerts (e.g., critical stockouts, absent specialists, saturated beds).
3. Click **Take Action** on any alert:
   - Enter administrative orders (e.g., *"Dispatch Mobile Medical Unit 3 and 40 vials ASV to PHC Khed Shivapur"*).
   - Enter authorizing official name.
   - Click **Dispatch to Block Officer** or **Mark Resolved**.
4. The dispatched action is recorded and broadcast in real time across the district grid.

