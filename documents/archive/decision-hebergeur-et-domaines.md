# Décision — Scaleway confirmé, domaines `.com` et `.fr` chez lui, compte au nom d'un particulier

*Archive non normative. L'état courant est au cadrage §13.7 et au chiffrage §1, §3 et §6 ; ce
fichier conserve le raisonnement, la comparaison et les relevés, pour qu'ils ne soient pas refaits
sans élément nouveau.*

**Date :** 30 août 2026. **Déclencheur :** l'ouverture du compte Scaleway (issue #30). Le porteur
a trouvé les ~26 € HT/mois élevés pour un MVP et a demandé si Scaleway restait le bon choix, et si
les domaines pouvaient être achetés ailleurs — chez OVH par exemple.

## Ce qui était en jeu

Le §13.7 est **clos et de rang 1**, et le §19 interdit de le rouvrir sans élément nouveau. Son
motif n'est pas le prix : c'est que le serveur et la base chez le même fournisseur permettent à
PostgreSQL de vivre sur le **réseau privé, sans IP publique**. Une alternative moins chère qui
casse cette propriété ne répond pas à la question posée.

## Les relevés, à la source, le 30 août 2026

- **`DEV1-S` et `DB-DEV-S` toujours commandables en région Paris**, aux prix de §13.7. C'était le
  risque principal : une gamme retirée aurait été une contradiction de rang 1, pas un choix de
  commande.
- **IPv4 flexible : 0,005 €/h, soit 3,65 €/mois** — et non 2,92 comme l'écrivait §13.7. Seule
  erreur de tarif trouvée.
- Block Storage 5K et snapshot conformes.
- Domaines, HT/an : `.com` **12,34** chez Scaleway contre **13,49** chez OVH ; `.fr` **5,98**
  contre **7,79**. Chez Scaleway, la création est au prix du renouvellement — pas de première
  année cassée suivie d'un renouvellement plus cher.

## Les options examinées

| Option | Verdict |
|---|---|
| **Scaleway pour tout** *(retenu)* | Seule offre du panel à réunir PostgreSQL managé et raccordement au réseau privé sans IP publique à ce niveau de prix |
| **OVH** | Le PostgreSQL managé est conforme au §13.7 — vRack sur toutes les offres — mais le plancher est à ~64 $/mois, plus du double du poste base actuel |
| **Hetzner** | Moins cher sur la machine, mais **aucun PostgreSQL managé natif**. Auto-héberger la base annule le PITR, que §13.7 appelle « le meilleur retour sur temps investi de toute la section 13 » |
| **Domaines chez un registrar tiers** | Techniquement sans surcoût : la ligne « 5,11 €/mois » du chiffrage ne vise que la zone DNS d'un domaine *externe hébergée chez Scaleway*, et un registrar tiers fournit la sienne gratuitement — un enregistrement A vers l'IPv4 suffirait. Écarté sur le **prix au renouvellement**, plus élevé chez OVH pour les deux extensions |

**Conclusion : Scaleway reste le plancher du marché** pour la contrainte « base managée sur réseau
privé sans IP publique ». Aucun élément nouveau ne justifie de rouvrir le §13.7 sur l'hébergeur.

## Le titulaire du compte, et pourquoi ce n'est pas l'auto-entreprise

Première hypothèse : compte professionnel au nom de l'auto-entreprise du porteur, pour récupérer
la TVA. Elle ne tient pas.

- Scaleway SAS est **français**. La TVA française de 20 % est facturée à une entreprise française
  comme à un particulier ; l'**autoliquidation intracommunautaire ne joue pas en domestique**. La
  note du chiffrage §1 qui l'évoquait était fausse.
- La TVA n'est récupérable qu'en **assujettissement au réel**. Une auto-entreprise en **franchise
  en base** — le régime par défaut — ne récupère rien.
- Sans gain fiscal, le compte professionnel n'apporte que des formalités.

**Retenu : compte Scaleway au nom d'un particulier, domaines en nom propre.** Conséquence à ne pas
perdre de vue : **le budget de référence devient le TTC**, soit 32,46 €/mois, et non le HT.

## Suite donnée, le 30 août 2026

- **Les deux domaines sont réservés chez Scaleway** — `arpendo.com` et `arpendo.fr`, aux prix
  relevés ci-dessus. La disponibilité pressentie était bonne. C'est le seul poste engagé.
- **Rien d'autre n'est commandé** : ni serveur, ni disque, ni snapshot, ni IPv4, ni base managée.
  La facturation démarre à la création, et #45 comme #47 ne sont pas triées — payer un socle que
  personne n'utilise n'achèterait rien. Le provisionnement attend **le déploiement**.
- Reste donc à vérifier **au moment de la création**, et pas avant : le raccordement de l'instance
  PostgreSQL au Private Network sans IP publique — l'argument même qui a fait retenir Scaleway.
  Et, dès maintenant : verrou de transfert et 2FA sur le compte registrar (cadrage §13.10, §19),
  ce qui est le sujet de l'issue #36.
