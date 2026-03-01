"""Alerts routes."""
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import RedirectResponse
from datetime import date

from app.database import get_db
from app.dependencies import get_current_user, get_alerts_for_user
from app.services.alerts import get_alerts
from app.csrf import validate_csrf_token

router = APIRouter()


@router.post("/dismiss", name="alerts_dismiss")
async def alerts_dismiss(request: Request, user=Depends(get_current_user)):
    """Dismiss the alert banner for the current month (sets a cookie)."""
    form = await request.form()
    if not validate_csrf_token(form.get("csrf_token")):
        return RedirectResponse(url="/dashboard", status_code=303)
    next_url = (form.get("next") or request.url_for("dashboard_page")).strip()
    if not next_url.startswith("/"):
        next_url = "/dashboard"
    response = RedirectResponse(url=next_url, status_code=303)
    response.set_cookie(
        key="alerts_dismissed",
        value=date.today().strftime("%Y-%m"),
        path="/",
        max_age=60 * 60 * 24 * 35,
        samesite="lax",
    )
    return response


@router.get("", name="alerts_page")
async def alerts_page(
    request: Request,
    db=Depends(get_db),
    user=Depends(get_current_user),
    year: int | None = Query(None, description="Year (default: current)"),
    month: int | None = Query(None, description="Month 1-12 (default: current)"),
):
    today = date.today()
    y = year or today.year
    m = month or today.month
    page_alerts = get_alerts(db, user.id, year=y, month=m)
    alerts = get_alerts_for_user(db, user.id)  # current month for nav banner
    from app.main import app
    return app.state.render_template(
        request,
        "alerts/index.html",
        {"user": user, "alerts": alerts, "page_alerts": page_alerts, "year": y, "month": m, "current_year": today.year, "current_month": today.month},
    )
