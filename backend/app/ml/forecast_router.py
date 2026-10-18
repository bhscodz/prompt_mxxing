# File: backend/app/ml/forecast_router.py
# Description: Pluggable model router that selects the best forecasting model
#              based on series length and variance.
#
#   Routing rules:
#     n >= 60 → PatchTST   (rich history, transformer-grade)
#     n >= 30 → XGBoost    (moderate history, gradient boosting with features)
#     n >= 14 → ARIMA      (short series, statistical baseline)
#     n < 14  → ARIMA      (fallback — ARIMA handles very short with its linear trend)

import logging
import numpy as np
from typing import Dict, Any, Optional, Literal

from backend.app.ml.patchtst import PatchTSTForecaster
from backend.app.ml.xgboost_forecaster import XGBoostForecaster
from backend.app.ml.arima_forecaster import ARIMAForecaster

logger = logging.getLogger("swasthya.ml.forecast_router")

ModelName = Literal["patchtst", "xgboost", "arima", "auto"]


class ForecastRouter:
    """
    Automatic or manual model selector.

    Usage (automatic):
        router = ForecastRouter()
        result = router.forecast(series, horizon=14)

    Usage (manual override):
        router = ForecastRouter(model="xgboost")
        result = router.forecast(series, horizon=14)
    """

    # Thresholds that drive automatic selection
    PATCHTST_MIN_POINTS = 60
    XGBOOST_MIN_POINTS  = 30
    ARIMA_MIN_POINTS    = 14

    def __init__(self, model: ModelName = "auto") -> None:
        """
        Args:
            model: "auto" selects automatically; otherwise force a specific model.
        """
        self.model_preference: ModelName = model
        self._last_model_used: Optional[str] = None

    # ------------------------------------------------------------------
    # Model selection
    # ------------------------------------------------------------------

    def _select_model(self, n: int) -> str:
        """Select the best model name based on series length."""
        if self.model_preference != "auto":
            return self.model_preference

        if n >= self.PATCHTST_MIN_POINTS:
            return "patchtst"
        elif n >= self.XGBOOST_MIN_POINTS:
            return "xgboost"
        else:
            return "arima"

    # ------------------------------------------------------------------
    # Core forecast method
    # ------------------------------------------------------------------

    def forecast(
        self,
        series: np.ndarray,
        horizon: int = 14,
        model_override: Optional[ModelName] = None,
        exog: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        Fit the selected model on *series* and produce *horizon*-step forecasts.

        Args:
            series:         1-D numpy array of historical observations (daily).
            horizon:        Number of future days to forecast.
            model_override: Override the router selection for this call only.
            exog:           Optional exogenous features (used by XGBoost only).

        Returns:
            dict: {
                predictions, confidence_lower, confidence_upper,
                model_used, horizon_days, series_length, model_selected_by
            }
        """
        series = np.asarray(series, dtype=np.float64)
        n = len(series)

        selected = model_override or self._select_model(n)
        self._last_model_used = selected

        logger.info(f"ForecastRouter: n={n}, horizon={horizon}, model={selected}")

        try:
            result = self._run_model(selected, series, horizon, exog)
        except Exception as exc:
            logger.warning(f"ForecastRouter: {selected} failed ({exc}), falling back to arima.")
            try:
                result = self._run_model("arima", series, horizon, exog)
            except Exception as exc2:
                logger.error(f"ForecastRouter: all models failed. {exc2}")
                # Last-resort: flat forecast at series mean
                mean_val = float(np.mean(series)) if n > 0 else 0.0
                std_val  = float(np.std(series)) * 0.5 if n > 0 else 1.0
                result = {
                    "predictions": [mean_val] * horizon,
                    "confidence_lower": [max(0.0, mean_val - 1.96 * std_val)] * horizon,
                    "confidence_upper": [mean_val + 1.96 * std_val] * horizon,
                    "model_used": "flat_fallback",
                    "horizon_days": horizon,
                }

        result["series_length"]    = n
        result["model_selected_by"] = "override" if model_override else (
            "auto" if self.model_preference == "auto" else "manual"
        )
        return result

    def _run_model(
        self,
        model_name: str,
        series: np.ndarray,
        horizon: int,
        exog: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """Instantiate, fit, and predict with the named model."""
        if model_name == "patchtst":
            forecaster = PatchTSTForecaster(forecast_horizon=horizon)
            forecaster.fit(series)
            return forecaster.predict(horizon)

        elif model_name == "xgboost":
            forecaster = XGBoostForecaster()
            forecaster.fit(series, exog=exog)
            return forecaster.predict(horizon, exog=exog)

        elif model_name == "arima":
            forecaster = ARIMAForecaster()
            forecaster.fit(series)
            return forecaster.predict(horizon)

        else:
            raise ValueError(f"Unknown model name: '{model_name}'")

    @property
    def last_model_used(self) -> Optional[str]:
        """Name of the model used in the most recent forecast() call."""
        return self._last_model_used

    # ------------------------------------------------------------------
    # Convenience: explain routing decision
    # ------------------------------------------------------------------

    def explain_selection(self, series_length: int) -> Dict[str, Any]:
        """Return a human-readable routing decision without running a forecast."""
        selected = self._select_model(series_length)
        return {
            "series_length": series_length,
            "model_selected": selected,
            "thresholds": {
                "patchtst": f">= {self.PATCHTST_MIN_POINTS} points",
                "xgboost":  f">= {self.XGBOOST_MIN_POINTS} points",
                "arima":    f">= {self.ARIMA_MIN_POINTS} points",
                "flat_fallback": f"< {self.ARIMA_MIN_POINTS} points",
            },
            "routing_mode": self.model_preference,
        }
