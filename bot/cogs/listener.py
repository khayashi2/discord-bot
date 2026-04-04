"""Cog that listens to messages and persists them to the database."""

import logging

import discord
from discord.ext import commands

from db.database import async_session
from db.operations import insert_message, upsert_channel, upsert_member

logger = logging.getLogger(__name__)


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
            await upsert_channel(session, message.channel)
            await upsert_member(session, message.author)
            await insert_message(session, message)
            await session.commit()


async def setup(bot: commands.Bot) -> None:
    """Register the Listener cog with the bot."""
    await bot.add_cog(Listener(bot))
