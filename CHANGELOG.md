# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/). Este proyecto sigue versionado semántico.

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
