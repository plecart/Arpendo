---
description: Écrit un plan de QA cadré sur un thème ou un lot livré et le publie en issue GitHub à cocher
argument-hint: ["Thème" | #issues couvertes par la QA]
---

Invoque le skill `plan-qa`.

Périmètre de la QA : $ARGUMENTS

Cadre le plan sur ce qui vient d'être livré, rien de plus. Ancre chaque case dans la réalité du
projet — vraies routes, vrais composants, vraies commandes issues de `.claude/pipeline.config.md`.
Une checklist générique est un mauvais signe.

Deux règles qui décident du contenu :
- **Ne double jamais la CI.** Une case n'existe que si un test automatisé ne peut structurellement
  pas la couvrir (rendu réel, console, isolation entre comptes, état terminal d'un job, artefact
  produit). Si un test aurait pu l'attraper, elle sort du plan.
- **Les surfaces viennent de la config**, pas d'un modèle en dur. Une surface que le projet n'a pas
  ne produit aucune section — pas même un « N/A ».
