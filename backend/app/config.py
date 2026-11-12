import logging
import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = ""
    mistral_api_key: str = ""
    tavily_api_key: str = ""
    gmail_address: str = ""
    gmail_app_password: str = ""
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_refresh_token: str = ""
    adzuna_app_id: str = ""
    adzuna_api_key: str = ""
    database_url: str = "sqlite:///./cyai_agent.db"
    supabase_database_url: str = ""
    token_secret_key: str = ""
    agent_api_key: str = ""
    # Extra website addresses allowed to call the API (CORS), comma-separated,
    # e.g. "https://cyai-club-agent-web.onrender.com,https://example.org".
    # These are added to DEFAULT_ALLOWED_ORIGINS below, not used instead of them.
    allowed_origins: str = ""
    # "local" (default on your computer) or "production" (default on Render,
    # which sets RENDER=true). Outside local, missing required settings stop
    # the app from starting; see check_required_settings().
    app_env: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://cyai-club-assistant.onrender.com",
    "https://cyai-club-agent-frontend.onrender.com",
]


def get_allowed_origins() -> list:
    """Default origins plus any listed in ALLOWED_ORIGINS, without duplicates.

    Browsers send an Origin with no trailing slash, so a trailing "/" typed
    into the env var is removed to avoid a silent mismatch.
    """
    origins = list(DEFAULT_ALLOWED_ORIGINS)
    for raw in settings.allowed_origins.split(","):
        origin = raw.strip().rstrip("/")
        if origin and origin not in origins:
            origins.append(origin)
    return origins


logger = logging.getLogger("cyai_startup")

LOCAL_ENVS = {"local", "development", "dev", "test"}
_PLACEHOLDER_HINTS = ("your_", "generate_a_random", "placeholder")


def current_env() -> str:
    env = settings.app_env.strip().lower()
    if env:
        return env
    return "production" if os.environ.get("RENDER") else "local"


def missing_required_settings() -> list:
    """Names of required settings that are unset, placeholders, or (for the
    database) still pointing at the local SQLite fallback."""
    missing = []
    db_url = settings.database_url.strip()
    if not db_url or db_url.startswith("sqlite"):
        missing.append("DATABASE_URL")
    for name, value in (
        ("AGENT_API_KEY", settings.agent_api_key),
        ("TOKEN_SECRET_KEY", settings.token_secret_key),
    ):
        value = value.strip()
        if not value or any(hint in value.lower() for hint in _PLACEHOLDER_HINTS):
            missing.append(name)
    return missing


def check_required_settings() -> None:
    """Stop the app outside local development if required settings are missing.

    Without this, a missing DATABASE_URL silently starts the app on an empty
    SQLite file, and an empty AGENT_API_KEY weakens the API key check.
    """
    env = current_env()
    if env in LOCAL_ENVS:
        return
    missing = missing_required_settings()
    if not missing:
        return
    lines = [
        f"STARTUP ERROR: refusing to start in '{env}' because these environment "
        f"variables are missing or still placeholders: {', '.join(missing)}.",
        "Set them in the Render service's Environment settings and redeploy.",
    ]
    if "DATABASE_URL" in missing and settings.supabase_database_url.strip():
        lines.append(
            "Note: SUPABASE_DATABASE_URL is set, but the app only reads "
            "DATABASE_URL. Put the Supabase connection string in DATABASE_URL."
        )
    lines.append("For local development, unset RENDER or set APP_ENV=local.")
    logger.critical("\n".join(lines))
    raise SystemExit(1)
