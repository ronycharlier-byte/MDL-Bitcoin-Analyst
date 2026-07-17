# Security

## Trust boundaries

Untrusted inputs include HTTP bodies/query strings/headers, Telegram updates, GPT-generated arguments, archived external text, market/fundamental APIs and webhook responses. FastAPI, the Worker, D1/SQLite and CI are separate trust zones. No content field may alter system policy or request unrelated external actions.

## Implemented controls

- Protected FastAPI routes fail closed when authentication is unavailable and compare secrets in constant time.
- Worker administration uses a separate token. Analysis-to-Render authentication stays server-side.
- Body sizes, upstream timeouts, security headers and trusted hosts are bounded centrally.
- Proxy IP headers are ignored unless explicitly trusted; Cloudflare limiting uses `CF-Connecting-IP`.
- Arbitrary webhooks are disabled by default, require an HTTPS hostname allowlist, reject embedded credentials/private resolution and do not follow redirects.
- Telegram requires its secret header, an owner chat allowlist, a bounded body and D1 `update_id` idempotency.
- Every state-changing Worker route is POST-only. GET analysis compatibility was removed because it wrote caches/archives.
- Private Bitget credentials and live order calls are absent. `/trading/approve` returns `EXECUTION_FORBIDDEN`.
- API docs are disabled by default. CORS is not wildcard. Errors are stable and sanitized.
- API and Worker request logs are JSON records containing bounded request IDs, routes, methods, durations and status codes; request bodies, tokens and chat content are not logged.
- CI actions are pinned by commit SHA; CodeQL, dependency review, Python/npm audits, CycloneDX SBOM generation and current/history secret scanning are configured.
- Render automatic deploy is disabled and containers run as an unprivileged user.

## Secret handling

Use platform secret stores or `wrangler secret put`; never store values in `wrangler.toml`, logs, archives, GPT knowledge files or screenshots. `.env.example` lists names only. Rotate a credential after suspected exposure and review Git history plus provider audit logs. The application intentionally has no private exchange trading credential variables.

Expected secrets include API/admin auth, Telegram bot/webhook, client hash, Stripe and optional delivery/storage integrations. Restrict scope and environment; production and staging must not share values.

## Retention and deletion

- Telegram `update_id` deduplication: retain only as long as replay protection requires (recommended 7 days).
- Telegram session/chat metadata and alert subscriptions: retain while enabled; delete within 30 days of verified user/admin request.
- Rate-limit events/cache: TTL cleanup; do not archive identifiers.
- Analysis archives/backtests: retention is product-governance data, recommended 365 days unless legal/audit requirements demand longer.
- CI artifacts: 14 days unless a documented incident requires preservation.
- Never store raw secrets, private messages unrelated to commands, or full simulation arrays in external Git archives.

Deletion must cover D1/SQLite rows, external archive mirrors, alert destinations and backups where supported. Git history is not an appropriate store for personal data.

## Remaining risks

The two runtime façades are still large, dashboard HTML needs a broader DOM-XSS refactor, historical schemas/docs contain stale operations, deployed Cloudflare/Render/WAF settings were not inspected, and the custom secret scanner uses high-confidence patterns rather than entropy analysis. See `AUDIT_REPORT.md` and `docs/MIGRATION_PLAN.md`.

## Reporting

Do not place exploit details or credentials in public issues. Report the affected version, endpoint, impact and reproduction with redacted values to the repository owner. Acknowledgement and remediation timelines are not contractually guaranteed by this repository.
