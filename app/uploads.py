"""
Bezpečné ukládání obrázků.

Bezpečnostní opatření:
  1. Čtení po chuncích — DoS prevence (server nenačte 10 GB do RAM)
  2. Pillow verify() — ověří skutečný formát souboru (magic bytes), ne klientský Content-Type
  3. Bezpečné jméno souboru — UUID, přípona odvozena z detekovaného formátu (nikoli od klienta)
"""
import io
import uuid

from fastapi import HTTPException, UploadFile
from pathlib import Path
from PIL import Image, UnidentifiedImageError

from app.config import settings

UPLOAD_DIR = Path("app/static/uploads")

# Maximální velikost v bytech (z konfigurace)
MAX_BYTES: int = settings.max_upload_size_mb * 1024 * 1024

# Mapování Pillow format → přípona souboru (whitelist)
_ALLOWED_FORMATS: dict[str, str] = {
    "JPEG": "jpg",
    "PNG":  "png",
    "WEBP": "webp",
}

# Maximální chunk při čtení (256 KB)
_CHUNK = 256 * 1024


async def save_image(file: UploadFile) -> str:
    """
    Uloží nahraný obrázek na disk, vrátí URL cestu `/static/uploads/<uuid>.<ext>`.

    Raises HTTPException 400 při:
    - příliš velkém souboru (překročení limitu při čtení, ne až po načtení)
    - neplatném nebo nepodporovaném formátu (Pillow ověřuje magic bytes)
    """
    # ── 1. Čti po chuncích — limit bez buffering celého souboru ────────────
    content = b""
    while True:
        chunk = await file.read(_CHUNK)
        if not chunk:
            break
        content += chunk
        if len(content) > MAX_BYTES:
            raise HTTPException(
                400,
                f"Soubor je příliš velký. Maximum je {settings.max_upload_size_mb} MB.",
            )

    if not content:
        raise HTTPException(400, "Soubor je prázdný.")

    # ── 2. Ověř skutečný formát pomocí Pillow (ne klientský Content-Type) ──
    try:
        img = Image.open(io.BytesIO(content))
        img.verify()          # ověří integritu souboru (magic bytes, strukturu)
        detected = img.format # "JPEG", "PNG", "WEBP" atd.
    except UnidentifiedImageError:
        raise HTTPException(400, "Soubor není rozpoznatelný jako obrázek.")
    except Exception:
        raise HTTPException(400, "Soubor je poškozený nebo neplatný.")

    # ── 3. Whitelist formátů ────────────────────────────────────────────────
    ext = _ALLOWED_FORMATS.get(detected)
    if ext is None:
        allowed = ", ".join(_ALLOWED_FORMATS.keys())
        raise HTTPException(400, f"Nepodporovaný formát ({detected}). Povoleno: {allowed}.")

    # ── 4. Bezpečné jméno — UUID + přípona z detekovaného formátu ──────────
    filename = f"{uuid.uuid4().hex}.{ext}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / filename).write_bytes(content)

    return f"/static/uploads/{filename}"
