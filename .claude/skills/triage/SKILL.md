---
name: triage
description: Trie les issues à travers une machine à états pilotée par des rôles de triage. À utiliser quand l'utilisateur veut créer une issue, trier des issues, examiner les bugs ou demandes de fonctionnalités entrants, préparer des issues pour un agent AFK, ou gérer le workflow des issues.
---

# Triage

Faire progresser les issues sur GitHub (via `gh`) à travers une petite machine à états composée de rôles de triage.

Chaque commentaire ou issue publié sur GitHub (via `gh`) pendant le triage **doit** commencer par ce disclaimer :

```
> *Généré par IA pendant le triage.*
```

## Documents de référence

- [brief-agent.md](brief-agent.md) — comment rédiger des briefs d'agent durables
- [hors-scope.md](hors-scope.md) — comment fonctionne la base de connaissances `.out-of-scope/`
- [themes-milestones.md](themes-milestones.md) — comment regrouper les issues par thème via les milestones GitHub

## Rôles

Deux rôles de **catégorie** :

- `bug` — quelque chose est cassé
- `enhancement` — nouvelle fonctionnalité ou amélioration

Six rôles d'**état** :

- `needs-triage` — le mainteneur doit évaluer
- `needs-info` — en attente d'informations complémentaires **de la part du rapporteur**
- `needs-interrogation` — triée et retenue, mais doit passer l'**interrogatoire** (`/interroge-moi`)
  avant de partir en développement
- `ready-for-agent` — entièrement spécifié, prêt pour un agent AFK
- `ready-for-human` — nécessite une implémentation humaine
- `wontfix` — ne sera pas traité

`needs-info` et `needs-interrogation` ne se confondent pas : le premier attend **quelqu'un d'autre**
(le rapporteur), le second attend **une session avec le mainteneur**. Une issue peut passer par les
deux, dans cet ordre.

Chaque issue **ouverte** triée doit porter exactement un rôle de catégorie et un rôle d'état ; une issue **fermée** n'en porte aucun — `cycle-pr` retire l'état à la clôture (Étape 8), et `wontfix` est le seul rôle qui survit à une fermeture. Si les rôles d'état entrent en conflit, signale-le et demande au mainteneur avant de faire quoi que ce soit d'autre.

Ce sont les noms de rôles canoniques ; le mapping vers les vrais labels GitHub est dans `.claude/pipeline.config.md` — sinon lancer `init-projet`.

## Thèmes (milestones)

En plus des rôles, chaque issue qui avance dans le triage est rattachée à **exactement un thème** —
un regroupement par sujet matérialisé par un **milestone GitHub** (purement thématique, sans date).
C'est **obligatoire pour toute issue triée, sauf celles fermées en `wontfix`**.

Les thèmes ne sont pas une taxonomie à part : ils reprennent **les domaines déclarés dans
`.claude/pipeline.config.md`** (section « Périmètre »). Si aucun domaine ne couvre l'issue, ne pas
créer de thème orphelin — le signaler au mainteneur. Voir
[themes-milestones.md](themes-milestones.md) pour le choix du thème, le nommage et les commandes
`gh`.

Transitions d'état :

```
(sans label) → needs-triage ─┬→ needs-info ──────────→ (retour needs-triage quand le rapporteur répond)
                             ├→ needs-interrogation ─┬→ ready-for-agent
                             │                       └→ ready-for-human
                             └→ wontfix
```

**`ready-for-agent` et `ready-for-human` ne sont atteignables que depuis `needs-interrogation`.**
Aucune issue ne part en développement sans être passée par l'interrogatoire — c'est le garde-fou
qui empêche une ambiguïté d'être découverte au cinquième commit.

Le mainteneur peut passer outre à tout moment — signale les transitions qui paraissent
inhabituelles et demande avant de continuer. Un passage en force de l'interrogatoire se **trace**
(voir « Changement d'état rapide »), il ne s'oublie pas.

## Invocation

Le mainteneur invoque `/triage` et décrit ce qu'il veut en langage naturel. Interprète la demande et agis. Exemples :

- « Montre-moi tout ce qui requiert mon attention »
- « Regardons l'issue #42 »
- « Passe l'issue #42 en ready-for-agent »
- « Qu'est-ce qui est prêt à être pris par les agents ? »

## Montrer ce qui requiert l'attention

Interroge GitHub (via `gh`) et présente quatre catégories, des plus anciennes aux plus récentes :

1. **Sans label** — jamais triées.
2. **`needs-triage`** — évaluation en cours.
3. **`needs-interrogation`** — en attente d'une session `/interroge-moi` avec le mainteneur. C'est la file qui bloque l'alimentation des agents : la signaler explicitement si elle s'allonge.
4. **`needs-info` avec activité du rapporteur depuis les dernières notes de triage** — nécessite une réévaluation.

Affiche les décomptes et un résumé d'une ligne par issue, en indiquant le thème (milestone) de chaque issue quand il y en a un. Si le mainteneur le demande, regroupe l'affichage par thème. Laisse le mainteneur choisir.

## Trier une issue spécifique

1. **Rassembler le contexte.** Lis l'issue complète (corps, commentaires, labels, milestone, rapporteur, dates). Analyse les éventuelles notes de triage antérieures pour ne pas reposer des questions déjà résolues. Explore le code en t'appuyant sur le glossaire métier du projet, en respectant les ADR du domaine concerné. Lis `.out-of-scope/*.md` et fais remonter tout rejet antérieur ressemblant à cette issue. Lis les **domaines** de `.claude/pipeline.config.md` et liste les **thèmes (milestones) existants** pour rattacher l'issue au bon domaine plutôt que de créer un thème en double ([themes-milestones.md](themes-milestones.md)).

2. **Recommander.** Indique au mainteneur ta recommandation de catégorie, d'état et de **thème** (un milestone existant qui colle, ou un nouveau thème à créer) avec ton raisonnement, ainsi qu'un bref résumé du code pertinent pour l'issue. Attends ses instructions.

3. **Reproduire (bugs uniquement).** Avant tout interrogatoire, tente de reproduire : lis les étapes du rapporteur, trace le code concerné, lance des tests ou des commandes. Rapporte ce qui s'est passé — reproduction réussie avec le chemin de code, reproduction échouée, ou détails insuffisants (un fort signal de `needs-info`). Une reproduction confirmée permet un brief d'agent bien plus solide.

4. **Interroger — systématiquement.** Toute issue destinée à `ready-for-agent` ou `ready-for-human` passe par l'interrogatoire, sans exception. Ce n'est pas conditionné à ton impression que « l'issue a l'air claire » : c'est précisément quand elle en a l'air que les hypothèses tacites passent.

   - Passe l'issue en `needs-interrogation`, puis lance le skill `interroge-moi` si le mainteneur est disponible tout de suite.
   - S'il ne l'est pas, **laisse l'issue en `needs-interrogation` et arrête-toi là** — elle attendra sa session. Ne la promeus pas « en attendant ».
   - **Consigne le résultat dans l'issue**, sinon le garde-fou n'est que décoratif : les points tranchés vont dans « Décisions verrouillées » du brief d'agent, les questions restées ouvertes en notes de triage. *Une interrogation dont les conclusions ne sont pas écrites n'a pas eu lieu* — c'est `cycle-pr` qui les relira, des jours plus tard, sans accès à cette conversation.

5. **Appliquer le résultat :**

   Sauf pour `wontfix`, **rattache l'issue à son thème** avant tout autre changement : réutilise le
   milestone du domaine qui correspond, ou crée-le au nom exact du domaine s'il n'existe pas encore
   (annonce alors le thème créé au mainteneur). Si aucun domaine ne couvre l'issue, arrête-toi et
   demande. Voir [themes-milestones.md](themes-milestones.md).

   - `needs-interrogation` — applique le rôle et publie les notes de triage de ce qui est déjà établi. L'issue attend sa session `/interroge-moi` ; ne rédige pas encore de brief d'agent.
   - `ready-for-agent` — publie un commentaire de brief d'agent ([brief-agent.md](brief-agent.md)), en y reportant les décisions tranchées pendant l'interrogatoire.
   - `ready-for-human` — même structure qu'un brief d'agent, mais précise pourquoi cela ne peut pas être délégué (jugements à porter, accès externe, décisions de conception, tests manuels).
   - `needs-info` — publie des notes de triage (modèle ci-dessous).
   - `wontfix` (bug) — explication polie, puis ferme.
   - `wontfix` (enhancement) — écris dans `.out-of-scope/`, fais-y référence depuis un commentaire, puis ferme ([hors-scope.md](hors-scope.md)).
   - `needs-triage` — applique le rôle. Commentaire optionnel s'il y a un avancement partiel.

## Changement d'état rapide

Si le mainteneur dit « passe l'issue #42 en ready-for-agent », fais-lui confiance sur le **fond** et applique le rôle directement. Confirme ce que tu t'apprêtes à faire (changements de rôle, commentaire, fermeture), puis agis.

**L'interrogatoire reste dû**, même en mode rapide. Trois cas :

- L'issue est déjà passée par `needs-interrogation` avec ses conclusions écrites → applique `ready-for-agent` et propose de rédiger le brief d'agent.
- Elle n'y est pas passée → dis-le et propose de lancer `interroge-moi` maintenant.
- Le mainteneur veut passer outre malgré tout → applique `ready-for-agent`, et **note explicitement dans le brief d'agent que l'issue n'a pas été interrogée**, sous un titre `**⚠️ Non interrogée au triage**`. C'est ce qui permet à `cycle-pr` de rattraper le coup à l'Étape 1 au lieu de partir sur des hypothèses tacites.

Même en mode rapide, si l'état cible n'est pas `wontfix` et que l'issue n'a pas encore de thème, rattache-la au thème de son domaine (existant ou créé à la volée) dans la même opération ([themes-milestones.md](themes-milestones.md)).

## Modèle needs-info

```markdown
## Notes de triage

**Ce que nous avons établi jusqu'ici :**

- point 1
- point 2

**Ce dont nous avons encore besoin de ta part (@rapporteur) :**

- question 1
- question 2
```

Consigne tout ce qui a été résolu pendant l'interrogatoire sous « établi jusqu'ici » afin que le travail ne soit pas perdu. Les questions doivent être précises et actionnables, pas « merci de fournir plus d'informations ».

## Reprendre une session précédente

Si des notes de triage antérieures existent sur l'issue, lis-les, vérifie si le rapporteur a répondu à des questions en suspens, et présente un état des lieux actualisé avant de continuer. Ne repose pas les questions déjà résolues.
