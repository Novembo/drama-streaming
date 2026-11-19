> **Mise à jour après revue** : le backend a été corrigé, durci et testé sur SQLite *et* PostgreSQL (22 tests, lint propre, migrations vérifiées).
> Détail des défauts et correctifs : [`docs/CORRECTIFS.md`](docs/CORRECTIFS.md) · configuration et déploiement : [`docs/CONFIG-DEPLOIEMENT.md`](docs/CONFIG-DEPLOIEMENT.md) ·
> prérequis juridiques : [`docs/LEGAL-CHECKLIST.md`](docs/LEGAL-CHECKLIST.md). L'app Flutter et le front web restent des prototypes non vérifiés.
> Tests : `cd backend && pip install --require-hashes -r requirements.txt -r requirements-dev.txt && pytest` (ajouter `TEST_DATABASE_URL=postgresql+psycopg://…` pour PostgreSQL).

# Drama Bénin — MVP

Application de découverte et de streaming de dramas pour le Bénin et la zone UEMOA. Le dépôt contient une API FastAPI, un client Flutter et un prototype web haute fidélité navigable.

## État réel du livrable

- **Prototype web** : navigation, recherche, catégories, détails, favoris, historique local, offres, lecteur simulé. Données éditoriales de démonstration et images distantes non contractuelles.
- **API** : authentification JWT access/refresh, catalogue paginé et filtré, détails/épisodes, favoris, progression, historique, plans, création de checkout FedaPay/CinetPay côté serveur, webhooks authentifiés et vérification canonique des transactions, import des métadonnées TMDB, health checks.
- **Flutter** : application mobile Flutter avec catalogue API, recherche, favoris synchronisés via API, compte/login/inscription, historique et plans VIP et lecteur vidéo avec choix de qualité et reprise de position.
- **Infrastructure** : PostgreSQL 16, Redis (cache catalogue avec repli si Redis indisponible), Docker Compose, Alembic, CI GitHub Actions.
- **Non activé sans comptes et médias** : les transactions nécessitent les clés marchandes et les URL HTTPS publiques; les flux vidéo licenciés/CDN signés, la sélection réelle de pistes audio/sous-titres et les téléchargements hors-ligne nécessitent encore le fournisseur média et des tests sur appareils. Le code refuse de simuler une confirmation de paiement.

## Démarrage local (Windows / Linux / macOS)

1. Installer Docker Desktop (Windows : moteur WSL2) et Git.
2. Copier `backend/.env.example` vers `backend/.env`.
3. Remplacer `JWT_SECRET` par un secret aléatoire fort et modifier `POSTGRES_PASSWORD` dans l'environnement si nécessaire.
4. Depuis la racine : `docker compose up --build`.
5. API : `http://localhost:8000/health/ready`; OpenAPI : `http://localhost:8000/docs` (hors production).
6. Prototype web : `make demo`, puis `http://localhost:5173`.

Sur Windows CMD sans Make : `copy backend\.env.example backend\.env`, puis `docker compose up --build`. Pour le prototype : `py -m http.server 5173 --directory frontend`.

## Backend sans Docker

```bash
cd backend
python -m venv .venv
# Windows CMD: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # Windows CMD; utiliser cp sous Unix
alembic upgrade head
uvicorn app.main:app --reload
```

Pour SQLite local, régler `DATABASE_URL=sqlite:///./drama.db`. PostgreSQL reste la cible recommandée.

## Flutter

```bash
cd mobile
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/api/v1
```

`10.0.2.2` désigne l'hôte depuis l'émulateur Android. Sur un téléphone physique, utiliser l'adresse LAN de l'ordinateur (et adapter CORS / pare-feu). Le catalogue API ne renvoie que les dramas publiés. Les médias et épisodes doivent être ajoutés par un compte admin avant d'apparaître. Le parcours VIP Flutter ouvre le checkout hébergé du prestataire après connexion.

## Administration et contenu

- Créer un compte via `POST /api/v1/auth/register`.
- Attribuer `role='admin'` directement dans PostgreSQL à un compte opérateur autorisé. Ne jamais exposer une route publique d'élévation de privilège.
- Configurer `TMDB_API_KEY` puis utiliser `GET /api/v1/admin/tmdb/search?q=...` et `POST /api/v1/admin/tmdb/import/{tmdb_id}`. L'import reste non publié.
- Ajouter les épisodes via `POST /api/v1/admin/dramas/{drama_id}/episodes`, avec `video_360p` obligatoire et URLs vers des médias dont vous détenez les droits. Publier ensuite le drama via une opération d'administration contrôlée (SQL / futur workflow CMS).

## API principale

| Méthode | Route | Accès |
|---|---|---|
| POST | `/api/v1/auth/register` | Public |
| POST | `/api/v1/auth/login` | Public |
| POST | `/api/v1/auth/refresh` | Refresh token |
| POST | `/api/v1/auth/logout` | Utilisateur |
| GET | `/api/v1/auth/me` | Utilisateur |
| GET | `/api/v1/dramas` | Public, paginé |
| GET | `/api/v1/dramas/{id}` | Public |
| GET | `/api/v1/episodes/{id}` | Utilisateur |
| GET/POST/DELETE | `/api/v1/me/favorites` | Utilisateur |
| PUT | `/api/v1/me/progress` | Utilisateur |
| GET | `/api/v1/me/history` | Utilisateur |
| GET | `/api/v1/subscriptions/plans` | Public |
| POST | `/api/v1/subscriptions/checkout` | Utilisateur, clés prestataire requises |
| POST | `/api/v1/webhooks/fedapay` | Webhook FedaPay signé |
| POST | `/api/v1/webhooks/cinetpay` | Notification CinetPay + vérification API |

## Architecture

```text
Flutter app ── HTTPS/JWT ── FastAPI (modular monolith)
                               ├── PostgreSQL (catalogue, comptes, progression, billing)
                               ├── Redis (cache catalogue, TTL 60 s)
                               ├── TMDB API (métadonnées uniquement)
                               ├── FedaPay/CinetPay (connecteurs serveur, secrets à configurer)
                               └── Video CDN / HLS (fournisseur à choisir)
Prototype web ── données démo locales (ne réalise aucun paiement/stream réel)
```

## Configuration des paiements

- **FedaPay** : renseigner `FEDAPAY_SECRET_KEY`, `FEDAPAY_WEBHOOK_SECRET`, `FEDAPAY_ENVIRONMENT=sandbox|live`. Déclarer dans le tableau de bord le webhook `PUBLIC_API_URL + /api/v1/webhooks/fedapay` et écouter `transaction.approved`, `transaction.declined`, `transaction.canceled`.
- **CinetPay** : renseigner `CINETPAY_API_KEY` et `CINETPAY_API_PASSWORD` pour le compte marchand du pays `BJ`, ainsi que `CINETPAY_ENVIRONMENT=sandbox|live` (ou `CINETPAY_BASE_URL`). Le webhook est `PUBLIC_API_URL + /api/v1/webhooks/cinetpay`; le numéro Mobile Money est requis à l'initialisation.
- Les deux prestataires nécessitent `PUBLIC_API_URL` et `PAYMENT_RETURN_URL` accessibles publiquement en HTTPS. Tester chaque opérateur avec les numéros et scénarios sandbox fournis par le prestataire avant le passage en production.
- Les secrets restent uniquement dans `backend/.env` ou dans un gestionnaire de secrets; ils ne doivent jamais être intégrés dans Flutter ou le prototype web.

## Sécurité / exploitation

- Access JWT 20 minutes; refresh JWT rotatif stocké sous forme de hash et révocable.
- Hashage de mots de passe Argon2 via `argon2-cffi`.
- RBAC opérateur/admin et validation Pydantic `extra='forbid'` sur les entrées critiques.
- Webhooks natifs : FedaPay (`X-FEDAPAY-SIGNATURE`, HMAC-SHA256 horodaté) et CinetPay (`notify_token` hashé + statut relu par API); comparaison en temps constant, montant/devise vérifiés lorsqu'ils sont retournés et traitement idempotent.
- Aucun secret fournisseur dans le dépôt. TLS obligatoire au déploiement, secrets injectés depuis le gestionnaire de secrets.
- Les URLs vidéo doivent être des URLs CDN autorisées, signées et de courte durée; ajouter une allowlist d'hôtes avant d'accepter des médias via un CMS. Le jeton de notification CinetPay est conservé sous forme de hash.
- Sauvegardes PostgreSQL chiffrées, test de restauration, alertes sur erreurs de webhook et de stockage.

## Décisions et limites

1. **Monolithe modulaire FastAPI** plutôt que microservices : cohérent avec le MVP, plus simple à déployer et à opérer.
2. **PostgreSQL source de vérité + Redis cache facultatif** : indisponibilité Redis ne bloque pas le catalogue.
3. **360p par défaut** : le backend expose au plus quatre qualités et place 360p en premier dans le client quand disponible.
4. **Pas de faux streaming ni de faux paiement** : l'application nécessite un hébergeur média, les droits de diffusion, les clés API marchandes et les tests sandbox avant mise en production.
5. **Contrôle de publication** : métadonnées TMDB importées non publiées jusqu'à ce que les épisodes et flux autorisés soient disponibles.
6. **Paiements** : les adaptateurs sont codés mais aucun compte marchand/secret n'est fourni dans le dépôt. Ils doivent être configurés en sandbox, testés avec des numéros de test, puis basculés en live après validation du marchand.

## Vérification

```bash
cd backend
python -m compileall -q app
pytest -q
```

La compilation, les tests, les migrations PostgreSQL et le build Flutter doivent être exécutés dans l'environnement du développeur / CI avant toute release. Les résultats ne sont pas présumés.
