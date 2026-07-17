# Cloudflare Worker

The Worker is an edge interface and compatibility façade. It authenticates, rate-limits, normalizes contracts, stores compact metadata in D1 and proxies bounded requests to the Python engine. It is not the authoritative quantitative model.

## Endpoint classes

- Public reads: liveness/version/status and explicitly public metadata.
- Analysis writes: POST `/analyze`, `/analyze-deep`, presets, `/run`, `/multi-run`; these may compute and archive.
- Archive reads: GET `/latest`, `/history`, `/compare-runs`.
- Admin mutations: ops monitoring/tests, model refresh, collection, rules, deep jobs, cleanup, paper/performance checkpoints and strategy proposals; require `WORKER_ADMIN_TOKEN` and POST. Their paired GET reports are cache-only.
- Telegram webhook: separate Telegram secret plus chat allowlist.
- Live approval: always 403 `EXECUTION_FORBIDDEN`.

The canonical GPT schema exposes only the minimal research/archive surface. Legacy routes remain runtime compatibility debt and must not be added to the production GPT Action.

## D1

Apply migrations in numeric order. D1 stores compact runs, rate/usage/client metadata, alert rules, ops state, Telegram sessions/idempotency, mock paper journals and strategy diagnostics. Use bound parameters, explicit limits and idempotency keys. Schedule TTL cleanup for caches, rate events and Telegram update IDs.

## Configuration

Non-secret operational limits may stay in `wrangler.toml`. Configure `RENDER_API_KEY`, `WORKER_ADMIN_TOKEN`, Telegram secrets and integration credentials via the Cloudflare secret store. There are deliberately no `BITGET_API_SECRET` or passphrase fields.

## Reliability

All external Worker requests have explicit timeouts. Cached output must expose age/freshness and cannot be relabeled live. 429 responses include stable errors. D1 failure degrades optional persistence but must be visible; Telegram idempotency fails closed if D1 is unavailable. Durable Objects are unnecessary until coordination requires stronger per-key serialization than D1 idempotency provides. Request logs are structured JSON with a bounded request ID, route, method, duration and status; bodies, tokens and chat contents are excluded.

## Deployment

Run `npm ci`, type check, lint, format check and tests. Apply migrations in staging, verify `/live`, status, POST-only behavior, canonical contract and negative auth cases. Deployment and production migration require human approval; this refactor did not deploy.
