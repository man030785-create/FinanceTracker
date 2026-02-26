"""Category management routes."""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse

from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter()


@router.get("", name="categories_list")
async def categories_list(request: Request, db=Depends(get_db), user=Depends(get_current_user)):
    from app.services.categories import get_categories_for_user
    cats = get_categories_for_user(db, user.id)
    from app.main import app
    return app.state.render_template(
        request, "categories/list.html", {"user": user, "categories": cats}
    )


@router.post("", name="category_create")
async def category_create(request: Request, db=Depends(get_db), user=Depends(get_current_user)):
    form = await request.form()
    from app.csrf import validate_csrf_token
    if not validate_csrf_token(form.get("csrf_token")):
        return RedirectResponse(url="/categories", status_code=303)
    name = (form.get("name") or "").strip()
    from app.services.categories import create_user_category
    cat, error = create_user_category(db, user.id, name)
    if error:
        from app.services.categories import get_categories_for_user
        cats = get_categories_for_user(db, user.id)
        from app.main import app
        return app.state.render_template(
            request, "categories/list.html", {"user": user, "categories": cats, "error": error}
        )
    return RedirectResponse(url="/categories", status_code=303)


@router.post("/{category_id}/delete", name="category_delete")
async def category_delete(
    request: Request, category_id: int, db=Depends(get_db), user=Depends(get_current_user)
):
    form = await request.form()
    from app.csrf import validate_csrf_token
    if not validate_csrf_token(form.get("csrf_token")):
        return RedirectResponse(url="/categories", status_code=303)
    from app.services.categories import delete_user_category
    delete_user_category(db, user.id, category_id)
    return RedirectResponse(url="/categories", status_code=303)
