"""Réglages de l'application, lus dans l'environnement et nulle part ailleurs."""

from typing import Annotated, Self

from pydantic import AfterValidator, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

``hide_input_in_errors`` (voir ``Settings.model_config``) retire cette entrée du **message**, mais
pas de ``ValidationError.errors()`` : la règle ci-dessus reste donc la bonne, avec un filet de
moins à traverser.
"""


Threshold = Annotated[int, Field(ge=1)]
"""Un réglage entier dont zéro n'est pas une valeur.

Le type de toute borne de limitation : un quota de zéro requête, ou une fenêtre de zéro seconde,
ne limite pas, il ferme. Et celui de tout **numéro de build** : la numérotation commence à 1, si
bien qu'un seuil de zéro ne désigne aucune version publiable. Dans les deux cas c'est une
configuration qu'on ne peut avoir voulue, et la refuser au démarrage évite de la découvrir en
production — une requête rejetée à la fois, ou une flotte entière renvoyée au magasin. La borne
est ici et non au point d'usage : un réglage impossible ne doit pas exister, plutôt que d'être
rattrapé à chaque lecture.
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
        client_build_min: numéro de build en deçà duquel l'application mobile est refusée —
            elle affiche un écran bloquant vers le magasin (cadrage §14.1, spec UX §11.2).
        client_build_recommended: numéro de build en deçà duquel une mise à jour est
            *suggérée*, par un bandeau que le joueur peut fermer. Jamais inférieur à
            ``client_build_min`` — voir :meth:`_reject_min_above_recommended`.

    Exemple :
        >>> Settings()  # doctest: +SKIP
        Settings(database_url=SecretStr('**********'), valkey_url='redis://…',
                 valkey_password=SecretStr('**********'), rate_limit_ip_requests=600,
                 rate_limit_ip_window_seconds=60, client_build_min=1,
                 client_build_recommended=1)
    """

    model_config = SettingsConfigDict(hide_input_in_errors=True)
    """Aucune ``ValidationError`` de cette classe ne montre la valeur qui l'a provoquée.

    Sans ce réglage, pydantic recopie l'entrée fautive dans le message : la valeur du champ pour
    un validateur de champ, et le **dictionnaire entier** pour un validateur de modèle — donc les
    secrets, avant tout emballage en ``SecretStr``, dont le masquage n'a alors pas encore de prise.
    Mesuré : `str(e)` laissait passer `{'database_url': 'p://s3c…`.

    Ce que la troncature de pydantic cachait, elle ne le cachait que par coïncidence — la longueur
    des valeurs du projet et celle du nom de champ qui les précède. Deux coïncidences qu'un champ
    renommé ou réordonné défait sans un mot.

    Le message reste parfaitement diagnostiquable : pydantic **nomme le champ** en cause, ce qui
    est tout ce dont a besoin la personne qui répare un ``.env``. Ce qu'on retire est la valeur,
    qu'elle connaît déjà.

    Ne couvre pas ``ValidationError.errors()`` ni ``json(include_input=True)``, qui portent
    toujours l'entrée brute. Aucun code du dépôt ne les appelle ; le filtrage entrant de Sentry
    (#42) est ce qui couvre ce chemin.
    """

    database_url: Secret
    valkey_url: NonEmpty
    valkey_password: Secret
    rate_limit_ip_requests: Threshold
    rate_limit_ip_window_seconds: Threshold
    client_build_min: Threshold
    client_build_recommended: Threshold

    @model_validator(mode="after")
    def _reject_min_above_recommended(self) -> Self:
        """Refuse un plancher de version au-dessus de la version recommandée.

        Chacun des deux seuils est valide pris seul ; c'est leur **ordre** qui ne l'est pas, d'où
        un validateur de modèle et non de champ. La configuration fautive renverrait au magasin
        une flotte entière pour une mise à jour que le serveur ne présente que comme suggérée —
        un incident qui ne se voit pas côté serveur, puisque la route répond 200.

        Les deux seuils **égaux** passent : c'est l'état nominal, où la version publiée est à la
        fois le plancher et la cible.

        Le message ne cite que les noms des variables d'environnement. Ce qui l'y garantit n'est
        pas le masquage de ``SecretStr`` — un validateur de modèle voit le dictionnaire brut,
        avant tout emballage — mais ``hide_input_in_errors`` du ``model_config``, et un test
        l'éprouve sur une valeur assez courte pour survivre à la troncature de pydantic.

        Returns:
            Les réglages inchangés — un validateur ``after`` rend le modèle, il ne le remplace pas.

        Raises:
            ValueError: si ``client_build_min`` dépasse ``client_build_recommended``. pydantic
                l'emballe en ``ValidationError``, comme tout refus de validation.
        """
        if self.client_build_min > self.client_build_recommended:
            raise ValueError(
                "CLIENT_BUILD_MIN doit être inférieur ou égal à CLIENT_BUILD_RECOMMENDED : "
                "un build refusé ne peut pas être seulement recommandé"
            )
        return self
