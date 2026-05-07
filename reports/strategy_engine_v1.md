# Quant BTC Strategy Engine v1

Statut : infrastructure de strategie probabiliste, pas conseil financier.

## Objectif

Le Strategy Engine transforme les sorties du Quant BTC Model en scores quantitatifs lisibles par GPT, Telegram et le journal de paper trading.

Il ne produit jamais une certitude. Il produit :

- un score ensemble entre -100 et +100 ;
- une action candidate : `buy_candidate`, `sell_or_reduce_candidate` ou `hold` ;
- un niveau d'accord entre strategies ;
- des gates de risque avant toute creation d'ordre paper/proposal.

## Methodes quantitatives

1. `trend_momentum`
   - Utilise P(up) et rendement median sur plusieurs horizons.
   - Donne plus de poids aux horizons tactiques et intermediaires.

2. `mean_reversion`
   - Compare le spot temps reel au P10, a la mediane et au P90 du frame choisi.
   - Score positif si le spot est sous le centre de distribution.

3. `volatility_breakout`
   - Mesure l'asymetrie positive de la distribution.
   - Penalise fortement la VaR 95.

4. `regime_filter`
   - Utilise bull / bear / range / transition.
   - Penalise les regimes transition eleves.

5. `risk_adjusted_quant`
   - Combine P(up), rendement median, confidence, VaR, CVaR et transition.
   - C'est le score defensif principal.

6. `flow_liquidity_context`
   - Utilise ETF flows, imbalance order book Bitget et contexte options Deribit si presents.
   - Faible poids, car ces donnees sont des snapshots.

## Endpoints

- `GET /strategies/status`
- `GET /strategies/deep-summary`
- `GET /strategies/signal?preset=deep&horizon=30`
- `GET /strategies/ensemble?preset=deep&horizon=30`
- `GET /strategies/signals?limit=10`
- `GET /strategies/performance`
- `GET /strategies/paper-order?preset=deep&horizon=30`
- `GET /strategies/propose-trade?preset=deep&horizon=30&mode=paper`
- `GET /trading/paper-pnl`
- `GET /trading/paper-portfolio`
- `GET /trading/paper-report`
- `GET /risk/live-readiness`
- `GET /market/realtime-capabilities`
- `GET /assets/supported`
- `GET /options/summary`

## Telegram

- `/strategy`
- `/strategy_deep`
- `/paper_strategy`
- `/strategy_orders`

## Regles de risque

Un candidat strategy ne devient actionnable que si :

- le spot est reel et frais ;
- le score ensemble depasse le seuil configure ;
- l'accord entre strategies depasse le seuil configure ;
- la confidence du frame respecte le seuil trading ;
- VaR 95 et transition restent sous les seuils de risque.

## Statuts

- Prix marche : `real` si Bitget est disponible.
- Outputs modele : `inferred`.
- Scores strategie : `inferred`.
- Ordres paper : `mock`.
- Ordres live : desactives par defaut et soumis a approbation explicite.

## Limites

Le Strategy Engine ne connait pas l'etat reel du portefeuille.
Un signal `sell_or_reduce_candidate` ne prouve pas qu'une position existe.
Les queues rares Monte Carlo restent approximatives.
Les backtests long terme doivent peser negativement dans toute conclusion.
Tout resultat doit citer `archive_id`, `run_id`, date UTC/Paris, spot et statuts de donnees.

## Upgrade operationnel v1.30.0

Ajouts :

- suivi mark-to-market des signaux stockes ;
- checkpoints strategie 1j/3j/7j/30j dans D1 ;
- rapport paper trading consolide ;
- dashboard enrichi avec strategie, paper portfolio et live readiness ;
- endpoint des capacites temps reel pour distinguer polling et WebSocket permanent ;
- support multi-assets documente, BTC seul en production ;
- readiness live qui bloque tant que les secrets Bitget et l'approbation explicite sont absents.

Regle produit : vendre le moteur comme infrastructure probabiliste d'analyse, de risque, de paper trading et d'alerting, pas comme bot de trading autonome.
