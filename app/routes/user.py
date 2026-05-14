from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.csrf import csrf_protect
from app.database import get_db
from app.dependencies import get_current_user
from app.jinja import templates
from app.models import Order, User
from app.template_context import base_ctx, flash

router = APIRouter()


@router.get("/auth/login")
async def login_page(request: Request):
    from app.template_context import base_ctx
    return templates.TemplateResponse("auth/login.html", base_ctx(request))


@router.get("/auth/register")
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", base_ctx(request))


@router.get("/profile")
async def profile_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("user/profile.html", base_ctx(request, current_user))


@router.post("/profile/save", dependencies=[Depends(csrf_protect)])
async def profile_save(
    request: Request,
    first_name: Optional[str] = Form(default=None),
    last_name: Optional[str] = Form(default=None),
    shipping_address: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.first_name = first_name or None
    current_user.last_name = last_name or None
    current_user.shipping_address = shipping_address or None
    db.commit()
    flash(request, "Změny uloženy." if request.session.get("lang", "cs") == "cs" else "Changes saved.")
    return RedirectResponse("/profile", status_code=303)


@router.get("/my-orders")
async def my_orders(request: Request, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    orders = db.query(Order).filter(Order.user_id == current_user.id)\
               .order_by(Order.created_at.desc()).all()
    return templates.TemplateResponse("user/orders.html", {
        **base_ctx(request, current_user),
        "orders": orders,
    })
