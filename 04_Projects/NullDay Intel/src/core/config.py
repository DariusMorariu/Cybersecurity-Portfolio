"""Configuration and environment management for NullDay Intel."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Automatically load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
SOURCES_CONFIG_PATH = CONFIG_DIR / "sources.yaml"
DB_PATH = DATA_DIR / "intel_history.db"

# Mode-to-hours mapping (with small buffer to prevent gaps between runs)
TIME_WINDOWS_HOURS = {
    "daily": 26,      # 24h + 2h buffer
    "weekly": 170,    # 7d + 2h buffer
    "monthly": 722,   # 30d + 2h buffer
}


class Settings:
    """Application settings resolved from environment variables."""

    # Google GenAI Settings
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    # Discord Settings
    DISCORD_WEBHOOK_URL: Optional[str] = os.getenv("DISCORD_WEBHOOK_URL")

    # X (Twitter) Settings (OAuth 1.0a User Context)
    X_CONSUMER_KEY: Optional[str] = (
        os.getenv("X_CONSUMER_KEY")
        or os.getenv("X_API_KEY")
        or os.getenv("TWITTER_API_KEY")
        or os.getenv("TWITTER_CONSUMER_KEY")
    )
    X_CONSUMER_SECRET: Optional[str] = (
        os.getenv("X_CONSUMER_SECRET")
        or os.getenv("X_API_SECRET")
        or os.getenv("TWITTER_API_SECRET")
        or os.getenv("TWITTER_CONSUMER_SECRET")
    )
    X_ACCESS_TOKEN: Optional[str] = (
        os.getenv("X_ACCESS_TOKEN") or os.getenv("TWITTER_ACCESS_TOKEN")
    )
    X_ACCESS_TOKEN_SECRET: Optional[str] = (
        os.getenv("X_ACCESS_TOKEN_SECRET") or os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    )

    # General
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def has_gemini(cls) -> bool:
        return bool(cls.GEMINI_API_KEY)

    @classmethod
    def has_discord(cls) -> bool:
        return bool(cls.DISCORD_WEBHOOK_URL)

    @classmethod
    def has_x(cls) -> bool:
        return bool(
            cls.X_CONSUMER_KEY
            and cls.X_CONSUMER_SECRET
            and cls.X_ACCESS_TOKEN
            and cls.X_ACCESS_TOKEN_SECRET
        )
