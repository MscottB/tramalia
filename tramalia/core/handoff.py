"""Handoff multiagente: agrega una entrada estructurada al log versionado."""

from __future__ import annotations

import datetime
from pathlib import Path

_HEADER = (
    "# 07 — Handoff de agentes\n\n"
    "> Traspaso estructurado entre agentes/sesiones. `tramalia handoff` agrega entradas aquí.\n"
)


def new_handoff(root: Path, task: str = "TASK-000",
                agent: str = "", reviewer: str = "",
                evidence_ref: str = "") -> Path:
    path = root / "docs" / "ai" / "07-handoff-agentes.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(_HEADER, encoding="utf-8")

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = (
        f"\n## {ts} — {task}\n"
        f"- Agente ejecutor: {agent or '[agente]'}\n"
        f"- Agente revisor sugerido: {reviewer or '[revisor]'}\n"
        f"- Tarea: {task}\n"
        f"- Evidence pack: {evidence_ref or '[pendiente — genera con tramalia close]'}\n"
        "- Archivos modificados:\n"
        "- Comandos ejecutados:\n"
        "- Resultado:\n"
        "- Riesgos:\n"
        "- Pendientes:\n"
        "- Siguiente paso recomendado:\n"
    )
    with path.open("a", encoding="utf-8") as fh:
        fh.write(entry)
    return path
