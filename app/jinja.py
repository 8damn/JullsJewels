"""Centrální Jinja2Templates instance se sdílenými helpery."""
from markupsafe import Markup
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")


def _csrf_input(token: str) -> Markup:
    return Markup(f'<input type="hidden" name="csrf_token" value="{token}">')


def _price_fmt(value: float) -> str:
    return f"{value:,.0f} Kč".replace(",", " ")


templates.env.globals["csrf_input"] = _csrf_input
templates.env.globals["price_fmt"] = _price_fmt
templates.env.filters["price"] = _price_fmt
