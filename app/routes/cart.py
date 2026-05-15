from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app import cart as cart_service
from app.csrf import csrf_protect
from app.database import get_db

router = APIRouter(prefix="/cart", tags=["cart"])

_QTY_MIN = 1
_QTY_MAX = 99


def _validate_qty(qty: int) -> int:
    if qty < _QTY_MIN or qty > _QTY_MAX:
        raise HTTPException(400, f"Množství musí být {_QTY_MIN}–{_QTY_MAX}")
    return qty


@router.post("/add", dependencies=[Depends(csrf_protect)])
async def add_to_cart(
    request: Request,
    product_id: int = Form(...),
    qty: int = Form(default=1),
    variant_id: Optional[int] = Form(default=None),
):
    _validate_qty(qty)
    cart_service.add_product(request, product_id, qty, variant_id)
    return RedirectResponse(url="/cart", status_code=303)


@router.post("/add-design", dependencies=[Depends(csrf_protect)])
async def add_design_to_cart(
    request: Request,
    design_id: int = Form(...),
):
    cart_service.add_design(request, design_id)
    return RedirectResponse(url="/cart", status_code=303)


@router.post("/remove", dependencies=[Depends(csrf_protect)])
async def remove_from_cart(
    request: Request,
    index: int = Form(...),
):
    cart_service.remove_item(request, index)
    return RedirectResponse(url="/cart", status_code=303)


@router.get("/json")
async def cart_json(request: Request, db: Session = Depends(get_db)):
    """JSON endpoint pro případné JS fetch na stránce košíku."""
    items, total = cart_service.calculate_total(cart_service.get_cart(request), db)
    return {"items": items, "total": total, "count": len(items)}
