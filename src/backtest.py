from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _normal_forecast(window_returns: np.ndarray, horizon: int) -> dict[str, float]:
    mu = float(np.mean(window_returns))
    sigma = float(max(np.std(window_returns, ddof=1), 1e-8))
    horizon_mu = mu * horizon
    horizon_sigma = sigma * np.sqrt(horizon)
    z0 = (0 - horizon_mu) / horizon_sigma
    prob_up = 0.5 * (1 - math.erf(z0 / np.sqrt(2)))
    return {
        "prob_up": float(prob_up),
        "median": float(np.expm1(horizon_mu)),
        "p10": float(np.expm1(horizon_mu - 1.28155 * horizon_sigma)),
        "p90": float(np.expm1(horizon_mu + 1.28155 * horizon_sigma)),
        "var95_return_threshold": float(np.expm1(horizon_mu - 1.64485 * horizon_sigma)),
        "var99_return_threshold": float(np.expm1(horizon_mu - 2.32635 * horizon_sigma)),
    }


def run_backtest(price_frame: pd.DataFrame, asset: str, model: str, horizons=(30, 90, 365), train_window: int = 365) -> list[dict]:
    frame = price_frame.sort_values("timestamp").copy()
    close = pd.to_numeric(frame["close"], errors="coerce").reset_index(drop=True)
    returns = close.pct_change().dropna().reset_index(drop=True)
    status = "mock" if price_frame["statut"].eq("mock").any() else "real"
    results = []
    for horizon in horizons:
        probs = []
        events = []
        hits = []
        absolute_errors = []
        covered = []
        p10_p90_covered = []
        var95_breaches = []
        var99_breaches = []
        actual_returns = []
        median_forecasts = []
        max_i = len(returns) - horizon
        if max_i <= train_window:
            results.append(
                {
                    "asset": asset.upper(),
                    "horizon_days": horizon,
                    "model": model,
                    "hit_rate": None,
                    "brier_score": None,
                    "calibration_error": None,
                    "mean_absolute_error": None,
                    "interval_coverage": None,
                    "p10_p90_coverage": None,
                    "var95_breach_rate": None,
                    "var99_breach_rate": None,
                    "expected_var95_breach_rate": 0.05,
                    "expected_var99_breach_rate": 0.01,
                    "random_walk_hit_rate": None,
                    "random_walk_brier_score": None,
                    "random_walk_mean_absolute_error": None,
                    "brier_skill_vs_random_walk": None,
                    "mae_skill_vs_random_walk": None,
                    "observations": 0,
                    "source": "walk_forward_backtest",
                    "statut": "missing",
                }
            )
            continue
        for i in range(train_window, max_i):
            window = returns.iloc[i - train_window : i].to_numpy()
            actual = float(close.iloc[i + horizon] / close.iloc[i] - 1)
            forecast = _normal_forecast(window, horizon)
            prob_up = forecast["prob_up"]
            median = forecast["median"]
            low = forecast["p10"]
            high = forecast["p90"]
            event = 1.0 if actual > 0 else 0.0
            probs.append(prob_up)
            events.append(event)
            hits.append(1.0 if (prob_up >= 0.5) == (actual > 0) else 0.0)
            absolute_errors.append(abs(median - actual))
            covered.append(1.0 if low <= actual <= high else 0.0)
            p10_p90_covered.append(1.0 if low <= actual <= high else 0.0)
            var95_breaches.append(1.0 if actual <= forecast["var95_return_threshold"] else 0.0)
            var99_breaches.append(1.0 if actual <= forecast["var99_return_threshold"] else 0.0)
            actual_returns.append(actual)
            median_forecasts.append(median)
        probs_arr = np.asarray(probs)
        events_arr = np.asarray(events)
        actual_arr = np.asarray(actual_returns, dtype=float)
        median_arr = np.asarray(median_forecasts, dtype=float)
        random_walk_probs = np.full_like(events_arr, 0.5, dtype=float)
        random_walk_median = np.zeros_like(actual_arr, dtype=float)
        brier = float(np.mean((probs_arr - events_arr) ** 2)) if len(probs_arr) else None
        rw_brier = float(np.mean((random_walk_probs - events_arr) ** 2)) if len(events_arr) else None
        mae = float(np.mean(absolute_errors)) if absolute_errors else None
        rw_mae = float(np.mean(np.abs(random_walk_median - actual_arr))) if len(actual_arr) else None
        hit_rate = float(np.mean(hits)) if hits else None
        rw_hit_rate = float(np.mean((random_walk_probs >= 0.5) == (events_arr > 0))) if len(events_arr) else None
        results.append(
            {
                "asset": asset.upper(),
                "horizon_days": horizon,
                "model": model,
                "hit_rate": hit_rate,
                "brier_score": brier,
                "calibration_error": float(abs(np.mean(probs_arr) - np.mean(events_arr))) if len(probs_arr) else None,
                "mean_absolute_error": mae,
                "interval_coverage": float(np.mean(covered)) if covered else None,
                "p10_p90_coverage": float(np.mean(p10_p90_covered)) if p10_p90_covered else None,
                "var95_breach_rate": float(np.mean(var95_breaches)) if var95_breaches else None,
                "var99_breach_rate": float(np.mean(var99_breaches)) if var99_breaches else None,
                "expected_var95_breach_rate": 0.05,
                "expected_var99_breach_rate": 0.01,
                "random_walk_hit_rate": rw_hit_rate,
                "random_walk_brier_score": rw_brier,
                "random_walk_mean_absolute_error": rw_mae,
                "brier_skill_vs_random_walk": (rw_brier - brier) if rw_brier is not None and brier is not None else None,
                "mae_skill_vs_random_walk": (rw_mae - mae) if rw_mae is not None and mae is not None else None,
                "calibration_bins": calibration_bins(probs_arr, events_arr),
                "observations": int(len(probs)),
                "source": "walk_forward_backtest",
                "statut": status,
            }
        )
    return results


def calibration_bins(probs: np.ndarray, events: np.ndarray, bins: int = 5) -> list[dict]:
    if len(probs) == 0 or len(events) == 0:
        return []
    edges = np.linspace(0.0, 1.0, bins + 1)
    rows = []
    for index in range(bins):
        low = edges[index]
        high = edges[index + 1]
        if index == bins - 1:
            mask = (probs >= low) & (probs <= high)
        else:
            mask = (probs >= low) & (probs < high)
        if not np.any(mask):
            rows.append(
                {
                    "bin_low": float(low),
                    "bin_high": float(high),
                    "count": 0,
                    "mean_probability": None,
                    "realized_frequency": None,
                }
            )
            continue
        rows.append(
            {
                "bin_low": float(low),
                "bin_high": float(high),
                "count": int(np.sum(mask)),
                "mean_probability": float(np.mean(probs[mask])),
                "realized_frequency": float(np.mean(events[mask])),
            }
        )
    return rows
