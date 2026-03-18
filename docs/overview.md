# Overview technique

## Objectif
Fournir une API HTTP simple pour transformer du texte en audio avec streaming et authentification Bearer.

## Ce que fait le service
- Détecte la langue par blocs de phrases.
- Sélectionne automatiquement une voix adaptée (langue + genre si demandé).
- Génère l'audio via Kokoro-82M.
- Convertit à la volée vers `wav`, `mp3`, `opus` ou `webm` via `ffmpeg`.

## Contrat API minimal
- Entrée: JSON `{ input, voice?, gender?, response_format? }`
- Sortie: flux binaire audio
- Sécurité: `Authorization: Bearer <token>`

## Exploitabilité
- Lancement standardisé: `make run`
- Vérification minimale: `make smoke`
- Déploiement: Docker + Helm fournis dans le repository

## Limites connues
- Le premier appel peut être plus lent (téléchargement des voix/modèle).
- La qualité/perf dépend du CPU/GPU disponible et de `ffmpeg`.
