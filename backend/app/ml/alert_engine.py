# File: backend/app/ml/alert_engine.py
# Description: Dual-mode stock depletion alert engine for SwasthyaGrid AI.
#
#   Type 1 — Real-Time Depletion:
#       Triggered when current_stock / daily_burn_rate < threshold days.
#       Instant, no forecasting model needed.
#
#   Type 2 — Forecasted Depletion with ETA Awareness:
#       Runs ForecastRouter on historical daily consumption and checks whether
#       the predicted run-out date falls BEFORE the next purchase order's
#       expected_delivery_date. If yes → alert is raised.

import logging
from datetime import date, timedelta
from typing import List, Optional, Dict, Any

import numpy as np

from backend.app.config import settings
from backend.app.ml.forecast_router import ForecastRouter

logger = logging.getLogger("swasthya.ml.alert_engine")


# ---------------------------------------------------------------------------
# Data classes (plain dicts keep it dependency-free from SQLAlchemy here)
# ---------------------------------------------------------------------------

def _severity(days_remaining: float) -> str:
    """Map days-remaining to a severity label."""
    if days_remaining <= settings.STOCKOUT_CRITICAL_THRESHOLD_DAYS:
        return "CRITICAL"
    elif days_remaining <= settings.STOCKOUT_WARNING_THRESHOLD_DAYS:
        return "WARNING"
    return "SAFE"


# ---------------------------------------------------------------------------
# Type 1: Real-Time Depletion Alert
# ---------------------------------------------------------------------------

def check_realtime_depletion(
    medicine_name: str,
    current_quantity: int,
    daily_burn_rate: float,
    facility_id: Optional[str] = None,
    medicine_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Evaluate current stock levels for immediate depletion risk.

    Returns an alert dict if below STOCKOUT_WARNING threshold, else None.

    Args:
        medicine_name:    Readable medicine name.
        current_quantity: Units currently in stock.
        daily_burn_rate:  Average units consumed per day.
        facility_id:      Optional facility UUID for context.
        medicine_id:      Optional MedicineStock UUID for context.

    Returns:
        dict | None: Alert payload or None if stock is adequate.
    """
    if daily_burn_rate <= 0:
        return None  # No consumption → no risk

    days_remaining = current_quantity / daily_burn_rate
    severity = _severity(days_remaining)

    if severity == "SAFE":
        return None

    run_out_date = date.today() + timedelta(days=days_remaining)

    return {
        "alert_type": "TYPE_1_REALTIME",
        "medicine_name": medicine_name,
        "medicine_id": medicine_id,
        "facility_id": facility_id,
        "current_quantity": current_quantity,
        "daily_burn_rate": daily_burn_rate,
        "days_remaining": round(days_remaining, 1),
        "run_out_date": run_out_date.isoformat(),
        "severity": severity,
        "message": (
            f"⚠ {medicine_name}: {days_remaining:.1f} days of stock remaining. "
            f"Estimated run-out on {run_out_date.strftime('%d %b %Y')}."
        ),
    }


def run_realtime_alerts(stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Batch Type-1 evaluation over a list of medicine stock dicts.

    Each item in *stocks* must have:
        medicine_name, current_quantity, daily_burn_rate
    Optional: medicine_id, facility_id.

    Returns only the items that triggered an alert.
    """
    alerts = []
    for item in stocks:
        alert = check_realtime_depletion(
            medicine_name=item.get("medicine_name", "Unknown"),
            current_quantity=item.get("current_quantity", 0),
            daily_burn_rate=item.get("daily_burn_rate", 0.0),
            facility_id=item.get("facility_id"),
            medicine_id=item.get("medicine_id") or item.get("id"),
        )
        if alert:
            alerts.append(alert)
    return alerts


# ---------------------------------------------------------------------------
# Type 2: Forecasted Depletion with ETA Awareness
# ---------------------------------------------------------------------------

def check_forecasted_depletion(
    medicine_name: str,
    current_quantity: int,
    daily_burn_rate: float,
    consumption_history: List[float],
    po_eta: Optional[date] = None,
    forecast_horizon: int = 30,
    facility_id: Optional[str] = None,
    medicine_id: Optional[str] = None,
    model_override: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Use ML forecasting to predict whether stock will run out before the next
    purchase order arrives.

    Args:
        medicine_name:       Readable name.
        current_quantity:    Current units in stock.
        daily_burn_rate:     Baseline average daily consumption.
        consumption_history: List of daily consumption values (chronological).
                             Used to train the forecast model.
        po_eta:              Expected delivery date of the incoming PO (or None if no PO).
        forecast_horizon:    How many days forward to project.
        facility_id:         Optional UUID.
        medicine_id:         Optional UUID.
        model_override:      Force a specific model ("patchtst"|"xgboost"|"arima").

    Returns:
        dict | None
    """
    if daily_burn_rate <= 0:
        return None

    # ── Run forecast ──────────────────────────────────────────────────────────
    history_arr = np.array(consumption_history, dtype=np.float64)
    if len(history_arr) < 3:
        # Not enough history — fall back to linear projection
        forecast_consumption = [daily_burn_rate] * forecast_horizon
        model_used = "linear_fallback"
    else:
        try:
            router = ForecastRouter(model="auto" if not model_override else model_override)
            result = router.forecast(history_arr, horizon=forecast_horizon)
            forecast_consumption = result["predictions"]
            model_used = result.get("model_used", "unknown")
        except Exception as exc:
            logger.warning(f"Forecast failed for {medicine_name}: {exc}. Using burn rate.")
            forecast_consumption = [daily_burn_rate] * forecast_horizon
            model_used = "linear_fallback"

    # ── Find projected run-out date ───────────────────────────────────────────
    remaining = float(current_quantity)
    run_out_day: Optional[int] = None
    today = date.today()

    for day_offset, consumption in enumerate(forecast_consumption):
        remaining -= max(0.0, consumption)
        if remaining <= 0:
            run_out_day = day_offset + 1  # 1-indexed days from today
            break

    if run_out_day is None:
        # Stock survives the entire forecast horizon
        return None

    run_out_date = today + timedelta(days=run_out_day)

    # ── Compare against PO ETA ────────────────────────────────────────────────
    # Alert only if there's no PO coming before the run-out, or PO is after run-out
    if po_eta is not None and po_eta <= run_out_date:
        # PO arrives before run-out → no alert needed
        return None

    # Compute effective days remaining at run-out vs ETA
    days_until_eta = (po_eta - today).days if po_eta else None
    days_gap = (
        (run_out_date - po_eta).days if po_eta else run_out_day
    )

    return {
        "alert_type": "TYPE_2_FORECASTED",
        "medicine_name": medicine_name,
        "medicine_id": medicine_id,
        "facility_id": facility_id,
        "current_quantity": current_quantity,
        "daily_burn_rate": daily_burn_rate,
        "forecast_horizon_days": forecast_horizon,
        "model_used": model_used,
        "projected_run_out_day": run_out_day,
        "projected_run_out_date": run_out_date.isoformat(),
        "po_eta": po_eta.isoformat() if po_eta else None,
        "days_before_eta": days_gap,
        "severity": "CRITICAL" if run_out_day <= 7 else "WARNING",
        "message": (
            f"🔮 {medicine_name}: AI forecast predicts stock exhaustion on "
            f"{run_out_date.strftime('%d %b %Y')} "
            + (f"({days_gap} days BEFORE PO delivery on {po_eta.strftime('%d %b %Y')})."
               if po_eta else f"(no purchase order on record).")
        ),
        "forecast_predictions": forecast_consumption,
    }


def run_forecasted_alerts(
    stocks: List[Dict[str, Any]],
    consumption_histories: Dict[str, List[float]],
    purchase_order_etas: Dict[str, Optional[date]],
    forecast_horizon: int = 30,
) -> List[Dict[str, Any]]:
    """
    Batch Type-2 evaluation over a list of medicine stocks.

    Args:
        stocks:               List of stock dicts (same format as run_realtime_alerts).
        consumption_histories: Map of medicine_id → list of daily consumption values.
        purchase_order_etas:  Map of medicine_id → expected PO delivery date (or None).
        forecast_horizon:     Days forward to project.

    Returns:
        List of alert dicts.
    """
    alerts = []
    for item in stocks:
        mid = item.get("medicine_id") or item.get("id", "")
        history = consumption_histories.get(mid, [])
        po_eta  = purchase_order_etas.get(mid)

        alert = check_forecasted_depletion(
            medicine_name=item.get("medicine_name", "Unknown"),
            current_quantity=item.get("current_quantity", 0),
            daily_burn_rate=item.get("daily_burn_rate", 0.0),
            consumption_history=history,
            po_eta=po_eta,
            forecast_horizon=forecast_horizon,
            facility_id=item.get("facility_id"),
            medicine_id=mid,
        )
        if alert:
            alerts.append(alert)
    return alerts


# ---------------------------------------------------------------------------
# Combined runner
# ---------------------------------------------------------------------------

def run_all_alerts(
    stocks: List[Dict[str, Any]],
    consumption_histories: Optional[Dict[str, List[float]]] = None,
    purchase_order_etas: Optional[Dict[str, Optional[date]]] = None,
    forecast_horizon: int = settings.FORECAST_HORIZON_DAYS,
) -> Dict[str, Any]:
    """
    Run both Type-1 and Type-2 alerts and return a combined summary.

    Returns:
        {
            "realtime_alerts":    [...],
            "forecasted_alerts":  [...],
            "total_critical":     int,
            "total_warnings":     int,
        }
    """
    rt_alerts = run_realtime_alerts(stocks)

    fc_alerts: List[Dict[str, Any]] = []
    if consumption_histories:
        fc_alerts = run_forecasted_alerts(
            stocks,
            consumption_histories=consumption_histories or {},
            purchase_order_etas=purchase_order_etas or {},
            forecast_horizon=forecast_horizon,
        )

    all_alerts = rt_alerts + fc_alerts
    total_critical = sum(1 for a in all_alerts if a.get("severity") == "CRITICAL")
    total_warnings  = sum(1 for a in all_alerts if a.get("severity") == "WARNING")

    return {
        "realtime_alerts":   rt_alerts,
        "forecasted_alerts": fc_alerts,
        "total_critical":    total_critical,
        "total_warnings":    total_warnings,
        "total_alerts":      len(all_alerts),
    }
