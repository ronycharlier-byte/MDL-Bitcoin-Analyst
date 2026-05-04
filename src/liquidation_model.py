from __future__ import annotations

import numpy as np

from simulation_utils import build_sample_paths_from_daily_returns, cap_simulations, clean_returns, estimate_return_params, sample_path_count


def simulate(returns, spot: float, horizon: int, simulations: int, seed: int = 42) -> dict:
    simulations = cap_simulations(simulations)
    rng = np.random.default_rng(seed)
    arr = clean_returns(returns)
    params = estimate_return_params(arr)
    negative_tail = arr[arr < np.quantile(arr, 0.05)] if len(arr) >= 60 else np.array([-0.08])
    cascade_probability = float(np.clip(len(negative_tail) / max(len(arr), 1) * 0.35, 0.002, 0.035))
    cascade_mu = float(min(np.mean(negative_tail), -0.05))
    cascade_sigma = float(max(np.std(negative_tail), 0.035))

    terminal_log = np.zeros(simulations)
    for _ in range(horizon):
        base = rng.normal(params["mu"], params["sigma"], size=simulations)
        cascade = rng.random(simulations) < cascade_probability
        liquidation_shock = np.zeros(simulations)
        if cascade.any():
            liquidation_shock[cascade] = rng.normal(cascade_mu, cascade_sigma, size=int(cascade.sum()))
        daily = base + liquidation_shock
        terminal_log += np.log1p(np.clip(daily, -0.95, None))
    terminal_prices = spot * np.exp(terminal_log)

    n_paths = sample_path_count(simulations)
    daily_paths = rng.normal(params["mu"], params["sigma"], size=(n_paths, horizon))
    cascade_paths = rng.random((n_paths, horizon)) < cascade_probability
    daily_paths += cascade_paths * rng.normal(cascade_mu, cascade_sigma, size=(n_paths, horizon))
    sample_paths = build_sample_paths_from_daily_returns(daily_paths, spot, max_paths=n_paths)
    return {
        "model": "liquidation",
        "terminal_prices": terminal_prices,
        "terminal_returns": terminal_prices / spot - 1,
        "sample_paths": sample_paths,
        "parameters": {
            **params,
            "cascade_probability_daily": cascade_probability,
            "cascade_mu": cascade_mu,
            "cascade_sigma": cascade_sigma,
        },
    }
