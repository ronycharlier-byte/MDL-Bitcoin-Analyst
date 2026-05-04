# No-Sleep Backend Status

## Current production API

Render endpoint:

```text
https://quant-btc-model-api.onrender.com
```

Status:

- Functional.
- Supports live `/run` and `/multi-run`.
- Free Render services may sleep.
- GitHub Actions monitoring pings `/health`, `/version`, and `/status` every 10 minutes when scheduled workflows are active. This can reduce cold starts, but it is not a hard no-sleep guarantee.

## Deployed no-sleep option

Cloudflare Worker folder:

```text
cloudflare-worker/
```

Status:

- Deployed and publicly reachable over HTTPS.
- TypeScript check passes.
- GPT Action schema generated and copied into `gpt_custom_upload_bundle/`.
- `/health`, `/version`, `/status`, `/latest`, `/run`, and `/multi-run` tested successfully.
- Worker version: `1.2.0`.

Public endpoint:

```text
https://quant-btc-model-lite.mdl-bitcoin-analyst.workers.dev
```

Generated GPT Action schema:

```text
cloudflare-worker/gpt_action_openapi.cloudflare.deployed.yaml
gpt_custom_upload_bundle/gpt_action_openapi.cloudflare.deployed.yaml
```

Redeploy command:

```powershell
cd C:\Users\ronyc\Desktop\Corpus\quant_btc_model\cloudflare-worker
npm run deploy:schema
```

Wrangler is authenticated on this machine for the Cloudflare account used during deployment.

Live data note:

- Bitget remains the primary market source.
- Bitget currently returns HTTP 403 from the Cloudflare Worker runtime.
- The Worker therefore falls back to real Kraken XBT/USD daily OHLC data and discloses this in `data_status.market_source` and `warnings`.
- If Bitget becomes reachable from Cloudflare later, the Worker will use Bitget automatically.
- Funding rate, open interest, DXY and Nasdaq are attempted as partial live fundamentals.
- ETF flows, liquidations, hash rate, exchange reserves, stablecoin supply and US rates remain absent unless a future connected source is added.
- Public run endpoints have a best-effort per-IP rate limit and simulation caps for safety.

Important limitation:

The Cloudflare Worker is `quant-lite`, not the full Python/numpy model. The full model currently runs on Render or another Python/Docker host.
