# Quant BTC Operational Upgrade v1.31

Date: 2026-05-07

## Changements livres

1. Telegram bruit reduit
   - Direct par defaut: CRITICAL uniquement.
   - WARNING: regroupes par digest horaire et resume quotidien.
   - `/alerts` reste disponible pour consulter a la demande.

2. Resume client
   - Endpoint: `/client-summary`.
   - Telegram: `/summary`.
   - Format court: biais, risque, strategie, raison principale, action recommandee prudente.

3. Dashboard vendable
   - Endpoint: `/dashboard`.
   - Ajouts: resume client, spot, VaR/CVaR, confidence, strategie, paper PnL, history quick/deep, backtests, liens produit.

4. Realtime Bitget
   - Endpoint ingest: `POST /realtime/ingest`.
   - Secret requis: `REALTIME_INGEST_SECRET`.
   - Secret configure sur lite, deep et strategy; copie locale ignoree: `cloudflare-worker/.env.realtime.local`.
   - Collecteur externe ajoute: `cloudflare-worker/tools/bitget_ws_collector/collector.py`.

5. Backtests visibles
   - Endpoint: `/backtests`.
   - Ajouts: score qualite, VaR breaches, calibration, random walk benchmark, period stability status.

6. Page Whop
   - Endpoint: `/sales`.
   - Contenu: promesse, fonctions, pricing indicatif, limites, disclaimer.

7. Onboarding
   - Endpoint: `/onboarding`.
   - Telegram: `/onboarding`.
   - Explique commandes, VaR/CVaR, confidence, hold/no-trade et limites GPT.

## Politique Telegram

- CRITICAL direct.
- WARNING digest.
- Tests manuels toujours envoyes.
- Alertes personnalisees utilisateur conservees.

## Limite restante

Le collecteur WebSocket n'est pas heberge en continu par Cloudflare Worker. Il faut le lancer sur une machine ou un host gratuit compatible Python long-running pour obtenir un flux permanent.
