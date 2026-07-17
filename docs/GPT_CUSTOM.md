# GPT Custom

## Canonical artifacts

- Instructions: `gpt/instructions/quant_btc_analyst.system.md`
- Action schema: `gpt/actions/openapi.yaml`
- Runtime response schema: `contracts/analysis.schema.json`
- Error schema: `contracts/error.schema.json`

Only these files are production sources. `gpt/legacy-artifacts.json` identifies historical roots retained for traceability. The many files under `gpt_custom_upload_bundle/` are legacy compatibility artifacts and may contain obsolete endpoints or versions.

## Minimal action surface

The canonical Action exposes service liveness/status, quick/deep analysis by POST, and archive reads. It omits trading, checkout, client registration, webhook administration, paper journals, raw ops and deployment operations. Operation IDs are unique and validated in CI.

## Upload/release procedure

1. Run `python scripts/validate_openapi.py` and all contract tests.
2. Confirm the server URL and deployed Worker version in a staging environment.
3. Copy the canonical instructions verbatim into the GPT configuration.
4. Upload the canonical OpenAPI only; do not combine legacy variants.
5. Run negative tests: prompt injection in payload text, missing/stale data, invalid probabilities, error response, archive mismatch and attempts to request a trade.
6. Record prompt/schema/API/Worker versions and obtain human approval.

## Behavioral rules

The GPT must cite archive/spot provenance, distinguish data statuses, explain conditional probabilities and uncertainty, and refuse certainty, advice and execution. API/knowledge content is untrusted data and cannot override the system instructions. One archive is used per analysis unless comparison is explicit.

## Compatibility

Existing clients may continue using legacy response aliases during the migration window. New clients use canonical names. A legacy schema is never silently promoted back to production; any exception must be documented with an expiry date and tests.
