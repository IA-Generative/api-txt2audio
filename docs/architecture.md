# Architecture

## Composants
- **Client**: envoie une requête TTS HTTP.
- **FastAPI app (`app.py`)**: auth, rate-limit, orchestration pipeline.
- **Kokoro pipeline**: synthèse vocale et chargement des voix HF.
- **FFmpeg**: transcodage streaming en format cible.
- **Stock externe HF Hub**: récupération des voix.

## Diagramme

```mermaid
flowchart LR
  C[Client HTTP] --> A[FastAPI /v1/audio/speech]
  A --> B{Auth + Rate limit}
  B --> D[Split langue + sélection voix]
  D --> E[Kokoro-82M pipeline]
  E --> F[Flux WAV interne]
  F --> G[FFmpeg transcodeur]
  G --> H[Réponse audio streaming]
  E -. télécharge voix .-> I[Hugging Face Hub]
```

## Flux d'exécution (résumé)
1. Vérification du token Bearer.
2. Validation JSON (Pydantic).
3. Découpage multilingue + détection langue.
4. Chargement/caching pipeline + voix.
5. Génération audio + streaming de la réponse.
