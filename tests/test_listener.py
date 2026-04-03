"""Tests for the message listener cog."""

import re
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.cogs.listener import EMOJI_PATTERN, Listener


def _make_message(
    *,
    guild_id=1,
    guild_name="Test Guild",
    channel_id=10,
    channel_name="general",
    author_id=100,
    author_name="testuser",
    content="hello world",
    message_id=1000,
    is_bot=False,
):
    """Build a fake discord.Message with nested guild/channel/author."""
    guild = MagicMock()
    guild.id = guild_id
    guild.name = guild_name
    guild.icon = None
    guild.member_count = 5
    guild.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

    channel = MagicMock()
    channel.id = channel_id
    channel.name = channel_name
    channel.guild = guild
    channel.type = "text"
    channel.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

    author = MagicMock()
    author.id = author_id
    author.name = author_name
    author.display_name = author_name
    author.avatar = None
    author.bot = is_bot
    author.joined_at = datetime(2024, 6, 1, tzinfo=timezone.utc)

    message = MagicMock()
    message.id = message_id
    message.guild = guild
    message.channel = channel
    message.author = author
    message.content = content
    message.attachments = []
    message.embeds = []
    message.created_at = datetime(2025, 1, 15, tzinfo=timezone.utc)
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
    async def test_persists_guild_message(self):
        """A normal guild message should trigger DB upserts."""
        bot = MagicMock()
        cog = Listener(bot)
        message = _make_message()

        mock_session_instance = AsyncMock()
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_begin = AsyncMock()
        mock_begin.__aenter__ = AsyncMock(return_value=None)
        mock_begin.__aexit__ = AsyncMock(return_value=False)
        mock_session_instance.begin.return_value = mock_begin

        with patch("bot.cogs.listener.async_session") as mock_session_factory:
            mock_session_factory.return_value = mock_ctx
            # Patch the upsert methods to verify they are called
            cog._upsert_guild = AsyncMock()
            cog._upsert_channel = AsyncMock()
            cog._upsert_member = AsyncMock()
            cog._insert_message = AsyncMock()

            await cog.on_message(message)

            cog._upsert_guild.assert_called_once()
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
