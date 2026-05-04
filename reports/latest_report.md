# Quant BTC Model - Latest Report

Generated: 2026-05-04T10:51:58.807012+00:00
Run ID: `BTC_ensemble_20260504T105158Z_29a31e6a`
Asset: BTC
Horizon: 30 days
Simulations: 1000
Model: ensemble
Data status: real

This report is probabilistic infrastructure output, not a deterministic forecast and not financial advice.

## Provenance des chiffres

- Report source: reports/latest_report.md
- Report date: 2026-05-04T10:51:58.807012+00:00
- Model run ID: `BTC_ensemble_20260504T105158Z_29a31e6a`
- Model version: source-code snapshot in `quant_btc_model/src`
- Reference spot price: $78,564.16
- Market prices status: real
- Simulation outputs status: inferred
- Risk metrics status: inferred
- Fundamental variables status: absent
- Rule: no precise quantitative figure should be reused without this source, report date, run ID, reference spot, and status context.

## Donnees utilisees

- Market rows: 1090
- Latest spot used: $78,564.16
- Market sources: bitget_btcusdt_spot_candles
- Fundamental rows: 1090
- Technical feature rows: 1090
- Corpus documents copied: 0
- Corpus chunks: 0
- Corpus claims: 0

## Donnees manquantes

- fundamental_features.etf_flows: NULL, warning logged
- fundamental_features.funding_rate: NULL, warning logged
- fundamental_features.open_interest: NULL, warning logged
- fundamental_features.liquidations: NULL, warning logged
- fundamental_features.hash_rate: NULL, warning logged
- fundamental_features.exchange_reserves: NULL, warning logged
- fundamental_features.stablecoins_supply: NULL, warning logged
- fundamental_features.dxy: NULL, warning logged
- fundamental_features.us_rates: NULL, warning logged
- fundamental_features.nasdaq: NULL, warning logged

## Hypotheses

- All outputs are distributions, probabilities, or risk measures.
- MOCK data are explicitly tagged when real market data cannot be loaded.
- Fundamental fields remain NULL unless supplied through CSV files in `data/raw`.
- Historical stationarity is a working assumption and can fail during structural regime changes.
- Stress tests are scenario shocks, not predictions.

## Resultats par modele

- monte_carlo: 14.29%
- student_t: 14.29%
- jump_diffusion: 14.29%
- garch: 14.29%
- regime_switching: 14.29%
- liquidation: 14.29%
- correlation: 14.29%

## Distribution horizon 30 jours

- P10 return: -13.66%
- Median return: 1.83%
- P90 return: 20.32%
- P10 price: $67,832.42
- Median price: $80,005.75
- P90 price: $94,527.17

## Probabilites seuils

- P(return > 0): 54.60%
- P(return <= -10%): 16.50%
- P(return <= -30%): 0.60%
- P(return >= +30%): 5.00%

## Repartition des regimes

- Bull: 10.30%
- Bear: 3.60%
- Range: 56.90%
- Non classe / transition: 29.20%
- Controle de coherence: The bull/bear/range probabilities sum to 70.80%, leaving 29.20% as non-classified / transition. Do not present the bull/bear/range split as complete.

## VaR / CVaR

- VaR 95 du rendement simule, exprimee comme perte positive: 17.28%
- VaR 99 du rendement simule, exprimee comme perte positive: 27.58%
- CVaR 95 du rendement simule, exprimee comme perte moyenne de queue positive: 23.49%
- CVaR 99 du rendement simule, exprimee comme perte moyenne de queue positive: 31.69%
- Interpretation VaR 95: under model assumptions, the worst 5% simulated scenarios begin around this loss threshold or worse.
- Interpretation CVaR 95: this estimates the average loss inside scenarios worse than VaR 95.
- Skewness: 0.81
- Kurtosis: 4.81
- Expected max drawdown: -11.93%
- Conditional volatility: 35.00%

## Stress tests

| Scenario | Instant shock | Shocked spot | Shocked median terminal |
|---|---:|---:|---:|
| crash_-30pct | -30.00% | $54,994.91 | $56,004.02 |
| crash_-50pct | -50.00% | $39,282.08 | $40,002.87 |
| etf_outflow_massif | -18.00% | $64,422.61 | $65,604.71 |
| hausse_dxy | -8.00% | $72,279.03 | $73,605.29 |
| hausse_taux_us | -10.00% | $70,707.74 | $72,005.17 |
| chute_nasdaq | -12.00% | $69,136.46 | $70,405.06 |
| cascade_liquidations | -28.00% | $56,566.20 | $57,604.14 |

## Position sizing

- Risk budget: 2.00%
- VaR based fraction: 11.57%
- CVaR based fraction: 8.52%
- Kelly fraction: 24.08%
- Drawdown limited fraction: 8.52%

## Confidence score

- Score: 71/100
- Components: {'data_quality': 70.0, 'model_stability': 76.49, 'backtest': 63.64, 'uncertainty': 79.61}
- Notes: Most fundamental features are NULL.

## Backtest

| Horizon | Hit rate | Brier | Calibration error | MAE | Interval coverage | Obs |
|---:|---:|---:|---:|---:|---:|---:|
| 30 | 48.99% | 0.28 | 0.11 | 10.83% | 78.96% | 694 |
| 90 | 53.47% | 0.32 | 0.26 | 26.43% | 64.35% | 634 |
| 365 | 55.15% | 0.36 | 0.38 | 105.69% | 59.89% | 359 |

## Limites explicites

- The model never emits certainty.
- Results depend on input data quality and may be MOCK if no real data source is available.
- Every precise quantitative figure must be traceable to an export file, report, run ID, connected database, or explicit user-provided result.
- If confidence score is below 50/100, any directional conclusion must be described as weak or fragile.
- Structural breaks, exchange outages, regulatory events, and liquidity gaps can invalidate historical calibration.
- NULL fundamental fields reduce confidence and should be replaced with audited data sources before production capital use.
