from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# Dummy hash pro constant-time porovnání i při neexistujícím uživateli.
# Bez toho by útočník mohl odlišit "user neexistuje" (rychle) od "špatné heslo" (bcrypt).
_DUMMY_HASH: str = hash_password("__dummy_password_never_valid__")


def create_access_token(user_id: int, role: str) -> str:
    """Krátký JWT (1h) — pro autentizaci běžných requestů."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_expire_minutes)
    payload = {"sub": str(user_id), "role": role, "type": "access", "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: int) -> str:
    """Dlouhý JWT (7d) — pouze pro obnovu access tokenu na /auth/refresh."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expire_days)
    payload = {"sub": str(user_id), "type": "refresh", "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


# ── Confirmation tokens pro hosty (objednávky bez účtu) ─────────────
# Tyto tokeny umožňují anonymnímu zákazníkovi vidět svou objednávku
# (např. z e-mailu) bez nutnosti registrace. Platí 30 dní.

def create_confirmation_token(order_id: int) -> str:
    """Vytvoří podepsaný token pro náhled objednávky hostem."""
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    payload = {"order_id": order_id, "purpose": "order_confirm", "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def verify_confirmation_token(token: str, expected_order_id: int) -> bool:
    """Ověří token a vrátí True, pokud platí pro danou objednávku."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return False
    if payload.get("purpose") != "order_confirm":
        return False
    return payload.get("order_id") == expected_order_id
