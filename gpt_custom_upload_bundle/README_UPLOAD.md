# GPT Custom Upload Bundle

Upload one Action schema depending on the backend you want:

- `gpt_action_openapi.yaml`: full Render Python API with `/run` and `/multi-run`.
- `gpt_action_openapi.cloudflare.deployed.yaml`: no-sleep Cloudflare Worker quant-lite API.

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
- GPT_CUSTOM_SMOKE_TEST.md

Do not upload SQLite databases, raw market data, simulation arrays, logs, `node_modules`, or dependency lock files as Knowledge.

Live analysis rule:

- Use Cloudflare no-sleep by default for fresh live analysis when the installed schema is `gpt_action_openapi.cloudflare.deployed.yaml`.
- Use Render only when the full Python/numpy engine or corpus-backed report generation is explicitly required.
- Use `runQuantBtcMultiFrame` for complete current BTC analysis.
- Use `runQuantBtcModel` for one explicit horizon.
- Use `latestQuantBtcReport` only as a stored artifact, never as a fresh calculation.
- Use `getQuantBtcStatus` to inspect current public API limits, sources, cache TTL, and operational status.
- If using the Cloudflare no-sleep schema, call `getQuantBtcLiteStatus` first, then `runQuantBtcMultiFrame` for complete analysis or `runQuantBtcModel` for one horizon.
- Cloudflare Worker results are quant-lite, not the full Python/numpy engine.
- Cloudflare Worker may disclose `bitget_market_prices: absent` and `fallback_market_prices: real` when Bitget rejects edge requests; this must be stated in the GPT answer.
- Cloudflare Worker has a best-effort public rate limit. If it returns 429, do not retry in a loop.

Default Render multi-frame request:

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

Default Cloudflare multi-frame request:

```json
{
  "asset": "BTC",
  "horizons": [7, 30, 90, 180, 365],
  "simulations": 2000,
  "model": "quant_lite"
}
```

Recommended GPT Custom smoke test prompt:

```text
Analyse BTC maintenant en plusieurs frames. Appelle le serveur, cite le run_id, le spot de reference, les statuts real/inferred/absent, puis donne une lecture probabiliste prudente.
```

Every precise number must retain source, report date, run ID, reference spot, source status, and model/version metadata when available.

If a live response includes `cache.hit: true`, disclose that the answer uses the short live cache and cite the cache validity window.
