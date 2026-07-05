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
_FRONTEND = ("node", "angular", "react", "next", "vue", "svelte")


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


# --- modo adopt: integrar el gobierno en archivos que el repo ya posee ---
# Se inyecta un bloque delimitado por marcadores (patrón "managed block"): re-ejecutar
# reemplaza el contenido entre marcadores sin tocar una línea del usuario.
_GOBIERNO_MARKER = "tramalia:gobierno"
_CLAUDE_MARKER = "tramalia:agents-import"

_GOBIERNO_BODY = """## Gobierno (Tramalia)

Este proyecto usa Tramalia para gobierno y evidencia. Antes de modificar código:

1. Lee `docs/ai/00-resumen-proyecto.md`, `01-arquitectura.md` y `.tramalia/current-task.md` + `specs/tasks.md`.
2. Aplica `docs/ai/02-reglas-codigo.md` (y las de BD/seguridad/UX según lo que toques).
3. Revisa `docs/ai/06-intentos-fallidos.md` antes de reintentar algo ya descartado.

**Cierre obligatorio:** termina cada tarea con `tramalia close --task <ID>` (gates → evidence pack con salidas crudas → handoff). No marques una tarea como hecha sin su evidence pack. Auditoría: `tramalia log`.

**Minimalismo (Ponytail/YAGNI):** haz lo mínimo correcto; no dupliques ni abstraigas de más. Usa primero las herramientas locales (`.tramalia/context`, Serena) antes de leer archivos enteros.

**Prohibiciones:** no expongas secretos/tokens; no ejecutes comandos destructivos sin confirmar; no conectes MCP remotos fuera de la allowlist."""


def _inject_block(existing: str, marker: str, body: str) -> str:
    """Inserta o reemplaza un bloque delimitado por marcadores. Idempotente."""
    start, end = f"<!-- {marker} inicio -->", f"<!-- {marker} fin -->"
    block = f"{start}\n{body}\n{end}"
    if start in existing and end in existing:
        pre = existing[: existing.index(start)]
        post = existing[existing.index(end) + len(end):]
        return pre + block + post
    sep = "" if existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
    return existing + sep + block + "\n"


def _merge_mcp(existing_text: str, servers: dict) -> tuple[str, bool]:
    """Fusiona servidores en un .mcp.json existente sin pisar los del usuario.

    Devuelve (texto, ok). ok=False si el JSON está malformado (no se toca).
    """
    import json
    try:
        data = json.loads(existing_text)
    except Exception:
        return existing_text, False
    if not isinstance(data, dict):
        return existing_text, False
    bag = data.setdefault("mcpServers", {})
    if not isinstance(bag, dict):
        return existing_text, False
    for name, cfg in servers.items():
        bag.setdefault(name, cfg)  # respeta cualquier servidor tuyo con el mismo nombre
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n", True


def _adopt_text(rel: str, dest: Path) -> str:
    """Integra el gobierno en un AGENTS.md/CLAUDE.md existente. Devuelve el estado."""
    if rel == "AGENTS.md":
        text = dest.read_text(encoding="utf-8")
        new = _inject_block(text, _GOBIERNO_MARKER, _GOBIERNO_BODY)
        if new != text:
            dest.write_text(new, encoding="utf-8")
            return "adaptado"
        return "existe"
    if rel == "CLAUDE.md":
        text = dest.read_text(encoding="utf-8")
        if "AGENTS.md" in text:
            return "existe"
        new = _inject_block(text, _CLAUDE_MARKER, "@AGENTS.md")
        dest.write_text(new, encoding="utf-8")
        return "adaptado"
    return "existe"


def scaffold(root: Path, answers: dict) -> list[tuple[str, str]]:
    """Devuelve [(ruta_relativa, 'creado'|'existe'|'adaptado'), ...].

    Con answers["adopt"], integra el gobierno en un AGENTS.md/CLAUDE.md/.mcp.json
    ya existentes (merge no destructivo) en vez de saltarlos.
    """
    variables = _variables(answers)
    adopt = bool(answers.get("adopt"))
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
            state = _adopt_text(rel, dest) if adopt else "existe"
            results.append((rel, state))
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        content = src.read_text(encoding="utf-8")
        if src.suffix == ".jinja":
            content = _render(content, variables)
        dest.write_text(content, encoding="utf-8")
        results.append((rel, "creado"))

    # 2. archivos generados según stack (`.sqlfluff` solo aplica si hay SQL: builder→None)
    for name, builder in (("mise.toml", build_mise_toml), (".mcp.json", build_mcp_json),
                          (".sqlfluff", build_sqlfluff)):
        content = builder(answers)
        if content is None:
            continue
        dest = root / name
        if dest.exists():
            state = "existe"
            if adopt and name == ".mcp.json":
                merged, ok = _merge_mcp(dest.read_text(encoding="utf-8"), _mcp_servers(answers))
                if not ok:
                    state = "existe (JSON inválido, sin tocar)"
                elif merged != dest.read_text(encoding="utf-8"):
                    dest.write_text(merged, encoding="utf-8")
                    state = "adaptado"
            results.append((name, state))
            continue
        dest.write_text(content, encoding="utf-8")
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
    elif any(s in stacks for s in ("node", "react", "next", "vue", "svelte")):
        # cubre también Nest (API Node): usa los scripts de package.json.
        build_cmds.append("npm run build"); test_cmds.append("npm test"); lint_cmds.append("npm run lint")
    if "dotnet" in stacks:
        build_cmds.append("dotnet build"); test_cmds.append("dotnet test")
    if "maven" in stacks:
        build_cmds.append("mvn -B compile"); test_cmds.append("mvn -B test")
    elif "gradle" in stacks:
        build_cmds.append("gradle build -x test"); test_cmds.append("gradle test")
    if "go" in stacks:
        build_cmds.append("go build ./..."); test_cmds.append("go test ./...")
    if "rust" in stacks:
        build_cmds.append("cargo build"); test_cmds.append("cargo test")
    if "python" in stacks:
        test_cmds.append("pytest"); lint_cmds.append("ruff check")
    if "notebooks" in stacks:
        # notebooks con outputs sucios rompen diffs y auditoría: verificar limpieza
        lint_cmds.append("uvx nbstripout --verify .")

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
        # el dialecto vive en .sqlfluff (soporta multi-motor por ruta), no en la CLI.
        emit("database", ["sqlfluff lint ."])
    if "databricks" in features:
        emit("bundle", ["databricks bundle validate"])
    if "notebooks" in stacks and answers.get("with_notebook_exec"):
        # opt-in: ejecuta los notebooks de punta a punta (equivale a "build" en datos).
        # requiere datos/entorno; ajusta la ruta si tus notebooks no están en notebooks/.
        emit("notebooks", ["jupyter execute notebooks/*.ipynb"])
    if "ux" in features:
        emit("ux", ["lhci autorun", "playwright test"])

    if gate_tasks:
        deps = ", ".join(f'"{t}"' for t in gate_tasks)
        lines.append("[tasks.gates]")
        lines.append(f"depends = [{deps}]")
        lines.append("")

    return "\n".join(lines)


def build_sqlfluff(answers: dict):
    """Genera `.sqlfluff` con el dialecto del gate `database`. None si no hay SQL.

    El dialecto no se puede adivinar del *.sql a ojo, así que se deriva del stack
    (Databricks / SQL Server via SqlClient / Postgres). Multi-motor: comenta cómo
    dar a cada carpeta su propio dialecto (SQLFluff usa el .sqlfluff más cercano).
    """
    stacks = answers.get("stacks", [])
    sql = [s for s in ("databricks", "sqlserver", "postgres") if s in stacks]
    if not sql:
        return None
    dialecto = {"databricks": "databricks", "sqlserver": "tsql", "postgres": "postgres"}[sql[0]]
    lines = [
        "# Generado por tramalia init: dialecto del gate `database` (sqlfluff).",
        "[sqlfluff]",
        f"dialect = {dialecto}",
        "",
    ]
    if len(sql) > 1:
        secundarios = ", ".join(sql[1:])
        lines += [
            f"# Detectado también: {secundarios}. SQLFluff usa un solo dialecto por config.",
            "# Para lintar otro motor con su gramática, crea un .sqlfluff con",
            "# `dialect = <tsql|postgres|...>` dentro de la carpeta de ese SQL.",
            "",
        ]
    return "\n".join(lines)


def _mcp_servers(answers: dict) -> dict:
    """Los servidores MCP que Tramalia cablea (reutilizado por init y por adopt)."""
    import shutil

    servers: dict = {
        "serena": {
            "command": "uvx",
            "args": ["--from", "git+https://github.com/oraios/serena",
                     "serena", "start-mcp-server"],
        }
    }
    # Engram (memoria local, seguro) se auto-cablea si está instalado.
    if shutil.which("engram"):
        servers["engram"] = {"command": "engram", "args": ["mcp"]}
    # Headroom (compresión; puede ser proxy) NUNCA por defecto: solo con --with-headroom.
    if answers.get("with_headroom"):
        servers["headroom"] = {"command": "headroom", "args": ["mcp"]}
    # Ponytail MCP (ruleset de minimalismo): opt-in; requiere `tramalia skills` + Node.
    if answers.get("with_ponytail"):
        servers["ponytail"] = {
            "command": "node",
            "args": [".tramalia/skills/ponytail/ponytail-mcp/index.js"],
        }
    return servers


def build_mcp_json(answers: dict) -> str:
    import json

    servers = _mcp_servers(answers)
    note = ("Serena = código vivo (token-saver). Memoria persistente opcional (N2): "
            "Engram (`engram mcp`) o basic-memory.")
    if "engram" in servers:
        note += " Engram detectado y añadido."
    if "headroom" in servers:
        note += (" Headroom añadido por --with-headroom; si tu versión difiere, "
                 "ajusta con `headroom mcp install`. No reemplaza la evidencia cruda.")
    if "ponytail" in servers:
        note += (" Ponytail añadido por --with-ponytail: ejecuta `tramalia skills` y "
                 "`npm install` en .tramalia/skills/ponytail/ponytail-mcp antes de usarlo.")
    return json.dumps({"_note": note, "mcpServers": servers}, indent=2, ensure_ascii=False) + "\n"
