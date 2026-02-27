"""Authentication service: password hashing, JWT, register, login."""
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.config import SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_HOURS
from app.models import User

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False,  # Silently truncate to 72 bytes (bcrypt limit)
)


def _truncate_72_bytes(s: str) -> str:
    """Bcrypt accepts max 72 bytes. Return s truncated to 72 UTF-8 bytes."""
    if not s:
        return s
    b = s.encode("utf-8")
    if len(b) <= 72:
        return s
    return b[:72].decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    return pwd_context.hash(_truncate_72_bytes(password))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_truncate_72_bytes(plain), hashed)


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
