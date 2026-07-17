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


def _cap_and_normalize_weights(raw: dict[str, float], cap: float = 0.35) -> dict[str, float]:
    if not raw:
        return {}
    cap = max(float(cap), 1.0 / len(raw))
    positive = {name: max(float(value), 0.0) for name, value in raw.items()}
    total = sum(positive.values())
    if total <= 0:
        return {name: 1.0 / len(positive) for name in positive}
    remaining = dict(positive)
    weights: dict[str, float] = {}
    remaining_mass = 1.0
    while remaining:
        remaining_total = sum(remaining.values())
        divisor = remaining_total if remaining_total > 0 else float(len(remaining))
        proposed = {
            name: remaining_mass * (value / divisor if remaining_total > 0 else 1.0 / divisor)
            for name, value in remaining.items()
        }
        oversized = {name for name, value in proposed.items() if value > cap}
        if not oversized:
            weights.update(proposed)
            break
        for name in oversized:
            weights[name] = cap
            remaining.pop(name)
        remaining_mass = max(0.0, 1.0 - sum(weights.values()))
    return {name: float(weights[name]) for name in raw}


def weight_diagnostics(model_names: list[str], backtest_rows: list[dict] | None = None) -> dict:
    if not model_names:
        return {
            "weights": {},
            "reason": "no_models_registered",
            "components": {},
            "maximum_weight": None,
            "weight_cap": None,
        }
    if not backtest_rows:
        equal = 1.0 / len(model_names)
        return {
            "weights": {name: equal for name in model_names},
            "reason": "equal_weights_no_out_of_sample_diagnostics",
            "components": {name: {"status": "absent"} for name in model_names},
            "maximum_weight": equal,
        }

    components: dict[str, dict] = {}
    raw_scores: dict[str, float] = {}
    for name in model_names:
        rows = [row for row in backtest_rows if row.get("model") == name and int(row.get("observations") or 0) > 0]
        if not rows:
            components[name] = {"status": "absent"}
            raw_scores[name] = 0.25
            continue
        brier_values = [float(row["brier_score"]) for row in rows if row.get("brier_score") is not None]
        calibration_values = [
            float(row["calibration_error"]) for row in rows if row.get("calibration_error") is not None
        ]
        coverage_values = [float(row["p10_p90_coverage"]) for row in rows if row.get("p10_p90_coverage") is not None]
        brier = float(np.mean(brier_values)) if brier_values else 0.5
        calibration = float(np.mean(calibration_values)) if calibration_values else 1.0
        coverage = float(np.mean(coverage_values)) if coverage_values else 0.0
        brier_quality = float(np.clip(1.0 - brier / 0.5, 0.0, 1.0))
        calibration_quality = float(np.clip(1.0 - calibration, 0.0, 1.0))
        coverage_quality = float(np.clip(1.0 - abs(coverage - 0.80) / 0.80, 0.0, 1.0))
        score = 0.45 * brier_quality + 0.35 * calibration_quality + 0.20 * coverage_quality
        raw_scores[name] = max(score, 0.05)
        components[name] = {
            "status": "inferred",
            "observations": int(sum(int(row.get("observations") or 0) for row in rows)),
            "brier_score_mean": brier,
            "calibration_error_mean": calibration,
            "p10_p90_coverage_mean": coverage,
            "quality_score": score,
        }
    equal = 1.0 / len(model_names)
    raw_total = sum(raw_scores.values()) or 1.0
    blended = {name: 0.80 * raw_scores[name] / raw_total + 0.20 * equal for name in model_names}
    weights = _cap_and_normalize_weights(blended)
    return {
        "weights": weights,
        "reason": "walk_forward_brier_calibration_coverage_with_equal_weight_shrinkage",
        "components": components,
        "maximum_weight": max(weights.values()),
        "weight_cap": max(0.35, equal),
    }


def weights_from_backtests(model_names: list[str], backtest_rows: list[dict] | None = None) -> dict[str, float]:
    return weight_diagnostics(model_names, backtest_rows)["weights"]


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
    diagnostics = weight_diagnostics(model_names, backtest_rows=backtest_rows)
    weights = diagnostics["weights"]
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
            "weighting": diagnostics["reason"],
            "sims_per_component": sims_per_model,
            "weights": weights,
            "weight_diagnostics": diagnostics,
        },
    }
