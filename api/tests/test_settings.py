from collections.abc import Callable

import pytest
from conftest import reglages_surcharges
from pydantic import SecretStr, ValidationError

from arpendo_api.core.settings import Settings

MOT_DE_PASSE_POSTGRESQL = "mot-de-passe-postgresql"
MOT_DE_PASSE_VALKEY = "mot-de-passe-valkey"
SECRETS = (MOT_DE_PASSE_POSTGRESQL, MOT_DE_PASSE_VALKEY)

DSN_COURT = "p://s3cr3t"
"""Un DSN **court** — le pire cas pour la divulgation, pas le cas courant."""

FRAGMENT_REVELATEUR = DSN_COURT[:7]
"""Le fragment de l'entrée brute que la troncature de pydantic laisse effectivement passer.

`str(ValidationError)` n'affiche l'entrée fautive que sur une vingtaine de caractères. Sur un
validateur de **modèle**, cette entrée est le dictionnaire entier, et son début se lit
`{'database_url': 'p://s3c...` — **mesuré**. Le mot de passe complet n'y tient donc jamais, et un
test qui ne chercherait que le secret entier serait vert par deux accidents cumulés : la longueur
de la valeur, et celle du nom de champ qui la précède. Deux accidents qu'une réorganisation des
champs, ou un nom plus court, suffiraient à défaire sans que rien ne le signale.

L'invariant qu'on veut n'est donc pas « le secret n'apparaît pas entier », c'est **« aucun
fragment de l'entrée brute n'atteint le message »** — ce que `hide_input_in_errors` garantit, et
que rien d'autre ne garantit.
"""

BLANCHES = {"vide": "", "espaces": "   ", "tabulation-et-saut": "\t\n"}
"""Les formes du vide qu'une variable d'environnement peut prendre, par nom de cas."""

SEUILS = (
    "RATE_LIMIT_IP_REQUESTS",
    "RATE_LIMIT_IP_WINDOW_SECONDS",
    "CLIENT_BUILD_MIN",
    "CLIENT_BUILD_RECOMMENDED",
)
"""Les réglages dont la valeur est un entier borné — les seuls que `0` doit faire échouer."""

REQUISES = {
    "DATABASE_URL": (
        f"postgresql+asyncpg://arpendo:{MOT_DE_PASSE_POSTGRESQL}@127.0.0.1:5432/arpendo"
    ),
    "VALKEY_URL": "redis://127.0.0.1:6379/0",
    "VALKEY_PASSWORD": MOT_DE_PASSE_VALKEY,
    "RATE_LIMIT_IP_REQUESTS": "600",
    "RATE_LIMIT_IP_WINDOW_SECONDS": "60",
    # Deux valeurs **distinctes**, et c'est nécessaire : avec un couple identique, un champ qui
    # lirait la variable de l'autre passerait le test de lecture sans qu'on le voie.
    "CLIENT_BUILD_MIN": "1",
    "CLIENT_BUILD_RECOMMENDED": "2",
}


@pytest.fixture
def environnement_complet(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isole les tests du `.env` du poste : seules les variables posées ici existent."""
    for nom in REQUISES:
        monkeypatch.delenv(nom, raising=False)
    for nom, valeur in REQUISES.items():
        monkeypatch.setenv(nom, valeur)


def _en_clair(valeur: object) -> str:
    """La valeur d'un réglage, secret déballé et rendue en texte.

    On la confronte à ce que l'environnement portait, et l'environnement n'est fait que de
    chaînes : un seuil lu en `int` se compare donc sous sa forme écrite, pas après reconversion
    du texte attendu — sinon le test ne prouverait plus que la variable a bien été lue.
    """
    return valeur.get_secret_value() if isinstance(valeur, SecretStr) else str(valeur)


@pytest.mark.parametrize("variable", sorted(REQUISES))
def test_les_reglages_lisent_chaque_variable_de_l_environnement(
    environnement_complet: None, variable: str
) -> None:
    reglages = Settings()

    assert _en_clair(getattr(reglages, variable.lower())) == REQUISES[variable]


@pytest.mark.parametrize("manquante", sorted(REQUISES))
def test_une_variable_requise_absente_empeche_le_demarrage(
    environnement_complet: None, monkeypatch: pytest.MonkeyPatch, manquante: str
) -> None:
    monkeypatch.delenv(manquante)

    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize("blanche", BLANCHES.values(), ids=BLANCHES)
@pytest.mark.parametrize("videe", sorted(REQUISES))
def test_une_variable_requise_blanche_empeche_le_demarrage(
    environnement_complet: None, monkeypatch: pytest.MonkeyPatch, videe: str, blanche: str
) -> None:
    monkeypatch.setenv(videe, blanche)

    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize("seuil", SEUILS)
def test_un_seuil_nul_empeche_le_demarrage(
    environnement_complet: None, monkeypatch: pytest.MonkeyPatch, seuil: str
) -> None:
    """Un quota de zéro requête, ou une fenêtre de zéro seconde, ne limite pas : il ferme.

    C'est une configuration qu'on ne peut avoir voulue, et que la borne basse refuse au
    démarrage plutôt que de la laisser rejeter chaque requête en production.
    """
    monkeypatch.setenv(seuil, "0")

    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize(
    ("minimum", "recommande", "accepte"),
    [("1", "1", True), ("2", "3", True), ("3", "2", False)],
    ids=["égaux", "minimum sous le recommandé", "minimum au-dessus du recommandé"],
)
def test_l_ordre_des_deux_seuils_de_version_decide_du_demarrage(
    environnement_complet: None,
    monkeypatch: pytest.MonkeyPatch,
    minimum: str,
    recommande: str,
    accepte: bool,
) -> None:
    """Un build refusé ne peut pas être seulement « recommandé » : l'ordre des deux seuils est une
    règle, pas une convention.

    L'inverse — un minimum au-dessus du recommandé — renverrait au magasin toute une flotte pour
    une mise à jour que le serveur ne présente que comme suggérée. Chaque seuil pris isolément est
    pourtant valide, d'où un validateur de **modèle** : la faute est dans la paire.

    Les trois cas bornent la frontière : **égaux** (l'état nominal, où la version publiée est à la
    fois le plancher et la cible), au-dessous, et au-dessus. Sans le premier, un validateur écrit
    en `>=` passerait la suite en refusant l'état le plus courant.
    """
    monkeypatch.setenv("CLIENT_BUILD_MIN", minimum)
    monkeypatch.setenv("CLIENT_BUILD_RECOMMENDED", recommande)

    if not accepte:
        with pytest.raises(ValidationError):
            Settings()
        return

    reglages = Settings()

    assert (reglages.client_build_min, reglages.client_build_recommended) == (
        int(minimum),
        int(recommande),
    )


@pytest.mark.parametrize("dsn", [REQUISES["DATABASE_URL"], DSN_COURT], ids=["long", "court"])
def test_le_refus_de_la_paire_de_builds_ne_divulgue_aucun_secret(
    environnement_complet: None, monkeypatch: pytest.MonkeyPatch, dsn: str
) -> None:
    """Un validateur de **modèle** voit la classe entière, et pydantic recopie l'entrée dans
    l'erreur — donc les secrets, en clair.

    C'est le piège que documente l'alias ``Secret``, aggravé d'un cran : sur un validateur de
    champ, l'entrée recopiée est la seule valeur du champ ; sur un validateur de modèle, c'est le
    **dictionnaire entier**, secrets compris. Le masquage de ``SecretStr`` n'y peut rien — mesuré :
    à ce moment-là l'emballage n'a pas encore eu lieu, pydantic tient les chaînes brutes.

    Ce qui protège réellement est ``hide_input_in_errors`` (`Settings.model_config`), et c'est ce
    que ce test éprouve. Le cas **court** est celui qui compte : sans ce réglage, la troncature de
    ``str`` suffirait à cacher un secret situé loin dans un DSN long, et le test passerait pour la
    mauvaise raison.

    Ce qu'il ne couvre **pas**, et qui reste vrai : ``errors()`` et ``json(include_input=True)``
    portent toujours l'entrée brute. Aucun code du dépôt ne les appelle ; le filtrage entrant de
    Sentry (#42) est ce qui couvre ce chemin le jour où une exception de démarrage y remonte.
    """
    monkeypatch.setenv("DATABASE_URL", dsn)
    monkeypatch.setenv("CLIENT_BUILD_MIN", "3")
    monkeypatch.setenv("CLIENT_BUILD_RECOMMENDED", "2")

    with pytest.raises(ValidationError) as refus:
        Settings()

    message = str(refus.value)

    assert [secret for secret in SECRETS if secret in message] == []
    assert FRAGMENT_REVELATEUR not in message


@pytest.mark.parametrize(
    "afficher",
    [repr, str, lambda reglages: str(reglages.model_dump())],
    ids=["repr", "str", "model_dump"],
)
def test_afficher_les_reglages_ne_divulgue_aucun_secret(
    environnement_complet: None, afficher: Callable[[Settings], str]
) -> None:
    affichage = afficher(Settings())

    assert [secret for secret in SECRETS if secret in affichage] == []


def test_une_surcharge_de_reglages_en_test_repasse_par_la_validation() -> None:
    """Un test ne peut décrire qu'un environnement que la production accepterait aussi.

    Sans cette garantie, un test prouverait quelque chose d'une application qui ne démarrerait
    jamais.
    """
    with pytest.raises(ValidationError):
        reglages_surcharges({"valkey_url": "   "})
