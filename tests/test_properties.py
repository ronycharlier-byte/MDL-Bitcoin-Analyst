from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from contract_validation import validate_analysis_payload
from ensemble_model import weight_diagnostics
from risk_metrics import compute_risk_metrics
from simulation_utils import seed_for

FINITE_RETURN = st.floats(min_value=-0.95, max_value=2.0, allow_nan=False, allow_infinity=False)
ROOT = Path(__file__).resolve().parents[1]


def fixture_payload() -> dict:
    return json.loads((ROOT / "contracts" / "fixtures" / "analysis.valid.json").read_text(encoding="utf-8"))


@settings(max_examples=75, deadline=None)
@given(
    probability=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    quantiles=st.lists(
        st.floats(min_value=-2.0, max_value=5.0, allow_nan=False, allow_infinity=False),
        min_size=3,
        max_size=3,
    ).map(sorted),
    regime_weights=st.lists(
        st.floats(min_value=0.001, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=4,
        max_size=4,
    ),
)
def test_valid_generated_frames_preserve_contract_invariants(
    probability: float,
    quantiles: list[float],
    regime_weights: list[float],
) -> None:
    payload = deepcopy(fixture_payload())
    frame = payload["frames"][0]
    frame["probability_up"] = probability
    frame["quantiles"] = dict(zip(("p10", "median", "p90"), quantiles, strict=True))
    total = sum(regime_weights)
    normalized = [value / total for value in regime_weights]
    frame["regimes"] = dict(zip(("bull", "bear", "range", "transition"), normalized, strict=True))

    validate_analysis_payload(payload)


@settings(max_examples=75, deadline=None)
@given(returns=st.lists(FINITE_RETURN, min_size=10, max_size=250))
def test_generated_tail_risk_is_finite_and_ordered(returns: list[float]) -> None:
    risk = compute_risk_metrics(np.asarray(returns, dtype=float))
    tail_fields = ["var95_loss", "cvar95_loss", "var99_loss", "cvar99_loss"]
    assert all(np.isfinite(risk[field]) for field in tail_fields)
    assert risk["var99_loss"] >= risk["var95_loss"] >= 0
    assert risk["cvar95_loss"] >= risk["var95_loss"]
    assert risk["cvar99_loss"] >= risk["var99_loss"]
    assert risk["cvar99_loss"] >= risk["cvar95_loss"]


@settings(max_examples=50, deadline=None)
@given(
    labels=st.lists(st.text(min_size=1, max_size=16), min_size=1, max_size=5),
    base_seed=st.integers(min_value=0, max_value=2**32 - 1),
)
def test_seed_derivation_is_reproducible(labels: list[str], base_seed: int) -> None:
    label = "\x1f".join(labels)
    assert seed_for(label, base_seed) == seed_for(label, base_seed)


@settings(max_examples=50, deadline=None)
@given(
    scores=st.lists(
        st.tuples(
            st.floats(min_value=0.001, max_value=0.999, allow_nan=False, allow_infinity=False),
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        ),
        min_size=3,
        max_size=10,
    )
)
def test_generated_ensemble_weights_are_positive_normalized_and_capped(
    scores: list[tuple[float, float, float]],
) -> None:
    names = [f"model_{index}" for index in range(len(scores))]
    diagnostics = weight_diagnostics(
        names,
        [
            {
                "model": name,
                "observations": 100,
                "brier_score": score[0],
                "calibration_error": score[1],
                "p10_p90_coverage": score[2],
            }
            for name, score in zip(names, scores, strict=True)
        ],
    )
    weights = list(diagnostics["weights"].values())
    assert sum(weights) == pytest.approx(1.0)
    assert all(0 < weight <= 0.35 + 1e-12 for weight in weights)
