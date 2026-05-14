"""Společný kontext předávaný do každé Jinja2 šablony."""
from datetime import datetime
from typing import Optional

from fastapi import Request

from app import cart as cart_service
from app.csrf import _get_or_create_token
from app.i18n import get_lang, make_t
from app.models import User


def base_ctx(request: Request, current_user: Optional[User] = None) -> dict:
    lang = get_lang(request)
    flash_data = request.session.pop("flash", None)
    return {
        "request": request,
        "lang": lang,
        "t": make_t(lang),
        "csrf_token": _get_or_create_token(request),
        "current_user": current_user,
        "cart_count": len(cart_service.get_cart(request)),
        "now": datetime.utcnow(),
        "flash": flash_data,
    }


def flash(request: Request, message: str, kind: str = "success") -> None:
    request.session["flash"] = {"message": message, "type": kind}
