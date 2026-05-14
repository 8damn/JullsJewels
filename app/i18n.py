import json
from pathlib import Path
from typing import Callable

from fastapi import Request

_TRANSLATIONS: dict[str, dict] = {}
_TRANS_DIR = Path(__file__).parent / "translations"


def _load(lang: str) -> dict:
    if lang not in _TRANSLATIONS:
        path = _TRANS_DIR / f"{lang}.json"
        if not path.exists():
            lang = "cs"
            path = _TRANS_DIR / "cs.json"
        _TRANSLATIONS[lang] = json.loads(path.read_text(encoding="utf-8"))
    return _TRANSLATIONS[lang]


def get_lang(request: Request) -> str:
    lang = request.session.get("lang", "cs")
    return lang if lang in ("cs", "en") else "cs"


def make_t(lang: str) -> Callable[[str], str]:
    data = _load(lang)
    def t(key: str) -> str:
        return data.get(key, key)
    return t
