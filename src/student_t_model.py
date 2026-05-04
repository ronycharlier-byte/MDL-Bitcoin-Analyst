from __future__ import annotations

import numpy as np

from simulation_utils import build_sample_paths_from_daily_returns, cap_simulations, clean_returns, estimate_return_params, sample_path_count


def _degrees_of_freedom(returns: np.ndarray) -> float:
    if len(returns) < 60:
        return 5.0
    centered = returns - np.mean(returns)
    variance = np.var(centered)
    if variance <= 0:
        return 8.0
    kurt = np.mean(centered**4) / (variance**2)
    if kurt <= 3.5:
        return 12.0
    return float(np.clip(6.0 / max(kurt - 3.0, 0.1) + 4.0, 3.0, 12.0))


def simulate(returns, spot: float, horizon: int, simulations: int, seed: int = 42) -> dict:
    simulations = cap_simulations(simulations)
    rng = np.random.default_rng(seed)
    arr = clean_returns(returns)
    params = estimate_return_params(arr)
    df = _degrees_of_freedom(arr)
    mu = params["mu"]
    sigma = params["sigma"]
    scale = sigma / np.sqrt(df / (df - 2)) if df > 2 else sigma
    terminal_log = np.zeros(simulations)
    for _ in range(horizon):
        daily = mu + scale * rng.standard_t(df, size=simulations)
        terminal_log += np.log1p(np.clip(daily, -0.95, None))
    terminal_prices = spot * np.exp(terminal_log)

    n_paths = sample_path_count(simulations)
    daily_paths = mu + scale * rng.standard_t(df, size=(n_paths, horizon))
    sample_paths = build_sample_paths_from_daily_returns(daily_paths, spot, max_paths=n_paths)
    params = {**params, "degrees_of_freedom": float(df)}
    return {
        "model": "student_t",
        "terminal_prices": terminal_prices,
        "terminal_returns": terminal_prices / spot - 1,
        "sample_paths": sample_paths,
        "parameters": params,
    }
