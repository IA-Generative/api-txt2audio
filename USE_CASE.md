# Cas d'usage réel

## Contexte métier
Un centre de relation client veut générer rapidement des messages vocaux multilingues (confirmation de rendez-vous, relance, information opérationnelle) sans studio d'enregistrement.

## Acteurs
- Équipe Service Client
- CRM / orchestrateur métier
- API `api-txt2audio`
- Client final (destinataire du message audio)

## Scénario cible
1. Le CRM compose un message personnalisé.
2. Le CRM appelle `POST /v1/audio/speech`.
3. L'API renvoie un fichier audio prêt à diffuser.
4. Le CRM stocke l'audio ou le diffuse immédiatement.

## Résultat attendu
- Audio généré en quelques secondes.
- Ton homogène d'un message à l'autre.
- Réduction des tâches manuelles de production audio.

---

## (B) Séquence du Test Critique (reproductible)

### Objectif
Valider le chemin critique "entrée texte valide -> sortie audio MP3".

### Préconditions
- API démarrée via `make run`.
- Token local par défaut : `dev-token`.

### Données d'entrée (déterministes)
Payload JSON exact :
```json
{
  "input": "Bonjour Mme Martin, votre rendez-vous est confirmé pour demain 9h.",
  "voice": "heart",
  "gender": "f",
  "response_format": "mp3"
}
```

### Commande d'exécution
```bash
curl -sS -X POST "http://localhost:8080/v1/audio/speech" \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{"input":"Bonjour Mme Martin, votre rendez-vous est confirmé pour demain 9h.","voice":"heart","gender":"f","response_format":"mp3"}' \
  --output critical_test.mp3
```

### Sortie attendue (reproductible)
1. Fichier `critical_test.mp3` créé.
2. Taille strictement supérieure à 0 octet.
3. `file critical_test.mp3` retourne un type audio MPEG/MP3.

### Vérification
```bash
test -s critical_test.mp3 && file critical_test.mp3
```
