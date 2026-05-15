import json
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from app import cart as cart_service
from app.auth import verify_confirmation_token
from app.csrf import csrf_protect
from app.database import get_db
from app.dependencies import get_current_user_optional
from app.jinja import templates
from app.models import Attribute, AttributeOption, Category, ConfiguratorType, CustomDesign, Product, Tag, User
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
    opts: List[int] = Query(default=[]),
    price_min_raw: Optional[str] = Query(default=None, alias="price_min"),
    price_max_raw: Optional[str] = Query(default=None, alias="price_max"),
):
    price_min = float(price_min_raw) if price_min_raw and price_min_raw.strip() else None
    price_max = float(price_max_raw) if price_max_raw and price_max_raw.strip() else None

    categories = db.query(Category).all()
    all_tags = db.query(Tag).order_by(Tag.name_cs).all()
    all_attributes = db.query(Attribute).order_by(Attribute.name_cs).all()

    q = db.query(Product).filter(Product.is_active == True)

    if category:
        cat_obj = next((c for c in categories if c.slug == category), None)
        if cat_obj:
            q = q.filter(Product.category_id == cat_obj.id)
        else:
            category = None

    if tags:
        q = q.filter(Product.tags.any(Tag.slug.in_(tags)))

    if price_min is not None:
        q = q.filter(Product.base_price >= price_min)
    if price_max is not None:
        q = q.filter(Product.base_price <= price_max)

    if opts:
        selected_options = db.query(AttributeOption).filter(AttributeOption.id.in_(opts)).all()
        by_attr: dict[int, list[int]] = {}
        for opt in selected_options:
            by_attr.setdefault(opt.attribute_id, []).append(opt.id)
        for opt_ids in by_attr.values():
            q = q.filter(Product.attribute_options.any(AttributeOption.id.in_(opt_ids)))

    products = q.all()

    from sqlalchemy import func as sqlfunc
    catalog_max_val = db.query(sqlfunc.max(Product.base_price)).filter(Product.is_active == True).scalar()
    catalog_max = int(catalog_max_val) + 1 if catalog_max_val else 10000

    return templates.TemplateResponse("catalog.html", {
        **base_ctx(request, current_user),
        "categories": categories,
        "all_tags": all_tags,
        "all_attributes": all_attributes,
        "products": products,
        "selected_category": category or "",
        "selected_tags": tags,
        "selected_opts": opts,
        "price_min": price_min,
        "price_max": price_max,
        "catalog_max": catalog_max,
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
async def order_confirmation_page(
    order_id: int,
    request: Request,
    t: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    from app.models import Order
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404)

    # Autorizace: buď je to vlastník (přihlášený), nebo má platný signed token (host z e-mailu).
    is_owner = current_user and order.user_id and order.user_id == current_user.id
    has_valid_token = bool(t) and verify_confirmation_token(t, order_id)

    if not is_owner and not has_valid_token:
        raise HTTPException(403, "Nemáte přístup k této objednávce")

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
    customer_note: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
):
    try:
        config = json.loads(configuration_json)
    except Exception:
        raise HTTPException(400, "Invalid configuration")

    if not isinstance(config, dict):
        raise HTTPException(400, "Konfigurace musí být objekt")

    # Cena se počítá SERVEROVĚ — klient ji NIKDY neposílá
    final_price = cart_service.calculate_design_price(db, configurator_type_id, config)

    design = CustomDesign(
        configurator_type_id=configurator_type_id,
        configuration_json=config,
        customer_note=customer_note or None,
        final_price=final_price,
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
