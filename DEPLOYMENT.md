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

## GPT Custom Action

1. Deploy the API.
2. Copy the deployed URL into `gpt_action_openapi.yaml`.
3. Upload the schema into GPT Custom Actions.
4. Configure API key auth with the same `QUANT_API_KEY`.

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
