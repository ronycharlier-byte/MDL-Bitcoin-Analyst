from __future__ import annotations

import numpy as np
import pandas as pd

from config import TRADING_DAYS
from simulation_utils import clean_returns


def value_at_risk(returns, level: float = 0.95) -> float | None:
    arr = clean_returns(returns)
    if arr.size == 0:
        return None
    q = np.quantile(arr, 1 - level)
    return float(max(0.0, -q))


def expected_shortfall(returns, level: float = 0.95) -> float | None:
    arr = clean_returns(returns)
    if arr.size == 0:
        return None
    q = np.quantile(arr, 1 - level)
    tail = arr[arr <= q]
    if tail.size == 0:
        return float(max(0.0, -q))
    return float(max(0.0, -np.mean(tail)))


def skewness(returns) -> float | None:
    arr = clean_returns(returns)
    if arr.size < 3:
        return None
    mean = np.mean(arr)
    std = np.std(arr, ddof=1)
    if std <= 0:
        return 0.0
    return float(np.mean(((arr - mean) / std) ** 3))


def kurtosis(returns) -> float | None:
    arr = clean_returns(returns)
    if arr.size < 4:
        return None
    mean = np.mean(arr)
    std = np.std(arr, ddof=1)
    if std <= 0:
        return 0.0
    return float(np.mean(((arr - mean) / std) ** 4))


def max_drawdown_from_returns(returns) -> float | None:
    arr = clean_returns(returns)
    if arr.size == 0:
        return None
    equity = np.cumprod(1 + np.clip(arr, -0.95, None))
    peak = np.maximum.accumulate(equity)
    drawdown = equity / peak - 1
    return float(np.min(drawdown))


def max_drawdown_from_paths(paths: np.ndarray) -> float | None:
    summary = drawdown_summary_from_paths(paths)
    return summary.get("mean_simulated_max_drawdown")


def drawdown_summary_from_paths(paths: np.ndarray | None) -> dict:
    if paths is None or paths.size == 0:
        return {
            "mean_simulated_max_drawdown": None,
            "expected_max_drawdown": None,
            "median_max_drawdown": None,
            "p95_max_drawdown": None,
            "worst_sample_drawdown": None,
            "drawdown_definition": "absent_pathwise_drawdown",
        }
    peak = np.maximum.accumulate(paths, axis=1)
    drawdown = paths / peak - 1
    per_path_max_drawdown = np.nanmin(drawdown, axis=1)
    per_path_max_drawdown = per_path_max_drawdown[np.isfinite(per_path_max_drawdown)]
    if per_path_max_drawdown.size == 0:
        return {
            "mean_simulated_max_drawdown": None,
            "expected_max_drawdown": None,
            "median_max_drawdown": None,
            "p95_max_drawdown": None,
            "worst_sample_drawdown": None,
            "drawdown_definition": "absent_pathwise_drawdown",
        }
    mean_drawdown = float(np.nanmean(per_path_max_drawdown))
    return {
        "mean_simulated_max_drawdown": mean_drawdown,
        "expected_max_drawdown": mean_drawdown,
        "median_max_drawdown": float(np.nanmedian(per_path_max_drawdown)),
        "p95_max_drawdown": float(np.nanquantile(per_path_max_drawdown, 0.05)),
        "worst_sample_drawdown": float(np.nanmin(per_path_max_drawdown)),
        "drawdown_definition": (
            "per-path peak-to-trough drawdown from simulated sample paths; values are negative returns. "
            "p95_max_drawdown is the 95% loss-side drawdown threshold, i.e. the 5th percentile of path drawdowns."
        ),
    }


def drawdown_summary_from_returns(returns) -> dict:
    fallback = max_drawdown_from_returns(returns)
    return {
        "mean_simulated_max_drawdown": fallback,
        "expected_max_drawdown": fallback,
        "median_max_drawdown": fallback,
        "p95_max_drawdown": fallback,
        "worst_sample_drawdown": fallback,
        "drawdown_definition": (
            "fallback drawdown computed on the sequence of simulated terminal returns because pathwise sample_paths "
            "were absent; use pathwise fields when available."
        ),
    }


def conditional_volatility(returns, lambda_: float = 0.94) -> float | None:
    arr = clean_returns(returns)
    if arr.size == 0:
        return None
    variance = np.var(arr[: min(30, len(arr))]) if len(arr) > 1 else arr[0] ** 2
    for value in arr:
        variance = lambda_ * variance + (1 - lambda_) * value**2
    return float(np.sqrt(max(variance, 0.0)) * np.sqrt(TRADING_DAYS))


def compute_risk_metrics(simulated_returns, historical_returns=None, sample_paths=None) -> dict:
    sim = clean_returns(simulated_returns)
    hist = clean_returns(historical_returns) if historical_returns is not None else sim
    drawdown_summary = (
        drawdown_summary_from_paths(sample_paths)
        if sample_paths is not None
        else drawdown_summary_from_returns(sim)
    )
    return {
        "var_95": value_at_risk(sim, 0.95),
        "var_99": value_at_risk(sim, 0.99),
        "cvar_95": expected_shortfall(sim, 0.95),
        "cvar_99": expected_shortfall(sim, 0.99),
        "skewness": skewness(sim),
        "kurtosis": kurtosis(sim),
        "max_drawdown": drawdown_summary.get("mean_simulated_max_drawdown"),
        **drawdown_summary,
        "conditional_volatility": conditional_volatility(hist),
    }


def rolling_drawdown(price_series: pd.Series) -> pd.Series:
    close = pd.to_numeric(price_series, errors="coerce")
    peak = close.cummax()
    return close / peak - 1
