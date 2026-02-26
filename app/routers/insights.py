"""Financial insights routes."""
from fastapi import APIRouter, Request, Depends, Query
from datetime import date, timedelta

from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter()


@router.get("", name="insights_page")
async def insights_page(
    request: Request,
    db=Depends(get_db),
    user=Depends(get_current_user),
    period: str = Query("30", description="30, 6months, or custom"),
    date_from: str | None = None,
    date_to: str | None = None,
):
    today = date.today()
    if period == "6months":
        date_from_val = today - timedelta(days=180)
        date_to_val = today
    elif period == "custom" and date_from and date_to:
        try:
            date_from_val = date.fromisoformat(date_from)
            date_to_val = date.fromisoformat(date_to)
        except ValueError:
            date_from_val = today - timedelta(days=30)
            date_to_val = today
    else:
        date_from_val = today - timedelta(days=30)
        date_to_val = today

    from app.services.insights import get_monthly_summary_range, get_category_breakdown
    summary = get_monthly_summary_range(db, user.id, date_from_val, date_to_val)
    breakdown = get_category_breakdown(db, user.id, date_from_val, date_to_val)
    from app.main import app
    return app.state.render_template(
        request,
        "insights/index.html",
        {
            "user": user,
            "summary": summary,
            "breakdown": breakdown,
            "period": period,
            "date_from": date_from_val.isoformat() if hasattr(date_from_val, "isoformat") else str(date_from_val),
            "date_to": date_to_val.isoformat() if hasattr(date_to_val, "isoformat") else str(date_to_val),
        },
    )
