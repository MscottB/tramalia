"""Evidence pack: paquete de cierre verificable de una tarea (pieza propia)."""

from __future__ import annotations

import datetime
import subprocess
from pathlib import Path


def _git_changed(root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=root, capture_output=True, text=True, timeout=10,
        )
        names = [n for n in out.stdout.splitlines() if n.strip()]
        if names:
            return "# Archivos modificados\n\n" + "\n".join(f"- {n}" for n in names) + "\n"
    except Exception:
        pass
    return "# Archivos modificados\n\n- [lista de archivos y motivo]\n"


def build_evidence(root: Path, task: str = "TASK-000") -> Path:
    ts = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
    target = root / ".tramalia" / "evidence" / f"{ts}-{task}"
    target.mkdir(parents=True, exist_ok=True)

    files = {
        "summary.md": (
            f"# Resumen\n\n- Tarea: {task}\n- Fecha: {ts}\n- Agente:\n"
            "- Resultado:\n- Qué se hizo:\n"
        ),
        "files-changed.md": _git_changed(root),
        "commands.md": (
            "# Comandos ejecutados\n\n"
            "| comando | hora | exit | observación |\n|---|---|---|---|\n"
        ),
        "build-output.txt": "",
        "test-output.txt": "",
        "lint-output.txt": "",
        "security-output.txt": "",
        "database-output.txt": "",
        "ux-output.txt": "",
        "risks.md": "# Riesgos\n\n- [técnico / seguridad / DB / UX / operación]\n",
        "rollback.md": "# Plan de reversa\n\n- [pasos para revertir]\n",
        "next-steps.md": "# Siguiente paso\n\n- [qué debe hacer el siguiente agente/persona]\n",
    }
    for name, content in files.items():
        path = target / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")
    return target
