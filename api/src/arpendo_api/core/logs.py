"""Les journaux du paquet : un objet JSON par ligne, sur la sortie standard, et rien d'autre.

Un seul rendu pour **tous** les loggers du processus — le nôtre, celui d'uvicorn, celui d'Alembic,
ceux des bibliothèques. Docker collecte la sortie standard ; il n'y a donc ni fichier, ni rotation,
ni second flux à déclarer quelque part.
"""

import logging
import sys

import structlog
from structlog.typing import Processor

UVICORN_LOGGERS = ("uvicorn", "uvicorn.error", "uvicorn.access")
"""Les loggers qu'uvicorn configure **avant** d'appeler la fabrique d'application.

Il leur pose ses propres handlers de texte : les laisser en place ferait deux formats sur la même
sortie. On les désarme et on les fait propager jusqu'au handler racine, ce qui évite d'avoir à
passer un ``--log-config`` — une troisième déclaration, qu'il faudrait tenir à jour dans le
Dockerfile, dans le compose et sur le poste.
"""

SHARED_PROCESSORS: tuple[Processor, ...] = (
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    structlog.processors.format_exc_info,
)
"""Ce qui compose une ligne, avant son rendu — et pour les deux origines à la fois.

La même liste sert de chaîne structlog et de ``foreign_pre_chain`` du formateur : c'est ce qui
donne les **mêmes clés** à une ligne venue d'un ``logging.Logger`` et à une ligne structlog. Deux
listes divergeraient au premier ajout, et la divergence ne se verrait que dans l'agrégateur.

``merge_contextvars`` en tête : c'est lui qui verse dans la ligne le contexte lié à la requête en
cours — l'identifiant de requête, et demain la partie ou le compte. Un contexte de plus s'ajoute
par un ``bind_contextvars`` dans le domaine qui le connaît, sans toucher à cette liste.
"""


class JsonHandler(logging.StreamHandler):  # type: ignore[type-arg]
    """Le handler que ce module pose — reconnaissable, et c'est là son unique raison d'être.

    Un ``StreamHandler`` nu obligerait à reconnaître le nôtre à son *formateur*, or un
    ``ProcessorFormatter`` n'a rien qui nous appartienne : le SDK Sentry, un agrégateur ou un
    tiers quelconque peut en poser un. ``configure_logging`` se croirait alors déjà configurée et
    rendrait la main sans rien faire — sans ``JSONRenderer``, sans reprendre les loggers d'uvicorn,
    sans poser le niveau : exactement les deux formats sur la même sortie que ce module existe pour
    empêcher.

    C'est aussi ce qui permet aux tests de désinstaller *notre* handler sans toucher aux leurs,
    sans réécrire le prédicat d'idempotence de leur côté.
    """


def _already_configured(root: logging.Logger) -> bool:
    """Dit si le handler de ce module est déjà posé sur la racine.

    L'état vit dans l'arbre de logging, pas dans un drapeau de module : c'est le seul endroit où
    il reste vrai. Un drapeau survivrait au retrait du handler — par un test, par un tiers — et la
    configuration ne se reposerait jamais.
    """
    return any(isinstance(handler, JsonHandler) for handler in root.handlers)


def configure_logging() -> None:
    """Installe le rendu JSON sur la racine, une fois, sans déloger personne.

    Appelée par les **trois** points d'entrée du paquet — la fabrique d'application, le worker et
    l'environnement des migrations, sans quoi ``alembic upgrade`` resterait muet. Elle est donc
    **idempotente** : le second appel ne fait rien, plutôt que de doubler chaque ligne.

    Elle **ajoute** son handler et n'en retire aucun. Mesuré : un ``basicConfig(force=True)`` vide
    le handler de capture de pytest, et la suite perd ses assertions sur les journaux. Le handler
    d'un tiers est là pour une raison que cette fonction ne connaît pas. Elle pose en revanche le
    **niveau** de la racine, qu'elle écrase donc : sans cela, le défaut ``WARNING`` de la stdlib
    retiendrait les lignes ``info`` que tout ce module existe pour produire.

    Les loggers d'uvicorn font exception et sont désarmés : lui les configure avant d'appeler la
    fabrique, donc ne pas le faire laisserait deux formats sur la même sortie.

    Limite connue : la garde n'observe que le **handler**, pas la configuration structlog. Les deux
    sont posées ensemble et rien en production ne défait l'une sans l'autre ; un test qui appelle
    ``structlog.reset_defaults()`` sans retirer le handler obtiendrait, lui, une moitié de
    configuration — d'où la fixture qui fait les deux.
    """
    root = logging.getLogger()
    if _already_configured(root):
        return

    structlog.configure(
        processors=[*SHARED_PROCESSORS, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
    )

    handler = JsonHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=SHARED_PROCESSORS,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ],
        )
    )
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    for name in UVICORN_LOGGERS:
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
