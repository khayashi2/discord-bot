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
    get_activity_over_time,
    get_all_members,
    get_emoji_stats,
    get_message_length_stats,
    get_overview,
    get_profanity_leaderboard,
    get_top_channels,
    get_top_users,
    get_top_words,
    get_user_activity_over_time,
    get_user_emoji_stats,
    get_user_message_count,
    get_user_message_length_distribution,
    get_user_top_channels,
    get_user_top_words,
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
    "top_channels": [],
    "activity": [],
    "top_words": [],
    "emoji": {"total_emoji": 0, "msgs_with_emoji": 0, "top_emoji": []},
    "profanity": [],
    "message_lengths": {
        "avg_length": 0,
        "max_length": 0,
        "short": 0,
        "medium": 0,
        "long": 0,
    },
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
                "top_channels": await get_top_channels(session, after=after),
                "activity": await get_activity_over_time(session, after=after),
                "top_words": await get_top_words(session, after=after),
                "emoji": await get_emoji_stats(session, after=after),
                "profanity": await get_profanity_leaderboard(session, after=after),
                "message_lengths": await get_message_length_stats(session, after=after),
            }
    except Exception:
        logger.exception("Failed to load dashboard data")
        context = dict(_EMPTY_CONTEXT)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Discord Analytics", "active_range": active_range, **context},
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
async def user_stats_api(member_id: int) -> dict:
    """Return per-user analytics as JSON."""
    async with async_session() as session:
        exists = await session.scalar(
            select(func.count()).select_from(Member).where(Member.id == member_id)
        )
        if not exists:
            raise HTTPException(status_code=404, detail="Member not found")

        try:
            return {
                "top_words": await get_user_top_words(session, member_id),
                "message_count": await get_user_message_count(session, member_id),
                "activity": await get_user_activity_over_time(session, member_id),
                "top_channels": await get_user_top_channels(session, member_id),
                "message_lengths": await get_user_message_length_distribution(
                    session, member_id
                ),
                "emoji_stats": await get_user_emoji_stats(session, member_id),
            }
        except Exception:
            logger.exception("Failed to load user stats for member %d", member_id)
            return {
                "top_words": [],
                "message_count": 0,
                "activity": [],
                "top_channels": [],
                "message_lengths": {
                    "avg_length": 0,
                    "short": 0,
                    "medium": 0,
                    "long": 0,
                },
                "emoji_stats": {
                    "total_emoji": 0,
                    "msgs_with_emoji": 0,
                    "top_emoji": [],
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
