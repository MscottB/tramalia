"""Menú interactivo: usa questionary si está; si no, menú numerado stdlib."""

from __future__ import annotations

try:
    import questionary
    _HAS_Q = True
except Exception:
    _HAS_Q = False

# (clave, etiqueta) — la clave es el comando que se ejecuta
OPTIONS: list[tuple[str, str]] = [
    ("doctor", "diagnosticar herramientas requeridas"),
    ("detect", "detectar el stack del proyecto"),
    ("init", "inicializar o reparar la estructura (copier)"),
    ("gates", "ejecutar quality gates (mise run gates)"),
    ("close", "★ cerrar tarea: gates → evidence → handoff"),
    ("log", "ver pista de auditoría (cierres)"),
    ("context", "generar contexto / token-saver (repomix + serena)"),
    ("evidence", "generar evidence pack"),
    ("handoff", "crear handoff multiagente"),
    ("sync", "sincronizar reglas a otros agentes (rulesync)"),
    ("skills", "administrar skills (sync desde sus repos)"),
    ("update", "actualizar todo (mise + copier + skills)"),
    ("quit", "salir"),
]


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
