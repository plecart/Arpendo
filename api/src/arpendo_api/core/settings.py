"""Réglages de l'application, lus dans l'environnement et nulle part ailleurs."""

from typing import Annotated

from pydantic import AfterValidator, SecretStr
from pydantic_settings import BaseSettings


def _refuse_le_blanc(texte: str) -> str:
    """Rejette une valeur que le shell a posée mais qui ne porte rien.

    ``VALKEY_PASSWORD="   "`` n'est pas une variable absente : elle existe, elle est non vide, et
    une longueur minimale la laisserait passer. Elle n'authentifie pourtant rien. Refuser le blanc
    ramène ce cas à celui qu'on sait déjà traiter — un démarrage qui échoue bruyamment.

    Args:
        texte: la valeur brute lue dans l'environnement.

    Returns:
        La valeur inchangée. On ne la rogne pas : c'est une validation, pas une correction, et
        rogner en silence masquerait un ``.env`` mal écrit au lieu de le signaler.

    Raises:
        ValueError: si la valeur ne contient que des blancs.
    """
    if not texte.strip():
        raise ValueError("valeur vide ou faite uniquement de blancs")
    return texte


def _refuse_le_secret_blanc(secret: SecretStr) -> SecretStr:
    """La même règle, appliquée sous l'emballage.

    On rend le secret reçu plutôt qu'un emballage neuf : ``_refuse_le_blanc`` ne sert ici qu'à
    lever, et sa valeur de retour n'a pas d'usage. Le message d'erreur, lui, ne cite jamais la
    valeur — pydantic nomme le champ, pas son contenu.
    """
    _refuse_le_blanc(secret.get_secret_value())
    return secret


NonEmpty = Annotated[str, AfterValidator(_refuse_le_blanc)]
"""Une chaîne requise et non blanche — le type de tout réglage qu'on peut afficher."""

Secret = Annotated[SecretStr, AfterValidator(_refuse_le_secret_blanc)]
"""Une chaîne requise et non vide, mais **masquée** partout où les réglages s'affichent.

Le type de tout réglage sensible : ``repr``, ``str`` et ``model_dump()`` en rendent
``SecretStr('**********')``, donc ni une trace, ni un journal, ni un rapport d'erreur qui
sérialise les réglages ne peut le divulguer. La valeur ne s'obtient que par un
``.get_secret_value()`` explicite, et seule la fabrique qui la consomme a une raison de l'écrire.

Tout futur secret — clé de session, DSN Sentry, jeton FCM — se déclare avec cet alias.
"""


class Settings(BaseSettings):
    """Configuration de l'api, validée une fois pour toutes au démarrage.

    Seule porte d'entrée de la configuration : **rien** ne lit ``os.environ`` ailleurs. La classe
    ne déclare aucun ``env_file`` — le cadrage §13.9 règle 5 interdit tout fichier propre à une
    instance, pour qu'ajouter un serveur ne demande que des variables d'environnement. Le ``.env``
    du poste est chargé en amont, par le justfile en local et par Compose dans les conteneurs.

    Aucun champ n'a de valeur par défaut et tous refusent le blanc : construire ``Settings``
    sans l'une des variables, ou avec une variable posée mais vide ou faite d'espaces, lève une
    ``pydantic.ValidationError``. Cet échec est voulu bruyant et immédiat — une api qui démarre
    avec une configuration trouée échoue plus tard, plus loin, et sur une erreur moins lisible.

    ``VALKEY_PASSWORD`` suit la même règle que les autres : le cadrage §13.10 exige un Valkey
    authentifié « même sans port publié », donc dans les trois environnements — poste, CI,
    production.

    Les champs sensibles sont des ``Secret`` : afficher les réglages ne révèle aucun mot de passe.

    Attributs :
        database_url: DSN PostgreSQL au format SQLAlchemy async (``postgresql+asyncpg://…``).
            Sensible : il porte le mot de passe de la base.
        valkey_url: URL du serveur Valkey (``redis://hôte:port/base``), sans le mot de passe —
            donc affichable.
        valkey_password: mot de passe Valkey, fourni séparément de l'URL. Sensible.

    Exemple :
        >>> Settings()  # doctest: +SKIP
        Settings(database_url=SecretStr('**********'), valkey_url='redis://…',
                 valkey_password=SecretStr('**********'))
    """

    database_url: Secret
    valkey_url: NonEmpty
    valkey_password: Secret
