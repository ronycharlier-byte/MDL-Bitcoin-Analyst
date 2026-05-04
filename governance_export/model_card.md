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

## Latest Export Snapshot

- Generated report timestamp: 2026-05-04T12:26:03.918344+00:00.
- Run ID: BTC_ensemble_20260504T122603Z_4f5be51e.
- Asset: BTC.
- Horizon: 365 days.
- Simulations: 5000.
- Model: ensemble.
- Market data status: real.
- Market data source: Bitget BTCUSDT spot candles; live API runs also append the Bitget BTCUSDT spot ticker as the reference spot.
- Fundamental data status: absent for all required fundamental fields.
- Confidence score: 42/100.

## Numeric Provenance Requirement

Every precise figure from this model card must be cited with:

- source: model_card.md or latest_report.md;
- report timestamp: 2026-05-04T12:26:03.918344+00:00;
- run ID: BTC_ensemble_20260504T122603Z_4f5be51e;
- reference spot: $78,952.42 when price levels or returns are discussed;
- status: real for market source, absent for fundamentals, inferred for simulations/risk/backtests.

Do not reproduce precise figures from memory without provenance.

## Latest Distribution Snapshot

- P10 return: -34.44%.
- Median return: 27.13%.
- P90 return: 144.89%.
- P10 price: $51,762.17.
- Median price: $100,370.89.
- P90 price: $193,349.17.

These values are inferred from simulations and are not deterministic predictions.

## Latest Risk Snapshot

- VaR 95 of simulated return, expressed as positive loss: 45.70%.
- VaR 99 of simulated return, expressed as positive loss: 61.19%.
- CVaR 95, average tail loss beyond VaR 95: 55.15%.
- CVaR 99, average tail loss beyond VaR 99: 67.28%.
- Expected max drawdown: -36.10%.
- Conditional volatility: 35.00%.

## Latest Regime Split

- Bull: 54.54%.
- Bear: 19.22%.
- Range: 13.16%.
- Non-classified / transition: 13.08%.

Bull, bear, and range sum to 86.92%, not 100%. The split is incomplete and should be interpreted with caution.

## Confidence Interpretation

The confidence score is 42/100. This is low-to-moderate and constrained by:

- absent fundamental features;
- wide P10-P90 interval;
- high tail loss estimate;
- high distribution uncertainty.

Confidence is not a probability of being correct.

Any directional conclusion must be weak or fragile because the confidence score is below 50/100.

## Validation Snapshot

Backtest diagnostics from the latest report:

| Horizon | Hit rate | Brier | Calibration error | MAE | Interval coverage | Observations |
|---:|---:|---:|---:|---:|---:|---:|
| 30 | 48.99% | 0.28 | 0.11 | 10.83% | 78.96% | 694 |
| 90 | 53.47% | 0.32 | 0.26 | 26.43% | 64.35% | 634 |
| 365 | 55.15% | 0.36 | 0.38 | 105.69% | 59.89% | 359 |

Backtests are diagnostics, not proof of future performance.

## Key Limitations

- The future BTC distribution may differ materially from historical data.
- Fundamental data are absent in the latest export.
- Macro variables are not real inputs in the current latest report.
- Stress tests are hypothetical shocks.
- The model does not know future liquidity, regulation, ETF flows, or exchange behavior.
- The output must be interpreted as probabilistic scenario analysis only.
