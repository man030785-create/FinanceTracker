"""Category service: predefined seed, list, create (with duplicate check), delete."""
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.models import Category, User

PREDEFINED_NAMES = [
    "Food", "Transport", "Salary", "Rent", "Utilities",
    "Entertainment", "Health", "Other",
]


def seed_predefined_categories(db: Session) -> None:
    """Create predefined categories if they don't exist (user_id=None)."""
    for name in PREDEFINED_NAMES:
        existing = db.execute(
            select(Category).where(
                Category.user_id.is_(None),
                Category.name == name,
            )
        ).scalar_one_or_none()
        if not existing:
            db.add(Category(name=name, user_id=None, is_predefined=True))
    db.commit()


def get_categories_for_user(db: Session, user_id: int) -> list[Category]:
    """Predefined + user's own categories, ordered by name."""
    return list(
        db.execute(
            select(Category)
            .where(or_(Category.user_id.is_(None), Category.user_id == user_id))
            .order_by(Category.name)
        ).scalars().all()
    )


def create_user_category(db: Session, user_id: int, name: str) -> tuple[Category | None, str | None]:
    """Create a user category. Duplicate name (case-insensitive) returns error."""
    name = (name or "").strip()
    if not name:
        return None, "Category name is required."
    existing = db.execute(
        select(Category).where(
            Category.user_id == user_id,
            Category.name.ilike(name),
        )
    ).scalar_one_or_none()
    if existing:
        return None, f"A category named '{name}' already exists."
    cat = Category(user_id=user_id, name=name, is_predefined=False)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat, None


def delete_user_category(db: Session, user_id: int, category_id: int) -> bool:
    """Delete only if category belongs to user (not predefined)."""
    cat = db.get(Category, category_id)
    if not cat or cat.user_id != user_id:
        return False
    db.delete(cat)
    db.commit()
    return True
