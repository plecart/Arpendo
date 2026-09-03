"""Sentry côté serveur : ce qu'on envoie, ce qu'on retire, et quand on n'envoie rien du tout."""

import json
from collections.abc import Iterator
from typing import Annotated, Any

import pytest
import sentry_sdk
from conftest import reglages_surcharges
from httpx import AsyncClient
from pydantic import AfterValidator, ValidationError
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
    "1.0.0+42",
    "arpendo_api.core.bus",
)
"""Ce qui **ressemble** à une donnée sensible sans en être une.

Un horodatage ISO porte une décimale à six chiffres, un index H3 une longue chaîne hexadécimale,
un numéro de build un point. Un assainissement qui les emporte rend les journaux Sentry inutiles
au diagnostic — et personne ne s'en aperçoit avant d'en avoir besoin.
"""


def _init_espionne(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Substitue `sentry_sdk.init` par un espion et rend la liste de ses appels.

    Doublure d'une **frontière du système** : `init` ouvre une porte vers le réseau et installe des
    effets globaux de processus. Ce qu'on éprouve ici est ce qu'on lui demande, pas ce qu'il en
    fait — le test qui capture un vrai événement, lui, l'appelle pour de bon.
    """
    appels: list[dict[str, Any]] = []
    monkeypatch.setattr(sentry_module.sentry_sdk, "init", lambda **kw: appels.append(kw))
    return appels


def _refuse_toujours(valeur: str) -> str:
    """Un validateur qui rejette **en citant la valeur** — ce que `Secret` interdit précisément.

    Il monte le seul cas où pydantic met une donnée d'utilisateur dans le texte de son exception :
    un validateur de format. Aucun réglage réel n'en porte, et c'est une règle écrite ; l'éprouver
    demande donc de la transgresser ici, dans un `Settings` jetable.
    """
    raise ValueError(f"format attendu, reçu : {valeur}")


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
        "extra": {"contexte": f"{EMAIL} depuis {COORDONNEES}"},
        "request": {"headers": {"Authorization": JETON}, "query_string": f"pos={COORDONNEES}"},
        "release": "1.0.0+42",
        "timestamp": "2026-09-03T08:41:35.751365Z",
        "tags": {"request_id": "8a2a1072b59ffff", "logger": "arpendo_api.core.bus"},
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

    `pydantic` recopie l'entrée **brute** dans le `input_value` de sa `ValidationError`, avant tout
    emballage `SecretStr` — et le texte de l'exception la porte donc en clair. `EventScrubber`
    travaille par clés et ne regarde jamais la valeur d'une exception.

    L'entrée est ici **une vraie position refusée par un vrai validateur**, pas une chaîne
    concaténée par le test : c'est ce qui distingue ce cas du balayage général, qui pose lui-même
    ses motifs aux bons endroits. Ici personne ne choisit où la donnée atterrit — c'est pydantic
    qui la range dans son message, et le test constate qu'elle en ressort assainie.
    """

    class ReglagesAuFormat(Settings):
        valkey_url: Annotated[str, AfterValidator(_refuse_toujours)]

    with pytest.raises(ValidationError) as refus:
        ReglagesAuFormat(valkey_url=COORDONNEES)

    assaini = scrub({"exception": {"values": [{"value": str(refus.value)}]}})

    assert COORDONNEES not in " ".join(_valeurs(assaini))
    assert REDACTED in " ".join(_valeurs(assaini))


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

    Le tag est lu sur la portée d'**isolation**, celle que l'intégration ASGI du SDK ouvre par
    requête. Ici aucune intégration n'est active — Sentry est désactivé dans la suite — donc la
    portée est celle du processus : ce test prouve l'appel et sa valeur, pas l'isolation, que
    seule l'intégration fournit.
    """
    reponse = await client.get("/health")

    assert sentry_sdk.get_isolation_scope()._tags["request_id"] == reponse.headers[HEADER]


class TransportFactice(Transport):
    """Un transport qui garde les enveloppes au lieu de les envoyer.

    C'est ce qui permet d'éprouver un événement **tel que le SDK le construit** — sérialisation,
    piles, variables locales comprises — sans réseau ni projet Sentry. Les tests de `scrub` seul
    ne peuvent pas le faire : ils partent d'un dictionnaire écrit à la main, donc de ce qu'on
    *croit* que le SDK produit.
    """

    def __init__(self) -> None:
        self.evenements: list[dict[str, Any]] = []

    def capture_envelope(self, envelope: Any) -> None:
        for element in envelope.items:
            self.evenements.append(json.loads(element.payload.get_bytes()))


@pytest.fixture
def sentry_reel() -> Iterator[TransportFactice]:
    """Sentry réellement initialisé, mais branché sur un transport qui n'envoie rien.

    Remet le SDK à l'arrêt après le test : `init` est un effet global de processus, et le laisser
    en place ferait partir les événements des tests suivants dans ce transport-ci.
    """
    transport = TransportFactice()
    configure_sentry(reglages_surcharges({"sentry_dsn": DSN}), transport=transport)
    yield transport
    sentry_sdk.get_client().close()
    sentry_sdk.init(dsn=None)


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
