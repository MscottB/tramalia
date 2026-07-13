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
from tramalia.core.integraciones import (
    EstadoHerramienta,
    herramientas_relevantes,
    sondear,
)


@dataclass
class Report:
    stack: list[str]
    features: tuple[str, ...]
    statuses: list[EstadoHerramienta]
    node_present: bool = True
    node_tools: list[str] = field(default_factory=list)
    uv_bin_on_path: bool = True

    @property
    def missing_blocking(self) -> list[EstadoHerramienta]:
        # bootstrap y stack bloquean; feature es advertencia
        return [
            estado
            for estado in self.statuses
            if not estado.presente and estado.herramienta.categoria in ("bootstrap", "stack")
        ]

    @property
    def missing_optional(self) -> list[EstadoHerramienta]:
        return [
            estado
            for estado in self.statuses
            if not estado.presente and estado.herramienta.categoria == "feature"
        ]

    @property
    def needs_node(self) -> bool:
        return bool(self.node_tools) and not self.node_present


def diagnose(root: Path | None = None, features: tuple[str, ...] | None = None) -> Report:
    root = root or Path.cwd()
    stack = detect_stack(root)
    feats = features if features is not None else enabled_features(stack)
    statuses = [sondear(herramienta) for herramienta in herramientas_relevantes(stack, feats)]
    node_tools = [
        estado.herramienta.comando
        for estado in statuses
        if estado.herramienta.entorno_ejecucion == "node"
    ]
    node_present = shutil.which("node") is not None
    # PATH de uv: solo es un problema si uv está presente pero su bin no está en PATH
    from tramalia.core import installer

    uv_ok = True
    if shutil.which("uv") is not None:
        uv_ok = installer.uv_bin_on_path()
    return Report(
        stack=stack,
        features=feats,
        statuses=statuses,
        node_present=node_present,
        node_tools=node_tools,
        uv_bin_on_path=uv_ok,
    )


def write_snapshot(report: Report, root: Path) -> Path | None:
    """Escribe .tramalia/context/tools.json: qué hay instalado y qué no.

    Es CONTEXTO PARA LOS AGENTES (AGENTS.md les indica consultarlo antes de
    invocar una herramienta externa — así no llaman a ciegas a una ausente).
    Solo se escribe si el proyecto tiene .tramalia/.
    """
    import datetime
    import json

    from tramalia.core import project as project_core

    if not (root / ".tramalia").is_dir():
        return None
    dest = root / ".tramalia" / "context"
    dest.mkdir(parents=True, exist_ok=True)
    data = {
        "_nota": (
            "generado por `tramalia doctor` — consúltalo antes de invocar "
            "una herramienta externa; si installed=false usa su alternativa "
            "o continúa sin ella"
        ),
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "stack": report.stack,
        "uv_bin_on_path": report.uv_bin_on_path,
        "context_backend": project_core.context_backend(root),
        "model_cap": project_core.agents_model_cap(root),
        "tools": [
            {
                "key": estado.herramienta.clave,
                "cmd": estado.herramienta.comando,
                "installed": estado.presente,
                "version": estado.version,
                "category": estado.herramienta.categoria,
                "feature": estado.herramienta.capacidad or None,
                "alternative": (
                    None if estado.presente else estado.herramienta.sugerencia_instalacion
                ),
            }
            for estado in report.statuses
        ],
    }
    out = dest / "tools.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def fix(report: Report) -> bool:
    """Intenta instalar lo que falte delegando en mise. Devuelve True si actuó."""
    mise_ok = next(
        (estado.presente for estado in report.statuses if estado.herramienta.clave == "mise"),
        False,
    )
    if not mise_ok:
        return False  # sin mise no se puede delegar; el caller mostrará el bootstrap
    try:
        subprocess.run(["mise", "install"], check=False)
        return True
    except Exception:
        return False
