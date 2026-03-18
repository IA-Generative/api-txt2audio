# api-txt2audio

API FastAPI de synthèse vocale multilingue (Kokoro-82M) avec sortie `wav|mp3|opus|webm`.

## Objectif
Transformer un texte en audio via un endpoint HTTP unique : `POST /v1/audio/speech`.

## Prérequis
- Python 3.11+
- `ffmpeg` installé et accessible dans le `PATH`

## Démarrage en une commande
```bash
make run
```

L'API démarre sur `http://localhost:8080` avec le token par défaut `dev-token`.

## Test rapide
### 1) Vérifier la base technique
```bash
make smoke
```

### 2) Générer un MP3
```bash
curl -X POST "http://localhost:8080/v1/audio/speech" \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{"input":"Bonjour, ceci est une démonstration TTS.","voice":"heart","gender":"f","response_format":"mp3"}' \
  --output sample.mp3
```

Validation minimale :
```bash
file sample.mp3
```

## Endpoints
- `GET /healthz` : état du service et du cache voix.
- `GET /readyz` : readiness du pipeline.
- `POST /v1/audio/speech` : génération audio.

## Variables d'environnement
- `API_TOKENS` : token(s) autorisés (obligatoire en environnement non local).
- `PORT` : port HTTP (défaut `8080`).
- `CORS_ALLOW_ORIGINS` : origines CORS autorisées.
- `RATE_WINDOW_S`, `RATE_MAX_REQ` : paramètres de limitation de débit.

## Documentation
- Architecture technique : `docs/architecture.md`
- Cas d'usage et test critique : `USE_CASE.md`
- Valeur métier : `VALUE.md`
- Statut d'innovation : `INNOVATION_STATUS.md`
- Intégration OpenWebUI : `OpenWEBUI-doc/README.md`
