# API Text2Audio 🎙️

API REST basée sur FastAPI pour convertir du texte en audio à l’aide de Kokoro TTS via Hugging Face.

## Endpoints

### `POST /v1/audio/speech`
Convertit un texte en audio (format `.wav` ou `.opus`).

#### Headers
- `Authorization: Bearer <token>`

#### Body JSON
```json
{
  "input": "Bonjour le monde",
  "voice": "siwis",
  "response_format": "wav"
}
```

#### Réponses
- `200 OK` : retourne un flux audio
- `401 Unauthorized` / `403 Forbidden`
- `500 Internal Server Error`

## Installation

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

## Exemple d'appel avec `curl`

```bash
curl -X POST http://localhost:8000/v1/audio/speech \
-H "Authorization: Bearer token_client_a" \
-H "Content-Type: application/json" \
-d '{"input": "Bonjour le monde", "voice": "siwis", "response_format": "wav"}' \
--output output.wav
```
