"""Limitation du débit : une table de dimensions, un compteur par clé, un refus au-delà."""

from collections.abc import Callable
from typing import NamedTuple

from fastapi import Request, status
from redis import exceptions as valkey_errors
from redis.asyncio import Redis
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from arpendo_api.core.settings import Settings

KEY_PREFIX = "ratelimit"
"""Espace de noms des compteurs dans Valkey : ``ratelimit:<dimension>:<clé>``.

Séparé du reste pour qu'un ``SCAN`` les énumère sans rien toucher d'autre. Les tests épinglent ce
format en clair plutôt que de l'importer : le recomposer depuis cette constante les rendrait
aveugles au jour où elle change.
"""


class Dimension(NamedTuple):
    """Un axe de limitation : de qui on compte les requêtes, combien, et sur quelle durée.

    Les deux bornes sont des **fonctions des réglages** plutôt que des entiers : la table est
    construite à l'import, les réglages n'existent qu'à la construction de l'application, et
    recopier une valeur au démarrage ferait diverger la table de la configuration réelle.

    Attributs :
        key: ce qui identifie l'appelant sur cet axe, tiré de la requête. ``None`` signifie que
            l'axe ne s'applique pas à cette requête — elle passe alors sans être comptée, ce qui
            est le cas d'un axe « compte » sur une requête anonyme.
        quota: le nombre de requêtes autorisées par fenêtre.
        window: la durée de la fenêtre, en secondes.
    """

    key: Callable[[Request], str | None]
    quota: Callable[[Settings], int]
    window: Callable[[Settings], int]


def _client_ip(request: Request) -> str | None:
    """L'adresse du pair telle que le serveur la voit — jamais un en-tête lu ici.

    Quand un proxy de confiance est déclaré (``FORWARDED_ALLOW_IPS``), c'est le
    ``ProxyHeadersMiddleware`` d'uvicorn qui a déjà remplacé cette adresse par celle que porte
    ``X-Forwarded-For``. Il est actif par défaut, et lui seul décide à qui l'on croit : analyser
    l'en-tête ici dupliquerait cette décision, avec le risque qu'un jour les deux divergent.

    Rend ``None`` quand le serveur n'expose pas de pair, ce qu'un transport de test ou une socket
    Unix peuvent faire : la requête n'est alors comptée sur aucune adresse.
    """
    return request.client.host if request.client else None


DIMENSIONS: dict[str, Dimension] = {
    "ip": Dimension(
        key=_client_ip,
        quota=lambda settings: settings.rate_limit_ip_requests,
        window=lambda settings: settings.rate_limit_ip_window_seconds,
    ),
}
"""Les axes sur lesquels une requête est comptée, sous le nom qui entre dans la clé Valkey.

**Ajouter un axe, c'est ajouter une entrée ici** — le middleware ne les connaît pas et ne change
pas. La dimension « compte », plus serrée, arrivera avec le premier endpoint authentifié ; une
limite par route s'écrirait de même, par une fonction de clé qui rend ``None`` ailleurs.
"""


async def _retry_after(valkey: Redis, key: str, quota: int, window: int) -> int | None:
    """Compte une requête et rend le délai à attendre si le quota est dépassé, ``None`` sinon.

    Fenêtre **fixe**, en un seul aller-retour : ``INCR`` crée le compteur ou l'incrémente,
    ``EXPIRE NX`` ne pose la durée de vie que sur le premier de la fenêtre — sans ``NX``, chaque
    requête repousserait l'échéance et la fenêtre ne se fermerait jamais — et ``TTL`` rend ce
    qu'il en reste, qui est exactement le délai à annoncer. Une fenêtre glissante serait plus
    juste aux bords ; l'anti-abus n'a pas besoin de cette justesse.

    Le pipeline est **transactionnel**, comme redis-py le fait par défaut : les trois commandes
    sont enveloppées dans un ``MULTI``/``EXEC`` et s'appliquent toutes ou aucune. Sans cela, une
    connexion qui meurt entre l'``INCR`` et l'``EXPIRE`` laisserait un compteur **sans échéance**
    — donc une adresse bloquée pour toujours, puisque plus rien ne remettrait le compteur à zéro.
    Le coût est de deux commandes sur le même aller-retour ; le prix de s'en passer est une panne
    silencieuse et définitive pour l'appelant qu'elle frappe.

    **Échoue ouvert** : Valkey injoignable rend ``None``, donc la requête passe sans être comptée
    (cadrage §13.8 — la perte de Valkey est indolore par conception, et des compteurs remis à
    zéro sont sans conséquence). Les deux exceptions nommées sont sœurs : ``TimeoutError``
    n'hérite pas de ``ConnectionError``, il faut donc citer les deux.

    L'ensemble attrapé est plus large qu'il n'en a l'air : tout ce qui hérite de
    ``ConnectionError`` y entre, dont ``AuthenticationError``. Un mot de passe Valkey erroné
    désarme donc la limitation au lieu de faire échouer l'api — sans trace dans les journaux
    jusqu'à #42, mais ``/health`` le signale en 503.
    C'est le choix assumé : rejeter chaque requête sur une erreur de configuration ferait une
    panne totale là où l'on a un service dégradé et visible. Attraper ``Exception``, en revanche,
    transformerait un bug de ce module en trou silencieux dans la limitation.

    Args:
        valkey: le client de l'application.
        key: la clé du compteur, préfixe et dimension compris.
        quota: le nombre de requêtes autorisées dans la fenêtre.
        window: la durée de la fenêtre, en secondes.

    Returns:
        Les secondes à attendre — au moins 1 — si la requête dépasse le quota, ``None`` si elle
        passe. ``max(ttl, 1)`` est une défense en profondeur, sans chemin connu pour y mener : un
        ``TTL`` de ``-1`` supposerait une clé sans expiration, or l'atomicité interdit à ce module
        d'en créer une et ``EXPIRE NX`` réparerait celle qu'un autre écrivain aurait posée, dans
        ce même pipeline. Le garde coûte un appel et évite un ``Retry-After`` invalide.
    """
    try:
        async with valkey.pipeline() as batch:
            batch.incr(key)
            batch.expire(key, window, nx=True)
            batch.ttl(key)
            count, _, ttl = await batch.execute()
    except (valkey_errors.ConnectionError, valkey_errors.TimeoutError):
        return None
    return None if int(count) <= quota else max(int(ttl), 1)


async def _first_exceeded(request: Request) -> int | None:
    """Compte la requête sur chaque axe et rend le délai du **premier** dépassé.

    Le parcours s'arrête au premier refus : les axes suivants ne sont pas comptés, puisque la
    requête ne sera pas servie de toute façon. Un axe dont la clé est ``None`` ne s'applique pas
    à cette requête et la laisse passer sans compteur.

    Args:
        request: la requête en cours, d'où chaque axe tire sa clé, et dont l'application porte
            le client Valkey et les réglages.

    Returns:
        Les secondes à attendre si un axe est dépassé, ``None`` si la requête passe sur tous.
    """
    valkey: Redis = request.app.state.valkey
    settings: Settings = request.app.state.settings

    for name, dimension in DIMENSIONS.items():
        key = dimension.key(request)
        if key is None:
            continue
        delay = await _retry_after(
            valkey,
            f"{KEY_PREFIX}:{name}:{key}",
            dimension.quota(settings),
            dimension.window(settings),
        )
        if delay is not None:
            return delay
    return None


def _too_many_requests(delay: int) -> JSONResponse:
    """La réponse **429**, annonçant en clair le délai qu'elle porte aussi en en-tête.

    Même forme de corps que les erreurs de FastAPI — ``{"detail": …}`` — pour qu'un client n'ait
    pas deux formats d'erreur à connaître selon qui le refuse.
    """
    return JSONResponse(
        {"detail": f"Trop de requêtes. Réessayez dans {delay} secondes."},
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers={"Retry-After": str(delay)},
    )


class RateLimitMiddleware:
    """Compte chaque requête sur tous les axes de ``DIMENSIONS``, et refuse au premier dépassé.

    Middleware ASGI **pur**, et non un ``BaseHTTPMiddleware`` : ce dernier tamponne la réponse
    entière avant de la transmettre, ce qui retiendrait indéfiniment le flux SSE dont l'écran Jeu
    se sert. Il ne détient aucun état : le client Valkey et les réglages sont ceux de
    l'application traversée, donc deux applications de test ne partagent jamais un compteur.

    La classe ne porte que la plomberie ASGI — filtrer, demander, transmettre ou refuser. La
    politique est dans ``_first_exceeded``, la réponse dans ``_too_many_requests`` : trois raisons
    de changer, trois endroits.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Laisse passer tout ce qui n'est pas une requête HTTP, compte le reste.

        Le cycle de vie (``lifespan``) traverse la pile de middlewares comme une requête : sans
        cette sortie, il chercherait un client et des réglages sur un scope qui n'en a pas.
        """
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        delay = await _first_exceeded(Request(scope))
        if delay is not None:
            return await _too_many_requests(delay)(scope, receive, send)

        return await self.app(scope, receive, send)
