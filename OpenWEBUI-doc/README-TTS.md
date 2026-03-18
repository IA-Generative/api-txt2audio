# Configuration de l'API TTS dans OpenWebUI

Ce guide explique comment connecter OpenWebUI à ce service TTS compatible OpenAI pour activer la synthèse vocale (Text-To-Speech).

## 1) Prérequis

- Une instance TTS compatible OpenAI déployée et accessible en HTTP/HTTPS.
- Un token API valide si le service impose une authentification.
- Une instance OpenWebUI opérationnelle.
- Une connectivité réseau fonctionnelle entre OpenWebUI et le service TTS.

> Endpoint TTS compatible : `POST /v1/audio/speech`

* * *

## 2) Vérifier l'API TTS

Avant la configuration OpenWebUI, testez l'API directement :

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
````

Si la commande génère un fichier audio lisible, la base est prête.

---

## 3) Configuration dans OpenWebUI

Dans OpenWebUI :

1. Ouvrez **Admin Panel**.
2. Allez dans **Settings** puis **Audio / Text-to-Speech (TTS)** selon votre version.
3. Activez le fournisseur **Custom / OpenAI-compatible** selon votre version.
4. Renseignez les champs suivants :

* **Base URL** : `https://api.example.com`
* **TTS Path** : `/v1/audio/speech`
* **API Key** : `VOTRE_TOKEN`
* **Voice** : `heart` (exemple)
* **Format** : `mp3` ou `opus`

5. Enregistrez la configuration.

> Selon la version d'OpenWebUI, les libellés peuvent légèrement varier, mais les valeurs ci-dessus restent les mêmes.

---

## 4) Paramètres recommandés

Pour une expérience stable :

* `response_format` : `mp3` (bonne compatibilité navigateur)
* `voice` : une voix existante côté backend (`heart`, `bella`, etc. selon disponibilité)
* `gender` : `f` ou `m` (optionnel selon le backend)

Exemple de payload utilisé par OpenWebUI :

```json
{
  "input": "Texte à synthétiser",
  "voice": "heart",
  "gender": "f",
  "response_format": "mp3"
}
```

---

## 5) Validation dans OpenWebUI

* Ouvrez une conversation.

* Lancez la lecture audio / synthèse vocale selon votre usage.

* Vérifiez qu'OpenWebUI envoie bien une requête vers :

* `POST /v1/audio/speech`

Si la configuration est correcte, un flux ou un fichier audio est renvoyé par le service.

---

## 6) Dépannage

### 401 Unauthorized

* Vérifiez l'en-tête `Authorization: Bearer <token>`.
* Vérifiez que la clé API est bien copiée dans OpenWebUI.

### 403 Forbidden

* Le token est reconnu mais non autorisé.

### 404 Not Found / 405 Method Not Allowed

* Vérifiez la **Base URL**.
* Vérifiez le chemin **`/v1/audio/speech`**.

### 429 Too Many Requests

* Réduisez la cadence des requêtes OpenWebUI.
* Ajustez les paramètres de rate-limit côté API si nécessaire.

### Audio vide / erreur de format

* Vérifiez que le format choisi (`mp3`, `opus`, `wav`, `webm`) est supporté par votre client.
* Vérifiez les logs du backend TTS.

---

## 7) Variables d'environnement utiles côté API

Selon l’implémentation du service TTS, les variables suivantes peuvent être utiles :

* `API_TOKENS` : liste des tokens autorisés.
* `CORS_ALLOW_ORIGINS` : origines autorisées.
* `RATE_WINDOW_S` : fenêtre de rate-limit.
* `RATE_MAX_REQ` : requêtes max par fenêtre.

Exemple :

```bash
API_TOKENS="token-openwebui-1 token-openwebui-2"
CORS_ALLOW_ORIGINS="https://openwebui.example.com"
RATE_WINDOW_S="2"
RATE_MAX_REQ="6"
```

````

### `OpenWEBUI-doc/README-STT.md`

```md
# Configuration de l'API STT dans OpenWebUI

Ce guide explique comment connecter OpenWebUI à un service de transcription compatible OpenAI pour activer la reconnaissance vocale (Speech-To-Text).

## 1) Prérequis

- Une instance STT compatible OpenAI déployée et accessible en HTTP/HTTPS.
- Un token API valide si le service impose une authentification.
- Une instance OpenWebUI opérationnelle.
- Une connectivité réseau fonctionnelle entre OpenWebUI et le service STT.

> Endpoint STT compatible : `POST /v1/audio/transcriptions`

* * *

## 2) Vérifier l'API STT

Avant la configuration OpenWebUI, testez l'API directement :

```bash
curl -X POST "https://api.example.com/v1/audio/transcriptions" \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -F "file=@test.wav" \
  -F "model=whisper-1"
````

Si la commande renvoie une transcription exploitable, la base est prête.

---

## 3) Configuration dans OpenWebUI

Dans OpenWebUI :

1. Ouvrez **Admin Panel**.
2. Allez dans **Settings** puis **Audio / Speech-to-Text (STT)** selon votre version.
3. Activez le fournisseur **OpenAI-compatible / OpenAI API** pour la transcription.
4. Renseignez les champs suivants :

* **Base URL** : `https://api.example.com`
* **STT Path** : `/v1/audio/transcriptions`
* **API Key** : `VOTRE_TOKEN`
* **Model** : `whisper-1`

5. Enregistrez la configuration.

> Selon la version d'OpenWebUI, les libellés peuvent légèrement varier, mais les valeurs ci-dessus restent les mêmes.

---

## 4) Paramètres recommandés

Pour une expérience stable :

* `model` : `whisper-1`
* Utiliser un format audio standard (`wav`, `mp3`, `m4a`, `webm`) selon le support de votre backend
* Vérifier que la taille maximale des fichiers envoyés est compatible avec les limites côté API

Exemple de requête attendue :

```http
POST /v1/audio/transcriptions
```

Avec au minimum :

* un fichier audio
* `model=whisper-1`

---

## 5) Validation dans OpenWebUI

* Ouvrez une conversation.
* Déposez un fichier audio.
* Lancez la transcription.

Si la configuration est correcte, OpenWebUI enverra une requête vers :

* `POST /v1/audio/transcriptions`

---

## 6) Dépannage

### 401 Unauthorized

* Vérifiez l'en-tête `Authorization: Bearer <token>`.
* Vérifiez que la clé API est bien copiée dans OpenWebUI.

### 403 Forbidden

* Le token est reconnu mais non autorisé.

### 404 Not Found / 405 Method Not Allowed

* Vérifiez la **Base URL**.
* Vérifiez le chemin **`/v1/audio/transcriptions`**.

### Timeout / Connection error

* Vérifiez le DNS, le port, le routage et les règles réseau entre OpenWebUI et le service STT.

### Aucune transcription / erreur de modèle

* Vérifiez que le modèle `whisper-1` est accepté par le service.
* Vérifiez les logs du backend STT.

### Fichier refusé / taille trop importante

* Vérifiez les limites d’upload côté reverse proxy, OpenWebUI et backend STT.
* Vérifiez le format réel du fichier audio envoyé.

---

## 7) Variables d'environnement utiles côté API

Selon l’implémentation du service STT, les variables suivantes peuvent être utiles :

* `API_TOKENS` : liste des tokens autorisés
* `CORS_ALLOW_ORIGINS` : origines autorisées
* variables de taille maximale d’upload selon votre backend
* variables de rate-limit selon votre backend

Exemple :

```bash
API_TOKENS="token-openwebui-1 token-openwebui-2"
CORS_ALLOW_ORIGINS="https://openwebui.example.com"
```
