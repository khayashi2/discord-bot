"""FastAPI dashboard entry point."""

import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import settings
from dashboard.queries import (
    get_activity_over_time,
    get_emoji_stats,
    get_message_length_stats,
    get_overview,
    get_top_channels,
    get_top_users,
    get_top_words,
)
from db.database import async_session

_BASE = Path(__file__).parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Discord Analytics Dashboard")

app.mount("/static", StaticFiles(directory=str(_BASE / "static")), name="static")
templates = Jinja2Templates(directory=str(_BASE / "templates"))


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
    "msg_length": {
        "avg_length": 0,
        "max_length": 0,
        "short": 0,
        "medium": 0,
        "long": 0,
    },
}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render the main dashboard page with analytics data."""
    try:
        async with async_session() as session:
            context = {
                "overview": await get_overview(session),
                "top_users": await get_top_users(session),
                "top_channels": await get_top_channels(session),
                "activity": await get_activity_over_time(session),
                "top_words": await get_top_words(session),
                "emoji": await get_emoji_stats(session),
                "msg_length": await get_message_length_stats(session),
            }
    except Exception:
        logger.exception("Failed to load dashboard data")
        context = dict(_EMPTY_CONTEXT)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "Discord Analytics", **context},
    )


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
