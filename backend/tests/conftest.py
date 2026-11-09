import pytest

from app.config import Config


@pytest.fixture(autouse=True)
def disable_login(monkeypatch):
    """API tests call routes directly; test_auth.py turns the login back on."""
    monkeypatch.setattr(Config, 'AUTH_ENABLED', False)
