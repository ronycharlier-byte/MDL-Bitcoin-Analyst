# Testing

Python tests cover the JSON Schema and semantic contract, invalid quantile/regime cases, deterministic seeds across processes, VaR/CVaR ordering, ensemble weight normalization/cap, walk-forward diagnostics, FastAPI fail-closed authentication, hidden docs, request-size limits, SSRF and static absence of live trading code. Hypothesis generates valid frames, return series, ensemble diagnostics and seeds to exercise the same invariants over hundreds of cases.

Worker tests cover canonicalization, invariant validation, stable errors, cache-only GET behavior and Telegram chunk limits. Python and TypeScript validate the same canonical JSON fixture. TypeScript remains strict. External APIs, D1 and Telegram are not contacted by unit tests.

Local commands:

```powershell
uv pip install --python .venv\Scripts\python.exe -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\ruff.exe check src\contract_validation.py src\simulation_utils.py src\risk_metrics.py src\ensemble_model.py src\backtest.py src\confidence_score.py src\run_manifest.py src\logging_utils.py tests scripts\validate_openapi.py scripts\scan_secrets.py scripts\generate_repository_inventory.py
.venv\Scripts\python.exe -m mypy
cd cloudflare-worker
npm ci
npm run check
npm run lint
npm run format:check
npm test
```

CI additionally audits production dependencies, scans reachable history for high-confidence secrets, and runs CodeQL/dependency review. Full end-to-end production verification remains manual because it requires real platform configuration and must not create external side effects from a test branch.
