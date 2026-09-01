# Arpendo — Chiffrage des coûts

*Annexe au document de cadrage (`01-cadrage.md`, §17 point 2).*

> **Ce document ne contient que ce que le projet va payer.** Les comparatifs de fournisseurs et
> les architectures écartées ont été retirés : la décision est prise et documentée en §13.7 du
> cadrage.
>
> **Tarifs relevés à la source le 10 août 2026**, après les hausses Scaleway du 1er juin 2026.
> Tous les montants Scaleway sont **hors taxes**, convertis en mensuel sur la base de **730 heures**.
> Les postes marqués ⛔ n'ont pas pu être vérifiés et ne sont pas chiffrés.

---

## 1. La facture d'aujourd'hui — bêta fermée, ~50 joueurs

Architecture : un serveur unique Scaleway en région Paris exécutant quatre conteneurs
(`caddy`, `api`, `worker`, `valkey`), plus PostgreSQL managé sur réseau privé.

| Poste | Détail | € HT/mois |
|---|---|---|
| Serveur applicatif | DEV1-S — 2 vCPU, 2 Go | 6,56 |
| Disque du serveur | Block Storage 5K, 20 Go | 1,99 |
| Snapshot du serveur | 20 Go | 0,64 |
| IPv4 flexible | 0,005 €/h | 3,65 |
| **PostgreSQL managé** | DB-DEV-S — 2 vCPU, 2 Go | 11,39 |
| Stockage + sauvegarde de la base | 10 Go + 10 Go | 1,29 |
| Noms de domaine `.com` + `.fr` | 12,34 + 5,98 €/an | 1,53 |
| **TOTAL** | | **27,05 € HT** |
| | | **32,46 € TTC** |

> **TVA — tranché le 30 août 2026 : compte Scaleway au nom d'un particulier, +20 %.** Le **TTC est
> donc le budget de référence**, pas le HT. L'ancienne branche « structure avec numéro de TVA
> intracommunautaire, autoliquidation » était inexacte : Scaleway SAS est français et facture la
> TVA française à une entreprise française comme à un particulier. Le seul régime qui rendrait la
> TVA récupérable est l'assujettissement au réel — hors de portée d'une auto-entreprise en
> franchise en base, d'où le choix du compte personnel.

### Ce qui est à 0 € et le restera

| Poste | Pourquoi c'est gratuit |
|---|---|
| **Mapbox** | Palier gratuit de **25 000 MAU/mois**. Le scénario le plus large du cadrage en compte 5 000 |
| **Licence de géolocalisation** | Tracelet, Apache 2.0 (§13.2) |
| **Sentry** | Plan Developer : 1 utilisateur, 5 000 erreurs/mois, 5 Go de logs, 5 M spans, rétention 30 jours, **1 moniteur d'uptime** |
| **TLS** | Caddy + Let's Encrypt, automatique |
| **DNS** | Gratuit : la zone d'un domaine enregistré chez Scaleway ne se facture pas. Le tarif de 0,007 €/h (**5,11 €/mois**) ne vise que la zone d'un domaine **externe** hébergée chez Scaleway — un registrar tiers fournit sa propre zone gratuitement, et un enregistrement A vers l'IPv4 suffirait. Ce n'est donc pas ce qui a fait choisir Scaleway comme registrar : c'est le prix au **renouvellement** (`.com` 12,34 contre 13,49 chez OVH ; `.fr` 5,98 contre 7,79, HT/an) |
| **Réseau privé** | Private Networks Scaleway : gratuits |
| **Pare-feu** | Groupes de sécurité inclus |
| **Préproduction** | Seconde base sur la même instance managée + second projet `docker compose` sur le même serveur (§13.7) |
| **Valkey** | Conteneur sur le serveur, aucun coût marginal |

### Frais hors abonnement

| Poste | Montant | Quand |
|---|---|---|
| Compte développeur Google Play | **25 $**, une seule fois | Avant la première publication |
| Compte développeur Apple | **99 $/an** | Phase 2 seulement — iOS est repoussé (§3) |

---

## 2. Ce que le projet paiera, et à quel signal exactement

Chaque dépense future est attachée à un **événement observable**, jamais à une intention.

| Déclencheur | Ce qu'on active | Delta |
|---|---|---|
| L'application quitte la piste de test interne pour une **publication publique** | Edge Services Starter + WAF | **+4,99 €/mois** |
| Même jour | Sortie de la gamme « Development » : DEV1-S → BASIC2-A2C-4G. Scaleway positionne explicitement les DEV1 pour « construire, tester et déployer de petites applications » | **+10,23 €/mois** |
| Le quota de **5 000 erreurs/mois** de Sentry Developer est atteint | Sentry Team | **+26 $/mois** |
| Une **seconde instance d'API sur une seconde machine** devient nécessaire | Second serveur PRO2-XXS 40,95 + son disque, snapshot et IPv4 8,17 + Load Balancer LB-S 16,79 + Redis managé RED1-MICRO 35,04 | **+100,95 €/mois** |
| La base sature | Montée d'un cran (voir l'échelle ci-dessous) | variable |

---

## 3. Trajectoire de coût

Hypothèse de dimensionnement : le nombre de joueurs pilote la taille de la base via le volume de
`capture_event` (12 mois) et de `position_batch` (72 h). **C'est une estimation d'ingénierie, pas
une donnée vérifiée** — à recalibrer par le test de charge prévu en §13.11.

| | Aujourd'hui ~50 | Public ~50-100 | ~500 | ~5 000 |
|---|---|---|---|---|
| Serveur | DEV1-S 6,56 | BASIC2-A2C-4G 16,79 | BASIC2-A2C-8G 25,19 | 2 × PRO2-XXS 81,90 |
| Disque + snapshot | 2,63 | 2,63 | 5,25 | 10,51 |
| IPv4 | 3,65 | 3,65 | 3,65 | 7,30 |
| Load Balancer | — | — | — | 16,79 |
| Redis managé | — | — | — | 35,04 |
| PostgreSQL | DEV-S 11,39 | DEV-S 11,39 | DEV-M 27,89 | PRO2-XXS 80,30 |
| Stockage base | 1,29 | 1,29 | 6,46 | 25,86 |
| Edge + WAF | — | 4,99 | 4,99 | 20,79 |
| Sentry | — | — | 24,00 | 24,00 |
| Domaines `.com` + `.fr` | 1,53 | 1,53 | 1,53 | 1,53 |
| Mapbox | 0,00 | 0,00 | 0,00 | 0,00 |
| **TOTAL HT** | **27,05 €** | **42,27 €** | **98,96 €** | **304,02 €** |
| **TOTAL TTC** | **32,46 €** | **50,72 €** | **118,75 €** | **364,82 €** |

**Le budget de 150 €/mois tient jusqu'à environ 500 joueurs** en HT comme en TTC, et se rompt
entre 500 et 5 000. À ce stade le jeu doit être monétisé — ce qui était prévu dès §3
(« budget avant revenus »).

**La marche n'est pas une falaise.** Entre le palier actuel et le palier production, la base
monte par crans successifs : `DB-DEV-S 11,39 € → DB-PLAY2-PICO 17,01 € → DB-DEV-M 27,89 €
→ DB-PLAY2-NANO 31,54 € → DB-DEV-L 55,19 € → DB-PRO2-XXS 80,30 €`. Côté serveur :
`DEV1-S 6,56 € → DEV1-M 14,75 € → BASIC2-A2C-4G 16,79 € → BASIC2-A2C-8G 25,19 €
→ DEV1-L 31,27 € → PRO2-XXS 40,95 €`.

À 5 000 joueurs, **l'architecture change** : seconde machine, répartiteur de charge et Redis
managé. Ce palier est un ordre de grandeur, pas un devis — il devra être rechiffré le moment venu.

---

## 4. Mapbox — le seul poste dont la facture n'est pas bornée

Les applications construites avec le Maps SDK for Android sont facturées au **monthly active
user (MAU)**, catégorie *Maps SDKs for Mobile*.

| Tranche de MAU mensuels | Coût par tranche de 1 000 |
|---|---|
| **Jusqu'à 25 000** | **Gratuit** |
| 25 001 – 125 000 | 4,00 $ |
| 125 001 – 250 000 | 3,20 $ |
| 250 001 et au-delà | 2,40 $ |

**Deux règles de comptage qui comptent :** un utilisateur devient MAU dès qu'il **affiche une
carte** ; et **désinstaller puis réinstaller consomme un MAU supplémentaire**. Le ratio
MAU / joueurs réels n'est donc **jamais égal à 1**.

**Seuils :** premier euro à 25 001 MAU · 10 $ à 27 500 · 50 $ à 37 500 · **100 $ à 50 000** ·
500 $ à 156 250. La progression est linéaire et douce — **Mapbox n'est pas un mur de croissance.**

⚠️ **Le risque est l'abus d'un jeton, pas la croissance.** Deux canaux facturent qui détient un
jeton valide : les MAU ci-dessus (un SDK usurpé en fabrique à volonté) et les **requêtes directes
de tuiles** — 200 000 gratuites par mois, puis 0,25 $ le millier. Un total de 200 000 MAU
coûterait **640 $/mois**, sans aucun signal préalable. C'est le seul poste du projet capable de
produire une facture surprise à trois chiffres — d'où le dispositif du cadrage §13.10 : aucun
jeton dans l'APK, un jeton temporaire d'une heure émis par l'api aux sessions authentifiées,
coupure par suppression du secret serveur.

---

## 5. Alertes de budget à configurer

Classées par dégât maximal possible, pas par coût nominal.

| Priorité | Poste | Garde-fou |
|---|---|---|
| **1** | **Mapbox** | Alerte **dès le premier dollar facturé** (seuil 25 000 MAU). Aucun jeton dans l'APK : jeton temporaire d'une heure émis par l'api, secret serveur à portée minimale, coupure par suppression de ce secret (cadrage §13.10, `documents/setup/mapbox.md`). **Surveiller le ratio MAU / joueurs actifs réels** — une divergence est la signature d'un abus |
| **2** | **Sentry** | Filtrage entrant et échantillonnage configurés **dès le jour 1**, en même temps que le scrubbing PII (§13.10). 5 000 erreurs se consomment en heures si une exception boucle en arrière-plan |
| **3** | **Edge Services / WAF** *(une fois activé)* | Alerte à 80 % du quota de 5 M requêtes/mois. ⛔ Comportement au dépassement sur le plan Starter à confirmer auprès du support |
| **4** | **Stockage PostgreSQL** | Croît de façon monotone ; la facture ne redescend jamais. Les purges de §12.3 (72 h / 12 mois) **sont le garde-fou de coût**, pas seulement une obligation RGPD |
| **5** | Compte Scaleway | Alerte globale à 50 € puis 100 € HT |

> **Ce qui n'a pas besoin d'alerte :** le serveur et PostgreSQL managé sont facturés à la
> **capacité provisionnée**. Leur facture est prévisible au centime et ne peut pas déraper toute
> seule. N'alerter que là où la facture peut surprendre — sinon on s'habitue à les ignorer.

---

## 6. À vérifier avant d'engager quoi que ce soit ⛔

1. **Raccordement de l'instance PostgreSQL managée au Private Network.** Toute l'architecture
   repose dessus : c'est ce qui permet à la base de n'avoir aucune IP publique, et c'est
   l'argument qui a fait retenir le même fournisseur pour le serveur et la base.
2. ~~Régime de TVA applicable.~~ **Tranché le 30 août 2026** : compte particulier, +20 %, budget de référence en TTC.
3. **Comportement au dépassement des 5 M requêtes WAF** sur les plans Starter et Professional.
4. **Taux de change EUR/USD du jour** — Sentry, Google Play et Apple sont facturés en dollars.
   La conversion « 26 $ ≈ 24 € » utilisée ici est un ordre de grandeur.
5. ~~Recherche « ARPENDO » sur les stores, disponibilité des domaines.~~ **Faites le 30 août
   2026** : aucune application de ce nom sur Play Store ni App Store, et `arpendo.com` comme
   `arpendo.fr` sont **réservés chez Scaleway** — seul poste de ce chiffrage effectivement engagé
   (cadrage §18.10).
6. **Revérifier les tarifs avant tout engagement pluriannuel.** Scaleway a augmenté ses prix au
   1er juin 2026, OVHcloud au 1er avril, Hetzner au 15 juin. Toute liste de prix tierce est
   périmée par construction — c'est ce qui a produit les chiffres erronés de la première version
   de §13.7.

---

## Sources

- [Mapbox — Pricing](https://www.mapbox.com/pricing) (section *Maps SDKs for Mobile*)
- [Mapbox — Maps SDK for Android, Pricing guide](https://docs.mapbox.com/android/maps/guides/pricing/)
- [Scaleway — Tarifs Managed Databases](https://www.scaleway.com/fr/tarifs/managed-databases/)
- [Scaleway — Tarifs Virtual Instances](https://www.scaleway.com/fr/tarifs/virtual-instances/)
- [Scaleway — Tarifs Network](https://www.scaleway.com/fr/tarifs/network/) (Edge Services, WAF, Load Balancer, DNS, IPv4)
- [Sentry — Pricing](https://sentry.io/pricing/)
- [Silicon.fr — Scaleway augmente ses prix](https://www.silicon.fr/cloud-1370/scaleway-hausse-prix-227020) (détail des hausses du 1er juin 2026)
