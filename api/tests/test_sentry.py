"""Sentry côté serveur : ce qu'on envoie, ce qu'on retire, et quand on n'envoie rien du tout."""

import json
from collections.abc import Iterator
from typing import Any

import pytest
import sentry_sdk
from conftest import reglages_surcharges
from httpx import AsyncClient
from pydantic import BaseModel, ValidationError
from sentry_sdk.transport import Transport

from arpendo_api import main
from arpendo_api.core import sentry as sentry_module
from arpendo_api.core.request_id import HEADER
from arpendo_api.core.sentry import REDACTED, configure_sentry, scrub
from arpendo_api.core.settings import Settings
from arpendo_api.main import create_app

DSN = "https://cle-de-projet@o0.ingest.sentry.io/1"
"""Un DSN de forme valide. Aucun réseau n'est joint : `init` est toujours doublé dans ces tests."""

COORDONNEES = "48.858370, 2.294481"
"""Une position — le motif que le cadrage §12.3 interdit de laisser reconstituer."""

LATITUDE, LONGITUDE = (float(nombre) for nombre in COORDONNEES.split(","))
"""La même position, **dérivée** plutôt que réécrite en littéral.

Elle sert au test qui capture un vrai événement, et la dérivation n'est pas une coquetterie : le
SDK joint à chaque frame le **code source** qui l'entoure. Un test qui écrirait les chiffres dans
sa propre ligne les verrait revenir dans l'événement par ce chemin-là, et échouerait sur sa propre
source au lieu d'échouer sur une fuite. Corollaire à connaître : une donnée sensible écrite en dur
dans le code part vers Sentry avec le contexte source — c'est du code, pas une donnée d'utilisateur,
mais un secret en dur en sortirait.
"""

JETON = "Bearer eyJhbGciOiJIUzI1NiJ9.charge-utile.signature"
EMAIL = "joueuse@example.com"

SENSIBLES = (COORDONNEES, JETON, EMAIL)
"""Les trois motifs qui ne doivent jamais atteindre Sentry, où qu'ils logent dans l'événement."""

INTACTS = (
    "2026-09-03T08:41:35.751365Z",
    "8a2a1072b59ffff",
    "3f2c9a4e-1b7d-4c8e-9a0f-5d6e7f8a9b0c",
    "1.0.0+42",
    "arpendo_api.core.bus",
    "p50=12.345678ms p99=98.765432ms",
    "12.50-13.75",
)
"""Ce qui **ressemble** à une donnée sensible sans en être une.

Un horodatage ISO porte une décimale à six chiffres, un index H3 une longue chaîne hexadécimale,
un UUID des tirets, un numéro de build un point ; deux centiles fins sont séparés par leur unité
et le nom du suivant, une plage à deux décimales par un tiret. Un assainissement qui les emporte
rend les journaux Sentry inutiles au diagnostic — et personne ne s'en aperçoit avant d'en avoir
besoin.
"""


def _init_espionne(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Substitue `sentry_sdk.init` par un espion et rend la liste de ses appels.

    Doublure d'une **frontière du système** : `init` ouvre une porte vers le réseau et installe des
    effets globaux de processus. Ce qu'on éprouve ici est ce qu'on lui demande, pas ce qu'il en
    fait — le test qui capture un vrai événement, lui, l'appelle pour de bon.
    """
    appels: list[dict[str, Any]] = []
    monkeypatch.setattr(sentry_sdk, "init", lambda **kw: appels.append(kw))
    return appels


def _valeurs(objet: Any) -> list[str]:
    """Toutes les chaînes d'une structure imbriquée, à plat — sans supposer où elles logent."""
    if isinstance(objet, str):
        return [objet]
    if isinstance(objet, dict):
        return [texte for valeur in objet.values() for texte in _valeurs(valeur)]
    if isinstance(objet, list):
        return [texte for element in objet for texte in _valeurs(element)]
    return []


def _evenement_complet() -> dict[str, Any]:
    """Un événement Sentry portant les trois motifs dans **chacun** des endroits qui les portent.

    Écrit à la main plutôt que capturé du SDK : `scrub` est une fonction pure, l'éprouver ne doit
    demander ni réseau, ni `init`, ni projet Sentry. La forme suit celle du protocole — `logentry`
    pour le message, `exception.values[].value` pour les exceptions, `breadcrumbs.values[].data`,
    `extra`, `request`.
    """
    return {
        "logentry": {"message": f"échec à {COORDONNEES}", "formatted": f"échec à {COORDONNEES}"},
        "exception": {
            "values": [
                {"type": "ValueError", "value": f"jeton refusé : {JETON}"},
                {"type": "LookupError", "value": f"compte inconnu : {EMAIL}"},
            ]
        },
        "breadcrumbs": {"values": [{"data": {"trace": f"position {COORDONNEES}"}}]},
        "extra": {
            "contexte": f"{EMAIL} depuis {COORDONNEES}",
            "latences": "p50=12.345678ms p99=98.765432ms",
            "plage": "12.50-13.75",
        },
        "request": {"headers": {"Authorization": JETON}, "query_string": f"pos={COORDONNEES}"},
        "release": "1.0.0+42",
        "timestamp": "2026-09-03T08:41:35.751365Z",
        "tags": {
            "request_id": "8a2a1072b59ffff",
            "trace_id": "3f2c9a4e-1b7d-4c8e-9a0f-5d6e7f8a9b0c",
            "logger": "arpendo_api.core.bus",
        },
    }


def test_scrub_retire_les_trois_motifs_partout_ou_ils_logent() -> None:
    """Un seul endroit oublié suffit : Sentry indexe l'événement entier, pas son message.

    Le test ne vérifie pas endroit par endroit — il aplatit l'événement et exige qu'aucune des
    chaînes sensibles n'y subsiste. Un `scrub` qui traiterait cinq emplacements sur six passerait
    une assertion par emplacement ; il ne passe pas celle-ci.
    """
    assaini = scrub(_evenement_complet())

    restants = [motif for motif in SENSIBLES if any(motif in v for v in _valeurs(assaini))]
    assert restants == []


def test_scrub_laisse_intact_ce_qui_ressemble_a_une_donnee_sensible() -> None:
    assaini = scrub(_evenement_complet())

    valeurs = _valeurs(assaini)
    absents = [temoin for temoin in INTACTS if not any(temoin in v for v in valeurs)]
    assert absents == []


def test_scrub_retire_la_valeur_brute_qu_une_erreur_de_validation_recopie() -> None:
    """Le cas qui a motivé `before_send` plutôt que le seul `EventScrubber`.

    `pydantic` recopie l'entrée **brute** dans le `input_value` de sa `ValidationError`, et le
    texte de l'exception la porte donc en clair. `EventScrubber` travaille par clés et ne regarde
    jamais la valeur d'une exception.

    **Le modèle est un corps de requête, et non `Settings` — c'est délibéré.** `Settings` porte
    depuis #91 un `hide_input_in_errors=True` qui retire l'entrée de ses messages : ce chemin-là
    est fermé à la source, et l'éprouver ici ne prouverait plus rien (mesuré : le test rougissait
    à la fusion, faute de valeur à assainir). Le chemin qui reste ouvert est celui de tout **autre**
    modèle, à commencer par le plus exposé : un corps de requête, dont les données viennent
    justement d'un joueur.

    Personne ne choisit ici où la donnée atterrit — c'est pydantic qui la range dans son message,
    et le test constate qu'elle en ressort assainie.
    """

    class CorpsDeRequete(BaseModel):
        latitude: float

    with pytest.raises(ValidationError) as refus:
        CorpsDeRequete(latitude=COORDONNEES)

    assert COORDONNEES in str(refus.value), "prémisse : pydantic recopie bien l'entrée brute"

    assaini = scrub({"exception": {"values": [{"value": str(refus.value)}]}})

    assert COORDONNEES not in " ".join(_valeurs(assaini))
    assert REDACTED in " ".join(_valeurs(assaini))


FORMES_DE_POSITION = {
    "virgule": {"m": "48.858370, 2.294481"},
    "longitude négative": {"m": "48.858370, -2.294481"},
    "longitude négative, espace": {"m": "48.858370 -2.294481"},
    "tiret nu": {"server_name": "hote-48.858370-2.294481"},
    "tiret espacé": {"m": "48.858370 - 2.294481"},
    "query string REST": {"request": {"query_string": "lat=48.858370&lon=2.294481"}},
    "WKT PostGIS": {"m": "POINT(2.294481 48.858370)"},
    "JSON sérialisé en chaîne": {"m": '{"latitude": 48.858370, "longitude": 2.294481}'},
    "saut de ligne": {"m": "48.858370\n2.294481"},
    "point-virgule": {"m": "48.858370;2.294481"},
    "paramètres d'un log": {"logentry": {"params": [48.858370, 2.294481]}},
    "extra en flottants": {"extra": {"position": [48.858370, 2.294481]}},
    "contexts en flottants": {"contexts": {"territoire": {"lat": 48.858370, "lon": 2.294481}}},
    "breadcrumb x/y": {"breadcrumbs": {"values": [{"data": {"y": 48.858370, "x": 2.294481}}]}},
}
"""**La population**, pas un échantillon : toutes les formes sous lesquelles une position peut
atteindre Sentry.

Écrite ici parce qu'un correctif de fuite se juge sur la classe entière et non sur l'occurrence
qui l'a révélée. Les chaînes d'abord, puis les quatre formes en **nombres** — deux
sous-classes que rien ne rapproche à la lecture, et qui ont chacune fait fuir une position pendant
que l'autre était couverte.
"""

NOMBRES_LEGITIMES = {
    "flottant isolé": {"extra": {"duree_ms": 12.345678}},
    "entiers": {"extra": {"requetes": 600, "fenetre": 60}},
    "nombres ronds": {"extra": {"taux": 1.0, "part": 0.25}},
    "un seul précis": {"extra": {"p50": 12.345678, "taux": 1.0}},
}
"""Ce que la règle de la paire ne doit **pas** emporter.

Un flottant isolé est indécidable et reste ; deux flottants dont un seul a la forme d'un degré
restent aussi. C'est ce qui empêche l'assainissement d'avaler la moitié des nombres d'un événement.
"""


@pytest.mark.parametrize("evenement", FORMES_DE_POSITION.values(), ids=FORMES_DE_POSITION)
def test_aucune_forme_de_position_n_atteint_sentry(evenement: dict[str, Any]) -> None:
    """Le balayage de la classe : chaque forme sous laquelle une position peut voyager.

    Mesuré à l'écriture : sept des onze formes d'alors fuyaient tandis que la huitième était
    couverte et servait de preuve. Les ajouter une à une au fil des incidents reviendrait à
    découvrir chacune en production.
    """
    rendu = json.dumps(scrub(evenement))

    assert "48.85837" not in rendu
    assert "2.294481" not in rendu


@pytest.mark.parametrize("evenement", NOMBRES_LEGITIMES.values(), ids=NOMBRES_LEGITIMES)
def test_un_nombre_qui_n_est_pas_une_position_survit(evenement: dict[str, Any]) -> None:
    assert REDACTED not in json.dumps(scrub(evenement))


def test_scrub_ne_rend_jamais_none_quel_que_soit_l_evenement() -> None:
    """`None` rendu par un `before_send` fait **abandonner l'événement** par le SDK (lu en source).

    Ce module ne décide jamais d'abandonner : c'est le rôle de l'échantillonnage, qui est un
    réglage. Une régression qui rendrait `None` sur une forme d'événement particulière couperait
    la collecte pour cette forme-là, sans aucun signal — Sentry note l'abandon dans son propre
    journal interne, que personne ne lit.
    """
    for evenement in ({}, {"exception": None}, _evenement_complet(), {"extra": {"vide": None}}):
        assert scrub(evenement) is not None


def test_scrub_est_pur_et_ne_modifie_pas_l_evenement_recu() -> None:
    """Un `before_send` qui muterait son entrée rendrait son propre test dépendant de l'ordre."""
    evenement = _evenement_complet()

    scrub(evenement)

    assert COORDONNEES in evenement["logentry"]["message"]


def test_un_dsn_absent_n_initialise_pas_sentry(monkeypatch: pytest.MonkeyPatch) -> None:
    """« Désactivé » doit vouloir dire *aucun appel*, pas un `init` avec un DSN vide.

    Un `init(dsn=None)` installe quand même les intégrations, les handlers de journalisation et
    le hook d'exceptions non rattrapées. C'est une différence qu'on ne voit pas en développement
    et qui compte partout ailleurs.
    """
    appels = _init_espionne(monkeypatch)

    configure_sentry(reglages_surcharges({}))

    assert appels == []


def test_un_dsn_pose_initialise_sentry_avec_les_garde_fous(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    appels = _init_espionne(monkeypatch)

    configure_sentry(reglages_surcharges({"sentry_dsn": DSN, "sentry_sample_rate": 0.25}))

    (appel,) = appels
    assert appel["dsn"] == DSN
    assert appel["sample_rate"] == 0.25
    assert appel["send_default_pii"] is False
    assert appel["include_local_variables"] is False
    assert appel["before_send"] is scrub
    assert "traces_sample_rate" not in appel

    scrubber = appel["event_scrubber"]
    assert scrubber.recursive is True
    assert {"latitude", "longitude", "password"} <= set(scrubber.denylist)


def test_le_denylist_couvre_les_cles_de_position_sans_perdre_celles_du_sdk() -> None:
    """`EventScrubber` **remplace** son denylist par défaut quand on lui en passe un (lu en source).

    Le nôtre doit donc contenir les deux : les clés du SDK — `password`, `token`, `authorization`,
    `cookie`… — et celles que ce projet ajoute, les clés de position. En perdre la moitié en
    croyant en ajouter est l'erreur que ce test existe pour empêcher.
    """
    denylist = sentry_module.DENYLIST

    assert {"latitude", "longitude", "lat", "lon", "email"} <= set(denylist)
    assert {"password", "token", "authorization", "cookie"} <= set(denylist)


async def test_l_identifiant_de_requete_devient_un_tag_sentry(client: AsyncClient) -> None:
    """Sans tag, retrouver dans Sentry les journaux d'une erreur demande de croiser à la main.

    **Ce que ce test prouve, et ce qu'il ne prouve pas.** Il prouve que le middleware pose bien la
    clé et la bonne valeur : retirer l'appel, poser une constante ou viser la portée courante au
    lieu de la portée d'isolation le font rougir. Il ne prouve **pas** l'isolation entre requêtes,
    qui vient de l'intégration ASGI du SDK — absente ici, Sentry étant désactivé dans la suite. La
    portée lue est donc celle du processus, et le test relit ce qu'il vient d'écrire.

    L'isolation elle-même est une propriété du SDK, vérifiée dans ses sources
    (`integrations/asgi.py` ouvre `with sentry_sdk.isolation_scope()` par requête) et non ici.
    """
    try:
        reponse = await client.get("/health")

        assert sentry_sdk.get_isolation_scope()._tags["request_id"] == reponse.headers[HEADER]
    finally:
        # Dans un `finally` : un échec de l'assertion laisserait sinon le tag posé pour toute la
        # suite — exactement ce que cette ligne existe pour éviter.
        sentry_sdk.get_isolation_scope().remove_tag("request_id")


class TransportFactice(Transport):
    """Un transport qui garde les enveloppes au lieu de les envoyer.

    C'est ce qui permet d'éprouver un événement **tel que le SDK le construit** — sérialisation,
    piles, variables locales comprises — sans réseau ni projet Sentry. Les tests de `scrub` seul
    ne peuvent pas le faire : ils partent d'un dictionnaire écrit à la main, donc de ce qu'on
    *croit* que le SDK produit.
    """

    def __init__(self) -> None:
        super().__init__()
        self.evenements: list[dict[str, Any]] = []

    def capture_envelope(self, envelope: Any) -> None:
        for element in envelope.items:
            self.evenements.append(json.loads(element.payload.get_bytes()))


@pytest.fixture
def sentry_reel() -> Iterator[TransportFactice]:
    """Sentry réellement initialisé, puis branché sur un transport qui n'envoie rien.

    Le transport est posé **après** `configure_sentry`, sur le client : lui ouvrir un paramètre
    dans la fonction de production ajouterait à celle-ci une surface qui n'existe que pour les
    tests — et une surface par laquelle on peut avaler silencieusement tous les événements.

    **Ce que le démontage ne fait pas** : il ne remet pas le SDK à l'arrêt. `init` est un effet
    global de processus, et il est **irréversible** en pratique — les intégrations restent
    chargées, `sys.excepthook`, `logging.Logger.callHandlers` et `starlette.routing` restent
    remplacés. Ce qu'on annule est le seul effet qui compte ici : le transport, remis à `None`,
    de sorte qu'aucun test suivant n'expédie ses événements dans ce tampon-ci. La conséquence à
    connaître : après ce test, le processus reste instrumenté par Sentry.
    """
    transport = TransportFactice()
    configure_sentry(reglages_surcharges({"sentry_dsn": DSN}))
    sentry_sdk.get_client().transport = transport
    yield transport
    sentry_sdk.get_client().transport = None


def test_une_position_en_variable_locale_ne_part_pas_vers_sentry(
    sentry_reel: TransportFactice,
) -> None:
    """Le chemin par lequel une coordonnée fuit sans qu'aucun des deux filets ne la voie.

    Mesuré : le SDK joint par défaut les **variables locales** de chaque frame de la pile
    (`include_local_variables`), et son sérialiseur éclate un tuple en éléments séparés — une
    position devient `["48.85837", "2.294481"]`. `EventScrubber` ne la voit pas, la clé n'étant
    pas au denylist ; `scrub` ne la voit pas non plus, chaque nombre étant devenu une chaîne
    isolée et le motif exigeant la paire.

    Le domaine Territoire est fait de fonctions dont les variables locales *sont* des coordonnées.
    C'est exactement « l'historique de localisation que §12.3 interdit » du cadrage §13.10.
    """

    def route_du_territoire() -> None:
        position = LATITUDE, LONGITUDE  # noqa: F841 — sa présence dans la frame est le sujet
        raise RuntimeError("capture impossible")

    try:
        route_du_territoire()
    except RuntimeError:
        sentry_sdk.capture_exception()

    (evenement,) = sentry_reel.evenements
    rendu = json.dumps(evenement)
    assert str(LATITUDE) not in rendu
    assert str(LONGITUDE) not in rendu


def test_la_fabrique_d_application_initialise_sentry(
    monkeypatch: pytest.MonkeyPatch, settings: Settings
) -> None:
    """L'hôte HTTP est l'un des deux qui servent du trafic — l'autre est le worker, testé ailleurs.

    Sans cette assertion, retirer l'appel de `create_app` laisse toute la suite au vert : le DSN
    est absent en test, donc `configure_sentry` réel ne fait rien d'observable.
    """
    recus: list[Settings] = []
    monkeypatch.setattr(main, "configure_sentry", recus.append)

    create_app(settings)

    assert recus == [settings]
