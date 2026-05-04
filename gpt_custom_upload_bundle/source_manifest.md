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
| Run ID | BTC_ensemble_20260504T131721Z_26e52ae0 | inferred |
| Report timestamp | 2026-05-04T13:17:22.171207+00:00 | inferred |
| Asset | BTC | real |
| Horizon | 365 days | inferred |
| Simulations | 5000 | inferred |
| Model | ensemble | inferred |
| Market source | bitget_btcusdt_spot_candles; live runs also append bitget_btcusdt_spot_ticker_realtime | real |
| Fundamental source | bitget_current_fund_rate; bitget_open_interest; stooq_dx_f_quote; stooq_ndx_quote; other fields absent | partial_real_absent |
| Confidence score | 42/100 | inferred |

## Corpus Pipeline Source Summary

| Item | Count / Value |
|---|---:|
| Copied documents | 100 |
| Chunks | 165 |
| Claims | 39 |
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
- model_run_id;
- BTC reference spot when relevant;
- status: real, mock, absent, or inferred;
- whether the figure is present in export or recalculated.

Latest numeric provenance:

| Source file | Report date | Run ID | Reference spot | Status mix |
|---|---|---|---:|---|
| latest_report.md | 2026-05-04T13:17:22.171207+00:00 | BTC_ensemble_20260504T131721Z_26e52ae0 | $78,912.63 | prices real; simulations inferred; fundamentals partial_real_absent |

Live Action provenance requirements:

- Operation: `runQuantBtcModel`.
- Multi-frame operation: `runQuantBtcMultiFrame`.
- Required source fields: `model_run_id`, `report_date`, `reference_spot`, `reference_spot_timestamp`, `reference_spot_source`.
- Expected market source for realtime price: `bitget_btcusdt_spot_ticker_realtime`.
- Expected status mix unless extra data are supplied: prices real; simulations inferred; fundamentals partial_real_absent or absent.
- Default live frames: 7, 30, 90, 180 and 365 days.
- Multi-frame runs expose `shared_spot_snapshot` so all frames can be compared from one reference price.
- Version fields may include `api_version`, `model_version`, `schema_version` and `git_commit`.
- Short cached responses may include a `cache` object with `created_at`, `expires_at`, and `ttl_seconds`.

No-sleep Cloudflare Worker requirements:

- Endpoint: `https://quant-btc-model-lite.mdl-bitcoin-analyst.workers.dev`.
- Schema file: `gpt_action_openapi.cloudflare.deployed.yaml`.
- Runtime: Cloudflare Worker bridge to the Render Bitget-backed Python engine.
- Source policy: Bitget required, no non-Bitget exchange fallback for live model conclusions.
- Operations: `health`, `getQuantBtcLiteVersion`, `getQuantBtcLiteStatus`, `runQuantBtcModel`, `runQuantBtcMultiFrame`, `latestQuantBtcReport`.
- Default fresh analysis route: `getQuantBtcLiteStatus` then `runQuantBtcMultiFrame` with 7, 30, 90, 180 and 365 day horizons.
- Required bridge fields when present: `cloudflare_bridge.mode`, `cloudflare_bridge.source_policy`, `cloudflare_bridge.render_api_base`.
- Primary market source remains Bitget through Render. If the bridge fails, live output is absent.
- Fundamental fields follow the Render response: funding rate, open interest, DXY and Nasdaq may be real when reachable; ETF flows, liquidations, hash rate, exchange reserves, stablecoins supply and US rates are absent unless explicitly present.
- Public rate limit is best-effort per IP / Worker isolate. A 429 response means no live model output was produced.

## Known Coherence Note

Latest regime probabilities:

- Bull: 52.16%.
- Bear: 19.90%.
- Range: 14.26%.
- Sum: 86.32%.
- Residual: 13.68% non-classified / transition.

The regime split is incomplete and must not be presented as a complete 100% partition unless the residual is included.
