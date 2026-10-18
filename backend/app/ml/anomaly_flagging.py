# File: backend/app/ml/anomaly_flagging.py
# Description: Automated district health center distress index (HFDI) and administrative red-flagging engine

from typing import List, Dict, Any, Tuple

class DistressEvaluationEngine:
    """
    Computes Health Facility Distress Index (HFDI: 0 to 100) based on 4 pillars:
    1. Medicine Stockout Severity (Weight: 30%)
    2. Doctor & Specialist Absenteeism (Weight: 25%)
    3. Bed Occupancy & Capacity Saturation (Weight: 25%)
    4. Diagnostic Test & Reagent Compliance (Weight: 20%)
    """

    @staticmethod
    def evaluate_facility(
        facility_id: str,
        facility_name: str,
        stocks: List[Dict[str, Any]],
        staff: List[Dict[str, Any]],
        beds: List[Dict[str, Any]],
        tests: List[Dict[str, Any]]
    ) -> Tuple[float, str, List[Dict[str, Any]]]:
        """
        Returns (distress_score, operational_status, generated_alerts)
        """
        generated_alerts = []
        
        # 1. Stockout Pillar (0-30 pts)
        stock_score = 0.0
        critical_stocks = [s for s in stocks if s.get("current_quantity", 0) < s.get("reorder_level", 100) * 0.3]
        if critical_stocks:
            stock_score = min(30.0, len(critical_stocks) * 10.0)
            items_str = ", ".join([s.get("medicine_name", "") for s in critical_stocks[:3]])
            generated_alerts.append({
                "facility_id": facility_id,
                "alert_type": "critical_stockout",
                "severity": "critical" if len(critical_stocks) > 1 else "high",
                "title": f"Critical Stock Exhaustion at {facility_name}",
                "description": f"{len(critical_stocks)} essential medications have breached emergency reserve levels: {items_str}.",
                "suggested_action": "Dispatch emergency replenishment buffer or initiate intra-district transfer from central CHC."
            })

        # 2. Doctor Attendance Pillar (0-25 pts)
        attendance_score = 0.0
        total_staff = len(staff)
        absent_staff = [st for st in staff if st.get("attendance_status") in ["Absent", "On Leave"] or not st.get("is_on_duty_today")]
        if total_staff > 0:
            absent_ratio = len(absent_staff) / total_staff
            if absent_ratio > 0.4:
                attendance_score = 25.0
            elif absent_ratio > 0.2:
                attendance_score = 15.0
                
            # Check specialist coverage (e.g. MO or OBGYN absent)
            critical_absentees = [st for st in absent_staff if "Doctor" in st.get("role", "") or "Officer" in st.get("role", "") or "OBGYN" in st.get("role", "")]
            if critical_absentees:
                generated_alerts.append({
                    "facility_id": facility_id,
                    "alert_type": "doctor_absenteeism",
                    "severity": "critical",
                    "title": f"Doctor Unavailability Flag at {facility_name}",
                    "description": f"Key medical officers absent today: {', '.join([c.get('full_name') for c in critical_absentees])}.",
                    "suggested_action": "Reroute roving medical officer from district pool or alert Block Medical Officer."
                })

        # 3. Bed Saturation Pillar (0-25 pts)
        bed_score = 0.0
        total_beds = len(beds)
        occupied_beds = [b for b in beds if b.get("status") == "occupied"]
        if total_beds > 0:
            occupancy_rate = len(occupied_beds) / total_beds
            if occupancy_rate >= 0.90:
                bed_score = 25.0
                generated_alerts.append({
                    "facility_id": facility_id,
                    "alert_type": "bed_saturation",
                    "severity": "high",
                    "title": f"Bed Capacity Overwhelmed ({int(occupancy_rate*100)}%) at {facility_name}",
                    "description": f"{len(occupied_beds)} of {total_beds} total beds are currently occupied.",
                    "suggested_action": "Divert non-emergency admissions to adjacent CHC or expedite discharge of stabilized patients."
                })
            elif occupancy_rate >= 0.75:
                bed_score = 15.0

        # 4. Diagnostic Audit Pillar (0-20 pts)
        test_score = 0.0
        broken_tests = [t for t in tests if not t.get("reagents_available") or not t.get("equipment_functional")]
        if broken_tests:
            test_score = min(20.0, len(broken_tests) * 7.0)
            generated_alerts.append({
                "facility_id": facility_id,
                "alert_type": "diagnostic_failure",
                "severity": "moderate",
                "title": f"Diagnostic Service Halt at {facility_name}",
                "description": f"{len(broken_tests)} essential laboratory tests halted due to reagent exhaustion or equipment outage.",
                "suggested_action": "Order expedited test cartridges and dispatch biomedical repair engineer."
            })

        # Composite Health Facility Distress Index
        total_hfdi = round(stock_score + attendance_score + bed_score + test_score, 1)

        if total_hfdi >= 65.0:
            status = "critical_distress"
        elif total_hfdi >= 35.0:
            status = "strained"
        else:
            status = "nominal"

        return total_hfdi, status, generated_alerts

distress_evaluator = DistressEvaluationEngine()

