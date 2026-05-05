from __future__ import annotations

import numpy as np

import correlation_model
import garch_model
import jump_diffusion
import liquidation_model
import monte_carlo
import regime_switching
import student_t_model
from simulation_utils import seed_for


MODEL_REGISTRY = {
    "monte_carlo": monte_carlo.simulate,
    "student_t": student_t_model.simulate,
    "jump_diffusion": jump_diffusion.simulate,
    "garch": garch_model.simulate,
    "regime_switching": regime_switching.simulate,
    "liquidation": liquidation_model.simulate,
    "correlation": correlation_model.simulate,
}


def weights_from_backtests(model_names: list[str], backtest_rows: list[dict] | None = None) -> dict[str, float]:
    if not backtest_rows:
        equal = 1.0 / len(model_names)
        return {name: equal for name in model_names}

    raw_scores = {name: 1.0 for name in model_names}
    for row in backtest_rows:
        name = row.get("model")
        if name not in raw_scores:
            continue
        brier = row.get("brier_score")
        calibration = row.get("calibration_error")
        hit_rate = row.get("hit_rate")
        score = 1.0
        if brier is not None:
            score *= 1.0 / max(float(brier), 1e-4)
        if calibration is not None:
            score *= 1.0 / max(float(calibration), 0.03)
        if hit_rate is not None:
            score *= max(float(hit_rate), 0.05)
        raw_scores[name] = max(raw_scores[name], score)
    total = sum(raw_scores.values())
    if total <= 0:
        equal = 1.0 / len(model_names)
        return {name: equal for name in model_names}
    return {name: float(score / total) for name, score in raw_scores.items()}


def simulate(
    returns,
    spot: float,
    horizon: int,
    simulations: int,
    seed: int = 42,
    fundamentals=None,
    backtest_rows: list[dict] | None = None,
) -> dict:
    model_names = list(MODEL_REGISTRY.keys())
    weights = weights_from_backtests(model_names, backtest_rows=backtest_rows)
    sims_per_model = max(200, int(np.ceil(simulations / len(model_names))))
    component_results = {}
    for name in model_names:
        func = MODEL_REGISTRY[name]
        kwargs = {
            "returns": returns,
            "spot": spot,
            "horizon": horizon,
            "simulations": sims_per_model,
            "seed": seed_for(name, seed),
        }
        if name == "correlation":
            kwargs["fundamentals"] = fundamentals
        component_results[name] = func(**kwargs)

    rng = np.random.default_rng(seed_for("ensemble_resample", seed))
    names = np.array(model_names)
    p = np.array([weights[name] for name in model_names], dtype=float)
    p = p / p.sum()
    chosen = rng.choice(names, size=simulations, p=p)
    terminal_prices = np.empty(simulations)
    for name in model_names:
        mask = chosen == name
        if not mask.any():
            continue
        source = component_results[name]["terminal_prices"]
        terminal_prices[mask] = rng.choice(source, size=int(mask.sum()), replace=True)

    sample_paths = []
    for name in model_names:
        paths = component_results[name].get("sample_paths")
        if paths is not None and paths.size:
            take = max(1, int(round(weights[name] * 800)))
            take = min(take, paths.shape[0])
            sample_paths.append(paths[:take])
    paths = np.vstack(sample_paths) if sample_paths else np.empty((0, 0))
    return {
        "model": "ensemble",
        "terminal_prices": terminal_prices,
        "terminal_returns": terminal_prices / spot - 1,
        "sample_paths": paths,
        "weights": weights,
        "component_results": component_results,
        "parameters": {
            "weighting": "performance_error_calibration",
            "sims_per_component": sims_per_model,
            "weights": weights,
        },
    }
