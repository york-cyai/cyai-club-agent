"""Test setup. Runs before the app is imported.

app/config.py reads backend/.env, which may contain the real Supabase
DATABASE_URL. Environment variables take priority over .env, so they are set
here to point the app at a throwaway SQLite file and a fake API key. The tests
never touch the real database or any outside service.
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
_TMP_DIR = tempfile.mkdtemp(prefix="cyai-tests-")

TEST_API_KEY = "test-api-key-not-real"

os.environ.update(
    {
        "APP_ENV": "test",
        "DATABASE_URL": f"sqlite:///{_TMP_DIR}/test.db",
        "AGENT_API_KEY": TEST_API_KEY,
        "TOKEN_SECRET_KEY": "test-token-secret-not-real",
        "ALLOWED_ORIGINS": "",
    }
)
os.environ.pop("RENDER", None)

# main.py uses paths relative to the backend folder (app/uploads, app/assets).
os.chdir(BACKEND_DIR)
sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from app.config import settings

    # Guard: never run the tests against a real database. Checked before
    # importing app.main, which creates tables as soon as it is imported.
    assert settings.database_url.startswith("sqlite:///" + _TMP_DIR), "tests must use the temp SQLite DB"

    from app.main import app

    # Not used as a context manager, so the startup event (the background
    # scheduler that calls outside services) does not run.
    return TestClient(app)
