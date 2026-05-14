from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_optional
from app.jinja import templates
from app.models import BlogPost, User
from app.template_context import base_ctx

router = APIRouter(prefix="/blog")


@router.get("")
async def blog_list(request: Request, db: Session = Depends(get_db),
                    current_user: Optional[User] = Depends(get_current_user_optional)):
    posts = db.query(BlogPost).filter(BlogPost.is_published == True)\
               .order_by(BlogPost.published_at.desc()).all()
    return templates.TemplateResponse("blog/list.html", {
        **base_ctx(request, current_user),
        "posts": posts,
    })


@router.get("/{slug}")
async def blog_detail(slug: str, request: Request, db: Session = Depends(get_db),
                      current_user: Optional[User] = Depends(get_current_user_optional)):
    post = db.query(BlogPost).filter(BlogPost.slug == slug, BlogPost.is_published == True).first()
    if not post:
        raise HTTPException(404)
    return templates.TemplateResponse("blog/detail.html", {
        **base_ctx(request, current_user),
        "post": post,
    })
