from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, verify_password
from app.csrf import csrf_protect
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

COOKIE_NAME = "access_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 dní


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # True v produkci za HTTPS
        max_age=COOKIE_MAX_AGE,
    )


# ---------------------------------------------------------------------------
# Registrace
# ---------------------------------------------------------------------------
@router.post("/register", dependencies=[Depends(csrf_protect)])
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    first_name: Optional[str] = Form(default=None),
    last_name: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Heslo musí mít alespoň 8 znaků")

    existing = db.query(User).filter(User.email == email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="E-mail je již registrován")

    user = User(
        email=email.lower(),
        hashed_password=hash_password(password),
        role=UserRole.customer,
        first_name=first_name,
        last_name=last_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.role)
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    _set_auth_cookie(response, token)
    return response


# ---------------------------------------------------------------------------
# Přihlášení  (rate-limitováno: 10 pokusů / minutu)
# ---------------------------------------------------------------------------
@router.post("/login", dependencies=[Depends(csrf_protect)])
@limiter.limit("10/minute")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Nesprávný e-mail nebo heslo")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Účet je deaktivován")

    token = create_access_token(user.id, user.role)
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    _set_auth_cookie(response, token)
    return response


# ---------------------------------------------------------------------------
# Odhlášení
# ---------------------------------------------------------------------------
@router.post("/logout", dependencies=[Depends(csrf_protect)])
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(COOKIE_NAME)
    return response


# ---------------------------------------------------------------------------
# Aktuální uživatel (JSON — pro případné JS fetch)
# ---------------------------------------------------------------------------
@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }
