# MDL Bitcoin Analyst - Quant BTC Model

Infrastructure quantitative probabiliste pour analyser Bitcoin avec un backend live, une API publique, une gouvernance GPT Custom et une logique de risque explicite.

Le système ne produit jamais de certitude ni de prix garanti. Il produit des distributions, des probabilités, des scénarios et des mesures de risque.

## Statut Actuel

- Backend Render : moteur Python complet.
- Worker Cloudflare : endpoint public no-sleep.
- Source marché obligatoire : Bitget.
- Analyse multi-frame : 7, 30, 90, 180 et 365 jours.
- Audit avant analyse : actif.
- Archivage des runs : actif.
- Monitoring qualité GitHub Actions : actif.
- Gouvernance GPT Custom : incluse.
- Licence : propriétaire, usage commercial soumis à autorisation écrite.

## Endpoint Public

```text
https://quant-btc-model-lite.mdl-bitcoin-analyst.workers.dev
```

Endpoints principaux :

```text
GET /health
GET /version
GET /status
GET /audit
GET /run?asset=BTC
GET /multi-run?asset=BTC
GET /latest
```

Endpoints de diagnostic ajoutés :

```text
GET /history?asset=BTC
GET /compare-runs?asset=BTC
GET /alerts?asset=BTC
GET /backtest-summary?asset=BTC
GET /dashboard
GET /pdf-report
GET /billing/plans
POST /billing/checkout
POST /clients/register
GET /clients/me
GET /usage-summary
POST /alerts/subscribe
GET /alerts/subscriptions
```

Flux recommandé pour un GPT Custom :

1. Appeler `auditQuantBtcLiteSystem`.
2. Si l'audit est OK, appeler `runQuantBtcMultiFrame`.
3. Utiliser un seul `archive_id` par analyse.
4. Citer les `model_run_id` complets.
5. Afficher les heures en UTC et Europe/Paris.
6. Distinguer `real`, `inferred`, `absent` et `mock`.

## Ce Que Le Modèle Produit

- Distribution P10 / médiane / P90.
- Probabilité de rendement positif.
- Probabilités de seuils haussiers et baissiers.
- VaR 95 / 99.
- CVaR 95 / 99.
- Drawdown simulé.
- Régimes bull / bear / range / transition.
- Stress tests.
- Confidence score.
- Statut des données utilisées.

Ajouts de robustesse :

- Gate de fraîcheur : le spot Bitget stale ou absent bloque le run live.
- Erreur Monte Carlo sur les probabilités.
- Stabilité multi-seed.
- Drawdown clarifié : moyenne/expected, médiane, P95 et pire échantillon simulé.
- Comparaison de runs archivés.
- Alertes : VaR élevée, confidence faible, transition de régime, données stale.
- Dashboard web simple et export PDF.
- Contexte premium best-effort : carnet Bitget, options/vol implicite, tendances ETF et explainability heuristique.

Couche produit ajoutee :

- Cles client pour quotas et logs d'usage.
- Plans Free, Analyst et Pro exposes par l'API.
- Checkout Stripe actif seulement si `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ANALYST` et `STRIPE_PRICE_PRO` sont configures.
- Stockage durable externe via `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` ou `EXTERNAL_ARCHIVE_WEBHOOK_URL`.
- Alertes webhook, Discord, Telegram ou email en best-effort.
- Backtests visibles : hit rate, Brier, calibration, couverture P10/P90, breaches VaR et benchmark random walk.

## Gouvernance Importante

Règles obligatoires :

- Ne jamais présenter une prédiction certaine.
- Ne jamais inventer de données absentes.
- Ne jamais mélanger deux `archive_id` dans une même analyse.
- Ne jamais remplacer Bitget par un autre exchange.
- Tout chiffre précis doit avoir une provenance.
- Si le confidence score est inférieur à 50/100, toute conclusion directionnelle doit être qualifiée de fragile.
- Les régimes doivent totaliser 100 % avec un bucket `non-classified / transition` si nécessaire.

## Exemple De Prompt GPT Custom

```text
Fais une analyse BTC live complète. Appelle d'abord auditQuantBtcLiteSystem. Si l'audit a des blockers, arrête et explique. Sinon appelle runQuantBtcMultiFrame pour BTC 7/30/90/180/365. Cite archive_id, run_id complets, spot Bitget, heures UTC et Europe/Paris, versions, statuts real/inferred/absent, VaR/CVaR, régimes et limites. Ne donne aucune certitude.
```

## Données Et Sources

Sources live possibles :

- Prix spot BTCUSDT : Bitget.
- Funding rate : Bitget.
- Open interest : Bitget.
- Liquidations : Bitget WebSocket si observation disponible, sinon absent.
- ETF flows : Farside Investors si accessible.
- Hash rate : Blockchain.com si accessible.
- Exchange reserves : Bitget Proof of Reserves si accessible.
- Stablecoins : DeFiLlama si accessible.
- DXY / Nasdaq : Stooq si accessible.
- Taux US : FRED ou U.S. Treasury si accessible.

Les variables fondamentales peuvent être partielles. Les sorties de simulation et de risque sont `inferred`.

## Installation Locale

Depuis le dossier du projet :

```powershell
python src/main.py --asset BTC --horizon 365 --simulations 200000 --model ensemble
```

Analyse multi-frame via API locale ou déployée :

```json
{
  "asset": "BTC",
  "horizons": [7, 30, 90, 180, 365],
  "simulations": 2000,
  "model": "ensemble",
  "skip_corpus": true,
  "no_online": false
}
```

## Bundle GPT Custom

Les fichiers à utiliser pour un GPT Custom sont dans :

```text
gpt_custom_upload_bundle/
```

Schéma Action recommandé :

```text
gpt_custom_upload_bundle/gpt_action_openapi.cloudflare.deployed.yaml
```

Fichiers Knowledge recommandés :

- `gpt_instructions.md`
- `governance_rules.md`
- `model_card.md`
- `data_dictionary.md`
- `claims_registry.md`
- `source_manifest.md`
- `output_policy.md`
- `GPT_CUSTOM_SMOKE_TEST.md`

Ne pas uploader les bases SQLite, les données massives, les arrays de simulation, les logs ou `node_modules`.

## Limites

- Le modèle reste probabiliste.
- Les données fondamentales peuvent être incomplètes.
- Les liquidations peuvent être absentes si Bitget ne pousse pas d'événement pendant la fenêtre observée.
- Les backtests sont des diagnostics, pas une preuve de performance future.
- Les marchés crypto peuvent changer brutalement de régime.
- Le système n'est pas un conseil financier.

## Licence

Ce projet est propriétaire et visible pour revue/évaluation seulement.

Usage commercial, revente, produit GPT, API hébergée, SaaS, client work, redistribution ou déploiement en production nécessitent une autorisation écrite préalable.

Voir [`LICENSE`](LICENSE).
