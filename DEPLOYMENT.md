# Deployment

Recommended runtime: Python 3.12 + FastAPI + Docker.

## Local API

```powershell
pip install -r requirements.txt
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
3. Set `QUANT_API_KEY`.
4. Deploy.

Render free services can sleep. Use Render only for the full Python/Docker engine when sleeping is acceptable or when the service is on a paid no-sleep plan.

Optional Render production environment variables:

```text
EXTERNAL_ARCHIVE_WEBHOOK_URL=https://your-storage-webhook.example.com
CLIENT_KEY_HASH_SECRET=long-random-secret
STRIPE_SECRET_KEY=sk_live_or_test_...
STRIPE_PRICE_ANALYST=price_...
STRIPE_PRICE_PRO=price_...
BILLING_SUCCESS_URL=https://your-site.example.com/success
BILLING_CANCEL_URL=https://your-site.example.com/cancel
TELEGRAM_BOT_TOKEN=...
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

Deploy:

```powershell
cd cloudflare-worker
npm install
npx wrangler login
npm run deploy
```

Safer one-command path after `npm install`:

```powershell
npm run deploy:schema
```

This logs in if needed, deploys the Worker, detects the real `workers.dev` URL, and writes `gpt_action_openapi.cloudflare.deployed.yaml`. Upload the generated file, not the placeholder template.

Manual path after deployment:

1. Copy the generated `workers.dev` URL.
2. Replace `https://quant-btc-model-lite.your-workers-subdomain.workers.dev` in `cloudflare-worker/gpt_action_openapi.cloudflare.yaml`.
3. Upload that schema into GPT Custom Actions.
4. Keep the governance export files in the GPT Knowledge.

## GPT Custom Action

1. Deploy the API.
2. Copy the deployed URL into `gpt_action_openapi.yaml`.
3. Upload the schema into GPT Custom Actions.
4. For Render with `QUANT_API_KEY`, configure API key auth with the same value.

For a public no-sleep GPT Action, prefer `cloudflare-worker/gpt_action_openapi.cloudflare.yaml`.

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
