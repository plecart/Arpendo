# Base de connaissances hors périmètre

Le répertoire `.out-of-scope/` d'un dépôt stocke des traces persistantes des demandes de fonctionnalités rejetées. Il sert deux objectifs :

1. **Mémoire institutionnelle** — pourquoi une fonctionnalité a été rejetée, afin que le raisonnement ne soit pas perdu lorsque l'issue est fermée
2. **Déduplication** — quand une nouvelle issue arrive et correspond à un rejet antérieur, le skill peut faire remonter la décision précédente au lieu de rouvrir le débat

## Structure du répertoire

```
.out-of-scope/
├── dark-mode.md
├── plugin-system.md
└── graphql-api.md
```

Un fichier par **concept**, pas par issue. Les multiples issues demandant la même chose sont regroupées dans un seul fichier.

## Format de fichier

Le fichier doit être rédigé dans un style détendu et lisible — davantage comme un court document de conception que comme une entrée de base de données. Utilise des paragraphes, des extraits de code et des exemples pour rendre le raisonnement clair et utile à quelqu'un qui le découvre pour la première fois.

```markdown
# Dark Mode

Ce projet ne prend pas en charge le mode sombre ni la thématisation côté utilisateur.

## Pourquoi c'est hors périmètre

Le pipeline de rendu suppose une palette de couleurs unique définie dans
`ThemeConfig`. Prendre en charge plusieurs thèmes nécessiterait :

- Un fournisseur de contexte de thème enveloppant l'ensemble de l'arbre de composants
- Une résolution de styles tenant compte du thème par composant
- Une couche de persistance pour les préférences de thème de l'utilisateur

C'est un changement architectural important qui ne s'aligne pas sur le
focus du projet sur la création de contenu. La thématisation est une préoccupation des
consommateurs en aval qui intègrent ou redistribuent la sortie.

```ts
// L'interface ThemeConfig actuelle n'est pas conçue pour un basculement à l'exécution :
interface ThemeConfig {
  colors: ColorPalette; // palette unique, résolue à la compilation
  fonts: FontStack;
}
```

## Demandes antérieures

- #42 — « Add dark mode support »
- #87 — « Night theme for accessibility »
- #134 — « Dark theme option »
```

### Nommer le fichier

Utilise un nom court et descriptif en kebab-case pour le concept : `dark-mode.md`, `plugin-system.md`, `graphql-api.md`. Le nom doit être suffisamment reconnaissable pour que quelqu'un qui parcourt le répertoire comprenne ce qui a été rejeté sans ouvrir le fichier.

### Rédiger la raison

La raison doit être substantielle — pas « on n'en veut pas » mais pourquoi. Les bonnes raisons font référence à :

- Le périmètre ou la philosophie du projet (« Ce projet se concentre sur X ; la thématisation est une préoccupation en aval »)
- Des contraintes techniques (« Prendre en charge cela nécessiterait Y, ce qui entre en conflit avec notre architecture Z »)
- Des décisions stratégiques (« Nous avons choisi d'utiliser A plutôt que B parce que... »)

La raison doit être durable. Évite de faire référence à des circonstances temporaires (« on est trop occupés en ce moment ») — ce ne sont pas de vrais rejets, ce sont des reports.

## Quand consulter `.out-of-scope/`

Pendant le triage (Étape 1 : Rassembler le contexte), lis tous les fichiers de `.out-of-scope/`. Lors de l'évaluation d'une nouvelle issue :

- Vérifie si la demande correspond à un concept hors périmètre existant
- La correspondance se fait par similarité de concept, pas par mot-clé — « night theme » correspond à `dark-mode.md`
- En cas de correspondance, fais-la remonter au mainteneur : « C'est similaire à `.out-of-scope/dark-mode.md` — nous avons rejeté cela auparavant parce que [raison]. Es-tu toujours du même avis ? »

Le mainteneur peut :

- **Confirmer** — la nouvelle issue est ajoutée à la liste « Demandes antérieures » du fichier existant, puis fermée
- **Reconsidérer** — le fichier hors périmètre est supprimé ou mis à jour, et l'issue suit le triage normal
- **Être en désaccord** — les issues sont liées mais distinctes, on poursuit avec le triage normal

## Quand écrire dans `.out-of-scope/`

Uniquement lorsqu'un **enhancement** (pas un bug) est rejeté en `wontfix`. Le déroulé :

1. Le mainteneur décide qu'une demande de fonctionnalité est hors périmètre
2. Vérifier si un fichier `.out-of-scope/` correspondant existe déjà
3. Si oui : ajouter la nouvelle issue à la liste « Demandes antérieures »
4. Si non : créer un nouveau fichier avec le nom du concept, la décision, la raison et la première demande antérieure
5. Publier un commentaire sur l'issue expliquant la décision et mentionnant le fichier `.out-of-scope/`
6. Fermer l'issue avec le label `wontfix`

## Mettre à jour ou supprimer des fichiers hors périmètre

Si le mainteneur change d'avis sur un concept précédemment rejeté :

- Supprime le fichier `.out-of-scope/`
- Le skill n'a pas besoin de rouvrir les anciennes issues — ce sont des traces historiques
- La nouvelle issue qui a déclenché la reconsidération suit le triage normal
