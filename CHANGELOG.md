# Changelog

## Unreleased — governance and safety refactor

### Added

- Canonical analysis/error schemas, Python/TypeScript adapters, semantic validators and shared fixtures.
- Stable error taxonomy, field-level data status vocabulary and explicit information-only policy.
- Telegram webhook authentication, idempotency migration, bounded parsing and chunked/429-aware delivery.
- FastAPI liveness/readiness separation, request size/trusted host/security headers and webhook SSRF policy.
- Deterministic seed derivation, richer backtest/calibration metrics, ensemble shrinkage/cap and confidence dimensions.
- Pytest, Ruff, mypy, Vitest, ESLint, Prettier, CI audits, CodeQL, dependency review and secret-history scanner.
- Hypothesis property tests, shared Python/TypeScript fixture validation and review-only CycloneDX SBOM artifacts.
- Structured redacted request logs and propagated request IDs for FastAPI and the Worker.
- Canonical GPT Action/instructions and architecture, security, data, model, Telegram, Worker and migration documents.

### Changed

- Protected API routes fail closed; Worker mutations and analysis runs are POST-only.
- Worker GET reports are cache-only; alert, paper checkpoint and strategy-performance refreshes use authenticated POST routes.
- Render proxy calls are authenticated and time-bounded; CORS no longer uses a wildcard.
- Every Worker external fetch is routed through a bounded timeout helper.
- Render automatic deployment is disabled; container runtime is non-root; GitHub Actions are SHA-pinned.
- VaR/CVaR expose explicit positive-loss canonical aliases while retaining legacy fields.

### Removed/blocked

- Private Bitget trading credential fields, request signing and live order placement.
- Live trade approval semantics; `/trading/approve` now returns `EXECUTION_FORBIDDEN`.

### Compatibility

Historical OpenAPI/prompt variants and response aliases remain in place for traceability. They are marked legacy and are not canonical production inputs.
