"""Le client Valkey : comment on l'ouvre."""

from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.backoff import NoBackoff

from arpendo_api.core.settings import Settings

CONNECT_TIMEOUT = 0.5
"""Secondes accordées à l'établissement d'une connexion Valkey.

Très au-dessus du coût réel — une poignée de millisecondes sur le réseau local d'un compose ou
d'un hôte — et sous le budget de la sonde de santé, pour qu'un serveur muet se constate au lieu
de s'attendre. Le client ignore volontairement ``health.PROBE_TIMEOUT`` : c'est un test qui
confronte les deux constantes et rougit si celle-ci passait au-dessus de l'autre.

Ce délai se paie **une fois par client et par requête**, et le chemin de ``/health`` en traverse
deux : celui du limiteur de débit, puis celui de la sonde. Le relever allonge donc d'autant chaque
requête pendant une panne de Valkey.
"""


def create_valkey(settings: Settings) -> Redis:
    """Ouvre le client Valkey de l'application, avec son pool de connexions.

    Le mot de passe est passé à part plutôt qu'enfoui dans l'URL : afficher ``valkey_url`` reste
    donc sans danger. C'est ici, et nulle part ailleurs, qu'on le déballe de son ``Secret`` — il
    ne prend sa forme lisible que pour être remis à redis-py. Comme pour le moteur, aucune
    connexion n'est ouverte ici : redis-py la crée au premier ordre.

    Le client **échoue vite** : la connexion est bornée par ``CONNECT_TIMEOUT`` et n'est jamais
    réessayée. redis-py réessaierait trois fois avec un délai croissant, ce qui met deux secondes
    à constater un serveur absent — plus que le budget de la sonde de santé, qui conclurait alors
    par expiration au lieu de par refus. Rien ici ne gagne à insister : le cadrage §13.8 pose que
    la perte de Valkey est indolore par conception, donc mieux vaut l'apprendre tout de suite que
    faire attendre l'appelant.

    Args:
        settings: les réglages validés, dont ``valkey_url`` et ``valkey_password``.

    Returns:
        Le client, à fermer par ``await client.aclose()``.
    """
    return Redis.from_url(
        settings.valkey_url,
        password=settings.valkey_password.get_secret_value(),
        socket_connect_timeout=CONNECT_TIMEOUT,
        retry=Retry(NoBackoff(), retries=0),
    )
