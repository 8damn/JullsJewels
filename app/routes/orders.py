import random
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app import cart as cart_service
from app.csrf import csrf_protect
from app.database import get_db
from app.dependencies import get_current_user, get_current_user_optional
from app.models import Order, OrderItem, PaymentStatus, FulfillmentStatus, User

router = APIRouter(prefix="/orders", tags=["orders"])


def _generate_var_symbol() -> str:
    """10-ciferný variabilní symbol: YYMMDD + 4 náhodné číslice."""
    date_part = datetime.now().strftime("%y%m%d")
    rand_part = str(random.randint(1000, 9999))
    return date_part + rand_part


@router.post("/checkout", dependencies=[Depends(csrf_protect)])
async def checkout(
    request: Request,
    background_tasks: BackgroundTasks,
    customer_email: str = Form(...),
    shipping_name: str = Form(...),
    shipping_street: str = Form(...),
    shipping_city: str = Form(...),
    shipping_zip: str = Form(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    raw_cart = cart_service.get_cart(request)
    if not raw_cart:
        raise HTTPException(status_code=400, detail="Košík je prázdný")

    enriched, total = cart_service.calculate_total(raw_cart, db)
    if not enriched:
        raise HTTPException(status_code=400, detail="Žádné platné položky v košíku")

    shipping_address = f"{shipping_name}\n{shipping_street}\n{shipping_zip} {shipping_city}"

    order = Order(
        user_id=current_user.id if current_user else None,
        total_price=total,
        shipping_address=shipping_address,
        customer_email=customer_email.lower(),
        var_symbol=_generate_var_symbol(),
        payment_status=PaymentStatus.pending,
        fulfillment_status=FulfillmentStatus.new,
    )
    db.add(order)
    db.flush()

    for item in enriched:
        db.add(OrderItem(
            order_id=order.id,
            product_id=item.get("product_id"),
            custom_design_id=item.get("design_id"),
            product_name_snapshot=item["name"],
            price_snapshot=item["unit_price"],
            variant_snapshot={"name": item.get("variant_name")} if item.get("variant_name") else None,
            quantity=item["qty"],
        ))

    db.commit()
    cart_service.clear_cart(request)

    from app.email import send_order_confirmation
    background_tasks.add_task(send_order_confirmation, order.id, customer_email, order.var_symbol, total)

    return RedirectResponse(url=f"/orders/{order.id}/confirmation", status_code=303)


