"""Réglages de l'application, lus dans l'environnement et nulle part ailleurs."""

from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings

NonEmpty = Annotated[str, Field(min_length=1)]


class Settings(BaseSettings):
    """Configuration de l'api, validée une fois pour toutes au démarrage.

    Seule porte d'entrée de la configuration : **rien** ne lit ``os.environ`` ailleurs. La classe
    ne déclare aucun ``env_file`` — le cadrage §13.9 règle 5 interdit tout fichier propre à une
    instance, pour qu'ajouter un serveur ne demande que des variables d'environnement. Le ``.env``
    du poste est chargé en amont, par le justfile en local et par Compose dans les conteneurs.

    Aucun champ n'a de valeur par défaut et tous refusent la chaîne vide : construire ``Settings``
    sans l'une des variables, ou avec une variable posée mais vide, lève une
    ``pydantic.ValidationError``. Cet échec est voulu bruyant et immédiat — une api qui démarre
    avec une configuration trouée échoue plus tard, plus loin, et sur une erreur moins lisible.

    ``VALKEY_PASSWORD`` suit la même règle que les autres : le cadrage §13.10 exige un Valkey
    authentifié « même sans port publié », donc dans les trois environnements — poste, CI,
    production.

    Attributs :
        database_url: DSN PostgreSQL au format SQLAlchemy async (``postgresql+asyncpg://…``).
        valkey_url: URL du serveur Valkey (``redis://hôte:port/base``), sans le mot de passe.
        valkey_password: mot de passe Valkey, fourni séparément de l'URL.

    Exemple :
        >>> Settings()  # doctest: +SKIP
        Settings(database_url='postgresql+asyncpg://…', valkey_url='redis://…', …)
    """

    database_url: NonEmpty
    valkey_url: NonEmpty
    valkey_password: NonEmpty
