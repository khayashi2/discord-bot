"""Historical message backfill script.

Fetches all messages from a Discord guild's text channels and inserts
them into the database. Designed to be run once (or idempotently re-run)
to populate the analytics database with historical data.
"""

import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Run the historical backfill."""
    logger.info("Backfill script initialized.")
    logger.info(
        "This is a placeholder. Full implementation will be added in Phase 3 "
        "(feature/historical-backfill)."
    )
    # TODO: Connect to Discord API, iterate channels, fetch history, upsert to DB


if __name__ == "__main__":
    asyncio.run(main())
