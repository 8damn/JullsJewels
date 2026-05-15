import logging
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import cart as cart_service
from app.auth import create_confirmation_token
from app.csrf import csrf_protect
from app.database import get_db
from app.dependencies import get_current_user_optional
from app.models import FulfillmentStatus, Order, OrderItem, PaymentStatus, ProductVariant, User

router = APIRouter(prefix="/orders", tags=["orders"])
logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _generate_var_symbol(order_id: int) -> str:
    """Variabilní symbol odvozený z order_id — zaručeně unikátní, bez kolizí.
    Formát: YYMMDD + order_id zero-padded na 4 místa (pro malé e-shopy stačí).
    Pokud order_id > 9999, použije se celé číslo."""
    date_part = datetime.now(timezone.utc).strftime("%y%m%d")
    id_part = str(order_id).zfill(4)
    return date_part + id_part


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
    # ── Validace vstupů ────────────────────────────────────────────────────
    customer_email = customer_email.strip().lower()
    if not _EMAIL_RE.match(customer_email):
        raise HTTPException(400, "Neplatná e-mailová adresa")

    for field, name in [
        (shipping_name, "Jméno"),
        (shipping_street, "Ulice"),
        (shipping_city, "Město"),
        (shipping_zip, "PSČ"),
    ]:
        if not field or not field.strip():
            raise HTTPException(400, f"{name} je povinné pole")

    # ── Košík ──────────────────────────────────────────────────────────────
    raw_cart = cart_service.get_cart(request)
    if not raw_cart:
        raise HTTPException(400, "Košík je prázdný")

    enriched, total = cart_service.calculate_total(raw_cart, db)
    if not enriched:
        raise HTTPException(400, "Žádné platné položky v košíku")

    shipping_address = (
        f"{shipping_name.strip()}\n"
        f"{shipping_street.strip()}\n"
        f"{shipping_zip.strip()} {shipping_city.strip()}"
    )

    # ── Atomická transakce: stock check + decrement + create order ─────────
    # SQLite serializes writes — BEGIN IMMEDIATE zajistí, že dva souběžné
    # checkouty nemohou oba "vidět" stock=1 a oba ho dekrementovat.
    try:
        db.execute(text("BEGIN IMMEDIATE"))
    except Exception:
        # Jiná transakce již drží zámek — fallback, SQLAlchemy session zvládne
        pass

    try:
        # Stock check + decrement pro varianty
        for item in enriched:
            if item["type"] != "product":
                continue
            variant_id = item.get("variant_id")
            if not variant_id:
                continue  # produkt bez varianty → sklad se nesleduje

            variant = db.get(ProductVariant, variant_id)
            if not variant:
                raise HTTPException(400, f"Varianta produktu '{item['name']}' neexistuje")

            needed = item["qty"]
            if variant.stock < needed:
                available = variant.stock
                raise HTTPException(
                    400,
                    f"Produkt '{item['name']}' ({variant.name_cs}) není dostatečně skladem. "
                    f"Dostupné množství: {available}",
                )
            variant.stock -= needed

        # Vytvoř objednávku s dočasným var_symbol (nahradíme po flush())
        order = Order(
            user_id=current_user.id if current_user else None,
            total_price=total,
            shipping_address=shipping_address,
            customer_email=customer_email,
            var_symbol="PENDING",  # dočasné — nahrazeno níže
            payment_status=PaymentStatus.pending,
            fulfillment_status=FulfillmentStatus.new,
        )
        db.add(order)
        db.flush()  # získáme order.id před commitem

        # var_symbol odvozený z order.id → zaručeně unikátní
        order.var_symbol = _generate_var_symbol(order.id)

        # Položky objednávky
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

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error("Checkout IntegrityError: %s", e)
        raise HTTPException(500, "Chyba při zpracování objednávky. Zkuste to prosím znovu.")
    except Exception as e:
        db.rollback()
        logger.error("Checkout error: %s", e)
        raise HTTPException(500, "Chyba při zpracování objednávky.")

    # ── Košík vymazat, e-mail odeslat, přesměrovat ────────────────────────
    cart_service.clear_cart(request)

    token = create_confirmation_token(order.id)

    from app.email import send_order_confirmation
    background_tasks.add_task(
        send_order_confirmation,
        order.id,
        customer_email,
        order.var_symbol,
        total,
        token,
    )

    return RedirectResponse(url=f"/orders/{order.id}/confirmation?t={token}", status_code=303)
