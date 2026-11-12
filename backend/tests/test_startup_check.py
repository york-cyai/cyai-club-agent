import pytest

from app import config


@pytest.fixture
def production(monkeypatch):
    monkeypatch.setattr(config.settings, "app_env", "production")
    monkeypatch.setattr(config.settings, "database_url", "postgresql://user:pw@host/db")
    monkeypatch.setattr(config.settings, "agent_api_key", "real-looking-key")
    monkeypatch.setattr(config.settings, "token_secret_key", "real-looking-secret")
    return monkeypatch


def test_production_with_all_settings_starts(production):
    config.check_required_settings()  # does not raise


@pytest.mark.parametrize(
    "field, value, name",
    [
        ("database_url", "sqlite:///./cyai_agent.db", "DATABASE_URL"),
        ("database_url", "", "DATABASE_URL"),
        ("agent_api_key", "", "AGENT_API_KEY"),
        ("agent_api_key", "your_agent_api_key_here", "AGENT_API_KEY"),
        ("token_secret_key", "generate_a_random_secret_here", "TOKEN_SECRET_KEY"),
    ],
)
def test_production_refuses_to_start_when_missing(production, caplog, field, value, name):
    production.setattr(config.settings, field, value)
    with pytest.raises(SystemExit):
        config.check_required_settings()
    assert name in caplog.text


def test_local_development_still_starts(monkeypatch):
    monkeypatch.setattr(config.settings, "app_env", "local")
    monkeypatch.setattr(config.settings, "database_url", "sqlite:///./cyai_agent.db")
    monkeypatch.setattr(config.settings, "agent_api_key", "")
    config.check_required_settings()  # does not raise
