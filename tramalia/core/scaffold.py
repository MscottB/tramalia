"""Motor de `tramalia init`: renderiza la plantilla en el proyecto, idempotente.

- Los archivos de texto se copian desde tramalia/templates/project con sustitución
  simple de `{{ var }}` (compatibles con copier para el futuro `copier update`).
- `mise.toml` y `.mcp.json` se generan en código porque dependen del stack.
- Idempotente: si un archivo ya existe, se respeta (no se pisa trabajo previo).
"""

from __future__ import annotations

import datetime
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from tramalia.core.versiones_herramientas import (
    FUENTE_SERENA,
    VERSION_GITLEAKS,
    VERSION_LIGHTHOUSE_CI,
    VERSION_PLAYWRIGHT,
    VERSION_REPOMIX,
    VERSION_RULESYNC,
    VERSION_SEMGREP,
    VERSION_SQLFLUFF,
)

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "project"

# stacks que se consideran frontend (para el gate ux)
_FRONTEND = ("node", "angular", "react", "next", "vue", "svelte")


def _render(text: str, variables: dict) -> str:
    for key, value in variables.items():
        text = text.replace("{{ " + key + " }}", str(value))
        text = text.replace("{{" + key + "}}", str(value))
    return text


def _reglas_stack(stacks: list) -> dict:
    """Bloques de reglas específicos del stack detectado (para docs/ai stack-aware)."""
    code, db, ux = [], [], []
    if "angular" in stacks:
        code.append(
            "- **Angular**: componentes standalone; `OnPush`/señales para estado local; "
            "sin lógica en templates; `inject()` sobre constructor largo."
        )
    if any(s in stacks for s in ("react", "next")):
        code.append(
            "- **React/Next**: server components por defecto (Next); estado global solo "
            "si cruza rutas; keys estables en listas; sin `useEffect` para datos derivables."
        )
    if "dotnet" in stacks:
        code.append(
            "- **.NET**: async/await de punta a punta (nunca `.Result`/`.Wait()`); "
            "DTOs ≠ entidades de dominio; `ILogger` estructurado; config con `IOptions<T>`."
        )
    if "python" in stacks:
        code.append(
            "- **Python**: type hints en toda función pública; dataclasses para datos; "
            "ruff manda en estilo (no discutir formato en review)."
        )
    if "sqlserver" in stacks:
        db.append(
            "- **SQL Server (tsql)**: `SET NOCOUNT ON` en procedimientos; evitar "
            "`NOLOCK` como default; `datetime2`/UTC; paginación con `OFFSET-FETCH`."
        )
    if "postgres" in stacks:
        db.append(
            "- **PostgreSQL**: `timestamptz` siempre; índices parciales para flags; "
            "`EXPLAIN ANALYZE` antes de optimizar a ciegas; migraciones transaccionales."
        )
    if "databricks" in stacks:
        db.append(
            "- **Databricks**: Delta como formato por defecto; `OPTIMIZE`/`VACUUM` "
            "programados, no manuales; esquemas explícitos (nunca inferSchema en prod)."
        )
    if any(s in stacks for s in _FRONTEND):
        ux.append(
            "- Accesibilidad mínima verificable: labels en inputs, contraste AA, foco "
            "visible, navegable por teclado (el gate ux lo mide con axe/Lighthouse)."
        )
        if "tailwind" in stacks:
            ux.append(
                "- **Tailwind**: tokens del `tailwind.config` (no valores mágicos "
                "inline); extraer componente cuando una clase se repite 3+ veces."
            )
    else:
        ux.append("- (Proyecto sin frontend detectado: esta sección aplica si agregas UI.)")
    vacio = "- (Sin reglas específicas del stack detectado: completa según necesidad.)"
    return {
        "reglas_stack_codigo": "\n".join(code) or vacio,
        "reglas_stack_bd": "\n".join(db) or vacio,
        "reglas_stack_ux": "\n".join(ux),
    }


def _variables(answers: dict) -> dict:
    stacks = answers.get("stacks", [])
    return {
        "project_name": answers.get("project_name", "mi-proyecto"),
        "stack": " · ".join(stacks) if stacks else "—",
        "primary_agent": answers.get("primary_agent", "codex"),
        "reviewer_agent": answers.get("reviewer_agent", "claude"),
        "date": answers.get("fecha", datetime.date.today().isoformat()),
        **_reglas_stack(stacks),
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
        post = existing[existing.index(end) + len(end) :]
        return pre + block + post
    sep = "" if existing.endswith("\n\n") else ("\n" if existing.endswith("\n") else "\n\n")
    return existing + sep + block + "\n"


@dataclass(frozen=True, slots=True)
class ResultadoMergeMCP:
    """Describe a non-destructive MCP configuration merge.

    Attributes:
        texto: Original or safely merged JSON text.
        estado: Stable merge outcome for callers.
    """

    texto: str
    estado: Literal["sin_cambios", "fusionado", "json_invalido", "conflicto"]


def _objeto_json_sin_duplicados(pares: list[tuple[str, object]]) -> dict[str, object]:
    resultado: dict[str, object] = {}
    for clave, valor in pares:
        if clave in resultado:
            raise ValueError("clave JSON duplicada")
        resultado[clave] = valor
    return resultado


def _numero_json_finito(valor: str) -> float:
    numero = float(valor)
    if not math.isfinite(numero):
        raise ValueError("numero JSON no finito")
    return numero


def _rechazar_constante_json(_valor: str) -> object:
    raise ValueError("constante JSON no formal")


def _merge_mcp(existing_text: str, servers: dict) -> ResultadoMergeMCP:
    try:
        data = json.loads(
            existing_text,
            object_pairs_hook=_objeto_json_sin_duplicados,
            parse_constant=_rechazar_constante_json,
            parse_float=_numero_json_finito,
        )
    except (json.JSONDecodeError, RecursionError, ValueError):
        return ResultadoMergeMCP(existing_text, "json_invalido")
    if not isinstance(data, dict):
        return ResultadoMergeMCP(existing_text, "json_invalido")
    servidores_existentes = data.get("mcpServers", {})
    if not isinstance(servidores_existentes, dict):
        return ResultadoMergeMCP(existing_text, "json_invalido")
    for nombre, configuracion in servers.items():
        if nombre not in servidores_existentes:
            continue
        existente = servidores_existentes[nombre]
        if not isinstance(existente, dict) or not isinstance(configuracion, dict):
            return ResultadoMergeMCP(existing_text, "conflicto")
        if existente.get("command") != configuracion.get("command") or existente.get(
            "args"
        ) != configuracion.get("args"):
            return ResultadoMergeMCP(existing_text, "conflicto")
    faltantes = {
        nombre: configuracion
        for nombre, configuracion in servers.items()
        if nombre not in servidores_existentes
    }
    if not faltantes:
        return ResultadoMergeMCP(existing_text, "sin_cambios")
    servidores_existentes.update(faltantes)
    data["mcpServers"] = servidores_existentes
    return ResultadoMergeMCP(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        "fusionado",
    )


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
        if src.suffix == ".jinja":
            content = _render(src.read_text(encoding="utf-8"), variables)
            dest.write_text(content, encoding="utf-8", newline="\n")
        else:
            # Las plantillas estaticas auditadas conservan exactamente sus bytes.
            dest.write_bytes(src.read_bytes())
        results.append((rel, "creado"))

    # 2. archivos generados según stack (`.sqlfluff` solo aplica si hay SQL: builder→None)
    for name, builder in (
        ("mise.toml", build_mise_toml),
        (".mcp.json", build_mcp_json),
        (".sqlfluff", build_sqlfluff),
    ):
        content = builder(answers)
        if content is None:
            continue
        dest = root / name
        if dest.exists():
            state = "existe"
            if adopt and name == ".mcp.json":
                resultado_merge = _merge_mcp(
                    dest.read_text(encoding="utf-8"),
                    _mcp_servers(answers),
                )
                if resultado_merge.estado == "fusionado":
                    dest.write_text(resultado_merge.texto, encoding="utf-8")
                    state = "adaptado"
            results.append((name, state))
            continue
        dest.write_text(content, encoding="utf-8")
        results.append((name, "creado"))

    # 3. .gitignore: excluir habilidades externas sin perder las propias NN-*.
    from tramalia.core.habilidades import asegurar_gitignore_habilidades

    results.append((".gitignore", asegurar_gitignore_habilidades(root)))

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
        tools.append(f'"npm:repomix" = "{VERSION_REPOMIX}"')
    if "security" in features:
        tools += [
            f'"pipx:semgrep" = "{VERSION_SEMGREP}"',
            f'"aqua:gitleaks/gitleaks" = "{VERSION_GITLEAKS}"',
        ]
    if "database" in features:
        tools.append(f'"pipx:sqlfluff" = "{VERSION_SQLFLUFF}"')
    if "sync" in features:
        tools.append(f'"npm:rulesync" = "{VERSION_RULESYNC}"')
    if "ux" in features:
        tools += [
            f'"npm:@lhci/cli" = "{VERSION_LIGHTHOUSE_CI}"',
            f'"npm:playwright" = "{VERSION_PLAYWRIGHT}"',
        ]

    comandos_construccion: list[str] = []
    comandos_prueba: list[str] = []
    comandos_lint: list[str] = []
    if "angular" in stacks:
        comandos_construccion.append("ng build")
        comandos_prueba.append("ng test --watch=false")
        comandos_lint.append("ng lint")
    elif any(tecnologia in stacks for tecnologia in ("node", "react", "next", "vue", "svelte")):
        # Nest y otras API Node usan los scripts declarados por el proyecto.
        comandos_construccion.append("npm run build")
        comandos_prueba.append("npm test")
        comandos_lint.append("npm run lint")
    if "dotnet" in stacks:
        comandos_construccion.append("dotnet build")
        comandos_prueba.append("dotnet test")
    if "maven" in stacks:
        comandos_construccion.append("mvn -B compile")
        comandos_prueba.append("mvn -B test")
    elif "gradle" in stacks:
        comandos_construccion.append("gradle build -x test")
        comandos_prueba.append("gradle test")
    if "go" in stacks:
        comandos_construccion.append("go build ./...")
        comandos_prueba.append("go test ./...")
    if "rust" in stacks:
        comandos_construccion.append("cargo build")
        comandos_prueba.append("cargo test")
    if "python" in stacks:
        comandos_prueba.append("pytest")
        comandos_lint.append("ruff check")
    if "notebooks" in stacks:
        # Los outputs sucios rompen diffs y auditoria; esta puerta verifica limpieza.
        comandos_lint.append("uvx nbstripout --verify .")

    lines: list[str] = [
        "# Generado por tramalia init. Herramientas fijadas; tasks = puertas de calidad.",
        "",
    ]
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

    # Conservar los nombres externos de las tareas mise, no los identificadores internos.
    emit("build", comandos_construccion)
    emit("test", comandos_prueba)
    emit("lint", comandos_lint)
    if "security" in features:
        emit(
            "security",
            [
                "gitleaks git --redact --no-banner",
                "gitleaks dir . --redact --no-banner --max-target-megabytes 10",
                (
                    "semgrep scan --config "
                    ".tramalia/configuracion/semgrep/seguridad-python.yml "
                    "--error --metrics=off --disable-version-check"
                ),
            ],
        )
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
            "args": [
                "--from",
                FUENTE_SERENA,
                "serena",
                "start-mcp-server",
            ],
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
            "args": [".tramalia/habilidades/ponytail/ponytail-mcp/index.js"],
        }
    return servers


def build_mcp_json(answers: dict) -> str:
    import json

    servers = _mcp_servers(answers)
    note = (
        "Serena = código vivo (token-saver). Memoria persistente opcional (N2): "
        "Engram (`engram mcp`) o basic-memory."
    )
    if "engram" in servers:
        note += " Engram detectado y añadido."
    if "headroom" in servers:
        note += (
            " Headroom añadido por --with-headroom; si tu versión difiere, "
            "ajusta con `headroom mcp install`. No reemplaza la evidencia cruda."
        )
    if "ponytail" in servers:
        note += (
            " Ponytail añadido por --with-ponytail: ejecuta `tramalia skills` y "
            "`npm install` en .tramalia/habilidades/ponytail/ponytail-mcp antes de usarlo."
        )
    return json.dumps({"_note": note, "mcpServers": servers}, indent=2, ensure_ascii=False) + "\n"
