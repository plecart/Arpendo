# Gabarit de découpage (parent + enfants)

À utiliser uniquement lorsque l'utilisateur rapporte des symptômes avec des **causes racines clairement séparables** que différentes personnes pourraient corriger en parallèle. Sinon, consigne une seule issue.

Crée les issues dans l'**ordre des dépendances** : le parent d'abord, puis les enfants sans bloqueurs, puis les enfants bloqués par des enfants précédents. Ainsi chaque champ « Bloqué par » peut référencer de vrais numéros d'issue.

## Issue parente (de suivi)

```markdown
## Résumé

<Un paragraphe énonçant le problème visible par l'utilisateur en langage clair. L'issue parente est un hub — les enfants portent le détail.>

## Enfants

- [ ] #<enfant-1> — <titre court>
- [ ] #<enfant-2> — <titre court>
- [ ] #<enfant-3> — <titre court>

## Découvert pendant

- Plan QA : #<issue-plan> — phase / bloc : `<emplacement>` — case en échec : `<texte exact>`
  (ou « QA libre / signalé par l'utilisateur »)

## Travaux liés

- **Issue(s) d'implémentation** : #<a>, #<b>
- **PRD** : #<p> — `<titre>` (si connu)

## Gravité

**<Bloquant | Majeur | Mineur>** — <justification d'une ligne pour le pire enfant>
```

Titre le parent : `[QA] <description englobante>` — moins de ~70 caractères, langage métier.

## Issue enfant

```markdown
## Parent

#<issue-parente>

## Ce qui ne va pas

<Décris CE problème de comportement précis — juste cette tranche, pas tout le rapport.>

## Ce que j'attendais

<Comportement attendu pour cette tranche.>

## Étapes pour reproduire

1. <Étapes propres à CETTE issue.>

## Gravité

**<Bloquant | Majeur | Mineur>** — <justification d'une ligne>

## Découvert pendant

<Même référence de plan QA que le parent, ou « QA libre ».>

## Travaux liés

- **Issue(s) d'implémentation** : #<a> (si propre à cette tranche)
- **Commit(s) à l'origine** : `<sha>` — `<message>` (si propre à cette tranche)

## Bloqué par

- #<enfant-X> (si cette tranche ne peut être testée ou corrigée tant qu'une autre n'est pas résolue)

(ou « Aucun — peut démarrer immédiatement » s'il n'y a pas de bloqueur)

## Preuves de l'échec

```text
<champs renseignés de l'intake d'échec, en supprimant les vides>
```

## Contexte additionnel

<Optionnel. Tout ce qui aide à cadrer CETTE tranche sans la lier à des fichiers précis.>
```

Titre l'enfant : `<description courte, propre à la tranche>` — moins de ~70 caractères, langage métier.

## Règles du découpage

- **Privilégie l'unique.** La plupart des rapports correspondent à une seule issue, pas trois.
- **Chaque enfant est corrigeable et vérifiable indépendamment.** Si deux tranches doivent être corrigées ensemble pour pouvoir vérifier l'une ou l'autre, c'est une seule issue, pas deux.
- **Marque le blocage honnêtement.** Si la tranche B ne peut vraiment pas être testée tant que la tranche A n'a pas atterri, dis-le. Si elles sont indépendantes, marque chacune « Aucun — peut démarrer immédiatement » pour que plusieurs agents/personnes puissent les prendre en parallèle.
- **Maximise le parallélisme.** L'intérêt d'un découpage est de permettre le travail en parallèle.
- **Mets à jour le plan QA une seule fois avec le parent.** Quand la source était une unique case en échec, remplace `🔴 needs-issue` par `🔴 BUG #<parent>` et ajoute le parent à l'Index des constats. Les enfants apparaissent imbriqués sous le parent dans l'Index des constats, pas comme des entrées de premier niveau distinctes.
