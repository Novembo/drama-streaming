# Configuration & déploiement (version corrigée)

Remplace le document « Configuration & Déploiement DramaStream Bénin ». Les noms de variables ci-dessous sont **ceux du code**
(`backend/app/core/config.py`) ; modèle prêt à copier : `.env.production.example`.

| Variable | Obligatoire en prod | Remarque |
|---|---|---|
| `ENVIRONMENT` | oui = `production` | absent ⇒ l'API se comporte comme en production (échoue fermé) |
| `DATABASE_URL` | oui | PostgreSQL ; `postgresql+asyncpg://` est converti en `postgresql+psycopg://` |
| `JWT_SECRET` (alias `JWT_SECRET_KEY`) | oui | ≥ 32 caractères aléatoires, sinon l'API refuse de démarrer |
| `ACCESS_TOKEN_MINUTES` (alias `ACCESS_TOKEN_EXPIRE_MINUTES`) | non | 20 par défaut, **≤ 60** en prod (jamais 30 jours) ; `REFRESH_TOKEN_DAYS=30` |
| `FEDAPAY_ENVIRONMENT`, `FEDAPAY_SECRET_KEY`, `FEDAPAY_WEBHOOK_SECRET` | si FedaPay | le secret webhook est exigé dès que la clé est définie |
| `CINETPAY_*` | si CinetPay | |
| `PUBLIC_API_URL`, `PAYMENT_RETURN_URL`, `FRONTEND_ORIGINS` | oui | |
| `API_DOMAIN`, `IMAGE_REPO` | oui (déploiement) | utilisés par Caddy et `deploy.sh` |

Les prix (1 000 / 2 500 / 18 000 XOF) sont définis dans `DEFAULT_PLANS` (`app/api/billing.py`), pas par variables d'environnement : `PRICE_*` n'existe pas.
Postgres et Redis ne doivent **jamais** être exposés sur Internet (réseau Docker interne, pas de nom de domaine public).

## Serveur (1 VPS) et publication
1. Pare-feu : 22, 80, 443 uniquement. Utilisateur `deploy` non-root. Docker + compose. DNS `api.<domaine>` → VPS (Caddy gère le certificat).
2. `/opt/drama-benin` : `docker-compose.prod.yml`, `deploy/`, `.env` (`chmod 600`, jamais versionné).
3. Cron : `15 2 * * * ./deploy/backup.sh` (copier ensuite les sauvegardes hors du serveur).
4. Version : `git tag v1.0.0 && git push --tags` (image GHCR) → GitHub Actions « Deploy (manual) » ou `./deploy/deploy.sh v1.0.0`.
   `deploy.sh` : sauvegarde → pull → migration → redémarrage → attente « healthy » → rollback du code si échec. Une seule instance ⇒ quelques secondes
   d'interruption (pas de « zero-downtime »). Les migrations doivent rester additives ; elles ne sont pas annulées automatiquement.
5. FedaPay : webhook `https://api.<domaine>/api/v1/webhooks/fedapay`, tester d'abord en sandbox.

## Fiche Play Store
Titre « DramaStream Bénin - Sans pub » (28 car.), sans « N°1 » (invérifiable) ni « HD » (la HD est payante). Voir `docs/LEGAL-CHECKLIST.md`.
