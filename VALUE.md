# Valeur métier

## Problème métier ciblé
La production de messages vocaux personnalisés est souvent manuelle, lente et coûteuse (rédaction + enregistrement + retouches). Cela freine les usages à grande échelle (notification client, relance, information en masse).

## ROI estimé
### Hypothèses
- Volume : **200 messages/semaine**.
- Temps manuel : **8 min/message**.
- Temps via API : **1 min/message**.
- Coût interne : **45 €/h**.
- Période annuelle : **48 semaines**.

### Calculs
- Temps économisé : `(8 - 1) * 200 = 1 400 min/semaine` soit **~23,3 h/semaine**.
- Coûts réduits : `23,3 h * 45 € = ~1 050 €/semaine`.
- Gain annualisé : `~1 050 € * 48 = ~50 400 €/an`.

## Risques diminués
- Variabilité de ton/qualité entre agents réduite.
- Dépendance à une ressource humaine unique réduite.
- Risque de retard de publication en période de pic réduit.

## Capacités créées
- Génération audio à la demande, multilingue, API-first.
- Intégration directe dans CRM / workflows automatisés.
- Réutilisation transverse (support, marketing, opérations).

## KPIs de suivi
- Latence p95 de génération audio (s).
- Taux de succès API (`2xx`) et taux d'erreur (`4xx`/`5xx`).
- Nombre de messages audio générés / semaine.
- Taux de réutilisation par applications consommatrices.
- Coût moyen par message généré.

## Conditions de validité
- `ffmpeg` disponible sur les environnements cibles.
- Connectivité vers Hugging Face Hub pour le bootstrap des voix.
- Politique d'authentification (`API_TOKENS`) active.
- Monitoring minimal en place (latence, erreurs, volume).
