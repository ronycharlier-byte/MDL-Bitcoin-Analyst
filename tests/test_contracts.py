from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from contract_validation import (
    ContractViolation,
    ErrorCode,
    canonicalize_analysis_payload,
    validate_analysis_payload,
)

ROOT = Path(__file__).resolve().parents[1]


def fixture_payload() -> dict:
    return json.loads((ROOT / "contracts" / "fixtures" / "analysis.valid.json").read_text(encoding="utf-8"))


def test_canonical_fixture_satisfies_schema_and_semantic_invariants() -> None:
    payload = fixture_payload()
    schema = json.loads((ROOT / "contracts" / "analysis.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)
    validate_analysis_payload(payload)


def test_invalid_quantile_order_has_stable_error_code() -> None:
    payload = fixture_payload()
    payload["frames"][0]["quantiles"] = {"p10": 0.1, "median": 0.0, "p90": 0.2}
    with pytest.raises(ContractViolation) as exc_info:
        validate_analysis_payload(payload)
    assert exc_info.value.code == ErrorCode.QUANTILE_ORDER_INVALID


def test_invalid_regime_sum_is_rejected() -> None:
    payload = fixture_payload()
    payload["frames"][0]["regimes"]["bull"] = 0.9
    with pytest.raises(ContractViolation) as exc_info:
        validate_analysis_payload(payload)
    assert exc_info.value.code == ErrorCode.REGIME_SUM_INVALID


def test_canonicalization_is_idempotent_for_required_frame_fields() -> None:
    original = fixture_payload()
    payload = canonicalize_analysis_payload(deepcopy(original), endpoint="/test")
    frame = payload["frames"][0]
    assert frame["probability_up"] == original["frames"][0]["probability_up"]
    assert frame["quantiles"] == original["frames"][0]["quantiles"]
    assert frame["regimes"] == original["frames"][0]["regimes"]
    validate_analysis_payload(payload)


def test_legacy_runtime_payload_is_upgraded_with_formatted_spot() -> None:
    legacy = {
        "status": "ok",
        "asset": "BTC",
        "model": "ensemble",
        "position_sizing": {"kelly_fraction": 0.2},
        "archive": {
            "archive_id": "archive-legacy-1",
            "report_date_utc": "2026-07-17T12:00:00Z",
            "report_date_paris": "2026-07-17T14:00:00+02:00",
        },
        "frames": [
            {
                "horizon": 30,
                "run_id": "legacy-run-1",
                "simulations": 5000,
                "model": "ensemble",
                "version": {"model_version": "legacy-v1"},
                "provenance": {
                    "reference_spot": "$102,345.67",
                    "reference_spot_source": "bitget_public_market_api",
                    "reference_spot_timestamp_utc": "2026-07-17T11:59:30Z",
                },
                "data_status": {"market_prices": "real", "simulation_outputs": "inferred"},
                "distribution": {"prob_up": 0.56, "p10_return": -0.2, "median_return": 0.03, "p90_return": 0.3},
                "regime_distribution": {"bull": 0.3, "bear": 0.2, "range": 0.4, "non_classified_transition": 0.1},
                "risk_metrics": {"var_95": 0.28, "cvar_95": 0.35, "var_99": 0.39, "cvar_99": 0.47},
                "confidence": {"score": 60},
                "position_sizing": {"kelly_fraction": 0.2},
            }
        ],
    }
    payload = canonicalize_analysis_payload(legacy, endpoint="/multi-run")
    assert payload["provenance"]["spot"]["value"] == 102345.67
    assert "position_sizing" not in payload
    assert "position_sizing" not in payload["frames"][0]
    validate_analysis_payload(payload)
