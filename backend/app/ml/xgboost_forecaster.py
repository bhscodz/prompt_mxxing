# File: backend/app/ml/xgboost_forecaster.py
# Description: XGBoost-based multi-step time series forecaster with lag/rolling features and quantile confidence bands

import logging
import numpy as np
from typing import List, Optional, Dict, Any

logger = logging.getLogger("swasthya.ml.xgboost")

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:  # pragma: no cover
    XGBOOST_AVAILABLE = False
    logger.warning("xgboost not installed – XGBoostForecaster will use linear fallback.")


class XGBoostForecaster:
    """
    Gradient-boosted tree forecaster that:
      1. Engineers rich temporal features (lags, rolling means, calendar).
      2. Trains separate XGBRegressor models for point forecast and quantile bands.
      3. Performs recursive multi-step prediction up to *horizon* days.

    If xgboost is unavailable, falls back to a simple linear-regression extrapolation.
    """

    # Lag offsets (in days) to create as features
    LAG_DAYS: List[int] = [1, 7, 14, 30]
    # Rolling window sizes for mean features
    ROLLING_WINDOWS: List[int] = [7, 14]

    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int = 4,
        learning_rate: float = 0.08,
        subsample: float = 0.85,
    ) -> None:
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.subsample = subsample

        # Three regressors: median (point), 10th pct (lower CI), 90th pct (upper CI)
        self._model_median: Optional[object] = None
        self._model_lower: Optional[object] = None
        self._model_upper: Optional[object] = None

        self._series_cache: Optional[np.ndarray] = None   # Last training series (for recursive pred)
        self._residual_std: float = 1.0                   # For fallback CI
        self._fallback_coeffs: Optional[np.ndarray] = None  # Linear fallback

    # ------------------------------------------------------------------
    # Feature engineering
    # ------------------------------------------------------------------

    def _create_features(
        self, series: np.ndarray, exog: Optional[np.ndarray] = None
    ) -> tuple:
        """
        Convert a 1-D time series into a supervised learning dataset.

        Returns:
            X: 2-D feature matrix  (n_samples, n_features)
            y: 1-D target vector   (n_samples,)
        """
        n = len(series)
        # Minimum lookback needed (max lag = 30)
        min_start = max(self.LAG_DAYS)
        rows_X, rows_y = [], []

        for t in range(min_start, n):
            features: List[float] = []

            # Lag features
            for lag in self.LAG_DAYS:
                features.append(float(series[t - lag]) if (t - lag) >= 0 else 0.0)

            # Rolling mean features
            for window in self.ROLLING_WINDOWS:
                start_w = max(0, t - window)
                features.append(float(np.mean(series[start_w:t])))

            # Calendar features (approximate; we only have array index as time proxy)
            features.append(float(t % 7))      # day-of-week proxy (0-6)
            features.append(float((t // 7) % 4))  # week-of-month proxy (0-3)
            features.append(float((t // 30) % 12))  # month-of-year proxy (0-11)

            # Optional exogenous variables
            if exog is not None and t < len(exog):
                features.extend(exog[t].tolist() if exog.ndim > 1 else [float(exog[t])])

            rows_X.append(features)
            rows_y.append(float(series[t]))

        X = np.array(rows_X, dtype=np.float32)
        y = np.array(rows_y, dtype=np.float32)
        return X, y

    def _make_feature_row(
        self, series: np.ndarray, t: int, exog_row: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """Build a single feature row for position *t* given the (possibly updated) series."""
        features: List[float] = []

        for lag in self.LAG_DAYS:
            idx = t - lag
            features.append(float(series[idx]) if idx >= 0 else 0.0)

        for window in self.ROLLING_WINDOWS:
            start_w = max(0, t - window)
            features.append(float(np.mean(series[start_w:t])))

        features.append(float(t % 7))
        features.append(float((t // 7) % 4))
        features.append(float((t // 30) % 12))

        if exog_row is not None:
            features.extend(exog_row.tolist() if exog_row.ndim > 0 else [float(exog_row)])

        return np.array(features, dtype=np.float32)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(self, series: np.ndarray, exog: Optional[np.ndarray] = None) -> "XGBoostForecaster":
        """
        Train the XGBoost forecaster.

        Args:
            series: 1-D numpy array of observed values (chronological).
            exog:   Optional 2-D array of exogenous features aligned with series.
        Returns:
            self (for chaining)
        """
        self._series_cache = series.astype(np.float64)

        if not XGBOOST_AVAILABLE or len(series) < max(self.LAG_DAYS) + 5:
            # Linear fallback
            logger.warning("XGBoostForecaster: using linear-trend fallback (short series or missing lib).")
            x = np.arange(len(series))
            self._fallback_coeffs = np.polyfit(x, series, 1)
            self._residual_std = float(np.std(series - np.polyval(self._fallback_coeffs, x))) or 1.0
            return self

        X, y = self._create_features(series, exog)

        # Base XGBRegressor params common to all three models
        base_params = dict(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            subsample=self.subsample,
            random_state=42,
            verbosity=0,
            tree_method="hist",
        )

        # Point-forecast model (squared-error objective)
        self._model_median = XGBRegressor(objective="reg:squarederror", **base_params)
        self._model_median.fit(X, y)

        # Lower quantile (10th percentile) – quantile objective
        self._model_lower = XGBRegressor(objective="reg:quantileerror", quantile_alpha=0.10, **base_params)
        self._model_lower.fit(X, y)

        # Upper quantile (90th percentile)
        self._model_upper = XGBRegressor(objective="reg:quantileerror", quantile_alpha=0.90, **base_params)
        self._model_upper.fit(X, y)

        # Compute in-sample residual std for reference
        y_hat = self._model_median.predict(X)
        self._residual_std = float(np.std(y - y_hat)) or 1.0
        logger.info(f"XGBoostForecaster fitted. In-sample RMSE≈{self._residual_std:.2f}")
        return self

    def predict(
        self, horizon: int, exog: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Recursive multi-step forecast.

        Each step appends the predicted value to the working series so lag
        features for the next step are computed on the extended series.

        Returns:
            dict with keys:
                predictions, confidence_lower, confidence_upper, model_used, horizon_days
        """
        if self._series_cache is None:
            raise RuntimeError("XGBoostForecaster.fit() must be called before predict().")

        # Working copy – will be extended with predictions for lag computation
        working_series = list(self._series_cache)

        predictions: List[float] = []
        lower_ci: List[float] = []
        upper_ci: List[float] = []

        for step in range(horizon):
            t = len(working_series)

            if self._fallback_coeffs is not None:
                # Linear fallback mode
                val = max(0.0, float(np.polyval(self._fallback_coeffs, t)))
                predictions.append(val)
                lower_ci.append(max(0.0, val - 1.645 * self._residual_std))
                upper_ci.append(val + 1.645 * self._residual_std)
            else:
                series_arr = np.array(working_series, dtype=np.float32)
                exog_row = exog[step] if (exog is not None and step < len(exog)) else None
                feat_row = self._make_feature_row(series_arr, t, exog_row).reshape(1, -1)

                val = max(0.0, float(self._model_median.predict(feat_row)[0]))
                lo  = max(0.0, float(self._model_lower.predict(feat_row)[0]))
                hi  = float(self._model_upper.predict(feat_row)[0])

                predictions.append(val)
                lower_ci.append(lo)
                upper_ci.append(max(hi, val))  # ensure upper >= point

            # Append predicted value to extend lag window for next step
            working_series.append(predictions[-1])

        return {
            "predictions": predictions,
            "confidence_lower": lower_ci,
            "confidence_upper": upper_ci,
            "model_used": "xgboost",
            "horizon_days": horizon,
        }
