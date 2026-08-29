# Arpendo

Jeu mobile de conquête territoriale en géolocalisation réelle. La carte du monde est recouverte
d'une grille d'hexagones ; **marcher sur un hexagone le fait passer à ta couleur**. Les joueurs
créent une partie, invitent des amis par un code, et pendant une durée choisie — de 30 minutes à un
mois — chacun colore le monde en marchant.

**Accroche :** « prends du terrain » · **Package :** `com.arpendo.game` · **Cible :** Android
d'abord, iOS ensuite · **Langue :** français seul au MVP, architecture i18n dès le jour 1.

---

## Par où commencer

**Tu reprends le projet, ou tu ouvres une session neuve ?** Lis dans cet ordre :

1. `documents/reference/01-cadrage.md` — **§19 en premier**, c'est l'instruction de reprise.
2. `documents/reference/02-specification-ux.md` — la spécification d'interface.
3. Ce README, section « Ce qui reste ouvert ».
4. `UBIQUITOUS_LANGUAGE.md` — le vocabulaire du domaine, extrait du cadrage et de la spec UX.

**Ne rouvre aucune décision du cadrage ni de la spécification UX sans élément nouveau.** Chacune
porte sa justification ; les rouvrir sans raison coûte plus que ce qu'elle rapporte.

---

## Prérequis

| Outil | Rôle | Vérifier |
|---|---|---|
| [`uv`](https://docs.astral.sh/uv/) | Paquets **et** version de Python (3.13) | `uv --version` |
| [`just`](https://just.systems/) | Lanceur des commandes du projet | `just --list` |
| [`fvm`](https://fvm.app/) | SDK Flutter à la version épinglée dans `.fvmrc` | `fvm install` **une fois** après le clone : il crée `.fvm/flutter_sdk`, que le justfile vise directement. `fvm` n'a donc pas besoin d'être dans le PATH ensuite |
| Docker Desktop | Services locaux (`just up`) | `docker compose version` |
| Chaîne Android | Build de l'app | `fvm flutter doctor` sans erreur |

**Ne jamais appeler `flutter` ou `dart` directement** : toujours via `just` ou `fvm`, sinon
c'est le SDK global de la machine qui répond et l'épinglage ne sert à rien. Le détail des
versions est dans `.claude/pipeline.config.md`.

---

## L'état du projet

| Phase | État |
|---|---|
| Cadrage produit, règles du jeu, architecture, hébergement, coûts | **Clos** |
| Étude technique et chiffrage | **Clos** — 25,82 € HT/mois au MVP |
| Spécification UX — écrans, états, textes, composants | **Close** |
| Identité visuelle — direction « Relevé » | **Close**, intégrée dans la spec |
| Maquette de référence | **Reçue** de Claude Design, à arbitrer |
| Développement | **Commencé** — squelettes `api/` et `app/`, CI verte ; suivi par les issues du thème « Socle technique » |

---

## Les documents

### `documents/reference/` — normatif

Ce sont les documents qui font autorité. Toute contradiction entre eux et autre chose se tranche
en leur faveur.

| Fichier | Ce qu'il contient |
|---|---|
| **`01-cadrage.md`** | Le produit, les règles du jeu, la sécurité, le RGPD, l'architecture technique, l'hébergement, les notifications. **19 sections, toutes closes.** Son **§19 est l'instruction de reprise**, son §18 le journal des changements |
| **`02-specification-ux.md`** | La spécification d'interface. Chaque composant avec ses six états, son ergonomie, ses textes exacts. Porte aussi les jetons de conception — espacements, typo, couleurs, mouvement — au §1 |
| **`03-identite-visuelle.md`** | Le raisonnement derrière la direction « Relevé » : la contrainte chromatique découverte par le calcul, les validations ΔE, les ressources SVG, et **pourquoi** les deux autres directions ont été écartées. **Leurs valeurs en ont été retirées** — le projet ne contient qu'une seule palette |
| **`04-chiffrage.md`** | Tarifs relevés à la source le 10 août 2026, scénarios 50 / 500 / 5 000 joueurs |

### `documents/assets/` et `documents/maquettes/` — le design

| Chemin | Contenu |
|---|---|
| `documents/assets/` | Les SVG définitifs de la marque : signe, logotype, icône d'app, marqueur vu de face. **Source unique.** La maquette en garde une copie à l'identique — elle est servie depuis son propre dossier et ne peut pas remonter d'un cran. Toute retouche de la marque se fait ici, puis se recopie ; un `md5sum` des deux fichiers détecte la divergence |
| `documents/maquettes/claude-design-v2/` | La maquette de référence — 8 planches en HTML autonome. **Inspiration, pas norme : en cas de divergence, la spécification l'emporte.** `trace-maquette.md` résume ce qui a été demandé, obtenu, et les deux écarts tranchés en sa faveur |

### `documents/setup/` — comptes et services externes à ouvrir

Les tutoriels des services tiers dont le projet dépend, à dérouler **avant** de coder le domaine
concerné. Ce ne sont pas des décisions produit : ce sont des marches à suivre, mises à jour quand
la console du fournisseur change.

| Fichier | À faire avant |
|---|---|
| `google-oauth.md` | Le domaine *Compte & identité* (spec UX §4) |

### `documents/archive/` — deux pièces, conservées comme justificatifs

**`brief-identite-visuelle.md`** — le questionnaire d'identité rempli le 13 août 2026. C'est la **seule
trace des préférences réelles du porteur**, et la pièce justificative si une décision d'identité est
un jour contestée. **Ne pas s'y référer pour décider** : ce sont des réponses brutes, pas des
conclusions.

**`journal-decisions-ux.md`** — le raisonnement, les options écartées et l'historique des révisions
**retirés de `02-specification-ux.md`**. La spécification ne porte que l'état courant : un
développeur qui la lit ne doit pas avoir à démêler une décision en vigueur d'une décision annulée.
Ce journal recueille ce qui a été retiré, pour que rien ne soit perdu. **Non normatif.**

---

## L'identité visuelle, en un coup d'œil

Direction **« Relevé »** — *une carte de randonnée qu'on aurait apprise par cœur : du papier, un
trait, et la couleur réservée à ce qui compte, le territoire.*

| | Mode clair | Mode sombre |
|---|---|---|
| `accent` | `#123D1E` | `#C9F7BE` |
| `surface` | `#FDFBF6` | `#1A1E1A` |
| `surface-dim` | `#F1EDE2` | `#101310` |
| `on-surface` | `#1A1D18` | `#EDEAE0` |
| `on-surface-muted` | `#5C6157` | `#9CA096` |
| `outline` | `#C7C3B5` | `#3A403A` |

Typographie **Roboto**, zéro octet d'APK. Le jeu complet des onze jetons est au **§1.5 de la spec
UX**.

**Les dix couleurs joueur — intouchables :** `#E9878A` `#BD3216` `#A6841D` `#97C425` `#007559`
`#56C4CA` `#3B6DF4` `#BE85F9` `#773B95` `#EB31A5`. Validées pour le daltonisme, pire paire à
ΔE 9,1 en deutéranopie. **Toute retouche invalide la validation.**

> **La contrainte à ne jamais re-dériver.** Les dix couleurs joueur occupent toute la roue
> chromatique entre L 0,47 et 0,76. Un balayage complet de l'espace OKLCH montre qu'**au-dessus de
> L 0,40, aucune teinte n'est à ΔE ≥ 15 des dix.** Tout accent de mode clair sera sombre, tout
> accent de mode sombre sera pâle, et l'état pressé fonce en clair mais **éclaircit** en sombre.

---

## Ce qui reste ouvert

| # | Point | Échéance |
|---|---|---|
| 1 | **Les CGU et la politique de confidentialité doivent couvrir la visibilité des zones.** La modale qui portait cette information a été retirée de l'interface ; l'obligation est passée aux documents juridiques, et la clause exacte est écrite au **§13.12 du cadrage** | Avant la publication |
| 2 | **La page web de suppression de compte n'existe pas.** Le cadrage §12.2 la donne comme **obligatoire pour Google Play** — « chemin dans l'app **et** URL web ». L'app a son chemin ; la page reste due | Avant la publication |
| 3 | **La modale « Mes hexagones »** — spécifiée au §7.6 du cadrage, **reportée post-MVP**. Ne bloque rien | Post-MVP |
| 4 | **Aucun jeton Mapbox.** Deux sont nécessaires, à ne pas confondre : le jeton **public** (`pk.*`) part dans l'APK pour charger les tuiles — il en est extractible, c'est le risque de facture n°1 du cadrage §13.10 (portées de lecture seules, alerte de budget dès le premier dollar) ; le jeton de **téléchargement** (`sk.*`, portée `DOWNLOADS:READ`) ne sert qu'à récupérer le SDK Android au moment du build et ne doit jamais partir dans l'APK. Ce dernier devra **aussi** exister en secret GitHub Actions (`MAPBOX_DOWNLOADS_TOKEN`) : le step Build de la CI en aura besoin dès que `mapbox_maps_flutter` sera une dépendance | Avant la première dépendance `mapbox_maps_flutter` |
| 5 | **Le sous-ensemble Phosphor n'est pas embarqué.** Le paquet `phosphor_icons` déclare **six graisses** ; le §1.8 n'en emploie qu'une, et les cinq autres pèsent **2,58 Mo** dans l'AAB — mesurés. Un sous-ensemble embarqué — police ou SVG — les supprimerait et rendrait l'inventaire indépendant du paquet | Post-MVP |
| 6 | **Le skill `dataviz` n'est pas épinglé** dans `skills-lock.json` : il est fourni par le runtime. C'est lui qui porte `validate_palette.py`, le validateur normatif de la palette | Avant de revalider la palette sur le style Mapbox réel |
| 7 | **`main` n'est protégé par aucune règle côté GitHub** — indisponible sur un dépôt privé hors plan GitHub Pro. « Jamais de force-push », « jamais d'auto-merge » et « CI verte avant merge » ne tiennent que par `.claude/rules/contraintes.md` | Avant la première PR |

**Tout le reste est clos.** Cadrage, spécification UX, identité visuelle et retour de maquette ont
été arbitrés et intégrés. Les journaux §18.1 à §18.5 du cadrage disent ce qui a changé et pourquoi ;
ils existent pour éviter qu'une décision close soit rouverte sans élément nouveau.

---

## Ce qui n'existe pas encore

- **Presque aucun code applicatif.** `api/` (FastAPI, `GET /health`) et `app/` (Flutter, écran
  vide sur le thème des jetons du §1) sont des squelettes ; chacun a son README. Le worker
  n'existe pas : il naît comme second point d'entrée du paquet `arpendo_api`, avec sa première
  tâche réelle.
- **Pas de modèle glTF du marqueur.** Sa spécification complète est au §3.4.1 de la spec UX ;
  c'est un travail de modeleur, pas de designer.
- **Pas de PDF de spécification complète.** C'est le point 6 du §17 du cadrage.
