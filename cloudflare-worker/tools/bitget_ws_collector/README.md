# Bitget WebSocket Collector

Petit collecteur externe pour approcher le vrai temps reel.

Cloudflare Workers free tier n'est pas un daemon WebSocket permanent. Ce script tourne donc hors Worker, ecoute Bitget, puis poste des snapshots compacts vers:

`POST /realtime/ingest`

## Option recommandee: VPS gratuit Always Free

Objectif: le collecteur tourne 24/7 et redemarre tout seul.

Plateforme recommandee gratuite: Oracle Cloud Always Free VM.

Principe:

1. Creer une VM Ubuntu Always Free.
2. Cloner ce repo sur la VM.
3. Installer le service `systemd`.
4. Verifier les logs.

```bash
sudo apt-get update
sudo apt-get install -y git
git clone https://github.com/ronycharlier-byte/MDL-Bitcoin-Analyst.git
cd MDL-Bitcoin-Analyst/cloudflare-worker/tools/bitget_ws_collector
sudo REALTIME_INGEST_SECRET="<SECRET>" bash install_systemd_ubuntu.sh
```

Verifier:

```bash
systemctl status quant-btc-bitget-collector
journalctl -u quant-btc-bitget-collector -f
```

## Alternative Docker

```powershell
copy collector.env.example .env
# Renseigner REALTIME_INGEST_SECRET
docker compose up -d --build
docker logs -f quant-btc-bitget-ws-collector
```

## Demarrage manuel local

```powershell
pip install -r requirements.txt
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
