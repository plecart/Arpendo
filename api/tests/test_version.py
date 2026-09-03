import pytest
from httpx import AsyncClient

SEUILS_PUBLIES = {"client_build_min": 12, "client_build_recommended": 34}
"""Deux valeurs **distinctes** et étrangères au `.env` du poste comme au job de CI.

Un couple identique laisserait passer une route qui rendrait deux fois le même champ ; des valeurs
qui coïncideraient avec celles de l'environnement laisseraient passer une route qui ne lirait pas
les réglages qu'on lui a donnés.

Posées par paramétrisation indirecte de la fixture `settings` — la chaîne `settings` → `app` →
`client` de `conftest` suit sans qu'on la reconstruise. La route ne touche ni la base ni le cache,
mais le cycle de vie reste nécessaire : le limiteur de débit traverse **toutes** les routes et va
chercher son client Valkey dans `app.state`.
"""


pytestmark = pytest.mark.parametrize("settings", [SEUILS_PUBLIES], indirect=True)
"""Tous les tests de ce module parlent à une api dont les seuils sont ceux de [SEUILS_PUBLIES]."""


async def test_version_publie_les_deux_seuils_sans_authentification(
    client: AsyncClient,
) -> None:
    """La première requête de la séquence de démarrage (spec UX §2.1), et la seule qui précède la
    session.

    Publique **par construction**, pas par oubli : un client obsolète doit apprendre qu'il l'est
    sans jamais taper une api qu'il ne comprend plus. Le client de test n'envoie aucun en-tête
    d'authentification, et la route répond quand même — ce test rougirait le jour où une
    dépendance d'authentification serait posée globalement plutôt que sur les routeurs de domaine.

    Elle vit à la racine, comme `/health` : un client qui doit apprendre qu'il est trop vieux pour
    parler à `/v1` ne peut pas être obligé de connaître `/v1` pour le demander. Un préfixe la
    ferait répondre 404 ici.
    """
    reponse = await client.get("/version")

    assert reponse.status_code == 200
    assert reponse.json() == {"min_build": 12, "recommended_build": 34}


async def test_version_ne_lit_pas_l_en_tete_de_version_du_client(
    client: AsyncClient,
) -> None:
    """Le serveur publie deux seuils ; il ne rend aucun verdict.

    Calculer « cette version est-elle acceptée ? » depuis `X-Client-Version` couplerait la route à
    l'en-tête et priverait l'app de la connaissance de sa cible — elle ne saurait plus quoi
    afficher, ni dans l'écran bloquant, ni dans le bandeau. La réponse doit donc être **la même**
    quelle que soit la version annoncée, y compris absente.

    C'est l'assertion qui rougit si quelqu'un rapatrie la comparaison côté serveur — une décision
    explicitement écartée à l'interrogatoire, et que seule la lecture garantirait autrement.
    """
    sans_en_tete = await client.get("/version")
    obsolete = await client.get("/version", headers={"X-Client-Version": "0.0.1+1"})
    recente = await client.get("/version", headers={"X-Client-Version": "9.9.9+999"})

    assert sans_en_tete.json() == obsolete.json() == recente.json()
