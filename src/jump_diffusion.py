from __future__ import annotations

import numpy as np

from simulation_utils import build_sample_paths_from_daily_returns, cap_simulations, clean_returns, estimate_return_params, sample_path_count


def _jump_params(returns: np.ndarray, sigma: float) -> dict:
    if len(returns) < 60 or sigma <= 0:
        return {"lambda_daily": 0.015, "jump_mu": -0.03, "jump_sigma": 0.08}
    threshold = 2.5 * sigma
    jumps = returns[np.abs(returns - np.mean(returns)) > threshold]
    if len(jumps) < 5:
        return {"lambda_daily": 0.015, "jump_mu": -0.03, "jump_sigma": 0.08}
    return {
        "lambda_daily": float(np.clip(len(jumps) / len(returns), 0.001, 0.08)),
        "jump_mu": float(np.mean(jumps)),
        "jump_sigma": float(max(np.std(jumps, ddof=1), 0.02)),
    }


def simulate(returns, spot: float, horizon: int, simulations: int, seed: int = 42) -> dict:
    simulations = cap_simulations(simulations)
    rng = np.random.default_rng(seed)
    arr = clean_returns(returns)
    params = estimate_return_params(arr)
    jumps = _jump_params(arr, params["sigma"])
    terminal_log = np.zeros(simulations)
    for _ in range(horizon):
        diffusion = rng.normal(params["mu"], params["sigma"], size=simulations)
        jump_mask = rng.random(simulations) < jumps["lambda_daily"]
        jump = np.zeros(simulations)
        if jump_mask.any():
            jump[jump_mask] = rng.normal(jumps["jump_mu"], jumps["jump_sigma"], size=int(jump_mask.sum()))
        terminal_log += np.log1p(np.clip(diffusion + jump, -0.95, None))
    terminal_prices = spot * np.exp(terminal_log)

    n_paths = sample_path_count(simulations)
    daily_paths = rng.normal(params["mu"], params["sigma"], size=(n_paths, horizon))
    jump_mask = rng.random((n_paths, horizon)) < jumps["lambda_daily"]
    daily_paths += jump_mask * rng.normal(jumps["jump_mu"], jumps["jump_sigma"], size=(n_paths, horizon))
    sample_paths = build_sample_paths_from_daily_returns(daily_paths, spot, max_paths=n_paths)
    return {
        "model": "jump_diffusion",
        "terminal_prices": terminal_prices,
        "terminal_returns": terminal_prices / spot - 1,
        "sample_paths": sample_paths,
        "parameters": {**params, **jumps},
    }
