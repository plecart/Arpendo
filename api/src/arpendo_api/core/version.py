"""Seuils de version du client — la première chose que l'application mobile demande."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from arpendo_api.core.settings import Settings

router = APIRouter()


class VersionThresholds(BaseModel):
    """Ce que le serveur publie sur les versions du client — deux nombres, aucun verdict.

    Le serveur **ne décide pas** si le client qui l'interroge est acceptable : il annonce ses deux
    seuils, et l'application compare. Lui faire rendre un verdict à partir de
    ``X-Client-Version`` couplerait cette route à l'en-tête et priverait l'application de la
    connaissance de sa cible — elle ne saurait plus quoi afficher, ni dans l'écran bloquant
    (spec UX §11.2), ni dans le bandeau de mise à jour recommandée.

    Les deux champs sont des **numéros de build** — l'entier monotone de ``version: x.y.z+N`` du
    manifeste de l'application, jamais du semver.

    Attributs :
        min_build: le build en deçà duquel l'application est refusée. ``build < min_build`` →
            écran bloquant vers le magasin, sans retour ni fermeture (cadrage §14.1).
        recommended_build: le build en deçà duquel une mise à jour est *suggérée*.
            ``build < recommended_build`` → bandeau fermable (priorité 12, spec UX §2.4).

    Les deux comparaisons sont **strictes** : un build égal à un seuil l'atteint.
    """

    min_build: int
    recommended_build: int


@router.get("/version")
async def version(request: Request) -> VersionThresholds:
    """Publie les deux seuils de version du client, sans authentification.

    C'est l'étape 1 de la séquence de démarrage (spec UX §2.1) : elle précède la session, donc
    elle ne peut pas en exiger une. Un client obsolète doit apprendre qu'il l'est **sans jamais
    taper une api qu'il ne comprend plus**.

    À la racine et non sous ``/v1`` — le pourquoi est dans ``create_app``, avec la carte des
    routeurs.

    Les seuils sortent des réglages, validés une fois au démarrage — ``min <= recommended`` y est
    déjà garanti, cette route n'a donc rien à revérifier. Aucun cache, aucun sondage : l'app
    interroge une fois par lancement, et le coût est celui d'une lecture en mémoire.
    """
    settings: Settings = request.app.state.settings
    return VersionThresholds(
        min_build=settings.client_build_min,
        recommended_build=settings.client_build_recommended,
    )
