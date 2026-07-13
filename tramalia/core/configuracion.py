"""Read and update project configuration through stable Spanish APIs."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Literal
from uuid import uuid4


def descripcion_tarea(raiz: Path, id_tarea: str) -> str | None:
    """Return one task section from the project specification."""
    ruta = raiz / "specs" / "tasks.md"
    if not ruta.exists() or not id_tarea:
        return None
    texto = ruta.read_text(encoding="utf-8")
    coincidencia = re.search(
        rf"^##\s+{re.escape(id_tarea)}\b.*?(?=^##\s|\Z)",
        texto,
        flags=re.M | re.S,
    )
    return coincidencia.group(0).strip() if coincidencia else None


def leer_configuracion(raiz: Path) -> dict[str, object]:
    """Read project JSON configuration or return an empty mapping."""
    ruta = raiz / ".tramalia" / "config.json"
    if not ruta.exists():
        return {}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return datos if isinstance(datos, dict) else {}


def guardar_configuracion(raiz: Path, datos: dict[str, object]) -> bool:
    """Publish project JSON configuration through an atomic sibling replace."""
    ruta = raiz / ".tramalia" / "config.json"
    temporal = ruta.with_name(f"{ruta.name}.tmp-{uuid4().hex}")
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal.write_text(
            json.dumps(datos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        validado = json.loads(temporal.read_text(encoding="utf-8"))
        if not isinstance(validado, dict):
            return False
        temporal.replace(ruta)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return False
    finally:
        temporal.unlink(missing_ok=True)
    return True


def agentes_predeterminados(raiz: Path) -> tuple[str, str]:
    """Return the configured primary and reviewer agent identifiers."""
    agentes = leer_configuracion(raiz).get("agents", {})
    if not isinstance(agentes, dict):
        return "", ""
    return (
        str(agentes.get("primary") or ""),
        str(agentes.get("reviewer") or ""),
    )


def proveedor_contexto(raiz: Path) -> str:
    """Return the selected code-navigation provider for a project."""
    from tramalia.core.proveedor_contexto import PREDETERMINADO

    contexto = leer_configuracion(raiz).get("context", {})
    if not isinstance(contexto, dict):
        return PREDETERMINADO
    return str(contexto.get("backend") or PREDETERMINADO)


def fijar_proveedor_contexto(raiz: Path, nombre: str) -> bool:
    """Persist one valid code-navigation provider for an initialized project."""
    from tramalia.core.proveedor_contexto import PROVEEDORES

    ruta = raiz / ".tramalia" / "config.json"
    if nombre not in PROVEEDORES or not ruta.exists():
        return False
    datos = leer_configuracion(raiz)
    if not datos:
        return False
    contexto = datos.setdefault("context", {})
    if not isinstance(contexto, dict):
        return False
    contexto["backend"] = nombre
    return guardar_configuracion(raiz, datos)


def modo_trabajo(raiz: Path) -> Literal["local-first", "team"]:
    """Return the exact supported project collaboration mode."""
    modo = leer_configuracion(raiz).get("mode")
    return "team" if modo == "team" else "local-first"


def tope_modelos_agentes(raiz: Path) -> str:
    """Return the configured agent model ceiling or ``none``."""
    agentes = leer_configuracion(raiz).get("agents", {})
    if not isinstance(agentes, dict):
        return "none"
    return str(agentes.get("model_cap") or "none")


def fijar_tope_modelos_agentes(raiz: Path, tope: str) -> bool:
    """Persist one supported model ceiling for an initialized project."""
    from tramalia.core.model_cap import CAPS

    ruta = raiz / ".tramalia" / "config.json"
    if tope not in (*CAPS, "none") or not ruta.exists():
        return False
    datos = leer_configuracion(raiz)
    if not datos:
        return False
    agentes = datos.setdefault("agents", {})
    if not isinstance(agentes, dict):
        return False
    agentes["model_cap"] = tope
    return guardar_configuracion(raiz, datos)


def version_andamiaje(raiz: Path) -> str | None:
    """Return the Tramalia version that last scaffolded the project."""
    ruta = raiz / ".tramalia" / "version"
    if not ruta.exists():
        return None
    version = ruta.read_text(encoding="utf-8").strip()
    return version or None


def fijar_version_andamiaje(raiz: Path, version: str) -> None:
    """Record the Tramalia version that scaffolded the project."""
    ruta = raiz / ".tramalia" / "version"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(version + "\n", encoding="utf-8")


def id_tarea_actual(raiz: Path) -> str | None:
    """Return the current non-placeholder task identifier."""
    ruta = raiz / ".tramalia" / "current-task.md"
    if not ruta.exists():
        return None
    coincidencia = re.search(r"^\s*-\s*ID:\s*(.+)$", ruta.read_text(encoding="utf-8"), flags=re.M)
    if not coincidencia:
        return None
    valor = coincidencia.group(1).strip()
    if not valor or valor.startswith("["):
        return None
    return valor.split()[0]


def resolver_argumentos_cierre(
    raiz: Path,
    tarea_posicional: str | None,
    tarea_bandera: str | None,
    agente: str | None,
    revisor: str | None,
    preguntar: Callable[[], str] | None = None,
) -> tuple[str, str, str]:
    """Resolve task, agent and reviewer through the configured precedence."""
    tarea = tarea_posicional or tarea_bandera or id_tarea_actual(raiz)
    if not tarea and preguntar is not None:
        tarea = preguntar()
    tarea = tarea or "TASK-000"
    agente_predeterminado, revisor_predeterminado = agentes_predeterminados(raiz)
    return (
        tarea,
        agente or agente_predeterminado,
        revisor or revisor_predeterminado,
    )
