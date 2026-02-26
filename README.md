# FinanceTracker

A web-based personal finance tracker built with FastAPI, Jinja2, and HTMX.

## Features

- **Authentication**: Register, login, JWT in HTTP-only cookie, protected routes
- **Transactions**: Create, list (with filters and pagination), update, soft delete
- **Financial insights**: Monthly summary, category breakdown, time-based reports (30 days, 6 months, custom)
- **Categories**: Predefined + user-defined, no duplicate names per user

## Setup

1. Create a virtual environment and activate it:

   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Optional: copy `.env.example` to `.env` and set `SECRET_KEY` and `DATABASE_URL`. Defaults use a local SQLite file and a dev secret.

## Run

From the project root (`FinanceTracker/`):

```bash
 uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 — you will be redirected to login or dashboard.

## Project structure

- `app/main.py` — FastAPI app, Jinja2, static files, router registration
- `app/config.py` — Settings from environment
- `app/database.py` — SQLAlchemy engine, session, base
- `app/models/` — User, Category, Transaction
- `app/schemas/` — Pydantic (reserved for API/forms)
- `app/services/` — Auth, categories, transactions, insights
- `app/routers/` — Auth, dashboard, categories, transactions, insights
- `app/templates/` — Jinja2 HTML
- `app/static/` — CSS (and optional JS)
