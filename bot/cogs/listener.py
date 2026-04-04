"""Cog that listens to messages and persists them to the database."""

import logging
import re

import discord
from discord.ext import commands
from sqlalchemy.dialects.postgresql import insert as pg_insert

from db.database import async_session
from db.models import Channel, Member, Message

logger = logging.getLogger(__name__)

EMOJI_PATTERN = re.compile(
    r"<a?:\w+:\d+>|[\U0001f600-\U0001f64f"
    r"\U0001f300-\U0001f5ff\U0001f680-\U0001f6ff"
    r"\U0001f1e0-\U0001f1ff\U00002702-\U000027b0"
    r"\U0000fe00-\U0000fe0f\U0001f900-\U0001f9ff"
    r"\U0001fa00-\U0001fa6f\U0001fa70-\U0001faff"
    r"\U00002600-\U000026ff]+"
)


class Listener(commands.Cog):
    """Listens for new messages and stores them in the database."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Persist every non-DM message to the database."""
        if message.guild is None:
            return
        if message.author.bot:
            return

        async with async_session() as session:
            await self._upsert_channel(session, message.channel)
            await self._upsert_member(session, message.author)
            await self._insert_message(session, message)
            await session.commit()

    async def _upsert_channel(self, session, channel: discord.abc.GuildChannel) -> None:
        stmt = (
            pg_insert(Channel)
            .values(
                id=channel.id,
                name=channel.name,
                type=str(channel.type),
                created_at=channel.created_at,
            )
            .on_conflict_do_update(
                index_elements=[Channel.id],
                set_=dict(name=channel.name, type=str(channel.type)),
            )
        )
        await session.execute(stmt)

    async def _upsert_member(
        self, session, author: discord.Member | discord.User
    ) -> None:
        member = author if isinstance(author, discord.Member) else None
        stmt = (
            pg_insert(Member)
            .values(
                id=author.id,
                username=author.name,
                display_name=author.display_name,
                avatar_url=str(author.avatar.url) if author.avatar else None,
                is_bot=author.bot,
                joined_at=member.joined_at if member else None,
            )
            .on_conflict_do_update(
                index_elements=[Member.id],
                set_=dict(
                    username=author.name,
                    display_name=author.display_name,
                    avatar_url=str(author.avatar.url) if author.avatar else None,
                ),
            )
        )
        await session.execute(stmt)

    async def _insert_message(self, session, message: discord.Message) -> None:
        content = message.content or ""
        emoji_count = len(EMOJI_PATTERN.findall(content))
        stmt = (
            pg_insert(Message)
            .values(
                id=message.id,
                channel_id=message.channel.id,
                author_id=message.author.id,
                content=content,
                content_length=len(content),
                has_attachments=len(message.attachments) > 0,
                has_embeds=len(message.embeds) > 0,
                emoji_count=emoji_count,
                created_at=message.created_at,
                edited_at=message.edited_at,
            )
            .on_conflict_do_nothing()
        )
        await session.execute(stmt)
        logger.debug("Stored message %s from %s", message.id, message.author)


async def setup(bot: commands.Bot) -> None:
    """Register the Listener cog with the bot."""
    await bot.add_cog(Listener(bot))
