# Gabarit d'issue de bug (issue unique)

La forme par défaut du corps d'un bug consigné par `bug-vers-issue`. Remplis les sections ci-dessous ; supprime celles dont le contenu est vide plutôt que de laisser le texte indicatif.

```markdown
## Ce qui s'est passé

<Description en langage clair du comportement réel vécu par l'utilisateur. Langage métier ; aucune référence au code.>

## Ce que j'attendais

<Le comportement attendu, également en langage clair.>

## Étapes pour reproduire

1. <Étape concrète, numérotée, copiable-collable.>
2. <Utilise les termes métier, pas les noms de modules internes.>
3. <Inclus les entrées, comptes, fixtures, flags, variables d'environnement pertinents.>

## Gravité

**<Bloquant | Majeur | Mineur>** — <justification d'une ligne>

## Découvert pendant

<L'un de :>
- Plan QA : #<issue-plan> — phase / bloc : `<emplacement>` — case en échec : `<texte exact>`
- QA libre / signalé par l'utilisateur

## Travaux liés

- **Issue(s) d'implémentation** : #<a>, #<b>
- **PRD** : #<p> — `<titre>` (si connu)
- **Commit(s) à l'origine** : `<sha1>` — `<message du commit>` ; `<sha2>` — `<message du commit>`

## Preuves de l'échec

```text
Bloc QA :          <nom, si piloté par un plan>
Action :           <commande exacte ou séquence d'UI>
Attendu :          <ce que le plan / l'utilisateur attendait>
Observé :          <ce qui s'est réellement passé>
URL / endpoint :   <route, URL de page, ou surface>
Charge utile :     <corps de la requête, expurgé>
Console :          <copier-coller borné de la console du navigateur>
Réseau :           <méthode, URL, statut, extrait de réponse>
Logs API :         <extrait borné de logs>
Logs worker :      <extrait borné de logs>
Lignes DB :        <SQL + extrait de résultat>
Stockage :         <chemins vérifiés + état>
Décision requise : <si l'échec révèle une ambiguïté de politique>
```

(Supprime tout champ sans contenu — ne laisse pas de texte indicatif vide.)

## Contexte additionnel

<Optionnel. Tout ce qui ressort de l'exploration du code et qui aide à cadrer l'issue sans la lier à des fichiers précis. Exemples : « cette surface ne lit que depuis la couche de cache, pas depuis la DB » — formulation métier, sans chemins.>
```

## Règles du titre

- Court (moins de ~70 caractères).
- Langage métier.
- Décrit le problème visible par l'utilisateur, pas le chemin de code.
- Bon : « L'envoi de connaissance accepte des PDF trop volumineux sans les rejeter »
- Mauvais : « uploadHandler.validateSize renvoie true quand fileSize > MAX_BYTES »

## Règles du corps

- Pas de chemins de fichiers, pas de numéros de ligne, pas de noms de symboles internes.
- Étapes de reproduction obligatoires.
- Gravité indiquée avec justification.
- Preuves de l'échec : supprime les champs vides plutôt que de les laisser en `<vide>`.
- Glossaire métier respecté.
