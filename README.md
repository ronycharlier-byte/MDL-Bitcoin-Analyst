# Quant BTC Model

Autonomous probabilistic quantitative engine for Bitcoin inside this corpus.

The system produces probabilities, distributions, and risk measures. It never emits certainty or a deterministic price prediction.

French product/GPT Custom README: [`README_FR.md`](README_FR.md).

## Created structure

```text
quant_btc_model/
  data/
    raw/
    processed/
    features/
    backtests/
    simulations/
    quant_model.db
  knowledge_base/
    corpus_raw/
    corpus_chunks/
    metadata/
    claims/
  models/
  reports/
    latest_report.md
    dashboard_summary.md
  logs/
    system.log
  src/
  README.md
```

## Quick start

From `C:\Users\ronyc\Desktop\Corpus\quant_btc_model`:

```powershell
python src/main.py --asset BTC --horizon 365 --simulations 200000 --model ensemble
```

Useful options:

```powershell
python src/main.py --asset BTC --horizon 90 --simulations 50000 --model garch
python src/main.py --asset BTC --horizon 365 --simulations 200000 --model ensemble --no-online
python src/main.py --asset BTC --horizon 365 --simulations 200000 --model ensemble --skip-corpus
```

## Always-awake GPT endpoint

The full Python API can run on Render/Fly/Railway/Cloud Run, but free Render services may sleep. For a free endpoint that does not sleep, this repo includes a Cloudflare Worker:

```powershell
cd cloudflare-worker
npm install
npx wrangler login
npm run deploy
```

Worker scope:

- `quant-lite` TypeScript model, not the full Python/numpy engine.
- Real market prices from Bitget BTCUSDT spot candles.
- Simulation outputs, risk metrics and stress tests tagged as inferred.
- Fundamentals, corpus KB and full backtest artifacts tagged as absent.
- Simulation count capped for the free Worker runtime.

GPT Action schema:

```text
cloudflare-worker/gpt_action_openapi.cloudflare.yaml
```

## Realtime API behavior

`POST /run` is the fresh calculation endpoint for GPT Actions. By default it:

- reloads online BTC market history;
- appends the latest Bitget BTCUSDT spot ticker as the reference price;
- runs the selected probabilistic model;
- returns provenance with `reference_spot`, `reference_spot_timestamp`, `reference_spot_source`, and `model_run_id`.

`GET /latest` only returns stored local artifacts. Use it for context, not for a fresh market calculation.

For multi-frame GPT analysis, use `POST /multi-run` with the standard horizons:

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

`/multi-run` uses a fast in-memory runtime. It captures one shared Bitget spot snapshot and applies it to every frame, so the 7/30/90/180/365 day outputs are comparable from the same reference price.

Live online fundamentals are partial:

- `etf_flows`: Farside Investors Bitcoin ETF flow total in USD millions.
- `funding_rate` and `open_interest`: Bitget futures.
- `liquidations`: Bitget UTA public liquidation WebSocket BTCUSDT quote amount when a push is received during the configured observation window; otherwise left `NULL`.
- `hash_rate`: Blockchain.com hash-rate chart.
- `exchange_reserves`: Bitget Proof of Reserves BTC platform assets.
- `stablecoins_supply`: DeFiLlama stablecoin pegged USD total.
- `dxy` and `nasdaq`: Stooq market quotes.
- `us_rates`: FRED DGS10, with U.S. Treasury 10Y yield fallback.

The public API includes a short SQLite-backed cache, a SQLite-backed rate limit with in-memory fallback, and version metadata:

- `GET /status`
- `GET /version`
- `GET /audit`
- `api_version`
- `model_version`
- `schema_version`
- `git_commit`
- UTC and Europe/Paris timestamp fields for report, audit, archive, cache, and spot provenance

`GET /audit` is the GPT preflight endpoint. It does not run a market simulation; it reports readiness, source policy, latest archive metadata, required real/absent fundamental fields, timezone policy, and the visible monitor alert rule.

Additional production diagnostics:

- `GET /history`: recent runtime archives plus durable-storage status.
- `GET /compare-runs`: latest archive vs previous archive deltas for spot, VaR/CVaR, regimes and confidence.
- `GET /alerts`: stale data, VaR, confidence and transition-regime alerts.
- `POST /alerts/subscribe`: register webhook, Discord, Telegram or email alert targets.
- `GET /alerts/subscriptions`: list stored alert subscriptions.
- `GET /backtest-summary`: visible walk-forward baseline diagnostics.
- `GET /dashboard`: simple live web dashboard, also mirrored at `reports/dashboard.html`.
- `GET /pdf-report`: lightweight timestamped PDF export for the latest archive.
- `POST /clients/register`: create a client key for quota and usage tracking.
- `GET /clients/me`: inspect the current client key and quota.
- `GET /usage-summary`: recent usage logs for public or keyed access.
- `GET /billing/plans`: public plan, quota and Stripe readiness metadata.
- `POST /billing/checkout`: create a Stripe subscription Checkout Session when Stripe env vars are configured.

Every live multi-frame response now includes:

- data freshness gates (`spot` blocks when stale or absent; fundamentals warn when stale);
- Monte Carlo probability error margins;
- multi-seed stability diagnostics;
- expanded drawdown fields: `mean_simulated_max_drawdown`, `median_max_drawdown`, `p95_max_drawdown`, `worst_sample_drawdown`;
- Bitget order-book liquidity snapshot when reachable;
- options/implied volatility context when reachable;
- ETF flow 1d/7d/30d trend diagnostics when reachable;
- heuristic explainability by momentum, volatility, macro, derivatives and ETF context.

Productization layer:

- Client keys are lightweight access tokens for quota tracking and usage logs.
- Plans are defined in the API as Free, Analyst and Pro; Stripe checkout is inactive until `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ANALYST` and `STRIPE_PRICE_PRO` are configured.
- Durable off-host storage is now available for free through Cloudflare D1 on the Worker. Render can still mirror compact records to Supabase or an external webhook if those env vars are configured.
- Alert delivery is best-effort: webhook/Discord use HTTPS targets, Telegram requires `TELEGRAM_BOT_TOKEN`, and email requires `ALERT_EMAIL_WEBHOOK_URL`.
- Public backtests expose hit rate, Brier score, calibration error, P10/P90 coverage, VaR breach rates and random-walk benchmark fields.

GitHub Actions monitoring:

```text
.github/workflows/monitor-api.yml
.github/workflows/archive-live-run.yml
```

The monitor runs every 10 minutes and fails if critical quality checks regress: Bitget-only routing, 5 default frames, backend version, runtime archive creation, ETF flows, exchange reserves, and required live fundamentals. If it fails, GitHub Actions opens or updates a visible issue titled `[quant-btc-monitor-alert] Live API quality monitor failing`; the next successful monitor closes it.

The archive workflow runs every 6 hours and commits compact live-run summaries into:

```text
external_archive/live_runs/
```

These summaries are a free external audit layer outside Render's runtime filesystem. They intentionally exclude raw simulation arrays and massive payloads.

GPT Custom upload bundle:

```text
gpt_custom_upload_bundle/
```

## Data policy

- No source file outside `quant_btc_model` is modified.
- Corpus integration copies relevant files into `knowledge_base/corpus_raw`.
- Market loading uses local CSV first, then public online Bitget candles unless `--no-online` is set. Non-Bitget market fallback is disabled by default for live GPT runs.
- If real market data are unavailable, the engine generates synthetic prices tagged `mock` and logs `MOCK`.
- Missing fundamental fields remain SQL `NULL` and are logged in `logs/system.log`.
- SQLite tables include `timestamp`, `source`, and `statut` (`real`, `mock`, or `missing`).

## Optional input files

Place audited CSV files in `data/raw`.

Market prices:

```csv
timestamp,open,high,low,close,volume
2024-01-01,42000,43000,41000,42500,123456789
```

Supported names:

- `BTC_prices.csv`
- `btc_prices.csv`
- `market_prices.csv`

Fundamentals:

```csv
timestamp,etf_flows,funding_rate,open_interest,liquidations,hash_rate,exchange_reserves,stablecoins_supply,dxy,us_rates,nasdaq
2024-01-01,,,,,,,,,,
```

Supported names:

- `BTC_fundamentals.csv`
- `btc_fundamentals.csv`
- `fundamental_features.csv`

## SQLite tables

- `market_prices`
- `technical_features`
- `fundamental_features`
- `risk_metrics`
- `model_runs`
- `simulation_results`
- `backtest_results`

Database path:

```text
data/quant_model.db
```

## Models

Implemented in `src`:

- `monte_carlo.py`: lognormal Monte Carlo from historical daily returns.
- `student_t_model.py`: heavy-tailed Student-t simulation.
- `jump_diffusion.py`: jump diffusion with historical tail calibration.
- `garch_model.py`: GARCH-like conditional variance simulation.
- `regime_switching.py`: calm/stress state simulation.
- `liquidation_model.py`: downside cascade shock model.
- `correlation_model.py`: macro-sensitive correlation model with NULL-safe fundamentals.
- `ensemble_model.py`: dynamic weighting by performance, error, and calibration inputs.

## Risk metrics

Implemented in `src/risk_metrics.py`:

- VaR 95 and 99
- CVaR 95 and 99
- skewness
- kurtosis
- `max_drawdown` backward-compatible alias for mean simulated max drawdown
- `mean_simulated_max_drawdown` / `expected_max_drawdown`
- `median_max_drawdown`
- `p95_max_drawdown`
- `worst_sample_drawdown`
- conditional volatility

## Corpus pipeline

`src/corpus_pipeline.py`:

1. Scans the existing corpus for relevant text files.
2. Copies relevant files into `knowledge_base/corpus_raw`.
3. Writes provenance into `knowledge_base/metadata/corpus_copy_manifest.jsonl`.
4. Chunks documents into 500-1000 token JSON chunks.
5. Extracts claims into `knowledge_base/claims/claims.jsonl`.

Claim categories:

- marche
- macro
- volatilite
- risques
- hypotheses

Default reliability is `unknown`.

## Reports

The run creates:

- `reports/latest_report.md`
- `reports/dashboard_summary.md`
- `data/simulations/<run_id>_summary.json`

Reports include data used, missing data, assumptions, model weights, P10/median/P90 distribution, threshold probabilities, VaR/CVaR, stress tests, drawdown, bull/bear/range probabilities, confidence score, backtest results, and explicit limits.

## Quality rules

- The engine is modular and NULL-safe.
- Data quality status is explicit.
- GitHub monitoring fails on silent regressions in frame count, source policy, required fundamentals, version, or archive creation.
- Live API responses include `archive.archive_id`; scheduled GitHub archives preserve compact summaries externally.
- GPT-facing outputs must not mix multiple archive IDs or spot snapshots in one analysis unless explicitly comparing runs.
- Mock data are never presented as real data.
- Exceptions are caught, logged, and written to `data/last_error.json`.
- This is research infrastructure, not financial advice.

## License

This repository is proprietary and source-visible for review/evaluation only.
Commercial use, resale, hosted services, production deployments, GPT products,
client work, or redistribution require prior written permission. See
[`LICENSE`](LICENSE).
