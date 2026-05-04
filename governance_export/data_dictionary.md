# Data Dictionary

## Status Vocabulary

| Status | Meaning | GPT Handling |
|---|---|---|
| real | Observed or loaded from an identified source. | Can cite as available data. |
| mock | Synthetic fallback generated when real data are unavailable. | Must label as MOCK and never treat as real. |
| absent | Required input unavailable, NULL, or not exported. | Must say absent and avoid invention. |
| inferred | Derived from calculations, simulations, stress assumptions, or model logic. | Must label as model-implied or inferred. |

## Numeric Provenance Fields

For every precise quantitative output, the GPT must identify:

| Field | Meaning |
|---|---|
| source_file | Export file or report containing the number. |
| report_date | Date/time of the report used. |
| model_run_id | Run ID if present. |
| reference_spot | BTC spot used for return-to-price conversion when relevant. |
| status | real, mock, absent, or inferred. |
| calculation_origin | present_in_export, recalculated, database_result, or user_supplied. |

If these provenance fields cannot be supplied, the GPT should not display the precise number.

## Market Prices

Latest export status: real.

| Field | Meaning | Latest status |
|---|---|---|
| timestamp | Candle date/time. | real |
| asset | Asset symbol. | real |
| open | Daily open price. | real |
| high | Daily high price. | real |
| low | Daily low price. | real |
| close | Daily close price. | real |
| volume | Daily traded volume from the source. | real |
| source | Data source identifier. | real |
| statut | real, mock, or missing in SQLite; exported here as status vocabulary. | real |

Latest stored market source: bitget_btcusdt_spot_candles.
Live API runs append source: bitget_btcusdt_spot_ticker_realtime.

## Technical Features

Latest export status: inferred from market prices.

| Field | Meaning |
|---|---|
| return_1d | One-day return. |
| return_7d | Seven-day return. |
| return_30d | Thirty-day return. |
| return_90d | Ninety-day return. |
| return_365d | Three-hundred-sixty-five-day return. |
| rsi_14 | Fourteen-period RSI. |
| macd | MACD line. |
| macd_signal | MACD signal line. |
| realized_vol_30d | Annualized 30-day realized volatility. |
| realized_vol_90d | Annualized 90-day realized volatility. |
| drawdown | Current drawdown from rolling all-time high. |
| distance_ath | Distance from rolling all-time high. |

## Fundamental Features

Latest export status: absent.

| Field | Meaning | Latest status |
|---|---|---|
| etf_flows | ETF net flows. | absent |
| funding_rate | Perpetual futures funding rate. | absent |
| open_interest | Derivatives open interest. | absent |
| liquidations | Liquidation volume. | absent |
| hash_rate | Bitcoin network hash rate. | absent |
| exchange_reserves | BTC reserves held on exchanges. | absent |
| stablecoins_supply | Stablecoin supply/liquidity proxy. | absent |
| dxy | US Dollar Index. | absent |
| us_rates | US rates proxy. | absent |
| nasdaq | Nasdaq or risk-asset proxy. | absent |

GPT rule: do not invent or estimate absent fundamental fields unless clearly labelled as a hypothetical assumption.

## Risk Metrics

Latest status: inferred from simulations and historical returns.

| Field | Meaning |
|---|---|
| var_95 | Simulated loss threshold at 95% confidence. |
| var_99 | Simulated loss threshold at 99% confidence. |
| cvar_95 | Average simulated tail loss beyond VaR 95. |
| cvar_99 | Average simulated tail loss beyond VaR 99. |
| skewness | Distribution asymmetry. |
| kurtosis | Tail thickness indicator. |
| max_drawdown | Expected path drawdown from simulated paths. |
| conditional_volatility | EWMA-like annualized conditional volatility. |

## Simulation Outputs

Latest status: inferred.

| Field | Meaning |
|---|---|
| p10_return | 10th percentile simulated return. |
| median_return | Median simulated return. |
| p90_return | 90th percentile simulated return. |
| p10_price | 10th percentile simulated terminal price. |
| median_price | Median simulated terminal price. |
| p90_price | 90th percentile simulated terminal price. |
| prob_up | Probability of return greater than zero. |
| prob_down_10 | Probability of return less than or equal to -10%. |
| prob_down_30 | Probability of return less than or equal to -30%. |
| prob_up_30 | Probability of return greater than or equal to +30%. |
| prob_bull | Probability of bull scenario. |
| prob_bear | Probability of bear scenario. |
| prob_range | Probability of range scenario. |

Regime probabilities require a completeness check:

```text
non_classified_or_transition = 100% - (prob_bull + prob_bear + prob_range)
```

If the residual is materially different from zero, display it and state that the regime split is incomplete.

## Backtest Outputs

Latest status: inferred from historical market data.

| Field | Meaning |
|---|---|
| hit_rate | Directional hit rate. |
| brier_score | Probability forecast error score. Lower is better. |
| calibration_error | Absolute calibration gap. Lower is better. |
| mean_absolute_error | Absolute return error. |
| interval_coverage | Fraction of realized outcomes inside model interval. |
| observations | Number of out-of-sample observations. |

## Risk Metric Wording

VaR and CVaR in this export should be explained as simulated losses:

- VaR 95 of simulated return, expressed as a positive loss.
- CVaR 95 as average loss in scenarios worse than VaR 95.

If another convention uses negative returns, explicitly state that convention.
