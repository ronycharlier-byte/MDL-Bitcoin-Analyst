from __future__ import annotations

import numpy as np

from simulation_utils import build_sample_paths_from_daily_returns, cap_simulations, clean_returns, estimate_return_params, sample_path_count


def simulate(returns, spot: float, horizon: int, simulations: int, seed: int = 42) -> dict:
    simulations = cap_simulations(simulations)
    rng = np.random.default_rng(seed)
    arr = clean_returns(returns)
    params = estimate_return_params(arr)
    mu = params["mu"]
    unconditional_var = params["sigma"] ** 2
    alpha = 0.08
    beta = 0.90
    omega = max(unconditional_var * (1 - alpha - beta), 1e-10)

    variance = np.full(simulations, unconditional_var)
    terminal_log = np.zeros(simulations)
    for _ in range(horizon):
        shock = rng.normal(size=simulations)
        daily = mu + np.sqrt(np.maximum(variance, 1e-10)) * shock
        terminal_log += np.log1p(np.clip(daily, -0.95, None))
        variance = omega + alpha * (daily - mu) ** 2 + beta * variance
    terminal_prices = spot * np.exp(terminal_log)

    n_paths = sample_path_count(simulations)
    path_variance = np.full(n_paths, unconditional_var)
    daily_paths = np.zeros((n_paths, horizon))
    for day in range(horizon):
        shock = rng.normal(size=n_paths)
        daily = mu + np.sqrt(np.maximum(path_variance, 1e-10)) * shock
        daily_paths[:, day] = daily
        path_variance = omega + alpha * (daily - mu) ** 2 + beta * path_variance
    sample_paths = build_sample_paths_from_daily_returns(daily_paths, spot, max_paths=n_paths)
    return {
        "model": "garch",
        "terminal_prices": terminal_prices,
        "terminal_returns": terminal_prices / spot - 1,
        "sample_paths": sample_paths,
        "parameters": {**params, "alpha": alpha, "beta": beta, "omega": omega},
    }
