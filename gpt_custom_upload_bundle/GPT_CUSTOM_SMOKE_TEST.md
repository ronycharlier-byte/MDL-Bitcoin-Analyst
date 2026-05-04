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
- Cites full `model_run_id` values, not only shortened suffixes.
- Cites one `archive_id` and does not mix it with older runs.
- Shows report date and spot timestamp in UTC and Europe/Paris.
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
- Keeps the same run/archive provenance for all displayed 365d numbers.
- Does not give financial advice.

## Prompt 3

```text
Fais une analyse live BTC 7/30/90/180/365. Je veux l'heure correcte pour Paris, un seul run, un seul archive_id, les run_id complets, et aucune certitude.
```

Expected behavior:

- Calls `auditQuantBtcLiteSystem`.
- Calls `runQuantBtcMultiFrame`.
- Stops or reruns if two different archive IDs or spot timestamps are mixed.
- Shows `report_date_utc` / `report_date_paris` and `reference_spot_timestamp_utc` / `reference_spot_timestamp_paris`.
- Labels prices as real Bitget and simulations/risks as inferred.

## Failure Behavior

If the Action returns `429`, the GPT must not retry repeatedly.

If live model output is absent, the GPT must not invent numbers.
