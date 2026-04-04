"""Tests for shared database operations."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from db.operations import (
    EMOJI_PATTERN,
    count_emojis,
    insert_message,
    upsert_channel,
    upsert_member,
)


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


class TestCountEmojis:
    """Tests for the count_emojis helper."""

    def test_returns_count(self):
        assert count_emojis("<:ok:123> <:no:456>") == 2

    def test_empty_string(self):
        assert count_emojis("") == 0


def _make_channel(channel_id=10, name="general"):
    channel = MagicMock()
    channel.id = channel_id
    channel.name = name
    channel.type = "text"
    channel.created_at = datetime(2024, 1, 1, tzinfo=UTC)
    return channel


def _make_author(author_id=100, name="testuser", is_member=True):
    import discord

    author = MagicMock(spec=discord.Member if is_member else discord.User)
    author.id = author_id
    author.name = name
    author.display_name = name
    author.avatar = None
    author.bot = False
    if is_member:
        author.joined_at = datetime(2024, 6, 1, tzinfo=UTC)
    return author


def _make_message(content="hello world", message_id=1000):
    msg = MagicMock()
    msg.id = message_id
    msg.channel = _make_channel()
    msg.author = _make_author()
    msg.content = content
    msg.attachments = []
    msg.embeds = []
    msg.created_at = datetime(2025, 1, 15, tzinfo=UTC)
    msg.edited_at = None
    return msg


class TestUpsertChannel:
    @pytest.mark.asyncio
    async def test_executes_upsert(self):
        session = AsyncMock()
        channel = _make_channel()
        await upsert_channel(session, channel)
        session.execute.assert_called_once()


class TestUpsertMember:
    @pytest.mark.asyncio
    async def test_executes_upsert_for_member(self):
        session = AsyncMock()
        author = _make_author(is_member=True)
        await upsert_member(session, author)
        session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_executes_upsert_for_user(self):
        session = AsyncMock()
        author = _make_author(is_member=False)
        await upsert_member(session, author)
        session.execute.assert_called_once()


class TestInsertMessage:
    @pytest.mark.asyncio
    async def test_executes_insert(self):
        session = AsyncMock()
        msg = _make_message()
        await insert_message(session, msg)
        session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_none_content(self):
        session = AsyncMock()
        msg = _make_message()
        msg.content = None
        await insert_message(session, msg)
        session.execute.assert_called_once()
