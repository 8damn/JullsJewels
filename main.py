import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.routes import admin, auth, blog, cart, orders, pages, user

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Jullsjewels", version="0.1.0")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="session",
    max_age=60 * 60 * 24 * 7,
    https_only=False,
    same_site="lax",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# SSR stránky (bez prefixu — jsou to "veřejné" URL)
app.include_router(pages.router)
app.include_router(user.router)
app.include_router(blog.router)

# API routery
app.include_router(auth.router)
app.include_router(cart.router)
app.include_router(orders.router)

# Admin panel
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
