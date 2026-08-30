# Décision — le jeton Mapbox ne part pas dans l'APK

*Archive non normative. L'état courant est au cadrage §13.10 ; ce fichier conserve le
raisonnement, pour qu'il ne soit pas rouvert sans élément nouveau.*

**Date :** 30 août 2026. **Déclencheur :** l'ouverture du compte Mapbox (issue #30), bloc « jeton
public » — le porteur a refusé qu'un jeton extractible de l'APK puisse faire exploser la facture.

## La contradiction

**§ concernés :** 13.0, 13.7, 13.8, 13.10, 16 ; chiffrage §4 et §5 ; README « Ce qui reste
ouvert » n°4 ; issues #4, #30, #37.

Le §13.10 donnait pour contre-mesures « jeton à portée minimale, restrictions d'usage, rotation,
alerte de budget dès le premier dollar facturé ». Vérification à la source le 30 août 2026 :

- Mapbox ne restreint un jeton que par **URL**, mécanisme de navigateur ; la documentation dit
  qu'ajouter une restriction d'URL « makes it unusable by a mobile application ». Il n'existe ni
  restriction par nom de paquet ni par empreinte de signature. **« Restrictions d'usage » était
  faux sur Android**, quel que soit le choix fait ensuite.
- Mapbox n'offre **aucun plafond de dépense** ; seules des alertes existent.
- Deux canaux facturent un jeton volé : les MAU (un SDK usurpé en fabrique à volonté, 4 $ le
  millier au-delà de 25 000) et les requêtes directes de tuiles (0,25 $ le millier au-delà de
  200 000). Le chiffrage ne voyait que le premier.
- Un jeton cuit dans l'APK ne se révoque qu'en publiant une nouvelle version : révoquer, c'est
  casser la carte de tous les joueurs jusqu'à leur mise à jour.

Il ne restait donc que de la détection, jamais de prévention, et une réponse à l'incident qui
coûtait une release.

## Les options

| | Option | Ce qu'elle change | Verdict |
|---|---|---|---|
| A | Statu quo : `pk.` dans l'APK + alerte | Rien — vol anonyme, facture non bornée, révocation par release | Écartée |
| B | **Jeton temporaire `tk.` d'une heure émis par l'api aux sessions authentifiées** | Le vol passe de « n'importe qui avec l'APK, pour toujours » à « un titulaire de compte, une heure à la fois, sous son nom ». Coupure en un clic (suppression du `sk.` serveur). ~½ à 1 jour | **Retenue** |
| C | Proxy des tuiles par le serveur | Contrôle total, mais transit à payer, facturation en tuiles directes plus chère que les MAU, SDK cassé, CGU frôlées | Écartée |
| D | Attestation Play Integrity à la connexion, seule une session attestée obtenant un `tk.` | Ferme le trou résiduel de B (un compte scripté). Exige un vrai appareil non rooté et le vrai APK signé par compte. Quota gratuit 10 000 vérifications/jour, dépend de Play App Signing (#31), ~1 à 2 jours, et un contournement à prévoir pour les builds de développement | **Déclencheur** au §13.7, pas MVP |

## Ce qui a été retenu, et pourquoi sous cette forme

- **Un seul `tk.` partagé par heure, en cache Valkey**, plutôt qu'un par compte : Mapbox
  n'attribue pas l'usage à un jeton temporaire, donc N jetons n'apporteraient aucune traçabilité
  de plus, pour N appels à la Tokens API au lieu d'un. L'attribution vit à l'api — qui a demandé
  un jeton, et à quelle fréquence. Valkey plutôt que la mémoire du processus : c'est le cache
  partagé du cadrage §13.8, et la perte du jeton en cache est indolore (on en émet un autre).
- **Pas de limite de débit propre à la route** : le rate limiting par compte de la story 4 du PRD
  (« étendu par compte dès le premier endpoint authentifié ») la couvre.
- **Le secret serveur porte exactement `tokens:write` + les quatre portées publiques** : les
  portées d'un jeton temporaire sont bornées par celles de son émetteur, donc un `sk.` qui fuit
  n'émet que des jetons de lecture.
- **Aucune ligne de code de coupure** : supprimer le `sk.` dans la console suffit, et c'est plus
  sûr qu'un drapeau qu'il faudrait déployer.
- **Le tableau des risques garde l'alerte et le ratio MAU/joueurs** : ils changent de rôle — de
  seule parade à déclencheur de la coupure.

## Point d'honnêteté

Aucune option ne borne la facture mathématiquement, parce que Mapbox n'offre pas de plafond. B
borne la **fenêtre** (une heure), l'**anonymat** (un compte) et le **délai de réponse** (un clic,
pas une release). C'est ce que A ne bornait pas du tout.

## Sources vérifiées le 30 août 2026

- Mapbox — Tokens API (`POST /tokens/v2/{username}`, expiration ≤ 1 h, portées ⊆ émetteur,
  jetons temporaires non révocables, sans restriction d'URL).
- Mapbox — « How to use Mapbox securely » et « Access tokens » : restrictions d'URL réservées au
  navigateur, incompatibles avec les SDK natifs.
- Mapbox — Pricing : Maps SDKs for Mobile 25 000 MAU gratuits puis 4 $/1 000 ; Vector Tiles API
  200 000 requêtes gratuites puis 0,25 $/1 000 ; aucun plafond de dépense.
- Maps SDK Android v11 : `MapboxOptions.accessToken` modifiable à tout moment du cycle de vie,
  pris en compte par les requêtes suivantes.
- Play Integrity : quota par défaut 10 000 requêtes/jour par projet Cloud.

## Répercussion faite

Cadrage §13.0, §13.7, §13.8, §13.10, §16, journal §18.7 · chiffrage §4, §5 · README n°4 ·
`documents/setup/mapbox.md` (procédure) · PRD #4 (story 114, story 119 neuve, décisions
d'implémentation, points de faisabilité) · issues #30 et #37 · issue neuve pour la route
d'émission.
