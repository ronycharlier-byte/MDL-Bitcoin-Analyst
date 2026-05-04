from __future__ import annotations

import numpy as np
import pandas as pd

from config import DEFAULT_SEED


def clean_returns(returns: pd.Series | np.ndarray) -> np.ndarray:
    arr = np.asarray(returns, dtype=float)
    arr = arr[np.isfinite(arr)]
    return arr


def estimate_return_params(returns: pd.Series | np.ndarray) -> dict:
    arr = clean_returns(returns)
    if len(arr) < 30:
        return {"mu": 0.0, "sigma": 0.04, "n": int(len(arr))}
    return {
        "mu": float(np.mean(arr)),
        "sigma": float(max(np.std(arr, ddof=1), 1e-6)),
        "n": int(len(arr)),
    }


def cap_simulations(simulations: int) -> int:
    return int(max(100, simulations))


def sample_path_count(simulations: int) -> int:
    return int(min(max(250, simulations // 20), 5000))


def build_sample_paths_from_daily_returns(
    daily_returns: np.ndarray,
    spot: float,
    max_paths: int = 5000,
) -> np.ndarray:
    if daily_returns.ndim != 2:
        raise ValueError("daily_returns must be 2D")
    count = min(max_paths, daily_returns.shape[0])
    log_paths = np.cumsum(np.log1p(np.clip(daily_returns[:count], -0.95, None)), axis=1)
    paths = spot * np.exp(log_paths)
    return np.column_stack([np.full(count, spot), paths])


def summarize_simulation(terminal_prices: np.ndarray, spot: float) -> dict:
    prices = np.asarray(terminal_prices, dtype=float)
    prices = prices[np.isfinite(prices)]
    if prices.size == 0 or not np.isfinite(spot) or spot <= 0:
        return {}
    returns = prices / spot - 1.0
    return {
        "p10_return": float(np.quantile(returns, 0.10)),
        "median_return": float(np.quantile(returns, 0.50)),
        "p90_return": float(np.quantile(returns, 0.90)),
        "p10_price": float(np.quantile(prices, 0.10)),
        "median_price": float(np.quantile(prices, 0.50)),
        "p90_price": float(np.quantile(prices, 0.90)),
        "prob_up": float(np.mean(returns > 0.0)),
        "prob_down_10": float(np.mean(returns <= -0.10)),
        "prob_down_30": float(np.mean(returns <= -0.30)),
        "prob_up_30": float(np.mean(returns >= 0.30)),
        "prob_bull": float(np.mean(returns >= 0.20)),
        "prob_bear": float(np.mean(returns <= -0.20)),
        "prob_range": float(np.mean((returns > -0.10) & (returns < 0.10))),
    }


def seed_for(name: str, base_seed: int = DEFAULT_SEED) -> int:
    return abs(hash((name, base_seed))) % (2**32 - 1)
