"""FastAPI dashboard entry point."""

import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select

from config import settings
from dashboard.queries import (
    cutoff_from_range,
    get_activity_heatmap,
    get_activity_over_time,
    get_all_members,
    get_awards,
    get_brainrot_leaderboard,
    get_brainrot_trend,
    get_catchphrase_lifespans,
    get_channel_activity,
    get_conversation_flow,
    get_digest,
    get_emoji_stats,
    get_overview,
    get_peak_hours,
    get_profanity_leaderboard,
    get_reaction_time_kings,
    get_sentiment_trend,
    get_top_brainrot_terms,
    get_top_users,
    get_top_words,
    get_unique_users_over_time,
    get_user_activity_over_time,
    get_user_brainrot_stats,
    get_user_catchphrase_lifespans,
    get_user_emoji_stats,
    get_user_message_count,
    get_user_peak_hours,
    get_user_top_profanity_words,
    get_user_top_words,
    get_user_vocabulary_diversity,
    get_vocabulary_diversity,
    get_word_cloud_data,
)
from db.database import async_session
from db.models import Member

_BASE = Path(__file__).parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Discord Analytics Dashboard")

app.mount("/static", StaticFiles(directory=str(_BASE / "static")), name="static")
templates = Jinja2Templates(directory=str(_BASE / "templates"))

_VALID_RANGES = {"7d", "30d", "90d"}

_EMPTY_CONTEXT = {
    "overview": {
        "total_messages": 0,
        "total_members": 0,
        "total_channels": 0,
        "messages_today": 0,
    },
    "top_users": [],
    "activity": [],
    "top_words": [],
    "emoji": {"total_emoji": 0, "msgs_with_emoji": 0, "top_emoji": []},
    "profanity": [],
    "heatmap": [],
    "awards": [],
    "vocabulary": [],
    "conversation_flow": [],
    "peak_hours": [],
    "reaction_time": [],
    "channel_activity": [],
    "digest": {
        "today_msgs": 0,
        "yesterday_msgs": 0,
        "msg_delta_pct": 0,
        "today_users": 0,
        "yesterday_users": 0,
        "user_delta_pct": 0,
        "week_msgs": 0,
        "last_week_msgs": 0,
        "week_msg_delta_pct": 0,
        "week_users": 0,
        "last_week_users": 0,
        "week_user_delta_pct": 0,
    },
    "growth": [],
    "word_cloud": [],
    "sentiment": [],
    "catchphrases": {"phrases": [], "timelines": {}},
    "brainrot": [],
    "brainrot_terms": [],
    "brainrot_trend": [],
}


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request, range: str = Query(default=None, alias="range")
) -> HTMLResponse:
    """Render the main dashboard page with analytics data."""
    active_range = range if range in _VALID_RANGES else None
    after = cutoff_from_range(active_range)
    try:
        async with async_session() as session:
            context = {
                "overview": await get_overview(session, after=after),
                "top_users": await get_top_users(session, after=after),
                "activity": await get_activity_over_time(session, after=after),
                "top_words": await get_top_words(session, after=after),
                "emoji": await get_emoji_stats(session, after=after),
                "profanity": await get_profanity_leaderboard(session, after=after),
                "heatmap": await get_activity_heatmap(session, after=after),
                "awards": await get_awards(session, after=after),
                "vocabulary": await get_vocabulary_diversity(session, after=after),
                "conversation_flow": await get_conversation_flow(session, after=after),
                "peak_hours": await get_peak_hours(session, after=after),
                "reaction_time": await get_reaction_time_kings(session, after=after),
                "channel_activity": await get_channel_activity(session, after=after),
                "digest": await get_digest(session),
                "growth": await get_unique_users_over_time(session, after=after),
                "word_cloud": await get_word_cloud_data(session, after=after),
                "sentiment": await get_sentiment_trend(session, after=after),
                "catchphrases": await get_catchphrase_lifespans(session, after=after),
                "brainrot": await get_brainrot_leaderboard(session, after=after),
                "brainrot_terms": await get_top_brainrot_terms(session, after=after),
                "brainrot_trend": await get_brainrot_trend(session, after=after),
            }
    except Exception:
        logger.exception("Failed to load dashboard data")
        context = dict(_EMPTY_CONTEXT)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "Discord Analytics",
            "active_range": active_range,
            "profanity_words_list": sorted(settings.load_profanity_words()),
            **context,
        },
    )


@app.get("/user", response_class=HTMLResponse)
async def user_page(request: Request) -> HTMLResponse:
    """Render the user stats page with a member dropdown."""
    try:
        async with async_session() as session:
            members = await get_all_members(session)
    except Exception:
        logger.exception("Failed to load user page data")
        members = []

    return templates.TemplateResponse(
        request=request,
        name="user.html",
        context={"title": "User Stats", "members": members},
    )


@app.get("/api/user/{member_id}")
async def user_stats_api(
    member_id: int, range: str | None = Query(default=None)
) -> dict:
    """Return per-user analytics as JSON."""
    async with async_session() as session:
        exists = await session.scalar(
            select(func.count()).select_from(Member).where(Member.id == member_id)
        )
        if not exists:
            raise HTTPException(status_code=404, detail="Member not found")

        active_range = range if range in _VALID_RANGES else None
        after = cutoff_from_range(active_range)

        try:
            return {
                "top_words": await get_user_top_words(session, member_id, after=after),
                "message_count": await get_user_message_count(
                    session, member_id, after=after
                ),
                "activity": await get_user_activity_over_time(
                    session, member_id, after=after
                ),
                "emoji_stats": await get_user_emoji_stats(
                    session, member_id, after=after
                ),
                "profanity_words": await get_user_top_profanity_words(
                    session, member_id, after=after
                ),
                "peak_hours": await get_user_peak_hours(
                    session, member_id, after=after
                ),
                "vocabulary": await get_user_vocabulary_diversity(
                    session, member_id, after=after
                ),
                "catchphrases": await get_user_catchphrase_lifespans(
                    session, member_id, after=after
                ),
                "brainrot_stats": await get_user_brainrot_stats(
                    session, member_id, after=after
                ),
            }
        except Exception:
            logger.exception("Failed to load user stats for member %d", member_id)
            return {
                "top_words": [],
                "message_count": 0,
                "activity": [],
                "profanity_words": [],
                "emoji_stats": {
                    "total_emoji": 0,
                    "msgs_with_emoji": 0,
                    "top_emoji": [],
                },
                "peak_hours": [],
                "vocabulary": {"ttr": 0, "unique_words": 0, "total_words": 0},
                "catchphrases": {"phrases": [], "timelines": {}},
                "brainrot_stats": {
                    "top_terms": [],
                    "repeated_msg_count": 0,
                    "total_keyword_hits": 0,
                },
            }


@app.get("/health")
async def health() -> dict:
    """Health check endpoint for monitoring."""
    return {"status": "ok"}


def main() -> None:
    """Start the dashboard server."""
    logger.info(
        "Starting dashboard on %s:%s", settings.DASHBOARD_HOST, settings.DASHBOARD_PORT
    )
    uvicorn.run(
        "dashboard.app:app",
        host=settings.DASHBOARD_HOST,
        port=settings.DASHBOARD_PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()
