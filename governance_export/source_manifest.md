# Source Manifest

## Purpose

This manifest describes the Knowledge export sources without including raw SQLite or massive data dumps.

## Export Folder

Path:

```text
quant_btc_model/governance_export/
```

Files included:

- gpt_instructions.md
- governance_rules.md
- model_card.md
- data_dictionary.md
- claims_registry.md
- source_manifest.md
- output_policy.md
- latest_report.md
- dashboard_summary.md

## Excluded From GPT Knowledge Export

- SQLite database: data/quant_model.db.
- Full raw market price tables.
- Full raw feature tables.
- Full simulation arrays.
- Full raw copied corpus files.
- Node/package lock files and dependency dumps.

These exclusions are intentional to keep GPT Custom Knowledge focused and lightweight.

## Latest Model Run Source

| Item | Value | Status |
|---|---|---|
| Run ID | BTC_ensemble_20260504T201559Z_4bf56cd8 | inferred |
| Report timestamp | 2026-05-04T20:16:00.068494+00:00 | inferred |
| Asset | BTC | real |
| Horizon | 7 days | inferred |
| Simulations | 100 | inferred |
| Model | ensemble | inferred |
| Market source | bitget_btcusdt_spot_candles; live runs also append bitget_btcusdt_spot_ticker_realtime | real |
| Fundamental source | farside_bitcoin_etf_flow_total_usd_m; bitget_current_fund_rate; bitget_open_interest; blockchain_info_hash_rate_chart; defillama_stablecoins_total_pegged_usd; stooq_dx_f_quote; fred_dgs10_10y_treasury_rate or treasury_daily_10y_yield_curve; stooq_ndx_quote; other fields absent | partial_real_absent |
| Confidence score | 76/100 | inferred |

## Corpus Pipeline Source Summary

| Item | Count / Value |
|---|---:|
| Copied documents | 100 |
| Chunks | 168 |
| Claims | 61 |
| Reliability default | unknown |
| Originals modified | false |

## Primary Corpus Sources Used For Governance Tone

Compact representative sources:

- BASE_DE_CONNAISSANCE/PRODUCTIZATION_DECISION.md
- BASE_DE_CONNAISSANCE/README.md
- BASE_DE_CONNAISSANCE/corpus_layers.json
- MDL Ynor/README.md
- MDL Ynor/corpus_layers.json

The raw manifest contains more copied files, including dependency metadata. For GPT Knowledge, those extra files should not be treated as financial or model evidence.

## Provenance Rules

- Numeric model outputs come from latest_report.md.
- Fresh numeric model outputs from the GPT Action must come from `runQuantBtcModel`, not `latestQuantBtcReport`.
- High-level dashboard labels come from dashboard_summary.md.
- Data field meanings come from data_dictionary.md.
- Behavioral constraints come from gpt_instructions.md, governance_rules.md, and output_policy.md.
- Corpus-derived claims come from claims_registry.md and must retain their reliability label.

## Required Numeric Citation

Every precise number shown by a GPT Custom answer must include:

- source file;
- report date;
- report date in UTC and Europe/Paris if a timestamp is shown;
- model_run_id;
- archive_id when present;
- BTC reference spot when relevant;
- reference spot timestamp in UTC and Europe/Paris when present;
- status: real, mock, absent, or inferred;
- whether the figure is present in export or recalculated.

Latest numeric provenance:

| Source file | Report date | Run ID | Reference spot | Status mix |
|---|---|---|---:|---|
| latest_report.md | 2026-05-04T20:16:00.068494+00:00 | BTC_ensemble_20260504T201559Z_4bf56cd8 | $80,118.03 | prices real; simulations inferred; fundamentals partial_real_absent |

Live Action provenance requirements:

- Operation: `runQuantBtcModel`.
- Multi-frame operation: `runQuantBtcMultiFrame`.
- Required source fields: full `model_run_id`, `report_date_utc`, `report_date_paris`, `reference_spot`, `reference_spot_timestamp_utc`, `reference_spot_timestamp_paris`, `reference_spot_source`.
- Required run consistency fields: one `archive.archive_id` and one shared spot snapshot per analysis when present.
- Fundamental provenance field: `fundamental_inputs` with `real_fields`, `absent_fields`, `sources`, `timestamp`, `status`, and compact point-in-time values.
- Expected market source for realtime price: `bitget_btcusdt_spot_ticker_realtime`.
- Expected status mix unless extra data are supplied: prices real; simulations inferred; fundamentals partial_real_absent or absent.
- Default live frames: 7, 30, 90, 180 and 365 days.
- Multi-frame runs expose `shared_spot_snapshot` so all frames can be compared from one reference price.
- Multi-frame answers must not combine two different `archive_id` values or two different shared spot snapshots unless explicitly framed as a comparison.
- Version fields may include `api_version`, `model_version`, `schema_version` and `git_commit`.
- Short cached responses may include a `cache` object with `created_at_utc`, `created_at_paris`, `expires_at_utc`, `expires_at_paris`, and `ttl_seconds`.

No-sleep Cloudflare Worker requirements:

- Endpoint: `https://quant-btc-model-lite.mdl-bitcoin-analyst.workers.dev`.
- Schema file: `gpt_action_openapi.cloudflare.deployed.yaml`.
- Runtime: Cloudflare Worker bridge to the Render Bitget-backed Python engine.
- Source policy: Bitget required, no non-Bitget exchange fallback for live model conclusions.
- Operations: `health`, `getQuantBtcLiteVersion`, `getQuantBtcLiteStatus`, `auditQuantBtcLiteSystem`, `runQuantBtcModel`, `runQuantBtcMultiFrame`, `getQuantBtcRunHistory`, `compareQuantBtcRuns`, `getQuantBtcAlerts`, `getQuantBtcBacktestSummary`, `latestQuantBtcReport`.
- Default fresh analysis route: `auditQuantBtcLiteSystem` then `runQuantBtcMultiFrame` with 7, 30, 90, 180 and 365 day horizons.
- Audit output is preflight governance only; do not treat it as a forecast.
- Required bridge fields when present: `cloudflare_bridge.mode`, `cloudflare_bridge.source_policy`, `cloudflare_bridge.render_api_base`.
- Primary market source remains Bitget through Render. If the bridge fails, live output is absent.
- Fundamental fields follow the Render response: ETF flows, funding rate, open interest, hash rate, exchange reserves, stablecoin supply, DXY, US rates and Nasdaq may be real when reachable. Liquidations are real only when the Bitget public WebSocket emits a BTCUSDT push during the configured observation window; otherwise they are absent.
- Fresh run responses may include an `archive` object with `archive_id`, SQLite table and runtime JSON/Markdown paths.
- Fresh run responses may include freshness gates, alerts, Monte Carlo error margins, multi-seed stability, expanded drawdown fields, liquidity, options, ETF trend and explainability diagnostics.
- GitHub Actions external archive may store compact live-run summaries under `external_archive/live_runs/`; these are audit snapshots, not raw simulation dumps.
- GitHub Actions monitor opens or updates a visible `[quant-btc-monitor-alert]` issue if live quality checks fail, then closes it on recovery.
- Public rate limit is best-effort per IP / Worker isolate. A 429 response means no live model output was produced.

## Known Coherence Note

Latest regime probabilities:

- Bull: 2.00%.
- Bear: 0.00%.
- Range: 85.00%.
- Sum: 87.00%.
- Residual: 13.00% non-classified / transition.

The regime split is incomplete and must not be presented as a complete 100% partition unless the residual is included.
