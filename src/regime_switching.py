from __future__ import annotations

import numpy as np

from simulation_utils import build_sample_paths_from_daily_returns, cap_simulations, clean_returns, estimate_return_params, sample_path_count


def _regime_params(returns: np.ndarray) -> dict:
    if len(returns) < 120:
        return {
            "calm_mu": 0.0004,
            "calm_sigma": 0.025,
            "stress_mu": -0.0006,
            "stress_sigma": 0.060,
            "p_calm_to_stress": 0.035,
            "p_stress_to_calm": 0.090,
        }
    rolling_vol = np.array([np.std(returns[max(0, i - 30) : i + 1]) for i in range(len(returns))])
    threshold = np.nanmedian(rolling_vol)
    calm = returns[rolling_vol <= threshold]
    stress = returns[rolling_vol > threshold]
    fallback = estimate_return_params(returns)
    return {
        "calm_mu": float(np.mean(calm)) if len(calm) else fallback["mu"],
        "calm_sigma": float(max(np.std(calm, ddof=1), 0.01)) if len(calm) > 1 else fallback["sigma"],
        "stress_mu": float(np.mean(stress)) if len(stress) else fallback["mu"] - 0.001,
        "stress_sigma": float(max(np.std(stress, ddof=1), fallback["sigma"] * 1.5, 0.02)),
        "p_calm_to_stress": 0.035,
        "p_stress_to_calm": 0.090,
    }


def _simulate_daily(params: dict, n: int, horizon: int, rng: np.random.Generator) -> np.ndarray:
    daily = np.zeros((n, horizon))
    regime = rng.choice([0, 1], size=n, p=[0.75, 0.25])
    for day in range(horizon):
        calm = regime == 0
        stress = ~calm
        daily[calm, day] = rng.normal(params["calm_mu"], params["calm_sigma"], size=int(calm.sum()))
        daily[stress, day] = rng.normal(params["stress_mu"], params["stress_sigma"], size=int(stress.sum()))
        u = rng.random(n)
        regime = np.where((regime == 0) & (u < params["p_calm_to_stress"]), 1, regime)
        regime = np.where((regime == 1) & (u < params["p_stress_to_calm"]), 0, regime)
    return daily


def simulate(returns, spot: float, horizon: int, simulations: int, seed: int = 42) -> dict:
    simulations = cap_simulations(simulations)
    rng = np.random.default_rng(seed)
    params = _regime_params(clean_returns(returns))
    terminal_log = np.zeros(simulations)
    regime = rng.choice([0, 1], size=simulations, p=[0.75, 0.25])
    for _ in range(horizon):
        daily = np.empty(simulations)
        calm = regime == 0
        stress = ~calm
        daily[calm] = rng.normal(params["calm_mu"], params["calm_sigma"], size=int(calm.sum()))
        daily[stress] = rng.normal(params["stress_mu"], params["stress_sigma"], size=int(stress.sum()))
        terminal_log += np.log1p(np.clip(daily, -0.95, None))
        u = rng.random(simulations)
        regime = np.where((regime == 0) & (u < params["p_calm_to_stress"]), 1, regime)
        regime = np.where((regime == 1) & (u < params["p_stress_to_calm"]), 0, regime)
    terminal_prices = spot * np.exp(terminal_log)

    n_paths = sample_path_count(simulations)
    daily_paths = _simulate_daily(params, n_paths, horizon, rng)
    sample_paths = build_sample_paths_from_daily_returns(daily_paths, spot, max_paths=n_paths)
    return {
        "model": "regime_switching",
        "terminal_prices": terminal_prices,
        "terminal_returns": terminal_prices / spot - 1,
        "sample_paths": sample_paths,
        "parameters": params,
    }
