# Checklist juridique et plateformes (avant publication)

> Je ne suis pas juriste : ces points sont des risques à faire valider, pas des avis juridiques.

1. **Droits des contenus** : streamer des dramas (coréens, chinois, etc.) suppose des licences de diffusion pour le Bénin/UEMOA.
   Sans contrat, retrait Play Store et risque de poursuites. Prévoir un processus de retrait (DMCA/notification) et conserver les contrats.
2. **TMDB** : les conditions de l'API exigent un accord écrit pour un usage commercial ; un abonnement payant est commercial.
   Obtenir la licence **avant** le lancement, afficher la mention d'attribution (déjà dans l'écran Profil). Les affiches restent la propriété des ayants droit.
3. **Google Play Billing** : les achats de contenus numériques doivent en principe passer par Google Play Billing ; les paiements alternatifs
   (Mobile Money) ne sont permis que dans les pays/programmes éligibles. **Vérifier l'éligibilité du Bénin dans la Play Console** (page « Payments policy »)
   avant d'inscrire MoMo comme moyen de paiement *dans* l'application. Plan B : abonnement vendu sur le web, application « lecteur » (reader app) selon la politique en vigueur.
4. **Marques** : logos MTN MoMo / Moov Money / FedaPay → autorisation ou texte simple sans logo.
5. **Affirmations marketing** : retirer « application N°1 » (invérifiable). Éviter « Dramas HD » comme titre tant que la HD est réservée au VIP ; préférer « Dramas sans pub ».
6. **Captures du store** : elles doivent montrer l'application réelle (pas les visuels IA de la maquette, qui contiennent du texte déformé et des visages générés).
7. **Données personnelles** : politique de confidentialité, mentions légales, base légale, durée de conservation, suppression de compte (exigée par Google Play), déclaration à l'autorité compétente (APDP) si requise.
8. **Mineurs / classification** : renseigner la classification de contenu du store ; les dramas à thèmes adultes exigent un filtrage.
9. **Facturation** : conditions de remboursement, TVA/fiscalité locale, conservation des preuves de paiement (table `payments`).
