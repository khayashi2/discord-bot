"""Discord bot entry point."""

import asyncio
import logging

import discord
from discord.ext import commands

from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


EXTENSIONS = [
    "bot.cogs.listener",
]


@bot.event
async def on_ready() -> None:
    """Log when the bot is connected and ready."""
    logger.info("Bot is online as %s (ID: %s)", bot.user, bot.user.id)
    logger.info("Connected to %d guild(s)", len(bot.guilds))


async def load_extensions() -> None:
    """Load all bot extensions/cogs."""
    for ext in EXTENSIONS:
        await bot.load_extension(ext)
        logger.info("Loaded extension: %s", ext)


def main() -> None:
    """Start the Discord bot."""
    if not settings.DISCORD_TOKEN:
        raise RuntimeError(
            "DISCORD_TOKEN is not set. Copy .env.example to .env and fill it in."
        )

    async def runner() -> None:
        async with bot:
            await load_extensions()
            await bot.start(settings.DISCORD_TOKEN)

    asyncio.run(runner())


if __name__ == "__main__":
    main()
