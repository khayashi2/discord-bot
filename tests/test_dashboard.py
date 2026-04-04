"""Tests for the dashboard FastAPI app and analytics queries."""

from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from dashboard.app import app
from dashboard.queries import EMOJI_PATTERN, STOPWORDS, WORD_PATTERN

# ---------------------------------------------------------------------------
# Utility function tests (no DB required)
# ---------------------------------------------------------------------------


def _count_emojis(text: str) -> int:
    """Count emoji in text using the shared pattern."""
    return len(EMOJI_PATTERN.findall(text))


def test_word_pattern_extracts_words():
    """WORD_PATTERN should match words with 3+ letters."""
    words = WORD_PATTERN.findall("Hi there, how are you doing today?")
    assert "there" in words
    assert "how" in words
    assert "are" in words
    # "Hi" is only 2 chars, should be excluded
    assert "Hi" not in words


def test_stopwords_filters_common_words():
    """Stopwords set should contain common English words."""
    assert "the" in STOPWORDS
    assert "and" in STOPWORDS
    assert "lol" in STOPWORDS


def test_emoji_pattern_matches_unicode():
    """Emoji pattern should detect Unicode emoji."""
    assert _count_emojis("Hello \U0001f60a") == 1
    assert _count_emojis("No emoji here") == 0


def test_emoji_pattern_matches_custom_discord():
    """Emoji pattern should detect custom Discord emoji."""
    assert _count_emojis("Nice <:pepe:123456789>") == 1
    assert _count_emojis("<a:animated:99999>") == 1


# ---------------------------------------------------------------------------
# Endpoint tests (mock DB queries)
# ---------------------------------------------------------------------------

MOCK_QUERY_RESULTS = {
    "get_overview": {
        "total_messages": 1234,
        "total_members": 56,
        "total_channels": 8,
        "messages_today": 42,
    },
    "get_top_users": [
        {
            "username": "alice",
            "display_name": "Alice",
            "avatar_url": None,
            "count": 500,
        },
    ],
    "get_top_channels": [{"name": "general", "count": 800}],
    "get_activity_over_time": [{"day": "2026-04-01", "count": 100}],
    "get_top_words": [{"word": "discord", "count": 50}],
    "get_emoji_stats": {
        "total_emoji": 200,
        "msgs_with_emoji": 80,
        "top_emoji": [{"emoji": "\U0001f60a", "count": 30}],
    },
    "get_message_length_stats": {
        "avg_length": 75,
        "max_length": 1500,
        "short": 400,
        "medium": 600,
        "long": 234,
    },
}


def _patch_queries(stack: ExitStack, results: dict) -> None:
    """Patch all dashboard query functions using an ExitStack for safe cleanup."""
    base = "dashboard.app"
    for name, value in results.items():
        stack.enter_context(patch(f"{base}.{name}", AsyncMock(return_value=value)))


def _patch_session(stack: ExitStack) -> None:
    """Patch the async_session factory with a mock."""
    mock_session_factory = stack.enter_context(patch("dashboard.app.async_session"))
    mock_session = AsyncMock()
    mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)


@pytest.mark.asyncio
async def test_health_endpoint():
    """Health endpoint should return ok status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_index_returns_html_with_data():
    """Index page should return HTML with analytics data when queries succeed."""
    with ExitStack() as stack:
        _patch_session(stack)
        _patch_queries(stack, MOCK_QUERY_RESULTS)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

        html = response.text
        # Check overview stats appear
        assert "1234" in html  # total_messages
        assert "42" in html  # messages_today

        # Check chart canvases are present
        assert 'id="activityChart"' in html
        assert 'id="topUsersChart"' in html
        assert 'id="topChannelsChart"' in html
        assert 'id="topWordsChart"' in html
        assert 'id="msgLengthChart"' in html

        # Check data is injected as JSON for Chart.js
        assert "discord" in html  # top word
        assert "general" in html  # top channel
        assert "Alice" in html  # top user


@pytest.mark.asyncio
async def test_index_handles_empty_data():
    """Index page should render gracefully with no data."""
    empty_results = {
        "get_overview": {
            "total_messages": 0,
            "total_members": 0,
            "total_channels": 0,
            "messages_today": 0,
        },
        "get_top_users": [],
        "get_top_channels": [],
        "get_activity_over_time": [],
        "get_top_words": [],
        "get_emoji_stats": {"total_emoji": 0, "msgs_with_emoji": 0, "top_emoji": []},
        "get_message_length_stats": {
            "avg_length": 0,
            "max_length": 0,
            "short": 0,
            "medium": 0,
            "long": 0,
        },
    }

    with ExitStack() as stack:
        _patch_session(stack)
        _patch_queries(stack, empty_results)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")

        assert response.status_code == 200
        assert "No activity data yet" in response.text
        assert "No user data yet" in response.text
