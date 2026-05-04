# GPT Custom Smoke Test

Use this file as a short checklist after uploading the Cloudflare no-sleep Action schema.

## Required Action Flow

For a complete fresh analysis, the GPT should call:

1. `auditQuantBtcLiteSystem`
2. `runQuantBtcMultiFrame`

For one explicit horizon, the GPT should call:

1. `auditQuantBtcLiteSystem`
2. `runQuantBtcModel`

It should not call `latestQuantBtcReport` for a fresh calculation.

## Prompt 1

```text
Analyse BTC maintenant en plusieurs frames. Appelle le serveur, cite le run_id, le spot de reference, les statuts real/inferred/absent, puis donne une lecture probabiliste prudente.
```

Expected behavior:

- Calls `auditQuantBtcLiteSystem`.
- Calls `runQuantBtcMultiFrame`.
- Cites `model_run_id`, `report_date`, shared reference spot, source and status mix.
- States Cloudflare is a Bitget bridge to Render.
- Does not use non-Bitget exchange fallback numbers.
- Cites `cloudflare_bridge.source_policy` when present.
- Uses probabilistic wording only.

## Prompt 2

```text
Donne-moi seulement l'horizon 365 jours pour BTC, avec VaR, CVaR, P10, mediane, P90 et limites.
```

Expected behavior:

- Calls `auditQuantBtcLiteSystem`.
- Calls `runQuantBtcModel`.
- Uses horizon `365`.
- Explains VaR/CVaR as simulated return loss metrics.
- Does not give financial advice.

## Failure Behavior

If the Action returns `429`, the GPT must not retry repeatedly.

If live model output is absent, the GPT must not invent numbers.
