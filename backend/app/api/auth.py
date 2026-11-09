"""Admin login: checks the credentials in .env and issues signed tokens."""

import hmac

from flask import Blueprint, current_app, jsonify, request
from itsdangerous import BadSignature, URLSafeTimedSerializer

auth_bp = Blueprint('auth', __name__)

TOKEN_MAX_AGE_SECONDS = 7 * 24 * 60 * 60


def _serializer() -> URLSafeTimedSerializer:
    # Including the password means changing it signs out every existing session.
    secret = f"{current_app.config['SECRET_KEY']}:{current_app.config['ADMIN_PASSWORD']}"
    return URLSafeTimedSerializer(secret, salt='mirofish-admin-login')


def _matches(given, expected: str) -> bool:
    return isinstance(given, str) and hmac.compare_digest(
        given.encode('utf-8'), expected.encode('utf-8')
    )


def is_authorized(authorization_header: str) -> bool:
    """Return whether an Authorization header holds a valid, unexpired token."""
    if not current_app.config.get('ADMIN_PASSWORD'):
        return False
    scheme, _, token = (authorization_header or '').partition(' ')
    if scheme.lower() != 'bearer' or not token:
        return False
    try:
        username = _serializer().loads(token, max_age=TOKEN_MAX_AGE_SECONDS)
    except BadSignature:
        return False
    return _matches(username, current_app.config['ADMIN_USERNAME'])


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    data = data if isinstance(data, dict) else {}
    expected_username = current_app.config.get('ADMIN_USERNAME')
    expected_password = current_app.config.get('ADMIN_PASSWORD')

    # Check both fields every time so a wrong username isn't faster to reject.
    username_ok = _matches(data.get('username'), expected_username or '')
    password_ok = _matches(data.get('password'), expected_password or '')
    if not (expected_username and expected_password and username_ok and password_ok):
        return jsonify({'success': False, 'error': 'Invalid username or password'}), 401

    return jsonify({
        'success': True,
        'data': {'token': _serializer().dumps(expected_username)},
    })
