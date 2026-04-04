"""Historical message backfill script.

Fetches all messages from a Discord guild's text channels and inserts
them into the database. Designed to be run once (or idempotently re-run)
to populate the analytics database with historical data.
"""

import asyncio
import logging

import discord

from config import settings
from db.database import async_session
from db.operations import insert_message, upsert_channel, upsert_member

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 500


async def backfill_channel(session_factory, channel: discord.TextChannel) -> int:
    """Fetch and persist all messages from a single channel.

    Returns the number of messages processed.
    """
    count = 0
    async with session_factory() as session:
        await upsert_channel(session, channel)
        await session.commit()

        async for message in channel.history(limit=None, oldest_first=True):
            if message.author.bot:
                continue

            await upsert_member(session, message.author)
            await insert_message(session, message)
            count += 1

            if count % BATCH_SIZE == 0:
                await session.commit()
                logger.info("  ... #%s: %d messages so far", channel.name, count)

        await session.commit()

    logger.info("Completed #%s: %d messages", channel.name, count)
    return count


async def main() -> None:
    """Run the historical backfill."""
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        try:
            guild = client.get_guild(settings.DISCORD_GUILD_ID)
            if guild is None:
                logger.error(
                    "Guild %s not found. Check DISCORD_GUILD_ID.",
                    settings.DISCORD_GUILD_ID,
                )
                return

            text_channels = [
                ch
                for ch in guild.text_channels
                if ch.permissions_for(guild.me).read_message_history
            ]
            logger.info(
                "Starting backfill for guild '%s' (%d text channels)",
                guild.name,
                len(text_channels),
            )

            total = 0
            for channel in text_channels:
                try:
                    count = await backfill_channel(async_session, channel)
                    total += count
                except discord.Forbidden:
                    logger.warning("Skipping #%s: missing permissions", channel.name)
                except discord.HTTPException as exc:
                    logger.warning("Skipping #%s: HTTP error: %s", channel.name, exc)
                except Exception:
                    logger.exception("Unexpected error in #%s, skipping", channel.name)

            logger.info("Backfill complete. Total messages ingested: %d", total)
        finally:
            await client.close()

    await client.start(settings.DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
