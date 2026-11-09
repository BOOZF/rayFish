import time

import pytest

from app import create_app
from app.api import auth
from app.config import Config


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(Config, 'AUTH_ENABLED', True)
    monkeypatch.setattr(Config, 'ADMIN_USERNAME', 'admin')
    monkeypatch.setattr(Config, 'ADMIN_PASSWORD', 'test-password')
    return create_app().test_client()


def _login(client, username='admin', password='test-password'):
    return client.post('/api/auth/login', json={'username': username, 'password': password})


def _bearer(token):
    return {'Authorization': f'Bearer {token}'}


def test_api_requires_login_but_health_does_not(client):
    assert client.get('/api/simulation/history').status_code == 401
    assert client.get('/health').status_code == 200


@pytest.mark.parametrize('username,password', [
    ('admin', 'wrong'),
    ('wrong', 'test-password'),
    ('', ''),
    (None, None),
    (1, 2),
])
def test_wrong_credentials_are_rejected(client, username, password):
    response = _login(client, username, password)
    assert response.status_code == 401
    assert 'token' not in response.get_json()


def test_login_token_opens_the_api(client):
    token = _login(client).get_json()['data']['token']
    assert client.get('/api/simulation/history', headers=_bearer(token)).status_code != 401


@pytest.mark.parametrize('header', ['Bearer not-a-token', 'Bearer ', 'Basic abc', ''])
def test_bad_authorization_is_rejected(client, header):
    response = client.get('/api/simulation/history', headers={'Authorization': header})
    assert response.status_code == 401


def test_changing_the_password_invalidates_tokens(client):
    token = _login(client).get_json()['data']['token']
    client.application.config['ADMIN_PASSWORD'] = 'new-password'
    assert client.get('/api/simulation/history', headers=_bearer(token)).status_code == 401


def test_expired_token_is_rejected(client, monkeypatch):
    token = _login(client).get_json()['data']['token']
    now = time.time()
    monkeypatch.setattr(
        'itsdangerous.timed.time.time',
        lambda: now + auth.TOKEN_MAX_AGE_SECONDS + 10,
    )
    assert client.get('/api/simulation/history', headers=_bearer(token)).status_code == 401


def test_missing_password_blocks_login_and_api(client):
    client.application.config['ADMIN_PASSWORD'] = None
    assert _login(client, 'admin', '').status_code == 401
    assert client.get('/api/simulation/history').status_code == 401
