"""Dashboard (home) routes."""
from fastapi import APIRouter, Request, Depends

from app.dependencies import get_current_user_optional
from app.database import get_db

router = APIRouter()


@router.get("/dashboard", name="dashboard_page")
async def dashboard_page(request: Request, db=Depends(get_db)):
    from fastapi.responses import RedirectResponse
    user = await get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    from app.services.insights import get_monthly_summary
    from datetime import date
    today = date.today()
    summary = get_monthly_summary(db, user.id, today.year, today.month)
    from app.services.transactions import get_recent_transactions
    recent = get_recent_transactions(db, user.id, limit=10)
    from app.main import app
    return app.state.render_template(
        request,
        "dashboard.html",
        {"user": user, "summary": summary, "recent_transactions": recent},
    )
