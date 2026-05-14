import json
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from app import cart as cart_service
from app.csrf import csrf_protect
from app.database import get_db
from app.dependencies import get_current_user_optional
from app.jinja import templates
from app.models import Category, ConfiguratorType, CustomDesign, Product, Tag, User
from app.qr import generate_qr_base64
from app.template_context import base_ctx
from sqlalchemy.orm import Session

router = APIRouter()


# ── Home ──────────────────────────────────────────────────────
@router.get("/")
async def home(request: Request, db: Session = Depends(get_db),
               current_user: Optional[User] = Depends(get_current_user_optional)):
    categories = db.query(Category).all()
    featured = db.query(Product).filter(Product.is_active == True).limit(4).all()
    return templates.TemplateResponse("index.html", {
        **base_ctx(request, current_user),
        "categories": categories,
        "featured_products": featured,
    })


# ── Katalog ───────────────────────────────────────────────────
@router.get("/catalog")
async def catalog(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    category: Optional[str] = Query(default=None),
    tags: List[str] = Query(default=[]),
):
    categories = db.query(Category).all()
    all_tags = db.query(Tag).order_by(Tag.name_cs).all()

    q = db.query(Product).filter(Product.is_active == True)

    if category:
        cat_obj = next((c for c in categories if c.slug == category), None)
        if cat_obj:
            q = q.filter(Product.category_id == cat_obj.id)
        else:
            category = None

    if tags:
        q = q.filter(Product.tags.any(Tag.slug.in_(tags)))

    products = q.all()

    return templates.TemplateResponse("catalog.html", {
        **base_ctx(request, current_user),
        "categories": categories,
        "all_tags": all_tags,
        "products": products,
        "selected_category": category or "",
        "selected_tags": tags,
    })


@router.get("/category/{slug}")
async def category(slug: str, request: Request, db: Session = Depends(get_db),
                   current_user: Optional[User] = Depends(get_current_user_optional)):
    cat = db.query(Category).filter(Category.slug == slug).first()
    if not cat:
        raise HTTPException(404)
    products = db.query(Product).filter(
        Product.category_id == cat.id, Product.is_active == True
    ).all()
    return templates.TemplateResponse("category.html", {
        **base_ctx(request, current_user),
        "category": cat,
        "products": products,
    })


# ── Sety ──────────────────────────────────────────────────────
@router.get("/sets")
async def sets_page(request: Request, db: Session = Depends(get_db),
                    current_user: Optional[User] = Depends(get_current_user_optional)):
    sets = db.query(Tag).filter(Tag.is_collection == True).order_by(Tag.name_cs).all()
    return templates.TemplateResponse("sets/list.html", {
        **base_ctx(request, current_user),
        "sets": sets,
    })


@router.get("/sets/{slug}")
async def set_detail(slug: str, request: Request, db: Session = Depends(get_db),
                     current_user: Optional[User] = Depends(get_current_user_optional)):
    tag = db.query(Tag).filter(Tag.slug == slug, Tag.is_collection == True).first()
    if not tag:
        raise HTTPException(404)
    products = [p for p in tag.products if p.is_active]
    return templates.TemplateResponse("sets/detail.html", {
        **base_ctx(request, current_user),
        "set": tag,
        "products": products,
    })


# ── Produkt ───────────────────────────────────────────────────
@router.get("/products/{slug}")
async def product_detail(slug: str, request: Request, db: Session = Depends(get_db),
                         current_user: Optional[User] = Depends(get_current_user_optional)):
    product = db.query(Product).filter(Product.slug == slug, Product.is_active == True).first()
    if not product:
        raise HTTPException(404)
    return templates.TemplateResponse("product.html", {
        **base_ctx(request, current_user),
        "product": product,
    })


# ── Košík ─────────────────────────────────────────────────────
@router.get("/cart")
async def cart_page(request: Request, db: Session = Depends(get_db),
                    current_user: Optional[User] = Depends(get_current_user_optional)):
    raw = cart_service.get_cart(request)
    items, total = cart_service.calculate_total(raw, db)
    return templates.TemplateResponse("cart.html", {
        **base_ctx(request, current_user),
        "items": items,
        "total": total,
    })


# ── Checkout ──────────────────────────────────────────────────
@router.get("/checkout")
async def checkout_page(request: Request, db: Session = Depends(get_db),
                        current_user: Optional[User] = Depends(get_current_user_optional)):
    raw = cart_service.get_cart(request)
    if not raw:
        return RedirectResponse("/cart", status_code=302)
    items, total = cart_service.calculate_total(raw, db)
    return templates.TemplateResponse("checkout.html", {
        **base_ctx(request, current_user),
        "items": items,
        "total": total,
    })


# ── Konfirmace objednávky ─────────────────────────────────────
@router.get("/orders/{order_id}/confirmation")
async def order_confirmation_page(order_id: int, request: Request,
                                  db: Session = Depends(get_db),
                                  current_user: Optional[User] = Depends(get_current_user_optional)):
    from app.models import Order
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404)
    if current_user and order.user_id and order.user_id != current_user.id:
        raise HTTPException(403)
    qr_b64 = generate_qr_base64(float(order.total_price), order.var_symbol)
    return templates.TemplateResponse("confirmation.html", {
        **base_ctx(request, current_user),
        "order": order,
        "qr_b64": qr_b64,
    })


# ── Konfigurátor ──────────────────────────────────────────────
@router.get("/configurator")
async def configurator_page(request: Request, db: Session = Depends(get_db),
                             current_user: Optional[User] = Depends(get_current_user_optional)):
    types = db.query(ConfiguratorType).filter(ConfiguratorType.is_active == True).all()
    return templates.TemplateResponse("configurator.html", {
        **base_ctx(request, current_user),
        "configurator_types": types,
    })


@router.post("/configurator/save", dependencies=[Depends(csrf_protect)])
async def configurator_save(
    request: Request,
    configurator_type_id: int = Form(...),
    configuration_json: str = Form(...),
    final_price: float = Form(...),
    customer_note: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
):
    try:
        config = json.loads(configuration_json)
    except Exception:
        raise HTTPException(400, "Invalid configuration")

    design = CustomDesign(
        configurator_type_id=configurator_type_id,
        configuration_json=config,
        customer_note=customer_note or None,
        final_price=round(final_price, 2),
    )
    db.add(design)
    db.commit()
    db.refresh(design)

    cart_service.add_design(request, design.id)
    return RedirectResponse("/cart", status_code=303)


# ── Přepnutí jazyka ───────────────────────────────────────────
@router.post("/set-lang/{lang}", dependencies=[Depends(csrf_protect)])
async def set_lang(lang: str, request: Request):
    if lang in ("cs", "en"):
        request.session["lang"] = lang
    referer = request.headers.get("referer", "/")
    return RedirectResponse(referer, status_code=303)
