# Thèmes (milestones GitHub)

Pendant le triage, chaque issue est rattachée à un **thème** afin de regrouper les issues par
sujet. Le thème est matérialisé par un **milestone GitHub**.

Les milestones sont utilisés ici de façon **purement thématique** : un nom et une description
courte, **aucune date d'échéance ni sémantique de release**. C'est un détournement assumé du
milestone GitHub comme étiquette de regroupement.

## Une seule taxonomie : les domaines

Les **domaines** déclarés dans `.claude/pipeline.config.md` (section « Périmètre ») sont la
**source de vérité** du découpage par sujet. Un thème n'est rien d'autre que la **matérialisation
GitHub d'un domaine** : même nom, même périmètre. On ne maintient jamais deux vocabulaires
concurrents.

| | Domaine (`pipeline.config.md`) | Thème (milestone GitHub) |
|---|---|---|
| Rôle | **cadrer le travail** — `vers-issues`, `plan-qa`, `cycle-pr` | **regrouper les issues** côté GitHub |
| Défini par | `init-projet`, au setup ou en reconfiguration | `triage`, à partir du domaine |
| Nom | `Authentification` | `Authentification` — identique |

Autrement dit : le domaine se déclare une fois, le thème se crée à la demande **à son image**.

## Règle

- Toute issue qui **avance dans le triage** (`needs-triage`, `needs-info`, `ready-for-agent`,
  `ready-for-human`) est rattachée à **exactement un thème**.
- Une issue fermée en **`wontfix` est exemptée** — on ne lui assigne pas de thème.
- Comme un milestone GitHub est unique par issue, « exactement un thème » est garanti par
  construction.

## Choisir un thème

1. **Lire les domaines déclarés** dans `.claude/pipeline.config.md`. Chercher celui qui couvre
   l'issue **par concept, pas par mot-clé** — « écran de connexion » relève du domaine
   `Authentification`, « lenteur au chargement » de `Performance`.
2. **Si un milestone porte déjà ce nom**, y rattacher l'issue.
3. **Sinon, créer le milestone au nom exact du domaine** (création automatique, sans demande de
   permission) et **annoncer au mainteneur** le thème créé.
4. **Si aucun domaine ne couvre l'issue**, c'est un signal — ne pas créer de thème orphelin en
   silence. Deux cas, à trancher avec le mainteneur :
   - l'issue est **hors du périmètre du projet** → candidate à `wontfix` (voir
     [hors-scope.md](hors-scope.md)) ;
   - la **liste de domaines est incomplète** → proposer d'ajouter le domaine à la config via
     `init-projet` en mode reconfiguration, puis créer le thème correspondant.

Cette boucle est ce qui garde les deux listes alignées dans le temps : un thème ne peut pas
apparaître sans que le domaine correspondant existe.

## Nommer un thème

Le nom du thème **est** le nom du domaine, repris tel quel — court, lisible, en **français** :
`Authentification`, `Facturation`, `Performance`, `Imports CSV`. La description d'une ligne du
milestone reprend le périmètre du domaine (« Connexion, sessions, gestion des comptes et
permissions »).

## Commandes (`gh`)

Le mapping rôle → label de `.claude/pipeline.config.md` ne concerne pas les thèmes ; les milestones
sont des objets GitHub natifs. Le dépôt cible (`owner/repo`) et les domaines viennent de cette même
config.

```bash
# Lister les thèmes existants (titres + descriptions)
gh api "repos/{owner}/{repo}/milestones" --jq '.[] | "\(.title) — \(.description)"'

# Créer un thème (purement thématique, sans date)
gh api "repos/{owner}/{repo}/milestones" -f title="Authentification" \
  -f description="Connexion, sessions, gestion des comptes et permissions" -f state=open

# Rattacher une issue à un thème
gh issue edit <numéro> --milestone "Authentification"
```

`gh issue edit --milestone` exige que le milestone existe déjà : crée-le d'abord si nécessaire.

## Renommer ou fusionner des thèmes

Les thèmes dérivent avec le temps. Quand deux thèmes se recouvrent ou qu'un nom devient flou :

- Le mainteneur peut demander une fusion. Réassigne les issues du thème absorbé vers le thème
  cible (`gh issue edit --milestone`), puis ferme le milestone vidé.
- **Répercute le changement sur les domaines** de `.claude/pipeline.config.md` : renommer ou
  fusionner un thème sans toucher au domaine recrée exactement la divergence que cette page évite.
- Ne supprime pas un milestone qui porte encore de l'historique utile ; ferme-le plutôt.

Ces opérations de réorganisation ne se font que **sur demande explicite** du mainteneur —
l'auto-création ne concerne que l'assignation d'une issue en cours de triage.
