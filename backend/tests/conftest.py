# File: backend/tests/conftest.py
# Description: Pytest configuration and shared fixtures for SwasthyaGrid AI backend tests.

import sys
import os
import pytest
import numpy as np

# Ensure project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))


@pytest.fixture(scope="session")
def sample_medicine_stocks():
    """Representative medicine stock dicts for alert engine tests."""
    return [
        {"medicine_name": "Paracetamol 500mg",   "current_quantity": 540,  "daily_burn_rate": 180.0, "id": "m1"},
        {"medicine_name": "Amoxicillin 250mg",   "current_quantity": 30,   "daily_burn_rate": 75.0,  "id": "m2"},  # CRITICAL
        {"medicine_name": "ORS Sachets",         "current_quantity": 250,  "daily_burn_rate": 60.0,  "id": "m3"},  # WARNING
        {"medicine_name": "Oxytocin 5 IU",       "current_quantity": 200,  "daily_burn_rate": 8.0,   "id": "m4"},
        {"medicine_name": "Anti-Snake Venom",    "current_quantity": 4,    "daily_burn_rate": 3.0,   "id": "m5"},  # CRITICAL
    ]


@pytest.fixture(scope="session")
def daily_series_30():
    rng = np.random.default_rng(0)
    return (rng.normal(50, 8, 30)).clip(min=0)


@pytest.fixture(scope="session")
def daily_series_90():
    rng = np.random.default_rng(0)
    trend = np.linspace(40, 65, 90)
    return (trend + rng.normal(0, 6, 90)).clip(min=0)
