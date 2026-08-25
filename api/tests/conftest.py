from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from arpendo_api.main import create_app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Client HTTP branché directement sur l'application, sans réseau ni serveur."""
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
