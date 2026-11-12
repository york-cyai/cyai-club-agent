from tests.conftest import TEST_API_KEY

PROTECTED_URL = "/events/"


def test_right_api_key_returns_200(client):
    response = client.get(PROTECTED_URL, headers={"x-api-key": TEST_API_KEY})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_wrong_api_key_returns_401(client):
    response = client.get(PROTECTED_URL, headers={"x-api-key": "wrong-key"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_missing_api_key_returns_422(client):
    response = client.get(PROTECTED_URL)
    assert response.status_code == 422


def test_health_check_needs_no_key(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "cyai-club-agent"}
