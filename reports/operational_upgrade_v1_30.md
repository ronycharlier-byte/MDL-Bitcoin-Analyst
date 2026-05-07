# Quant BTC Operational Upgrade v1.30.0

Statut : couche operationnelle ajoutee pour transformer le GPT en outil plus vendable, auditable et surveillable.

Ce document separe clairement :

- `implemented` : disponible dans le Worker et D1 ;
- `scaffolded` : structure prete, mais depend d'un collecteur ou de credentials ;
- `blocked_by_credentials` : volontairement bloque tant que les secrets/approbations ne sont pas configures ;
- `external_required` : impossible a garantir dans un Worker gratuit seul.

## 14 priorites

| # | Priorite | Statut | Livrable |
|---:|---|---|---|
| 1 | Backtests plus visibles | implemented | `GET /backtests`, dashboard, conclusion VaR breach explicite |
| 2 | Historique signaux strategies | implemented | table `strategy_signals`, `GET /strategies/signals`, `GET /strategies/performance` |
| 3 | Dashboard client | implemented | `GET /dashboard` avec ops, spot, backtests, strategies, paper, live readiness |
| 4 | Vrai temps reel WebSocket Bitget | scaffolded/external_required | `tools/bitget_ws_collector`, `GET /market/realtime-capabilities` |
| 5 | Alertes personnalisees | implemented | `GET/POST /alert-rules`, Telegram, metric `spot_age` ajoutee |
| 6 | Strategy Engine ameliore | implemented | 6 methodes quant + ensemble + gates + resume GPT compact |
| 7 | Paper trading complet | implemented | journal d'ordres, PnL checkpoints, `GET /trading/paper-report` |
| 8 | Portefeuille virtuel | implemented | `GET /trading/paper-portfolio`, exposition, PnL latent, invalidation proxy |
| 9 | Documentation methodologique | implemented | `reports/strategy_engine_v1.md`, ce rapport, governance export |
| 10 | UX produit | implemented | dashboard + endpoints courts + schema GPT core safe |
| 11 | Multi-assets | scaffolded | `GET /assets/supported`; BTC seul en production, autres assets non exposes comme production |
| 12 | Options avancees | implemented/scaffolded | `GET /options/summary`; Deribit contexte, max pain absent si non fourni |
| 13 | Liquidations reelles | scaffolded/external_required | collecteur WebSocket externe; Worker declare absent si non observe |
| 14 | Live trading securise | blocked_by_credentials | `GET /risk/live-readiness`; live bloque sans secrets Bitget + approbation |

## Nouveaux endpoints operationnels

- `GET /strategies/performance`
  - evalue les signaux stockes contre le dernier mark price Bitget ;
  - cree des checkpoints 1j/3j/7j/30j dans D1 quand ils sont dus ;
  - statut performance : `inferred_mark_to_market`.

- `GET /trading/paper-report`
  - consolide paper orders, PnL, portefeuille virtuel et checkpoints ;
  - ne represente pas un compte exchange reel.

- `GET /market/realtime-capabilities`
  - explique ce qui est temps reel polling et ce qui exige un WebSocket externe.

- `GET /assets/supported`
  - declare BTC comme seul actif production.

- `GET /options/summary`
  - expose le contexte options present dans le dernier run archive.

- `GET /risk/live-readiness`
  - audite les conditions de trading live sans envoyer d'ordre.

## Points qui restent volontairement limites

1. Le Worker gratuit n'est pas un daemon WebSocket permanent.
2. Les liquidations restent `absent` sans collecteur externe.
3. Le live trading reste bloque par defaut.
4. Les non-BTC assets ne doivent pas etre vendus comme supportes.
5. Les performances strategies sont des proxies mark-to-market, pas des executions auditees.

## Politique GPT

Le GPT doit toujours repondre de facon probabiliste.

Pour les strategies :

1. appeler `btcStrategyDeepSummary` pour une reponse client courte ;
2. citer provenance et gates bloquantes ;
3. utiliser `btcStrategyDeepPaperOrder` uniquement si l'utilisateur demande explicitement un paper trade ;
4. ne jamais presenter un `hold` comme un signal de marche, mais comme absence de consensus exploitable.

