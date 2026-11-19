# État de livraison et critères d'acceptation

## Inclus dans le dépôt

- [x] API FastAPI versionnée, OpenAPI, health live/ready.
- [x] Authentification email/mot de passe, Argon2, access JWT, refresh token rotatif/révocable.
- [x] Catalogue public, recherche, filtre catégorie, détail et épisodes.
- [x] Favoris, historique et progression de lecture côté API.
- [x] Limitation des flux gratuits à 360p; qualités HD disponibles avec abonnement VIP actif.
- [x] Plans hebdo/mensuel/annuel en XOF.
- [x] Adaptateur de création checkout FedaPay et vérification de webhook signée.
- [x] Adaptateur CinetPay pays BJ, notify_token, vérification de statut par API.
- [x] Activation d'abonnement côté serveur après vérification du paiement.
- [x] Import de métadonnées TMDB en brouillon non publié.
- [x] PostgreSQL, migrations Alembic, cache Redis best-effort.
- [x] Docker Compose, CI GitHub Actions, documentation d'installation.
- [x] Prototype web navigable : recherche, filtres, détail, favoris, historique, lecteur simulé et offres.
- [x] Maquettes visuelles haute fidélité incluses.
- [x] Source Flutter : catalogue, recherche, favoris API, historique API, authentification, plans/checkouts, lecture vidéo, choix qualité et sauvegarde de progression.

## Bloquants externes avant une vraie mise en production

- [ ] Renseigner les clés FedaPay sandbox/live, le secret webhook FedaPay et configurer les événements `transaction.approved`, `transaction.declined`, `transaction.canceled`.
- [ ] Renseigner les credentials CinetPay émis pour le pays `BJ` et tester les notifications de paiement.
- [ ] Configurer `PUBLIC_API_URL` et `PAYMENT_RETURN_URL` en HTTPS, accessibles depuis les prestataires.
- [ ] Fournir les droits de diffusion, URLs HLS/DASH ou stockage/CDN, flux 360p/480p/720p/1080p et vignettes.
- [ ] La sélection effective des pistes audio et sous-titres doit être raccordée à un moteur vidéo prenant en charge les pistes du manifeste; `video_player` seul ne réalise pas encore cette sélection.
- [ ] Téléchargement hors-ligne : stockage chiffré, droits, expiration et politique de licences à implémenter avant d'activer cette promesse.
- [ ] Ajouter une interface d'administration/CMS pour éditer et publier les contenus sans SQL manuel.
- [ ] Définir les mentions légales, politique de confidentialité, CGU, politique de remboursement et conservation des données.
- [ ] Exécuter les tests sandbox de bout en bout et les tests sur appareils Android/iOS réels; Flutter SDK et Docker n'étaient pas disponibles dans l'environnement de génération.
- [ ] Revue de sécurité indépendante, sauvegardes/restauration et observabilité avant ouverture publique.

## Vérifications exécutées dans l'environnement de génération

- [x] `python -m compileall -q backend/app backend/tests`
- [x] `python -m pytest -q` — 11 tests réussis, dont authentification, RBAC, favoris, progression, restrictions de qualité et webhooks mockés.
- [x] `alembic upgrade head` sur SQLite de vérification.
- [x] `node --check frontend/app.js`
- [ ] Build Flutter / `flutter analyze` — Flutter SDK absent.
- [ ] Docker Compose build et smoke test PostgreSQL/Redis — Docker absent.
- [ ] Parcours navigateur automatisé — Chromium/Playwright bloqué par l'environnement d'exécution.
