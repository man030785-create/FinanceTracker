"""Transaction CRUD routes."""
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import RedirectResponse

from app.database import get_db
from app.dependencies import get_current_user, get_alerts_for_user

router = APIRouter()


@router.get("", name="transactions_list")
async def transactions_list(
    request: Request,
    db=Depends(get_db),
    user=Depends(get_current_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    date_from: str | None = None,
    date_to: str | None = None,
    category_id: int | None = None,
    type_filter: str | None = Query(None, alias="type"),
):
    from app.services.transactions import list_transactions
    from app.services.categories import get_categories_for_user
    result = list_transactions(
        db, user.id, page=page, per_page=per_page,
        date_from=date_from, date_to=date_to, category_id=category_id, type_filter=type_filter,
    )
    categories = get_categories_for_user(db, user.id)
    alerts = get_alerts_for_user(db, user.id)
    from app.main import app
    return app.state.render_template(
        request,
        "transactions/list.html",
        {
            "user": user,
            "alerts": alerts,
            "transactions": result["items"],
            "total": result["total"],
            "page": page,
            "per_page": per_page,
            "total_pages": result["total_pages"],
            "categories": categories,
            "filters": {
                "date_from": date_from,
                "date_to": date_to,
                "category_id": category_id,
                "type": type_filter,
            },
        },
    )


@router.get("/new", name="transaction_new")
async def transaction_new(request: Request, db=Depends(get_db), user=Depends(get_current_user)):
    from app.services.categories import get_categories_for_user
    categories = get_categories_for_user(db, user.id)
    alerts = get_alerts_for_user(db, user.id)
    from app.main import app
    return app.state.render_template(
        request, "transactions/form.html", {"user": user, "alerts": alerts, "categories": categories, "transaction": None}
    )


@router.post("", name="transaction_create")
async def transaction_create(request: Request, db=Depends(get_db), user=Depends(get_current_user)):
    form = await request.form()
    from app.csrf import validate_csrf_token
    if not validate_csrf_token(form.get("csrf_token")):
        return RedirectResponse(url="/transactions", status_code=303)
    from app.services.transactions import create_transaction
    trans, error = create_transaction(
        db,
        user_id=user.id,
        amount=form.get("amount"),
        type_=form.get("type"),
        category_id=form.get("category_id"),
        description=form.get("description") or None,
        transaction_date=form.get("transaction_date"),
    )
    if error:
        from app.services.categories import get_categories_for_user
        categories = get_categories_for_user(db, user.id)
        alerts = get_alerts_for_user(db, user.id)
        from app.main import app
        return app.state.render_template(
            request,
            "transactions/form.html",
            {"user": user, "alerts": alerts, "categories": categories, "transaction": None, "error": error},
        )
    return RedirectResponse(url="/transactions", status_code=303)


@router.get("/{transaction_id}/edit", name="transaction_edit")
async def transaction_edit(
    request: Request, transaction_id: int, db=Depends(get_db), user=Depends(get_current_user)
):
    from app.services.transactions import get_transaction
    from fastapi.responses import RedirectResponse
    trans = get_transaction(db, user.id, transaction_id)
    if not trans:
        return RedirectResponse(url="/transactions", status_code=303)
    from app.services.categories import get_categories_for_user
    categories = get_categories_for_user(db, user.id)
    alerts = get_alerts_for_user(db, user.id)
    from app.main import app
    return app.state.render_template(
        request,
        "transactions/form.html",
        {"user": user, "alerts": alerts, "categories": categories, "transaction": trans},
    )


@router.post("/{transaction_id}", name="transaction_update")
async def transaction_update(
    request: Request, transaction_id: int, db=Depends(get_db), user=Depends(get_current_user)
):
    form = await request.form()
    from app.csrf import validate_csrf_token
    if not validate_csrf_token(form.get("csrf_token")):
        return RedirectResponse(url="/transactions", status_code=303)
    from app.services.transactions import update_transaction
    trans, error = update_transaction(
        db,
        user_id=user.id,
        transaction_id=transaction_id,
        amount=form.get("amount"),
        type_=form.get("type"),
        category_id=form.get("category_id"),
        description=form.get("description") or None,
        transaction_date=form.get("transaction_date"),
    )
    if error:
        from app.services.transactions import get_transaction
        from app.services.categories import get_categories_for_user
        trans = get_transaction(db, user.id, transaction_id)
        categories = get_categories_for_user(db, user.id)
        alerts = get_alerts_for_user(db, user.id)
        from app.main import app
        return app.state.render_template(
            request,
            "transactions/form.html",
            {"user": user, "alerts": alerts, "categories": categories, "transaction": trans, "error": error},
        )
    return RedirectResponse(url="/transactions", status_code=303)


@router.post("/{transaction_id}/delete", name="transaction_delete")
async def transaction_delete(
    request: Request, transaction_id: int, db=Depends(get_db), user=Depends(get_current_user)
):
    form = await request.form()
    from app.csrf import validate_csrf_token
    if not validate_csrf_token(form.get("csrf_token")):
        return RedirectResponse(url="/transactions", status_code=303)
    from app.services.transactions import soft_delete_transaction
    soft_delete_transaction(db, user.id, transaction_id)
    return RedirectResponse(url="/transactions", status_code=303)
