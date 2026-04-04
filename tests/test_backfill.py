"""Tests for the historical backfill script."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from scripts.backfill import backfill_channel


def _make_message(message_id=1000, author_bot=False):
    """Build a fake discord.Message for backfill testing."""
    channel = MagicMock()
    channel.id = 10
    channel.name = "general"
    channel.type = "text"
    channel.created_at = datetime(2024, 1, 1, tzinfo=UTC)

    author = MagicMock()
    author.id = 100
    author.name = "testuser"
    author.display_name = "testuser"
    author.avatar = None
    author.bot = author_bot
    author.joined_at = datetime(2024, 6, 1, tzinfo=UTC)

    msg = MagicMock()
    msg.id = message_id
    msg.guild = MagicMock()
    msg.channel = channel
    msg.author = author
    msg.content = "hello"
    msg.attachments = []
    msg.embeds = []
    msg.created_at = datetime(2025, 1, 15, tzinfo=UTC)
    msg.edited_at = None
    return msg


async def _fake_history(messages):
    """Async generator that yields fake messages."""
    for m in messages:
        yield m


class TestBackfillChannel:
    @pytest.mark.asyncio
    @patch("scripts.backfill.insert_message", new_callable=AsyncMock)
    @patch("scripts.backfill.upsert_member", new_callable=AsyncMock)
    @patch("scripts.backfill.upsert_channel", new_callable=AsyncMock)
    async def test_returns_message_count(
        self, mock_upsert_ch, mock_upsert_mem, mock_insert_msg
    ):
        messages = [_make_message(message_id=i) for i in range(5)]
        channel = MagicMock(spec=discord.TextChannel)
        channel.name = "general"
        channel.history.return_value = _fake_history(messages)

        session = AsyncMock()
        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        count = await backfill_channel(session_factory, channel)
        assert count == 5

    @pytest.mark.asyncio
    @patch("scripts.backfill.insert_message", new_callable=AsyncMock)
    @patch("scripts.backfill.upsert_member", new_callable=AsyncMock)
    @patch("scripts.backfill.upsert_channel", new_callable=AsyncMock)
    async def test_commits_in_batches(
        self, mock_upsert_ch, mock_upsert_mem, mock_insert_msg
    ):
        """With 1200 messages and BATCH_SIZE=500, expect multiple commits."""
        messages = [_make_message(message_id=i) for i in range(1200)]
        channel = MagicMock(spec=discord.TextChannel)
        channel.name = "general"
        channel.history.return_value = _fake_history(messages)

        session = AsyncMock()
        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        await backfill_channel(session_factory, channel)

        # 1 for channel upsert + 2 batch commits (at 500, 1000) + 1 final = 4
        assert session.commit.call_count == 4

    @pytest.mark.asyncio
    @patch("scripts.backfill.insert_message", new_callable=AsyncMock)
    @patch("scripts.backfill.upsert_member", new_callable=AsyncMock)
    @patch("scripts.backfill.upsert_channel", new_callable=AsyncMock)
    async def test_skips_bot_messages(
        self, mock_upsert_ch, mock_upsert_mem, mock_insert_msg
    ):
        messages = [
            _make_message(message_id=1, author_bot=False),
            _make_message(message_id=2, author_bot=True),
            _make_message(message_id=3, author_bot=False),
        ]
        channel = MagicMock(spec=discord.TextChannel)
        channel.name = "general"
        channel.history.return_value = _fake_history(messages)

        session = AsyncMock()
        session_factory = MagicMock()
        session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
        session_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        count = await backfill_channel(session_factory, channel)
        assert count == 2
        assert mock_insert_msg.call_count == 2
