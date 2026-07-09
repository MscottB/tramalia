"""Lógica del comando `doctor`: diagnostica qué herramientas faltan.

No instala nada por sí mismo: clasifica, sondea y delega. La parte que sí puede
"arreglar" es invocar a mise (`mise install`) cuando mise ya está presente.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from tramalia.core.detect import detect_stack, enabled_features
from tramalia.core.tools import Status, probe, relevant_tools


@dataclass
class Report:
    stack: list[str]
    features: tuple[str, ...]
    statuses: list[Status]
    node_present: bool = True
    node_tools: list[str] = field(default_factory=list)
    uv_bin_on_path: bool = True

    @property
    def missing_blocking(self) -> list[Status]:
        # bootstrap y stack bloquean; feature es advertencia
        return [s for s in self.statuses
                if not s.present and s.tool.category in ("bootstrap", "stack")]

    @property
    def missing_optional(self) -> list[Status]:
        return [s for s in self.statuses
                if not s.present and s.tool.category == "feature"]

    @property
    def needs_node(self) -> bool:
        return bool(self.node_tools) and not self.node_present


def diagnose(root: Path | None = None,
             features: tuple[str, ...] | None = None) -> Report:
    root = root or Path.cwd()
    stack = detect_stack(root)
    feats = features if features is not None else enabled_features(stack)
    statuses = [probe(t) for t in relevant_tools(stack, feats)]
    node_tools = [s.tool.cmd for s in statuses if s.tool.runtime == "node"]
    node_present = shutil.which("node") is not None
    # PATH de uv: solo es un problema si uv está presente pero su bin no está en PATH
    from tramalia.core import installer
    uv_ok = True
    if shutil.which("uv") is not None:
        uv_ok = installer.uv_bin_on_path()
    return Report(stack=stack, features=feats, statuses=statuses,
                  node_present=node_present, node_tools=node_tools,
                  uv_bin_on_path=uv_ok)


def write_snapshot(report: Report, root: Path) -> Path | None:
    """Escribe .tramalia/context/tools.json: qué hay instalado y qué no.

    Es CONTEXTO PARA LOS AGENTES (AGENTS.md les indica consultarlo antes de
    invocar una herramienta externa — así no llaman a ciegas a una ausente).
    Solo se escribe si el proyecto tiene .tramalia/.
    """
    import datetime
    import json
    if not (root / ".tramalia").is_dir():
        return None
    dest = root / ".tramalia" / "context"
    dest.mkdir(parents=True, exist_ok=True)
    data = {
        "_nota": ("generado por `tramalia doctor` — consúltalo antes de invocar "
                  "una herramienta externa; si installed=false usa su alternativa "
                  "o continúa sin ella"),
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "stack": report.stack,
        "uv_bin_on_path": report.uv_bin_on_path,
        "tools": [
            {"key": s.tool.key, "cmd": s.tool.cmd, "installed": s.present,
             "version": s.version, "category": s.tool.category,
             "feature": s.tool.feature or None,
             "alternative": None if s.present else s.tool.install_hint}
            for s in report.statuses
        ],
    }
    out = dest / "tools.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    return out


def fix(report: Report) -> bool:
    """Intenta instalar lo que falte delegando en mise. Devuelve True si actuó."""
    mise_ok = next((s.present for s in report.statuses if s.tool.key == "mise"), False)
    if not mise_ok:
        return False  # sin mise no se puede delegar; el caller mostrará el bootstrap
    try:
        subprocess.run(["mise", "install"], check=False)
        return True
    except Exception:
        return False
