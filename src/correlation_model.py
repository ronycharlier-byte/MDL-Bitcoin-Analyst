from __future__ import annotations

import numpy as np
import pandas as pd

from simulation_utils import build_sample_paths_from_daily_returns, cap_simulations, clean_returns, estimate_return_params, sample_path_count


def _macro_signal(fundamentals: pd.DataFrame | None) -> dict:
    if fundamentals is None or fundamentals.empty:
        return {"macro_drift_adjustment": 0.0, "macro_risk_multiplier": 1.0, "available_macro_fields": 0}
    available = 0
    adjustment = 0.0
    multiplier = 1.0
    latest = fundamentals.tail(1).to_dict("records")[0]
    for field in ["dxy", "us_rates", "nasdaq"]:
        value = latest.get(field)
        if value is not None and np.isfinite(value):
            available += 1
    if available:
        if np.isfinite(latest.get("dxy", np.nan)):
            adjustment -= 0.0001
            multiplier += 0.05
        if np.isfinite(latest.get("us_rates", np.nan)):
            adjustment -= 0.0001
            multiplier += 0.05
        if np.isfinite(latest.get("nasdaq", np.nan)):
            adjustment += 0.0001
    return {
        "macro_drift_adjustment": adjustment,
        "macro_risk_multiplier": multiplier,
        "available_macro_fields": available,
    }


def simulate(returns, spot: float, horizon: int, simulations: int, seed: int = 42, fundamentals=None) -> dict:
    simulations = cap_simulations(simulations)
    rng = np.random.default_rng(seed)
    arr = clean_returns(returns)
    params = estimate_return_params(arr)
    macro = _macro_signal(fundamentals)
    mu = params["mu"] + macro["macro_drift_adjustment"]
    sigma = params["sigma"] * macro["macro_risk_multiplier"]
    rho = 0.35

    terminal_log = np.zeros(simulations)
    for _ in range(horizon):
        market_shock = rng.normal(size=simulations)
        idiosyncratic = rng.normal(size=simulations)
        combined = rho * market_shock + np.sqrt(1 - rho**2) * idiosyncratic
        daily = mu + sigma * combined
        terminal_log += np.log1p(np.clip(daily, -0.95, None))
    terminal_prices = spot * np.exp(terminal_log)

    n_paths = sample_path_count(simulations)
    market_shock = rng.normal(size=(n_paths, horizon))
    idiosyncratic = rng.normal(size=(n_paths, horizon))
    daily_paths = mu + sigma * (rho * market_shock + np.sqrt(1 - rho**2) * idiosyncratic)
    sample_paths = build_sample_paths_from_daily_returns(daily_paths, spot, max_paths=n_paths)
    return {
        "model": "correlation",
        "terminal_prices": terminal_prices,
        "terminal_returns": terminal_prices / spot - 1,
        "sample_paths": sample_paths,
        "parameters": {**params, **macro, "assumed_macro_correlation": rho},
    }
