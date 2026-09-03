"""Sentry côté serveur : l'initialisation, et ce qu'on retire d'un événement avant de l'envoyer.

Deux filets superposés, parce qu'aucun ne suffit seul (cadrage §13.10 — « le scrubbing PII doit
être configuré explicitement, sinon on reconstruit exactement l'historique de localisation que
§12.3 interdit ») :

- ``EventScrubber``, fourni par le SDK, travaille **par clé** — il vide ``password``, ``token``,
  ``authorization``, et les clés de position qu'on lui ajoute. Il ne regarde ni le message, ni la
  valeur d'une exception : mesuré, il les laisse passer entiers.
- ``scrub``, en ``before_send``, travaille **par motif** sur tout le corps de l'événement. C'est
  lui qui attrape une coordonnée noyée dans un message, ou le secret qu'une ``ValidationError``
  de pydantic recopie en clair dans son texte.
"""

import re
from typing import Any

import sentry_sdk
from sentry_sdk.scrubber import DEFAULT_DENYLIST, EventScrubber

from arpendo_api.core.settings import Settings

POSITION_KEYS = ["latitude", "longitude", "lat", "lon", "email"]
"""Les clés que ce projet ajoute au denylist du SDK — position et adresse.

``token``, ``authorization``, ``password``, ``cookie`` et une trentaine d'autres y sont **déjà** :
les répéter ici donnerait à croire qu'ils n'y seraient pas sans nous.
"""

DENYLIST = [*DEFAULT_DENYLIST, *POSITION_KEYS]
"""Le denylist complet passé à ``EventScrubber``.

Il **remplace** celui du SDK et ne s'y ajoute pas — lu dans ``sentry_sdk/scrubber.py`` :
``self.denylist = DEFAULT_DENYLIST.copy() if denylist is None else denylist``. N'y poser que les
clés du projet retirerait donc en silence les trente-sept du SDK, en croyant en ajouter cinq.
"""

PATTERNS = (
    re.compile(r"-?\d{1,3}\.\d{4,}\s*,\s*-?\d{1,3}\.\d{4,}"),
    re.compile(r"\bBearer\s+[\w\-._~+/]+=*", re.IGNORECASE),
    re.compile(r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
)
"""Les motifs retirés du corps entier de l'événement, quel que soit l'endroit où ils logent.

La coordonnée se reconnaît à la **paire**, jamais à un nombre isolé : un horodatage ISO
(``…:35.751365Z``) porte exactement la même forme décimale, et un motif à un seul nombre les
emporterait tous — on assainirait alors la seule chose qui permet de dater une erreur.
"""

REDACTED = "[retiré]"
"""Ce qui remplace un motif. Explicite : une valeur simplement absente se lit comme un bug."""


def _scrub_text(text: str) -> str:
    """Retire de ce texte chaque motif sensible."""
    for pattern in PATTERNS:
        text = pattern.sub(REDACTED, text)
    return text


def _scrub_value(value: Any) -> Any:
    """Descend dans la structure et n'assainit que les chaînes qu'elle contient.

    Générique par nécessité, pas par goût : le protocole Sentry range le texte à des endroits qui
    changent d'une version à l'autre — ``logentry``, ``exception.values[].value``,
    ``breadcrumbs.values[].data``, ``extra``, ``request``, et ceux qu'une intégration ajoutera. Une
    traversée qui nomme ses emplacements est une liste à tenir à jour, et le jour où elle manque
    un emplacement, personne ne le voit : l'événement part.
    """
    if isinstance(value, str):
        return _scrub_text(value)
    if isinstance(value, dict):
        return {key: _scrub_value(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_scrub_value(inner) for inner in value]
    return value


def scrub(event: Any, hint: Any = None) -> Any:
    """Le ``before_send`` : rend une copie assainie de l'événement, sans jamais toucher l'original.

    **Pure**, et c'est ce qui la rend éprouvable : un test la nourrit d'un dictionnaire écrit à la
    main, sans réseau, sans ``init``, sans projet Sentry. La copie est **structurelle et gratuite**
    — ``_scrub_value`` reconstruit chaque dictionnaire et chaque liste au lieu de les modifier, ce
    qui rend l'original intact sans qu'un ``deepcopy`` soit nécessaire. Mesuré : le retirer ne fait
    rougir aucun test, parce qu'il ne servait à rien.

    Args:
        event: l'événement que le SDK s'apprête à envoyer.
        hint: le contexte que le SDK joint à l'événement (exception d'origine, enregistrement de
            journal). Non lu — la signature l'exige, ``before_send`` étant appelé avec deux
            arguments.

    Returns:
        L'événement assaini. Jamais ``None`` : ce module ne décide pas d'abandonner un événement,
        c'est le rôle de l'échantillonnage.
    """
    return _scrub_value(event)


def configure_sentry(settings: Settings) -> None:
    """Initialise Sentry — ou ne fait **rien du tout**, si aucun DSN n'est configuré.

    « Désactivé » veut dire *aucun appel à* ``sentry_sdk.init``, et non un ``init`` avec un DSN
    vide : ce dernier installe quand même les intégrations, les handlers de journalisation et le
    hook d'exceptions non rattrapées. C'est une différence qu'on ne voit pas sur un poste de
    développement et qui compte partout ailleurs. C'est le validateur d'``OptionalSecret`` qui rend
    cette branche atteignable — sans lui, ``SENTRY_DSN=`` donnerait ``SecretStr('')``, une valeur
    présente et fausse.

    Appelée par les deux hôtes qui servent du trafic — la fabrique d'application et le worker —
    **après** ``configure_logging``, pour que le handler du SDK s'ajoute au nôtre plutôt que de le
    précéder. L'environnement des migrations ne l'appelle pas : un processus court, sans requête,
    dont l'échec se lit dans le code de retour.

    Args:
        settings: les réglages validés. Seuls ``sentry_dsn`` et ``sentry_sample_rate`` sont lus.
    """
    if settings.sentry_dsn is None:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn.get_secret_value(),
        sample_rate=settings.sentry_sample_rate,
        send_default_pii=False,
        before_send=scrub,
        event_scrubber=EventScrubber(denylist=DENYLIST, recursive=True),
    )
