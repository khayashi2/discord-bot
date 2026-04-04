"""Analytics queries for the Discord dashboard.

Each function takes an AsyncSession and returns plain dicts/lists
ready for JSON serialization in Jinja2 templates.
"""

import re
from collections import Counter
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
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

# Pattern to strip URLs before word extraction
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

# File extensions and domain suffixes to filter from word counts
FILTERED_WORDS = frozenset(
    "txt gif jpg jpeg png mp4 mp3 pdf doc docx zip rar webp webm mov avi wav "
    "com org net edu gov io dev co uk us ca http https www".split()
)


def _clean_content(text: str) -> str:
    """Strip URLs from text before word extraction."""
    return URL_PATTERN.sub("", text)


def _is_filtered_word(word: str) -> bool:
    """Check if a word should be excluded from analytics."""
    return word in STOPWORDS or word in FILTERED_WORDS


def cutoff_from_range(range_key: str | None) -> datetime | None:
    """Convert a range key like '7d', '30d', '90d' to a cutoff datetime."""
    if not range_key:
        return None
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(range_key)
    if days is None:
        return None
    return datetime.now(UTC) - timedelta(days=days)


async def get_overview(session: AsyncSession, after: datetime | None = None) -> dict:
    """Return high-level server stats in a single query."""
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    msg_filter = select(func.count()).select_from(Message)
    if after:
        msg_filter = msg_filter.where(Message.created_at >= after)
    total_msgs = msg_filter.scalar_subquery().label("total_messages")

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

    today_cutoff = after if (after and after > today_start) else today_start
    today_filter = (
        select(func.count())
        .select_from(Message)
        .where(Message.created_at >= today_cutoff)
    )
    msgs_today = today_filter.scalar_subquery().label("messages_today")

    stmt = select(total_msgs, total_members, total_channels, msgs_today)
    row = (await session.execute(stmt)).one()

    return {
        "total_messages": row.total_messages or 0,
        "total_members": row.total_members or 0,
        "total_channels": row.total_channels or 0,
        "messages_today": row.messages_today or 0,
    }


async def get_top_users(
    session: AsyncSession, limit: int = 10, after: datetime | None = None
) -> list[dict]:
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
    )
    if after:
        stmt = stmt.where(Message.created_at >= after)
    stmt = (
        stmt
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


async def get_top_channels(
    session: AsyncSession, limit: int = 10, after: datetime | None = None
) -> list[dict]:
    """Return the most active channels by message count."""
    stmt = select(Channel.name, func.count().label("count")).join(
        Message, Message.channel_id == Channel.id
    )
    if after:
        stmt = stmt.where(Message.created_at >= after)
    stmt = (
        stmt.group_by(Channel.id).order_by(literal_column("count").desc()).limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [{"name": r.name, "count": r.count} for r in rows]


async def get_activity_over_time(
    session: AsyncSession, days: int = 30, after: datetime | None = None
) -> list[dict]:
    """Return daily message counts for the last N days, including zero-activity days."""
    now = datetime.now(UTC)
    cutoff = after if after else now - timedelta(days=days)
    day_col = func.date_trunc("day", Message.created_at).label("day")
    stmt = (
        select(day_col, func.count().label("count"))
        .where(Message.created_at >= cutoff)
        .group_by(day_col)
        .order_by(day_col)
    )
    range_days = (now - cutoff).days
    rows = (await session.execute(stmt)).all()

    # Build a lookup and fill in days with zero messages
    counts_by_day = {r.day.strftime("%Y-%m-%d"): r.count for r in rows}
    result = []
    for i in range(range_days + 1):
        day_str = (cutoff + timedelta(days=i)).strftime("%Y-%m-%d")
        result.append({"day": day_str, "count": counts_by_day.get(day_str, 0)})
    return result


async def get_top_words(
    session: AsyncSession, limit: int = 20, after: datetime | None = None
) -> list[dict]:
    """Return the most frequently used words across recent messages.

    NOTE: Word counting is done in Python over the 5,000 most recent messages.
    At high volume, consider moving this to a materialized view or PostgreSQL
    full-text search aggregation.
    """
    stmt = select(Message.content).where(Message.content.isnot(None))
    if after:
        stmt = stmt.where(Message.created_at >= after)
    stmt = stmt.order_by(Message.created_at.desc()).limit(5000)
    rows = (await session.execute(stmt)).scalars().all()

    counter: Counter[str] = Counter()
    for content in rows:
        cleaned = _clean_content(content.lower())
        words = WORD_PATTERN.findall(cleaned)
        counter.update(w for w in words if not _is_filtered_word(w))

    return [
        {"word": word, "count": count} for word, count in counter.most_common(limit)
    ]


async def get_emoji_stats(session: AsyncSession, after: datetime | None = None) -> dict:
    """Return emoji usage statistics."""
    total_q = select(func.coalesce(func.sum(Message.emoji_count), 0))
    count_q = select(func.count()).select_from(Message).where(Message.emoji_count > 0)
    if after:
        total_q = total_q.where(Message.created_at >= after)
        count_q = count_q.where(Message.created_at >= after)
    total_emoji = await session.scalar(total_q)
    msgs_with_emoji = await session.scalar(count_q)

    # Extract top individual emoji from recent messages.
    # NOTE: Emoji extraction is done in Python over 2,000 rows. At high
    # volume, consider caching or a materialized view.
    stmt = (
        select(Message.content)
        .where(Message.emoji_count > 0)
        .order_by(Message.created_at.desc())
    )
    if after:
        stmt = stmt.where(Message.created_at >= after)
    stmt = stmt.limit(2000)
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


async def get_message_length_stats(
    session: AsyncSession, after: datetime | None = None
) -> dict:
    """Return message length distribution stats."""
    base = select(func.count()).select_from(Message)
    avg_q = select(func.coalesce(func.avg(Message.content_length), 0))
    max_q = select(func.coalesce(func.max(Message.content_length), 0))
    if after:
        base = base.where(Message.created_at >= after)
        avg_q = avg_q.where(Message.created_at >= after)
        max_q = max_q.where(Message.created_at >= after)

    avg_length = await session.scalar(avg_q)
    max_length = await session.scalar(max_q)

    short_q = base.where(Message.content_length < 50)
    medium_q = base.where(Message.content_length.between(50, 200))
    long_q = base.where(Message.content_length > 200)
    short = await session.scalar(short_q)
    medium = await session.scalar(medium_q)
    long_ = await session.scalar(long_q)

    return {
        "avg_length": round(float(avg_length or 0)),
        "max_length": max_length or 0,
        "short": short or 0,
        "medium": medium or 0,
        "long": long_ or 0,
    }


async def get_all_members(session: AsyncSession) -> list[dict]:
    """Return all non-bot members sorted by display name."""
    stmt = (
        select(Member.id, Member.username, Member.display_name, Member.avatar_url)
        .where(Member.is_bot.is_(False))
        .order_by(func.coalesce(Member.display_name, Member.username))
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "id": r.id,
            "username": r.username,
            "display_name": r.display_name or r.username,
            "avatar_url": r.avatar_url,
        }
        for r in rows
    ]


async def get_user_top_words(
    session: AsyncSession, member_id: int, limit: int = 10
) -> list[dict]:
    """Return the most frequently used words for a specific user."""
    stmt = (
        select(Message.content)
        .where(Message.author_id == member_id, Message.content.isnot(None))
        .order_by(Message.created_at.desc())
        .limit(5000)  # Cap to bound memory usage on large histories
    )
    rows = (await session.execute(stmt)).scalars().all()

    counter: Counter[str] = Counter()
    for content in rows:
        cleaned = _clean_content(content.lower())
        words = WORD_PATTERN.findall(cleaned)
        counter.update(w for w in words if not _is_filtered_word(w))

    return [
        {"word": word, "count": count} for word, count in counter.most_common(limit)
    ]


async def get_user_top_emoji(
    session: AsyncSession, member_id: int, limit: int = 3
) -> list[dict]:
    """Return the most used emoji for a specific user."""
    stmt = (
        select(Message.content)
        .where(
            Message.author_id == member_id,
            Message.emoji_count > 0,
            Message.content.isnot(None),
        )
        .order_by(Message.created_at.desc())
        .limit(2000)  # Cap to bound memory usage on large histories
    )
    rows = (await session.execute(stmt)).scalars().all()

    emoji_counter: Counter[str] = Counter()
    for content in rows:
        emoji_counter.update(EMOJI_PATTERN.findall(content))

    return [
        {"emoji": emoji, "count": count}
        for emoji, count in emoji_counter.most_common(limit)
    ]


async def get_user_message_count(session: AsyncSession, member_id: int) -> int:
    """Return the total message count for a specific user."""
    result = await session.scalar(
        select(func.count()).select_from(Message).where(Message.author_id == member_id)
    )
    return result or 0


async def get_profanity_leaderboard(
    session: AsyncSession, limit: int = 10, after: datetime | None = None
) -> list[dict]:
    """Return the top users by profanity usage in recent messages."""

    profanity_words = settings.load_profanity_words()
    if not profanity_words:
        return []

    stmt = (
        select(Message.author_id, Message.content)
        .join(Member, Message.author_id == Member.id)
        .where(Member.is_bot.is_(False), Message.content.isnot(None))
    )
    if after:
        stmt = stmt.where(Message.created_at >= after)
    stmt = stmt.order_by(Message.created_at.desc()).limit(10000)
    rows = (await session.execute(stmt)).all()

    counter: Counter[int] = Counter()
    for row in rows:
        cleaned = _clean_content(row.content.lower())
        words = WORD_PATTERN.findall(cleaned)
        count = sum(1 for w in words if w in profanity_words)
        if count:
            counter[row.author_id] += count

    if not counter:
        return []

    # Fetch display names for the top offenders
    top_ids = [author_id for author_id, _ in counter.most_common(limit)]
    member_stmt = select(
        Member.id, Member.display_name, Member.username, Member.avatar_url
    ).where(Member.id.in_(top_ids))
    member_rows = (await session.execute(member_stmt)).all()
    member_map = {
        r.id: {"display_name": r.display_name or r.username, "avatar_url": r.avatar_url}
        for r in member_rows
    }

    return [
        {
            "display_name": member_map[author_id]["display_name"],
            "avatar_url": member_map[author_id]["avatar_url"],
            "count": count,
        }
        for author_id, count in counter.most_common(limit)
        if author_id in member_map
    ]


async def get_user_activity_over_time(
    session: AsyncSession, member_id: int, days: int = 30
) -> list[dict]:
    """Return daily message counts for a specific user over the last N days."""
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=days)
    day_col = func.date_trunc("day", Message.created_at).label("day")
    stmt = (
        select(day_col, func.count().label("count"))
        .where(Message.author_id == member_id, Message.created_at >= cutoff)
        .group_by(day_col)
        .order_by(day_col)
    )
    rows = (await session.execute(stmt)).all()

    counts_by_day = {r.day.strftime("%Y-%m-%d"): r.count for r in rows}
    result = []
    for i in range(days + 1):
        day_str = (cutoff + timedelta(days=i)).strftime("%Y-%m-%d")
        result.append({"day": day_str, "count": counts_by_day.get(day_str, 0)})
    return result


async def get_user_top_channels(
    session: AsyncSession, member_id: int, limit: int = 10
) -> list[dict]:
    """Return the channels where a specific user posts most."""
    stmt = (
        select(Channel.name, func.count().label("count"))
        .join(Message, Message.channel_id == Channel.id)
        .where(Message.author_id == member_id)
        .group_by(Channel.id)
        .order_by(literal_column("count").desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [{"name": r.name, "count": r.count} for r in rows]


async def get_user_message_length_distribution(
    session: AsyncSession, member_id: int
) -> dict:
    """Return message length distribution for a specific user."""
    base = (
        select(func.count()).select_from(Message).where(Message.author_id == member_id)
    )
    avg_length = await session.scalar(
        select(func.coalesce(func.avg(Message.content_length), 0)).where(
            Message.author_id == member_id
        )
    )
    short = await session.scalar(base.where(Message.content_length < 50))
    medium = await session.scalar(base.where(Message.content_length.between(50, 200)))
    long_ = await session.scalar(base.where(Message.content_length > 200))

    return {
        "avg_length": round(float(avg_length or 0)),
        "short": short or 0,
        "medium": medium or 0,
        "long": long_ or 0,
    }


async def get_user_emoji_stats(session: AsyncSession, member_id: int) -> dict:
    """Return emoji usage statistics for a specific user."""
    total_emoji = await session.scalar(
        select(func.coalesce(func.sum(Message.emoji_count), 0)).where(
            Message.author_id == member_id
        )
    )
    msgs_with_emoji = await session.scalar(
        select(func.count())
        .select_from(Message)
        .where(Message.author_id == member_id, Message.emoji_count > 0)
    )

    stmt = (
        select(Message.content)
        .where(
            Message.author_id == member_id,
            Message.emoji_count > 0,
            Message.content.isnot(None),
        )
        .order_by(Message.created_at.desc())
        .limit(2000)
    )
    rows = (await session.execute(stmt)).scalars().all()

    emoji_counter: Counter[str] = Counter()
    for content in rows:
        emoji_counter.update(EMOJI_PATTERN.findall(content))

    return {
        "total_emoji": total_emoji or 0,
        "msgs_with_emoji": msgs_with_emoji or 0,
        "top_emoji": [
            {"emoji": emoji, "count": count}
            for emoji, count in emoji_counter.most_common(10)
        ],
    }
