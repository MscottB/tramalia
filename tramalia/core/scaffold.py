"""Motor de `tramalia init`: renderiza la plantilla en el proyecto, idempotente.

- Los archivos de texto se copian desde tramalia/templates/project con sustitución
  simple de `{{ var }}` (compatibles con copier para el futuro `copier update`).
- `mise.toml` y `.mcp.json` se generan en código porque dependen del stack.
- Idempotente: si un archivo ya existe, se respeta (no se pisa trabajo previo).
"""

from __future__ import annotations

import datetime
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "project"

# stacks que se consideran frontend (para el gate ux)
_FRONTEND = ("node", "angular", "react", "vue", "svelte")


def _render(text: str, variables: dict) -> str:
    for key, value in variables.items():
        text = text.replace("{{ " + key + " }}", str(value))
        text = text.replace("{{" + key + "}}", str(value))
    return text


def _variables(answers: dict) -> dict:
    stacks = answers.get("stacks", [])
    return {
        "project_name": answers.get("project_name", "mi-proyecto"),
        "stack": " · ".join(stacks) if stacks else "—",
        "primary_agent": answers.get("primary_agent", "codex"),
        "reviewer_agent": answers.get("reviewer_agent", "claude"),
        "date": datetime.date.today().isoformat(),
    }


def scaffold(root: Path, answers: dict) -> list[tuple[str, str]]:
    """Devuelve [(ruta_relativa, 'creado'|'existe'), ...]."""
    variables = _variables(answers)
    results: list[tuple[str, str]] = []

    # 1. archivos de texto desde la plantilla
    for src in sorted(TEMPLATE_DIR.rglob("*")):
        if src.is_dir():
            continue
        rel = str(src.relative_to(TEMPLATE_DIR)).replace("\\", "/")
        if rel.endswith(".jinja"):
            rel = rel[:-6]
        dest = root / rel
        if dest.exists():
            results.append((rel, "existe"))
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        content = src.read_text(encoding="utf-8")
        if src.suffix == ".jinja":
            content = _render(content, variables)
        dest.write_text(content, encoding="utf-8")
        results.append((rel, "creado"))

    # 2. archivos generados según stack
    for name, builder in (("mise.toml", build_mise_toml), (".mcp.json", build_mcp_json)):
        dest = root / name
        if dest.exists():
            results.append((name, "existe"))
            continue
        dest.write_text(builder(answers), encoding="utf-8")
        results.append((name, "creado"))

    return results


def build_mise_toml(answers: dict) -> str:
    stacks = answers.get("stacks", [])
    features = answers.get("features", ())

    tools: list[str] = []
    if "python" in stacks:
        tools.append('python = "3.12"')
    if any(s in stacks for s in _FRONTEND):
        tools.append('node = "22"')
    if "context" in features:
        tools.append('"npm:repomix" = "latest"')
    if "security" in features:
        tools += ['"pipx:semgrep" = "latest"', '"aqua:gitleaks" = "latest"']
    if "database" in features:
        tools.append('"pipx:sqlfluff" = "latest"')
    if "sync" in features:
        tools.append('"npm:rulesync" = "latest"')
    if "ux" in features:
        tools += ['"npm:@lhci/cli" = "latest"', '"npm:playwright" = "latest"']

    build_cmds: list[str] = []
    test_cmds: list[str] = []
    lint_cmds: list[str] = []
    if "angular" in stacks:
        build_cmds.append("ng build"); test_cmds.append("ng test --watch=false"); lint_cmds.append("ng lint")
    elif any(s in stacks for s in ("node", "react", "vue", "svelte")):
        build_cmds.append("npm run build"); test_cmds.append("npm test"); lint_cmds.append("npm run lint")
    if "dotnet" in stacks:
        build_cmds.append("dotnet build"); test_cmds.append("dotnet test")
    if "python" in stacks:
        test_cmds.append("pytest"); lint_cmds.append("ruff check")

    lines: list[str] = ["# Generado por tramalia init. tools = auto-update; tasks = quality gates.", ""]
    lines.append("[tools]")
    lines += tools or ["# (sin herramientas declaradas para este stack)"]
    lines.append("")

    gate_tasks: list[str] = []

    def emit(name: str, cmds: list[str]) -> None:
        if not cmds:
            return
        lines.append(f"[tasks.{name}]")
        if len(cmds) == 1:
            lines.append(f'run = "{cmds[0]}"')
        else:
            joined = ", ".join(f'"{c}"' for c in cmds)
            lines.append(f"run = [{joined}]")
        lines.append("")
        gate_tasks.append(name)

    emit("build", build_cmds)
    emit("test", test_cmds)
    emit("lint", lint_cmds)
    if "security" in features:
        emit("security", ["gitleaks detect --no-banner", "semgrep scan --error --quiet"])
    if "database" in features:
        emit("database", ["sqlfluff lint ."])
    if "ux" in features:
        emit("ux", ["lhci autorun", "playwright test"])

    if gate_tasks:
        deps = ", ".join(f'"{t}"' for t in gate_tasks)
        lines.append("[tasks.gates]")
        lines.append(f"depends = [{deps}]")
        lines.append("")

    return "\n".join(lines)


def build_mcp_json(answers: dict) -> str:
    import json
    import shutil

    servers = {
        "serena": {
            "command": "uvx",
            "args": ["--from", "git+https://github.com/oraios/serena",
                     "serena", "start-mcp-server"],
        }
    }
    note = ("Serena = código vivo (token-saver). Memoria persistente opcional (N2): "
            "Engram (`engram mcp`) o basic-memory.")
    # Engram (memoria local, seguro) se auto-cablea si está instalado.
    if shutil.which("engram"):
        servers["engram"] = {"command": "engram", "args": ["mcp"]}
        note += " Engram detectado y añadido."
    # Headroom (compresión; puede ser proxy) NUNCA por defecto: solo con --with-headroom.
    if answers.get("with_headroom"):
        servers["headroom"] = {"command": "headroom", "args": ["mcp"]}
        note += (" Headroom añadido por --with-headroom; si tu versión difiere, "
                 "ajusta con `headroom mcp install`. No reemplaza la evidencia cruda.")
    # Ponytail MCP (ruleset de minimalismo): opt-in; requiere `tramalia skills`
    # (clona el repo) y `npm install` dentro de ponytail-mcp. Requiere Node.
    if answers.get("with_ponytail"):
        servers["ponytail"] = {
            "command": "node",
            "args": [".tramalia/skills/ponytail/ponytail-mcp/index.js"],
        }
        note += (" Ponytail añadido por --with-ponytail: ejecuta `tramalia skills` y "
                 "`npm install` en .tramalia/skills/ponytail/ponytail-mcp antes de usarlo.")
    return json.dumps({"_note": note, "mcpServers": servers}, indent=2, ensure_ascii=False) + "\n"
