"""Sonde de santé de l'api : une route, l'état de chaque dépendance, un verdict."""

import asyncio
from collections.abc import Awaitable, Callable
from functools import partial

from fastapi import APIRouter, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from arpendo_api.core.valkey import Valkey
from arpendo_api.db.engine import Engine

router = APIRouter()

Sonde = Callable[[], Awaitable[object]]
"""Un aller-retour vers une dépendance.

Ce qu'elle rend est ignoré : seul compte qu'elle aboutisse.
"""

DELAI_DE_SONDE = 1.0
"""Secondes accordées à chaque dépendance.

Une sonde de santé qui pend est pire qu'une sonde qui échoue : le reverse proxy et le moniteur
d'uptime attendraient, et un `docker compose up` resterait bloqué sur un `healthcheck` sans
réponse. Une seconde est très au-dessus de ce que coûtent un `SELECT 1` et un `PING` sur le
réseau local ; la dépasser signifie que quelque chose ne va pas, pas que la machine est lente.
"""

JOIGNABLE = "ok"
INJOIGNABLE = "unreachable"
SAIN = "ok"
DEGRADE = "degraded"


async def _interroger_postgresql(engine: AsyncEngine) -> None:
    """Ouvre une connexion et l'utilise : c'est le seul moyen de savoir qu'elle sert encore.

    Le moteur ne se connecte qu'au premier usage et son pool peut contenir des connexions
    coupées depuis. Vérifier l'objet moteur ne prouverait donc rien.
    """
    async with engine.connect() as connexion:
        await connexion.execute(text("SELECT 1"))


async def _etat(sonde: Sonde) -> str:
    """Rend ``ok`` si la sonde aboutit dans le délai, ``unreachable`` sinon.

    Attrape ``Exception`` volontairement : du point de vue de l'appelant, une dépendance qui
    refuse la connexion, qui répond une erreur de protocole ou qui expire sont le même fait —
    elle n'est pas exploitable. Laisser fuir l'une d'elles transformerait la sonde de santé en
    500, c'est-à-dire en panne supplémentaire au moment précis où on l'interroge pour
    diagnostiquer.
    """
    try:
        async with asyncio.timeout(DELAI_DE_SONDE):
            await sonde()
    except Exception:
        return INJOIGNABLE
    return JOIGNABLE


@router.get("/health")
async def health(engine: Engine, valkey: Valkey, response: Response) -> dict[str, str]:
    """Rapporte l'état de l'api et de chacune de ses dépendances.

    Répond **200** ``{"status": "ok", …}`` si toutes répondent, **503**
    ``{"status": "degraded", …}`` dès qu'une manque, en la nommant : un moniteur d'uptime a
    besoin du verdict, la personne d'astreinte a besoin de savoir laquelle.

    Les sondes partent **en parallèle** — deux dépendances lentes coûtent le délai de la plus
    lente, pas leur somme — et chacune est bornée par ``DELAI_DE_SONDE``.

    Une seule route, pas de ``/ready`` distinct : rien ici ne redémarre un conteneur sur un état
    dégradé, donc distinguer « vivant » de « disponible » n'aurait aucun lecteur.

    Ajouter une dépendance, c'est ajouter un paramètre et une entrée à ``sondes`` ; ni le calcul
    du verdict, ni le code de statut, ni le format de la réponse n'ont à changer.
    """
    sondes: dict[str, Sonde] = {
        "postgres": partial(_interroger_postgresql, engine),
        "valkey": valkey.ping,
    }
    resultats = await asyncio.gather(*(_etat(sonde) for sonde in sondes.values()))
    etats = dict(zip(sondes, resultats, strict=True))

    sain = all(etat == JOIGNABLE for etat in etats.values())
    response.status_code = 200 if sain else 503
    return {"status": SAIN if sain else DEGRADE, **etats}
