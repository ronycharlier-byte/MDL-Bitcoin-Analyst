# Model Card - Quant BTC Model

## Name

Quant BTC Model

## Purpose

Probabilistic quantitative infrastructure for Bitcoin scenario analysis, risk estimation, stress testing, and report generation.

## Intended Use

- Summarize model-implied BTC distributions.
- Explain risk metrics such as VaR, CVaR, drawdown, skewness, kurtosis, and conditional volatility.
- Compare bull, bear, and range scenario probabilities.
- Explain model assumptions and limitations.
- Support governance, research, and decision review.
- Check live data freshness, Monte Carlo uncertainty, multi-seed stability, archived run comparisons, alerts and baseline backtests when available.

## Not Intended For

- Deterministic price prediction.
- Automated trading without additional controls.
- Financial advice.
- Certainty claims.
- Capital allocation without independent validation.

## Implemented Model Families

- Monte Carlo lognormal simulation.
- Student-t heavy-tail simulation.
- Jump diffusion model.
- GARCH-like conditional volatility model.
- Calm/stress regime switching model.
- Liquidation cascade model.
- Macro correlation model.
- Dynamic ensemble model.

## Live Diagnostics Added

- Data freshness gate: stale or absent Bitget spot blocks live quantitative analysis.
- Expanded drawdown metrics: mean/expected, median, P95 loss-side threshold and worst sample drawdown.
- Monte Carlo error margins for simulated probabilities.
- Multi-seed stability diagnostics.
- Run comparison endpoint for latest vs previous archives.
- Alerts for VaR, confidence, transition regime and stale data.
- Optional context: Bitget liquidity, options/implied volatility, ETF flow trends and heuristic explainability.

## Latest Export Snapshot

- Generated report timestamp: 2026-05-04T20:16:00.068494+00:00.
- Run ID: BTC_ensemble_20260504T201559Z_4bf56cd8.
- Asset: BTC.
- Horizon: 7 days.
- Simulations: 100.
- Model: ensemble.
- Market data status: real.
- Market data source: Bitget BTCUSDT spot candles; live API runs also append the Bitget BTCUSDT spot ticker as the reference spot.
- Fundamental data status: partial; live API runs may include real point-in-time ETF flows, funding rate, open interest, hash rate, stablecoin supply, DXY, US rates and Nasdaq when sources respond.
- Confidence score: 76/100.

## Numeric Provenance Requirement

Every precise figure from this model card must be cited with:

- source: model_card.md or latest_report.md;
- report timestamp: 2026-05-04T20:16:00.068494+00:00;
- run ID: BTC_ensemble_20260504T201559Z_4bf56cd8;
- reference spot: $80,118.03 when price levels or returns are discussed;
- status: real for market source and any returned live fundamentals, absent for missing fundamentals, inferred for simulations/risk/backtests.

Do not reproduce precise figures from memory without provenance.

## Latest Distribution Snapshot

- P10 return: -6.64%.
- Median return: 0.59%.
- P90 return: 10.29%.
- P10 price: $74,799.27.
- Median price: $80,587.40.
- P90 price: $88,362.58.

These values are inferred from simulations and are not deterministic predictions.

## Latest Risk Snapshot

- VaR 95 of simulated return, expressed as positive loss: 8.44%.
- VaR 99 of simulated return, expressed as positive loss: 11.60%.
- CVaR 95, average tail loss beyond VaR 95: 10.91%.
- CVaR 99, average tail loss beyond VaR 99: 14.49%.
- Expected max drawdown: -5.27%.
- Conditional volatility: 35.18%.

## Latest Regime Split

- Bull: 2.00%.
- Bear: 0.00%.
- Range: 85.00%.
- Non-classified / transition: 13.00%.

Bull, bear, and range sum to 87.00%, not 100%. The split is incomplete and should be interpreted with caution.

## Confidence Interpretation

The confidence score is 76/100. This is moderate and constrained by:

- partial or absent fundamental features;
- wide P10-P90 interval;
- high tail loss estimate;
- high distribution uncertainty.

Confidence is not a probability of being correct.

Any directional conclusion must remain probabilistic and tied to the 7-day horizon.

## Validation Snapshot

Backtest diagnostics from the latest report:

| Horizon | Hit rate | Brier | Calibration error | MAE | Interval coverage | Observations |
|---:|---:|---:|---:|---:|---:|---:|
| 30 | 48.92% | 0.28 | 0.11 | 10.84% | 78.85% | 695 |
| 90 | 53.54% | 0.32 | 0.26 | 26.40% | 64.41% | 635 |
| 365 | 55.00% | 0.36 | 0.38 | 105.67% | 59.72% | 360 |

Backtests are diagnostics, not proof of future performance.

## Key Limitations

- The future BTC distribution may differ materially from historical data.
- Fundamental data coverage is partial and may be absent for several required fields.
- Macro variables are point-in-time inputs only when explicitly returned by the live API.
- Stress tests are hypothetical shocks.
- The model does not know future liquidity, regulation, ETF flows, or exchange behavior.
- The output must be interpreted as probabilistic scenario analysis only.
