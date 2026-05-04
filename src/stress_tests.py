from __future__ import annotations

import numpy as np


SCENARIOS = {
    "crash_-30pct": {"shock": -0.30, "description": "Instantaneous BTC crash"},
    "crash_-50pct": {"shock": -0.50, "description": "Severe BTC crash"},
    "etf_outflow_massif": {"shock": -0.18, "description": "Large ETF outflow shock"},
    "hausse_dxy": {"shock": -0.08, "description": "Stronger DXY liquidity pressure"},
    "hausse_taux_us": {"shock": -0.10, "description": "US rate repricing"},
    "chute_nasdaq": {"shock": -0.12, "description": "Risk asset correlation shock"},
    "cascade_liquidations": {"shock": -0.28, "description": "Leveraged liquidation cascade"},
}


def run_stress_tests(spot: float, terminal_prices, sample_paths=None) -> list[dict]:
    prices = np.asarray(terminal_prices, dtype=float)
    prices = prices[np.isfinite(prices)]
    base_median = float(np.median(prices)) if prices.size else spot
    results = []
    for name, scenario in SCENARIOS.items():
        shocked_spot = spot * (1 + scenario["shock"])
        shocked_terminal = base_median * (1 + scenario["shock"])
        results.append(
            {
                "scenario": name,
                "description": scenario["description"],
                "instant_return": scenario["shock"],
                "price_after_instant_shock": float(shocked_spot),
                "median_terminal_after_shock": float(max(shocked_terminal, 0.0)),
                "statut": "modelled_stress",
            }
        )
    return results
