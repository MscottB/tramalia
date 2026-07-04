# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/). Este proyecto sigue versionado semántico.

## [0.10.0] - 2026-07-03

Instalación unificada en un comando + catálogo de skills externas.

### Instalación
- **`pip install tramalia-cli` es ahora la única línea necesaria**: Rich y
  Questionary (puras-Python, diminutas) pasan a ser dependencias por defecto —
  la experiencia recomendada sin corchetes. El núcleo sigue degradando a stdlib
  si faltan (`--plain`).
- **Auto-oferta de extras**: `tramalia ui` y `tramalia mcp` ofrecen instalar
  Textual/SDK MCP ahí mismo la primera vez (solo con terminal interactiva;
  en scripts imprimen el hint). Si el entorno bloquea pip (externally-managed,
  pipx), muestran el comando manual y `pipx inject` sin traceback.
- Alias `[pretty]` queda vacío (compatibilidad); nuevo alias `[full]`
  (Textual + SDK MCP de una vez).

### Integraciones (revisión del ecosistema)
- **Catálogo de skills externas verificadas** en `skills.toml` (comentadas):
  anthropics/skills (oficial), vercel-labs/agent-skills (web-design-guidelines
  complementa el gate ux), superpowers, mattpocock/skills.
- **CodeGraph** detectado por `doctor` (feature `context`): grafo pre-indexado
  con auto-sync, alternativa a Serena/codebase-memory-mcp.
- Docs: sección de orquestación multiagente externa (Multica/Vibe Kanban) y
  tips de Claude Code (`/model opusplan`, "ultrathink", `/compact`).

### Calidad
- 65 tests con pytest.

## [0.9.1] - 2026-07-03

Primer lanzamiento a PyPI.

### Empaquetado
- `[project.urls]` en `pyproject.toml` (Homepage/Documentation → sitio mkdocs,
  Repository, Changelog, Issues) — visibles en el sidebar de la página de PyPI.
- Clasificadores de PyPI (Development Status, Python 3.10–3.13, Topics).
- Workflow `.github/workflows/publish.yml`: construye sdist+wheel y publica en
  PyPI en cada GitHub Release, vía **Trusted Publishing** (OIDC, sin tokens).
- Validado con `twine check` (PASSED) e instalación limpia del wheel en venv nuevo.

### Documentación
- Instrucciones de instalación actualizadas a `pip install "tramalia-cli[...]"`
  para usuario final (README ES/EN, manual, instalación, flujo, ejemplo completo);
  la instalación editable (`pip install -e ".[dev]"`) queda reservada para
  contribuidores, con nota explícita apuntando a `CONTRIBUTING.md`.

## [0.9.0] - 2026-07-03

Comandos simples: el cierre del día a día son dos palabras.

### CLI
- **Task posicional** en `close`/`handoff`/`evidence`: `tramalia close TASK-001`
  (los flags `--task/--agent/--reviewer` siguen funcionando como overrides).
- **Defaults desde el proyecto**: agente/revisor salen de `.tramalia/config.json`
  (`agents.primary`/`agents.reviewer`); la tarea, del ID declarado en
  `.tramalia/current-task.md`. Resultado: `tramalia close` a secas cierra la tarea
  en curso con los agentes configurados.
- Prompt interactivo solo si hay terminal (los scripts caen a `TASK-000`, nunca
  se cuelgan). El menú prellena sus preguntas con estos mismos defaults.

### Documentación
- Tabla completa de los 15 comandos con ejemplos simples en ambos README.
- Referencia de comandos reescrita "forma simple primero" (sin corchetes en los
  títulos); cadena de resolución documentada en comandos/manual/flujo/ejemplo.

### Calidad
- 60 tests con pytest.

## [0.8.0] - 2026-07-03

Subagentes por rol con ruteo de modelo y auditoría de modelo.

### Subagentes (init)
- `.claude/agents/` con **5 roles de gobierno** que Claude Code lee nativamente:
  planificador→opus, **ejecutor→inherit** (respeta la selección del usuario en la app),
  revisor→opus, documentador→haiku, resolutor-profundo→fable (solo invocación explícita).
- Cada agente ancla su workflow a skills/comandos de Tramalia; idempotente (no pisa
  agentes existentes).

### Fan-out multi-host
- `tramalia sync` gana `--features` (def. `rules,subagents`): propaga también los
  subagentes vía rulesync a Copilot, Cursor, Cline y demás targets soportados.

### Auditoría de modelo
- `tramalia close --model <modelo>` registra en `metadata.json` qué modelo cerró la
  tarea; `tramalia log` lo muestra (`codex (opus)`).

### Presentación
- README en inglés pasa a ser el principal (`README.md`); el español queda en
  `README.es.md`. El About del repo enlaza la documentación.

### Calidad
- 52 tests con pytest.

## [0.7.0] - 2026-07-01

Convención completa, nuevas integraciones y dashboard TUI.

### Convención (init)
- `docs/ai/` completo **00–11** (se agregan 01-arquitectura, 02-reglas-codigo,
  05-decisiones-adr, 08-comandos-proyecto, 09-quality-gates, 10-contexto-operativo).
- Carpeta `specs/` generada (constitution, specification, plan, tasks, checklist),
  integrada con el flujo: `tasks.md` ↔ `close --task`, `checklist.md` ↔ evidence pack.
- **13 skills numeradas** en `.tramalia/skills/` (01-spec-governance … 13-documentation-handoff),
  cada una anclada a comandos/gates de Tramalia.
- `.tramalia/current-task.md` placeholder; AGENTS.md con orden de lectura completo.

### Integraciones
- **Spec Kit** detectado por `doctor` (binario `specify`, feature `specs`).
- **Ponytail**: referencia activa en `skills.toml` (se clona con `tramalia skills`) y
  `init --with-ponytail` cablea su servidor MCP (`ponytail-mcp`) en `.mcp.json`.

### Interfaz
- **`tramalia ui`** — dashboard TUI (Textual, extra `[tui]`): Resumen con doctor en vivo,
  Auditoría navegable con detalle de `metadata.json`, y Cierre guiado con salida de gates.
- `tramalia menu` ahora corre **en bucle**, muestra el último cierre y hace
  **prompts guiados** (tarea/agente/revisor) para close/handoff/evidence.

### Arreglos
- `update` ejecuta también `skills sync` (antes solo `mise upgrade`).
- `close` enlaza la ruta del evidence pack dentro de la entrada de handoff.

### Calidad
- 47 tests con pytest.

## [0.6.0] - 2026-06-30

Primera muestra pública (preview) de Tramalia: capa repo-first de gobierno y evidencia.

### Núcleo (gobierno)
- `tramalia close` — ritual de cierre: gates → evidence (salida cruda) + `metadata.json` → handoff, con enforcement (bloquea si un gate falla salvo `--allow-fail`).
- `tramalia log` — pista de auditoría que lee `metadata.json`; `status` honesto (`passed` / `blocked` / `passed_with_exceptions` / `no_gates`).
- `tramalia evidence`, `handoff` — evidence pack e historial de traspasos.
- `tramalia init` — genera la convención idempotente (AGENTS.md, docs/ai/, mise.toml, .mcp.json, .tramalia/).
- `tramalia doctor` / `detect` — diagnóstico de herramientas y detección de stack.
- `tramalia mcp` — fachada MCP (nivel 1) con 8 herramientas.

### Interop (opcional)
- `gates` → mise · `context` → Repomix/Serena · `sync` → rulesync · `skills` → git · `update` → mise/copier.
- Memoria N2: Engram (auto-cableado si está) · basic-memory · mem0.
- Compresión: Headroom (`--with-headroom`, opt-in; nunca reemplaza la evidencia).
- Inteligencia de código: codebase-memory-mcp (backend opcional de `context`).

### Calidad y empaquetado
- 34 tests con pytest.
- Plantilla empaquetada en el wheel; sitio de documentación bilingüe (ES/EN) con MkDocs Material.
- Licencia Apache-2.0.
