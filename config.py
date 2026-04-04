"""Centralized configuration loaded from environment variables."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class Settings:
    """Application settings sourced from .env file."""

    # Discord
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    DISCORD_GUILD_ID: int = int(os.getenv("DISCORD_GUILD_ID", "0"))

    # Database
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "discord_bot")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "change_me")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "discord_analytics")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    @property
    def database_url(self) -> str:
        """Build the async database URL for SQLAlchemy."""
        return os.getenv(
            "DATABASE_URL",
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}",
        )

    @property
    def sync_database_url(self) -> str:
        """Build the sync database URL for Alembic migrations."""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Dashboard
    DASHBOARD_HOST: str = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    DASHBOARD_PORT: int = int(os.getenv("DASHBOARD_PORT", "8000"))
    DASHBOARD_SECRET_KEY: str = os.getenv("DASHBOARD_SECRET_KEY", "dev-secret-key")

    # Profanity
    _profanity_words: frozenset[str] | None = None

    @property
    def profanity_file(self) -> Path:
        """Path to the profanity word list file."""
        return Path(__file__).parent / "config" / "profanity.txt"

    def load_profanity_words(self) -> frozenset[str]:
        """Load profanity words from the config file.

        Results are cached after the first call.
        """
        if self._profanity_words is not None:
            return self._profanity_words

        path = self.profanity_file
        if not path.exists():
            logger.warning("Profanity file not found: %s", path)
            self._profanity_words = frozenset()
            return self._profanity_words

        words: set[str] = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                words.add(line.lower())

        self._profanity_words = frozenset(words)
        return self._profanity_words


settings = Settings()
