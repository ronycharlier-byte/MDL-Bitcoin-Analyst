# Rapport final de validation

Date : 2026-07-17
Branche : `refactor/global-mdl-bitcoin-analyst`
Commit de départ : `2cda4faabf44679a94622a6559e793cc7abe4a49`
Déploiement, publication, release et push : **non effectués**

Ce rapport prépare une revue humaine. Il ne constitue ni une certification de sécurité, ni une autorisation de fusion, ni une autorisation de déploiement, ni un avis financier.

## Résumé

### Avant

Le dépôt comptait 158 fichiers suivis, aucun test automatisé suivi, aucune configuration Ruff/mypy/pytest/Vitest/ESLint/Prettier, plus de quarante variantes GPT/OpenAPI et deux façades monolithiques. Le Worker contenait une capacité d'ordre Bitget réel, Telegram n'authentifiait pas son webhook, FastAPI pouvait échouer en mode ouvert, des mutations Worker étaient accessibles par GET, les contrats Python/TypeScript divergeaient et les seeds Python variaient entre processus.

### Après

- Contrat d'analyse v2 et contrat d'erreur canoniques, validateurs sémantiques Python/TypeScript et fixture JSON commune.
- Exécution Bitget privée supprimée du runtime ; autorité d'exécution `none`, live bloqué et paper explicitement `mock_paper`.
- FastAPI fail-closed, erreurs stables, body/host/proxy/SSRF/timeouts bornés, documentation désactivée par défaut et logs JSON expurgés.
- Worker avec timeouts externes centralisés, IDs de requête, mutations POST admin, GET cache-only et validation des sorties canoniques.
- Webhook Telegram secret, body borné, allowlist propriétaire, rejet des updates anciens et déduplication D1 par `update_id`.
- Seeds SHA-256, conventions de perte positives, diagnostics d'ensemble, plafond corrigé à 35 %, backtest enrichi, incertitudes séparées et qualité de données en cinq dimensions.
- Source GPT canonique minimale sans trading, prompt versionné, variantes historiques conservées mais classées legacy.
- CI Python/Worker/contrats/sécurité, actions SHA-pinnées, dépendances auditées, scan de secrets/historique et SBOM CycloneDX.
- Inventaire exhaustif généré avec rôle, entrées, sorties, dépendances, tests, risque et action pour chaque fichier.

L'architecture reste une migration progressive : `api_server.py` et `cloudflare-worker/src/index.ts` sont encore des façades de compatibilité volumineuses. Le système n'est pas déclaré « production-ready ».

## Architecture résultante

```text
GPT / Telegram / HTTP
        |
Cloudflare Worker (auth, limites, cache, D1, compatibilité)
        |
Contrat canonique + erreurs stables
        |
FastAPI (orchestration, archives, validation)
        |
Quant Python (données, modèles, risques, backtests)
        |
Bitget public / fondamentaux + SQLite
```

Sources d'autorité :

- contrat : `contracts/analysis.schema.json` et `contracts/error.schema.json` ;
- validation Python : `src/contract_validation.py` ;
- validation Worker : `cloudflare-worker/src/contracts.ts` ;
- GPT : `gpt/actions/openapi.yaml` et `gpt/instructions/quant_btc_analyst.system.md` ;
- gouvernance et migration : `docs/MODEL_GOVERNANCE.md` et `docs/MIGRATION_PLAN.md`.

## Modifications principales

| Fichier ou groupe | Modification | Justification | Risque | Validation |
|---|---|---|---|---|
| `api_server.py` | Auth fail-closed, limites de body, TrustedHost, SSRF, timeouts, erreurs/IDs stables, live/ready, canonicalisation et manifeste | Fermer les frontières HTTP et garantir le contrat | Élevé | pytest, OpenAPI, compile |
| `src/contract_validation.py` | Adaptateur v2, statuts, taxonomie et invariants | Source Python canonique | Élevé | schéma, unit/property tests |
| `contracts/*` | Schémas analyse/erreur et fixture commune | Contrat machine-readable partagé | Élevé | Python + TypeScript |
| `src/run_manifest.py` | Hash stable, versions, seeds et bornes temporelles | Traçabilité/reproductibilité | Moyen | pytest + mypy |
| `src/simulation_utils.py` | Seeds SHA-256 | Reproductibilité inter-processus | Élevé | test subprocess + property |
| `src/risk_metrics.py` | Alias VaR/CVaR de perte positive et drawdowns qualifiés | Convention non ambiguë | Élevé | invariants/property tests |
| `src/ensemble_model.py` | Brier/calibration/couverture, shrinkage et plafond robuste | Éviter domination et pondération opaque | Élevé | exemples + Hypothesis |
| `src/backtest.py` | Log loss, ECE, calibration, bootstrap, période et benchmark | Qualifier les résultats hors échantillon | Élevé | pytest |
| `src/confidence_score.py` | Incertitudes séparées et qualité en cinq dimensions | Ne pas masquer l'incertitude | Moyen | pytest |
| `src/logging_utils.py` | Format JSON structuré sans payload sensible | Observabilité expurgée | Moyen | API security tests |
| `cloudflare-worker/src/index.ts` | Suppression live trading, Telegram sécurisé, POST-only, GET cache-only, timeouts, logs, request IDs et policy non prescriptive | Frontière edge sûre et explicite | Critique | tsc, ESLint, Vitest, dry-run Wrangler |
| `cloudflare-worker/src/contracts.ts` | Adaptateur/validateur v2 idempotent | Cohérence Worker/Python | Élevé | fixture commune + Vitest |
| `cloudflare-worker/migrations/0008_telegram_webhook_security.sql` | Table de déduplication Telegram | Idempotence persistante | Élevé | 8 migrations SQLite mémoire |
| `cloudflare-worker/package*.json`, `tsconfig.json`, configs ESLint/Prettier/Vitest | Toolchain stricte et dépendances épinglées | Reproductibilité CI | Moyen | npm ci/check/lint/test/audit |
| `cloudflare-worker/wrangler*.toml` | Retrait des variables privées de trading | Supprimer la capacité, pas seulement la désactiver | Critique | source scan + dry-run |
| `gpt/actions/openapi.yaml` | OpenAPI v2 minimal recherche/archive | Réduire surface et divergence | Élevé | validateur OpenAPI |
| `gpt/instructions/*`, `gpt/legacy-artifacts.json` | Prompt canonique et classement legacy | Gouvernance GPT et anti-injection | Élevé | tests GPT |
| `tests/*`, `cloudflare-worker/test/*` | Tests contrats, invariants, propriétés, API, Worker, Telegram et GPT | Preuve automatisée | Moyen | 27 Python + 6 Worker |
| `scripts/scan_secrets.py` | Scan arbre + historique Git | Prévenir l'ajout de secrets | Élevé | scan local complet |
| `scripts/validate_openapi.py` | Validation canonique et interdiction des mutations GET | Empêcher dérive GPT | Moyen | exécution locale/CI |
| `scripts/generate_repository_inventory.py` | Inventaire exhaustif enrichi | Traçabilité fichier par fichier | Faible | génération + Ruff |
| `scripts/quality_monitor.py`, `scripts/archive_live_run.py` | POST pour les calculs et contrôles de versions v2 | Cohérence avec les routes sûres | Élevé | Ruff/compile ; production non appelée |
| `.github/workflows/ci.yml`, `security.yml` | Lint/tests/audits/secret scan/CodeQL/dependency review/SBOM | Gates de revue reproductibles | Élevé | YAML parse + scan SHA |
| `monitor-api.yml`, `archive-live-run.yml` | Versions v2, actions épinglées et POST explicite | Monitoring sans dérive | Élevé | YAML parse ; non exécuté live |
| `requirements*.txt`, `pyproject.toml`, `.pre-commit-config.yaml` | Versions, Ruff, mypy, pytest, Hypothesis et audits | Toolchain Python contrôlée | Moyen | installation uv + audits |
| `.env.example` | Noms de secrets sans valeur ; aucune clé privée d'exchange | Configuration sûre | Élevé | secret scan |
| `Dockerfile`, `render.yaml` | Utilisateur non-root et auto-deploy désactivé | Déploiement humain | Élevé | parse ; build bloqué par daemon local |
| `README*`, `DEPLOYMENT.md`, `PRIVACY_POLICY.md`, `NO_SLEEP_STATUS.md`, `CREATED_FILES.md` | Architecture, commandes génériques, rétention, sécurité et limites | Documentation alignée | Moyen | revue/scan de chemins |
| `docs/*`, `AUDIT_REPORT.md`, `CHANGELOG.md` | Audit, architecture, contrat, gouvernance, sécurité, Telegram, Worker, GPT, migration, tests et inventaire | Dossier de revue complet | Faible | inventaire + revue |
| Documents collector/legacy concernés | Chemins personnels remplacés par des commandes génériques | Portabilité et confidentialité | Faible | scan de chemins actifs |

La liste exhaustive des fichiers et leur classification est dans `docs/REPOSITORY_INVENTORY.md`. Aucun fichier historique ou archive n'a été supprimé.

## Résultats de validation

### PASS

| Commande | Résultat | Durée observée | Limitation |
|---|---|---:|---|
| `git diff --check` | PASS | 0,2 s | Avertissements CRLF Windows, aucun défaut de whitespace |
| `ruff check ...` | PASS | 0,2 s | Surfaces maintenues ciblées ; monolithes en adoption progressive |
| `ruff format --check ...` | PASS | 0,2 s | 20 fichiers ciblés |
| `python -m compileall -q src scripts api_server.py` | PASS | 0,2 s | Compilation, pas exécution externe |
| `python -m mypy` | PASS | 0,4 s | 3 modules canoniques ciblés |
| `python -m pytest -q` | PASS, 27 tests | 4,64 s | Couverture globale 29 % ; `api_server.py` 28 % |
| `python scripts/validate_openapi.py` | PASS | 0,7 s | OpenAPI GPT canonique |
| Validation OpenAPI générée FastAPI | PASS, 22 chemins | 1,5 s | Schéma interne non exposé par défaut |
| `python scripts/scan_secrets.py --history` | PASS | 3,6 s | Motifs haute confiance ; pas d'analyse entropique/gitleaks |
| `pip-audit --local` | PASS, 0 vulnérabilité connue | 3,9 s | Base de vulnérabilités au moment du test |
| `uv pip install -r requirements-dev.txt` | PASS | 0,2 s | Environnement local Python 3.11 ; CI cible 3.12 |
| `npm ci` | PASS, 185 paquets | 4,3 s | Installation locale |
| `npm run check` | PASS | 1,9 s | TypeScript strict |
| `npm run lint` | PASS | 2,1 s | Worker et tests |
| `npm run format:check` | PASS | 0,7 s | Surfaces TypeScript configurées |
| `npm test` | PASS, 6 tests | 0,55 s | Mocks isolés, pas de D1/Telegram réel |
| `npm audit --omit=dev --audit-level=high` | PASS, 0 vulnérabilité | 0,7 s | Dépendances de production npm |
| Parse JSON/YAML/TOML | PASS, 51/16/4 fichiers | 0,4 s | Validation syntaxique |
| Migrations D1 sur SQLite mémoire | PASS, 8 migrations | 0,2 s | Pas une migration Cloudflare distante |
| Scan des actions GitHub | PASS, toutes SHA 40 caractères | 0,2 s | Les jobs SaaS ne sont pas exécutés localement |
| `wrangler deploy --dry-run` | PASS, 343,37 KiB / gzip 75,46 KiB | 1,8 s | Aucun déploiement ; bindings réels non vérifiés |
| `wrangler types` vers répertoire temporaire | PASS | 2,9 s | Recommande une migration future hors `@cloudflare/workers-types` |
| Génération/parse de 2 SBOM CycloneDX | PASS | < 2 s | Artefacts de revue, non publiés comme release |
| Scan des chemins personnels actifs | PASS | 0,2 s | L'audit initial conserve volontairement la preuve historique redigée |

### Échecs intermédiaires corrigés

- Hypothesis a trouvé un dépassement possible du plafond d'ensemble de 35 %. L'algorithme de redistribution a été corrigé, puis 50 cas générés ont passé.
- La fixture commune a révélé que l'adaptateur TypeScript écrasait le spot d'un payload déjà canonique (`SPOT_MISSING`). L'adaptateur est désormais idempotent et le test partagé passe.
- Un premier Ruff final a trouvé un alias UTC et un ordre d'imports ; les deux ont été corrigés avant le PASS final.
- La première redirection PowerShell du SBOM npm a produit de l'UTF-16. Le fichier a été régénéré en UTF-8 et les deux JSON ont été reparsés.
- Une première commande ad hoc de validation OpenAPI FastAPI avait une erreur de quoting shell ; la commande here-string corrigée a validé les 22 chemins.

### INFRASTRUCTURE_FAILURE

| Commande | Résultat | Cause | Impact |
|---|---|---|---|
| `docker build --pull=false -t mdl-bitcoin-analyst-refactor:validation .` | INFRASTRUCTURE_FAILURE | Docker Desktop/Linux daemon absent (`dockerDesktopLinuxEngine`) | Le Dockerfile n'a pas été construit ; aucun échec applicatif démontré |
| Installation initiale via `pip` | INFRASTRUCTURE_FAILURE initial documenté | Certificat TLS local auto-signé | Résolu sans désactiver TLS en utilisant `uv`; l'installation finale passe |

### NOT_RUN

- Aucun test contre les endpoints, données, secrets, WAF, quotas ou bindings Cloudflare/Render de production.
- Aucun envoi Telegram réel, Stripe, webhook, Supabase, GitHub issue, archive distante ou ordre d'exchange.
- Aucun déploiement Worker/Render/GPT, aucune migration D1 distante, aucun push, commit ou release.
- CodeQL et dependency-review sont configurés mais nécessitent GitHub Actions.
- Pas de test Miniflare/D1 complet, de charge, de chaos réseau ni de benchmark de coût Worker.
- Pas de validation statistique complète de tous les modèles/horizons/régimes ; pas de séparation train/validation/test généralisée, ni tests Kupiec/Christoffersen.
- Pas de test Docker tant que le daemon local n'est pas disponible.

## Compatibilité et migrations

- Version canonique API/Worker : `2.0.0`; contrat : `analysis_contract_v2.0.0`.
- Les alias historiques VaR/CVaR et payloads legacy restent lisibles par adaptateur.
- Les anciens schémas GPT sont conservés et classés `legacy_deprecated`; ils ne sont pas des sources de production canoniques.
- Les routes de calcul Worker n'acceptent plus GET : POST est requis. C'est un changement de comportement volontaire de sécurité.
- Les GET de statut, signaux internes et rapports paper/performance sont cache-only. Les rafraîchissements utilisent des POST admin authentifiés.
- `/trading/approve` retourne toujours `EXECUTION_FORBIDDEN`; les anciens enregistrements live ne peuvent plus être exécutés.
- La migration D1 `0008` est additive. Elle doit être appliquée en staging dans l'ordre numérique avant tout déploiement.
- Render `autoDeploy` est désactivé. Les protections d'environnement et approbations doivent être configurées sur les plateformes.

## Risques et dette restants

1. Les façades FastAPI et Worker restent monolithiques ; un découpage brutal aurait créé trop de risque de régression.
2. La couverture de 29 % est concentrée sur les nouveaux contrats et invariants ; les adaptateurs réseau/données et plusieurs modèles restent peu couverts.
3. Le manifeste de run n'inclut pas encore les corps bruts des fournisseurs ni une durée réelle sur tous les chemins legacy ; il est explicitement limité.
4. Les données fondamentales historiques n'ont pas été migrées vers un adaptateur uniforme champ par champ ; la canonicalisation se fait principalement à la frontière.
5. Le dashboard utilise encore largement `innerHTML`; les valeurs dynamiques principales sont échappées, mais une refonte DOM/CSP complète reste nécessaire.
6. Telegram reste intégré au grand Worker et ne possède pas encore une suite complète de tests de commandes/callbacks/429/état conversationnel avec Miniflare.
7. Le rate limiting Worker en mémoire n'est pas une coordination globale forte entre isolates ; D1/Durable Objects doivent être évalués selon la charge réelle.
8. Les configurations réelles des plateformes, rotations de secrets historiques et politiques de rétention exécutables n'ont pas été vérifiées.
9. Le scan de secrets est heuristique ; activer le secret scanning natif GitHub et effectuer une revue humaine de l'historique avant fusion.
10. La migration vers les types runtime générés par Wrangler et le découpage en packages partagés restent des travaux P1/P2.

## Checklist locale avant fusion ou déploiement

1. Relire le diff, `AUDIT_REPORT.md`, ce rapport et `docs/MIGRATION_PLAN.md`.
2. Faire exécuter CI/CodeQL/dependency-review sur une PR sans secrets de fork.
3. Démarrer Docker Desktop et construire/tester l'image localement.
4. Faire une rotation des identifiants historiquement exposés ou dont la portée est incertaine.
5. Appliquer la migration D1 `0008` sur un environnement de staging sauvegardé.
6. Configurer les secrets via Render/Cloudflare, jamais via Git ou Wrangler vars.
7. Vérifier en staging `/live`, `/ready`, `/version`, `/audit`, auth négative, SSRF, Telegram secret/doublons et contrats quick/deep.
8. Comparer une archive connue et vérifier spot, horizons, quantiles, régimes, VaR/CVaR, versions et fraîcheur.
9. Exiger une approbation humaine distincte pour Render, Worker, migration D1 et configuration GPT.
10. Préparer un rollback vers le commit précédent ; ne jamais réactiver sélectivement l'exécution live.

## Action suivante sûre

Faire relire le diff, l'audit et le rapport de validation avant toute fusion ou tout déploiement.
