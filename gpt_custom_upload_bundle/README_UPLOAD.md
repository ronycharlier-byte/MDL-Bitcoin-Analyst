# GPT Custom Upload Bundle

Upload one Action schema depending on the backend you want:

- `gpt_action_openapi.yaml`: full Render Python API with `/run` and `/multi-run`.
- `gpt_action_openapi.cloudflare.deployed.yaml`: no-sleep Cloudflare Worker bridge to the Bitget-backed Render API.
- `gpt_action_openapi.cloudflare.deployed.json`: same Cloudflare schema in JSON format; use it if GPT rejects the YAML parser format.

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
- NO_SLEEP_STATUS.md

Do not upload SQLite databases, raw market data, simulation arrays, logs, `node_modules`, or dependency lock files as Knowledge.

Live analysis rule:

- Use Cloudflare no-sleep by default for fresh live analysis when the installed schema is `gpt_action_openapi.cloudflare.deployed.yaml`.
- The Cloudflare schema bridges to Render so Bitget remains the required source.
- Do not substitute any non-Bitget exchange if the Bitget bridge fails.
- Use `runQuantBtcModel` with `horizons: [7, 30, 90, 180, 365]` for complete current BTC analysis. Do not use `horizon: 365` for a multi-frame request.
- If the GPT Actions UI only exposes `asset`, call `runQuantBtcModel` with `asset: BTC`; `/run` defaults to the 5-frame result when no `horizon` is sent.
- `runQuantBtcMultiFrame` may be used if the GPT Actions UI exposes it, but it is optional because `/run` supports multi-frame routing.
- Use `runQuantBtcModel` for one explicit horizon.
- Use `latestQuantBtcReport` only as a stored artifact, never as a fresh calculation.
- Use `getQuantBtcStatus` to inspect current public API limits, sources, cache TTL, and operational status.
- If using the Cloudflare no-sleep schema, call `auditQuantBtcLiteSystem` first, then `runQuantBtcMultiFrame` for complete analysis or `runQuantBtcModel` for one horizon.
- Cloudflare Worker responses may include `cloudflare_bridge` metadata; cite it when useful.
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

Default Cloudflare Bitget-bridge multi-frame request:

```text
GET /run?asset=BTC
```

Recommended GPT Custom smoke test prompt:

```text
Analyse BTC maintenant en plusieurs frames. Appelle le serveur, cite le run_id, le spot de reference, les statuts real/inferred/absent, puis donne une lecture probabiliste prudente.
```

Every precise number must retain source, report date, run ID, reference spot, source status, and model/version metadata when available.

If a live response includes `cache.hit: true`, disclose that the answer uses the short live cache and cite the cache validity window.
