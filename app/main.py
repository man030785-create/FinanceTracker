"""FastAPI application entry point."""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import BASE_DIR, ASSET_VERSION
from app.database import Base, engine, get_db, SessionLocal
from app.routers import auth, dashboard, categories, transactions, insights, alerts
from app.services.categories import seed_predefined_categories

# Create tables
Base.metadata.create_all(bind=engine)
# Seed predefined categories
db = SessionLocal()
try:
    seed_predefined_categories(db)
finally:
    db.close()

app = FastAPI(title="FinanceTracker")

# Jinja2
templates_dir = Path(__file__).resolve().parent / "templates"
env = Environment(
    loader=FileSystemLoader(str(templates_dir)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_template(request: Request, name: str, context: dict) -> HTMLResponse:
    """Render a Jinja2 template with request in context."""
    from datetime import date
    from app.csrf import generate_csrf_token
    from app.config import SHOW_ALERTS_BANNER_DEMO
    ctx = {
        "request": request,
        "csrf_token": generate_csrf_token(),
        "asset_version": ASSET_VERSION,
        "alerts_dismiss_key": date.today().strftime("%Y-%m"),
        "show_alerts_banner_demo": SHOW_ALERTS_BANNER_DEMO,
        "force_show_alerts_banner": request.query_params.get("show_alerts") == "1",
        **context,
    }
    # Ensure alerts is always set when user is present (so banner works even if a route forgot to pass it)
    if ctx.get("user") is not None and ctx.get("alerts") is None:
        from app.dependencies import get_alerts_for_user
        db = SessionLocal()
        try:
            ctx["alerts"] = get_alerts_for_user(db, ctx["user"].id)
        finally:
            db.close()
    template = env.get_template(name)
    return HTMLResponse(template.render(ctx))


# Expose render_template to routers via app state
app.state.render_template = render_template

# Static files
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Routers
app.include_router(auth.router, prefix="", tags=["auth"])
app.include_router(dashboard.router, prefix="", tags=["dashboard"])
app.include_router(categories.router, prefix="/categories", tags=["categories"])
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(insights.router, prefix="/insights", tags=["insights"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])


@app.get("/")
async def root(request: Request):
    """Redirect to dashboard or login."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=request.url_for("dashboard_page"))


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return render_template(request, "errors/404.html", {})


@app.exception_handler(Exception)
async def server_error_handler(request: Request, exc: Exception):
    import logging
    logging.exception("Unhandled error: %s", exc)
    return render_template(request, "errors/500.html", {"error": str(exc)})
