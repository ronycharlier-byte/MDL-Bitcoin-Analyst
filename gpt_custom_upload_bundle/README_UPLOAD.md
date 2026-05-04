# GPT Custom Upload Bundle

Upload `gpt_action_openapi.yaml` in GPT Custom Actions.

Upload the Markdown files in this folder into GPT Custom Knowledge:

- gpt_instructions.md
- governance_rules.md
- model_card.md
- data_dictionary.md
- claims_registry.md
- source_manifest.md
- output_policy.md
- latest_report.md
- dashboard_summary.md

Do not upload SQLite databases, raw market data, simulation arrays, logs, `node_modules`, or dependency lock files as Knowledge.

Live analysis rule:

- Use `runQuantBtcMultiFrame` for complete current BTC analysis.
- Use `runQuantBtcModel` for one explicit horizon.
- Use `latestQuantBtcReport` only as a stored artifact, never as a fresh calculation.
- Use `getQuantBtcStatus` to inspect current public API limits, sources, cache TTL, and operational status.

Default multi-frame request:

```json
{
  "asset": "BTC",
  "horizons": [7, 30, 90, 180, 365],
  "simulations": 2000,
  "model": "ensemble",
  "skip_corpus": true,
  "no_online": false
}
```

Every precise number must retain source, report date, run ID, reference spot, source status, and model/version metadata when available.

If a live response includes `cache.hit: true`, disclose that the answer uses the short live cache and cite the cache validity window.
