"""Tests for the message listener cog."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.cogs.listener import Listener


def _make_message(
    *,
    channel_id=10,
    channel_name="general",
    author_id=100,
    author_name="testuser",
    content="hello world",
    message_id=1000,
    is_bot=False,
):
    """Build a fake discord.Message with nested channel/author."""
    channel = MagicMock()
    channel.id = channel_id
    channel.name = channel_name
    channel.type = "text"
    channel.created_at = datetime(2024, 1, 1, tzinfo=UTC)

    author = MagicMock()
    author.id = author_id
    author.name = author_name
    author.display_name = author_name
    author.avatar = None
    author.bot = is_bot
    author.joined_at = datetime(2024, 6, 1, tzinfo=UTC)

    message = MagicMock()
    message.id = message_id
    message.guild = MagicMock()
    message.channel = channel
    message.author = author
    message.content = content
    message.attachments = []
    message.embeds = []
    message.created_at = datetime(2025, 1, 15, tzinfo=UTC)
    message.edited_at = None

    return message


class TestListenerCog:
    """Tests for the Listener cog message handling."""

    @pytest.mark.asyncio
    async def test_ignores_dm_messages(self):
        """Messages without a guild (DMs) should be skipped."""
        bot = MagicMock()
        cog = Listener(bot)
        message = MagicMock()
        message.guild = None

        with patch("bot.cogs.listener.async_session") as mock_session:
            await cog.on_message(message)
            mock_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_ignores_bot_messages(self):
        """Messages from bots should be skipped."""
        bot = MagicMock()
        cog = Listener(bot)
        message = _make_message(is_bot=True)
        message.author.bot = True

        with patch("bot.cogs.listener.async_session") as mock_session:
            await cog.on_message(message)
            mock_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_persists_guild_message(self):
        """A normal guild message should trigger DB upserts."""
        bot = MagicMock()
        cog = Listener(bot)
        message = _make_message()

        mock_session = AsyncMock()

        with (
            patch("bot.cogs.listener.async_session") as mock_factory,
            patch("bot.cogs.listener.upsert_channel") as mock_upsert_ch,
            patch("bot.cogs.listener.upsert_member") as mock_upsert_mem,
            patch("bot.cogs.listener.insert_message") as mock_insert_msg,
        ):
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

            await cog.on_message(message)

            mock_upsert_ch.assert_called_once_with(mock_session, message.channel)
            mock_upsert_mem.assert_called_once_with(mock_session, message.author)
            mock_insert_msg.assert_called_once_with(mock_session, message)

    @pytest.mark.asyncio
    async def test_setup_adds_cog(self):
        """The setup function should register the cog on the bot."""
        from bot.cogs.listener import setup

        bot = AsyncMock()
        await setup(bot)
        bot.add_cog.assert_called_once()
