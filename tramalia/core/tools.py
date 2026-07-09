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
    ephemeral: bool = False       # corre vía uvx/npx: no requiere instalación


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
         stacks=("node", "angular", "react", "next", "nest", "vue", "svelte")),
    Tool("dotnet", "dotnet", "SDK .NET", "stack", stacks=("dotnet",)),
    Tool("mvn", "mvn", "build Java (Maven)", "stack", stacks=("maven",),
         managed_by_mise=False, install_hint="https://maven.apache.org/install.html"),
    Tool("gradle", "gradle", "build Java (Gradle)", "stack", stacks=("gradle",),
         managed_by_mise=False, install_hint="https://gradle.org/install/"),
    Tool("go", "go", "toolchain Go (build/test)", "stack", stacks=("go",),
         managed_by_mise=False, install_hint="https://go.dev/doc/install"),
    Tool("cargo", "cargo", "toolchain Rust (build/test)", "stack", stacks=("rust",),
         managed_by_mise=False, install_hint="https://www.rust-lang.org/tools/install"),

    # --- por feature/gate ---
    Tool("copier", "copier", "scaffolding de la convención (tramalia init)", "feature",
         feature="init", managed_by_mise=False, install_hint="uv tool install copier"),
    Tool("repomix", "repomix", "snapshot de contexto para IA", "feature",
         feature="context", runtime="node", install_hint="mise use npm:repomix"),
    Tool("serena", "serena", "navegación/edición semántica (MCP)", "feature",
         feature="context", managed_by_mise=False, ephemeral=True,
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
    # binario vía npm (@colbymchenry/codegraph); el wiring a agentes es aparte:
    # `codegraph install --skip-config` (nunca automatizado por Tramalia).
    Tool("codegraph", "codegraph", "grafo de código pre-indexado (contexto, opcional)",
         "feature", feature="context", managed_by_mise=False,
         install_hint="npm i -g @colbymchenry/codegraph"),
    # grafo de conocimiento desde código/docs/schemas (CLI+MCP+skill, opcional).
    Tool("graphify", "graphify", "grafo de conocimiento del proyecto (contexto, opcional)",
         "feature", feature="context", managed_by_mise=False,
         install_hint="uv tool install graphifyy"),
    # ingesta de documentos: PDF/Office/imágenes → Markdown (contexto, opcional).
    Tool("markitdown", "markitdown", "convierte PDF/Office/imágenes a Markdown (ingesta, contexto)",
         "feature", feature="context", managed_by_mise=False,
         install_hint='pip install "markitdown[all]"'),
    # analítica: Databricks Asset Bundles (gate bundle validate).
    Tool("databricks", "databricks", "Databricks CLI (bundle validate, analítica)",
         "feature", feature="databricks", managed_by_mise=False,
         install_hint="https://docs.databricks.com/dev-tools/cli/install"),

    # --- agentes CLI (detección informativa: Tramalia NO los configura) ---
    Tool("claude", "claude", "Claude Code (agente CLI)", "agent",
         managed_by_mise=False, install_hint="https://claude.com/claude-code"),
    Tool("codex", "codex", "OpenAI Codex (agente CLI)", "agent",
         managed_by_mise=False, install_hint="npm i -g @openai/codex"),
    # el binario real en PATH se llama "agy" (no "antigravity"); Antigravity CLI
    # reemplazó oficialmente a Gemini CLI (descontinuado 2026-06-18).
    Tool("antigravity", "agy", "Google Antigravity CLI — comando `agy` (agente CLI; ex-Gemini CLI)",
         "agent", managed_by_mise=False,
         install_hint="instalador oficial (agy) — ver antigravity.google/docs/cli-install"),
    Tool("opencode", "opencode", "OpenCode (agente CLI)", "agent",
         managed_by_mise=False, install_hint="npm i -g opencode-ai"),
    Tool("openclaw", "openclaw", "OpenClaw (gateway multi-modelo)", "agent",
         managed_by_mise=False, install_hint="ver documentación de OpenClaw"),
    Tool("hermes", "hermes", "Hermes (agente vía gateway)", "agent",
         managed_by_mise=False, install_hint="ver documentación de Hermes"),
]

# documentación oficial de cada herramienta (tecla `d` en la TUI / docs del sitio)
DOCS: dict[str, str] = {
    "mise": "https://mise.jdx.dev", "git": "https://git-scm.com/doc",
    "uv": "https://docs.astral.sh/uv/", "node": "https://nodejs.org/docs",
    "dotnet": "https://learn.microsoft.com/dotnet/", "go": "https://go.dev/doc/",
    "cargo": "https://doc.rust-lang.org/cargo/", "mvn": "https://maven.apache.org/guides/",
    "gradle": "https://docs.gradle.org", "copier": "https://copier.readthedocs.io",
    "repomix": "https://repomix.com", "serena": "https://github.com/oraios/serena",
    "semgrep": "https://semgrep.dev/docs/", "gitleaks": "https://github.com/gitleaks/gitleaks",
    "sqlfluff": "https://docs.sqlfluff.com", "rulesync": "https://github.com/dyoshikawa/rulesync",
    "lhci": "https://github.com/GoogleChrome/lighthouse-ci",
    "playwright": "https://playwright.dev/docs/intro",
    "engram": "https://github.com/gentleman-programming/engram",
    "headroom": "https://github.com/headroom-ai/headroom",
    "speckit": "https://github.com/github/spec-kit",
    "codegraph": "https://github.com/colbymchenry/codegraph",
    "graphify": "https://github.com/irsbugs/graphifyy",
    "markitdown": "https://github.com/microsoft/markitdown",
    "databricks": "https://docs.databricks.com/dev-tools/cli/",
    "claude": "https://code.claude.com/docs", "codex": "https://developers.openai.com/codex",
    "antigravity": "https://antigravity.google/docs/cli-getting-started",
    "opencode": "https://opencode.ai/docs",
    "openclaw": "https://github.com/openclaw", "hermes": "https://hermes.nousresearch.com",
}


def docs_url(tool: Tool) -> str:
    if tool.key in DOCS:
        return DOCS[tool.key]
    return tool.install_hint if tool.install_hint.startswith("http") else ""


@dataclass
class Status:
    tool: Tool
    present: bool
    version: str | None = None


def _mise_has(cmd: str, timeout: float = 6.0) -> bool:
    """¿La instaló mise? Sus shims no están en el PATH hasta `mise activate` /
    reiniciar la terminal, así que `shutil.which` no las ve — `mise which` sí."""
    if shutil.which("mise") is None:
        return False
    try:
        cp = subprocess.run(["mise", "which", cmd], capture_output=True,
                            text=True, timeout=timeout)
        return cp.returncode == 0 and bool((cp.stdout or "").strip())
    except Exception:
        return False


def _uv_has(cmd: str) -> bool:
    """¿La instaló `uv tool install`? uv deja los ejecutables en ~/.local/bin,
    que en Windows NO entra al PATH (ni reiniciando) salvo `uv tool update-shell`
    — se revisa la carpeta directamente, sin depender del PATH."""
    from pathlib import Path
    base = Path.home() / ".local" / "bin"
    return any((base / f"{cmd}{ext}").is_file() for ext in (".exe", ".cmd", ""))


def _go_has(cmd: str) -> bool:
    """¿La instaló `go install`? Deja el binario en ~/go/bin (o $GOPATH/bin),
    que a menudo tampoco está en el PATH — se revisa la carpeta directamente."""
    import os
    from pathlib import Path
    gopath = os.environ.get("GOPATH")
    base = (Path(gopath) / "bin") if gopath else (Path.home() / "go" / "bin")
    return any((base / f"{cmd}{ext}").is_file() for ext in (".exe", ""))


def probe(tool: Tool, timeout: float = 8.0) -> Status:
    """Comprueba si una herramienta está disponible y su versión."""
    from tramalia.i18n import t
    if shutil.which(tool.cmd) is None:
        if tool.ephemeral and shutil.which("uv"):
            # corre vía uvx: no hay nada que instalar
            return Status(tool, present=True, version=t("doctor.ephemeral"))
        if tool.managed_by_mise and _mise_has(tool.cmd):
            return Status(tool, present=True, version=t("doctor.viamise"))
        if _uv_has(tool.cmd):
            return Status(tool, present=True, version=t("doctor.viauv"))
        if _go_has(tool.cmd):
            return Status(tool, present=True, version=t("doctor.viago"))
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
        if t.category in ("bootstrap", "agent"):
            out.append(t)
        elif t.category == "stack" and any(s in stack for s in t.stacks):
            out.append(t)
        elif t.category == "feature" and t.feature in features:
            out.append(t)
    return out
