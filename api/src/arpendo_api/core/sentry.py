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

PROJECT_KEYS = ["latitude", "longitude", "lat", "lon", "email"]
"""Les clés que **ce projet** ajoute au denylist du SDK : la position, et l'adresse e-mail.

Nommées par leur provenance et non par leur nature — « les clés de position » exclurait ``email``,
qui est là pour la même raison sans être une position.

``token``, ``authorization``, ``password``, ``cookie`` et 29 autres y sont **déjà** : les répéter
ici donnerait à croire qu'ils n'y seraient pas sans nous.
"""

DENYLIST = [*DEFAULT_DENYLIST, *PROJECT_KEYS]
"""Le denylist complet passé à ``EventScrubber``.

Il **remplace** celui du SDK et ne s'y ajoute pas — lu dans ``sentry_sdk/scrubber.py`` :
``self.denylist = DEFAULT_DENYLIST.copy() if denylist is None else denylist``. N'y poser que les
clés du projet retirerait donc en silence les **33** du SDK, en croyant en ajouter cinq.

Les quatre clés d'adresse IP (``x_forwarded_for``, ``x_real_ip``, ``ip_address``, ``remote_addr``)
ne sont pas concernées : ``EventScrubber`` les ajoute **toujours** ici, quel que soit le denylist
qu'on lui passe — mesuré. Elles dépendent du paramètre ``send_default_pii`` de *son constructeur*,
qu'on ne lui passe pas et dont le défaut est faux ; ce n'est pas l'option homonyme d'``init``.
"""

PATTERNS = (
    re.compile(r"-?\d{1,3}\.\d{4,}[^\d]{1,20}-?\d{1,3}\.\d{4,}"),
    re.compile(r"\bBearer\s+[\w\-._~+/]+=*", re.IGNORECASE),
    re.compile(r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
)
"""Les motifs retirés des **chaînes**, quel que soit l'endroit de l'événement où elles logent.

La coordonnée se reconnaît à la **paire**, jamais à un nombre isolé : un horodatage ISO
(``…:35.751365Z``) porte exactement la même forme décimale, et un motif à un seul nombre les
emporterait tous — on assainirait alors la seule chose qui permet de dater une erreur. Le
séparateur, lui, est délibérément large : la virgule seule laissait passer ``lat=…&lon=…``, un WKT
``POINT(… …)``, un JSON sérialisé et un saut de ligne, tous mesurés. Le **tiret** en fait partie :
l'exclure pour préserver le signe d'une longitude négative ne protégeait de rien — c'est le passage
entier qui est remplacé, signe compris — et laissait passer ``hote-48.858370-2.294481``. Le faux
positif assumé est l'intervalle à quatre décimales (``12.345678-98.765432``), assaini pour rien,
comme la paire de durées jointe par une virgule l'est déjà.

Une position voyage aussi sous forme de **nombres**, et le motif ne peut rien pour elle : c'est
``_has_coordinate_pair`` qui la reconnaît, par la même règle de la paire. Les deux natures sont
épinglées ensemble par ``FORMES_DE_POSITION`` dans les tests.
"""

REDACTED = "[retiré]"
"""Ce qui remplace un motif. Explicite : une valeur simplement absente se lit comme un bug."""


def _scrub_text(text: str) -> str:
    """Retire de ce texte chaque motif sensible."""
    for pattern in PATTERNS:
        text = pattern.sub(REDACTED, text)
    return text


DEGREE_LIMIT = 180.0
"""La plus grande valeur absolue qu'un degré prenne — au-delà, ce n'est pas une longitude."""

DEGREE_PRECISION = 4
"""Décimales minimales pour qu'un nombre soit tenu pour une coordonnée.

Quatre décimales valent environ 11 m. En dessous, la valeur ne localise plus personne, et le seuil
évite d'emporter les nombres ronds que le code produit partout — un `1.0`, un `0.25`.
"""


def _looks_like_degree(value: Any) -> bool:
    """Dit si ce **nombre** a la forme d'une composante de coordonnée.

    Une forme, pas une certitude : `12.345678` peut être une durée. C'est pourquoi cette fonction
    ne décide rien seule — voir ``_has_coordinate_pair``.
    """
    if not isinstance(value, float):
        return False
    return abs(value) <= DEGREE_LIMIT and len(repr(value).partition(".")[2]) >= DEGREE_PRECISION


def _has_coordinate_pair(values: Any) -> bool:
    """Dit si ces valeurs voisines contiennent **au moins deux** composantes de coordonnée.

    C'est la même règle que pour les chaînes, transposée aux nombres : **une position se reconnaît
    à la paire**. Un flottant isolé est indécidable — durée, prix, moyenne — et le redresser
    emporterait la moitié des nombres d'un événement. Deux flottants de forme géographique dans le
    **même conteneur** — la liste des paramètres d'un log, le contexte d'une frame, un `extra` —
    sont une position bien plus souvent qu'une coïncidence.

    Le faux positif assumé est un conteneur de deux mesures fines (`{"p50": 12.345678, "p99":
    98.765432}`), qui sera assaini pour rien. L'asymétrie est voulue : perdre un centile se voit et
    se répare, laisser fuir une position ne se voit pas et ne se répare pas (cadrage §12.3).
    """
    return sum(1 for valeur in values if _looks_like_degree(valeur)) >= 2


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
        paire = _has_coordinate_pair(value.values())
        return {clef: _scrub_child(inner, paire) for clef, inner in value.items()}
    if isinstance(value, list):
        paire = _has_coordinate_pair(value)
        return [_scrub_child(inner, paire) for inner in value]
    return value


def _scrub_child(value: Any, in_coordinate_pair: bool) -> Any:
    """Assainit un élément, en tenant compte de ce que ses **voisins** révèlent.

    C'est là que la règle de la paire s'applique : un nombre n'est retiré que si le conteneur qui
    le porte en contient un second de même forme.
    """
    if in_coordinate_pair and _looks_like_degree(value):
        return REDACTED
    return _scrub_value(value)


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
    après ``configure_logging``. **Cet ordre est une convention, pas une contrainte** : mesuré, le
    SDK n'installe aucun handler sur la racine, il remplace ``logging.Logger.callHandlers``, ce qui
    le rend insensible à l'ordre. On va donc simplement du moins effectif au plus effectif :
    les réglages, puis les journaux, puis le seul des trois qui ouvre une porte vers le réseau.
    L'environnement des migrations ne l'appelle pas : un processus court, sans requête, dont
    l'échec se lit dans le code de retour.

    ``include_local_variables=False`` ferme **une** voie : le SDK joint par défaut les variables
    locales de chaque frame, et une ``position = (48.858370, 2.294481)`` en sortait telle quelle.
    Le prix est réel — les traces perdent leurs variables locales, partout et pas seulement dans
    Territoire — et il est assumé : §12.3 pèse plus lourd qu'un confort de débogage, et type,
    message, pile, fichier et ligne restent.

    **Ce n'est pas la seule voie, et il ne faut pas le croire.** Les autres sont fermées par
    ``scrub``, dont la règle de la paire vaut pour les chaînes *et* pour les nombres — le détail
    est dans ``PATTERNS`` et ``_has_coordinate_pair``, et la population complète des formes connues
    est épinglée par ``FORMES_DE_POSITION`` dans les tests. Reste ouvert, et documenté : le
    **contexte source** des frames, que le SDK joint aussi (``include_source_context``) — il porte
    du code, donc une donnée d'utilisateur ne peut pas s'y trouver, mais une valeur écrite en dur
    dans le code, si.

    Args:
        settings: les réglages validés. Seuls ``sentry_dsn`` et ``sentry_sample_rate`` sont lus.
    """
    if settings.sentry_dsn is None:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn.get_secret_value(),
        sample_rate=settings.sentry_sample_rate,
        send_default_pii=False,
        include_local_variables=False,
        before_send=scrub,
        event_scrubber=EventScrubber(denylist=DENYLIST, recursive=True),
    )
