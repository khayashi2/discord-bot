"""FastAPI dashboard entry point."""

import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Discord Analytics Dashboard")

app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")
templates = Jinja2Templates(directory="dashboard/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Render the main dashboard page."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Discord Analytics"},
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
