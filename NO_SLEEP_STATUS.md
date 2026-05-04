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

## Prepared no-sleep option

Cloudflare Worker folder:

```text
cloudflare-worker/
```

Status:

- Code prepared.
- TypeScript check passes.
- Dry-run bundle works.
- Deployment is blocked until Cloudflare Wrangler is authenticated on this machine.

Required command:

```powershell
cd C:\Users\ronyc\Desktop\Corpus\quant_btc_model\cloudflare-worker
npx wrangler login
npm run deploy:schema
```

After login and deploy, upload the generated Cloudflare schema to GPT Actions if you want the no-sleep Worker endpoint as the primary backend.

Important limitation:

The Cloudflare Worker is `quant-lite`, not the full Python/numpy model. The full model currently runs on Render or another Python/Docker host.
