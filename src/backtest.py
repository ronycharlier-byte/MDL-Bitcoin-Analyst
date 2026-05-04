from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _normal_probability_positive(window_returns: np.ndarray, horizon: int) -> tuple[float, float, float, float]:
    mu = float(np.mean(window_returns))
    sigma = float(max(np.std(window_returns, ddof=1), 1e-8))
    horizon_mu = mu * horizon
    horizon_sigma = sigma * np.sqrt(horizon)
    z0 = (0 - horizon_mu) / horizon_sigma
    prob_up = 0.5 * (1 - math.erf(z0 / np.sqrt(2)))
    median = np.expm1(horizon_mu)
    low = np.expm1(horizon_mu - 1.28155 * horizon_sigma)
    high = np.expm1(horizon_mu + 1.28155 * horizon_sigma)
    return float(prob_up), float(median), float(low), float(high)


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
                    "observations": 0,
                    "source": "walk_forward_backtest",
                    "statut": "missing",
                }
            )
            continue
        for i in range(train_window, max_i):
            window = returns.iloc[i - train_window : i].to_numpy()
            actual = float(close.iloc[i + horizon] / close.iloc[i] - 1)
            prob_up, median, low, high = _normal_probability_positive(window, horizon)
            event = 1.0 if actual > 0 else 0.0
            probs.append(prob_up)
            events.append(event)
            hits.append(1.0 if (prob_up >= 0.5) == (actual > 0) else 0.0)
            absolute_errors.append(abs(median - actual))
            covered.append(1.0 if low <= actual <= high else 0.0)
        probs_arr = np.asarray(probs)
        events_arr = np.asarray(events)
        results.append(
            {
                "asset": asset.upper(),
                "horizon_days": horizon,
                "model": model,
                "hit_rate": float(np.mean(hits)) if hits else None,
                "brier_score": float(np.mean((probs_arr - events_arr) ** 2)) if len(probs_arr) else None,
                "calibration_error": float(abs(np.mean(probs_arr) - np.mean(events_arr))) if len(probs_arr) else None,
                "mean_absolute_error": float(np.mean(absolute_errors)) if absolute_errors else None,
                "interval_coverage": float(np.mean(covered)) if covered else None,
                "observations": int(len(probs)),
                "source": "walk_forward_backtest",
                "statut": status,
            }
        )
    return results
