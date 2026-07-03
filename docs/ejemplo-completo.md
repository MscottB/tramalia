# Ejemplo completo: un proyecto real, paso a paso

Este es el recorrido de un proyecto ficticio pero realista — **`clinica-web`** (Angular + .NET + PostgreSQL) — mostrando **qué le hace Tramalia al proyecto** con cada opción propia y qué aporta **cada herramienta de terceros** en el camino.

## Día 0 · Instalar y gobernar el repo

```bash
cd clinica-web
pip install "tramalia-cli[pretty,tui]"     # solo Python 3.10+
tramalia init
```

`init` detecta el stack (`node · angular · dotnet · postgres`) y deja **37 archivos**. Qué cambia en tu proyecto, pieza por pieza:

| Lo que aparece | Efecto en el proyecto |
|---|---|
| `AGENTS.md` | **Todos** los agentes (Claude, Codex, Cursor…) leen las mismas reglas: orden de lectura, Ponytail/YAGNI, prohibiciones, cierre con `close` |
| `CLAUDE.md` (`@AGENTS.md`) | Claude Code queda alineado sin duplicar reglas |
| `docs/ai/00–11` | La memoria del proyecto: arquitectura, reglas de código/BD/seguridad/UX, ADR, **intentos fallidos**, handoff |
| `specs/` | Toda feature nace como tarea con ID en `tasks.md` — ese ID es el que audita `close` |
| `.tramalia/skills/01…13` | 13 workflows que le dicen al agente *cómo se trabaja aquí* |
| `.claude/agents/` | **5 subagentes con ruteo de modelo**: planificador→opus, ejecutor→inherit, revisor→opus, documentador→haiku, resolutor-profundo→fable |
| `mise.toml` | Los gates del stack detectado: `ng build`, `dotnet test`, `sqlfluff`, `semgrep`, `lhci`… |
| `.mcp.json` | Serena cableada (navegación semántica); Engram si está instalado |

```bash
tramalia doctor      # qué falta y cómo instalarlo
mise install         # ← mise (3º) instala TODO lo declarado: repomix, semgrep, sqlfluff…
```

**Herramientas de terceros que ya están actuando:** `mise` instala y versiona el toolchain; `git` versiona la memoria.

## Día 0.5 · Propagar a todos los agentes

```bash
tramalia sync
```

Dos pasadas de **rulesync** (3º): las reglas (`AGENTS.md` → `.cursor/rules/`, `.github/copilot-instructions.md`, `.clinerules/`) y **los 5 subagentes** (→ 15 archivos convertidos a Copilot/Cursor/Cline). Efecto: da igual qué agente abra el repo — mismas reglas, mismos roles.

## Día 1 · Una feature completa: TASK-001

**Pedido:** "registrar pacientes: tabla, endpoint y pantalla".

### 1. Planificar (subagente `planificador` → Opus)

En Claude Code pides *"planifica el registro de pacientes"*. El modelo principal delega al **planificador** (corre en Opus aunque tu sesión esté en Sonnet), que aplica la skill `01-spec-governance` y deja en `specs/tasks.md`:

```markdown
## TASK-001 — Registro de pacientes
- Gates aplicables: build · test · lint · security · database · ux
- Criterios de aceptación: alta de paciente con RUT válido…
```

### 2. Implementar (subagente `ejecutor` → inherit: tu modelo)

El ejecutor trabaja con ayuda de terceros, sin gastar contexto de más:

- **Serena** (MCP): lee *solo* el símbolo `PacienteController` que va a tocar — no el archivo entero.
- **Repomix** vía `tramalia context`: refresca `project-map.md` y `tech-stack.md`.
- Antes de inventar, lee `docs/ai/06-intentos-fallidos.md` (aquí vive lo que ya se descartó).

### 3. Cerrar con enforcement

```bash
tramalia close TASK-001 --model sonnet   # agente y revisor salen de config.json
```

Y aquí actúan **todos los gates de terceros a la vez** (vía mise):

| Gate | Herramienta (3º) | Qué valida en clinica-web |
|---|---|---|
| build | ng + dotnet | compila front y back |
| test | ng test + dotnet test | la lógica de pacientes |
| lint | eslint + dotnet format | estilo |
| security | **Semgrep + Gitleaks** | inputs sin validar, secretos filtrados |
| database | **SQLFluff** | la migración `create table pacientes` (¿PK? ¿rollback?) |
| ux | **Lighthouse + Playwright + axe** | accesibilidad y rendimiento de la pantalla |

Supongamos que SQLFluff encuentra un problema:

```text
✗ gate database: FALLA
✗ cierre BLOQUEADO por gates fallidos: database.
```

**Ese es el gobierno**: la tarea *no se puede* declarar terminada. El ejecutor corrige la migración y reintenta — ahora todo pasa y queda el **evidence pack**:

```text
.tramalia/evidence/2026-07-03-1015-TASK-001/
├── metadata.json         ← task, agente, MODELO (sonnet), gates, status: passed
├── database-output.txt   ← salida CRUDA de SQLFluff (oficial, inmutable)
├── security-output.txt   ← salida CRUDA de Semgrep/Gitleaks
└── … build/test/lint/ux + risks + rollback + next-steps
```

…y el **handoff** en `docs/ai/07` queda enlazado al pack.

### 4. Revisar (subagente `revisor` → Opus) y auditar

El revisor lee el pack (crudo + metadata) y registra su veredicto. Tú miras la historia:

```bash
tramalia log
✓ 2026-07-03-1015-TASK-001  ·  ✓ passed  ·  claude-code (sonnet)
```

O en el **dashboard**: `tramalia ui` → pestaña Auditoría, Enter sobre el cierre muestra su `metadata.json`.

## Extras opcionales (cuando los quieras)

| Activas | Herramienta (3º) | Efecto en el proyecto |
|---|---|---|
| `close --engram` | **Engram** | el cierre queda en memoria persistente entre sesiones (N2) |
| `init --with-headroom` | **Headroom** | comprime contexto/outputs para los agentes — **nunca** la evidencia cruda |
| `tramalia skills` + `init --with-ponytail` | **Ponytail** | clona su ruleset a `.tramalia/skills/ponytail/` y cablea su MCP (`ponytail_instructions`) |
| `/speckit.specify` | **Spec Kit** | potencia la carpeta `specs/` que Tramalia ya generó (doctor lo detecta) |
| servidor MCP de consulta | **codebase-memory-mcp** | grafo estructural del código como backend de contexto (instalar con `--skip-config`) |

## El antes y el después

| Sin Tramalia | Con Tramalia |
|---|---|
| Cada agente con sus reglas; el contexto se pierde entre sesiones | Una convención versionada que todos leen; handoff tipado |
| "Ya funciona" — sin prueba | `close` bloquea sin gates verdes; evidencia cruda + `metadata.json` |
| ¿Quién hizo esto y con qué? | `log`: tarea · agente · **modelo** · estado honesto |
| 10 herramientas sueltas que aprender una a una | `doctor` las diagnostica, `mise` las instala, Tramalia las orquesta |

!!! tip "Para reproducirlo"
    Todo lo de arriba funciona en cualquier repo: `pip install "tramalia-cli[pretty]"`, `tramalia init`, `tramalia doctor` — y desde ahí el flujo de [Flujo completo](flujo-completo.md).
