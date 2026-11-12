from tests.conftest import TEST_API_KEY

UNLISTED_ORIGIN = "https://not-the-club.example"
LISTED_ORIGIN = "https://cyai-club-agent-frontend.onrender.com"


def _preflight(client, origin):
    return client.options(
        "/events/",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "x-api-key",
        },
    )


def test_unlisted_origin_is_blocked_by_cors(client):
    # The browser's preflight check is refused...
    response = _preflight(client, UNLISTED_ORIGIN)
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers

    # ...and a direct request gets no permission header, so browsers block it.
    response = client.get(
        "/events/", headers={"Origin": UNLISTED_ORIGIN, "x-api-key": TEST_API_KEY}
    )
    assert "access-control-allow-origin" not in response.headers


def test_listed_origin_is_allowed(client):
    # Control case: proves the test above fails for the right reason.
    response = _preflight(client, LISTED_ORIGIN)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == LISTED_ORIGIN


def test_allowed_origins_env_var_adds_to_defaults(monkeypatch):
    from app import config

    monkeypatch.setattr(
        config.settings, "allowed_origins", " https://new.example/ ,,http://localhost:5173"
    )
    origins = config.get_allowed_origins()
    assert origins[: len(config.DEFAULT_ALLOWED_ORIGINS)] == config.DEFAULT_ALLOWED_ORIGINS
    assert "https://new.example" in origins  # trailing slash removed
    assert origins.count("http://localhost:5173") == 1  # no duplicates
