"""Analytics queries for the Discord dashboard.

Each function takes an AsyncSession and returns plain dicts/lists
ready for JSON serialization in Jinja2 templates.
"""

import re
from collections import Counter
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Channel, Member, Message

# Common English stopwords to filter from top-words results
STOPWORDS = frozenset(
    "the be to of and a in that have i it for not on with he as you do at "
    "this but his by from they we say her she or an will my one all would "
    "there their what so up out if about who get which go me when make can "
    "like time no just him know take people into year your good some could "
    "them see other than then now look only come its over think also back "
    "after use two how our work first well way even new want because any "
    "these give day most us is was are been has had did got would im dont "
    "thats really right yeah just like lol lmao".split()
)

EMOJI_PATTERN = re.compile(
    r"<a?:\w+:\d+>|[\U0001f600-\U0001f64f"
    r"\U0001f300-\U0001f5ff\U0001f680-\U0001f6ff"
    r"\U0001f1e0-\U0001f1ff\U00002702-\U000027b0"
    r"\U0000fe00-\U0000fe0f\U0001f900-\U0001f9ff"
    r"\U0001fa00-\U0001fa6f\U0001fa70-\U0001faff"
    r"\U00002600-\U000026ff]+"
)

WORD_PATTERN = re.compile(r"[a-zA-Z]{3,}")


async def get_overview(session: AsyncSession) -> dict:
    """Return high-level server stats in a single query."""
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    total_msgs = (
        select(func.count())
        .select_from(Message)
        .scalar_subquery()
        .label("total_messages")
    )
    total_members = (
        select(func.count())
        .select_from(Member)
        .where(Member.is_bot.is_(False))
        .scalar_subquery()
        .label("total_members")
    )
    total_channels = (
        select(func.count())
        .select_from(Channel)
        .scalar_subquery()
        .label("total_channels")
    )
    msgs_today = (
        select(func.count())
        .select_from(Message)
        .where(Message.created_at >= today_start)
        .scalar_subquery()
        .label("messages_today")
    )
    stmt = select(total_msgs, total_members, total_channels, msgs_today)
    row = (await session.execute(stmt)).one()

    return {
        "total_messages": row.total_messages or 0,
        "total_members": row.total_members or 0,
        "total_channels": row.total_channels or 0,
        "messages_today": row.messages_today or 0,
    }


async def get_top_users(session: AsyncSession, limit: int = 10) -> list[dict]:
    """Return the most active users by message count."""
    stmt = (
        select(
            Member.username,
            Member.display_name,
            Member.avatar_url,
            func.count().label("count"),
        )
        .join(Message, Message.author_id == Member.id)
        .where(Member.is_bot.is_(False))
        # GROUP BY primary key; other Member columns are functionally dependent
        .group_by(Member.id)
        .order_by(literal_column("count").desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "username": r.username,
            "display_name": r.display_name or r.username,
            "avatar_url": r.avatar_url,
            "count": r.count,
        }
        for r in rows
    ]


async def get_top_channels(session: AsyncSession, limit: int = 10) -> list[dict]:
    """Return the most active channels by message count."""
    stmt = (
        select(Channel.name, func.count().label("count"))
        .join(Message, Message.channel_id == Channel.id)
        .group_by(Channel.id)
        .order_by(literal_column("count").desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [{"name": r.name, "count": r.count} for r in rows]


async def get_activity_over_time(session: AsyncSession, days: int = 30) -> list[dict]:
    """Return daily message counts for the last N days, including zero-activity days."""
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=days)
    day_col = func.date_trunc("day", Message.created_at).label("day")
    stmt = (
        select(day_col, func.count().label("count"))
        .where(Message.created_at >= cutoff)
        .group_by(day_col)
        .order_by(day_col)
    )
    rows = (await session.execute(stmt)).all()

    # Build a lookup and fill in days with zero messages
    counts_by_day = {r.day.strftime("%Y-%m-%d"): r.count for r in rows}
    result = []
    for i in range(days):
        day_str = (cutoff + timedelta(days=i)).strftime("%Y-%m-%d")
        result.append({"day": day_str, "count": counts_by_day.get(day_str, 0)})
    return result


async def get_top_words(session: AsyncSession, limit: int = 20) -> list[dict]:
    """Return the most frequently used words across recent messages.

    NOTE: Word counting is done in Python over the 5,000 most recent messages.
    At high volume, consider moving this to a materialized view or PostgreSQL
    full-text search aggregation.
    """
    stmt = (
        select(Message.content)
        .where(Message.content.isnot(None))
        .order_by(Message.created_at.desc())
        .limit(5000)
    )
    rows = (await session.execute(stmt)).scalars().all()

    counter: Counter[str] = Counter()
    for content in rows:
        words = WORD_PATTERN.findall(content.lower())
        counter.update(w for w in words if w not in STOPWORDS)

    return [
        {"word": word, "count": count} for word, count in counter.most_common(limit)
    ]


async def get_emoji_stats(session: AsyncSession) -> dict:
    """Return emoji usage statistics."""
    total_emoji = await session.scalar(
        select(func.coalesce(func.sum(Message.emoji_count), 0))
    )
    msgs_with_emoji = await session.scalar(
        select(func.count()).select_from(Message).where(Message.emoji_count > 0)
    )

    # Extract top individual emoji from recent messages.
    # NOTE: Emoji extraction is done in Python over 2,000 rows. At high
    # volume, consider caching or a materialized view.
    stmt = (
        select(Message.content)
        .where(Message.emoji_count > 0)
        .order_by(Message.created_at.desc())
        .limit(2000)
    )
    rows = (await session.execute(stmt)).scalars().all()

    emoji_counter: Counter[str] = Counter()
    for content in rows:
        emoji_counter.update(EMOJI_PATTERN.findall(content))

    top_emoji = [
        {"emoji": emoji, "count": count}
        for emoji, count in emoji_counter.most_common(10)
    ]

    return {
        "total_emoji": total_emoji or 0,
        "msgs_with_emoji": msgs_with_emoji or 0,
        "top_emoji": top_emoji,
    }


async def get_message_length_stats(session: AsyncSession) -> dict:
    """Return message length distribution stats."""
    avg_length = await session.scalar(
        select(func.coalesce(func.avg(Message.content_length), 0))
    )
    max_length = await session.scalar(
        select(func.coalesce(func.max(Message.content_length), 0))
    )

    short = await session.scalar(
        select(func.count()).select_from(Message).where(Message.content_length < 50)
    )
    medium = await session.scalar(
        select(func.count())
        .select_from(Message)
        .where(Message.content_length.between(50, 200))
    )
    long_ = await session.scalar(
        select(func.count()).select_from(Message).where(Message.content_length > 200)
    )

    return {
        "avg_length": round(float(avg_length or 0)),
        "max_length": max_length or 0,
        "short": short or 0,
        "medium": medium or 0,
        "long": long_ or 0,
    }
