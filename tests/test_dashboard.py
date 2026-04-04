"""Tests for the dashboard FastAPI app and analytics queries."""

from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from dashboard.app import app
from dashboard.queries import (
    EMOJI_PATTERN,
    FILTERED_WORDS,
    STOPWORDS,
    URL_PATTERN,
    WORD_PATTERN,
    _clean_content,
    _is_filtered_word,
)

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


def test_url_pattern_strips_urls():
    """URL_PATTERN should match http/https and www URLs."""
    text = "check https://example.com and www.foo.org here"
    cleaned = URL_PATTERN.sub("", text)
    assert "https://example.com" not in cleaned
    assert "www.foo.org" not in cleaned
    assert "check" in cleaned


def test_clean_content_removes_urls():
    """_clean_content should strip URLs from text."""
    result = _clean_content("visit https://discord.gg/abc for info")
    assert "https://discord.gg/abc" not in result
    assert "visit" in result


def test_is_filtered_word_excludes_extensions_and_stopwords():
    """_is_filtered_word should catch stopwords, extensions, and domains."""
    assert _is_filtered_word("jpg") is True
    assert _is_filtered_word("com") is True
    assert _is_filtered_word("https") is True
    assert _is_filtered_word("the") is True
    assert _is_filtered_word("discord") is False
    assert _is_filtered_word("hello") is False


def test_filtered_words_contains_expected():
    """FILTERED_WORDS should include file extensions and domain suffixes."""
    assert "gif" in FILTERED_WORDS
    assert "pdf" in FILTERED_WORDS
    assert "org" in FILTERED_WORDS


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
    "get_activity_over_time": [{"day": "2026-04-01", "count": 100}],
    "get_top_words": [{"word": "discord", "count": 50}],
    "get_emoji_stats": {
        "total_emoji": 200,
        "msgs_with_emoji": 80,
        "top_emoji": [{"emoji": "\U0001f60a", "count": 30}],
    },
    "get_profanity_leaderboard": [
        {"display_name": "Bob", "avatar_url": None, "count": 42},
    ],
    "get_activity_heatmap": [{"dow": 1, "hour": 14, "count": 25}],
    "get_awards": [
        {
            "title": "Chatterbox",
            "icon": "\U0001f4ac",
            "member_display_name": "Alice",
            "member_avatar_url": None,
            "detail_text": "500 messages sent",
        },
    ],
    "get_vocabulary_diversity": [
        {
            "display_name": "Alice",
            "ttr": 0.45,
            "unique_words": 450,
            "total_words": 1000,
        },
    ],
    "get_conversation_flow": [
        {"from_user": "Alice", "to_user": "Bob", "count": 30},
    ],
    "get_peak_hours": [{"hour": 14, "count": 50}],
    "get_reaction_time_kings": [
        {"display_name": "Alice", "avg_seconds": 32.5, "response_count": 15},
    ],
    "get_channel_activity": [
        {"name": "general", "count": 1000, "last_message": "2026-04-03 14:30"},
    ],
    "get_digest": {
        "today_msgs": 42,
        "yesterday_msgs": 38,
        "msg_delta_pct": 10.5,
        "today_users": 5,
        "yesterday_users": 4,
        "user_delta_pct": 25.0,
        "week_msgs": 300,
        "last_week_msgs": 280,
        "week_msg_delta_pct": 7.1,
        "week_users": 12,
        "last_week_users": 10,
        "week_user_delta_pct": 20.0,
    },
    "get_unique_users_over_time": [{"day": "2026-04-01", "unique_users": 8}],
    "get_word_cloud_data": [{"word": "discord", "count": 50}],
    "get_sentiment_trend": [{"day": "2026-04-01", "positive": 10, "negative": 3}],
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
        stack.enter_context(
            patch(
                "dashboard.app.settings.load_profanity_words", return_value=frozenset()
            )
        )

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

        # Check data is injected as JSON for Chart.js
        assert "discord" in html  # top word
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
        "get_activity_over_time": [],
        "get_top_words": [],
        "get_emoji_stats": {"total_emoji": 0, "msgs_with_emoji": 0, "top_emoji": []},
        "get_profanity_leaderboard": [],
        "get_activity_heatmap": [],
        "get_awards": [],
        "get_vocabulary_diversity": [],
        "get_conversation_flow": [],
        "get_peak_hours": [],
        "get_reaction_time_kings": [],
        "get_channel_activity": [],
        "get_digest": {
            "today_msgs": 0,
            "yesterday_msgs": 0,
            "msg_delta_pct": 0,
            "today_users": 0,
            "yesterday_users": 0,
            "user_delta_pct": 0,
            "week_msgs": 0,
            "last_week_msgs": 0,
            "week_msg_delta_pct": 0,
            "week_users": 0,
            "last_week_users": 0,
            "week_user_delta_pct": 0,
        },
        "get_unique_users_over_time": [],
        "get_word_cloud_data": [],
        "get_sentiment_trend": [],
    }

    with ExitStack() as stack:
        _patch_session(stack)
        _patch_queries(stack, empty_results)
        stack.enter_context(
            patch(
                "dashboard.app.settings.load_profanity_words", return_value=frozenset()
            )
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")

        assert response.status_code == 200
        assert "No activity data yet" in response.text
        assert "No user data yet" in response.text


@pytest.mark.asyncio
async def test_user_page_returns_html():
    """User stats page should return HTML with member dropdown."""
    with ExitStack() as stack:
        _patch_session(stack)
        stack.enter_context(
            patch(
                "dashboard.app.get_all_members",
                AsyncMock(
                    return_value=[
                        {
                            "id": 1,
                            "username": "alice",
                            "display_name": "Alice",
                            "avatar_url": None,
                        },
                    ]
                ),
            )
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/user")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Alice" in response.text
        assert "user-select" in response.text


@pytest.mark.asyncio
async def test_user_stats_api_returns_json():
    """User stats API should return JSON with analytics for an existing member."""
    with ExitStack() as stack:
        mock_session_factory = stack.enter_context(patch("dashboard.app.async_session"))
        mock_session = AsyncMock()
        # Return 1 for the member-existence check (session.scalar)
        mock_session.scalar = AsyncMock(return_value=1)
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        stack.enter_context(
            patch(
                "dashboard.app.get_user_top_words",
                AsyncMock(return_value=[{"word": "hello", "count": 10}]),
            )
        )
        stack.enter_context(
            patch(
                "dashboard.app.get_user_message_count",
                AsyncMock(return_value=100),
            )
        )
        stack.enter_context(
            patch(
                "dashboard.app.get_user_activity_over_time",
                AsyncMock(return_value=[{"day": "2026-04-01", "count": 10}]),
            )
        )
        stack.enter_context(
            patch(
                "dashboard.app.get_user_emoji_stats",
                AsyncMock(
                    return_value={
                        "total_emoji": 30,
                        "msgs_with_emoji": 15,
                        "top_emoji": [{"emoji": "\U0001f60a", "count": 10}],
                    }
                ),
            )
        )
        stack.enter_context(
            patch(
                "dashboard.app.get_user_top_profanity_words",
                AsyncMock(return_value=[{"word": "damn", "count": 5}]),
            )
        )
        stack.enter_context(
            patch(
                "dashboard.app.get_user_peak_hours",
                AsyncMock(
                    return_value=[{"hour": 14, "count": 20}],
                ),
            )
        )
        stack.enter_context(
            patch(
                "dashboard.app.get_user_vocabulary_diversity",
                AsyncMock(
                    return_value={
                        "ttr": 0.456,
                        "unique_words": 200,
                        "total_words": 438,
                    },
                ),
            )
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/user/12345")

        assert response.status_code == 200
        data = response.json()
        assert data["message_count"] == 100
        assert data["top_words"][0]["word"] == "hello"
        assert data["activity"][0]["day"] == "2026-04-01"
        assert data["emoji_stats"]["total_emoji"] == 30
        assert data["profanity_words"][0]["word"] == "damn"
        assert data["peak_hours"][0]["hour"] == 14
        assert data["vocabulary"]["ttr"] == 0.456


@pytest.mark.asyncio
async def test_user_stats_api_with_range_parameter():
    """User stats API should pass cutoff to query functions when range is provided."""
    with ExitStack() as stack:
        mock_session_factory = stack.enter_context(patch("dashboard.app.async_session"))
        mock_session = AsyncMock()
        mock_session.scalar = AsyncMock(return_value=1)
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_top_words = stack.enter_context(
            patch(
                "dashboard.app.get_user_top_words",
                AsyncMock(return_value=[]),
            )
        )
        stack.enter_context(
            patch("dashboard.app.get_user_message_count", AsyncMock(return_value=0))
        )
        stack.enter_context(
            patch(
                "dashboard.app.get_user_activity_over_time",
                AsyncMock(return_value=[]),
            )
        )
        stack.enter_context(
            patch(
                "dashboard.app.get_user_emoji_stats",
                AsyncMock(
                    return_value={
                        "total_emoji": 0,
                        "msgs_with_emoji": 0,
                        "top_emoji": [],
                    }
                ),
            )
        )
        stack.enter_context(
            patch(
                "dashboard.app.get_user_top_profanity_words",
                AsyncMock(return_value=[]),
            )
        )
        stack.enter_context(
            patch(
                "dashboard.app.get_user_peak_hours",
                AsyncMock(return_value=[]),
            )
        )
        stack.enter_context(
            patch(
                "dashboard.app.get_user_vocabulary_diversity",
                AsyncMock(return_value={"ttr": 0, "unique_words": 0, "total_words": 0}),
            )
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/user/12345?range=7d")

        assert response.status_code == 200
        # Verify that after was passed (non-None) to query functions
        call_kwargs = mock_top_words.call_args
        assert call_kwargs.kwargs["after"] is not None


@pytest.mark.asyncio
async def test_user_stats_api_ignores_invalid_range():
    """User stats API should treat invalid range as all-time (after=None)."""
    with ExitStack() as stack:
        mock_session_factory = stack.enter_context(patch("dashboard.app.async_session"))
        mock_session = AsyncMock()
        mock_session.scalar = AsyncMock(return_value=1)
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_top_words = stack.enter_context(
            patch(
                "dashboard.app.get_user_top_words",
                AsyncMock(return_value=[]),
            )
        )
        stack.enter_context(
            patch("dashboard.app.get_user_message_count", AsyncMock(return_value=0))
        )
        stack.enter_context(
            patch(
                "dashboard.app.get_user_activity_over_time",
                AsyncMock(return_value=[]),
            )
        )
        stack.enter_context(
            patch(
                "dashboard.app.get_user_emoji_stats",
                AsyncMock(
                    return_value={
                        "total_emoji": 0,
                        "msgs_with_emoji": 0,
                        "top_emoji": [],
                    }
                ),
            )
        )
        stack.enter_context(
            patch(
                "dashboard.app.get_user_top_profanity_words",
                AsyncMock(return_value=[]),
            )
        )
        stack.enter_context(
            patch(
                "dashboard.app.get_user_peak_hours",
                AsyncMock(return_value=[]),
            )
        )
        stack.enter_context(
            patch(
                "dashboard.app.get_user_vocabulary_diversity",
                AsyncMock(return_value={"ttr": 0, "unique_words": 0, "total_words": 0}),
            )
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/user/12345?range=invalid")

        assert response.status_code == 200
        # Invalid range should result in after=None (all-time)
        call_kwargs = mock_top_words.call_args
        assert call_kwargs.kwargs["after"] is None


@pytest.mark.asyncio
async def test_user_stats_api_returns_404_for_unknown_member():
    """User stats API should return 404 for a non-existent member."""
    with ExitStack() as stack:
        mock_session_factory = stack.enter_context(patch("dashboard.app.async_session"))
        mock_session = AsyncMock()
        # Return 0 for the member-existence check
        mock_session.scalar = AsyncMock(return_value=0)
        mock_session_factory.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/user/999999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Member not found"
