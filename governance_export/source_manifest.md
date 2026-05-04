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
| Run ID | BTC_ensemble_20260504T122603Z_4f5be51e | inferred |
| Report timestamp | 2026-05-04T12:26:03.918344+00:00 | inferred |
| Asset | BTC | real |
| Horizon | 365 days | inferred |
| Simulations | 5000 | inferred |
| Model | ensemble | inferred |
| Market source | bitget_btcusdt_spot_candles; live runs also append bitget_btcusdt_spot_ticker_realtime | real |
| Fundamental source | no_fundamental_source | absent |
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
| latest_report.md | 2026-05-04T12:26:03.918344+00:00 | BTC_ensemble_20260504T122603Z_4f5be51e | $78,952.42 | prices real; simulations inferred; fundamentals absent |

Live Action provenance requirements:

- Operation: `runQuantBtcModel`.
- Required source fields: `model_run_id`, `report_date`, `reference_spot`, `reference_spot_timestamp`, `reference_spot_source`.
- Expected market source for realtime price: `bitget_btcusdt_spot_ticker_realtime`.
- Expected status mix unless extra data are supplied: prices real; simulations inferred; fundamentals absent.

## Known Coherence Note

Latest regime probabilities:

- Bull: 54.54%.
- Bear: 19.22%.
- Range: 13.16%.
- Sum: 86.92%.
- Residual: 13.08% non-classified / transition.

The regime split is incomplete and must not be presented as a complete 100% partition unless the residual is included.
