from __future__ import annotations

import numpy as np
import pandas as pd


def _bounded(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return float(max(lo, min(hi, value)))


def data_quality_dimensions(
    price_frame: pd.DataFrame,
    fundamentals: pd.DataFrame | None,
) -> tuple[dict[str, float], list[str]]:
    notes: list[str] = []
    if price_frame is None or price_frame.empty:
        return {
            "freshness": 0.0,
            "completeness": 0.0,
            "consistency": 0.0,
            "source_integrity": 0.0,
            "temporal_alignment": 0.0,
        }, ["No market price history."]

    statuses = set(price_frame.get("statut", pd.Series(dtype=str)).dropna().astype(str).str.lower())
    if "real" in statuses and "mock" not in statuses:
        source_integrity = 100.0
    elif "mock" in statuses:
        source_integrity = 0.0
        notes.append("Market prices are tagged MOCK.")
    else:
        source_integrity = 25.0
        notes.append("Market price source status is unknown or incomplete.")

    close = pd.to_numeric(price_frame.get("close", pd.Series(dtype=float)), errors="coerce")
    close_ratio = float(close.notna().mean()) if len(price_frame) else 0.0
    positive_close_ratio = float((close.dropna() > 0).mean()) if close.notna().any() else 0.0
    completeness = 70.0 * close_ratio
    consistency = 60.0 * positive_close_ratio

    price_timestamps = pd.to_datetime(price_frame.get("timestamp", pd.Series(dtype=str)), utc=True, errors="coerce")
    valid_price_timestamps = price_timestamps.dropna()
    freshness = 0.0
    if not valid_price_timestamps.empty:
        age_days = max(0.0, (pd.Timestamp.now(tz="UTC") - valid_price_timestamps.max()).total_seconds() / 86400.0)
        freshness = 100.0 if age_days <= 2 else 50.0 if age_days <= 7 else 0.0
        consistency += 20.0 if valid_price_timestamps.is_monotonic_increasing else 0.0
        consistency += 20.0 if not valid_price_timestamps.duplicated().any() else 0.0
    else:
        notes.append("Market timestamps are absent or invalid.")

    temporal_alignment = 0.0
    if fundamentals is None or fundamentals.empty:
        notes.append("Fundamental feature table is empty.")
    else:
        feature_columns = [c for c in fundamentals.columns if c not in {"timestamp", "asset", "source", "statut"}]
        available = float(fundamentals[feature_columns].notna().mean().mean()) if feature_columns else 0.0
        completeness += 30.0 * available
        if available < 0.25:
            notes.append("Most fundamental features are NULL.")
        fundamental_timestamps = pd.to_datetime(
            fundamentals.get("timestamp", pd.Series(dtype=str)),
            utc=True,
            errors="coerce",
        ).dropna()
        if not valid_price_timestamps.empty and not fundamental_timestamps.empty:
            delta_days = abs((valid_price_timestamps.max() - fundamental_timestamps.max()).total_seconds()) / 86400.0
            temporal_alignment = 100.0 if delta_days <= 2 else 50.0 if delta_days <= 7 else 0.0
        else:
            notes.append("Price/fundamental temporal alignment cannot be established.")

    return {
        "freshness": _bounded(freshness),
        "completeness": _bounded(completeness),
        "consistency": _bounded(consistency),
        "source_integrity": _bounded(source_integrity),
        "temporal_alignment": _bounded(temporal_alignment),
    }, notes


def data_quality_score(price_frame: pd.DataFrame, fundamentals: pd.DataFrame | None) -> tuple[float, list[str]]:
    dimensions, notes = data_quality_dimensions(price_frame, fundamentals)
    return _data_quality_composite(dimensions), notes


def _data_quality_composite(dimensions: dict[str, float]) -> float:
    return _bounded(
        0.25 * dimensions["freshness"]
        + 0.25 * dimensions["completeness"]
        + 0.20 * dimensions["consistency"]
        + 0.20 * dimensions["source_integrity"]
        + 0.10 * dimensions["temporal_alignment"]
    )


def model_stability_score(risk_metrics: dict, distribution: dict) -> tuple[float, list[str]]:
    notes = []
    width = distribution.get("p90_return", 0.0) - distribution.get("p10_return", 0.0)
    cvar = risk_metrics.get("cvar_95") or 0.0
    score = 100.0 - 45.0 * min(width, 3.0) - 35.0 * min(cvar, 1.0)
    if width > 1.0:
        notes.append("Wide P10-P90 interval.")
    if cvar > 0.5:
        notes.append("High tail loss estimate.")
    return _bounded(score), notes


def backtest_score(backtest_rows: list[dict]) -> tuple[float, list[str]]:
    valid = [row for row in backtest_rows if row.get("observations", 0) and row.get("brier_score") is not None]
    if not valid:
        return 25.0, ["Backtest sample is unavailable or insufficient."]
    brier = float(np.mean([row["brier_score"] for row in valid]))
    calibration = float(np.mean([row["calibration_error"] for row in valid]))
    hit = float(np.mean([row["hit_rate"] for row in valid]))
    score = 40.0 * hit + 35.0 * (1.0 - min(brier, 1.0)) + 25.0 * (1.0 - min(calibration, 1.0))
    return _bounded(score), []


def uncertainty_score(distribution: dict) -> tuple[float, list[str]]:
    width = distribution.get("p90_return", 0.0) - distribution.get("p10_return", 0.0)
    score = 100.0 - 60.0 * min(width, 1.5)
    notes = ["Distribution uncertainty is high."] if width > 1.0 else []
    return _bounded(score), notes


def compute_confidence_score(
    price_frame: pd.DataFrame,
    fundamentals: pd.DataFrame | None,
    risk_metrics: dict,
    distribution: dict,
    backtest_rows: list[dict],
) -> dict:
    data_dimensions, data_notes = data_quality_dimensions(price_frame, fundamentals)
    data_score = _data_quality_composite(data_dimensions)
    stability, stability_notes = model_stability_score(risk_metrics, distribution)
    backtest, backtest_notes = backtest_score(backtest_rows)
    uncertainty, uncertainty_notes = uncertainty_score(distribution)
    score = 0.35 * data_score + 0.25 * stability + 0.25 * backtest + 0.15 * uncertainty
    interval_width = max(float(distribution.get("p90_return", 0.0)) - float(distribution.get("p10_return", 0.0)), 0.0)
    classified = sum(float(distribution.get(name, 0.0) or 0.0) for name in ("prob_bull", "prob_bear", "prob_range"))
    return {
        "score": int(round(_bounded(score))),
        "status": "inferred",
        "components": {
            "data_quality": round(data_score, 2),
            "data_quality_dimensions": {name: round(value, 2) for name, value in data_dimensions.items()},
            "model_stability": round(stability, 2),
            "backtest": round(backtest, 2),
            "uncertainty": round(uncertainty, 2),
        },
        "uncertainty_dimensions": {
            "aleatoric_uncertainty": round(min(interval_width / 1.5, 1.0), 4),
            "parameter_uncertainty": None,
            "model_uncertainty": round(1.0 - stability / 100.0, 4),
            "regime_uncertainty": round(max(0.0, 1.0 - min(classified, 1.0)), 4),
            "data_quality_uncertainty": round(1.0 - data_score / 100.0, 4),
            "monte_carlo_sampling_error": None,
            "scale": "0_to_1_higher_is_more_uncertain",
        },
        "notes": data_notes + stability_notes + backtest_notes + uncertainty_notes,
    }
