# Quant BTC Model - Latest Report

Generated: 2026-05-04T19:45:12.996236+00:00
Run ID: `BTC_ensemble_20260504T194512Z_1a995520`
Asset: BTC
Horizon: 30 days
Simulations: 2000
Model: ensemble
Data status: real

This report is probabilistic infrastructure output, not a deterministic forecast and not financial advice.

## Provenance des chiffres

- Report source: reports/latest_report.md
- Report date: 2026-05-04T19:45:12.996236+00:00
- Model run ID: `BTC_ensemble_20260504T194512Z_1a995520`
- Model version: source-code snapshot in `quant_btc_model/src`
- Code version / git commit: 25fcf9e9483f
- Reference spot price: $79,970.88
- Reference spot timestamp: 2026-05-04T19:45:10Z
- Reference spot source: bitget_btcusdt_spot_ticker_realtime
- Market prices status: real
- Simulation outputs status: inferred
- Risk metrics status: inferred
- Fundamental variables status: partial_real_absent
- Fundamental variables with real values: funding_rate, open_interest, hash_rate, stablecoins_supply, dxy, us_rates, nasdaq
- Rule: no precise quantitative figure should be reused without this source, report date, run ID, reference spot, and status context.

## Donnees utilisees

- Market rows: 1091
- Latest spot used: $79,970.88
- Latest spot timestamp: 2026-05-04T19:45:10Z
- Market sources: bitget_btcusdt_spot_candles, bitget_btcusdt_spot_ticker_realtime
- Fundamental rows: 1091
- Technical feature rows: 1091
- Corpus documents copied: 100
- Corpus chunks: 168
- Corpus claims: 61

## Donnees manquantes

- fundamental_features.etf_flows: NULL, warning logged
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

## Distribution horizon 30 jours

- P10 return: -14.35%
- Median return: 1.55%
- P90 return: 20.93%
- P10 price: $68,493.40
- Median price: $81,208.07
- P90 price: $96,710.18

## Probabilites seuils

- P(return > 0): 55.00%
- P(return <= -10%): 17.90%
- P(return <= -30%): 0.35%
- P(return >= +30%): 4.60%

## Repartition des regimes

- Bull: 11.05%
- Bear: 3.75%
- Range: 54.75%
- Non classe / transition: 30.45%
- Controle de coherence: The bull/bear/range probabilities sum to 69.55%, leaving 30.45% as non-classified / transition. Do not present the bull/bear/range split as complete.

## VaR / CVaR

- VaR 95 du rendement simule, exprimee comme perte positive: 18.78%
- VaR 99 du rendement simule, exprimee comme perte positive: 26.16%
- CVaR 95 du rendement simule, exprimee comme perte moyenne de queue positive: 23.31%
- CVaR 99 du rendement simule, exprimee comme perte moyenne de queue positive: 30.03%
- Interpretation VaR 95: under model assumptions, the worst 5% simulated scenarios begin around this loss threshold or worse.
- Interpretation CVaR 95: this estimates the average loss inside scenarios worse than VaR 95.
- Skewness: 0.70
- Kurtosis: 4.25
- Expected max drawdown: -12.21%
- Conditional volatility: 34.96%

## Stress tests

| Scenario | Instant shock | Shocked spot | Shocked median terminal |
|---|---:|---:|---:|
| crash_-30pct | -30.00% | $55,979.62 | $56,845.65 |
| crash_-50pct | -50.00% | $39,985.44 | $40,604.03 |
| etf_outflow_massif | -18.00% | $65,576.12 | $66,590.61 |
| hausse_dxy | -8.00% | $73,573.21 | $74,711.42 |
| hausse_taux_us | -10.00% | $71,973.79 | $73,087.26 |
| chute_nasdaq | -12.00% | $70,374.37 | $71,463.10 |
| cascade_liquidations | -28.00% | $57,579.03 | $58,469.81 |

## Position sizing

- Risk budget: 2.00%
- VaR based fraction: 10.65%
- CVaR based fraction: 8.58%
- Kelly fraction: 24.15%
- Drawdown limited fraction: 8.58%

## Confidence score

- Score: 71/100
- Components: {'data_quality': 70.02, 'model_stability': 75.96, 'backtest': 63.6, 'uncertainty': 78.83}
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
