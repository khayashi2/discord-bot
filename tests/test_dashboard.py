"""Tests for the dashboard FastAPI app."""

import pytest
from httpx import ASGITransport, AsyncClient

from dashboard.app import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Health endpoint should return ok status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_index_returns_html():
    """Index page should return HTML content."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
