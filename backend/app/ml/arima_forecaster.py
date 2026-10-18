# File: backend/app/ml/arima_forecaster.py
# Description: ARIMA-based time series forecaster using statsmodels with automatic order selection via AIC

import logging
import numpy as np
from typing import List, Tuple, Optional, Dict, Any

logger = logging.getLogger("swasthya.ml.arima")

try:
    from statsmodels.tsa.arima.model import ARIMA
    STATSMODELS_AVAILABLE = True
except ImportError:  # pragma: no cover
    STATSMODELS_AVAILABLE = False
    logger.warning("statsmodels not installed – ARIMAForecaster will use fallback linear trend.")


class ARIMAForecaster:
    """
    ARIMA forecaster with automatic order selection.
    Tries a set of common (p,d,q) orders and picks the one with the lowest AIC.
    Falls back to a simple linear trend if statsmodels is unavailable.
    """

    # Candidate orders to evaluate during auto-selection
    CANDIDATE_ORDERS: List[Tuple[int, int, int]] = [
        (1, 1, 1),
        (2, 1, 1),
        (1, 1, 2),
        (0, 1, 1),
    ]

    def __init__(self) -> None:
        self._fitted_model = None          # Fitted ARIMA results object
        self._best_order: Optional[Tuple[int, int, int]] = None
        self._residual_std: float = 1.0   # Used to build confidence intervals
        self._series_mean: float = 0.0    # Scale reference for fallback
        self._series: Optional[np.ndarray] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _try_fit(self, series: np.ndarray, order: Tuple[int, int, int]):
        """Fit a single ARIMA(p,d,q) and return (model_result, aic) or (None, inf)."""
        try:
            model = ARIMA(series, order=order)
            result = model.fit()
            return result, result.aic
        except Exception as exc:
            logger.debug(f"ARIMA{order} fit failed: {exc}")
            return None, float("inf")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def auto_order(self, series: np.ndarray) -> Tuple[int, int, int]:
        """
        Evaluate all candidate ARIMA orders on *series* and return the one
        with the lowest AIC score.
        """
        if not STATSMODELS_AVAILABLE:
            return (1, 1, 1)  # dummy when library is missing

        best_order = (1, 1, 1)
        best_aic = float("inf")

        for order in self.CANDIDATE_ORDERS:
            _, aic = self._try_fit(series, order)
            logger.debug(f"ARIMA{order} AIC={aic:.2f}")
            if aic < best_aic:
                best_aic = aic
                best_order = order

        logger.info(f"Best ARIMA order selected: {best_order} (AIC={best_aic:.2f})")
        return best_order

    def fit(self, series: np.ndarray) -> "ARIMAForecaster":
        """
        Fit the ARIMA model on the provided univariate time series.

        Args:
            series: 1-D numpy array of observed values (chronological order).
        Returns:
            self (for chaining)
        """
        self._series = series.astype(np.float64)
        self._series_mean = float(np.mean(self._series)) or 1.0

        if not STATSMODELS_AVAILABLE or len(series) < 15:
            # Fallback: store mean for linear-trend extrapolation
            logger.warning("ARIMAForecaster using linear-trend fallback (short series or missing lib).")
            self._fitted_model = None
            self._residual_std = float(np.std(series)) * 0.5 or 1.0
            return self

        best_order = self.auto_order(self._series)
        self._best_order = best_order

        result, _ = self._try_fit(self._series, best_order)
        if result is None:
            # All orders failed – fall back to linear trend
            logger.warning("All ARIMA orders failed to converge; using linear fallback.")
            self._fitted_model = None
            self._residual_std = float(np.std(series)) * 0.5 or 1.0
            return self

        self._fitted_model = result
        # Compute in-sample residual std for confidence intervals
        residuals = np.asarray(result.resid)
        self._residual_std = float(np.std(residuals)) or 1.0
        logger.info(f"ARIMAForecaster fitted. Residual std={self._residual_std:.3f}")
        return self

    def predict(self, horizon: int) -> Dict[str, Any]:
        """
        Generate *horizon*-step ahead forecasts with 95% confidence intervals.

        Returns:
            dict with keys:
                predictions       – list of float (point forecasts)
                confidence_lower  – list of float (lower 95% CI)
                confidence_upper  – list of float (upper 95% CI)
                model_used        – 'arima'
                horizon_days      – int
        """
        if self._fitted_model is not None:
            # Use statsmodels built-in forecast method
            forecast_result = self._fitted_model.get_forecast(steps=horizon)
            summary = forecast_result.summary_frame(alpha=0.05)  # 95% CI
            predictions = [max(0.0, float(v)) for v in summary["mean"].values]
            lower       = [max(0.0, float(v)) for v in summary["mean_ci_lower"].values]
            upper       = [max(0.0, float(v)) for v in summary["mean_ci_upper"].values]
        else:
            # Linear-trend fallback when statsmodels is absent or series too short
            if self._series is not None and len(self._series) >= 2:
                x = np.arange(len(self._series))
                coeffs = np.polyfit(x, self._series, 1)  # slope, intercept
                slope, intercept = coeffs
                start = len(self._series)
                predictions = [
                    max(0.0, slope * (start + i) + intercept) for i in range(horizon)
                ]
            else:
                predictions = [self._series_mean] * horizon

            # Build confidence bands using ±1.96 * residual_std
            z = 1.96
            lower = [max(0.0, p - z * self._residual_std) for p in predictions]
            upper = [p + z * self._residual_std for p in predictions]

        return {
            "predictions": predictions,
            "confidence_lower": lower,
            "confidence_upper": upper,
            "model_used": "arima",
            "horizon_days": horizon,
        }
