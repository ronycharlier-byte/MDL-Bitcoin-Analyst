from __future__ import annotations

import numpy as np

from simulation_utils import build_sample_paths_from_daily_returns, cap_simulations, estimate_return_params, sample_path_count


def simulate(returns, spot: float, horizon: int, simulations: int, seed: int = 42) -> dict:
    simulations = cap_simulations(simulations)
    rng = np.random.default_rng(seed)
    params = estimate_return_params(returns)
    mu = params["mu"]
    sigma = params["sigma"]
    z = rng.normal(size=simulations)
    log_terminal = (mu - 0.5 * sigma**2) * horizon + sigma * np.sqrt(horizon) * z
    terminal_prices = spot * np.exp(log_terminal)

    n_paths = sample_path_count(simulations)
    daily = rng.normal(mu, sigma, size=(n_paths, horizon))
    sample_paths = build_sample_paths_from_daily_returns(daily, spot, max_paths=n_paths)
    return {
        "model": "monte_carlo",
        "terminal_prices": terminal_prices,
        "terminal_returns": terminal_prices / spot - 1,
        "sample_paths": sample_paths,
        "parameters": params,
    }
