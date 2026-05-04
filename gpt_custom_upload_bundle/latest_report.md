# Quant BTC Model - Latest Report

Generated: 2026-05-04T20:16:00.068494+00:00
Run ID: `BTC_ensemble_20260504T201559Z_4bf56cd8`
Asset: BTC
Horizon: 7 days
Simulations: 100
Model: ensemble
Data status: real

This report is probabilistic infrastructure output, not a deterministic forecast and not financial advice.

## Provenance des chiffres

- Report source: reports/latest_report.md
- Report date: 2026-05-04T20:16:00.068494+00:00
- Model run ID: `BTC_ensemble_20260504T201559Z_4bf56cd8`
- Model version: source-code snapshot in `quant_btc_model/src`
- Code version / git commit: 97b9d841d535
- Reference spot price: $80,118.03
- Reference spot timestamp: 2026-05-04T20:15:57Z
- Reference spot source: bitget_btcusdt_spot_ticker_realtime
- Market prices status: real
- Simulation outputs status: inferred
- Risk metrics status: inferred
- Fundamental variables status: partial_real_absent
- Fundamental variables with real values: etf_flows, funding_rate, open_interest, hash_rate, stablecoins_supply, dxy, us_rates, nasdaq
- Rule: no precise quantitative figure should be reused without this source, report date, run ID, reference spot, and status context.

## Donnees utilisees

- Market rows: 1091
- Latest spot used: $80,118.03
- Latest spot timestamp: 2026-05-04T20:15:57Z
- Market sources: bitget_btcusdt_spot_candles, bitget_btcusdt_spot_ticker_realtime
- Fundamental rows: 1091
- Technical feature rows: 1091
- Corpus documents copied: 0
- Corpus chunks: 0
- Corpus claims: 0

## Donnees manquantes

- fundamental_features.liquidations: NULL, warning logged
- fundamental_features.exchange_reserves: NULL, warning logged

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

## Distribution horizon 7 jours

- P10 return: -6.64%
- Median return: 0.59%
- P90 return: 10.29%
- P10 price: $74,799.27
- Median price: $80,587.40
- P90 price: $88,362.58

## Probabilites seuils

- P(return > 0): 54.00%
- P(return <= -10%): 3.00%
- P(return <= -30%): 0.00%
- P(return >= +30%): 1.00%

## Repartition des regimes

- Bull: 2.00%
- Bear: 0.00%
- Range: 85.00%
- Non classe / transition: 13.00%
- Controle de coherence: The bull/bear/range probabilities sum to 87.00%, leaving 13.00% as non-classified / transition. Do not present the bull/bear/range split as complete.

## VaR / CVaR

- VaR 95 du rendement simule, exprimee comme perte positive: 8.44%
- VaR 99 du rendement simule, exprimee comme perte positive: 11.60%
- CVaR 95 du rendement simule, exprimee comme perte moyenne de queue positive: 10.91%
- CVaR 99 du rendement simule, exprimee comme perte moyenne de queue positive: 14.49%
- Interpretation VaR 95: under model assumptions, the worst 5% simulated scenarios begin around this loss threshold or worse.
- Interpretation CVaR 95: this estimates the average loss inside scenarios worse than VaR 95.
- Skewness: 1.02
- Kurtosis: 5.73
- Expected max drawdown: -5.27%
- Conditional volatility: 35.18%

## Stress tests

| Scenario | Instant shock | Shocked spot | Shocked median terminal |
|---|---:|---:|---:|
| crash_-30pct | -30.00% | $56,082.62 | $56,411.18 |
| crash_-50pct | -50.00% | $40,059.01 | $40,293.70 |
| etf_outflow_massif | -18.00% | $65,696.78 | $66,081.67 |
| hausse_dxy | -8.00% | $73,708.59 | $74,140.41 |
| hausse_taux_us | -10.00% | $72,106.23 | $72,528.66 |
| chute_nasdaq | -12.00% | $70,503.87 | $70,916.91 |
| cascade_liquidations | -28.00% | $57,684.98 | $58,022.93 |

## Position sizing

- Risk budget: 2.00%
- VaR based fraction: 23.70%
- CVaR based fraction: 18.34%
- Kelly fraction: 24.32%
- Drawdown limited fraction: 18.34%

## Confidence score

- Score: 76/100
- Components: {'data_quality': 70.02, 'model_stability': 88.56, 'backtest': 63.6, 'uncertainty': 89.84}
- Notes: Most fundamental features are NULL.

## Backtest

| Horizon | Hit rate | Brier | Calibration error | MAE | Interval coverage | Obs |
|---:|---:|---:|---:|---:|---:|---:|
| 30 | 48.92% | 0.28 | 0.11 | 10.84% | 78.85% | 695 |
| 90 | 53.54% | 0.32 | 0.26 | 26.40% | 64.41% | 635 |
| 365 | 55.00% | 0.36 | 0.38 | 105.67% | 59.72% | 360 |

## Limites explicites

- The model never emits certainty.
- Results depend on input data quality and may be MOCK if no real data source is available.
- Every precise quantitative figure must be traceable to an export file, report, run ID, connected database, or explicit user-provided result.
- If confidence score is below 50/100, any directional conclusion must be described as weak or fragile.
- Structural breaks, exchange outages, regulatory events, and liquidity gaps can invalidate historical calibration.
- NULL fundamental fields reduce confidence and should be replaced with audited data sources before production capital use.
