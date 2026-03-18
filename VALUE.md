# Valeur métier

## 🎯 Problème métier ciblé
La production de messages vocaux personnalisés est lente, coûteuse et difficile à industrialiser lorsqu'elle dépend d'enregistrements humains.

## ⏱ Temps économisé (estimation)
- Hypothèse: 200 messages/semaine.
- Processus manuel: ~8 min/message (rédaction + enregistrement + export).
- Processus API: ~1 min/message (génération + intégration).
- **Gain estimé: ~1 400 min/semaine (~23 h/semaine).**

## 💰 Coût évité/réduit (estimation)
- Hypothèse coût interne: 45 €/h.
- 23 h/semaine économisées ≈ **1 035 €/semaine**.
- Annualisé (48 semaines): **~49 680 €/an**.

## 🛡 Risque diminué
- Réduit le risque d'incohérence de messages entre agents.
- Réduit la dépendance à une ressource humaine unique pour la voix.
- Réduit les retards de diffusion en période de pic.

## 🚀 Capacité nouvelle créée
- Génération audio à la demande, multilingue, intégrable en temps réel dans les workflows CRM/ops.

## KPIs proposés
- Délai moyen de génération audio (p95, secondes).
- Nombre de messages générés par semaine.
- Taux de réutilisation de l'API par application consommatrice.
- Taux d'échec API (4xx/5xx) et taux d'erreur TTS.

## Hypothèses explicites
- Volume stable entre 100 et 500 messages/semaine.
- Utilisation majoritaire en messages courts (< 60 secondes).
- Infrastructure cible avec `ffmpeg` disponible et connectivité HF Hub.

## Conditions de validité
- Token d'auth correctement géré.
- Monitoring minimal en place (latence, erreurs).
- Revue qualité audio sur les langues critiques avant passage à grande échelle.
