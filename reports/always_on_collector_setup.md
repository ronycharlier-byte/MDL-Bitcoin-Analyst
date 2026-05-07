# Setup 24/7 du collecteur Bitget

Objectif: obtenir un flux Bitget WebSocket continu, sans dependre du PC local.

## Choix recommande

Oracle Cloud Always Free VM Ubuntu.

Pourquoi:

- VM toujours allumee si elle est bien creee en Always Free.
- Suffisant pour un petit collecteur WebSocket Python.
- Pas besoin de reecrire le collecteur en JavaScript.

## Architecture

```text
Bitget WebSocket
  -> collector.py sur VPS 24/7
  -> POST /realtime/ingest
  -> Cloudflare D1
  -> Telegram / Dashboard / Strategy gates
```

## Installation rapide

Sur la VM Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y git
git clone https://github.com/ronycharlier-byte/MDL-Bitcoin-Analyst.git
cd MDL-Bitcoin-Analyst/cloudflare-worker/tools/bitget_ws_collector
sudo REALTIME_INGEST_SECRET="<SECRET>" bash install_systemd_ubuntu.sh
```

## Verification

```bash
systemctl status quant-btc-bitget-collector
journalctl -u quant-btc-bitget-collector -f
```

Puis:

```bash
curl https://quant-btc-model-lite.mdl-bitcoin-analyst.workers.dev/realtime/status
```

## Notes importantes

- Le secret est deja configure sur les Workers Cloudflare.
- La copie locale est ignoree par Git: `cloudflare-worker/.env.realtime.local`.
- Le collecteur tourne en `systemd` avec `Restart=always`.
- Si la VM reboot, le service redemarre automatiquement.
- Si Bitget coupe le WebSocket, le script se reconnecte.

## Limite

Oracle Always Free peut demander une carte bancaire pour verification et la creation de VM depend de la disponibilite de region. Il faut choisir une forme marquee Always Free.
