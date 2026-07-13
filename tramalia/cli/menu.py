"""Render the interactive CLI menu with Questionary or a stdlib fallback."""

from __future__ import annotations

from tramalia.i18n import t

try:
    import questionary

    _TIENE_QUESTIONARY = True
except Exception:
    _TIENE_QUESTIONARY = False

# Las claves son comandos públicos heredados; el orden define el menú.
CLAVES_OPCIONES: list[str] = [
    "close",
    "log",
    "doctor",
    "detect",
    "init",
    "gates",
    "context",
    "evidence",
    "handoff",
    "sync",
    "skills",
    "update",
    "ui",
    "quit",
]


def _opciones() -> list[tuple[str, str]]:
    return [(clave, t(f"menu.{clave}")) for clave in CLAVES_OPCIONES]


def elegir() -> str:
    """Prompt for one stable public command.

    Returns:
        Selected public command, or ``quit`` when the prompt is cancelled.
    """
    opciones = _opciones()
    if _TIENE_QUESTIONARY:
        respuesta = questionary.select(
            t("menu.title"),
            choices=[
                questionary.Choice(title=etiqueta, value=clave) for clave, etiqueta in opciones
            ],
            qmark="?",
            instruction=t("menu.instruction"),
        ).ask()
        return respuesta or "quit"

    print(f"\n{t('menu.title')}")
    for indice, (_, etiqueta) in enumerate(opciones, 1):
        print(f"  {indice:>2}. {etiqueta}")
    entrada = input(t("menu.option")).strip()
    if not entrada.isdigit() or not (1 <= int(entrada) <= len(opciones)):
        return "quit"
    return opciones[int(entrada) - 1][0]


def pedir_texto(pregunta: str, predeterminado: str = "") -> str:
    """Prompt for text without requiring Questionary.

    Args:
        pregunta: User-facing prompt.
        predeterminado: Value returned for an empty or cancelled response.

    Returns:
        Trimmed response or the supplied default.
    """
    if _TIENE_QUESTIONARY:
        respuesta = questionary.text(
            pregunta,
            default=predeterminado,
            qmark="?",
        ).ask()
        return (respuesta if respuesta is not None else predeterminado).strip() or predeterminado
    entrada = input(f"{pregunta} [{predeterminado}]> ").strip()
    return entrada or predeterminado
