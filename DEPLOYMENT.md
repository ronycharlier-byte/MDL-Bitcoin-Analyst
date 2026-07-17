# Deployment

Recommended runtime: Python 3.12 + FastAPI + Docker.

Every production deployment, migration and GPT schema change requires human approval. This repository deliberately does not auto-deploy Render. Validate in staging and follow `docs/MIGRATION_PLAN.md`; never deploy directly from an unreviewed refactor branch.

## Local API

```powershell
$env:QUANT_API_KEY="local-only-secret"
$env:CLIENT_KEY_HASH_SECRET="different-local-only-secret"
pip install -r requirements-dev.txt
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

Run endpoint:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/run `
  -ContentType application/json `
  -Body '{"asset":"BTC","horizon":365,"simulations":200000,"model":"ensemble"}'
```

## Docker

```powershell
docker build -t quant-btc-model-api .
docker run --rm -p 8000:8000 -e QUANT_API_KEY=change-me quant-btc-model-api
```

## Render

This repo includes `render.yaml`.

1. Push the repository to GitHub.
2. Open Render Blueprint:
   `https://dashboard.render.com/blueprint/new?repo=<YOUR_GITHUB_REPO_URL>`
3. Set distinct `QUANT_API_KEY` and `CLIENT_KEY_HASH_SECRET` values plus the production `ALLOWED_HOSTS`.
4. Review the Blueprint diff, tests and migration plan.
5. Manually approve deployment.

Render free services can sleep. Use Render only for the full Python/Docker engine when sleeping is acceptable or when the service is on a paid no-sleep plan.

Optional Render production environment variables:

```text
CLIENT_KEY_HASH_SECRET=long-random-secret
ALERT_WEBHOOK_ALLOWED_HOSTS=alerts.example.com
STRIPE_SECRET_KEY=use-the-platform-secret-store
STRIPE_PRICE_ANALYST=price_...
STRIPE_PRICE_PRO=price_...
BILLING_SUCCESS_URL=https://your-site.example.com/success
BILLING_CANCEL_URL=https://your-site.example.com/cancel
TELEGRAM_BOT_TOKEN=use-the-platform-secret-store
TELEGRAM_WEBHOOK_SECRET=use-a-distinct-high-entropy-secret
ALERT_EMAIL_WEBHOOK_URL=https://your-email-provider-webhook.example.com
```

If these are absent, the API still runs and returns explicit `absent` statuses instead of fabricating storage, payment or alert delivery.

Cloudflare D1 is the default free durable store for the Worker. It is configured in `cloudflare-worker/wrangler.toml`:

```toml
[[d1_databases]]
binding = "DB"
database_name = "quant-btc-model-lite-db"
database_id = "db04fd15-f1ac-46c7-9a08-755757849a24"
migrations_dir = "migrations"
```

Apply D1 migrations:

```powershell
cd cloudflare-worker
npx wrangler d1 migrations apply quant-btc-model-lite-db --remote
```

## Cloudflare Worker no-sleep option

Use this for the GPT Custom endpoint when the backend must not sleep and must stay free.

Important scope:

- Cloudflare Worker runs `quant-lite`, not the full Python/numpy engine.
- It fetches real BTCUSDT spot candles from Bitget.
- Simulation outputs, risk metrics and stress tests are `inferred`.
- Fundamental variables and the corpus knowledge base are `absent` unless a future Cloudflare storage binding is added.
- It caps simulations to protect the free Worker CPU limit.

Validate before an approved deployment:

```powershell
cd cloudflare-worker
npm ci
npm run check
npm run lint
npm run format:check
npm test
npx wrangler login
```

After review and an explicit human approval, apply migrations and deploy with the documented Wrangler commands. `npm run deploy:schema` is a legacy convenience command and must not be used as an automatic CI step.

```powershell
npx wrangler d1 migrations apply quant-btc-model-lite-db --remote
npm run deploy
```

Verify `/live`, `/status`, POST-only analysis, admin denial, Telegram secret denial and the canonical response contract after deployment.

Manual path after deployment:

1. Copy the generated `workers.dev` URL.
2. Verify the server URL in `gpt/actions/openapi.yaml`.
3. Validate it with `python scripts/validate_openapi.py`.
4. Upload only the canonical schema and canonical instructions after separate human approval.

## GPT Custom Action

1. Deploy the API.
2. Confirm the deployed URL in `gpt/actions/openapi.yaml`.
3. Upload that canonical schema and `gpt/instructions/quant_btc_analyst.system.md`.
4. Do not upload root, Worker or `gpt_custom_upload_bundle` legacy variants.

The Cloudflare Worker also proxies the SaaS helper routes:

```text
GET /billing/plans
POST /billing/checkout
POST /clients/register
GET /clients/me
GET /usage-summary
POST /alerts/subscribe
GET /alerts/subscriptions
```

## Other Docker Platforms

Prepared config files:

- `fly.toml` for Fly.io.
- `railway.json` for Railway.
- `cloudrun-service.yaml` for Google Cloud Run.

These platforms all use the same Dockerfile and FastAPI app.

The action must preserve the governance rules:

- no deterministic prediction;
- every precise number needs provenance;
- price data status, simulation status and fundamental status must be explicit;
- regime residual must be shown when bull/bear/range do not total 100%.
