"""Transaction service: CRUD, list with filters and pagination, soft delete."""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from app.models import Transaction, Category
from app.models.transaction import TransactionType


def _parse_amount(v) -> Decimal | None:
    if v is None or v == "":
        return None
    try:
        return Decimal(str(v).strip())
    except Exception:
        return None


def _parse_date(v) -> date | None:
    if v is None or v == "":
        return None
    try:
        return date.fromisoformat(str(v).strip())
    except ValueError:
        return None


def create_transaction(
    db: Session,
    user_id: int,
    amount: str | None,
    type_: str | None,
    category_id: str | None,
    description: str | None,
    transaction_date: str | None,
) -> tuple[Transaction | None, str | None]:
    amount_val = _parse_amount(amount)
    if amount_val is None or amount_val <= 0:
        return None, "Amount must be a positive number."
    try:
        type_enum = TransactionType(type_) if type_ else TransactionType.expense
    except ValueError:
        return None, "Type must be income or expense."
    try:
        cat_id = int(category_id) if category_id else None
    except (TypeError, ValueError):
        cat_id = None
    if not cat_id:
        return None, "Category is required."
    date_val = _parse_date(transaction_date)
    if not date_val:
        return None, "Transaction date is required."
    # Check category exists and is available to user
    cat = db.get(Category, cat_id)
    if not cat or (cat.user_id is not None and cat.user_id != user_id):
        return None, "Invalid category."
    trans = Transaction(
        user_id=user_id,
        amount=amount_val,
        type=type_enum,
        category_id=cat_id,
        description=(description or "").strip() or None,
        transaction_date=date_val,
    )
    db.add(trans)
    db.commit()
    db.refresh(trans)
    return trans, None


def get_transaction(db: Session, user_id: int, transaction_id: int) -> Transaction | None:
    trans = db.get(Transaction, transaction_id)
    if not trans or trans.user_id != user_id or trans.deleted_at:
        return None
    return trans


def list_transactions(
    db: Session,
    user_id: int,
    page: int = 1,
    per_page: int = 20,
    date_from: str | None = None,
    date_to: str | None = None,
    category_id: int | None = None,
    type_filter: str | None = None,
) -> dict:
    q = select(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.deleted_at.is_(None),
    )
    if date_from:
        d = _parse_date(date_from)
        if d:
            q = q.where(Transaction.transaction_date >= d)
    if date_to:
        d = _parse_date(date_to)
        if d:
            q = q.where(Transaction.transaction_date <= d)
    if category_id is not None:
        q = q.where(Transaction.category_id == category_id)
    if type_filter and type_filter in ("income", "expense"):
        q = q.where(Transaction.type == type_filter)
    count_q = select(func.count()).select_from(q.subquery())
    total = db.execute(count_q).scalar() or 0
    q = q.order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
    q = q.offset((page - 1) * per_page).limit(per_page)
    items = list(db.execute(q).scalars().all())
    import math
    total_pages = max(1, math.ceil(total / per_page)) if total else 1
    return {"items": items, "total": total, "total_pages": total_pages}


def update_transaction(
    db: Session,
    user_id: int,
    transaction_id: int,
    amount: str | None,
    type_: str | None,
    category_id: str | None,
    description: str | None,
    transaction_date: str | None,
) -> tuple[Transaction | None, str | None]:
    trans = get_transaction(db, user_id, transaction_id)
    if not trans:
        return None, "Transaction not found."
    amount_val = _parse_amount(amount)
    if amount_val is None or amount_val <= 0:
        return None, "Amount must be a positive number."
    try:
        type_enum = TransactionType(type_) if type_ else trans.type
    except ValueError:
        return None, "Type must be income or expense."
    try:
        cat_id = int(category_id) if category_id else trans.category_id
    except (TypeError, ValueError):
        cat_id = trans.category_id
    if not cat_id:
        return None, "Category is required."
    date_val = _parse_date(transaction_date)
    if not date_val:
        return None, "Transaction date is required."
    cat = db.get(Category, cat_id)
    if not cat or (cat.user_id is not None and cat.user_id != user_id):
        return None, "Invalid category."
    trans.amount = amount_val
    trans.type = type_enum
    trans.category_id = cat_id
    trans.description = (description or "").strip() or None
    trans.transaction_date = date_val
    db.commit()
    db.refresh(trans)
    return trans, None


def soft_delete_transaction(db: Session, user_id: int, transaction_id: int) -> bool:
    trans = get_transaction(db, user_id, transaction_id)
    if not trans:
        return False
    trans.deleted_at = datetime.utcnow()
    db.commit()
    return True


def get_recent_transactions(db: Session, user_id: int, limit: int = 10) -> list[Transaction]:
    q = (
        select(Transaction)
        .where(Transaction.user_id == user_id, Transaction.deleted_at.is_(None))
        .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
        .limit(limit)
    )
    return list(db.execute(q).scalars().all())
