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
- GitHub Actions monitoring pings `/health`, `/version`, `/status`, and `/audit` every 10 minutes when scheduled workflows are active. This can reduce cold starts, but it is not a hard no-sleep guarantee.

## Deployed no-sleep option

Cloudflare Worker folder:

```text
cloudflare-worker/
```

Status:

- Deployed and publicly reachable over HTTPS.
- TypeScript check passes.
- GPT Action schema generated and copied into `gpt_custom_upload_bundle/`.
- `/health`, `/version`, `/status`, `/audit`, `/latest`, `/run`, and `/multi-run` tested successfully.
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

- Bitget is mandatory for live model conclusions.
- Cloudflare direct egress to Bitget is not used.
- The Worker bridges `/run`, `/multi-run`, and `/latest` to the Render Bitget-backed API.
- No non-Bitget exchange fallback is used for live model conclusions. If the bridge fails, live output is absent.
- Cloudflare Cron warms the Render bridge every 5 minutes.
- Public run endpoints have a best-effort per-IP rate limit and simulation caps for safety.

Important limitation:

The Cloudflare Worker is a public no-sleep facade. The full Bitget-backed Python/numpy model runs on Render behind the bridge.
