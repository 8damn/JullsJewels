from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    verify_password,
    _DUMMY_HASH,
)
from app.config import settings
from app.csrf import csrf_protect
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

ACCESS_COOKIE  = "access_token"
REFRESH_COOKIE = "refresh_token"
ACCESS_MAX_AGE  = 60 * 60          # 1 hodina
REFRESH_MAX_AGE = 60 * 60 * 24 * 7 # 7 dní

# Počet neúspěšných pokusů než se účet uzamkne
_MAX_ATTEMPTS  = 5
# Doba uzamčení v minutách
_LOCKOUT_MIN   = 15


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Nastaví oba auth cookies — access (1h) i refresh (7d)."""
    secure = settings.is_production
    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=secure,
        max_age=ACCESS_MAX_AGE,
    )
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=secure,
        max_age=REFRESH_MAX_AGE,
        path="/auth/refresh",  # refresh cookie dostupný jen na /auth/refresh
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE)
    response.delete_cookie(REFRESH_COOKIE, path="/auth/refresh")


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
    import re
    email = email.strip().lower()

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise HTTPException(status_code=400, detail="Neplatná e-mailová adresa")

    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Heslo musí mít alespoň 8 znaků")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="E-mail je již registrován")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        role=UserRole.customer,
        first_name=first_name,
        last_name=last_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Rotace session při registraci (session fixation prevence)
    request.session.clear()

    access  = create_access_token(user.id, user.role)
    refresh = create_refresh_token(user.id)

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    _set_auth_cookies(response, access, refresh)
    return response


# ---------------------------------------------------------------------------
# Přihlášení — rate limit 10/min per IP + per-account lockout
# ---------------------------------------------------------------------------
@router.post("/login", dependencies=[Depends(csrf_protect)])
@limiter.limit("10/minute")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    import re
    email = email.strip().lower()

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise HTTPException(status_code=401, detail="Nesprávný e-mail nebo heslo")

    user = db.query(User).filter(User.email == email).first()

    # ── Timing attack prevence: vždy spustíme bcrypt, i když user neexistuje ──
    candidate_hash = user.hashed_password if user else _DUMMY_HASH
    password_ok = verify_password(password, candidate_hash)

    # ── Per-account lockout ────────────────────────────────────────────────
    if user and user.locked_until:
        locked_until_utc = user.locked_until.replace(tzinfo=timezone.utc) if user.locked_until.tzinfo is None else user.locked_until
        if locked_until_utc > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=429,
                detail="Účet je dočasně uzamčen z důvodu příliš mnoha neúspěšných pokusů. Zkuste to za chvíli.",
            )
        # Lockout vypršel — reset
        user.failed_login_attempts = 0
        user.locked_until = None

    if not user or not password_ok:
        # Zaznamenat neúspěšný pokus
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= _MAX_ATTEMPTS:
                user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None)
                from datetime import timedelta
                user.locked_until = (datetime.now(timezone.utc) + timedelta(minutes=_LOCKOUT_MIN)).replace(tzinfo=None)
            db.commit()
        raise HTTPException(status_code=401, detail="Nesprávný e-mail nebo heslo")

    if not user.is_active:
        # Vrátíme stejnou zprávu — neodhalíme stav účtu
        raise HTTPException(status_code=401, detail="Nesprávný e-mail nebo heslo")

    # ── Úspěšný login — reset counter, rotace session ─────────────────────
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    # Rotace session (session fixation + CSRF token rotation)
    request.session.clear()

    access  = create_access_token(user.id, user.role)
    refresh = create_refresh_token(user.id)

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    _set_auth_cookies(response, access, refresh)
    return response


# ---------------------------------------------------------------------------
# Refresh — vymění expirovaný access token za nový pomocí refresh cookie
# ---------------------------------------------------------------------------
@router.post("/refresh")
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Volá se automaticky JS kódem na frontendu, nebo middlewarem,
    když access token expiruje (1h). Refresh token platí 7 dní.
    """
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token chybí")

    payload = decode_access_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Neplatný refresh token")

    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Neplatný refresh token")

    new_access  = create_access_token(user.id, user.role)
    new_refresh = create_refresh_token(user.id)

    response = JSONResponse({"ok": True})
    _set_auth_cookies(response, new_access, new_refresh)
    return response


# ---------------------------------------------------------------------------
# Odhlášení
# ---------------------------------------------------------------------------
@router.post("/logout", dependencies=[Depends(csrf_protect)])
async def logout(request: Request):
    request.session.clear()
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    _clear_auth_cookies(response)
    return response


# ---------------------------------------------------------------------------
# Aktuální uživatel (JSON — pro JS fetch)
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
