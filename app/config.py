"""Application configuration from environment."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
_default_db_path = BASE_DIR / "financetracker.db"
DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{_default_db_path}")
# Render and some hosts give postgres://; SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://") :]
# Render Postgres requires SSL
if "postgresql" in DATABASE_URL and "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require" if "?" not in DATABASE_URL else "&sslmode=require"
if "sqlite" in DATABASE_URL and "///" in DATABASE_URL:
    path_part = DATABASE_URL.split("///", 1)[-1]
    if path_part.startswith("./") or (path_part != "" and not path_part.startswith("/") and ":" not in path_part[:2]):
        DATABASE_URL = f"sqlite:///{BASE_DIR / path_part.lstrip('./')}"

# JWT
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 1
COOKIE_NAME = "financetracker_token"

# Pagination
DEFAULT_PAGE_SIZE = 20

# Alerts: budget vs earnings and large transactions
# Alert when expenses >= this percent of income (e.g. 90 = 90%)
BUDGET_ALERT_PERCENT: float = float(os.getenv("BUDGET_ALERT_PERCENT", "90"))
# Alert when a single expense is >= this percent of monthly income (e.g. 25 = 25%)
LARGE_TRANSACTION_PERCENT: float = float(os.getenv("LARGE_TRANSACTION_PERCENT", "25"))

# Cache busting for static assets (Render sets RENDER_GIT_COMMIT)
ASSET_VERSION: str = os.getenv("RENDER_GIT_COMMIT", "dev")
