from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Cookie, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import decode_access_token
from app.csrf import csrf_protect
from app.database import get_db
from app.jinja import templates
from app.models import (
    Attribute, AttributeOption,
    BlogPost, Category, ConfiguratorDimension, ConfiguratorType,
    FulfillmentStatus, Modifier, Order, PaymentStatus,
    Product, ProductImage, ProductVariant, Tag, User, UserRole,
)
from app.template_context import base_ctx, flash
from app.uploads import save_image

router = APIRouter(prefix="/admin")


async def _require_admin(
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(default=None),
) -> User:
    from fastapi.responses import RedirectResponse as _Redirect
    payload = decode_access_token(access_token) if access_token else None
    # Odmítnout refresh tokeny — smí se použít jen access tokeny
    if not payload or payload.get("type") == "refresh":
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/auth/login"},
        )
    try:
        user = db.get(User, int(payload["sub"]))
    except (KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/auth/login"},
        )
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/auth/login"},
        )
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user


def _ctx(request: Request, user: User) -> dict:
    return base_ctx(request, user)


# ── Dashboard ─────────────────────────────────────────────────

@router.get("")
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    stats = {
        "orders_total": db.query(func.count(Order.id)).scalar() or 0,
        "orders_pending": db.query(func.count(Order.id)).filter(Order.payment_status == PaymentStatus.pending).scalar() or 0,
        "orders_paid": db.query(func.count(Order.id)).filter(Order.payment_status == PaymentStatus.paid).scalar() or 0,
        "revenue": db.query(func.sum(Order.total_price)).filter(Order.payment_status == PaymentStatus.paid).scalar() or 0,
        "products": db.query(func.count(Product.id)).scalar() or 0,
        "blog_posts": db.query(func.count(BlogPost.id)).scalar() or 0,
    }
    recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(10).all()
    return templates.TemplateResponse("admin/dashboard.html", {
        **_ctx(request, current_user),
        "stats": stats,
        "recent_orders": recent_orders,
    })


# ── Produkty ──────────────────────────────────────────────────

@router.get("/products")
async def products_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    products = db.query(Product).order_by(Product.id.desc()).all()
    return templates.TemplateResponse("admin/products/list.html", {
        **_ctx(request, current_user),
        "products": products,
    })


@router.get("/products/new")
async def product_new_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    categories = db.query(Category).all()
    all_tags = db.query(Tag).order_by(Tag.name_cs).all()
    all_attributes = db.query(Attribute).order_by(Attribute.name_cs).all()
    return templates.TemplateResponse("admin/products/form.html", {
        **_ctx(request, current_user),
        "product": None,
        "categories": categories,
        "all_tags": all_tags,
        "all_attributes": all_attributes,
    })


@router.post("/products/new", dependencies=[Depends(csrf_protect)])
async def product_new(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    title_cs: str = Form(...),
    title_en: str = Form(...),
    slug: str = Form(...),
    base_price: float = Form(...),
    category_id: Optional[str] = Form(default=None),
    description_cs: Optional[str] = Form(default=None),
    description_en: Optional[str] = Form(default=None),
    is_active: Optional[str] = Form(default=None),
    tag_ids: List[str] = Form(default=[]),
    opt_ids: List[str] = Form(default=[]),
):
    cat_id = int(category_id) if category_id else None
    product = Product(
        title_cs=title_cs,
        title_en=title_en,
        slug=slug,
        base_price=base_price,
        category_id=cat_id,
        description_cs=description_cs or None,
        description_en=description_en or None,
        is_active=is_active is not None,
    )
    db.add(product)
    db.flush()
    product.tags = db.query(Tag).filter(Tag.id.in_([int(x) for x in tag_ids])).all() if tag_ids else []
    product.attribute_options = db.query(AttributeOption).filter(AttributeOption.id.in_([int(x) for x in opt_ids])).all() if opt_ids else []
    db.commit()
    db.refresh(product)
    flash(request, "Produkt byl vytvořen.")
    return RedirectResponse(f"/admin/products/{product.id}/edit", status_code=303)


@router.get("/products/{product_id}/edit")
async def product_edit_form(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404)
    categories = db.query(Category).all()
    all_tags = db.query(Tag).order_by(Tag.name_cs).all()
    all_attributes = db.query(Attribute).order_by(Attribute.name_cs).all()
    return templates.TemplateResponse("admin/products/form.html", {
        **_ctx(request, current_user),
        "product": product,
        "categories": categories,
        "all_tags": all_tags,
        "all_attributes": all_attributes,
    })


@router.post("/products/{product_id}/edit", dependencies=[Depends(csrf_protect)])
async def product_edit(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    title_cs: str = Form(...),
    title_en: str = Form(...),
    slug: str = Form(...),
    base_price: float = Form(...),
    category_id: Optional[str] = Form(default=None),
    description_cs: Optional[str] = Form(default=None),
    description_en: Optional[str] = Form(default=None),
    is_active: Optional[str] = Form(default=None),
    images: List[UploadFile] = File(default=[]),
    v_name_cs: Optional[str] = Form(default=None),
    v_name_en: Optional[str] = Form(default=None),
    v_price_modifier: float = Form(default=0),
    v_stock: int = Form(default=0),
    tag_ids: List[str] = Form(default=[]),
    opt_ids: List[str] = Form(default=[]),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404)

    product.title_cs = title_cs
    product.title_en = title_en
    product.slug = slug
    product.base_price = base_price
    product.category_id = int(category_id) if category_id else None
    product.description_cs = description_cs or None
    product.description_en = description_en or None
    product.is_active = is_active is not None

    for file in images:
        if file.filename:
            url = await save_image(file)
            img = ProductImage(product_id=product.id, image_url=url)
            db.add(img)

    if v_name_cs and v_name_cs.strip():
        variant = ProductVariant(
            product_id=product.id,
            name_cs=v_name_cs.strip(),
            name_en=(v_name_en or v_name_cs).strip(),
            price_modifier=v_price_modifier,
            stock=v_stock,
        )
        db.add(variant)

    product.tags = db.query(Tag).filter(Tag.id.in_([int(x) for x in tag_ids])).all() if tag_ids else []
    product.attribute_options = db.query(AttributeOption).filter(AttributeOption.id.in_([int(x) for x in opt_ids])).all() if opt_ids else []

    db.commit()
    flash(request, "Produkt byl uložen.")
    return RedirectResponse(f"/admin/products/{product_id}/edit", status_code=303)


@router.post("/products/{product_id}/toggle", dependencies=[Depends(csrf_protect)])
async def product_toggle(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404)
    product.is_active = not product.is_active
    db.commit()
    return RedirectResponse("/admin/products", status_code=303)


@router.post("/products/{product_id}/delete", dependencies=[Depends(csrf_protect)])
async def product_delete(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404)
    db.delete(product)
    db.commit()
    flash(request, "Produkt byl smazán.", "warning")
    return RedirectResponse("/admin/products", status_code=303)


@router.post("/products/{product_id}/image/{img_id}/replace", dependencies=[Depends(csrf_protect)])
async def product_image_replace(
    product_id: int,
    img_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    image: UploadFile = File(...),
):
    img = db.get(ProductImage, img_id)
    if not img or img.product_id != product_id:
        raise HTTPException(404)
    url = await save_image(image)
    img.image_url = url
    db.commit()
    flash(request, "Obrázek nahrazen.")
    return RedirectResponse(f"/admin/products/{product_id}/edit", status_code=303)


@router.post("/products/{product_id}/image/{img_id}/delete", dependencies=[Depends(csrf_protect)])
async def product_image_delete(
    product_id: int,
    img_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    img = db.get(ProductImage, img_id)
    if not img or img.product_id != product_id:
        raise HTTPException(404)
    db.delete(img)
    db.commit()
    return RedirectResponse(f"/admin/products/{product_id}/edit", status_code=303)


@router.post("/variants/{variant_id}/delete", dependencies=[Depends(csrf_protect)])
async def variant_delete(
    variant_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    variant = db.get(ProductVariant, variant_id)
    if not variant:
        raise HTTPException(404)
    product_id = variant.product_id
    db.delete(variant)
    db.commit()
    return RedirectResponse(f"/admin/products/{product_id}/edit", status_code=303)


# ── Kategorie ─────────────────────────────────────────────────

@router.get("/categories")
async def categories_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    categories = db.query(Category).all()
    return templates.TemplateResponse("admin/categories.html", {
        **_ctx(request, current_user),
        "categories": categories,
    })


@router.post("/categories/add", dependencies=[Depends(csrf_protect)])
async def category_add(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    title_cs: str = Form(...),
    title_en: str = Form(...),
    slug: str = Form(...),
):
    cat = Category(title_cs=title_cs, title_en=title_en, slug=slug)
    db.add(cat)
    db.commit()
    flash(request, "Kategorie přidána.")
    return RedirectResponse("/admin/categories", status_code=303)


@router.post("/categories/{cat_id}/delete", dependencies=[Depends(csrf_protect)])
async def category_delete(
    cat_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    cat = db.get(Category, cat_id)
    if not cat:
        raise HTTPException(404)
    for product in cat.products:
        product.category_id = None
    db.delete(cat)
    db.commit()
    flash(request, "Kategorie smazána.", "warning")
    return RedirectResponse("/admin/categories", status_code=303)


# ── Objednávky ────────────────────────────────────────────────

@router.get("/orders")
async def orders_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    payment: Optional[str] = None,
):
    q = db.query(Order)
    if payment in ("pending", "paid", "failed"):
        q = q.filter(Order.payment_status == payment)
    orders = q.order_by(Order.created_at.desc()).all()
    return templates.TemplateResponse("admin/orders/list.html", {
        **_ctx(request, current_user),
        "orders": orders,
        "payment_filter": payment or "",
    })


@router.get("/orders/{order_id}")
async def order_detail(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404)
    return templates.TemplateResponse("admin/orders/detail.html", {
        **_ctx(request, current_user),
        "order": order,
    })


@router.post("/orders/{order_id}/status", dependencies=[Depends(csrf_protect)])
async def order_status(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    payment_status: str = Form(...),
    fulfillment_status: str = Form(...),
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404)
    try:
        order.payment_status = PaymentStatus(payment_status)
        order.fulfillment_status = FulfillmentStatus(fulfillment_status)
    except ValueError:
        raise HTTPException(400, "Neplatný stav")
    db.commit()
    flash(request, "Stav objednávky uložen.")
    return RedirectResponse(f"/admin/orders/{order_id}", status_code=303)


# ── Blog ──────────────────────────────────────────────────────

@router.get("/blog")
async def blog_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    posts = db.query(BlogPost).order_by(BlogPost.created_at.desc()).all()
    return templates.TemplateResponse("admin/blog/list.html", {
        **_ctx(request, current_user),
        "posts": posts,
    })


@router.get("/blog/new")
async def blog_new_form(
    request: Request,
    current_user: User = Depends(_require_admin),
):
    return templates.TemplateResponse("admin/blog/form.html", {
        **_ctx(request, current_user),
        "post": None,
    })


@router.post("/blog/new", dependencies=[Depends(csrf_protect)])
async def blog_new(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    title_cs: str = Form(...),
    title_en: str = Form(...),
    slug: str = Form(...),
    excerpt_cs: Optional[str] = Form(default=None),
    excerpt_en: Optional[str] = Form(default=None),
    content_cs: Optional[str] = Form(default=None),
    content_en: Optional[str] = Form(default=None),
    cover_image_url: Optional[str] = Form(default=None),
    seo_description_cs: Optional[str] = Form(default=None),
    seo_description_en: Optional[str] = Form(default=None),
    is_published: Optional[str] = Form(default=None),
):
    published = is_published is not None
    post = BlogPost(
        title_cs=title_cs,
        title_en=title_en,
        slug=slug,
        excerpt_cs=excerpt_cs or None,
        excerpt_en=excerpt_en or None,
        content_cs=content_cs or None,
        content_en=content_en or None,
        cover_image_url=cover_image_url or None,
        seo_description_cs=seo_description_cs or None,
        seo_description_en=seo_description_en or None,
        is_published=published,
        published_at=datetime.utcnow() if published else None,
    )
    db.add(post)
    db.commit()
    flash(request, "Článek byl vytvořen.")
    return RedirectResponse("/admin/blog", status_code=303)


@router.get("/blog/{post_id}/edit")
async def blog_edit_form(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    post = db.get(BlogPost, post_id)
    if not post:
        raise HTTPException(404)
    return templates.TemplateResponse("admin/blog/form.html", {
        **_ctx(request, current_user),
        "post": post,
    })


@router.post("/blog/{post_id}/edit", dependencies=[Depends(csrf_protect)])
async def blog_edit(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    title_cs: str = Form(...),
    title_en: str = Form(...),
    slug: str = Form(...),
    excerpt_cs: Optional[str] = Form(default=None),
    excerpt_en: Optional[str] = Form(default=None),
    content_cs: Optional[str] = Form(default=None),
    content_en: Optional[str] = Form(default=None),
    cover_image_url: Optional[str] = Form(default=None),
    seo_description_cs: Optional[str] = Form(default=None),
    seo_description_en: Optional[str] = Form(default=None),
    is_published: Optional[str] = Form(default=None),
):
    post = db.get(BlogPost, post_id)
    if not post:
        raise HTTPException(404)

    published = is_published is not None
    post.title_cs = title_cs
    post.title_en = title_en
    post.slug = slug
    post.excerpt_cs = excerpt_cs or None
    post.excerpt_en = excerpt_en or None
    post.content_cs = content_cs or None
    post.content_en = content_en or None
    post.cover_image_url = cover_image_url or None
    post.seo_description_cs = seo_description_cs or None
    post.seo_description_en = seo_description_en or None
    if published and not post.is_published:
        post.published_at = datetime.utcnow()
    post.is_published = published

    db.commit()
    flash(request, "Článek byl uložen.")
    return RedirectResponse(f"/admin/blog/{post_id}/edit", status_code=303)


@router.post("/blog/{post_id}/delete", dependencies=[Depends(csrf_protect)])
async def blog_delete(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    post = db.get(BlogPost, post_id)
    if not post:
        raise HTTPException(404)
    db.delete(post)
    db.commit()
    flash(request, "Článek byl smazán.", "warning")
    return RedirectResponse("/admin/blog", status_code=303)


@router.post("/blog/{post_id}/toggle", dependencies=[Depends(csrf_protect)])
async def blog_toggle(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    post = db.get(BlogPost, post_id)
    if not post:
        raise HTTPException(404)
    post.is_published = not post.is_published
    if post.is_published and not post.published_at:
        post.published_at = datetime.utcnow()
    db.commit()
    return RedirectResponse("/admin/blog", status_code=303)


# ── Konfigurátor ──────────────────────────────────────────────

@router.get("/configurator")
async def configurator(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    types = db.query(ConfiguratorType).all()
    return templates.TemplateResponse("admin/configurator.html", {
        **_ctx(request, current_user),
        "configurator_types": types,
    })


@router.post("/configurator/types/add", dependencies=[Depends(csrf_protect)])
async def configurator_type_add(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    name_cs: str = Form(...),
    name_en: str = Form(...),
    slug: str = Form(...),
    base_price: float = Form(default=0),
):
    ct = ConfiguratorType(name_cs=name_cs, name_en=name_en, slug=slug, base_price=base_price)
    db.add(ct)
    db.commit()
    flash(request, "Typ přidán.")
    return RedirectResponse("/admin/configurator", status_code=303)


@router.post("/configurator/types/{type_id}/set-layout", dependencies=[Depends(csrf_protect)])
async def configurator_type_set_layout(
    type_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    layout_mode: str = Form(...),
):
    ct = db.get(ConfiguratorType, type_id)
    if not ct:
        raise HTTPException(404)
    if layout_mode in ("layered", "bead_chain"):
        ct.layout_mode = layout_mode
        db.commit()
    return RedirectResponse("/admin/configurator", status_code=303)


@router.post("/configurator/types/{type_id}/toggle", dependencies=[Depends(csrf_protect)])
async def configurator_type_toggle(
    type_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    ct = db.get(ConfiguratorType, type_id)
    if not ct:
        raise HTTPException(404)
    ct.is_active = not ct.is_active
    db.commit()
    return RedirectResponse("/admin/configurator", status_code=303)


@router.post("/configurator/types/{type_id}/delete", dependencies=[Depends(csrf_protect)])
async def configurator_type_delete(
    type_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    ct = db.get(ConfiguratorType, type_id)
    if not ct:
        raise HTTPException(404)
    db.delete(ct)
    db.commit()
    flash(request, "Typ smazán.", "warning")
    return RedirectResponse("/admin/configurator", status_code=303)


@router.post("/configurator/dimensions/add", dependencies=[Depends(csrf_protect)])
async def configurator_dimension_add(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    configurator_type_id: int = Form(...),
    name_cs: str = Form(...),
    name_en: str = Form(...),
    slug: str = Form(...),
    sort_order: int = Form(default=0),
    is_required: Optional[str] = Form(default=None),
):
    dim = ConfiguratorDimension(
        configurator_type_id=configurator_type_id,
        name_cs=name_cs,
        name_en=name_en,
        slug=slug,
        sort_order=sort_order,
        is_required=is_required is not None,
    )
    db.add(dim)
    db.commit()
    flash(request, "Dimenze přidána.")
    return RedirectResponse("/admin/configurator", status_code=303)


@router.post("/configurator/dimensions/{dim_id}/delete", dependencies=[Depends(csrf_protect)])
async def configurator_dimension_delete(
    dim_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    dim = db.get(ConfiguratorDimension, dim_id)
    if not dim:
        raise HTTPException(404)
    db.delete(dim)
    db.commit()
    flash(request, "Dimenze smazána.", "warning")
    return RedirectResponse("/admin/configurator", status_code=303)


@router.post("/configurator/modifiers/add", dependencies=[Depends(csrf_protect)])
async def configurator_modifier_add(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    dimension_id: int = Form(...),
    name_cs: str = Form(...),
    name_en: str = Form(...),
    price_modifier: float = Form(default=0),
    is_default: Optional[str] = Form(default=None),
    color_hex: Optional[str] = Form(default=None),
    bead_count: Optional[int] = Form(default=None),
):
    mod = Modifier(
        dimension_id=dimension_id,
        name_cs=name_cs,
        name_en=name_en,
        price_modifier=price_modifier,
        is_default=is_default is not None,
        color_hex=color_hex or None,
        bead_count=bead_count,
    )
    db.add(mod)
    db.commit()
    flash(request, "Volba přidána.")
    return RedirectResponse("/admin/configurator", status_code=303)


@router.post("/configurator/modifiers/{mod_id}/delete", dependencies=[Depends(csrf_protect)])
async def configurator_modifier_delete(
    mod_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    mod = db.get(Modifier, mod_id)
    if not mod:
        raise HTTPException(404)
    db.delete(mod)
    db.commit()
    return RedirectResponse("/admin/configurator", status_code=303)


@router.post("/configurator/modifiers/{mod_id}/edit", dependencies=[Depends(csrf_protect)])
async def configurator_modifier_edit(
    mod_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    name_cs: str = Form(...),
    name_en: str = Form(...),
    price_modifier: float = Form(default=0),
    is_default: Optional[str] = Form(default=None),
    color_hex: Optional[str] = Form(default=None),
    bead_count: Optional[int] = Form(default=None),
    image: Optional[UploadFile] = File(default=None),
):
    mod = db.get(Modifier, mod_id)
    if not mod:
        raise HTTPException(404)
    mod.name_cs = name_cs
    mod.name_en = name_en
    mod.price_modifier = price_modifier
    mod.is_default = is_default is not None
    mod.color_hex = color_hex or None
    mod.bead_count = bead_count
    if image and image.filename:
        mod.image_asset_path = await save_image(image)
    db.commit()
    flash(request, "Volba upravena.")
    return RedirectResponse("/admin/configurator", status_code=303)


@router.post("/configurator/modifiers/{mod_id}/image/delete", dependencies=[Depends(csrf_protect)])
async def configurator_modifier_image_delete(
    mod_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    mod = db.get(Modifier, mod_id)
    if not mod:
        raise HTTPException(404)
    mod.image_asset_path = None
    db.commit()
    return RedirectResponse("/admin/configurator", status_code=303)


# ── Tagy ──────────────────────────────────────────────────────

@router.get("/tags")
async def tags_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    tags = db.query(Tag).order_by(Tag.name_cs).all()
    return templates.TemplateResponse("admin/tags.html", {
        **_ctx(request, current_user),
        "tags": tags,
        "active": "tags",
    })


@router.post("/tags/add", dependencies=[Depends(csrf_protect)])
async def tag_add(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    name_cs: str = Form(...),
    name_en: str = Form(...),
    slug: str = Form(...),
    is_collection: Optional[str] = Form(default=None),
    cover_image: Optional[UploadFile] = File(default=None),
):
    cover_url = None
    if cover_image and cover_image.filename:
        cover_url = await save_image(cover_image)
    tag = Tag(
        name_cs=name_cs,
        name_en=name_en,
        slug=slug,
        is_collection=is_collection is not None,
        cover_image_url=cover_url,
    )
    db.add(tag)
    db.commit()
    flash(request, "Tag přidán.")
    return RedirectResponse("/admin/tags", status_code=303)


@router.post("/tags/{tag_id}/toggle", dependencies=[Depends(csrf_protect)])
async def tag_toggle(
    tag_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(404)
    tag.is_collection = not tag.is_collection
    db.commit()
    return RedirectResponse("/admin/tags", status_code=303)


@router.post("/tags/{tag_id}/cover", dependencies=[Depends(csrf_protect)])
async def tag_cover_upload(
    tag_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    cover_image: UploadFile = File(...),
):
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(404)
    tag.cover_image_url = await save_image(cover_image)
    db.commit()
    return RedirectResponse("/admin/tags", status_code=303)


@router.post("/tags/{tag_id}/cover/delete", dependencies=[Depends(csrf_protect)])
async def tag_cover_delete(
    tag_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(404)
    tag.cover_image_url = None
    db.commit()
    return RedirectResponse("/admin/tags", status_code=303)


@router.post("/tags/{tag_id}/delete", dependencies=[Depends(csrf_protect)])
async def tag_delete(
    tag_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(404)
    db.delete(tag)
    db.commit()
    flash(request, "Tag smazán.", "warning")
    return RedirectResponse("/admin/tags", status_code=303)


# ── Atributy ──────────────────────────────────────────────────

@router.get("/attributes")
async def attributes_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    attributes = db.query(Attribute).order_by(Attribute.name_cs).all()
    return templates.TemplateResponse("admin/attributes.html", {
        **_ctx(request, current_user),
        "attributes": attributes,
        "active": "attributes",
    })


@router.post("/attributes/add", dependencies=[Depends(csrf_protect)])
async def attribute_add(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    name_cs: str = Form(...),
    name_en: str = Form(...),
    slug: str = Form(...),
):
    attr = Attribute(name_cs=name_cs, name_en=name_en, slug=slug)
    db.add(attr)
    db.commit()
    flash(request, "Atribut přidán.")
    return RedirectResponse("/admin/attributes", status_code=303)


@router.post("/attributes/{attr_id}/delete", dependencies=[Depends(csrf_protect)])
async def attribute_delete(
    attr_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    attr = db.get(Attribute, attr_id)
    if not attr:
        raise HTTPException(404)
    db.delete(attr)
    db.commit()
    flash(request, "Atribut smazán.", "warning")
    return RedirectResponse("/admin/attributes", status_code=303)


@router.post("/attributes/{attr_id}/options/add", dependencies=[Depends(csrf_protect)])
async def attribute_option_add(
    attr_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
    value_cs: str = Form(...),
    value_en: str = Form(...),
    slug: str = Form(...),
):
    attr = db.get(Attribute, attr_id)
    if not attr:
        raise HTTPException(404)
    opt = AttributeOption(attribute_id=attr_id, value_cs=value_cs, value_en=value_en, slug=slug)
    db.add(opt)
    db.commit()
    return RedirectResponse("/admin/attributes", status_code=303)


@router.post("/attribute-options/{opt_id}/delete", dependencies=[Depends(csrf_protect)])
async def attribute_option_delete(
    opt_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    opt = db.get(AttributeOption, opt_id)
    if not opt:
        raise HTTPException(404)
    db.delete(opt)
    db.commit()
    return RedirectResponse("/admin/attributes", status_code=303)


# ── Produkty — update tagů ────────────────────────────────────

@router.post("/products/{product_id}/tags", dependencies=[Depends(csrf_protect)])
async def product_tags_update(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404)
    form = await request.form()
    tag_ids = [int(v) for v in form.getlist("tag_ids")]
    product.tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all() if tag_ids else []
    db.commit()
    return RedirectResponse(f"/admin/products/{product_id}/edit", status_code=303)
