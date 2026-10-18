# File: backend/app/ml/time_series_transformer.py
# Description: PyTorch Multi-Head Self-Attention Time Series Transformer for healthcare demand forecasting.
#   Falls back gracefully if PyTorch is not installed (free-tier / lightweight deployment).

import math
import logging
import numpy as np

logger = logging.getLogger("swasthya.ml.transformer")

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not installed — TimeSeriesTransformer will not be available.")


if TORCH_AVAILABLE:
    class PositionalEncoding(nn.Module):
        """Sinusoidal Positional Encoding for temporal sequence awareness."""
        def __init__(self, d_model: int, max_len: int = 500):
            super().__init__()
            pe = torch.zeros(max_len, d_model)
            position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
            div_term = torch.exp(
                torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
            )
            pe[:, 0::2] = torch.sin(position * div_term)
            pe[:, 1::2] = torch.cos(position * div_term)
            self.register_buffer("pe", pe.unsqueeze(0))

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            return x + self.pe[:, : x.size(1)]

    class TimeSeriesTransformer(nn.Module):
        """
        Multi-Head Self-Attention Transformer for Multivariate Health Facility Time Series.
        Predicts multi-step future values with predictive variance for confidence bands.
        """
        def __init__(
            self,
            input_dim: int = 4,
            d_model: int = 64,
            nhead: int = 4,
            num_layers: int = 3,
            dim_feedforward: int = 128,
            forecast_horizon: int = 14,
            dropout: float = 0.1,
        ):
            super().__init__()
            self.input_dim = input_dim
            self.d_model = d_model
            self.forecast_horizon = forecast_horizon

            self.input_projection = nn.Linear(input_dim, d_model)
            self.pos_encoder = PositionalEncoding(d_model)

            encoder_layer = nn.TransformerEncoderLayer(
                d_model=d_model,
                nhead=nhead,
                dim_feedforward=dim_feedforward,
                dropout=dropout,
                batch_first=True,
                activation="gelu",
            )
            self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

            self.mean_head = nn.Sequential(
                nn.Linear(d_model, dim_feedforward),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(dim_feedforward, forecast_horizon),
            )
            self.variance_head = nn.Sequential(
                nn.Linear(d_model, dim_feedforward // 2),
                nn.GELU(),
                nn.Linear(dim_feedforward // 2, forecast_horizon),
                nn.Softplus(),
            )

        def forward(self, x: "torch.Tensor"):
            projected = self.input_projection(x) * math.sqrt(self.d_model)
            encoded_inputs = self.pos_encoder(projected)
            memory = self.transformer_encoder(encoded_inputs)
            last_step_repr = memory[:, -1, :]
            predicted_mean = self.mean_head(last_step_repr)
            predicted_std = self.variance_head(last_step_repr)
            return predicted_mean, predicted_std, memory

else:
    # Stub classes so imports don't break when torch is absent
    class PositionalEncoding:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            pass

    class TimeSeriesTransformer:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "PyTorch is required for TimeSeriesTransformer. "
                "Install it with: pip install torch"
            )
