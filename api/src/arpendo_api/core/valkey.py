"""Le client Valkey : comment on l'ouvre, et comment les routes y accèdent."""

from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis

from arpendo_api.core.settings import Settings


def create_valkey(settings: Settings) -> Redis:
    """Ouvre le client Valkey de l'application, avec son pool de connexions.

    Le mot de passe est passé à part plutôt qu'enfoui dans l'URL : afficher ``valkey_url`` reste
    donc sans danger. C'est ici, et nulle part ailleurs, qu'on le déballe de son ``Secret`` — il
    ne prend sa forme lisible que pour être remis à redis-py. Comme pour le moteur, aucune
    connexion n'est ouverte ici : redis-py la crée au premier ordre.

    Args:
        settings: les réglages validés, dont ``valkey_url`` et ``valkey_password``.

    Returns:
        Le client, à fermer par ``await client.aclose()``.
    """
    return Redis.from_url(settings.valkey_url, password=settings.valkey_password.get_secret_value())


def _from_state(request: Request) -> Redis:
    """Rend le client rangé dans ``app.state`` par le cycle de vie de l'application."""
    valkey: Redis = request.app.state.valkey
    return valkey


Valkey = Annotated[Redis, Depends(_from_state)]
"""Le client Valkey, vu par une route : ``async def route(valkey: Valkey)``.

Même raison que pour ``db.engine.Engine`` : une dépendance, pas un singleton de module.
"""
