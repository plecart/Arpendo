# Arpendo — infra

Deux piles Docker Compose, un seul paquet applicatif (cadrage §13.0) :

| Fichier | Rôle | Qui la lève |
|---|---|---|
| `docker-compose.yml` | la pile **locale** : PostgreSQL et Valkey en conteneurs, `api` en `--reload`, `worker`, trois ports publiés sur la boucle locale | `just up`, depuis la racine, avec le `.env` de la racine — README d'`api/` |
| `compose.prod.yml` + `Caddyfile` | la pile de **production** : `caddy`, `api`, `worker`, `valkey`, PostgreSQL **managé** à côté (§13.7) | personne avant #47 : le déploiement, le `.env` du serveur et l'amorçage de la machine sont son périmètre |

## Topologie de production

```
Internet ──443/tcp──▶ caddy ──▶ api:8000 ─┬──▶ valkey:6379          réseau 10.89.45.0/24, interne
                      (TLS,     worker ───┘                          (sous-réseau fixé, hors du
                      X-Forwarded-For)                                pool par défaut de Docker)
                                api, worker ──▶ PostgreSQL managé   réseau privé Scaleway, hors compose
```

**Ce qui est exposé : le port 443 de `caddy`, et rien d'autre.** `api`, `worker` et `valkey` n'ont
aucun `ports:` ; ils se joignent par nom de service sur le réseau du compose, dont le sous-réseau
est **fixé** (`ipam`) parce que `api` ne croit le `X-Forwarded-For` que d'un pair de ce CIDR
(`FORWARDED_ALLOW_IPS`, cadrage §13.7). Il est pris **hors** du pool que Docker distribue lui-même
(172.17–172.31.0.0/16, 192.168.0.0/16) : un /24 posé dedans entre en collision avec tout projet
voisin qui aurait décroché ce /16 — la préproduction du §13.7, par exemple (« Pool overlaps with
other one », mesuré). #47 ne doit pas non plus le donner au Private Network Scaleway.

Le nom de projet est `arpendo` (`name:` en tête du fichier), jamais celui du répertoire : `infra`
est déjà le projet de la pile de développement, et un `down` sur ce fichier la viserait.
`COMPOSE_PROJECT_NAME` le surcharge — c'est ainsi que #47 distingue la **préproduction** (second
projet, second `.env`, second sous-réseau, second sous-domaine).

`caddy` ne dépend d'`api` que par `service_started`, pas `service_healthy` : un reverse proxy
réessaie à chaque requête, et conditionner son démarrage à la santé de l'api empêcherait
l'émission du certificat tant que la base n'est pas jointe — au premier déploiement, un site noir
au lieu d'un 502.

Caddy sert `{$API_DOMAIN}` en TLS automatique. Le port 80 étant fermé par le pare-feu du
fournisseur (§13.10), le défi ACME se fait en **TLS-ALPN-01 sur 443** ; HTTP/3 est désactivé
(`protocols h1 h2`) puisque seul TCP 443 est publié. Le `reverse_proxy` porte `flush_interval -1`
sur toutes les réponses : la SSE n'est jamais tamponnée (§13.7), sans dépendre d'un chemin de route
qui n'existe pas encore ni de l'heuristique de type MIME de Caddy.

## Durcissement — la table du cadrage §13.10, ligne à ligne

Chaque service de `compose.prod.yml` porte, par l'ancre `x-durci` ou en propre :

| Mesure | Dans le fichier | Gardé par |
|---|---|---|
| Un seul port publié | `ports: ["443:443"]` sur `caddy` seul | `test_seul_caddy_publie_un_port_et_c_est_443` |
| Non-root | `user:` sur `caddy` (65534) et `valkey` (999) ; `USER arpendo` dans `api/Dockerfile` pour `api` et `worker` | `test_chaque_service_tourne_sous_un_utilisateur_non_root` |
| Lecture seule + tmpfs | `read_only: true` ; `/tmp` pour `api` et `worker`, `/data` pour `valkey`, `/config` (mode 1777) pour `caddy` | `test_chaque_service_a_un_systeme_de_fichiers_en_lecture_seule` |
| Aucune capacité superflue | `cap_drop: [ALL]`, `no-new-privileges` ; **un seul réajout**, `NET_BIND_SERVICE` sur `caddy` | `test_chaque_service_abandonne_toutes_les_capacites` |
| Socket Docker jamais monté | aucun volume `docker.sock` | `test_aucun_service_ne_monte_le_socket_docker` |
| Images épinglées par empreinte | `caddy:2@sha256:…`, `valkey/valkey:8@sha256:…` ; l'image du paquet est `${ARPENDO_IMAGE:?…}`, publiée par #47 | `test_images.py` |
| Valkey authentifié | `--requirepass` dans `VALKEY_EXTRA_FLAGS`, et `--save ""` : aucune persistance | `test_valkey_exige_un_mot_de_passe` |
| Limites de ressources | `mem_limit` et `cpus` par service, somme commentée pour le DEV1-S | `test_chaque_service_est_borne_redemarre_et_sonde` |
| Redémarrage et sondes | `restart: unless-stopped` ; `healthcheck` sur chaque service — celui du `worker` redéclaré sur la fraîcheur de son battement | idem |
| Arrêt gracieux | `stop_grace_period: 30s` sur **chaque** service (§13.7 : « ne jamais s'en remettre au défaut », 1 s sur Docker 29.2.1) ; borne uvicorn sous `:?` pour `api`, `grace_period 25s` du Caddyfile pour `caddy` — tous deux sous le délai | `test_compose_prod.py`, `test_compose.py` |

Les gardes tournent dans `just test` ; ils lisent le YAML, pas Docker.

**Pourquoi `NET_BIND_SERVICE`, et pourquoi pas ailleurs.** Ce n'est pas pour le port : dans un
conteneur Docker, 443 n'est pas privilégié (`ip_unprivileged_port_start=0` dans l'espace réseau —
mesuré, un `bind` sous un uid quelconque sans aucune capacité réussit). La raison est que
`/usr/bin/caddy` porte une **capacité de fichier** (`getcap` → `cap_net_bind_service=ep`) et que le
noyau refuse l'`exec` d'un tel binaire quand la capacité manque à l'ensemble *bounding* :
`operation not permitted`, avant la première ligne de journal.

## Le volume de Caddy appartient à l'uid 65534 — à poser avant le premier `up`

Caddy doit **persister** `/data` (certificats, clés, compte ACME — la doc officielle : « must not be
treated as a cache » ; le perdre à chaque redéploiement épuiserait la limite d'émission de Let's
Encrypt). C'est le volume nommé `caddy-data`. Or un volume nommé neuf hérite `root:root 755` de
l'image, et `caddy` tourne sous `65534` : **sans chown préalable, Caddy ne peut pas écrire ses
certificats et s'arrête à son premier démarrage** — visible aussitôt dans `docker compose ps` et
ses journaux. Rien dans `compose.prod.yml` ne peut le corriger sans un conteneur root, ce que le
fichier s'interdit ; c'est le **script d'amorçage de #47** qui crée le volume et le donne à 65534,
une fois par machine, et à rejouer après tout `docker volume rm` :

```
docker volume create arpendo_caddy-data
docker run --rm -v arpendo_caddy-data:/data caddy:2@sha256:<empreinte du compose> chown -R 65534:65534 /data
```

Le constater : `docker run --rm -v arpendo_caddy-data:/data alpine stat -c %u /data` → `65534`.
`/config` n'a pas besoin de ce geste : tmpfs en mode 1777. Le préfixe `arpendo_` est le nom de
projet ; il change avec `COMPOSE_PROJECT_NAME` (préproduction).

## Comment vérifier, sans rien lever

Depuis la racine du dépôt. Les valeurs de poste (`ARPENDO_IMAGE=arpendo-api:dev`,
`API_DOMAIN=localhost`) sont dans `.env.example` ; un `.env` qui ne porte pas la section
« Production » est refusé sous `:?` — la recopier.

```
# Le compose interpolé, tel que Compose le lit — chaque `:?` doit être satisfait :
docker compose -f infra/compose.prod.yml --env-file .env config

# Le Caddyfile, validé par l'image épinglée du compose, sous l'utilisateur et les contraintes du
# service (des tmpfs remplacent le volume : `validate` provisionne une CA interne pour localhost) :
IMAGE_CADDY=$(docker compose -f infra/compose.prod.yml --env-file .env config --images | grep '^caddy')
docker run --rm --user 65534:65534 --cap-drop ALL --cap-add NET_BIND_SERVICE --read-only \
  --tmpfs /data:mode=1777 --tmpfs /config:mode=1777 \
  -v "$PWD/infra/Caddyfile:/etc/caddy/Caddyfile:ro" -e API_DOMAIN=localhost \
  "$IMAGE_CADDY" caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
```

La CI joue ces deux commandes à chaque PR (job `image`, avec `.env.example`). Sous Git Bash,
préfixer `MSYS_NO_PATHCONV=1` pour que le chemin du `-v` ne soit pas réécrit.

**Sur une machine où la pile tourne**, les options de durcissement se lisent sur les conteneurs,
pas dans le fichier :

```
docker inspect <conteneur> --format \
  'user={{.Config.User}} ro={{.HostConfig.ReadonlyRootfs}} drop={{.HostConfig.CapDrop}} add={{.HostConfig.CapAdd}} sec={{.HostConfig.SecurityOpt}} mem={{.HostConfig.Memory}} cpus={{.HostConfig.NanoCpus}}'
```

## Ce que #47 vérifie sur la machine — et que rien ici ne prouve

- **TLS** : un certificat public émis pour `API_DOMAIN`, renouvelé sans intervention — donc le
  volume `caddy-data` bien possédé par 65534 et conservé entre deux déploiements.
- **SSE sans tampon** : un flux ouvert à travers `caddy` reçoit chaque événement à l'instant où
  `api` l'émet, pas par paquets.
- **IP réelle** : le limiteur de #41 compte l'adresse du client, pas celle de `caddy` — clé
  `ratelimit:ip:<adresse publique>` dans Valkey, jamais une adresse en `10.89.45.`.
- **Arrêt gracieux** : `docker compose stop api` et `… stop caddy` rendent 0 dans le délai, jamais
  137 — mesuré sur le poste pour `caddy` seul (`grace period initiated, duration 25`, code 0),
  jamais encore avec un flux SSE ouvert à travers lui.
