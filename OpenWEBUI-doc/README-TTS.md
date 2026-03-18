# Configuration de l'API TTS dans OpenWebUI

Ce guide explique comment connecter OpenWebUI à un service de synthèse vocale compatible OpenAI pour activer le Text-To-Speech (TTS).

## 1) Prérequis

- Une instance TTS compatible OpenAI déployée et accessible en HTTP/HTTPS.
- Un token API valide si le service impose une authentification.
- Une instance OpenWebUI opérationnelle.
- Une connectivité réseau fonctionnelle entre OpenWebUI et le service TTS.
- Si OpenWebUI est exposé dans un navigateur distant, HTTPS peut être nécessaire pour que les fonctions audio fonctionnent correctement.

> Endpoint TTS compatible attendu par le backend : `POST /audio/speech` via une base URL de type `https://api.example.com/v1`

* * *

## 2) Vérifier l'API TTS

Avant la configuration OpenWebUI, testez l'API directement :

```bash
curl -X POST "https://api.example.com/v1/audio/speech" \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "voice": "alloy",
    "input": "Bonjour depuis OpenWebUI"
  }' \
  --output test.mp3
````

Si la commande génère un fichier audio lisible, la base est prête.

---

## 3) Configuration dans OpenWebUI

Dans OpenWebUI :

1. Ouvrez **Admin Panel**.
2. Allez dans **Settings** puis **Audio**.
3. Dans la section TTS, configurez :

* **Text-to-Speech Engine** : `OpenAI`
* **API Base URL** : `https://api.example.com/v1`
* **API Key** : `VOTRE_TOKEN`
* **TTS Model** : `tts-1`
* **TTS Voice** : `alloy`

4. Enregistrez la configuration.

> OpenWebUI documente un champ **API Base URL** et des champs **TTS Model** / **TTS Voice**.
> Il n’y a pas lieu d’ajouter un champ séparé `TTS Path` dans cette documentation.

---

## 4) Paramètres recommandés

Pour une expérience stable :

* **Text-to-Speech Engine** : `OpenAI`
* **API Base URL** : URL complète finissant généralement par `/v1`
* **TTS Model** : `tts-1`
* **TTS Voice** : `alloy`

Exemple cohérent :

* **Text-to-Speech Engine** : `OpenAI`
* **API Base URL** : `https://api.example.com/v1`
* **TTS Model** : `tts-1`
* **TTS Voice** : `alloy`

Si votre backend OpenAI-compatible utilise d’autres modèles ou voix, remplacez simplement `tts-1` et `alloy` par les valeurs acceptées par votre service.

---

## 5) Validation dans OpenWebUI

* Ouvrez une conversation.
* Déclenchez la lecture audio d’une réponse.
* Vérifiez qu’un audio est produit correctement.

Si l’audio ne se lance pas, vérifiez les logs OpenWebUI et ceux du backend TTS.

---

## 6) Dépannage

### 401 Unauthorized

* Vérifiez l'en-tête `Authorization: Bearer <token>`.
* Vérifiez que la clé API est bien copiée dans OpenWebUI.

### 403 Forbidden

* Le token est reconnu mais non autorisé.

### 404 Not Found / 405 Method Not Allowed

* Vérifiez la **API Base URL**.
* Vérifiez que votre service expose bien un endpoint OpenAI-compatible sous `/v1/audio/speech`.

### Aucun son / chargement infini

* Vérifiez que l’URL de base se termine bien par `/v1` si votre backend l’exige.
* Vérifiez que le modèle et la voix existent réellement côté backend.
* Vérifiez les logs OpenWebUI et ceux du backend TTS.

### Problème réseau depuis Docker

* Si OpenWebUI tourne dans Docker, `localhost` peut être incorrect depuis le conteneur.
* Utilisez selon le cas :

  * `host.docker.internal`
  * le nom du service Docker
  * l’IP de la machine hôte

### TTS ne fonctionne pas dans le navigateur

* Vérifiez que l’instance est servie en **HTTPS** ou via `localhost`.

---

## 7) Variables d'environnement utiles côté OpenWebUI

Si vous configurez OpenWebUI par variables d’environnement, les plus utiles sont :

```bash
AUDIO_TTS_ENGINE=openai
AUDIO_TTS_OPENAI_API_BASE_URL=https://api.example.com/v1
AUDIO_TTS_OPENAI_API_KEY=VOTRE_TOKEN
AUDIO_TTS_MODEL=tts-1
AUDIO_TTS_VOICE=alloy
```

> Attention : OpenWebUI peut privilégier les valeurs persistées dans son stockage interne par rapport aux variables d’environnement déjà changées après coup.
