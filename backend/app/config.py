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
