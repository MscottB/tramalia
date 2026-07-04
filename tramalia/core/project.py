"""Lectura del estado del proyecto: config.json y current-task.md.

Permite que los comandos resuelvan defaults sin flags:
  tarea:   posicional > --task > ID en .tramalia/current-task.md > prompt/TASK-000
  agente:  --agent    > config.json agents.primary
  revisor: --reviewer > config.json agents.reviewer
"""

from __future__ import annotations

import json
import re
from pathlib import Path


def is_initialized(root: Path) -> bool:
    """Un proyecto está gobernado por Tramalia si existe .tramalia/ (o AGENTS.md)."""
    return (root / ".tramalia").exists() or (root / "AGENTS.md").exists()


def task_description(root: Path, task_id: str) -> str | None:
    """Sección de la tarea en specs/tasks.md (## <ID> … hasta el siguiente ##)."""
    f = root / "specs" / "tasks.md"
    if not f.exists() or not task_id:
        return None
    text = f.read_text(encoding="utf-8")
    m = re.search(rf"^##\s+{re.escape(task_id)}\b.*?(?=^##\s|\Z)", text,
                  flags=re.M | re.S)
    return m.group(0).strip() if m else None


def read_config(root: Path) -> dict:
    f = root / ".tramalia" / "config.json"
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return {}


def default_agents(root: Path) -> tuple[str, str]:
    """(primary, reviewer) desde config.json; cadenas vacías si no hay."""
    agents = read_config(root).get("agents", {})
    return (str(agents.get("primary") or ""), str(agents.get("reviewer") or ""))


def current_task_id(root: Path) -> str | None:
    """ID declarado en .tramalia/current-task.md, o None si sigue en placeholder."""
    f = root / ".tramalia" / "current-task.md"
    if not f.exists():
        return None
    m = re.search(r"^\s*-\s*ID:\s*(.+)$", f.read_text(encoding="utf-8"), flags=re.M)
    if not m:
        return None
    value = m.group(1).strip()
    # el placeholder de la plantilla viene entre corchetes: [TASK-XXX — …]
    if not value or value.startswith("["):
        return None
    return value.split()[0]


def resolve_close_args(root: Path, task_pos: str | None, task_flag: str | None,
                       agent: str | None, reviewer: str | None,
                       ask=None) -> tuple[str, str, str]:
    """Resuelve (tarea, agente, revisor) aplicando la cadena de defaults.

    `ask` es un callable opcional (prompt interactivo) usado solo si no hay
    tarea por ninguna otra vía; si es None, cae a TASK-000 (scripts no se cuelgan).
    """
    task = task_pos or task_flag or current_task_id(root)
    if not task and ask is not None:
        task = ask()
    task = task or "TASK-000"

    primary, rev = default_agents(root)
    return task, (agent or primary), (reviewer or rev)
