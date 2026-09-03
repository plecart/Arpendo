"""L'identifiant de requête : ce qui relie une réponse à toutes les lignes qu'elle a produites."""

from uuid import uuid4

import structlog
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

HEADER = "X-Request-ID"
"""L'en-tête sous lequel la réponse annonce son identifiant.

Une seule direction : **sortante**. Il n'est jamais lu sur la requête — le pourquoi est dans
``RequestIdMiddleware``.
"""

CONTEXT_KEY = "request_id"
"""La clé sous laquelle l'identifiant est lié au contexte, donc le nom de la clé dans le journal.

Nommée ici plutôt qu'écrite en clair aux deux endroits qui la lient et la délient : les deux
doivent parler de la même chose, et une divergence laisserait un contexte qui ne se nettoie jamais.
"""


def _announcing(send: Send, request_id: str) -> Send:
    """Enveloppe ``send`` pour poser l'en-tête sur la réponse, et rien d'autre.

    L'en-tête ne peut se poser qu'à l'ouverture de la réponse : après le premier ``http.response
    .body``, les en-têtes sont déjà partis sur le fil. Les messages suivants — corps, fin de flux
    — traversent sans être touchés, ce qui laisse passer une SSE ou un téléchargement sans le
    retenir.

    Args:
        send: le ``send`` de l'application enveloppée.
        request_id: la valeur à annoncer.

    Returns:
        Un ``send`` équivalent, qui enrichit le seul message d'ouverture de réponse.
    """

    async def announcing_send(message: Message) -> None:
        if message["type"] == "http.response.start":
            message.setdefault("headers", [])
            MutableHeaders(scope=message)[HEADER] = request_id
        await send(message)

    return announcing_send


class RequestIdMiddleware:
    """Donne à chaque requête un identifiant neuf, le lie au journal, et l'annonce en réponse.

    **L'identifiant est généré par le serveur, jamais repris d'un en-tête entrant.** Un en-tête est
    une entrée non fiable, et le journal est un lieu de confiance : reprendre la valeur de
    l'appelant lui laisserait choisir la clé sur laquelle ses requêtes sont regroupées — donc se
    confondre avec un autre appelant, ou déposer dans l'agrégateur une chaîne de son choix, où un
    saut de ligne suffit à fabriquer une fausse entrée. Le jour où un identifiant de corrélation
    venu d'un client légitime aura un sens, il aura son propre en-tête et sa propre validation.

    Middleware ASGI **pur**, et non un ``BaseHTTPMiddleware`` — même raison que pour le limiteur de
    débit : ce dernier tamponne la réponse entière avant de la transmettre, ce qui retiendrait le
    flux SSE dont l'écran Jeu se sert. Il ne détient aucun état ; l'identifiant vit dans le
    contexte de la tâche qui sert la requête.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Lie l'identifiant le temps de la requête, et le délie **quoi qu'il arrive**.

        Le ``finally`` n'est pas une précaution de style : le contexte appartient au fil
        d'exécution, pas à la requête. Une requête qui lève laisserait sa clé derrière elle, et la
        ligne suivante — une tâche de fond, une autre requête servie par la même tâche — se verrait
        rattachée à un travail qui ne l'a pas demandée.

        Tout ce qui n'est pas une requête HTTP traverse sans être touché : le cycle de vie
        (``lifespan``) parcourt la pile de middlewares comme une requête, et n'a ni réponse à
        enrichir ni contexte à porter.
        """
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request_id = str(uuid4())
        structlog.contextvars.bind_contextvars(**{CONTEXT_KEY: request_id})
        try:
            await self.app(scope, receive, _announcing(send, request_id))
        finally:
            structlog.contextvars.unbind_contextvars(CONTEXT_KEY)
