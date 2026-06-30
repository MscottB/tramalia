# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/). Este proyecto sigue versionado semántico.

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

### Diseñado / siguiente
- `tramalia learn` (importar aprendizajes a `docs/ai/06-intentos-fallidos.md`, con `--review`).
- Doble capa en `close` con Headroom (`review-summary.md` derivado, junto al output crudo).
- Publicar `tramalia-template` para habilitar `copier update`.
