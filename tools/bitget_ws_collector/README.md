# Bitget WebSocket Collector

Objectif : capter en continu les donnees Bitget que le Worker gratuit ne peut pas maintenir lui-meme en WebSocket permanent.

## Pourquoi ce collecteur existe

Cloudflare Workers gratuit est excellent pour exposer des endpoints GPT sans sommeil, mais ce n'est pas un processus permanent.

Pour du vrai temps reel continu, il faut un collecteur separe qui tourne :

- sur une machine locale ;
- sur un petit VPS gratuit si disponible ;
- sur un service long-running ;
- ou en job supervise par l'utilisateur.

## Donnees visees

- spot ticker BTCUSDT ;
- order book/depth ;
- funding/open interest ;
- liquidations Bitget ;
- horodatage UTC + Europe/Paris ;
- statut `real`, `absent`, `stale`.

## Installation

```powershell
cd C:\Users\ronyc\Desktop\Corpus\quant_btc_model\tools\bitget_ws_collector
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Lancement local

```powershell
python collector.py --asset BTC --out ../../data/raw/bitget_ws_latest.jsonl
```

## Integration Worker

La version actuelle ecrit localement en JSONL.

Prochaine etape possible : ajouter un endpoint Worker ingest protege par secret :

```text
POST /realtime/ingest
```

Le Worker stockera alors les snapshots dans D1, et Telegram pourra alerter sur :

- liquidations > seuil ;
- spot stale ;
- spread anormal ;
- imbalance carnet ;
- funding/OI extremes.

## Limite

Ce collecteur est une brique operationnelle externe. Il ne transforme pas le GPT en trader autonome et ne remplace pas une infrastructure exchange professionnelle.
