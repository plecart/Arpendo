# Gabarit de plan de QA

Squelette par défaut du corps d'issue GitHub pour un plan de QA. Remplace les espaces réservés.

**Deux règles héritées du SKILL, qui priment sur ce gabarit :**

1. **Une surface que le projet n'a pas ne produit aucune section** — pas même une section marquée
   « N/A ». Les surfaces se déduisent de `.claude/pipeline.config.md`. Les sections ci-dessous sont
   un menu, pas une liste à remplir intégralement.
2. **Aucune case ne re-teste ce que la CI couvre déjà.** Pas de « les tests passent », pas de « le
   lint est vert », pas de « le build réussit » : `cycle-pr` et la CI l'ont déjà prouvé. Ce plan ne
   contient que ce qu'un test automatisé ne peut pas voir.

````markdown
# Plan QA : <court périmètre>

## Vue d'ensemble

- **Thème / PRD** : <thème recetté, ou #<issue-prd> — titre>
- **Issues dans le périmètre** : #<a>, #<b>, #<c>
- **Surfaces couvertes** : <celles que le projet possède, d'après la config>
- **Comportements visibles par l'utilisateur dans le périmètre** :
  - <une puce par comportement — langage clair, termes du domaine>
- **Hors périmètre** : <puces>
- **État de départ supposé** : <ex. données vierges, fixtures X seedés, flag Z activé>

## Paliers de sévérité

- **Bloquant** : fuite de sécurité, accès entre comptes, perte de données, entrée dangereuse
  acceptée, workflow central impossible, crash, artefact produit inutilisable.
- **Majeur** : mauvais comportement métier, garde-fou manquant, erreur masquée par un message
  générique, traitement échoué sans erreur exploitable, attente qui ne se termine jamais.
- **Mineur** : formulation, finition visuelle, état vide non bloquant, message peu clair mais
  récupérable.

## Saisie d'échec

Quand une case échoue, capturer le bloc de
`execution-qa/references/gabarit-intake-echec.md` dans la conversation. `bug-vers-issue` le
consomme tel quel. Les champs sans contenu sont supprimés, jamais laissés vides.

## Données de test

- **Fixtures principaux** : <liste, chemins vérifiés contre le dépôt>
- **Fixtures invalides** : <liste>
- **Attentes du cas de référence** : <le cas échéant>

---

## Phase 0 — Préliminaires

**Objectif** : prouver que l'application **démarre et est joignable** dans un environnement réel.
La CI prouve que le code compile et que les tests passent ; elle ne prouve pas qu'il tourne ici.
Ne rien recetter d'autre si cette phase est rouge.

**Checklist** :
- [ ] Les fichiers d'environnement existent et correspondent à l'exemple versionné.
- [ ] L'application démarre — `<commande "run local" de la config>`.
- [ ] Les services dont elle dépend sont montés et joignables.
- [ ] Chaque surface exposée répond — `<url, commande ou point d'entrée par surface>`.
- [ ] La configuration façon production refuse les valeurs par défaut non sûres.

**Règle d'arrêt** : si l'application ne démarre pas, rien d'autre n'est recettable.

---

## Phase 1 — Sécurité & Propriété

*(Section à inclure uniquement si le projet a de l'authentification et des ressources liées à un
utilisateur. Sinon, elle n'apparaît pas dans le plan.)*

**Objectif** : prouver qu'un utilisateur ne peut ni voir ni modifier les ressources d'un autre.

**Préconditions** : deux comptes distincts existent, le premier possède au moins une ressource.

- [ ] Authentification absente → refus attendu.
- [ ] Authentification invalide / expirée → refus attendu, session vidée côté client.
- [ ] Le compte A liste ses propres ressources → volume attendu.
- [ ] Le compte B ne peut ni lister, ni lire, ni modifier, ni exporter les ressources du compte A
      → code conforme à la politique anti-énumération du projet.
- [ ] Aucun refus d'accès ne produit une erreur serveur.
- [ ] Aucune donnée croisée n'est persistée pendant les actions rejetées.

**Règle d'arrêt** : toute donnée visible entre comptes est bloquante.

---

## Bloc de fonctionnalité : Issue #<N> — <Titre court>

**Source** : #<N> | thème/PRD <ref> | commits de livraison : `<sha1>`, `<sha2>`

**Objectif** : <le comportement visible par l'utilisateur, en une phrase>

**Critères d'acceptation** (depuis #<N>) :
- [ ] <critère 1>
- [ ] <critère 2>

<!--
  Une sous-section par surface QUE CE PROJET POSSÈDE. Supprimer celles qui ne s'appliquent pas —
  ne pas les conserver vides. Exemples de sous-sections selon les cas :
-->

**Point d'entrée (API / CLI / commande)** :
- [ ] `<appel>` avec entrée valide → `<résultat attendu, code, forme de sortie>`.
- [ ] `<appel>` avec entrée invalide → `<erreur attendue, visible et exploitable>`.

**Interface** :
- [ ] État vide / chargement / succès / erreur affichés pour `<surface>`.
- [ ] Le détail de l'erreur réelle est visible, pas remplacé par un message générique.
- [ ] Les contrôles sont neutralisés pendant une action en attente.
- [ ] Console et réseau propres — aucune erreur inexpliquée.

**Persistance** :
- [ ] L'enregistrement attendu existe, avec les champs et le rattachement au propriétaire.
- [ ] Aucun enregistrement résiduel pour les tentatives rejetées.

**Traitements asynchrones** :
- [ ] Le traitement atteint son état terminal de **succès**.
- [ ] Sur une variante d'échec, il atteint son état terminal d'**échec**, avec erreur exploitable.
- [ ] Aucune exception non gérée dans les journaux (queue bornée).

**Artefacts produits** :
- [ ] Le fichier / export attendu est produit, au bon emplacement, au bon format.
- [ ] Les originaux sont préservés ; les entrées rejetées ne laissent rien.

**Règle d'arrêt** : <quand s'arrêter et trier avant de continuer>

**Indices de sévérité** : <les défaillances probables de ce bloc, pré-classées>

---

## Phase R — Régression

**Objectif** : les parcours existants fonctionnent toujours après cette livraison. Uniquement des
parcours **manuels** : la non-régression automatisée est le travail de la CI.

- [ ] <parcours antérieur 1> fonctionne toujours de bout en bout — `<commande ou action>`.
- [ ] <parcours antérieur 2> fonctionne toujours — `<commande ou action>`.
- [ ] Aucun nouveau bruit de console / réseau / journaux sur les surfaces antérieures.

**Règle d'arrêt** : une régression sur un comportement déjà livré est au moins majeure.

---

## Phase Finale — Définition du Terminé

- [ ] Chaque case des phases incluses est `[x]`, ou porte une annotation explicite
      (`N/A : <raison>`, `BLOQUÉ`, `accepté : <décision>`).
- [ ] Chaque bloc de fonctionnalité est entièrement traité.
- [ ] Chaque constat bloquant est corrigé, ou explicitement accepté avec la décision consignée.
- [ ] Chaque constat majeur a un lien `🔴 BUG #N` ou une décision `reporté` explicite.
- [ ] Les actions en échec ont été rejouées après correction.

---

## Index des constats

*(`execution-qa` ajoute les liens ici à mesure que les bugs sont déposés via `bug-vers-issue`.)*

- 🔴 #<numéro-issue-bug> — <titre court> — phase / bloc : `<emplacement>`
````
