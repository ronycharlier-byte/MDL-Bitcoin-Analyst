# Data contract

The canonical analysis contract is `contracts/analysis.schema.json`; semantic checks are implemented in `src/contract_validation.py` and `cloudflare-worker/src/contracts.ts`. JSON Schema validates shape, while runtime validators enforce relationships JSON Schema cannot express clearly.

## Required root fields

`status`, `asset`, `response_type`, `archive_id`, `analysis_id`, `provenance`, `data_inventory`, `frames`, `backtests`, `alerts`, `warnings`, `limitations` and `policy`.

Only BTC is supported. Every successful analysis has a non-empty archive ID and at least one frame. Partial results use `status=partial`; failures use the separate stable error contract.

## Provenance

Provenance records report UTC/local timestamps, timezone, archive creation time, API/Worker/model/schema/git versions, runtime, cache status/age/threshold and spot value/currency/source/timestamps/age/status. Europe/Paris is a display timezone; UTC is the storage and comparison reference.

Each `data_inventory` row is a field-level fact:

```json
{
  "field": "liquidations",
  "value": null,
  "status": "absent",
  "source": null,
  "observed_at_utc": null,
  "unit": null,
  "limitations": ["No validated source was available for this run."]
}
```

Never infer `real` from the presence of a numeric value. `inferred` denotes model output; `mock` and `mock_paper` are synthetic; `stale` failed freshness; `unknown` lacks classification; `ambiguous_status` preserves a legacy state that cannot be mapped safely.

## Frame invariants

- `horizon_days > 0`, `simulation_count > 0`.
- `0 ≤ probability_up ≤ 1`.
- `p10 ≤ median ≤ p90`.
- bull + bear + range + transition = 1 within 0.015.
- VaR/CVaR use positive loss: `var99_loss ≥ var95_loss`, `cvar95_loss ≥ var95_loss`, `cvar99_loss ≥ var99_loss` and `cvar99_loss ≥ cvar95_loss`.
- confidence scores, when present, are in [0,100].
- comparisons require compatible asset, schema/model definition and horizons; spot snapshots must be reported separately.

Legacy aliases `var_95`, `cvar_95`, `var_99` and `cvar_99` are kept during migration. Canonical fields take precedence.

## Stable errors

Errors always contain `status=error`, `error_code`, `message`, `retryable`, `details` and `request_id`. The shared taxonomy includes request/source/freshness/archive/frame/quantile/probability/regime/risk/backtest/cache/rate/storage/model/schema/auth/method/execution/internal failures. Clients branch on `error_code`, never on the prose message.

## Contract evolution

- Additive optional fields are backward compatible.
- Removing/renaming a field or changing its unit/meaning requires a major schema version.
- New aliases are normalized at the boundary; internal code uses canonical names.
- Fixtures under `contracts/fixtures/` must validate in Python and TypeScript before merge.
- Historical archives are immutable; adapters upgrade them on read and preserve raw metadata.
