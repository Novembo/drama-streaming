# ADR-001 — Architecture MVP

- **Statut** : accepté pour le MVP.
- **Contexte** : lancement Bénin/UEMOA, équipe réduite, besoin de maîtriser le coût opérationnel et de garder une architecture extensible.
- **Décision** : monolithe modulaire FastAPI, PostgreSQL source de vérité, Redis cache best-effort, Flutter client mobile. Un prototype web statique permet de valider les parcours UX sans se substituer à Flutter.
- **Alternatives** : microservices (isolation mais coût/complexité prématurés); Supabase-only backend (rapidité mais logique métier et paiement plus difficile à maîtriser).
- **Conséquences** : déploiement simple; modules métier séparés; Redis ne bloque pas le catalogue; les connecteurs de paiement et de médias sont des dépendances explicites.
- **Risques** : absence de contenu vidéo licencié et de secrets marchands empêche le streaming et les paiements réels; tests sur devices et migrations doivent précéder release.
