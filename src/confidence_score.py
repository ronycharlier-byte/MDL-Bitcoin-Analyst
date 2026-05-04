from __future__ import annotations

import numpy as np
import pandas as pd


def _bounded(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return float(max(lo, min(hi, value)))


def data_quality_score(price_frame: pd.DataFrame, fundamentals: pd.DataFrame | None) -> tuple[float, list[str]]:
    notes = []
    if price_frame is None or price_frame.empty:
        return 0.0, ["No market price history."]
    status = set(price_frame["statut"].dropna().astype(str).str.lower())
    if "real" in status and "mock" not in status:
        score = 70.0
    elif "mock" in status:
        score = 20.0
        notes.append("Market prices are tagged MOCK.")
    else:
        score = 10.0
        notes.append("Market prices are missing or incomplete.")
    close_ratio = pd.to_numeric(price_frame["close"], errors="coerce").notna().mean()
    score *= float(close_ratio)
    if fundamentals is None or fundamentals.empty:
        score -= 20.0
        notes.append("Fundamental feature table is empty.")
    else:
        feature_columns = [c for c in fundamentals.columns if c not in {"timestamp", "asset", "source", "statut"}]
        available = fundamentals[feature_columns].notna().mean().mean() if feature_columns else 0.0
        score += 30.0 * float(available)
        if available < 0.25:
            notes.append("Most fundamental features are NULL.")
    return _bounded(score), notes


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
    data_score, data_notes = data_quality_score(price_frame, fundamentals)
    stability, stability_notes = model_stability_score(risk_metrics, distribution)
    backtest, backtest_notes = backtest_score(backtest_rows)
    uncertainty, uncertainty_notes = uncertainty_score(distribution)
    score = 0.35 * data_score + 0.25 * stability + 0.25 * backtest + 0.15 * uncertainty
    return {
        "score": int(round(_bounded(score))),
        "components": {
            "data_quality": round(data_score, 2),
            "model_stability": round(stability, 2),
            "backtest": round(backtest, 2),
            "uncertainty": round(uncertainty, 2),
        },
        "notes": data_notes + stability_notes + backtest_notes + uncertainty_notes,
    }
