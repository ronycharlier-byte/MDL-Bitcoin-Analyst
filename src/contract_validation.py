from __future__ import annotations

from collections.abc import Iterable
from copy import deepcopy
from enum import StrEnum
from typing import Any, cast


class DataStatus(StrEnum):
    REAL = "real"
    INFERRED = "inferred"
    ABSENT = "absent"
    MOCK = "mock"
    MOCK_PAPER = "mock_paper"
    UNKNOWN = "unknown"
    STALE = "stale"
    AMBIGUOUS = "ambiguous_status"


class ErrorCode(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    UNSUPPORTED_ASSET = "UNSUPPORTED_ASSET"
    BITGET_UNAVAILABLE = "BITGET_UNAVAILABLE"
    SPOT_MISSING = "SPOT_MISSING"
    SPOT_STALE = "SPOT_STALE"
    MARKET_HISTORY_INSUFFICIENT = "MARKET_HISTORY_INSUFFICIENT"
    FUNDAMENTAL_SOURCE_UNAVAILABLE = "FUNDAMENTAL_SOURCE_UNAVAILABLE"
    ARCHIVE_NOT_FOUND = "ARCHIVE_NOT_FOUND"
    ARCHIVE_MISMATCH = "ARCHIVE_MISMATCH"
    SPOT_SNAPSHOT_MISMATCH = "SPOT_SNAPSHOT_MISMATCH"
    FRAME_COUNT_MISMATCH = "FRAME_COUNT_MISMATCH"
    QUANTILE_ORDER_INVALID = "QUANTILE_ORDER_INVALID"
    PROBABILITY_OUT_OF_RANGE = "PROBABILITY_OUT_OF_RANGE"
    REGIME_SUM_INVALID = "REGIME_SUM_INVALID"
    RISK_METRIC_INCONSISTENT = "RISK_METRIC_INCONSISTENT"
    BACKTEST_UNAVAILABLE = "BACKTEST_UNAVAILABLE"
    CACHE_STALE = "CACHE_STALE"
    RATE_LIMITED = "RATE_LIMITED"
    STORAGE_UNAVAILABLE = "STORAGE_UNAVAILABLE"
    MODEL_EXECUTION_FAILED = "MODEL_EXECUTION_FAILED"
    SCHEMA_VALIDATION_FAILED = "SCHEMA_VALIDATION_FAILED"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    EXECUTION_FORBIDDEN = "EXECUTION_FORBIDDEN"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ContractViolation(ValueError):
    def __init__(self, code: ErrorCode, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}


_STATUS_ALIASES = {
    "missing": DataStatus.ABSENT,
    "modelled_stress": DataStatus.INFERRED,
    "partial_real_absent": DataStatus.AMBIGUOUS,
    "mock_or_missing": DataStatus.AMBIGUOUS,
    "real_or_mock_per_frame": DataStatus.AMBIGUOUS,
    "absent_unless_supplied": DataStatus.ABSENT,
}


def _object_value(value: Any) -> dict[str, Any]:
    return cast(dict[str, Any], value) if isinstance(value, dict) else {}


def _list_value(value: Any) -> list[Any]:
    return cast(list[Any], value) if isinstance(value, list) else []


def normalize_status(value: Any, default: DataStatus = DataStatus.UNKNOWN) -> str:
    text = str(value or "").strip().lower()
    if text in DataStatus._value2member_map_:
        return text
    return str(_STATUS_ALIASES.get(text, default))


def error_payload(
    code: ErrorCode,
    message: str,
    request_id: str,
    *,
    retryable: bool = False,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": "error",
        "error_code": str(code),
        "message": message,
        "retryable": retryable,
        "details": details or {},
        "request_id": request_id,
    }


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        normalized = value.replace("$", "").replace(",", "").strip() if isinstance(value, str) else value
        number = float(normalized)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _first_number(mapping: dict[str, Any], names: Iterable[str]) -> float | None:
    for name in names:
        number = _number(mapping.get(name))
        if number is not None:
            return number
    return None


def _canonical_risk(risk: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(risk)
    aliases = {
        "var95_loss": ("var95_loss", "var_95"),
        "cvar95_loss": ("cvar95_loss", "cvar_95"),
        "var99_loss": ("var99_loss", "var_99"),
        "cvar99_loss": ("cvar99_loss", "cvar_99"),
    }
    for canonical, names in aliases.items():
        result[canonical] = _first_number(risk, names)
    result.setdefault("loss_sign_convention", "positive_loss")
    result.setdefault("status", DataStatus.INFERRED)
    return result


def canonical_frame(frame: dict[str, Any], *, fallback_model: str = "ensemble") -> dict[str, Any]:
    distribution = _object_value(frame.get("distribution"))
    quantiles = _object_value(frame.get("quantiles"))
    regimes_legacy = _object_value(frame.get("regime_distribution")) or _object_value(frame.get("regimes"))
    transition = _first_number(regimes_legacy, ("transition", "non_classified_transition"))
    regimes = {
        "bull": _first_number(regimes_legacy, ("bull",)) or 0.0,
        "bear": _first_number(regimes_legacy, ("bear",)) or 0.0,
        "range": _first_number(regimes_legacy, ("range",)) or 0.0,
        "transition": transition if transition is not None else 0.0,
    }
    confidence_value = frame.get("confidence")
    confidence = (
        deepcopy(confidence_value) if isinstance(confidence_value, dict) else {"score": _number(confidence_value)}
    )
    data_status = _object_value(frame.get("data_status"))
    status = normalize_status(data_status.get("simulation_outputs") or frame.get("status"), DataStatus.INFERRED)
    result = deepcopy(frame)
    result.pop("position_sizing", None)
    result.update(
        {
            "horizon_days": int(frame.get("horizon_days") or frame.get("horizon") or 0),
            "model_name": str(frame.get("model_name") or frame.get("model") or fallback_model),
            "model_version": str(
                frame.get("model_version") or (frame.get("version") or {}).get("model_version") or "unknown"
            ),
            "simulation_count": int(frame.get("simulation_count") or frame.get("simulations") or 0),
            "probability_up": _first_number(frame, ("probability_up",))
            if _first_number(frame, ("probability_up",)) is not None
            else _first_number(distribution, ("probability_up", "prob_up")),
            "quantiles": {
                "p10": _first_number(quantiles, ("p10",))
                if _first_number(quantiles, ("p10",)) is not None
                else _first_number(distribution, ("p10", "p10_return")),
                "median": _first_number(quantiles, ("median",))
                if _first_number(quantiles, ("median",)) is not None
                else _first_number(distribution, ("median", "median_return")),
                "p90": _first_number(quantiles, ("p90",))
                if _first_number(quantiles, ("p90",)) is not None
                else _first_number(distribution, ("p90", "p90_return")),
            },
            "regimes": regimes,
            "risk": _canonical_risk(_object_value(frame.get("risk_metrics")) or _object_value(frame.get("risk"))),
            "confidence": confidence,
            "monte_carlo": deepcopy(frame.get("monte_carlo_error") or {}),
            "stability": deepcopy(frame.get("multi_seed_stability") or {}),
            "warnings": [str(frame["warning"])] if frame.get("warning") else [],
            "status": status,
        }
    )
    return result


def _data_inventory(payload: dict[str, Any]) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    statuses = _object_value(payload.get("data_status"))
    for field, value in sorted(statuses.items()):
        inventory.append(
            {
                "field": str(field),
                "value": None,
                "status": normalize_status(value),
                "source": None,
                "observed_at_utc": None,
                "unit": None,
                "limitations": [],
            }
        )
    fundamentals = _object_value(payload.get("fundamental_inputs"))
    values = _object_value(fundamentals.get("values"))
    field_status = _object_value(fundamentals.get("field_status"))
    sources = _list_value(fundamentals.get("sources"))
    for field in sorted(set(values) | set(field_status)):
        inventory.append(
            {
                "field": str(field),
                "value": values.get(field),
                "status": normalize_status(field_status.get(field), DataStatus.ABSENT),
                "source": ", ".join(str(item) for item in sources) or None,
                "observed_at_utc": fundamentals.get("timestamp_utc"),
                "unit": None,
                "limitations": ["Point-in-time context; unit is source-specific unless explicitly supplied."],
            }
        )
    return inventory


def canonicalize_analysis_payload(payload: dict[str, Any], *, endpoint: str) -> dict[str, Any]:
    payload.pop("position_sizing", None)
    archive = _object_value(payload.get("archive"))
    version = _object_value(payload.get("version"))
    summary = _object_value(payload.get("provenance_summary"))
    existing_provenance = _object_value(payload.get("provenance"))
    legacy_frames = _list_value(payload.get("frames"))
    if not legacy_frames and payload.get("run_id"):
        legacy_frames = [payload]
    frames = [
        canonical_frame(frame, fallback_model=str(payload.get("model") or "ensemble"))
        for frame in legacy_frames
        if isinstance(frame, dict)
    ]
    spot_value = _object_value(summary.get("shared_spot_snapshot")) or _object_value(existing_provenance.get("spot"))
    if not spot_value and frames:
        spot_value = _object_value(frames[0].get("provenance"))
    cache = _object_value(payload.get("cache")) or _object_value(existing_provenance.get("cache"))
    cache_age = _number(cache.get("age_seconds")) or 0.0
    archive_id = str(payload.get("archive_id") or archive.get("archive_id") or summary.get("archive_id") or "")
    generated_utc = (
        summary.get("report_date_utc")
        or archive.get("report_date_utc")
        or existing_provenance.get("report_generated_at_utc")
    )
    generated_local = (
        summary.get("report_date_paris")
        or archive.get("report_date_paris")
        or existing_provenance.get("report_generated_at_local")
    )
    canonical_provenance = {
        "report_generated_at_utc": generated_utc,
        "report_generated_at_local": generated_local,
        "timezone": "Europe/Paris",
        "archive_created_at_utc": archive.get("created_at_utc") or existing_provenance.get("archive_created_at_utc"),
        "api_version": version.get("api_version") or existing_provenance.get("api_version"),
        "worker_version": version.get("worker_version") or existing_provenance.get("worker_version"),
        "model_version": version.get("model_version") or existing_provenance.get("model_version"),
        "schema_version": version.get("schema_version") or existing_provenance.get("schema_version"),
        "git_commit": version.get("git_commit") or existing_provenance.get("git_commit"),
        "runtime": summary.get("runtime") or existing_provenance.get("runtime") or "python_fastapi",
        "cache": {
            "status": "hit" if cache.get("hit") or cache.get("status") == "hit" else "miss",
            "age_seconds": cache_age,
            "freshness_threshold_seconds": _number(cache.get("ttl_seconds")) or 0.0,
            "freshness_class": "recent" if cache_age <= (_number(cache.get("ttl_seconds")) or 0.0) else "unknown",
        },
        "spot": {
            "value": _first_number(spot_value, ("value", "price", "reference_spot")),
            "currency": "USDT",
            "source": spot_value.get("source") or spot_value.get("reference_spot_source"),
            "observed_at_utc": spot_value.get("observed_at_utc")
            or spot_value.get("timestamp")
            or spot_value.get("reference_spot_timestamp_utc"),
            "observed_at_local": spot_value.get("observed_at_local")
            or spot_value.get("reference_spot_timestamp_paris"),
            "age_seconds": _number(spot_value.get("age_seconds")),
            "status": normalize_status(
                spot_value.get("status")
                or _object_value(frames[0].get("data_status") if frames else {}).get("market_prices"),
                DataStatus.REAL,
            ),
        },
    }
    warnings = [str(payload["warning"])] if payload.get("warning") else []
    warnings.extend(str(item) for item in _list_value(payload.get("warnings")))
    limitations = [
        "Probabilistic research output only; no deterministic prediction.",
        "Financial advice and buy/sell recommendations are forbidden.",
        "Execution authority is none; paper trading is mock-only.",
    ]
    limitations.extend(str(item) for item in _list_value(payload.get("limitations")))
    response_type = (
        "comparison"
        if "compare" in endpoint
        else "deep"
        if "deep" in endpoint
        else "quick"
        if "quick" in endpoint
        else "standard"
    )
    payload.update(
        {
            "status": str(payload.get("status") or "ok"),
            "asset": str(payload.get("asset") or "BTC").upper(),
            "response_type": response_type,
            "archive_id": archive_id,
            "analysis_id": archive_id,
            "provenance": canonical_provenance,
            "data_inventory": _data_inventory(payload) or deepcopy(_list_value(payload.get("data_inventory"))),
            "frames": frames,
            "backtests": deepcopy(payload.get("backtest_diagnostics") or {}),
            "alerts": deepcopy(payload.get("alerts") or []),
            "warnings": list(dict.fromkeys(warnings)),
            "limitations": list(dict.fromkeys(limitations)),
            "policy": {
                "user_effect": "information_only",
                "execution_authority": "none",
                "financial_advice": False,
                "paper_trading": "mock_only",
                "live_trading": "blocked",
            },
            "contract": {
                "schema": "contracts/analysis.schema.json",
                "schema_version": "2.0.0",
                "compatibility_endpoint": endpoint,
            },
        }
    )
    return payload


def _require_probability(value: Any, path: str) -> float:
    number = _number(value)
    if number is None or not 0.0 <= number <= 1.0:
        raise ContractViolation(
            ErrorCode.PROBABILITY_OUT_OF_RANGE,
            f"Probability at {path} must be between 0 and 1.",
            {"path": path, "value": value},
        )
    return number


def validate_frame(frame: dict[str, Any], index: int = 0) -> None:
    horizon = int(frame.get("horizon_days") or 0)
    simulations = int(frame.get("simulation_count") or 0)
    if horizon <= 0 or simulations <= 0:
        raise ContractViolation(
            ErrorCode.SCHEMA_VALIDATION_FAILED,
            "Frame horizon_days and simulation_count must be positive.",
            {"frame": index, "horizon_days": horizon, "simulation_count": simulations},
        )
    _require_probability(frame.get("probability_up"), f"frames[{index}].probability_up")
    quantiles = _object_value(frame.get("quantiles"))
    p10, median, p90 = (_number(quantiles.get(name)) for name in ("p10", "median", "p90"))
    if p10 is None or median is None or p90 is None or not p10 <= median <= p90:
        raise ContractViolation(
            ErrorCode.QUANTILE_ORDER_INVALID,
            "Frame quantiles must satisfy p10 <= median <= p90.",
            {"frame": index, "quantiles": quantiles},
        )
    regimes = _object_value(frame.get("regimes"))
    total = sum(
        [
            _require_probability(regimes.get(name), f"frames[{index}].regimes.{name}")
            for name in ("bull", "bear", "range", "transition")
        ]
    )
    if abs(total - 1.0) > 0.015:
        raise ContractViolation(
            ErrorCode.REGIME_SUM_INVALID,
            "Frame regime probabilities must sum to 1 within tolerance.",
            {"frame": index, "sum": total},
        )
    risk = _object_value(frame.get("risk"))
    var95, cvar95, var99, cvar99 = (
        _number(risk.get(name)) for name in ("var95_loss", "cvar95_loss", "var99_loss", "cvar99_loss")
    )
    if (
        var95 is not None
        and cvar95 is not None
        and var99 is not None
        and cvar99 is not None
        and not (var99 >= var95 and cvar95 >= var95 and cvar99 >= var99 and cvar99 >= cvar95)
    ):
        raise ContractViolation(
            ErrorCode.RISK_METRIC_INCONSISTENT,
            "Risk metrics violate the positive-loss VaR/CVaR ordering.",
            {"frame": index, "risk": risk},
        )
    confidence = _object_value(frame.get("confidence"))
    score = _number(confidence.get("score"))
    if score is not None and not 0.0 <= score <= 100.0:
        raise ContractViolation(
            ErrorCode.SCHEMA_VALIDATION_FAILED,
            "Confidence score must be between 0 and 100.",
            {"frame": index, "score": score},
        )


def validate_analysis_payload(payload: dict[str, Any]) -> None:
    if payload.get("asset") != "BTC":
        raise ContractViolation(ErrorCode.UNSUPPORTED_ASSET, "Only BTC is supported.", {"asset": payload.get("asset")})
    archive_id = payload.get("archive_id")
    if not isinstance(archive_id, str) or not archive_id:
        raise ContractViolation(ErrorCode.ARCHIVE_NOT_FOUND, "archive_id is required on analysis payloads.")
    provenance = _object_value(payload.get("provenance"))
    spot = _object_value(provenance.get("spot"))
    if (_number(spot.get("value")) or 0.0) <= 0.0 or not spot.get("source") or not spot.get("observed_at_utc"):
        raise ContractViolation(
            ErrorCode.SPOT_MISSING,
            "A positive reference spot with source and UTC observation time is required.",
        )
    if normalize_status(spot.get("status")) == DataStatus.STALE:
        raise ContractViolation(ErrorCode.SPOT_STALE, "The reference spot is stale.")
    frames = payload.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ContractViolation(ErrorCode.FRAME_COUNT_MISMATCH, "At least one analysis frame is required.")
    for index, frame in enumerate(frames):
        if not isinstance(frame, dict):
            raise ContractViolation(
                ErrorCode.SCHEMA_VALIDATION_FAILED, "Each frame must be an object.", {"frame": index}
            )
        validate_frame(frame, index)
