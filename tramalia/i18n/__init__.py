"""i18n por archivos JSON: agregar un idioma = agregar un catálogo, sin tocar código.

Resolución del idioma (en orden):
  1. TRAMALIA_LANG (env)
  2. "language" en .tramalia/config.json del proyecto actual
  3. locale del sistema
  4. fallback: inglés

Uso: from tramalia.i18n import t;  t("tui.title")  ·  t("close.blocked", gates="db")
"""

from __future__ import annotations

import json
import locale
import os
from pathlib import Path

_DIR = Path(__file__).parent
_catalogs: dict[str, dict] = {}
_lang: str | None = None

AVAILABLE = ("es", "en")


def _load(lang: str) -> dict:
    if lang not in _catalogs:
        f = _DIR / f"{lang}.json"
        try:
            _catalogs[lang] = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            _catalogs[lang] = {}
    return _catalogs[lang]


def detect_lang(root: Path | None = None) -> str:
    env = os.environ.get("TRAMALIA_LANG", "").strip().lower()
    if env in AVAILABLE:
        return env
    try:
        from tramalia.core.project import read_config
        cfg = read_config(root or Path.cwd()).get("language", "")
        if str(cfg).lower() in AVAILABLE:
            return str(cfg).lower()
    except Exception:
        pass
    try:
        loc = (locale.getlocale()[0] or os.environ.get("LANG", "") or "").lower()
    except Exception:
        loc = ""
    return "es" if loc.startswith(("es", "spanish")) else "en"


def get_lang() -> str:
    global _lang
    if _lang is None:
        _lang = detect_lang()
    return _lang


def set_lang(lang: str) -> None:
    global _lang
    _lang = lang if lang in AVAILABLE else None


def t(key: str, **kwargs) -> str:
    """Traduce una clave; cae a inglés y, en último caso, devuelve la clave."""
    text = _load(get_lang()).get(key) or _load("en").get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
