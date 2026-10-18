# File: backend/app/ml/redistribution_engine.py
# Description: Intra-district smart resource redistribution optimizer using Haversine geodesic routing and multi-facility balancing

import math
from typing import List, Dict, Any, Tuple

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two GPS coordinates on Earth in kilometers.
    """
    R = 6371.0 # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = (math.sin(dphi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(dlambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)

class ResourceRedistributionEngine:
    """
    Balances medical inventory and emergency resources across PHCs/CHCs.
    Identifies centers with acute stock deficits (days_of_supply < 7)
    and pairs them with the nearest surplus centers (days_of_supply > 21).
    """

    @staticmethod
    def calculate_redistribution_plan(
        facilities: List[Dict[str, Any]], 
        stocks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generates optimal intra-district transfer recommendations.
        """
        facility_map = {f["id"]: f for f in facilities}
        recommendations = []
        
        # Group stocks by medicine_name
        grouped_stocks: Dict[str, List[Dict[str, Any]]] = {}
        for s in stocks:
            med_name = s["medicine_name"]
            grouped_stocks.setdefault(med_name, []).append(s)

        for med_name, med_stock_list in grouped_stocks.items():
            # Identify Deficits and Surpluses
            deficits = []
            surpluses = []
            
            for s in med_stock_list:
                current_qty = s["current_quantity"]
                burn_rate = max(1.0, s["daily_burn_rate"])
                days_supply = current_qty / burn_rate
                reorder = s["reorder_level"]
                
                if current_qty < reorder or days_supply < 7.0:
                    needed_qty = int((reorder * 1.5) - current_qty)
                    if needed_qty > 0:
                        deficits.append({
                            "facility_id": s["facility_id"],
                            "stock_id": s["id"],
                            "needed_quantity": needed_qty,
                            "days_supply": days_supply,
                            "unit": s.get("unit", "tablets")
                        })
                elif days_supply > 21.0 and current_qty > (reorder * 2.0):
                    # Retain 14 days safety stock, remainder is shareable surplus
                    shareable_surplus = int(current_qty - (burn_rate * 14))
                    if shareable_surplus > 50:
                        surpluses.append({
                            "facility_id": s["facility_id"],
                            "stock_id": s["id"],
                            "surplus_quantity": shareable_surplus,
                            "days_supply": days_supply,
                            "unit": s.get("unit", "tablets")
                        })
                        
            # Pair each deficit with the nearest eligible surplus center
            for def_item in deficits:
                target_fac = facility_map.get(def_item["facility_id"])
                if not target_fac:
                    continue
                    
                best_surplus = None
                best_distance = float("inf")
                
                for sur_item in surpluses:
                    if sur_item["surplus_quantity"] <= 0:
                        continue
                    if sur_item["facility_id"] == def_item["facility_id"]:
                        continue
                        
                    source_fac = facility_map.get(sur_item["facility_id"])
                    if not source_fac:
                        continue
                        
                    dist = haversine_distance_km(
                        source_fac["latitude"], source_fac["longitude"],
                        target_fac["latitude"], target_fac["longitude"]
                    )
                    
                    if dist < best_distance:
                        best_distance = dist
                        best_surplus = sur_item
                        
                if best_surplus and best_distance < 80.0: # within district transit radius
                    transfer_qty = min(def_item["needed_quantity"], best_surplus["surplus_quantity"])
                    if transfer_qty > 0:
                        best_surplus["surplus_quantity"] -= transfer_qty
                        source_fac = facility_map[best_surplus["facility_id"]]
                        
                        # Average rural transport speed in India ~35-40 km/h
                        transit_hours = round(max(0.3, best_distance / 35.0), 1)
                        
                        recommendations.append({
                            "source_facility_id": source_fac["id"],
                            "source_facility_name": source_fac["name"],
                            "target_facility_id": target_fac["id"],
                            "target_facility_name": target_fac["name"],
                            "item_name": med_name,
                            "item_type": "medicine",
                            "quantity": transfer_qty,
                            "unit": def_item["unit"],
                            "haversine_distance_km": best_distance,
                            "estimated_transit_hours": transit_hours,
                            "urgency_reason": f"Critical stockout prevention. Target has {round(def_item['days_supply'], 1)} days left.",
                            "status": "suggested_by_ai"
                        })
                        
        return recommendations

redistribution_engine = ResourceRedistributionEngine()

