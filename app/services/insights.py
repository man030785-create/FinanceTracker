"""Insights service: monthly summary, category breakdown, date range summary."""
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models import Transaction
from app.models.transaction import TransactionType


def get_monthly_summary(
    db: Session, user_id: int, year: int, month: int
) -> dict:
    """Summary for a single month: income, expenses, net, savings_rate."""
    from calendar import monthrange
    start = date(year, month, 1)
    _, last = monthrange(year, month)
    end = date(year, month, last)
    return get_monthly_summary_range(db, user_id, start, end)


def get_monthly_summary_range(
    db: Session, user_id: int, date_from: date, date_to: date
) -> dict:
    """Summary for a date range: total income, total expenses, net, savings_rate."""
    q_income = (
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Transaction.type == TransactionType.income,
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
        )
    )
    q_expense = (
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Transaction.type == TransactionType.expense,
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
        )
    )
    income = db.execute(q_income).scalar() or Decimal("0")
    expenses = db.execute(q_expense).scalar() or Decimal("0")
    net = income - expenses
    rate = (float(net) / float(income) * 100) if income and income > 0 else Decimal("0")
    return {
        "total_income": income,
        "total_expenses": expenses,
        "net_savings": net,
        "savings_rate": round(rate, 1),
    }


def get_category_breakdown(
    db: Session, user_id: int, date_from: date, date_to: date
) -> list[dict]:
    """Per-category totals (expenses only) and % of total spending."""
    from app.models import Category
    q = (
        select(Transaction.category_id, func.sum(Transaction.amount).label("total"))
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Transaction.type == TransactionType.expense,
            Transaction.transaction_date >= date_from,
            Transaction.transaction_date <= date_to,
        )
        .group_by(Transaction.category_id)
    )
    rows = db.execute(q).all()
    total_expenses = sum(r.total for r in rows)
    result = []
    for r in rows:
        cat = db.get(Category, r.category_id)
        name = cat.name if cat else "Unknown"
        pct = (float(r.total) / float(total_expenses) * 100) if total_expenses else 0
        result.append({
            "category_id": r.category_id,
            "category_name": name,
            "total": r.total,
            "percent": round(pct, 1),
        })
    result.sort(key=lambda x: -float(x["total"]))
    return result
