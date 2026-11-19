# Correctifs appliqués après revue

Chaque ligne = un défaut **constaté en exécutant le code**, la correction, et le test qui le garde.
Les tests tournent sur SQLite **et** sur PostgreSQL (`TEST_DATABASE_URL`), 22 tests au total.

| # | Défaut constaté | Correctif | Garde-fou |
|---|---|---|---|
| 1 | Filtre par catégorie → **HTTP 500 sur PostgreSQL** (colonne `JSON` sans opérateur de contenance) ; sur SQLite il dégradait en `LIKE` et ratait les drames à plusieurs catégories | Migration `0002_hardening` : `JSONB` + index GIN ; requête adaptée au dialecte (`@>` sur PG, `json_each` sur SQLite) | `test_category_filter_works_on_the_production_engine` |
| 2 | Les tests ne tournaient que sur SQLite (les clés étrangères n'y sont pas appliquées) | `tests/support.py` : mêmes tests sur PostgreSQL via `TEST_DATABASE_URL`, CI avec service Postgres | job `backend` de la CI |
| 3 | `JWT_SECRET_KEY` (nom du document de déploiement) **ignoré** → secret par défaut public actif, jetons falsifiables | alias accepté ; en production le démarrage échoue si secret faible/par défaut, access token > 60 min, base non PostgreSQL | `test_production_rejects_default_secret…`, `test_jwt_secret_key_alias_is_honoured` |
| 4 | `ENVIRONMENT` absent ⇒ mode développement | défaut = `production` (échoue fermé) ; `docker-compose.yml` dev positionne `ENVIRONMENT=development` | `test_missing_environment_fails_closed` |
| 5 | `DATABASE_URL=postgresql+asyncpg://…` (document) incompatible avec le moteur synchrone psycopg | URL normalisée automatiquement vers `postgresql+psycopg://` | `test_production_rejects_…` (assertion d'URL) |
| 6 | **Aucune limitation** des tentatives de connexion (25 échecs acceptés) | Limiteur Redis (20/min/IP + 5/min/e-mail sur le login, inscription, refresh) ; temps de réponse égalisé si l'e-mail est inconnu | `test_login_attempts_are_throttled`, `test_unknown_and_wrong_password_look_identical` |
| 7 | Réutilisation d'un refresh token déjà utilisé non détectée | `family_id` par session de connexion ; rejeu ⇒ révocation de toute la famille | `test_refresh_rotation_and_reuse_revokes_the_whole_family` |
| 8 | Recherche : `%` et `_` interprétés comme jokers | échappement + `ESCAPE` | `test_search_treats_like_wildcards_literally` |
| 9 | Webhook FedaPay pour une transaction inconnue ⇒ 404 ⇒ relances pendant des jours | réponse 200 « ignored » | `test_fedapay_webhook_for_unknown_transaction…` |
| 10 | Un renouvellement écrasait la période restante | la nouvelle période s'empile après l'abonnement actif | `test_renewals_stack_after_the_current_period` |
| 11 | `GET /subscriptions/plans` écrivait en base à chaque appel | amorçage seulement si la table est vide | — |
| 12 | Pas d'en-têtes de sécurité, erreurs 500 non maîtrisées | `nosniff`, `X-Frame-Options`, `no-store`, HSTS en prod ; handler 500 générique | `test_security_headers_present` |
| 13 | CI rouge (`ruff` : 76 erreurs), sans Postgres, sans scan | code reformaté (lisible), `ruff.toml`, CI : lint + tests SQLite/PG + migrations + `bandit` + `pip-audit` + `gitleaks` + `trivy` + image | `.github/workflows/ci.yml` |
| 14 | Dépendances non verrouillées (pytest en prod), Dockerfile mono-étape sans hash | `requirements.in/.txt` avec **hash** (`--require-hashes`), `requirements-dev`, image multi-étapes uid 10001, healthcheck | `backend/Dockerfile` |
| 15 | Déploiement « zero-downtime » sans sauvegarde ni retour arrière | `deploy/deploy.sh` (sauvegarde → migration → santé → rollback du code), `backup.sh`, compose prod (Caddy HTTPS, réseau interne, lecture seule) | — |

## Non corrigé (volontairement ou faute de moyens de vérification)
- **App Flutter** (`mobile/`, un seul fichier) et **front web** (`frontend/`, données en dur) : inchangés. Un client Flutter complet et testé en
  analyse statique existe dans l'autre livrable (`drama-benin-mvp-v2.zip`), mais il parle à *son* API (routes différentes de `/me/favorites`, `/me/progress`…).
- `docs/skills-applied/` : copies de fiches génériques, conservées telles quelles (elles n'ont pas de valeur d'application).
- Rejeu complet sur le **sandbox FedaPay / CinetPay** à faire avant la production ; Docker non exécuté dans l'environnement de revue.
- Voir `docs/LEGAL-CHECKLIST.md` (licence TMDB commerciale, droits des contenus, Google Play Billing).
