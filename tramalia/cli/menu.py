"""Menú interactivo: usa questionary si está; si no, menú numerado stdlib.

Etiquetas vía tramalia.i18n (claves menu.*), resueltas al momento de mostrar.
"""

from __future__ import annotations

from tramalia.i18n import t

try:
    import questionary
    _HAS_Q = True
except Exception:
    _HAS_Q = False

# claves de comando (el orden define el menú); la etiqueta es t("menu.<clave>")
OPTION_KEYS: list[str] = [
    "close", "log", "doctor", "detect", "init", "gates", "context",
    "evidence", "handoff", "sync", "skills", "update", "ui", "quit",
]


def _options() -> list[tuple[str, str]]:
    return [(key, t(f"menu.{key}")) for key in OPTION_KEYS]


def choose() -> str:
    options = _options()
    if _HAS_Q:
        answer = questionary.select(
            t("menu.title"),
            choices=[questionary.Choice(title=label, value=key) for key, label in options],
            qmark="?",
            instruction=t("menu.instruction"),
        ).ask()
        return answer or "quit"

    # fallback stdlib
    print(f"\n{t('menu.title')}")
    for i, (_, label) in enumerate(options, 1):
        print(f"  {i:>2}. {label}")
    raw = input(t("menu.option")).strip()
    if not raw.isdigit() or not (1 <= int(raw) <= len(options)):
        return "quit"
    return options[int(raw) - 1][0]


def ask_text(prompt: str, default: str = "") -> str:
    """Pregunta un texto (questionary si está; input stdlib si no)."""
    if _HAS_Q:
        answer = questionary.text(prompt, default=default, qmark="?").ask()
        return (answer if answer is not None else default).strip() or default
    raw = input(f"{prompt} [{default}]> ").strip()
    return raw or default
