"""Menú interactivo: usa questionary si está; si no, menú numerado stdlib."""

from __future__ import annotations

try:
    import questionary
    _HAS_Q = True
except Exception:
    _HAS_Q = False

# (clave, etiqueta) — la clave es el comando que se ejecuta
OPTIONS: list[tuple[str, str]] = [
    ("close", "★ cerrar tarea: gates → evidence → handoff"),
    ("log", "ver pista de auditoría (cierres)"),
    ("doctor", "diagnosticar herramientas requeridas"),
    ("detect", "detectar el stack del proyecto"),
    ("init", "inicializar o reparar la estructura"),
    ("gates", "ejecutar quality gates (mise run gates)"),
    ("context", "generar contexto / token-saver (repomix + serena)"),
    ("evidence", "generar evidence pack"),
    ("handoff", "crear handoff multiagente"),
    ("sync", "sincronizar reglas a otros agentes (rulesync)"),
    ("skills", "administrar skills (sync desde sus repos)"),
    ("update", "actualizar todo (mise + skills)"),
    ("ui", "abrir dashboard (TUI)"),
    ("quit", "salir"),
]


def ask_text(prompt: str, default: str = "") -> str:
    """Pregunta un texto (questionary si está; input stdlib si no)."""
    if _HAS_Q:
        answer = questionary.text(prompt, default=default, qmark="?").ask()
        return (answer if answer is not None else default).strip() or default
    raw = input(f"{prompt} [{default}]> ").strip()
    return raw or default


def choose() -> str:
    if _HAS_Q:
        answer = questionary.select(
            "¿qué quieres hacer?",
            choices=[questionary.Choice(title=label, value=key) for key, label in OPTIONS],
            qmark="?",
            instruction="(↑↓ navegar · ⏎ seleccionar)",
        ).ask()
        return answer or "quit"

    # fallback stdlib
    print("\n¿qué quieres hacer?")
    for i, (_, label) in enumerate(OPTIONS, 1):
        print(f"  {i:>2}. {label}")
    raw = input("opción> ").strip()
    if not raw.isdigit() or not (1 <= int(raw) <= len(OPTIONS)):
        return "quit"
    return OPTIONS[int(raw) - 1][0]
