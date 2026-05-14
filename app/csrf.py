"""
CSRF ochrana pro SSR formuláře (synchronizer token pattern).

Použití v Jinja2 šabloně:
    {{ csrf_input() }}   →  <input type="hidden" name="csrf_token" value="...">

Použití v route:
    from app.csrf import csrf_protect
    @router.post("/something")
    async def handler(request: Request, _=Depends(csrf_protect)): ...
"""
import secrets

from fastapi import Depends, HTTPException, Request, status


def _get_or_create_token(request: Request) -> str:
    session = request.session
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


async def csrf_protect(request: Request) -> None:
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    session_token = request.session.get("csrf_token")
    if not session_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing")
    form = await request.form()
    submitted_token = form.get("csrf_token")
    if not submitted_token or not secrets.compare_digest(session_token, str(submitted_token)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token invalid")


def make_csrf_input(request: Request) -> str:
    """Vrátí HTML hidden input s CSRF tokenem pro Jinja2 šablony."""
    token = _get_or_create_token(request)
    return f'<input type="hidden" name="csrf_token" value="{token}">'
