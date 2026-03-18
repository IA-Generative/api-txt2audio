# API Text-to-Audio (Kokoro-82M)

Service FastAPI de synthèse vocale multilingue basé sur `hexgrad/Kokoro-82M`.

## Démarrage rapide

Prérequis:
- Python 3.11+
- `ffmpeg` installé dans le PATH

```bash
make run
```

Par défaut, l'API écoute sur `http://localhost:8080` avec le token `dev-token`.

## Vérification rapide

```bash
make check
curl -X POST "http://localhost:8080/v1/audio/speech" \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{"input":"Bonjour, ceci est une démonstration TTS.","voice":"heart","gender":"f","response_format":"mp3"}' \
  --output sample.mp3
file sample.mp3
```

## Endpoints

- `GET /healthz` : statut service + cache.
- `GET /readyz` : readiness du pipeline.
- `POST /v1/audio/speech` : génération audio (`wav|mp3|opus|webm`).

## Variables d'environnement

- `API_TOKENS` (obligatoire): token(s) séparé(s) par virgule/espace (`*` pour tout accepter).
- `PORT` : port HTTP (défaut `8080`).
- `CORS_ALLOW_ORIGINS` : liste d'origines CORS.
- `RATE_WINDOW_S`, `RATE_MAX_REQ` : limite de débit.

## Déploiement

- Kubernetes/Helm: voir `helm/README.md`.
- OpenWebUI: voir `OpenWEBUI-doc/README.md`.

## Documentation projet

- Flux / états: `STATE.md`
- Vue d'ensemble: `docs/overview.md`
- Architecture: `docs/architecture.md`
- Cas d'usage: `USE_CASE.md`
- Valeur métier: `VALUE.md`
- Statut innovation: `INNOVATION_STATUS.md`
