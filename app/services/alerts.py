"""Alerts service: budget vs earnings, unusual large transactions."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.config import BUDGET_ALERT_PERCENT, LARGE_TRANSACTION_PERCENT
from app.models import Transaction
from app.models.transaction import TransactionType
from app.services.insights import get_monthly_summary


def get_alerts(db: Session, user_id: int, year: int | None = None, month: int | None = None) -> list[dict]:
    """
    Return list of active alerts for the user.
    Each alert is a dict: kind, title, message, severity, optional transaction_id, amount, etc.
    Uses current month if year/month not provided.
    """
    today = date.today()
    y = year or today.year
    m = month or today.month
    summary = get_monthly_summary(db, user_id, y, m)
    income = summary["total_income"]
    expenses = summary["total_expenses"]
    alerts: list[dict] = []

    # 1) Budget exceeded: expenses >= X% of earnings
    if income and income > 0:
        pct = float(expenses) / float(income) * 100
        if pct >= BUDGET_ALERT_PERCENT:
            alerts.append({
                "kind": "budget_exceeded",
                "title": "Budget alert",
                "message": f"Expenses are {pct:.1f}% of earnings this month (threshold: {BUDGET_ALERT_PERCENT}%).",
                "severity": "warning",
                "percent": round(pct, 1),
                "threshold_percent": BUDGET_ALERT_PERCENT,
            })

    # 2) Unusual large transactions: single expense >= Y% of monthly income
    if income and income > 0:
        threshold_amount = float(income) * (LARGE_TRANSACTION_PERCENT / 100)
        from calendar import monthrange
        _, last_day = monthrange(y, m)
        date_from = date(y, m, 1)
        date_to = date(y, m, last_day)
        q = (
            select(Transaction)
            .where(
                Transaction.user_id == user_id,
                Transaction.deleted_at.is_(None),
                Transaction.type == TransactionType.expense,
                Transaction.transaction_date >= date_from,
                Transaction.transaction_date <= date_to,
                Transaction.amount >= Decimal(str(threshold_amount)),
            )
            .order_by(Transaction.amount.desc())
        )
        large_trans = list(db.execute(q).scalars().all())
        for t in large_trans:
            pct = float(t.amount) / float(income) * 100
            alerts.append({
                "kind": "large_transaction",
                "title": "Unusual large transaction",
                "message": f"Expense of {t.amount:.2f} ({pct:.1f}% of monthly income) on {t.transaction_date}.",
                "severity": "info",
                "transaction_id": t.id,
                "amount": t.amount,
                "transaction_date": t.transaction_date,
                "description": t.description,
                "category_name": t.category.name if t.category else None,
            })

    return alerts
