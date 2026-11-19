# Contrats des prestataires de paiement

## FedaPay

- Création côté serveur : `POST /v1/transactions`, puis `POST /v1/transactions/{id}/token`.
- Environnement sandbox : `https://sandbox-api.fedapay.com/v1`; live : `https://api.fedapay.com/v1`.
- Devise `XOF`; la référence interne est transmise en `custom_metadata.merchant_reference`.
- Webhook : `X-FEDAPAY-SIGNATURE`, format `t=<unix>,s=<hex>`. Signature HMAC-SHA256 de `timestamp + '.' + raw_body`, avec secret propre à l'endpoint; fenêtre anti-rejeu 300 secondes.
- À l'événement `transaction.approved`, relire la transaction par API et vérifier statut `approved`, montant et devise avant activation.

## CinetPay

- Le client mobile ne reçoit jamais les clés marchandes. Les credentials sont propres au compte pays `BJ`.
- Authentification : `POST /v1/oauth/login`; initialisation : `POST /v1/payment`; statut : `GET /v1/payment/{identifier}`.
- Sandbox `https://api.cinetpay.net`; production `https://api.cinetpay.co` (la clé `sk_test_` / `sk_live_` peut déterminer la base).
- Référence marchand limitée à 30 caractères; le projet génère `DRM` + 24 caractères hexadécimaux.
- Le `notify_token` retourné à l'initialisation est stocké sous forme de hash SHA-256. À la notification, comparaison en temps constant, puis lecture du statut canonique auprès de CinetPay avant activation.
- La référence marchand doit correspondre; montant et devise sont comparés lorsqu'ils sont présents dans la réponse de vérification.

## Déploiement

1. Créer les clés sandbox et les secrets webhook depuis les tableaux de bord marchands.
2. Renseigner les variables dans un coffre de secrets (ou `.env` local non versionné).
3. Déployer l'API derrière HTTPS et configurer les URL publiques de notification.
4. Tester succès, annulation, refus, notification répétée, notification mal signée, montant incorrect et délai d'expiration.
5. Ne passer en live qu'après validation marchande et tests réels à faible montant.

Références techniques consultées :
- FedaPay transactions : https://docs-v1.fedapay.com/paiements/transactions
- FedaPay webhooks : https://docs-v1.fedapay.com/developpement/webhooks
- CinetPay Python SDK : https://github.com/cinetpay/cinetpay-python
