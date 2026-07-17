from __future__ import annotations

import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from backtest import run_backtest
from confidence_score import data_quality_dimensions
from ensemble_model import weight_diagnostics
from risk_metrics import compute_risk_metrics
from simulation_utils import seed_for


def test_seed_is_stable_across_python_processes() -> None:
    expected = seed_for("ensemble", 42)
    code = (
        "import sys; sys.path.insert(0, 'src'); from simulation_utils import seed_for; print(seed_for('ensemble', 42))"
    )
    completed = subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)
    assert int(completed.stdout.strip()) == expected


def test_risk_metrics_use_positive_loss_and_consistent_tail_order() -> None:
    returns = np.array([-0.50, -0.40, -0.30, -0.20, -0.10, 0.0, 0.05, 0.10, 0.20, 0.30])
    risk = compute_risk_metrics(returns)
    assert risk["loss_sign_convention"] == "positive_loss"
    assert risk["var99_loss"] >= risk["var95_loss"] >= 0
    assert risk["cvar95_loss"] >= risk["var95_loss"]
    assert risk["cvar99_loss"] >= risk["var99_loss"]


def test_ensemble_weights_are_normalized_shrunk_and_capped() -> None:
    names = [f"model_{index}" for index in range(7)]
    rows = [
        {
            "model": name,
            "observations": 100,
            "brier_score": 0.05 if index == 0 else 0.35,
            "calibration_error": 0.02 if index == 0 else 0.25,
            "p10_p90_coverage": 0.80 if index == 0 else 0.50,
        }
        for index, name in enumerate(names)
    ]
    diagnostics = weight_diagnostics(names, rows)
    assert sum(diagnostics["weights"].values()) == pytest.approx(1.0)
    assert diagnostics["maximum_weight"] <= 0.35 + 1e-12
    assert all(weight > 0 for weight in diagnostics["weights"].values())


def test_walk_forward_backtest_records_period_and_probabilistic_scores() -> None:
    rng = np.random.default_rng(7)
    prices = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.015, 140)))
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2025-01-01", periods=len(prices), tz="UTC"),
            "close": prices,
            "statut": "real",
        }
    )
    result = run_backtest(frame, "BTC", "normal_baseline", horizons=(7,), train_window=30)[0]
    assert result["observations"] > 0
    assert 0 <= result["brier_score"] <= 1
    assert result["log_loss"] >= 0
    assert result["period_start_utc"] is not None
    assert result["period_end_utc"] is not None
    assert result["brier_score_bootstrap_ci"]["seed"] == 49


def test_data_quality_exposes_separate_transparent_dimensions() -> None:
    now = pd.Timestamp.now(tz="UTC")
    prices = pd.DataFrame(
        {
            "timestamp": [now - pd.Timedelta(days=1), now],
            "close": [100.0, 101.0],
            "statut": ["real", "real"],
        }
    )
    fundamentals = pd.DataFrame(
        {
            "timestamp": [now],
            "funding_rate": [0.001],
            "statut": ["real"],
        }
    )
    dimensions, notes = data_quality_dimensions(prices, fundamentals)
    assert set(dimensions) == {
        "freshness",
        "completeness",
        "consistency",
        "source_integrity",
        "temporal_alignment",
    }
    assert all(0 <= value <= 100 for value in dimensions.values())
    assert dimensions["source_integrity"] == 100
    assert notes == []
