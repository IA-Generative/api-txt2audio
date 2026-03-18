# Configuration de l'API TTS dans OpenWebUI

Ce guide explique comment connecter **OpenWebUI** à ce service `api-txt2audio` pour activer la synthèse vocale (Text-To-Speech).

## 1) Prérequis

- Une instance `api-txt2audio` déployée et accessible en HTTP/HTTPS.
- Un token API valide (variable `API_TOKENS` côté service).
- Une instance OpenWebUI opérationnelle.

> Endpoint TTS compatible : `POST /v1/audio/speech`

---

## 2) Vérifier l'API TTS

Avant la configuration OpenWebUI, testez l'API directement :

```bash
curl -X POST "https://api.example.com/v1/audio/speech" \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "input": "Bonjour depuis OpenWebUI",
    "voice": "heart",
    "gender": "f",
    "response_format": "mp3"
  }' \
  --output test.mp3
```

Si la commande génère un fichier audio lisible, la base est prête.

---

## 3) Configuration dans OpenWebUI

Dans OpenWebUI :

1. Ouvrez **Admin Panel**.
2. Allez dans **Settings** puis **Audio / Text-to-Speech (TTS)**.
3. Activez le fournisseur TTS personnalisé (Custom/OpenAI-compatible selon votre version).
4. Renseignez les champs suivants :

- **Base URL**: `https://api.example.com`
- **TTS Path**: `/v1/audio/speech`
- **API Key**: `VOTRE_TOKEN`
- **Voice**: `heart` (exemple)
- **Format**: `mp3` ou `opus`

5. Enregistrez la configuration.

> Selon la version d'OpenWebUI, les libellés peuvent légèrement varier, mais les valeurs ci-dessus restent les mêmes.

---

## 4) Paramètres recommandés

Pour une expérience stable :

- `response_format`: `mp3` (bonne compatibilité navigateur)
- `voice`: une voix existante dans Kokoro (`heart`, `bella`, etc. selon disponibilité)
- `gender`: `f` ou `m` (optionnel)

Exemple de payload utilisé par OpenWebUI :

```json
{
  "input": "Texte à synthétiser",
  "voice": "heart",
  "gender": "f",
  "response_format": "mp3"
}
```

---

## 5) Dépannage

### 401 Unauthorized

- Vérifiez l'en-tête `Authorization: Bearer <token>`.
- Vérifiez la variable `API_TOKENS` côté service.

### 403 Forbidden

- Le token est reconnu mais non autorisé.

### 429 Too Many Requests

- Réduire la cadence des requêtes OpenWebUI.
- Ajuster `RATE_WINDOW_S` et `RATE_MAX_REQ` côté API si nécessaire.

### Audio vide / erreur ffmpeg

- Vérifiez que le format choisi (`mp3`, `opus`, `wav`, `webm`) est supporté par votre client.
- Vérifiez les logs de l'API.

---

## 6) Variables d'environnement utiles côté API

- `API_TOKENS`: liste des tokens autorisés (séparés par espaces ou virgules).
- `CORS_ALLOW_ORIGINS`: origines autorisées.
- `RATE_WINDOW_S`: fenêtre de rate-limit.
- `RATE_MAX_REQ`: requêtes max par fenêtre.

Exemple :

```bash
API_TOKENS="token-openwebui-1 token-openwebui-2"
CORS_ALLOW_ORIGINS="https://openwebui.example.com"
RATE_WINDOW_S="2"
RATE_MAX_REQ="6"
```
