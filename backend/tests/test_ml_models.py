# File: backend/tests/test_ml_models.py
# Description: Unit tests for PatchTST, XGBoost, ARIMA forecasters, ForecastRouter,
#              and the dual-mode alert engine.

import pytest
import numpy as np
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def short_series():
    """14-point series — routes to ARIMA."""
    rng = np.random.default_rng(42)
    return rng.normal(loc=50, scale=5, size=14).clip(min=0)

@pytest.fixture
def medium_series():
    """35-point series — routes to XGBoost."""
    rng = np.random.default_rng(42)
    return rng.normal(loc=80, scale=10, size=35).clip(min=0)

@pytest.fixture
def long_series():
    """90-point series — routes to PatchTST."""
    rng = np.random.default_rng(42)
    trend = np.linspace(50, 70, 90)
    noise = rng.normal(0, 5, 90)
    return (trend + noise).clip(min=0)


# ─── ARIMAForecaster ──────────────────────────────────────────────────────────

class TestARIMAForecaster:
    def test_fit_and_predict_short(self, short_series):
        from backend.app.ml.arima_forecaster import ARIMAForecaster
        f = ARIMAForecaster()
        f.fit(short_series)
        result = f.predict(7)
        assert "predictions" in result
        assert len(result["predictions"]) == 7

    def test_predictions_non_negative(self, short_series):
        from backend.app.ml.arima_forecaster import ARIMAForecaster
        result = ARIMAForecaster().fit(short_series).predict(14)
        assert all(v >= 0 for v in result["predictions"])

    def test_confidence_intervals_ordered(self, short_series):
        from backend.app.ml.arima_forecaster import ARIMAForecaster
        result = ARIMAForecaster().fit(short_series).predict(7)
        for lo, hi in zip(result["confidence_lower"], result["confidence_upper"]):
            assert hi >= lo

    def test_model_used_field(self, short_series):
        from backend.app.ml.arima_forecaster import ARIMAForecaster
        result = ARIMAForecaster().fit(short_series).predict(7)
        assert result["model_used"] == "arima"

    def test_horizon_days_field(self, short_series):
        from backend.app.ml.arima_forecaster import ARIMAForecaster
        result = ARIMAForecaster().fit(short_series).predict(10)
        assert result["horizon_days"] == 10


# ─── XGBoostForecaster ────────────────────────────────────────────────────────

class TestXGBoostForecaster:
    def test_fit_and_predict(self, medium_series):
        from backend.app.ml.xgboost_forecaster import XGBoostForecaster
        f = XGBoostForecaster()
        f.fit(medium_series)
        result = f.predict(14)
        assert len(result["predictions"]) == 14

    def test_predictions_non_negative(self, medium_series):
        from backend.app.ml.xgboost_forecaster import XGBoostForecaster
        result = XGBoostForecaster().fit(medium_series).predict(7)
        assert all(v >= 0 for v in result["predictions"])

    def test_confidence_intervals_ordered(self, medium_series):
        from backend.app.ml.xgboost_forecaster import XGBoostForecaster
        result = XGBoostForecaster().fit(medium_series).predict(7)
        for lo, hi, pt in zip(result["confidence_lower"], result["confidence_upper"], result["predictions"]):
            assert hi >= lo

    def test_predict_without_fit_raises(self):
        from backend.app.ml.xgboost_forecaster import XGBoostForecaster
        with pytest.raises(RuntimeError):
            XGBoostForecaster().predict(7)

    def test_model_used_field(self, medium_series):
        from backend.app.ml.xgboost_forecaster import XGBoostForecaster
        result = XGBoostForecaster().fit(medium_series).predict(7)
        assert "xgboost" in result["model_used"] or "fallback" in result["model_used"]


# ─── PatchTSTForecaster ───────────────────────────────────────────────────────

class TestPatchTSTForecaster:
    def test_fit_and_predict_long(self, long_series):
        from backend.app.ml.patchtst import PatchTSTForecaster
        f = PatchTSTForecaster(forecast_horizon=14, epochs=5)
        f.fit(long_series)
        result = f.predict(14)
        assert len(result["predictions"]) == 14

    def test_predictions_non_negative(self, long_series):
        from backend.app.ml.patchtst import PatchTSTForecaster
        result = PatchTSTForecaster(forecast_horizon=14, epochs=5).fit(long_series).predict(14)
        assert all(v >= 0 for v in result["predictions"])

    def test_fallback_on_short_series(self, short_series):
        """Should use linear fallback without crashing."""
        from backend.app.ml.patchtst import PatchTSTForecaster
        result = PatchTSTForecaster(forecast_horizon=7, epochs=3).fit(short_series).predict(7)
        assert len(result["predictions"]) == 7
        assert "fallback" in result["model_used"]

    def test_confidence_intervals_ordered(self, long_series):
        from backend.app.ml.patchtst import PatchTSTForecaster
        result = PatchTSTForecaster(forecast_horizon=7, epochs=3).fit(long_series).predict(7)
        for lo, hi in zip(result["confidence_lower"], result["confidence_upper"]):
            assert hi >= lo

    def test_predict_before_fit_raises(self):
        from backend.app.ml.patchtst import PatchTSTForecaster
        with pytest.raises(RuntimeError):
            PatchTSTForecaster().predict(7)


# ─── ForecastRouter ───────────────────────────────────────────────────────────

class TestForecastRouter:
    def test_routes_to_arima_short(self, short_series):
        from backend.app.ml.forecast_router import ForecastRouter
        r = ForecastRouter()
        assert r._select_model(len(short_series)) == "arima"

    def test_routes_to_xgboost_medium(self, medium_series):
        from backend.app.ml.forecast_router import ForecastRouter
        r = ForecastRouter()
        assert r._select_model(len(medium_series)) == "xgboost"

    def test_routes_to_patchtst_long(self, long_series):
        from backend.app.ml.forecast_router import ForecastRouter
        r = ForecastRouter()
        assert r._select_model(len(long_series)) == "patchtst"

    def test_manual_override(self, medium_series):
        from backend.app.ml.forecast_router import ForecastRouter
        r = ForecastRouter(model="arima")
        result = r.forecast(medium_series, horizon=7)
        assert result["model_used"] == "arima"

    def test_forecast_returns_correct_length(self, medium_series):
        from backend.app.ml.forecast_router import ForecastRouter
        result = ForecastRouter().forecast(medium_series, horizon=10)
        assert len(result["predictions"]) == 10

    def test_forecast_has_series_length(self, medium_series):
        from backend.app.ml.forecast_router import ForecastRouter
        result = ForecastRouter().forecast(medium_series, horizon=7)
        assert result["series_length"] == len(medium_series)

    def test_explain_selection_keys(self):
        from backend.app.ml.forecast_router import ForecastRouter
        info = ForecastRouter().explain_selection(45)
        assert "model_selected" in info
        assert "thresholds" in info

    def test_fallback_on_failure(self):
        """Very small series should not crash — uses flat fallback."""
        from backend.app.ml.forecast_router import ForecastRouter
        tiny = np.array([5.0, 6.0, 5.5])
        result = ForecastRouter().forecast(tiny, horizon=5)
        assert len(result["predictions"]) == 5


# ─── Alert Engine ─────────────────────────────────────────────────────────────

class TestAlertEngine:
    def test_type1_critical_alert(self):
        from backend.app.ml.alert_engine import check_realtime_depletion
        alert = check_realtime_depletion(
            medicine_name="Amoxicillin",
            current_quantity=30,
            daily_burn_rate=15.0,  # 2 days left → CRITICAL
        )
        assert alert is not None
        assert alert["severity"] == "CRITICAL"
        assert alert["alert_type"] == "TYPE_1_REALTIME"

    def test_type1_warning_alert(self):
        from backend.app.ml.alert_engine import check_realtime_depletion
        alert = check_realtime_depletion(
            medicine_name="Paracetamol",
            current_quantity=280,
            daily_burn_rate=50.0,  # 5.6 days → WARNING
        )
        assert alert is not None
        assert alert["severity"] == "WARNING"

    def test_type1_no_alert_when_safe(self):
        from backend.app.ml.alert_engine import check_realtime_depletion
        alert = check_realtime_depletion(
            medicine_name="ORS",
            current_quantity=1000,
            daily_burn_rate=50.0,  # 20 days → safe
        )
        assert alert is None

    def test_type1_zero_burn_rate_no_alert(self):
        from backend.app.ml.alert_engine import check_realtime_depletion
        alert = check_realtime_depletion("Med", 0, 0.0)
        assert alert is None

    def test_type1_message_contains_medicine_name(self):
        from backend.app.ml.alert_engine import check_realtime_depletion
        alert = check_realtime_depletion("Oxytocin", 10, 5.0)
        assert "Oxytocin" in alert["message"]

    def test_type2_alert_when_po_after_runout(self):
        from backend.app.ml.alert_engine import check_forecasted_depletion
        history = [10.0] * 30
        po_eta = date.today() + timedelta(days=20)  # PO arrives day 20
        alert = check_forecasted_depletion(
            medicine_name="ASV",
            current_quantity=50,
            daily_burn_rate=10.0,
            consumption_history=history,  # burns ~10/day → runs out day 5
            po_eta=po_eta,
        )
        assert alert is not None
        assert alert["alert_type"] == "TYPE_2_FORECASTED"

    def test_type2_no_alert_when_po_before_runout(self):
        from backend.app.ml.alert_engine import check_forecasted_depletion
        history = [5.0] * 30
        po_eta = date.today() + timedelta(days=2)  # PO arrives before runout
        alert = check_forecasted_depletion(
            medicine_name="Safe Med",
            current_quantity=100,
            daily_burn_rate=5.0,
            consumption_history=history,  # runs out day 20, PO arrives day 2
            po_eta=po_eta,
        )
        assert alert is None

    def test_run_realtime_alerts_batch(self):
        from backend.app.ml.alert_engine import run_realtime_alerts
        stocks = [
            {"medicine_name": "Med A", "current_quantity": 10, "daily_burn_rate": 5.0},   # CRITICAL
            {"medicine_name": "Med B", "current_quantity": 500, "daily_burn_rate": 10.0}, # safe
            {"medicine_name": "Med C", "current_quantity": 30, "daily_burn_rate": 5.0},   # WARNING
        ]
        alerts = run_realtime_alerts(stocks)
        assert len(alerts) == 2  # Med A + Med C

    def test_run_all_alerts_keys(self):
        from backend.app.ml.alert_engine import run_all_alerts
        stocks = [{"medicine_name": "Med", "current_quantity": 5, "daily_burn_rate": 3.0}]
        result = run_all_alerts(stocks)
        assert "realtime_alerts" in result
        assert "forecasted_alerts" in result
        assert "total_critical" in result
        assert "total_warnings" in result
