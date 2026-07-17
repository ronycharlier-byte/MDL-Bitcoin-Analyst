# Migration plan

## P0 — implemented in this refactor

- Remove live Bitget signing/order execution and private trading credential configuration.
- Block approval with a stable error; keep mock paper journals only.
- Authenticate/deduplicate Telegram and split/rate-limit deliveries.
- Fail closed for API/admin auth; add trusted-host/body/network/SSRF protections.
- Make state-changing Worker endpoints POST-only and admin-gated.
- Add canonical analysis/error contracts, adapters, semantic validators and fixtures.
- Stabilize seeds, risk aliases, ensemble caps/shrinkage, backtest diagnostics and confidence dimensions.
- Add Python/TypeScript tests, lint/type checks, dependency audits, secret/history scan and CodeQL.
- Disable Render auto-deploy and pin Actions by SHA.
- Establish canonical GPT artifacts and classify legacy variants.

Rollback: revert the refactor commit before deployment. Do not selectively re-enable live trading. D1 migration 0008 is additive; leaving the table in place is safe.

## P1 — next release

- Split `api_server.py` into interface/application/domain/adapters while preserving route tests.
- Split Worker routing, auth, Telegram, storage, alerts and compatibility modules.
- Persist a complete replayable run manifest and input hashes.
- Add isolated train/validation/test orchestration, leakage tests, Kupiec/Christoffersen coverage tests and rolling-origin evaluation for all models.
- Normalize historical SQLite/D1 statuses through versioned views or additive columns.
- Replace dashboard `innerHTML` rendering and convert obsolete action links to authenticated POST forms.
- Add integration tests with Miniflare/D1 and mocked external APIs.
- Implement retention cleanup jobs and verified deletion procedures.

Rollback: retain compatibility adapters and old columns for one major version; dual-read before cutover; never overwrite archives in place.

## P2 — consolidation

- Remove legacy GPT schemas after usage telemetry and a published deprecation window.
- Retire Worker quant-lite duplication or generate shared statistical fixtures across implementations.
- Remove obsolete route aliases and historical trading tables only after export/review.
- Consider Durable Objects only if D1 idempotency cannot meet concurrency requirements.
- Add signed release provenance and environment protection rules in the hosting platforms. CI now generates review-only CycloneDX SBOM artifacts; publication remains a release decision.

## Manual production checklist

Review the diff and audit; rotate any historically exposed credential; apply D1 migration in staging; set secrets; validate host/WAF/rate limits; run negative auth/SSRF/Telegram tests; compare a known archive; approve Render/Worker/GPT changes separately; deploy during a rollback window; monitor readiness/errors/schema failures; then close the change record. No step is automated by this branch.
