"""
Košík uložený v server-side session (Starlette SessionMiddleware).

Struktura session["cart"]:
[
  {"type": "product",  "product_id": 1, "variant_id": 2,  "qty": 1},
  {"type": "design",   "design_id": 5,                    "qty": 1},
]
"""
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models import CustomDesign, Product, ProductVariant

CART_KEY = "cart"


def get_cart(request: Request) -> list[dict]:
    return request.session.get(CART_KEY, [])


def _save_cart(request: Request, cart: list[dict]) -> None:
    request.session[CART_KEY] = cart


def add_product(request: Request, product_id: int, qty: int = 1, variant_id: Optional[int] = None) -> None:
    cart = get_cart(request)
    for item in cart:
        if item["type"] == "product" and item["product_id"] == product_id and item.get("variant_id") == variant_id:
            item["qty"] += qty
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
