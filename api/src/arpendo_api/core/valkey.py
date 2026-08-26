"""Le client Valkey de l'application."""

from redis.asyncio import Redis

from arpendo_api.core.settings import Settings


def create_valkey(settings: Settings) -> Redis:
    """Ouvre le client Valkey de l'application, avec son pool de connexions.

    Le mot de passe est passé à part plutôt qu'enfoui dans l'URL : il ne se retrouve donc ni dans
    un journal, ni dans une trace d'erreur qui afficherait le DSN. Comme pour le moteur, aucune
    connexion n'est ouverte ici — redis-py la crée au premier ordre.

    Args:
        settings: les réglages validés, dont ``valkey_url`` et ``valkey_password``.

    Returns:
        Le client, à fermer par ``await client.aclose()``.
    """
    return Redis.from_url(settings.valkey_url, password=settings.valkey_password)
