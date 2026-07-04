"""Registro de herramientas externas y sondeo de su presencia.

Categorías:
  - bootstrap: lo único que Tramalia/mise no pueden instalar por sí mismos
               (mise, git, uv). doctor muestra el comando oficial.
  - stack:     depende del stack detectado (node, dotnet, ...).
  - feature:   se activa solo si el gate/feature correspondiente está habilitado
               (semgrep -> seguridad, sqlfluff -> db, lhci -> ux, ...).

La instalación real la hace mise (`mise install` / `mise use ...`); Tramalia solo
diagnostica y delega.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Tool:
    key: str
    cmd: str
    role: str
    category: str  # "bootstrap" | "stack" | "feature"
    version_args: tuple[str, ...] = ("--version",)
    managed_by_mise: bool = True
    install_hint: str = ""
    stacks: tuple[str, ...] = ()  # category "stack": stacks que la requieren
    feature: str = ""             # category "feature": gate/feature que la activa
    runtime: str = ""             # runtime externo que necesita: "node", "python", ...


REGISTRY: list[Tool] = [
    # --- bootstrap (mise no puede instalarse a sí mismo) ---
    Tool("mise", "mise", "gestor de versiones + runner de gates", "bootstrap",
         managed_by_mise=False, install_hint="https://mise.jdx.dev/getting-started.html"),
    Tool("git", "git", "control de versiones (memoria, ADR, handoff)", "bootstrap",
         managed_by_mise=False, install_hint="https://git-scm.com/downloads"),
    Tool("uv", "uv", "instalador de tools Python (copier, specify, ...)", "bootstrap",
         managed_by_mise=False, install_hint="https://docs.astral.sh/uv/getting-started/installation/"),

    # --- por stack ---
    Tool("node", "node", "runtime JS para frontend/build", "stack",
         stacks=("node", "angular", "react", "vue", "svelte")),
    Tool("dotnet", "dotnet", "SDK .NET", "stack", stacks=("dotnet",)),

    # --- por feature/gate ---
    Tool("copier", "copier", "scaffolding de la convención (tramalia init)", "feature",
         feature="init", managed_by_mise=False, install_hint="uv tool install copier"),
    Tool("repomix", "repomix", "snapshot de contexto para IA", "feature",
         feature="context", runtime="node", install_hint="mise use npm:repomix"),
    Tool("serena", "serena", "navegación/edición semántica (MCP)", "feature",
         feature="context", managed_by_mise=False,
         install_hint="uvx --from git+https://github.com/oraios/serena serena --help"),
    Tool("semgrep", "semgrep", "SAST (gate seguridad)", "feature",
         feature="security", install_hint="mise use pipx:semgrep"),
    Tool("gitleaks", "gitleaks", "secret scanning (gate seguridad)", "feature",
         feature="security", install_hint="mise use aqua:gitleaks"),
    Tool("sqlfluff", "sqlfluff", "lint SQL (gate base de datos)", "feature",
         feature="database", install_hint="mise use pipx:sqlfluff"),
    Tool("rulesync", "rulesync", "fan-out de reglas/skills por agente", "feature",
         feature="sync", runtime="node", install_hint="mise use npm:rulesync"),
    Tool("lhci", "lhci", "Lighthouse CI (gate UX/UI)", "feature",
         feature="ux", runtime="node", install_hint="mise use npm:@lhci/cli"),
    Tool("playwright", "playwright", "regresión visual + e2e (gate UX/UI)", "feature",
         feature="ux", runtime="node", install_hint="mise use npm:playwright"),
    # memoria persistente opcional (nivel N2). Tramalia no la construye: la delega.
    Tool("engram", "engram", "memoria persistente para agentes (N2, opcional)", "feature",
         feature="memory", managed_by_mise=False,
         install_hint="brew install gentleman-programming/tap/engram"),
    # compresión de contexto/outputs (token-saver opcional). NO reemplaza la evidencia.
    Tool("headroom", "headroom", "compresión de contexto/outputs (token-saver, opcional)",
         "feature", feature="context", managed_by_mise=False,
         install_hint='pip install "headroom-ai[all]"'),
    # spec-driven development (opcional): complementa specs/ generada por init.
    Tool("speckit", "specify", "spec-driven development (Spec Kit, opcional)",
         "feature", feature="specs", managed_by_mise=False,
         install_hint="uv tool install specify-cli --from git+https://github.com/github/spec-kit.git"),
    # grafo de código pre-indexado (contexto quirúrgico en una llamada, opcional).
    Tool("codegraph", "codegraph", "grafo de código pre-indexado (contexto, opcional)",
         "feature", feature="context", managed_by_mise=False,
         install_hint="ver github.com/colbymchenry/codegraph (instalar con --skip si no quieres que configure agentes)"),
]


@dataclass
class Status:
    tool: Tool
    present: bool
    version: str | None = None


def probe(tool: Tool, timeout: float = 8.0) -> Status:
    """Comprueba si una herramienta está en el PATH y su versión."""
    if shutil.which(tool.cmd) is None:
        return Status(tool, present=False)
    version = None
    try:
        out = subprocess.run(
            [tool.cmd, *tool.version_args],
            capture_output=True, text=True, timeout=timeout,
        )
        raw = (out.stdout or out.stderr or "").strip()
        if raw:
            version = raw.splitlines()[0].strip()
    except Exception:
        version = None
    return Status(tool, present=True, version=version)


def relevant_tools(stack: list[str], features: tuple[str, ...]) -> list[Tool]:
    """Filtra el registro a lo que aplica para este proyecto."""
    out: list[Tool] = []
    for t in REGISTRY:
        if t.category == "bootstrap":
            out.append(t)
        elif t.category == "stack" and any(s in stack for s in t.stacks):
            out.append(t)
        elif t.category == "feature" and t.feature in features:
            out.append(t)
    return out
