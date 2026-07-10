# Referencia de comandos

El **núcleo de gobierno** (`init`, `doctor`, `close`, `log`, `evidence`, `handoff`) es lógica propia y funciona **standalone, solo con Python**. El resto hace *shell-out* transparente a herramientas externas (interop opcional) y muestra su salida sin esconder errores.

| Comando | Qué hace | Tipo |
|---|---|---|
| `tramalia menu` | menú interactivo **en bucle** con prompts guiados | core |
| `tramalia ui` | **dashboard TUI** (Resumen · Auditoría · Cierre) | core (+ extra `[tui]`) |
| `tramalia init [--with-headroom --with-ponytail]` | genera la convención completa (idempotente) | core |
| `tramalia doctor [--fix]` | diagnostica herramientas y cómo instalarlas | core |
| `tramalia detect` | detecta el stack y los gates aplicables | core |
| **`tramalia close [TAREA]`** | **ritual de cierre: gates → evidence → handoff (enforcement)** | **core ★** |
| **`tramalia log`** | **pista de auditoría de los cierres** | **core ★** |
| `tramalia evidence [TAREA]` | crea el evidence pack de cierre | core |
| `tramalia handoff [TAREA]` | traspaso multiagente | core |
| `tramalia gates` | ejecuta los quality gates | interop (mise) |
| `tramalia context [build\|list\|set <backend>]` | genera memoria derivada; ve o fija el backend de navegación activo | interop (repomix + stdlib) |
| `tramalia agents [list\|cap <nivel>]` | ve o fija el tope de modelos de los subagentes | core |
| `tramalia sync [--to --features]` | propaga AGENTS.md **y subagentes** a otros agentes | interop (rulesync) |
| `tramalia skills [sync [<n>]\|list\|outdated\|enable\|disable\|add]` | administra skills: catálogo con estados y versión, actualizar una o todas, ver cuáles están atrasadas | interop (git) |
| `tramalia update` | actualiza todo | interop (mise + copier + skills) |
| `tramalia mcp` | levanta la fachada MCP | core (+ SDK mcp) |

## close — el ritual de gobierno

Es el comando estrella. En un paso: corre cada gate (`mise run <gate>`), **escribe sus salidas dentro del evidence pack**, genera el handoff y **bloquea el cierre si un gate falla** (a menos que pases `--allow-fail` con la excepción anotada en `risks.md`).

**Forma simple — el cierre del día a día son dos palabras:**

```bash
tramalia close              # tarea desde .tramalia/current-task.md; agentes desde config.json
tramalia close TASK-001     # tarea explícita (posicional)
```

**Cadena de resolución** (cada dato busca en orden):

| Dato | 1º | 2º | 3º | 4º |
|---|---|---|---|---|
| tarea | posicional | `--task` | ID en `.tramalia/current-task.md` | prompt si hay terminal; `TASK-000` en scripts |
| agente | `--agent` | `config.json → agents.primary` | — | — |
| revisor | `--reviewer` | `config.json → agents.reviewer` | — | — |

Flags avanzados (overrides): `--task · --agent · --reviewer · --model · --allow-fail · --engram`.

Funciona **standalone**: si `mise` no está, no inventa un resultado — registra en el pack que los gates no se ejecutaron como **excepción documentada**, y aun así deja evidence + handoff.

Cada cierre escribe **`metadata.json`** (task, agente, reviewer, timestamps, exit codes y `status` honesto: `passed` / `blocked` / `passed_with_exceptions` / `no_gates`). Los `*-output.txt` crudos son la evidencia oficial; ningún derivado (p. ej. compresión de Headroom) puede reemplazarlos.

**Métricas de dominio (ML/analítica):** si existe `.tramalia/metrics.json`, `close` lo copia crudo al pack y lo incrusta en `metadata.json`; si además hay `.tramalia/thresholds.json`, un umbral incumplido **bloquea el cierre** como un gate fallido. Ver [Analítica](analitica.md#metricas-y-umbrales-en-la-evidencia-mlanalitica).

## log — la pista de auditoría

Lee el `metadata.json` de cada cierre y lista los cierres (más reciente primero) con su `status` y el agente. Es el historial verificable del trabajo agéntico sobre el repo.

## doctor

Clasifica los requisitos y la tabla sale **agrupada por dominio** — base (bootstrap) · stack · **contexto · memoria · seguridad · base de datos · UX/UI · analítica** · convención · agentes CLI — y solo molesta con lo que aplica a tu proyecto. El estado dice claro si está **instalada o no** (`✓ instalada` / `○ no instalada (opcional)` / `✗ no instalada (requerida)`). Los hints de instalación son **por sistema operativo** (winget/brew/choco…) y por gestor disponible; también avisa si el PATH de uv necesita `uv tool update-shell`.

`--fix` arma el plan de instalación automatizado (mejor vía por herramienta: winget/brew, `mise use`, `uv tool`, `npm` solo con Node), te deja **seleccionar una o más** antes de ejecutar, y configura el PATH de uv si hace falta. En la TUI (tecla `i`), el selector muestra **todas** las faltantes — las automatizables marcables y las manuales listadas aparte. Detalle: [Instalación](instalacion.md#instalacion-automatizada-por-sistema).

## init

Genera de forma idempotente (no pisa lo existente): `AGENTS.md` único, `CLAUDE.md` (`@AGENTS.md`), **`docs/ai/` completo 00–13** (incl. deploy y analítica), **`specs/`** (constitution/specification/plan/tasks/checklist, integrada con `close`), **16 skills numeradas** en `.tramalia/skills/` (ver [Skills](skills-guia.md)), **5 subagentes con ruteo de modelo** en `.claude/agents/` (ver [Integraciones → agentes](interop-agentes.md)), `mise.toml` a la medida del stack, `.mcp.json` con Serena y `.tramalia/` (config, current-task, skills.toml).

Flags opt-in: `--with-headroom` (compresión) y `--with-ponytail` (MCP del ruleset de minimalismo; requiere `tramalia skills` + Node).

**`--adopt`** — para repos que **ya tienen agente**: integra el gobierno en un `AGENTS.md`/`.mcp.json`/`CLAUDE.md` existentes con un merge por marcadores (no destructivo) en vez de saltarlos. Sin `--adopt`, un `init` normal que detecta un `AGENTS.md` sin gobierno te avisa cómo hacerlo. Detalle: [Adoptar un repo existente](adopcion.md).

Al terminar, `init` registra la versión en `.tramalia/version` y —si detecta otros agentes CLI instalados— sugiere `tramalia sync` para propagar tus reglas a sus formatos (ver [`sync`](#sync) y [por qué solo se genera `.claude/`](interop-agentes.md#por-que-init-solo-genera-claude)).

## upgrade — actualizar un repo ya inicializado

Cuando actualizas Tramalia (`pip install -U tramalia-cli`), tus repos ya generados **no cambian solos**. `tramalia upgrade` los pone al día **sin pisar tu trabajo**:

- **Agrega** los archivos nuevos que falten (skills, páginas de `docs/ai/`, etc. que tu versión no tenía) y refresca el bloque de `.gitignore`.
- **No toca** ningún archivo que ya exista — nunca sobrescribe tus ediciones.
- Registra la versión en `.tramalia/version` y te reporta el balance (`N nuevos, M sin cambios`), apuntando al CHANGELOG por cambios de plantilla que quizás quieras adoptar a mano.

Es idempotente: córrelo tras cada actualización del CLI. Para el merge de 3 vías del contenido editado (estilo `copier update`) se apoyará a futuro en copier; por ahora, los cambios de plantilla sobre archivos que editaste se revisan a mano con el CHANGELOG como guía.

## ui — el dashboard TUI

`tramalia ui` abre un panel en la terminal (Textual; si falta, `tramalia ui` **ofrece instalarlo** ahí mismo) con cuatro vistas: **Resumen** (doctor en vivo + gates aplicables + backend de contexto), **Skills** (administrar propias y externas), **Auditoría** (los cierres de `log`, navegables; Enter muestra el `metadata.json`) y **Cierre** (formulario tarea/agente/revisor + salida de gates). Solo lee e invoca el core — cero lógica nueva. Guía completa de la interfaz: [La interfaz (TUI)](interfaz.md).

## agents

`tramalia agents list` muestra los 5 subagentes con su modelo actual (y el default de cada rol) más el tope activo. `tramalia agents cap <fable\|opus\|sonnet\|haiku\|none>` fija un **tope**: ningún rol usa un modelo por encima; lo inferior se conserva (`inherit` no se toca). Se guarda en `.tramalia/config.json → agents.model_cap`, se aplica a los frontmatter de Claude Code, e imprime la equivalencia por nivel para Codex/Antigravity (que Tramalia no configura). Default `none`. Detalle y matriz por host: [Modelos y esfuerzo por host](multi-host.md#tope-de-modelos-portable-entre-proveedores).

## context

`tramalia context` (sin argumento, o `build`) genera `.tramalia/context/` (project-map, tech-stack) — snapshot completo si hay Repomix, árbol stdlib si no. Además administra el **backend de navegación de código activo** del proyecto:

- **`tramalia context list`** — las 4 opciones que compiten por ese rol (Serena, CodeGraph, codebase-memory-mcp, Graphify) con su alcance, caso de uso ideal, cuál está instalada y cuál activa.
- **`tramalia context set <backend>`** — la fija en `.tramalia/config.json → context.backend` (default `serena`); queda también en `tools.json` para que los agentes la lean.

Por qué importa: si tienes varias instaladas y un agente alterna entre ellas de tarea en tarea, los índices quedan inconsistentes. Ver [Contexto e inteligencia de código](interop-contexto.md#si-tengo-varios-instalados-cual-usa-el-agente-contextbackend).

## evidence y handoff

Las dos piezas propias de Tramalia para trazabilidad:

- **`evidence`** crea `.tramalia/evidence/<fecha>-<task>/` con `summary`, `files-changed` (lee `git diff`), `commands`, las salidas de cada gate, `risks`, `rollback` y `next-steps`.
- **`handoff`** agrega una entrada estructurada a `docs/ai/07-handoff-agentes.md`.

## sync

`rulesync convert --from agentsmd --to copilot,cursor,cline --features rules`. No incluye Claude/Codex (ya leen `AGENTS.md` nativamente). Configurable con `--to`.

## mcp — la fachada (nivel 1)

Expone la convención como herramientas MCP nativas: `project_status`, `get_agent_rules`, `get_failed_attempts`, `get_current_task`, `doctor`, `record_handoff`, `build_evidence`, `build_context`. Conéctala en `.mcp.json`:

```json
{
  "mcpServers": {
    "tramalia": { "command": "tramalia", "args": ["mcp"] }
  }
}
```
