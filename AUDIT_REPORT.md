# Audit initial — MDL Bitcoin Analyst

Date de l'audit : 2026-07-17
Branche de travail : `refactor/global-mdl-bitcoin-analyst`
Commit de référence : `2cda4faabf44679a94622a6559e793cc7abe4a49`
Fichiers suivis au départ : 158
Portée : moteur Python, API FastAPI, Worker Cloudflare, Telegram, GPT Actions, stratégie, paper trading, stockage, CI/CD, archives et documentation.

Cet audit prépare une revue humaine. Il ne constitue ni une validation de production, ni une autorisation de fusion ou de déploiement.

## État actuel

Le dépôt est un monorepo logique mais non structuré : le moteur quantitatif Python est réparti sous `src/`, l'API publique est concentrée dans `api_server.py` (environ 2 900 lignes), et l'essentiel des fonctions Worker, Telegram, stratégie, stockage et trading se trouve dans `cloudflare-worker/src/index.ts` (environ 7 900 lignes). Le système expose deux implémentations partiellement divergentes des calculs, plusieurs contrats de réponse, deux stockages SQLite locaux, un stockage D1, des archives Git, et plus de quarante variantes OpenAPI.

La politique déclarée est probabiliste et Bitget-only pour le spot live. Les sorties utilisent déjà des avertissements, de la provenance, des identifiants d'archive, des métriques de risque et des statuts de données. Cependant, ces garanties ne sont pas portées par un contrat canonique validé aux frontières ; elles reposent sur des dictionnaires construits séparément dans Python, TypeScript, les schémas GPT et les documents de gouvernance.

## Forces

- Les dépendances Python de production sont épinglées et TypeScript est en mode `strict`.
- Les requêtes de données de marché Python ont généralement des délais d'attente bornés.
- Les écritures SQLite/D1 utilisent majoritairement des paramètres liés.
- Les runs multi-frame Python partagent un snapshot spot et un `archive_id`.
- Les métriques VaR/CVaR utilisent une convention de perte positive.
- Les drawdowns pathwise sont distingués par moyenne, médiane, P95 et pire échantillon.
- Les archives externes sont compactes et n'embarquent pas les tableaux de simulation bruts.
- Le monitoring GitHub déduplique déjà ses issues d'alerte.
- Aucun secret réel n'a été détecté dans l'arbre courant ni par le scan de motifs sur les 100 commits visibles. `gitleaks` n'est pas installé ; cette conclusion reste donc limitée à un scan heuristique avec valeurs toujours expurgées.

## Risques critiques et élevés

### SEC-001 — Critique — Capacité d'exécution réelle incompatible avec la gouvernance

Localisation initiale : `cloudflare-worker/src/index.ts`, fonctions `approveTradeOrder`, `canApproveLiveTrade`, `placeBitgetSpotOrder`, routes `/trading/propose` et `/trading/approve`.

Preuve : le Worker peut signer puis envoyer `POST /api/v2/spot/trade/place-order` à Bitget lorsque des secrets et certains flags sont configurés.

Impact : le produit possède une autorité d'exécution réelle alors que le mandat impose `execution_authority = none` et `live_trading_default = blocked`. Une erreur de configuration ou un contournement des contrôles applicatifs pourrait créer un ordre réel.

Correction prévue : retirer toute signature et tout appel d'ordre réel du runtime ; conserver uniquement un journal `mock_paper`. Les anciennes routes retourneront une erreur stable de compatibilité indiquant que l'exécution réelle est interdite.

### SEC-002 — Critique conditionnelle — Webhook Telegram falsifiable

Localisation initiale : `cloudflare-worker/src/index.ts`, route `/telegram/webhook`, fonctions `setupTelegramWebhook` et `handleTelegramWebhook`.

Preuve : aucun `secret_token` n'est transmis à `setWebhook` et le header `X-Telegram-Bot-Api-Secret-Token` n'est pas validé. Le contrôle d'autorisation se limite au `chat_id` contenu dans le JSON fourni par l'appelant.

Impact : un tiers pouvant deviner ou obtenir le chat ID peut falsifier une update Telegram. Dans la configuration live historique, une fausse commande d'approbation pouvait atteindre le chemin d'exécution Bitget.

Correction prévue : secret de webhook obligatoire, comparaison en temps constant, body borné, POST uniquement, allowlist du chat propriétaire, déduplication persistante par `update_id`, rejet stable des payloads invalides.

### SEC-003 — Élevé — Authentification FastAPI en mode fail-open

Localisation initiale : `api_server.py`, `require_api_key`.

Preuve : si `QUANT_API_KEY` est absent, la dépendance retourne sans authentifier. Des routes de création de client, checkout, abonnement d'alerte, historique et calcul restent alors publiques.

Impact : exposition involontaire de mutations, quotas, métadonnées et appels coûteux après un déploiement incomplet.

Correction prévue : distinguer explicitement les routes publiques et administratives ; refuser les mutations sensibles si le secret requis est absent ; préserver les endpoints d'analyse publique avec limites documentées si ce mode est choisi.

### SEC-004 — Élevé — SSRF via abonnements webhook

Localisation initiale : `api_server.py`, `AlertSubscriptionRequest`, `create_alert_subscription`, `send_json_webhook`.

Preuve : une URL HTTPS arbitraire est persistée puis appelée côté serveur. Le schéma seul ne bloque ni loopback, ni IP privées, ni metadata cloud, ni redirections.

Impact : accès réseau côté serveur vers des destinations internes et exfiltration de métadonnées de run.

Correction prévue : désactiver les webhooks arbitraires par défaut, imposer une allowlist de destinations configurée, interdire les adresses privées/link-local, désactiver les redirections et conserver des timeouts courts.

### SEC-005 — Élevé — Mutations Worker accessibles en GET et sans frontière d'administration

Localisation initiale : `cloudflare-worker/src/index.ts`, notamment `/ops/test-alert`, `/realtime/collect`, `/deep-jobs/process`, `/trading/cleanup-paper-tests`, `/trading/paper-order`, `/trading/propose`, `/trading/approve`, `/strategies/paper-order`, `/strategies/propose-trade`.

Impact : CSRF-like triggers, robots/caches déclenchant des effets, déni de service, altération de l'état D1 et confusion entre lecture et action.

Correction prévue : POST uniquement pour toute mutation, authentification d'administration explicite, erreurs `METHOD_NOT_ALLOWED` et tests de non-régression.

## Risques moyens et faibles

- **SEC-006 — Moyen :** le rate limiting Python fait confiance à `X-Forwarded-For` sans frontière de proxy vérifiée ; il est contournable.
- **SEC-007 — Moyen :** CORS Worker est globalement `*`, sans politique par route ; les headers de sécurité et la taille maximale du body ne sont pas centralisés.
- **SEC-008 — Moyen :** la documentation FastAPI interactive est exposée par défaut et aucun `TrustedHostMiddleware` n'est visible. Une protection à l'edge reste à vérifier.
- **SEC-009 — Moyen :** les proxys Worker vers Render n'utilisent pas le helper de timeout déjà présent.
- **SEC-010 — Moyen :** plusieurs erreurs renvoient `str(exc)` au client, ce qui peut divulguer des détails internes.
- **SEC-011 — Faible à moyen :** le secret de hash client possède un fallback constant (`quant_btc_default_client_hash_secret`).
- **SEC-012 — Moyen :** `render.yaml` contient `autoDeploy: true`, contraire à l'approbation humaine obligatoire.
- **SEC-013 — Moyen :** le dashboard Python injecte des données d'API via `innerHTML`; une donnée externe malveillante pourrait produire du HTML actif.

## Incohérences de contrat et de données

- Les statuts Python historiques sont `real`, `mock`, `missing`, tandis que la cible impose `real`, `inferred`, `absent`, `mock`, `mock_paper`, `unknown`, `stale`, `ambiguous_status`.
- Le contrat canonique demandé (`status`, `asset`, `response_type`, `archive_id`, `analysis_id`, `provenance`, `data_inventory`, `frames`, `backtests`, `alerts`, `warnings`, `limitations`) n'existe pas.
- Les métriques Python s'appellent `var_95`/`cvar_95`; la cible demande des noms non ambigus `var95_loss`/`cvar95_loss`. Une phase de compatibilité est nécessaire.
- Les régimes `bull`, `bear` et `range` ne forment pas toujours une partition ; le résidu n'est pas garanti par validation backend.
- Les erreurs sont des chaînes, des `HTTPException.detail` variables ou des objets Worker ad hoc ; aucune taxonomie stable n'est partagée.
- Le cache, la fraîcheur et la provenance sont présents sous plusieurs formes incompatibles.
- Les comparaisons de runs ne vérifient pas systématiquement la version de schéma, la version de modèle, les horizons et la compatibilité des définitions.
- Les données fondamentales sont agrégées en une ligne dont le statut peut devenir globalement ambigu ; les statuts et unités par champ ne sont pas uniformes.

## Dette quantitative

- `seed_for()` utilise `hash()` de Python, randomisé entre processus : un même run logique n'est pas reproductible d'un processus à l'autre.
- Les seeds, hashes d'entrée, versions de dépendances, bornes temporelles et temps d'exécution ne sont pas rassemblés dans un manifeste de run rejouable.
- La pondération d'ensemble multiplie inverse de Brier, inverse de calibration et hit rate sans plafonnement robuste ni justification détaillée ; elle peut être dominée par une métrique quasi nulle.
- Le backtest est walk-forward mais ne sépare pas explicitement train/validation/test et ne calcule pas log loss, ECE, tests de Kupiec/Christoffersen ni intervalles bootstrap.
- `walk_forward.py` n'est qu'un alias mince ; les conventions et périodes ne sont pas documentées par artefact.
- Le confidence score agrège des dimensions hétérogènes et peut masquer l'incertitude de modèle, de régime, de qualité et d'échantillonnage.
- `position_sizing.py` produit des fractions proches d'une aide à la décision prescriptive ; ces valeurs doivent rester internes ou être qualifiées `information_only`.
- Les implémentations Python et TypeScript des simulations et risques divergent et ne partagent aucune fixture de contrat.

## Dette de tests et CI

État initial : aucun dossier de tests suivi, aucun `pytest`, `ruff`, `mypy`, `vitest`, ESLint ou Prettier configuré. La CI ne fait qu'une compilation Python et un smoke test `/health`; elle n'exécute pas `tsc`, malgré le script local existant.

Résultats initiaux :

| Commande | Résultat | Durée | Limitation |
|---|---|---:|---|
| `npm ci` | PASS | installation terminée | dépendances npm uniquement |
| `npm run check` | PASS | 1.1 s | vérification TypeScript statique seulement |
| `python -m compileall -q src scripts api_server.py` | PASS | 0.17 s | syntaxe, sans imports runtime |
| `pip install -r requirements.txt` | INFRASTRUCTURE_FAILURE | 16.6 s | certificat TLS local auto-signé ; aucune désactivation TLS appliquée |
| `uv pip install --python .venv/Scripts/python.exe -r requirements.txt` | PASS | 5.44 s | installation locale non versionnée |
| smoke test FastAPI `GET /health` | PASS | 5.42 s | ne couvre ni calcul, ni stockage, ni réseau |

## Dette documentaire et GPT

- `README.md` et `NO_SLEEP_STATUS.md` contiennent des chemins personnels `C:\Users\ronyc\...`.
- Plusieurs documents déclarent des versions de Worker/API anciennes par rapport au code.
- Plus de quarante schémas GPT Action sont suivis, avec des versions de `1.15.x` à `1.30.x`, des operation IDs et des domaines divergents.
- Les bundles `governance_export/` et `gpt_custom_upload_bundle/` dupliquent plusieurs fichiers sans générateur canonique.
- Des variantes GPT exposent encore des opérations de trading/proposition incompatibles avec la gouvernance cible.
- La politique de confidentialité ne décrit pas suffisamment le chat ID, le username, les commandes Telegram, les cibles d'alertes, les clés client, les durées de rétention et la suppression.

## Appels réseau cartographiés

Marché et fondamentaux : Bitget REST/WebSocket, Farside, Blockchain.com, DeFiLlama, Stooq, FRED, U.S. Treasury et Deribit (contexte options). CoinGecko existe comme fallback conditionnel désactivé par défaut.
Produit : Stripe, Telegram, Supabase REST, webhooks d'archive/alertes, Render et GitHub raw.
Le Worker contient également l'appel privé Bitget d'ordre spot identifié par SEC-001.

## Stockages cartographiés

- SQLite quant : `data/quant_model.db` (`market_prices`, `technical_features`, `fundamental_features`, `risk_metrics`, `model_runs`, `simulation_results`, `backtest_results`).
- SQLite API : `data/api_runtime.db` (`rate_limit_events`, `response_cache`, `run_archive`, `api_clients`, `usage_events`, `alert_subscriptions`).
- Cloudflare D1 : runs, usage, clients, alertes, ops, locks, snapshots, deep jobs, règles utilisateur, sessions Telegram, journal paper/trading, performance stratégie et portefeuille virtuel.
- Fichiers : rapports, archives runtime ignorées, archives Git suivies, JSONL externes, corpus et artefacts de backtest/simulation.
- Stockages externes optionnels : Supabase et webhook d'archive.

Aucune politique de rétention exécutable et commune n'est définie. Les archives historiques suivies ne seront pas supprimées pendant cette mission.

## Secrets attendus

Les valeurs ne sont jamais reproduites ici. Les noms attendus comprennent : `QUANT_API_KEY`, `CLIENT_KEY_HASH_SECRET`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_WEBHOOK_SECRET`, `REALTIME_INGEST_SECRET`, `BITGET_API_KEY`, `BITGET_API_SECRET`, `BITGET_API_PASSPHRASE`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`, `ALERT_EMAIL_WEBHOOK_URL`, `OPS_ALERT_WEBHOOK_URL` et `EXTERNAL_ARCHIVE_WEBHOOK_URL`.

## Plan d'intervention

1. Bloquer définitivement l'exécution réelle, authentifier Telegram, interdire les mutations GET et durcir les frontières réseau.
2. Introduire un JSON Schema canonique, une taxonomie d'erreurs et des validateurs Python/TypeScript avec fixtures communes.
3. Stabiliser reproductibilité, risques, ensemble, provenance et statuts par champ sans casser les anciens alias.
4. Ajouter une couche de compatibilité progressive autour des monolithes plutôt qu'un déplacement massif immédiat.
5. Ajouter tests unitaires, propriétés, contrats, sécurité et CI Python/Worker.
6. Définir une source GPT canonique et classer les anciennes variantes comme artefacts de compatibilité, sans suppression silencieuse.
7. Finaliser les documents d'architecture, données, gouvernance, Workers, Telegram, GPT, sécurité, migration et validation.

## Éléments non vérifiés à ce stade

- Configuration réelle du compte Cloudflare, secrets déployés, WAF, routes, quotas et approvals.
- État des endpoints de production et intégrité des données live ; aucun appel live n'est requis pour l'audit statique initial.
- Paramétrage réel Render/Fly/Railway/Cloud Run et protection de leurs environnements.
- Droits exacts des clés Bitget historiques.
- Contenu d'éventuels secrets hors Git ou déjà supprimés avant l'historique visible.
