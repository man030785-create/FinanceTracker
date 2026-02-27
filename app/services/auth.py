"""Authentication service: password hashing, JWT, register, login."""
from datetime import datetime, timedelta

import bcrypt
from jose import jwt
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.config import SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_HOURS
from app.models import User

# Bcrypt accepts at most 72 bytes; we truncate before calling to avoid any library raising.
MAX_PASSWORD_BYTES = 72


def _password_bytes(password: str) -> bytes:
    """Return password as bytes, truncated to 72 bytes (bcrypt limit)."""
    b = password.encode("utf-8") if isinstance(password, str) else password
    return b[:MAX_PASSWORD_BYTES]


def hash_password(password: str) -> str:
    pw_bytes = _password_bytes(password)
    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pw_bytes = _password_bytes(plain)
    try:
        hashed_bytes = hashed.encode("utf-8") if isinstance(hashed, str) else hashed
        return bcrypt.checkpw(pw_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def register_user(db: Session, email: str, password: str) -> tuple[User | None, str | None]:
    """Register a new user. Returns (user, None) or (None, error_message)."""
    if not email or "@" not in email:
        return None, "Invalid email."
    if not password or len(password) < 8:
        return None, "Password must be at least 8 characters."
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing:
        return None, "Email already registered."
    user = User(
        email=email,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, None


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return user if credentials are valid."""
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
