# Cas d'usage réel

## Contexte
Un centre de relation client veut produire des messages vocaux multilingues (confirmation de rendez-vous, relance, informations opérationnelles) sans studio d'enregistrement.

## Acteurs
- Équipe produit/service client
- Système CRM qui appelle l'API
- Destinataires finaux (clients)

## Scénario
1. Le CRM envoie un texte personnalisé à `/v1/audio/speech`.
2. L'API génère un MP3 dans la langue détectée.
3. Le CRM stocke ou diffuse immédiatement l'audio.

## Résultat attendu
- Mise à disposition d'un message audio en quelques secondes.
- Homogénéité de ton/voix entre campagnes.
- Réduction des tâches manuelles de production audio.

## Exemple I/O métier
- Entrée: "Bonjour Mme Martin, votre rendez-vous est confirmé pour demain 9h."
- Sortie: fichier `mp3` utilisable dans un appel automatisé ou un canal messaging.
