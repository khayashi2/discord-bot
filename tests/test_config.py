"""Tests for application configuration."""

import os


def test_settings_loads_defaults():
    """Settings should have sensible defaults when env vars are missing."""
    # Import inside test to avoid polluting other tests
    from config import Settings

    s = Settings()
    assert s.POSTGRES_USER == os.getenv("POSTGRES_USER", "discord_bot")
    assert s.POSTGRES_DB == os.getenv("POSTGRES_DB", "discord_analytics")
    assert isinstance(s.database_url, str)
    assert "postgresql" in s.database_url


def test_settings_database_url_format():
    """Database URL should contain all connection components."""
    from config import Settings

    s = Settings()
    url = s.database_url
    assert s.POSTGRES_USER in url
    assert s.POSTGRES_HOST in url
    assert s.POSTGRES_PORT in url
    assert s.POSTGRES_DB in url
