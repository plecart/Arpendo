"""Sonde de vie de l'hôte HTTP, pour le reverse proxy et le moniteur d'uptime."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Répond ``{"status": "ok"}`` dès que le processus sert des requêtes.

    Ne vérifie aucune dépendance : un 200 signifie « le processus est vivant », rien de plus.
    """
    return {"status": "ok"}
