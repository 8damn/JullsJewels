import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import Base, engine
from app.routes import admin, auth, blog, cart, orders, pages, user
import app.models  # noqa: F401 — zajistí registraci všech modelů před create_all

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Jullsjewels", version="0.1.0")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="session",
    max_age=60 * 60 * 24 * 7,
    https_only=settings.is_production,  # HTTPS-only v produkci
    same_site="lax",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)
    _run_migrations()


def _run_migrations():
    """Přidá nové sloupce do existujících tabulek (SQLite ALTER TABLE)."""
    from sqlalchemy import text
    migrations = [
        "ALTER TABLE configurator_types ADD COLUMN layout_mode VARCHAR(20) NOT NULL DEFAULT 'layered'",
        "ALTER TABLE modifiers ADD COLUMN color_hex VARCHAR(7)",
        "ALTER TABLE modifiers ADD COLUMN bead_count INTEGER",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass  # sloupec již existuje


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

# Experimentální sandbox (izolovaný modul, 3 vizualizéry konfigurátoru)
from app.experiment.router import router as experiment_router
app.include_router(experiment_router)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
