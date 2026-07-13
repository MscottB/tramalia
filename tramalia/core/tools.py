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
from dataclasses import dataclass


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
    feature: str = ""  # category "feature": gate/feature que la activa
    runtime: str = ""  # runtime externo que necesita: "node", "python", ...
    ephemeral: bool = False  # corre vía uvx/npx: no requiere instalación
    winget_id: str = ""  # app de escritorio detectable vía `winget list` (sin cmd propio)


REGISTRY: list[Tool] = [
    # --- bootstrap (mise no puede instalarse a sí mismo) ---
    Tool(
        "mise",
        "mise",
        "gestor de versiones + runner de gates",
        "bootstrap",
        managed_by_mise=False,
        install_hint="https://mise.jdx.dev/getting-started.html",
    ),
    Tool(
        "git",
        "git",
        "control de versiones (memoria, ADR, handoff)",
        "bootstrap",
        managed_by_mise=False,
        install_hint="https://git-scm.com/downloads",
    ),
    Tool(
        "uv",
        "uv",
        "instalador de tools Python (copier, specify, ...)",
        "bootstrap",
        managed_by_mise=False,
        install_hint="https://docs.astral.sh/uv/getting-started/installation/",
    ),
    # --- por stack ---
    Tool(
        "node",
        "node",
        "runtime JS para frontend/build",
        "stack",
        stacks=("node", "angular", "react", "next", "nest", "vue", "svelte"),
    ),
    Tool("dotnet", "dotnet", "SDK .NET", "stack", stacks=("dotnet",)),
    Tool(
        "mvn",
        "mvn",
        "build Java (Maven)",
        "stack",
        stacks=("maven",),
        managed_by_mise=False,
        install_hint="https://maven.apache.org/install.html",
    ),
    Tool(
        "gradle",
        "gradle",
        "build Java (Gradle)",
        "stack",
        stacks=("gradle",),
        managed_by_mise=False,
        install_hint="https://gradle.org/install/",
    ),
    Tool(
        "go",
        "go",
        "toolchain Go (build/test)",
        "stack",
        stacks=("go",),
        managed_by_mise=False,
        install_hint="https://go.dev/doc/install",
    ),
    Tool(
        "cargo",
        "cargo",
        "toolchain Rust (build/test)",
        "stack",
        stacks=("rust",),
        managed_by_mise=False,
        install_hint="https://www.rust-lang.org/tools/install",
    ),
    # --- por feature/gate ---
    Tool(
        "copier",
        "copier",
        "scaffolding de la convención (tramalia init)",
        "feature",
        feature="init",
        managed_by_mise=False,
        install_hint="uv tool install copier",
    ),
    Tool(
        "repomix",
        "repomix",
        "snapshot de contexto para IA",
        "feature",
        feature="context",
        runtime="node",
        install_hint="mise use npm:repomix",
    ),
    Tool(
        "serena",
        "serena",
        "navegación/edición semántica (MCP)",
        "feature",
        feature="context",
        managed_by_mise=False,
        ephemeral=True,
        install_hint="uvx --from git+https://github.com/oraios/serena serena --help",
    ),
    Tool(
        "semgrep",
        "semgrep",
        "SAST (gate seguridad)",
        "feature",
        feature="security",
        install_hint="mise use pipx:semgrep",
    ),
    Tool(
        "gitleaks",
        "gitleaks",
        "secret scanning (gate seguridad)",
        "feature",
        feature="security",
        install_hint="mise use aqua:gitleaks",
    ),
    Tool(
        "sqlfluff",
        "sqlfluff",
        "lint SQL (gate base de datos)",
        "feature",
        feature="database",
        install_hint="mise use pipx:sqlfluff",
    ),
    Tool(
        "rulesync",
        "rulesync",
        "fan-out de reglas/skills por agente",
        "feature",
        feature="sync",
        runtime="node",
        install_hint="mise use npm:rulesync",
    ),
    Tool(
        "lhci",
        "lhci",
        "Lighthouse CI (gate UX/UI)",
        "feature",
        feature="ux",
        runtime="node",
        install_hint="mise use npm:@lhci/cli",
    ),
    Tool(
        "playwright",
        "playwright",
        "regresión visual + e2e (gate UX/UI)",
        "feature",
        feature="ux",
        runtime="node",
        install_hint="mise use npm:playwright",
    ),
    # memoria persistente opcional (nivel N2). Tramalia no la construye: la delega.
    Tool(
        "engram",
        "engram",
        "memoria persistente para agentes (N2, opcional)",
        "feature",
        feature="memory",
        managed_by_mise=False,
        install_hint="brew install gentleman-programming/tap/engram",
    ),
    # compresión de contexto/outputs (token-saver opcional). NO reemplaza la evidencia.
    Tool(
        "headroom",
        "headroom",
        "compresión de contexto/outputs (token-saver, opcional)",
        "feature",
        feature="context",
        managed_by_mise=False,
        install_hint='pip install "headroom-ai[all]"',
    ),
    # spec-driven development (opcional): complementa specs/ generada por init.
    Tool(
        "speckit",
        "specify",
        "spec-driven development (Spec Kit, opcional)",
        "feature",
        feature="specs",
        managed_by_mise=False,
        install_hint="uv tool install specify-cli --from git+https://github.com/github/spec-kit.git",
    ),
    # grafo de código pre-indexado (contexto quirúrgico en una llamada, opcional).
    # binario vía npm (@colbymchenry/codegraph); el wiring a agentes es aparte:
    # `codegraph install --skip-config` (nunca automatizado por Tramalia).
    Tool(
        "codegraph",
        "codegraph",
        "grafo de código pre-indexado (contexto, opcional)",
        "feature",
        feature="context",
        managed_by_mise=False,
        install_hint="npm i -g @colbymchenry/codegraph",
    ),
    # grafo de conocimiento desde código/docs/schemas (CLI+MCP+skill, opcional).
    Tool(
        "graphify",
        "graphify",
        "grafo de conocimiento del proyecto (contexto, opcional)",
        "feature",
        feature="context",
        managed_by_mise=False,
        install_hint="uv tool install graphifyy",
    ),
    # ingesta de documentos: PDF/Office/imágenes → Markdown (contexto, opcional).
    Tool(
        "markitdown",
        "markitdown",
        "convierte PDF/Office/imágenes a Markdown (ingesta, contexto)",
        "feature",
        feature="context",
        managed_by_mise=False,
        install_hint='pip install "markitdown[all]"',
    ),
    # analítica: Databricks Asset Bundles (gate bundle validate).
    Tool(
        "databricks",
        "databricks",
        "Databricks CLI (bundle validate, analítica)",
        "feature",
        feature="databricks",
        managed_by_mise=False,
        install_hint="https://docs.databricks.com/dev-tools/cli/install",
    ),
    # --- agentes CLI y hosts (detección informativa: Tramalia NO los configura) ---
    # El rol dice explícitamente "CLI" para no confundir con las apps de escritorio.
    Tool(
        "claude",
        "claude",
        "Claude Code — CLI del agente (no la app de escritorio)",
        "agent",
        managed_by_mise=False,
        install_hint="https://claude.com/claude-code",
    ),
    Tool(
        "codex",
        "codex",
        "OpenAI Codex — CLI del agente",
        "agent",
        managed_by_mise=False,
        install_hint="npm i -g @openai/codex",
    ),
    # el binario real en PATH se llama "agy" (no "antigravity"); Antigravity CLI
    # reemplazó oficialmente a Gemini CLI (descontinuado 2026-06-18). En Windows
    # se automatiza vía winget (Google.AntigravityCLI); ver installer._SYSTEM.
    Tool(
        "antigravity",
        "agy",
        "Antigravity CLI — comando `agy` (agente; ex-Gemini CLI)",
        "agent",
        managed_by_mise=False,
        install_hint="winget install -e --id Google.AntigravityCLI",
    ),
    # Antigravity IDE y 2.0 son apps de ESCRITORIO (hosts), no CLIs: se detectan
    # por `winget list` (winget_id), no por un comando en PATH.
    Tool(
        "antigravity-ide",
        "antigravity-ide",
        "Antigravity IDE — app de escritorio (fork de VS Code)",
        "agent",
        managed_by_mise=False,
        winget_id="Google.AntigravityIDE",
        install_hint="winget install -e --id Google.AntigravityIDE",
    ),
    Tool(
        "antigravity-2",
        "antigravity-2.0",
        "Antigravity 2.0 — app de escritorio (plataforma de agentes)",
        "agent",
        managed_by_mise=False,
        winget_id="Google.Antigravity",
        install_hint="winget install -e --id Google.Antigravity",
    ),
    Tool(
        "opencode",
        "opencode",
        "OpenCode — CLI del agente",
        "agent",
        managed_by_mise=False,
        install_hint="npm i -g opencode-ai",
    ),
    # OpenClaw: CLI real por npm (requiere Node). El `onboard`/daemon es config
    # posterior del usuario, no la instalación del binario.
    Tool(
        "openclaw",
        "openclaw",
        "OpenClaw — CLI gateway multi-modelo",
        "agent",
        managed_by_mise=False,
        runtime="node",
        install_hint="npm i -g openclaw",
    ),
    # Hermes Agent: CLI real, pero solo instalable vía script (`curl … | bash`),
    # que Tramalia NUNCA ejecuta automatizado — se muestra el comando exacto.
    Tool(
        "hermes",
        "hermes",
        "Hermes Agent — CLI (auto-mejora + gateway)",
        "agent",
        managed_by_mise=False,
        install_hint="curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash",
    ),
]

# documentación oficial de cada herramienta (tecla `d` en la TUI / docs del sitio)
DOCS: dict[str, str] = {
    "mise": "https://mise.jdx.dev",
    "git": "https://git-scm.com/doc",
    "uv": "https://docs.astral.sh/uv/",
    "node": "https://nodejs.org/docs",
    "dotnet": "https://learn.microsoft.com/dotnet/",
    "go": "https://go.dev/doc/",
    "cargo": "https://doc.rust-lang.org/cargo/",
    "mvn": "https://maven.apache.org/guides/",
    "gradle": "https://docs.gradle.org",
    "copier": "https://copier.readthedocs.io",
    "repomix": "https://repomix.com",
    "serena": "https://github.com/oraios/serena",
    "semgrep": "https://semgrep.dev/docs/",
    "gitleaks": "https://github.com/gitleaks/gitleaks",
    "sqlfluff": "https://docs.sqlfluff.com",
    "rulesync": "https://github.com/dyoshikawa/rulesync",
    "lhci": "https://github.com/GoogleChrome/lighthouse-ci",
    "playwright": "https://playwright.dev/docs/intro",
    "engram": "https://github.com/gentleman-programming/engram",
    "headroom": "https://github.com/headroom-ai/headroom",
    "speckit": "https://github.com/github/spec-kit",
    "codegraph": "https://github.com/colbymchenry/codegraph",
    "graphify": "https://github.com/irsbugs/graphifyy",
    "markitdown": "https://github.com/microsoft/markitdown",
    "databricks": "https://docs.databricks.com/dev-tools/cli/",
    "claude": "https://code.claude.com/docs",
    "codex": "https://developers.openai.com/codex",
    "antigravity": "https://antigravity.google/docs/cli-install",
    "antigravity-ide": "https://antigravity.google/docs",
    "antigravity-2": "https://antigravity.google/docs",
    "opencode": "https://opencode.ai/docs",
    "openclaw": "https://github.com/openclaw/openclaw",
    "hermes": "https://hermes-agent.nousresearch.com/docs/",
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
        cp = subprocess.run(["mise", "which", cmd], capture_output=True, text=True, timeout=timeout)
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


# `winget list` completo, cacheado UNA vez por proceso: las apps de escritorio
# (Antigravity IDE/2.0) no tienen comando en PATH, así que se detectan por su id.
_WINGET_STATE: dict = {"loaded": False, "text": ""}


def _winget_has(winget_id: str, timeout: float = 15.0) -> bool:
    if not winget_id:
        return False
    if not _WINGET_STATE["loaded"]:
        _WINGET_STATE["loaded"] = True
        if shutil.which("winget") is not None:
            try:
                cp = subprocess.run(
                    ["winget", "list", "--disable-interactivity"],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    encoding="utf-8",
                    errors="replace",
                )
                _WINGET_STATE["text"] = cp.stdout or ""
            except Exception:
                _WINGET_STATE["text"] = ""
    return winget_id.lower() in _WINGET_STATE["text"].lower()


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
        if tool.winget_id and _winget_has(tool.winget_id):
            return Status(tool, present=True, version=t("doctor.viawinget"))
        return Status(tool, present=False)
    version = None
    try:
        out = subprocess.run(
            [tool.cmd, *tool.version_args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        raw = (out.stdout or out.stderr or "").strip()
        if raw:
            version = raw.splitlines()[0].strip()
    except Exception:
        version = None
    return Status(tool, present=True, version=version)


# orden de preferencia para prellenar primary/reviewer en init: CLIs reales que
# pueden ejecutar `close` por shell. Excluye antigravity-ide/antigravity-2 (apps
# de escritorio sin shell propio) — no tiene sentido prellenarlas como ejecutor.
_AGENT_DETECT_ORDER = ("claude", "codex", "opencode", "antigravity", "openclaw", "hermes")


def detect_default_agents() -> tuple[str, str]:
    """(primary, reviewer) para prellenar config.json en `init`, basado en los
    agentes CLI REALMENTE instalados (no un ejemplo fijo).

    Dos agentes distintos detectados → el primero ejecuta, el segundo revisa
    (el patrón recomendado: cross-model review). Uno solo → se usa como ambos
    (editable después). Ninguno → cae a codex/claude como ejemplo editable,
    para que el proyecto no quede con campos vacíos."""
    presentes = [
        key
        for key in _AGENT_DETECT_ORDER
        if probe(next(t for t in REGISTRY if t.key == key)).present
    ]
    if len(presentes) >= 2:
        return presentes[0], presentes[1]
    if len(presentes) == 1:
        return presentes[0], presentes[0]
    return "codex", "claude"


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
