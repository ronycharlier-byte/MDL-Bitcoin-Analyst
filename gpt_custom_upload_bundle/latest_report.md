# Quant BTC Model - Latest Report

Generated: 2026-05-04T13:17:22.171207+00:00
Run ID: `BTC_ensemble_20260504T131721Z_26e52ae0`
Asset: BTC
Horizon: 365 days
Simulations: 5000
Model: ensemble
Data status: real

This report is probabilistic infrastructure output, not a deterministic forecast and not financial advice.

## Provenance des chiffres

- Report source: reports/latest_report.md
- Report date: 2026-05-04T13:17:22.171207+00:00
- Model run ID: `BTC_ensemble_20260504T131721Z_26e52ae0`
- Model version: source-code snapshot in `quant_btc_model/src`
- Code version / git commit: 16ab407b5622
- Reference spot price: $78,912.63
- Reference spot timestamp: 2026-05-04T13:17:18Z
- Reference spot source: bitget_btcusdt_spot_ticker_realtime
- Market prices status: real
- Simulation outputs status: inferred
- Risk metrics status: inferred
- Fundamental variables status: partial_real_absent
- Fundamental variables with real values: funding_rate, open_interest, dxy, nasdaq
- Rule: no precise quantitative figure should be reused without this source, report date, run ID, reference spot, and status context.

## Donnees utilisees

- Market rows: 1091
- Latest spot used: $78,912.63
- Latest spot timestamp: 2026-05-04T13:17:18Z
- Market sources: bitget_btcusdt_spot_candles, bitget_btcusdt_spot_ticker_realtime
- Fundamental rows: 1091
- Technical feature rows: 1091
- Corpus documents copied: 0
- Corpus chunks: 0
- Corpus claims: 0

## Donnees manquantes

- fundamental_features.etf_flows: NULL, warning logged
- fundamental_features.liquidations: NULL, warning logged
- fundamental_features.hash_rate: NULL, warning logged
- fundamental_features.exchange_reserves: NULL, warning logged
- fundamental_features.stablecoins_supply: NULL, warning logged
- fundamental_features.us_rates: NULL, warning logged

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

- P10 return: -34.49%
- Median return: 24.07%
- P90 return: 146.48%
- P10 price: $51,693.42
- Median price: $97,904.94
- P90 price: $194,501.05

## Probabilites seuils

- P(return > 0): 66.20%
- P(return <= -10%): 26.78%
- P(return <= -30%): 12.68%
- P(return >= +30%): 46.56%

## Repartition des regimes

- Bull: 52.16%
- Bear: 19.90%
- Range: 14.26%
- Non classe / transition: 13.68%
- Controle de coherence: The bull/bear/range probabilities sum to 86.32%, leaving 13.68% as non-classified / transition. Do not present the bull/bear/range split as complete.

## VaR / CVaR

- VaR 95 du rendement simule, exprimee comme perte positive: 44.62%
- VaR 99 du rendement simule, exprimee comme perte positive: 60.67%
- CVaR 95 du rendement simule, exprimee comme perte moyenne de queue positive: 54.48%
- CVaR 99 du rendement simule, exprimee comme perte moyenne de queue positive: 66.74%
- Interpretation VaR 95: under model assumptions, the worst 5% simulated scenarios begin around this loss threshold or worse.
- Interpretation CVaR 95: this estimates the average loss inside scenarios worse than VaR 95.
- Skewness: 2.64
- Kurtosis: 21.12
- Expected max drawdown: -37.31%
- Conditional volatility: 34.00%

## Stress tests

| Scenario | Instant shock | Shocked spot | Shocked median terminal |
|---|---:|---:|---:|
| crash_-30pct | -30.00% | $55,238.84 | $68,533.46 |
| crash_-50pct | -50.00% | $39,456.32 | $48,952.47 |
| etf_outflow_massif | -18.00% | $64,708.36 | $80,282.05 |
| hausse_dxy | -8.00% | $72,599.62 | $90,072.55 |
| hausse_taux_us | -10.00% | $71,021.37 | $88,114.45 |
| chute_nasdaq | -12.00% | $69,443.11 | $86,156.35 |
| cascade_liquidations | -28.00% | $56,817.09 | $70,491.56 |

## Position sizing

- Risk budget: 2.00%
- VaR based fraction: 4.48%
- CVaR based fraction: 3.67%
- Kelly fraction: 25.00%
- Drawdown limited fraction: 1.97%

## Confidence score

- Score: 42/100
- Components: {'data_quality': 70.01, 'model_stability': 0.0, 'backtest': 63.6, 'uncertainty': 10.0}
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
