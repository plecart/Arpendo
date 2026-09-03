"""Sentry côté serveur : ce qu'on envoie, ce qu'on retire, et quand on n'envoie rien du tout."""

from typing import Any

import pytest
import sentry_sdk
from conftest import reglages_surcharges
from httpx import AsyncClient
from pydantic import ValidationError

from arpendo_api import main
from arpendo_api.core import sentry as sentry_module
from arpendo_api.core.request_id import HEADER
from arpendo_api.core.sentry import configure_sentry, scrub
from arpendo_api.core.settings import Settings
from arpendo_api.main import create_app

DSN = "https://cle-de-projet@o0.ingest.sentry.io/1"
"""Un DSN de forme valide. Aucun réseau n'est joint : `init` est toujours doublé dans ces tests."""

COORDONNEES = "48.858370, 2.294481"
"""Une position — le motif que le cadrage §12.3 interdit de laisser reconstituer."""

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
    travaille par clés et ne regarde pas la valeur d'une exception : mesuré au triage, il la laisse
    passer entière.
    """
    try:
        reglages_surcharges({"valkey_password": "   "})
    except ValidationError as invalide:
        texte = str(invalide)

    evenement = {"exception": {"values": [{"type": "ValidationError", "value": texte}]}}
    evenement["exception"]["values"][0]["value"] = f"{texte} {JETON}"

    assaini = scrub(evenement)

    assert JETON not in " ".join(_valeurs(assaini))


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
    appels: list[dict[str, Any]] = []
    monkeypatch.setattr(sentry_module.sentry_sdk, "init", lambda **kw: appels.append(kw))

    configure_sentry(reglages_surcharges({}))

    assert appels == []


def test_un_dsn_pose_initialise_sentry_avec_les_garde_fous(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    appels: list[dict[str, Any]] = []
    monkeypatch.setattr(sentry_module.sentry_sdk, "init", lambda **kw: appels.append(kw))
    reglages: Settings = reglages_surcharges({"sentry_dsn": DSN, "sentry_sample_rate": 0.25})

    configure_sentry(reglages)

    (appel,) = appels
    assert appel["dsn"] == DSN
    assert appel["sample_rate"] == 0.25
    assert appel["send_default_pii"] is False
    assert appel["before_send"] is scrub
    assert "traces_sample_rate" not in appel


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
