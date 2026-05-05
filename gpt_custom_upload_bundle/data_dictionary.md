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
| report_date_utc | UTC report timestamp from the API/source. |
| report_date_paris | Europe/Paris conversion for user-facing display. |
| archive_id | Runtime archive ID when the Action response includes one. |
| model_run_id | Run ID if present. |
| reference_spot | BTC spot used for return-to-price conversion when relevant. |
| reference_spot_timestamp_utc | UTC timestamp of the spot reference when available. |
| reference_spot_timestamp_paris | Europe/Paris timestamp of the spot reference when available. |
| status | real, mock, absent, or inferred. |
| calculation_origin | present_in_export, recalculated, database_result, or user_supplied. |

If these provenance fields cannot be supplied, the GPT should not display the precise number.
Do not mix numeric outputs from different archive_id values or different reference spot timestamps in one analysis unless the user explicitly asks for a run comparison.

## Market Prices

Latest export status: real.

| Field | Meaning | Latest status |
|---|---|---|
| timestamp | Candle date/time. | real |
| timestamp_utc | UTC timestamp supplied or normalized by the API. | real when provided |
| timestamp_paris | Europe/Paris display timestamp derived from timestamp_utc. | inferred conversion |
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

Latest export status: partial_real_absent.

| Field | Meaning | Latest status |
|---|---|---|
| etf_flows | Latest published total Bitcoin ETF net flow in USD millions. | real in live API when Farside Investors provides it; absent otherwise |
| funding_rate | Perpetual futures funding rate. | real in live API when Bitget provides it; absent otherwise |
| open_interest | Derivatives open interest. | real in live API when Bitget provides it; absent otherwise |
| liquidations | BTCUSDT liquidation amount from Bitget UTA public liquidation WebSocket, unit quote coin/USDT. | real only if a live Bitget push is observed during the configured observation window; absent otherwise |
| hash_rate | Bitcoin network hash rate. | real in live API when Blockchain.com provides it; absent otherwise |
| exchange_reserves | Bitget Proof of Reserves BTC platform assets, unit BTC. | real in live API when Bitget Proof of Reserves provides it; absent otherwise |
| stablecoins_supply | Stablecoin supply/liquidity proxy. | real in live API when DeFiLlama provides it; absent otherwise |
| dxy | US Dollar Index. | real in live API when Stooq provides it; absent otherwise |
| us_rates | US 10Y Treasury rate proxy. | real in live API when FRED DGS10 or U.S. Treasury provides it; absent otherwise |
| nasdaq | Nasdaq or risk-asset proxy. | real in live API when Stooq provides it; absent otherwise |

GPT rule: do not invent or estimate absent fundamental fields unless clearly labelled as a hypothetical assumption. Treat partial online fundamentals as point-in-time snapshots, not complete historical series.

## Fundamental Display Requirements

When the GPT displays any precise fundamental value, it must include:

- unit;
- source;
- timestamp;
- status;
- whether the value is a point-in-time snapshot, historical series value, or aggregate.

Recommended unit wording:

| Field | Unit to display | Nature |
|---|---|---|
| etf_flows | USD millions | Dated flow series / aggregate window |
| funding_rate | Rate or percent, matching API convention | Point-in-time/current funding snapshot |
| open_interest | Unit returned by Bitget, plus source label | Point-in-time derivatives snapshot |
| liquidations | Quote coin/USDT amount when observed | Live observation window snapshot |
| hash_rate | Source-provided hash-rate unit | Historical network series value |
| exchange_reserves | BTC | Proof-of-reserves snapshot |
| stablecoins_supply | USD | Aggregate liquidity snapshot |
| dxy | Index points | Market series value |
| us_rates | Percent | Daily rate series value |
| nasdaq | Index points | Market series value |

If the unit is not explicit in the live response, state "unit: source convention" rather than inventing a conversion.

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
| mean_simulated_max_drawdown | Mean of per-path peak-to-trough simulated drawdowns. Preferred field for expected drawdown. |
| expected_max_drawdown | Alias of mean_simulated_max_drawdown. |
| median_max_drawdown | Median per-path simulated max drawdown. |
| p95_max_drawdown | 95% loss-side simulated drawdown threshold, stored as a negative return. |
| worst_sample_drawdown | Worst path drawdown observed in the simulated sample. Do not present as theoretical worst case. |
| drawdown_definition | Text definition of how drawdown was computed. |
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

## Live Quality Diagnostics

| Field | Meaning |
|---|---|
| freshness.spot | Spot freshness gate. If stale/absent, live analysis must stop. |
| freshness.fundamentals | Fundamental snapshot freshness. Stale/absent should be reported as a warning. |
| monte_carlo_error | Binomial sampling error and 95% margins for simulated probabilities. |
| multi_seed_stability | Dispersion of key metrics across multiple seeds. |
| alerts | Quality/risk warnings such as stale spot, VaR > 30%, confidence < 50, transition > 25%. |
| liquidity | Bitget order-book spread/depth/imbalance snapshot when reachable. |
| options | Options/implied volatility context when reachable; not a Bitget spot replacement. |
| etf_flow_trends | ETF 1d/7d/30d flow diagnostics when reachable. |
| explainability | Heuristic contribution summary; not causal proof. |

## Risk Metric Wording

VaR and CVaR in this export should be explained as simulated losses:

- VaR 95 of simulated return, expressed as a positive loss.
- CVaR 95 as average loss in scenarios worse than VaR 95.

If another convention uses negative returns, explicitly state that convention.

## Monte Carlo Error Wording

When `monte_carlo_error` is available, key displayed probabilities should include:

- estimate;
- 95% margin;
- sample size if useful;
- rare-tail warning if `tail_counts` is below 30.

Example:

```text
P(up) = 60.25% +/- 2.14 points, status inferred_sampling_error.
```

If a probability is shown without an available margin, write "Monte Carlo margin: absent".

## Backtest Caveat Wording

Backtest diagnostics must modify the conclusion when available. If observed VaR breaches are materially above expected breach levels, especially at 90/180/365 days, use:

```text
Long-horizon risk metrics are indicative and probably historically under-calibrated because observed VaR breaches exceed the expected breach rate.
```
