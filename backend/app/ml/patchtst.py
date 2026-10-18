# File: backend/app/ml/patchtst.py
# Description: PatchTST — Patch Time Series Transformer for long-sequence forecasting.
#   Paper: "A Time Series is Worth 64 Words: Long-term Forecasting with Transformers" (Nie et al. 2023)
#   Architecture: segment series into overlapping patches → linear embedding → Transformer encoder → linear head.
#   Falls back to a simple attention-free MLP if PyTorch is unavailable.

import logging
import numpy as np
from typing import Dict, Any, Optional

logger = logging.getLogger("swasthya.ml.patchtst")

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not installed — PatchTSTForecaster will use linear-trend fallback.")


# ---------------------------------------------------------------------------
# PyTorch Module (only defined when torch is available)
# ---------------------------------------------------------------------------

if TORCH_AVAILABLE:
    class _PatchEmbedding(nn.Module):
        """Splits a time series into fixed-length patches and projects each patch to d_model."""

        def __init__(self, patch_len: int, stride: int, d_model: int, dropout: float = 0.1):
            super().__init__()
            self.patch_len = patch_len
            self.stride = stride
            self.proj = nn.Linear(patch_len, d_model)
            self.dropout = nn.Dropout(dropout)

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            # x: (batch, seq_len)
            # unfold into (batch, num_patches, patch_len)
            patches = x.unfold(dimension=1, size=self.patch_len, step=self.stride)
            return self.dropout(self.proj(patches))  # (batch, num_patches, d_model)

    class _PatchTSTModel(nn.Module):
        """
        Lightweight PatchTST model.
        Encoder-only Transformer over patch embeddings with a linear forecast head.
        """

        def __init__(
            self,
            seq_len: int,
            patch_len: int = 16,
            stride: int = 8,
            d_model: int = 64,
            n_heads: int = 4,
            n_layers: int = 2,
            dim_ff: int = 128,
            dropout: float = 0.1,
            forecast_horizon: int = 14,
        ):
            super().__init__()
            self.patch_embed = _PatchEmbedding(patch_len, stride, d_model, dropout)
            # Number of patches produced by the unfold
            num_patches = max(1, (seq_len - patch_len) // stride + 1)
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=d_model,
                nhead=n_heads,
                dim_feedforward=dim_ff,
                dropout=dropout,
                batch_first=True,
                norm_first=True,  # Pre-LN for training stability
            )
            self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
            # Flatten all patch representations and project to forecast_horizon
            self.head = nn.Sequential(
                nn.Flatten(start_dim=1),
                nn.Linear(num_patches * d_model, forecast_horizon),
            )

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            # x: (batch, seq_len)  normalized to [0,1] by the caller
            embed = self.patch_embed(x)          # (batch, num_patches, d_model)
            encoded = self.encoder(embed)        # (batch, num_patches, d_model)
            out = self.head(encoded)             # (batch, forecast_horizon)
            return out


# ---------------------------------------------------------------------------
# Public Wrapper
# ---------------------------------------------------------------------------

class PatchTSTForecaster:
    """
    High-level wrapper around _PatchTSTModel with:
      - Automatic normalization (z-score per series)
      - Simple MSE training loop
      - Confidence intervals via MC-dropout (4 forward passes)
      - Graceful linear-trend fallback when PyTorch is unavailable
    """

    def __init__(
        self,
        seq_len: int = 64,
        patch_len: int = 16,
        stride: int = 8,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 2,
        dim_ff: int = 128,
        dropout: float = 0.1,
        forecast_horizon: int = 14,
        epochs: int = 80,
        lr: float = 3e-4,
    ):
        self.seq_len = seq_len
        self.forecast_horizon = forecast_horizon
        self.epochs = epochs
        self.lr = lr
        self.patch_len = patch_len
        self.stride = stride
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.dim_ff = dim_ff
        self.dropout = dropout

        self._model: Optional[object] = None   # _PatchTSTModel instance
        self._mean: float = 0.0
        self._std: float = 1.0
        self._series: Optional[np.ndarray] = None
        self._fallback_coeffs: Optional[np.ndarray] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _normalize(self, arr: np.ndarray) -> np.ndarray:
        return (arr - self._mean) / (self._std + 1e-8)

    def _denormalize(self, arr: np.ndarray) -> np.ndarray:
        return arr * (self._std + 1e-8) + self._mean

    def _build_samples(self, series: np.ndarray):
        """Sliding window: (seq_len → horizon) samples for training."""
        X, y = [], []
        n = len(series)
        for i in range(n - self.seq_len - self.forecast_horizon + 1):
            X.append(series[i: i + self.seq_len])
            y.append(series[i + self.seq_len: i + self.seq_len + self.forecast_horizon])
        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit(self, series: np.ndarray) -> "PatchTSTForecaster":
        """
        Train PatchTST on a univariate time series.

        Args:
            series: 1-D numpy array with at least seq_len + forecast_horizon observations.
        Returns:
            self
        """
        self._series = series.astype(np.float64)
        self._mean = float(np.mean(series))
        self._std = float(np.std(series)) or 1.0

        min_len = self.seq_len + self.forecast_horizon
        if not TORCH_AVAILABLE or len(series) < min_len:
            logger.warning(
                f"PatchTSTForecaster using linear fallback "
                f"(series_len={len(series)} < min_len={min_len} or torch missing)."
            )
            x = np.arange(len(series))
            self._fallback_coeffs = np.polyfit(x, series, 1)
            return self

        norm_series = self._normalize(self._series).astype(np.float32)
        X, y = self._build_samples(norm_series)

        if len(X) == 0:
            # Not enough sliding windows — fall back
            logger.warning("PatchTSTForecaster: not enough windows for training, using linear fallback.")
            x = np.arange(len(series))
            self._fallback_coeffs = np.polyfit(x, series, 1)
            return self

        model = _PatchTSTModel(
            seq_len=self.seq_len,
            patch_len=self.patch_len,
            stride=self.stride,
            d_model=self.d_model,
            n_heads=self.n_heads,
            n_layers=self.n_layers,
            dim_ff=self.dim_ff,
            dropout=self.dropout,
            forecast_horizon=self.forecast_horizon,
        )

        optimizer = torch.optim.Adam(model.parameters(), lr=self.lr)
        criterion = nn.MSELoss()

        X_t = torch.tensor(X)
        y_t = torch.tensor(y)

        model.train()
        for epoch in range(self.epochs):
            optimizer.zero_grad()
            pred = model(X_t)
            loss = criterion(pred, y_t)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

        self._model = model
        logger.info(f"PatchTSTForecaster trained for {self.epochs} epochs. Final loss={loss.item():.5f}")
        return self

    def predict(self, horizon: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate horizon-step forecasts with 95% confidence intervals (via MC-Dropout).

        Args:
            horizon: Number of steps to forecast (defaults to self.forecast_horizon).
        Returns:
            dict with predictions, confidence_lower, confidence_upper, model_used, horizon_days.
        """
        h = horizon or self.forecast_horizon

        if self._series is None:
            raise RuntimeError("PatchTSTForecaster.fit() must be called before predict().")

        if self._fallback_coeffs is not None:
            # Linear trend fallback
            n = len(self._series)
            std_val = float(np.std(self._series)) * 0.5 or 1.0
            predictions = [
                max(0.0, float(np.polyval(self._fallback_coeffs, n + i)))
                for i in range(h)
            ]
            lower = [max(0.0, p - 1.96 * std_val) for p in predictions]
            upper = [p + 1.96 * std_val for p in predictions]
            return {
                "predictions": predictions,
                "confidence_lower": lower,
                "confidence_upper": upper,
                "model_used": "patchtst_fallback",
                "horizon_days": h,
            }

        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch not available.")

        norm_series = self._normalize(self._series).astype(np.float32)
        # Use the last seq_len observations as input
        input_seq = norm_series[-self.seq_len:]
        if len(input_seq) < self.seq_len:
            # Pad left with zeros if series is shorter than seq_len
            pad = np.zeros(self.seq_len - len(input_seq), dtype=np.float32)
            input_seq = np.concatenate([pad, input_seq])

        input_t = torch.tensor(input_seq).unsqueeze(0)  # (1, seq_len)

        # MC-Dropout: run 8 forward passes with dropout active to get uncertainty
        n_mc = 8
        mc_preds = []
        self._model.train()  # enable dropout
        with torch.no_grad():
            for _ in range(n_mc):
                out = self._model(input_t)      # (1, forecast_horizon)
                mc_preds.append(out.squeeze(0).numpy())

        mc_preds = np.stack(mc_preds, axis=0)   # (n_mc, forecast_horizon)
        mean_pred = mc_preds.mean(axis=0)
        std_pred = mc_preds.std(axis=0)

        # Denormalize
        mean_pred = self._denormalize(mean_pred)
        lower = mean_pred - 1.96 * self._denormalize(std_pred)
        upper = mean_pred + 1.96 * self._denormalize(std_pred)

        # Clip to first h steps in case horizon < forecast_horizon
        predictions = [max(0.0, float(v)) for v in mean_pred[:h]]
        conf_lower  = [max(0.0, float(v)) for v in lower[:h]]
        conf_upper  = [float(v) for v in upper[:h]]

        return {
            "predictions": predictions,
            "confidence_lower": conf_lower,
            "confidence_upper": conf_upper,
            "model_used": "patchtst",
            "horizon_days": h,
        }
