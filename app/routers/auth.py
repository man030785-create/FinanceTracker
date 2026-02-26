"""Auth routes: login, register, logout."""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter()


@router.get("/login", name="login_page")
async def login_page(request: Request):
    next_url = request.query_params.get("next", "")
    from app.main import app
    return app.state.render_template(request, "auth/login.html", {"error": None, "next": next_url})


async def _render_login(request: Request, db: Session | None, error: str | None = None, next_url: str = ""):
    from app.main import app
    return app.state.render_template(request, "auth/login.html", {"error": error, "next": next_url})


@router.get("/register", name="register_page")
async def register_page(request: Request):
    from app.main import app
    return app.state.render_template(request, "auth/register.html", {"error": None})


@router.post("/login", name="login_submit")
async def login_submit(request: Request, db: Session = Depends(get_db)):
    from app.services.auth import authenticate_user, create_access_token
    from fastapi.responses import RedirectResponse
    from app.csrf import validate_csrf_token
    form = await request.form()
    if not validate_csrf_token(form.get("csrf_token")):
        return await _render_login(request, db, error="Invalid request. Please try again.", next_url=form.get("next", ""))
    email = form.get("email", "").strip()
    password = form.get("password", "")
    user = authenticate_user(db, email, password)
    if not user:
        next_url = form.get("next", "")
        return await _render_login(request, db, error="Invalid email or password", next_url=next_url)
    token = create_access_token(user.id)
    next_url = form.get("next", "").strip() or "/dashboard"
    response = RedirectResponse(url=next_url, status_code=303)
    response.set_cookie(key="financetracker_token", value=token, httponly=True, samesite="lax")
    return response


@router.post("/register", name="register_submit")
async def register_submit(request: Request, db: Session = Depends(get_db)):
    from app.services.auth import register_user, create_access_token
    from fastapi.responses import RedirectResponse
    from app.csrf import validate_csrf_token
    form = await request.form()
    if not validate_csrf_token(form.get("csrf_token")):
        from app.main import app
        return app.state.render_template(request, "auth/register.html", {"error": "Invalid request. Please try again."})
    email = form.get("email", "").strip()
    password = form.get("password", "")
    user, error = register_user(db, email, password)
    if error:
        from app.main import app
        return app.state.render_template(request, "auth/register.html", {"error": error})
    token = create_access_token(user.id)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="financetracker_token", value=token, httponly=True, samesite="lax")
    return response


@router.get("/logout", name="logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("financetracker_token")
    return response
