# Quant BTC User Onboarding

## Commandes Telegram

- `/summary`: resume client court.
- `/status`: sante operationnelle.
- `/quick`: dernier run quick.
- `/deep`: dernier run deep.
- `/deep_run`: lance un job deep en file.
- `/alerts`: alertes modele detaillees.
- `/strategy_deep`: signal strategie complet.
- `/paper_strategy`: cree un paper trade si les gates passent.
- `/trade_orders`: derniers ordres paper/proposal.
- `/mute 60`: coupe Telegram pendant 60 minutes.

## Lire les sorties

- `P(up)`: probabilite simulee de rendement positif.
- `VaR95`: seuil ou commencent les 5% pires scenarios simules.
- `CVaR95`: perte moyenne dans les scenarios pires que la VaR95.
- `confidence < 50`: conclusion directionnelle fragile.
- `transition elevee`: regime de marche peu lisible.
- `hold/no-trade`: les gates ne valident pas un biais operationnel robuste.

## Ce que le GPT peut faire

- Analyser BTC avec provenance.
- Surveiller alertes.
- Expliquer les risques.
- Proposer des paper trades.
- Comparer le dashboard, les backtests et les strategies.

## Ce que le GPT ne fait pas

- Il ne donne pas de certitude.
- Il ne donne pas de conseil financier.
- Il ne trade pas reellement sans activation live, secrets Bitget et approbation explicite.
- Il n'invente pas une donnee absente.
