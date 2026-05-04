# Quant BTC Model - Latest Report

Generated: 2026-05-04T12:45:43.086312+00:00
Run ID: `BTC_ensemble_20260504T124542Z_24e975ff`
Asset: BTC
Horizon: 365 days
Simulations: 5000
Model: ensemble
Data status: real

This report is probabilistic infrastructure output, not a deterministic forecast and not financial advice.

## Provenance des chiffres

- Report source: reports/latest_report.md
- Report date: 2026-05-04T12:45:43.086312+00:00
- Model run ID: `BTC_ensemble_20260504T124542Z_24e975ff`
- Model version: source-code snapshot in `quant_btc_model/src`
- Reference spot price: $78,955.53
- Reference spot timestamp: 2026-05-04T12:45:40Z
- Reference spot source: bitget_btcusdt_spot_ticker_realtime
- Market prices status: real
- Simulation outputs status: inferred
- Risk metrics status: inferred
- Fundamental variables status: absent
- Rule: no precise quantitative figure should be reused without this source, report date, run ID, reference spot, and status context.

## Donnees utilisees

- Market rows: 1091
- Latest spot used: $78,955.53
- Latest spot timestamp: 2026-05-04T12:45:40Z
- Market sources: bitget_btcusdt_spot_candles, bitget_btcusdt_spot_ticker_realtime
- Fundamental rows: 1091
- Technical feature rows: 1091
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

## Distribution horizon 365 jours

- P10 return: -33.00%
- Median return: 27.62%
- P90 return: 150.35%
- P10 price: $52,900.03
- Median price: $100,765.44
- P90 price: $197,665.19

## Probabilites seuils

- P(return > 0): 68.02%
- P(return <= -10%): 25.04%
- P(return <= -30%): 11.86%
- P(return >= +30%): 48.70%

## Repartition des regimes

- Bull: 54.48%
- Bear: 17.30%
- Range: 14.02%
- Non classe / transition: 14.20%
- Controle de coherence: The bull/bear/range probabilities sum to 85.80%, leaving 14.20% as non-classified / transition. Do not present the bull/bear/range split as complete.

## VaR / CVaR

- VaR 95 du rendement simule, exprimee comme perte positive: 44.83%
- VaR 99 du rendement simule, exprimee comme perte positive: 60.39%
- CVaR 95 du rendement simule, exprimee comme perte moyenne de queue positive: 53.63%
- CVaR 99 du rendement simule, exprimee comme perte moyenne de queue positive: 68.24%
- Interpretation VaR 95: under model assumptions, the worst 5% simulated scenarios begin around this loss threshold or worse.
- Interpretation CVaR 95: this estimates the average loss inside scenarios worse than VaR 95.
- Skewness: 2.55
- Kurtosis: 19.33
- Expected max drawdown: -36.17%
- Conditional volatility: 34.02%

## Stress tests

| Scenario | Instant shock | Shocked spot | Shocked median terminal |
|---|---:|---:|---:|
| crash_-30pct | -30.00% | $55,268.87 | $70,535.81 |
| crash_-50pct | -50.00% | $39,477.76 | $50,382.72 |
| etf_outflow_massif | -18.00% | $64,743.53 | $82,627.66 |
| hausse_dxy | -8.00% | $72,639.09 | $92,704.20 |
| hausse_taux_us | -10.00% | $71,059.98 | $90,688.89 |
| chute_nasdaq | -12.00% | $69,480.87 | $88,673.58 |
| cascade_liquidations | -28.00% | $56,847.98 | $72,551.11 |

## Position sizing

- Risk budget: 2.00%
- VaR based fraction: 4.46%
- CVaR based fraction: 3.73%
- Kelly fraction: 25.00%
- Drawdown limited fraction: 2.06%

## Confidence score

- Score: 42/100
- Components: {'data_quality': 70.0, 'model_stability': 0.0, 'backtest': 63.6, 'uncertainty': 10.0}
- Notes: Most fundamental features are NULL.; Wide P10-P90 interval.; High tail loss estimate.; Distribution uncertainty is high.

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
