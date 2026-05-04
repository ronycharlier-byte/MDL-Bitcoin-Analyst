# Quant BTC Model - Latest Report

Generated: 2026-05-04T10:39:31.659477+00:00
Run ID: `BTC_ensemble_20260504T103929Z_724e8807`
Asset: BTC
Horizon: 365 days
Simulations: 200000
Model: ensemble
Data status: real

This report is probabilistic infrastructure output, not a deterministic forecast and not financial advice.

## Provenance des chiffres

- Report source: reports/latest_report.md
- Report date: 2026-05-04T10:39:31.659477+00:00
- Model run ID: `BTC_ensemble_20260504T103929Z_724e8807`
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
- Corpus documents copied: 100
- Corpus chunks: 165
- Corpus claims: 39

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

- P10 return: -32.33%
- Median return: 27.41%
- P90 return: 147.87%
- P10 price: $53,165.70
- Median price: $100,096.79
- P90 price: $194,734.85

## Probabilites seuils

- P(return > 0): 68.47%
- P(return <= -10%): 24.39%
- P(return <= -30%): 11.33%
- P(return >= +30%): 48.34%

## Repartition des regimes

- Bull: 54.75%
- Bear: 17.59%
- Range: 14.15%
- Non classe / transition: 13.50%
- Controle de coherence: The bull/bear/range probabilities sum to 86.50%, leaving 13.50% as non-classified / transition. Do not present the bull/bear/range split as complete.

## VaR / CVaR

- VaR 95 du rendement simule, exprimee comme perte positive: 43.11%
- VaR 99 du rendement simule, exprimee comme perte positive: 59.89%
- CVaR 95 du rendement simule, exprimee comme perte moyenne de queue positive: 53.28%
- CVaR 99 du rendement simule, exprimee comme perte moyenne de queue positive: 66.03%
- Interpretation VaR 95: under model assumptions, the worst 5% simulated scenarios begin around this loss threshold or worse.
- Interpretation CVaR 95: this estimates the average loss inside scenarios worse than VaR 95.
- Skewness: 2.08
- Kurtosis: 12.04
- Expected max drawdown: -36.10%
- Conditional volatility: 35.00%

## Stress tests

| Scenario | Instant shock | Shocked spot | Shocked median terminal |
|---|---:|---:|---:|
| crash_-30pct | -30.00% | $54,994.91 | $70,067.75 |
| crash_-50pct | -50.00% | $39,282.08 | $50,048.39 |
| etf_outflow_massif | -18.00% | $64,422.61 | $82,079.37 |
| hausse_dxy | -8.00% | $72,279.03 | $92,089.04 |
| hausse_taux_us | -10.00% | $70,707.74 | $90,087.11 |
| chute_nasdaq | -12.00% | $69,136.46 | $88,085.17 |
| cascade_liquidations | -28.00% | $56,566.20 | $72,069.69 |

## Position sizing

- Risk budget: 2.00%
- VaR based fraction: 4.64%
- CVaR based fraction: 3.75%
- Kelly fraction: 25.00%
- Drawdown limited fraction: 2.08%

## Confidence score

- Score: 42/100
- Components: {'data_quality': 70.0, 'model_stability': 0.26, 'backtest': 63.64, 'uncertainty': 10.0}
- Notes: Most fundamental features are NULL.; Wide P10-P90 interval.; High tail loss estimate.; Distribution uncertainty is high.

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
