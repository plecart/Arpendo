---
description: Trie les issues via la machine à états (catégorie + état + thème) et rédige les briefs d'agent
argument-hint: [#issue | vide pour ce qui requiert ton attention]
---

Invoque le skill `triage`.

Demande du mainteneur : $ARGUMENTS

Sans argument, montre ce qui requiert l'attention : issues sans label, `needs-triage`,
`needs-interrogation` en attente de session, `needs-info` ayant reçu une réponse du rapporteur
depuis les dernières notes de triage, et issues fermées portant encore un rôle d'état.

Rappel : `ready-for-agent` et `ready-for-human` ne s'atteignent que via `needs-interrogation`.

