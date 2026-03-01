"""FastAPI dependencies (e.g. auth)."""
from datetime import date
from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import COOKIE_NAME, SECRET_KEY
from app.models import User


async def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> User:
    """Require authenticated user; redirect to login if not."""
    user = await get_current_user_optional(request, db)
    if user is None:
        next_url = request.url.path
        if request.query_params:
            next_url += "?" + str(request.query_params)
        return RedirectResponse(url=f"/login?next={next_url}", status_code=303)
    return user


def get_alerts_for_user(db: Session, user_id: int) -> list:
    """Return current month alerts for template context (e.g. nav banner)."""
    from app.services.alerts import get_alerts
    today = date.today()
    return get_alerts(db, user_id, year=today.year, month=today.month)


async def get_current_user_optional(
    request: Request, db: Session = Depends(get_db)
) -> User | None:
    """Return current user if authenticated, else None."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    from jose import jwt, JWTError
    from app.config import JWT_ALGORITHM
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        user = db.get(User, int(user_id))
        return user
    except (JWTError, ValueError, TypeError):
        return None
