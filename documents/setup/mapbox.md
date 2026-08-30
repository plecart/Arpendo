# Mise en place des jetons Mapbox

À faire **avant** la première dépendance `mapbox_maps_flutter`. Référence produit : cadrage
§13.10 (le risque financier n°1 et son dispositif), §13.7 (déclencheur Play Integrity),
chiffrage §4 et §5.

---

## Le piège à connaître avant de commencer

**Aucun jeton Mapbox ne part dans l'APK.** Mapbox ne sait restreindre un jeton que par URL de
navigateur — et cette restriction rend le jeton inutilisable par un SDK mobile. Il n'existe ni
restriction par nom de paquet, ni plafond de dépense. Un jeton `pk.` embarqué serait extractible,
anonyme et irrévocable sans nouvelle release. L'app demande donc à l'api un **jeton temporaire**
(`tk.`, une heure au plus), et c'est l'api qui détient le seul secret.

**Les portées décident du préfixe.** Cocher une seule portée secrète (`tokens:write`,
`downloads:read`, `styles:write`, `styles:list`…) fait émettre un `sk.` au lieu d'un `pk.`. Le
préfixe obtenu est donc un contrôle : un jeton qui n'a pas le préfixe attendu a une portée de
trop ou de moins — le recréer.

**Ne jamais employer « les portées publiques » comme raccourci.** Mapbox n'en publie aucune liste
figée : il les définit par la propriété `public` de `GET /scopes/v1/{username}`, et l'ensemble peut
bouger. Le projet en veut **quatre**, nommées une à une : `styles:tiles`, `styles:read`,
`fonts:read`, `datasets:read`. La console en coche davantage — `vision:read` au 30 août 2026,
constaté en console (issue #30) — et le Vision SDK n'est nulle part dans la stack : la décocher
partout.

Le contrôle du préfixe se fait par **oui ou non** — « commence-t-il bien par `sk.` ? ». Ne jamais
demander d'en citer une partie : la réponse la plus simple à une telle question est de coller le
jeton entier.

---

## 1. Les trois jetons

Console : <https://console.mapbox.com/account/access-tokens/>. **Un jeton par usage**, nommé par
son usage, jamais réutilisé d'un usage à l'autre.

| Nom | Portées | Préfixe attendu | Où il vit | À quoi il sert |
|---|---|---|---|---|
| `arpendo-api-tokens` | `tokens:write` **+** `styles:tiles`, `styles:read`, `fonts:read`, `datasets:read` — **rien d'autre**. La console pré-coche `vision:read` : la décocher avant d'enregistrer | `sk.` | `.env` du serveur (`MAPBOX_TOKENS_SECRET`) et `.env` du poste ; **jamais** en secret CI, jamais dans l'image | Émet les jetons temporaires servis à l'app. Ses portées sont le plafond de ce qu'un jeton temporaire peut recevoir : s'il fuit, il ne sait émettre que des jetons de lecture |
| `arpendo-ci-downloads` | `downloads:read` seule | `sk.` | Secret GitHub Actions `MAPBOX_DOWNLOADS_TOKEN` et `.env` du poste | Télécharge le SDK Android au build. Ne quitte jamais la machine de build |
| `arpendo-devkit` | les quatre portées publiques de lecture ; `vision:read` décochée elle aussi | `pk.` | `MAPBOX_DEVKIT_TOKEN` de `.claude/settings.local.json` (hors dépôt) | Laisse démarrer le serveur MCP DevKit (`CLAUDE.md`) ; ses outils de validation sont locaux |

Le nom d'utilisateur Mapbox du compte va aussi dans le `.env` (`MAPBOX_USERNAME`) : la Tokens API
l'exige dans son chemin. Les deux variables arrivent dans `.env.example` avec l'issue qui les lit,
jamais avant.

## 2. L'alerte de budget

**Account → Billing → alerte dès le premier dollar facturé.** Seuil effectif : 25 000 MAU/mois
(chiffrage §4). Elle ne prévient pas l'abus, elle le **détecte** — la réponse est en §4.

## 3. Ce que fait l'api avec `arpendo-api-tokens`

Pour que la procédure et le code disent la même chose :

- `POST https://api.mapbox.com/tokens/v2/{MAPBOX_USERNAME}?access_token={MAPBOX_TOKENS_SECRET}`
  avec `{"expires": <ISO 8601, ≤ 1 h>, "scopes": ["styles:tiles", "styles:read", "fonts:read",
  "datasets:read"]}` rend un `tk.`. Ces quatre-là et pas `vision:read`.
- Un **seul** `tk.` est partagé par tous les clients, mis en cache dans Valkey avec une durée de
  vie inférieure à son expiration, pour que l'app reçoive toujours un jeton qui a encore quelques
  minutes devant lui. Une émission par heure, quel que soit le nombre d'instances d'api.
- La route est **authentifiée** et sous le rate limiting par compte (cadrage §12.4). Un jeton
  temporaire ne s'obtient qu'avec une session Arpendo valide.
- Un `tk.` ne se révoque pas : il expire. C'est le secret d'émission qu'on coupe (§4).

## 4. Coupure et rotation

**Coupure — en cas d'alerte ou de divergence du ratio MAU / joueurs actifs réels :**

1. Console Mapbox → supprimer `arpendo-api-tokens`. Tous les `tk.` en circulation meurent en une
   heure au plus. L'api répond alors en erreur sur la route d'émission ; la carte passe dans son
   état « Erreur » (spec UX §7), sans release ni action des joueurs.
2. Identifier le compte qui demandait les jetons (journal des requêtes, compteurs de rate limit)
   et le passer `banned` (cadrage §12.6).
3. Recréer le secret (étape 1), le poser dans le `.env` du serveur, redémarrer l'api. Le service
   reprend au premier jeton émis.

**Rotation — au moins tous les 90 jours, ou après tout soupçon de fuite du `.env` :** créer le
nouveau `sk.` **avant** de supprimer l'ancien, poser le nouveau dans le `.env`, redémarrer l'api,
vérifier qu'un jeton est émis, puis supprimer l'ancien. Le cache Valkey n'a rien à savoir : le
`tk.` en cache reste valide jusqu'à son expiration, quel que soit le secret qui l'a émis.

Le jeton de téléchargement se tourne de la même façon, secret GitHub Actions compris. Le jeton
DevKit n'a rien à protéger : le recréer si besoin.

---

## Ce qui reste ouvert, et son déclencheur

Un titulaire de compte Arpendo peut demander un jeton frais chaque heure. Ce risque est
attribuable, limité par compte et bannissable. Le durcissement suivant est l'**attestation Play
Integrity à la connexion** — seule une session attestée obtient un jeton — dont le déclencheur
est écrit au cadrage §13.7 : divergence du ratio MAU / joueurs, ou publication publique. Il
dépend de Play App Signing (`documents/setup/google-oauth.md`, « Avant la publication »).

Rappel du cadrage §13.10 : **2FA obligatoire** sur le compte Mapbox, codes de récupération hors
ligne.
