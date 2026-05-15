"""
Košík uložený v server-side session (Starlette SessionMiddleware).

Struktura session["cart"]:
[
  {"type": "product",  "product_id": 1, "variant_id": 2,  "qty": 1},
  {"type": "design",   "design_id": 5,                    "qty": 1},
]
"""
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.models import ConfiguratorType, CustomDesign, Modifier, Product, ProductVariant

CART_KEY = "cart"


def calculate_design_price(
    db: Session,
    configurator_type_id: int,
    configuration: dict,
) -> float:
    """
    Server-side výpočet ceny custom designu.
    NIKDY nepřijímat cenu od klienta — vždy spočítat zde.

    configuration: {dimension_id: modifier_id, ...}
    """
    ctype = db.get(ConfiguratorType, configurator_type_id)
    if not ctype or not ctype.is_active:
        raise HTTPException(400, "Neplatný typ konfigurátoru")

    # Validní dimension_ids pro tento configurator_type
    valid_dimension_ids = {d.id for d in ctype.dimensions}

    total = Decimal(str(ctype.base_price))

    for dim_id_raw, mod_id_raw in configuration.items():
        try:
            dim_id = int(dim_id_raw)
            mod_id = int(mod_id_raw)
        except (ValueError, TypeError):
            raise HTTPException(400, "Neplatný formát konfigurace")

        # Bezpečnostní check: dimension musí patřit tomuto configurator_type
        if dim_id not in valid_dimension_ids:
            raise HTTPException(400, f"Dimenze {dim_id} nepatří k tomuto konfigurátoru")

        # Modifier musí existovat A patřit této dimenzi
        modifier = db.get(Modifier, mod_id)
        if not modifier or modifier.dimension_id != dim_id:
            raise HTTPException(400, f"Modifikátor {mod_id} nepatří k dimenzi {dim_id}")

        total += Decimal(str(modifier.price_modifier))

    return float(round(total, 2))


def get_cart(request: Request) -> list[dict]:
    return request.session.get(CART_KEY, [])


def _save_cart(request: Request, cart: list[dict]) -> None:
    request.session[CART_KEY] = cart


_QTY_MAX = 99


def add_product(request: Request, product_id: int, qty: int = 1, variant_id: Optional[int] = None) -> None:
    if qty < 1 or qty > _QTY_MAX:
        raise HTTPException(400, f"Množství musí být 1–{_QTY_MAX}")
    cart = get_cart(request)
    for item in cart:
        if item["type"] == "product" and item["product_id"] == product_id and item.get("variant_id") == variant_id:
            new_qty = item["qty"] + qty
            item["qty"] = min(new_qty, _QTY_MAX)  # cap na maximum
            _save_cart(request, cart)
            return
    cart.append({"type": "product", "product_id": product_id, "variant_id": variant_id, "qty": qty})
    _save_cart(request, cart)


def add_design(request: Request, design_id: int) -> None:
    cart = get_cart(request)
    for item in cart:
        if item["type"] == "design" and item["design_id"] == design_id:
            return  # design je unikátní, nepřidávat dvakrát
    cart.append({"type": "design", "design_id": design_id, "qty": 1})
    _save_cart(request, cart)


def remove_item(request: Request, index: int) -> None:
    cart = get_cart(request)
    if 0 <= index < len(cart):
        cart.pop(index)
    _save_cart(request, cart)


def clear_cart(request: Request) -> None:
    request.session[CART_KEY] = []


def calculate_total(cart: list[dict], db: Session) -> tuple[list[dict], float]:
    """Vrátí (obohacené položky s názvy a cenami, celková cena)."""
    enriched = []
    total = 0.0

    for item in cart:
        if item["type"] == "product":
            product = db.get(Product, item["product_id"])
            if not product or not product.is_active:
                continue
            price = float(product.base_price)
            variant_name = None
            if item.get("variant_id"):
                variant = db.get(ProductVariant, item["variant_id"])
                if variant:
                    price += float(variant.price_modifier)
                    variant_name = variant.name_cs
            line_total = price * item["qty"]
            total += line_total
            enriched.append({**item, "name": product.title_cs, "unit_price": price,
                              "line_total": line_total, "variant_name": variant_name})

        elif item["type"] == "design":
            design = db.get(CustomDesign, item["design_id"])
            if not design:
                continue
            price = float(design.final_price)
            total += price
            enriched.append({**item, "name": f"Šperk na míru #{design.id}",
                              "unit_price": price, "line_total": price})

    return enriched, round(total, 2)
