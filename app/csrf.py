"""CSRF token generation and validation."""
import os
from itsdangerous import URLSafeTimedSerializer, BadSignature

from app.config import SECRET_KEY

_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="csrf")


def generate_csrf_token() -> str:
    return _serializer.dumps(os.urandom(16).hex())


def validate_csrf_token(token: str | None) -> bool:
    if not token:
        return False
    try:
        _serializer.loads(token, max_age=3600)
        return True
    except BadSignature:
        return False
