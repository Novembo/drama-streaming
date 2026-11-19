# Skills V12 appliqués

Les instructions ci-dessous ont été extraites de `universal-agent-skills-pack-v12-fixed.zip` fourni pour ce projet. Elles ont guidé les choix d'architecture, de sécurité, de données, de tests, de déploiement, d'expérience mobile et de paiements.

| Skill | Application dans le MVP |
|---|---|
| fullstack-project-delivery | Livrables, structure de dépôt et limites explicites |
| senior-engineering-standards | Séparation des responsabilités, validation, documentation |
| technical-roadmapping | Découpage du périmètre et critères de livraison |
| backend-architecture | Monolithe modulaire FastAPI |
| fastapi-development / fastapi-production-engineering | API versionnée, configuration et health checks |
| api-security / jwt-rbac / python-security-engineering | Argon2, JWT, refresh révocable, RBAC, validation stricte |
| sqlalchemy-development / data-modeling-postgresql / alembic-migrations | Modèles relationnels, contraintes, index et migrations |
| rest-api-design | Contrats REST et pagination/filtrage |
| payments-webhooks / mobile-money-payments-africa | Adaptateurs FedaPay/CinetPay, vérification serveur, idempotence |
| low-bandwidth-offline-first-design | 360p prioritaire, cache Redis et images lazy côté web |
| frontend-design-systems / mockup-to-ui-implementation | Système visuel sombre, composants réutilisables et maquettes |
| mobile-ux-guidelines / mobile-security / mobile-performance / mobile-testing | Navigation mobile, stockage sécurisé, flux vidéo et vérification à compléter sur appareils |
| docker-compose-local-dev / github-actions | Environnement reproductible et CI |

Flutter n'est pas couvert par un skill Flutter spécialisé dans la sélection utilisée; les règles mobiles transversales ont été appliquées et les pratiques propres à Flutter doivent être confirmées avec `flutter analyze`, tests et builds Android/iOS dans un environnement Flutter.
