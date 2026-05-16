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


# ── V4 FreeBuilder (flexibilní sekvence, dynamická délka) ──────────
# Záměrně bez admin pohledu — pattern si volí sám zákazník.
@router.get("/v4", response_class=HTMLResponse)
def v4_customer(request: Request):
    return templates.TemplateResponse("v4_freebuilder_customer.html", _ctx(request))


# ── V5 Studio (drag-drop reorder, start overlay s kostrami) ────────
# Iterace nad V4: hladší interakce přes drag-and-drop, vizuální výběr
# kostry na začátku, redukované UI pro přidávání slotů.
@router.get("/v5", response_class=HTMLResponse)
def v5_customer(request: Request):
    return templates.TemplateResponse("v5_studio_customer.html", _ctx(request))


# ── V6 Atelier (s pravidly výroby — validace) ──────────────────────
# Iterace nad V5: žádné prázdné sloty (pure sekvence), předplněné startery,
# pravidla pro separátory (ne na okraji, ne dva vedle sebe), délkový rozsah
# ±1 cm (CTA jen v toleranci). Filozofie: výsledek je vždy reálně vyrobitelný.
@router.get("/v6", response_class=HTMLResponse)
def v6_customer(request: Request):
    return templates.TemplateResponse("v6_atelier_customer.html", _ctx(request))


# ── V7 CurveStudio (kruhová vizualizace tvaru náramku) ─────────────
# Iterace nad V6: přidává primární kruhový pohled — náramek vykreslen
# jako top-down kruh s poloměrem odpovídajícím skutečné délce.
# Cílový kruh + tolerance band jsou viditelně podloženy. Zachovává všechna
# pravidla výroby, drag-drop a startery z V6.
@router.get("/v7", response_class=HTMLResponse)
def v7_customer(request: Request):
    return templates.TemplateResponse("v7_curvestudio_customer.html", _ctx(request))


# ── V8 Loop (kruh-centric, fixed velikosti, drag-drop přímo na kruh) ─
# Iterace nad V7: kruh je hlavní interakce — drag z palety přímo na obvod
# kruhu, klik na korálek v kruhu = smazat, reorder dragem. Korálky mají
# fixní velikost (neškálují se s obvodem), kruh má minimum 12 cm.
# Žádný lineární sequence vespod — kruh je vše. Minimalist UX.
@router.get("/v8", response_class=HTMLResponse)
def v8_customer(request: Request):
    return templates.TemplateResponse("v8_loop_customer.html", _ctx(request))


# ── V9 Duo (kruh + linear sdílí sekvenci, plná default kostra) ────
# Iterace nad V8: vrací linear sequence pod kruh. Oba pohledy sdílí
# stejnou sekvenci a stejné drag-drop capabilities. Auto-load plné default
# kostry (29× onyx + 1× ametyst akcent uprostřed) — vyplní celý obvod kruhu.
@router.get("/v9", response_class=HTMLResponse)
def v9_customer(request: Request):
    return templates.TemplateResponse("v9_duo_customer.html", _ctx(request))
