"""Tests for the message listener cog."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.cogs.listener import EMOJI_PATTERN, Listener


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


class TestEmojiPattern:
    """Tests for the emoji counting regex."""

    def test_counts_unicode_emoji(self):
        assert len(EMOJI_PATTERN.findall("hello 😀😂")) == 1  # group match

    def test_counts_custom_discord_emoji(self):
        text = "nice <:thumbsup:123456789> and <a:party:987654321>"
        matches = EMOJI_PATTERN.findall(text)
        assert len(matches) == 2

    def test_no_emoji(self):
        assert len(EMOJI_PATTERN.findall("just plain text")) == 0


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

        cog._upsert_channel = AsyncMock()
        cog._upsert_member = AsyncMock()
        cog._insert_message = AsyncMock()

        mock_session = AsyncMock()

        with patch("bot.cogs.listener.async_session") as mock_factory:
            mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

            await cog.on_message(message)

            cog._upsert_channel.assert_called_once()
            cog._upsert_member.assert_called_once()
            cog._insert_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_adds_cog(self):
        """The setup function should register the cog on the bot."""
        from bot.cogs.listener import setup

        bot = AsyncMock()
        await setup(bot)
        bot.add_cog.assert_called_once()
