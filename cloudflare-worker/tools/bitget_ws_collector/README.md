# Bitget WebSocket Collector

Petit collecteur externe pour approcher le vrai temps reel.

Cloudflare Workers free tier n'est pas un daemon WebSocket permanent. Ce script tourne donc hors Worker, ecoute Bitget, puis poste des snapshots compacts vers:

`POST /realtime/ingest`

## Demarrage

```powershell
pip install websockets
python collector.py --worker-url https://quant-btc-model-lite.mdl-bitcoin-analyst.workers.dev --secret "<REALTIME_INGEST_SECRET>"
```

## Secret Worker

Un secret a ete configure dans Cloudflare. La copie locale est ignoree par Git:

`cloudflare-worker/.env.realtime.local`

Pour le reconfigurer:

```powershell
"<SECRET>" | npx wrangler secret put REALTIME_INGEST_SECRET
"<SECRET>" | npx wrangler secret put REALTIME_INGEST_SECRET --name quant-btc-model-deep
"<SECRET>" | npx wrangler secret put REALTIME_INGEST_SECRET --name quant-btc-model-strategy
```

## Statuts

- `price`, `bid`, `ask`, `spread_bps`: real Bitget WebSocket.
- `liquidations_status`: absent tant que le collecteur ne branche pas un vrai canal liquidation.
- `non_bitget_fallback`: absent.

Le collecteur ne remplace pas les runs quantitatifs. Il enrichit seulement la couche realtime utilisee par le dashboard, Telegram et les gates de trading/paper.
