"""Réglages de l'application, lus dans l'environnement et nulle part ailleurs."""

from typing import Annotated

from pydantic import AfterValidator, Field, SecretStr
from pydantic_settings import BaseSettings


def _reject_blank(text: str) -> str:
    """Rejette une valeur que le shell a posée mais qui ne porte rien.

    ``VALKEY_PASSWORD="   "`` n'est pas une variable absente : elle existe, elle est non vide, et
    une longueur minimale la laisserait passer. Elle n'authentifie pourtant rien. Refuser le blanc
    ramène ce cas à celui qu'on sait déjà traiter — un démarrage qui échoue bruyamment.

    Args:
        text: la valeur brute lue dans l'environnement.

    Returns:
        La valeur inchangée. On ne la rogne pas : c'est une validation, pas une correction, et
        rogner en silence masquerait un ``.env`` mal écrit au lieu de le signaler.

    Raises:
        ValueError: si la valeur ne contient que des blancs.
    """
    if not text.strip():
        raise ValueError("valeur vide ou faite uniquement de blancs")
    return text


def _reject_blank_secret(secret: SecretStr) -> SecretStr:
    """La même règle, appliquée sous l'emballage.

    On rend le secret reçu plutôt qu'un emballage neuf : ``_reject_blank`` ne sert ici qu'à
    lever, et sa valeur de retour n'a pas d'usage. Le message d'erreur, lui, ne cite jamais la
    valeur — pydantic nomme le champ, pas son contenu.
    """
    _reject_blank(secret.get_secret_value())
    return secret


NonEmpty = Annotated[str, AfterValidator(_reject_blank)]
"""Une chaîne requise et non blanche — le type de tout réglage qu'on peut afficher."""

Secret = Annotated[SecretStr, AfterValidator(_reject_blank_secret)]
"""Une chaîne requise et non blanche, mais **masquée** partout où les réglages s'affichent.

Le type de tout réglage sensible : ``repr``, ``str`` et ``model_dump()`` en rendent
``SecretStr('**********')``, donc ni une trace, ni un journal, ni un rapport d'erreur qui
sérialise les réglages ne peut le divulguer. La valeur ne s'obtient que par un
``.get_secret_value()`` explicite, et seule la fabrique qui la consomme a une raison de l'écrire.

Tout futur secret — clé de session, DSN Sentry, jeton FCM — se déclare avec cet alias. **Une règle
ajoutée ici ne doit jamais rejeter sur le contenu** : pydantic recopie l'entrée *brute* dans le
``input_value`` de sa ``ValidationError``, avant l'emballage. Refuser le blanc est sûr — la valeur
imprimée est alors du blanc ; refuser un format ferait imprimer le secret dans la trace même que
cet alias existe pour assainir.
"""


Threshold = Annotated[int, Field(ge=1)]
"""Un réglage entier dont zéro n'est pas une valeur — le type de toute borne de limitation.

Un quota de zéro requête, ou une fenêtre de zéro seconde, ne limite pas : il ferme. C'est une
configuration qu'on ne peut avoir voulue, et la refuser au démarrage évite de la découvrir en
production, une requête rejetée à la fois. La borne est ici et non dans le limiteur : un réglage
impossible ne doit pas exister, plutôt que d'être rattrapé à chaque usage.
"""


class Settings(BaseSettings):
    """Configuration de l'api, validée une fois pour toutes au démarrage.

    Seule porte d'entrée de la configuration : **rien** ne lit ``os.environ`` ailleurs. La classe
    ne déclare aucun ``env_file`` — le cadrage §13.9 règle 5 interdit tout fichier propre à une
    instance, pour qu'ajouter un serveur ne demande que des variables d'environnement. Le ``.env``
    du poste est chargé en amont, par le justfile en local et par Compose dans les conteneurs.

    Aucun champ n'a de valeur par défaut et tous refusent le vide — le blanc pour les chaînes,
    zéro pour les seuils : construire ``Settings`` sans l'une des variables, ou avec une variable
    posée mais sans contenu utile, lève une ``pydantic.ValidationError``. Cet échec est voulu
    bruyant et immédiat — une api qui démarre avec une configuration trouée échoue plus tard,
    plus loin, et sur une erreur moins lisible.

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
        rate_limit_ip_requests: requêtes autorisées par adresse IP et par fenêtre.
        rate_limit_ip_window_seconds: durée de cette fenêtre, en secondes.

    Exemple :
        >>> Settings()  # doctest: +SKIP
        Settings(database_url=SecretStr('**********'), valkey_url='redis://…',
                 valkey_password=SecretStr('**********'), rate_limit_ip_requests=600,
                 rate_limit_ip_window_seconds=60)
    """

    database_url: Secret
    valkey_url: NonEmpty
    valkey_password: Secret
    rate_limit_ip_requests: Threshold
    rate_limit_ip_window_seconds: Threshold
