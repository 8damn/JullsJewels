from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth import decode_access_token
from app.database import get_db
from app.models import User, UserRole


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(default=None),
) -> Optional[User]:
    if not access_token:
        return None
    payload = decode_access_token(access_token)
    if not payload:
        return None
    # Zamezit použití refresh tokenu jako access tokenu
    # Starší tokeny (bez "type") jsou stále akceptovány pro zpětnou kompatibilitu
    if payload.get("type") == "refresh":
        return None
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        return None
    return user


def get_current_user(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def require_editor(user: User = Depends(get_current_user)) -> User:
    if user.role not in (UserRole.editor, UserRole.admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user
