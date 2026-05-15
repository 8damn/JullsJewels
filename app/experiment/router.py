"""Experimentální router se třemi vizualizéry konfigurátoru.

Plně izolováno od hlavního projektu: vlastní Jinja2Templates instance,
žádné importy z app.models / app.routes / app.jinja.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.experiment import data

router = APIRouter(prefix="/experiment", tags=["experiment"])
templates = Jinja2Templates(directory="app/experiment/templates")


def _ctx(request: Request, **extra):
    """Sdílený kontext: vždy zahrnuje paletu korálků jako JSON-serializable dict."""
    return {
        "request": request,
        "beads_6mm": data.BEADS_6MM,
        "beads_8mm": data.BEADS_8MM,
        "separators": data.SEPARATORS,
        "lengths": data.LENGTHS,
        "collections": data.COLLECTIONS,
        "all_beads": data.all_beads_flat(),
        "default_pattern_v1": data.DEFAULT_PATTERN_V1,
        **extra,
    }


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", _ctx(request))


# ── V1 Photostrand ───────────────────────────────────────────────
@router.get("/v1", response_class=HTMLResponse)
def v1_customer(request: Request):
    return templates.TemplateResponse("v1_photostrand_customer.html", _ctx(request))


@router.get("/v1/admin", response_class=HTMLResponse)
def v1_admin(request: Request):
    return templates.TemplateResponse("v1_photostrand_admin.html", _ctx(request))


# ── V2 Slotbuilder ───────────────────────────────────────────────
@router.get("/v2", response_class=HTMLResponse)
def v2_customer(request: Request):
    return templates.TemplateResponse("v2_slotbuilder_customer.html", _ctx(request))


@router.get("/v2/admin", response_class=HTMLResponse)
def v2_admin(request: Request):
    return templates.TemplateResponse("v2_slotbuilder_admin.html", _ctx(request))


# ── V3 Quickpicker ───────────────────────────────────────────────
@router.get("/v3", response_class=HTMLResponse)
def v3_customer(request: Request):
    return templates.TemplateResponse("v3_quickpicker_customer.html", _ctx(request))


@router.get("/v3/admin", response_class=HTMLResponse)
def v3_admin(request: Request):
    return templates.TemplateResponse("v3_quickpicker_admin.html", _ctx(request))
