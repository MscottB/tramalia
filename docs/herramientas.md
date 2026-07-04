# Herramientas: internas y externas

Tramalia tiene un **núcleo propio** (poco código, lo que nadie más hace bien) y **orquesta herramientas externas** (que invoca como programas separados vía CLI o MCP). Aquí está todo, con su alcance y licencia.

## Internas — el núcleo de Tramalia

Código propio de Tramalia (Python, MIT). Funciona **standalone, solo con la stdlib**; Rich/Questionary son extras opcionales para el "modo bonito".

| Comando / módulo | Qué hace | Tipo |
|---|---|---|
| `init` (`core/scaffold.py`) | genera la convención idempotente (AGENTS.md, docs/ai, mise.toml, .mcp.json) | core |
| `doctor` (`core/doctor.py`) | diagnostica herramientas requeridas/opcionales y cómo instalarlas | core |
| `detect` (`core/detect.py`) | detecta el stack y los gates aplicables | core |
| **`close` (`core/governance.py`)** | **ritual: gates → evidence (crudo) + `metadata.json` → handoff, con enforcement** | core ★ |
| **`log` (`core/governance.py`)** | **pista de auditoría: lee `metadata.json` de cada cierre** | core ★ |
| `evidence` (`core/evidence.py`) | crea el evidence pack de cierre | core |
| `handoff` (`core/handoff.py`) | agrega un traspaso estructurado a `docs/ai/07` | core |
| `skills` (`core/skills.py`) | clona/actualiza skills desde sus repos | core (usa git) |
| `mcp` (`mcp_server.py`) | fachada MCP: expone la convención como tools nativas | core (+ SDK mcp) |
| `ui` (`tui.py`) | dashboard TUI: Resumen · Auditoría · Cierre | core (+ extra `[tui]`) |
| `tools` (`core/tools.py`) | registro de herramientas y sondeo de presencia | interno |
| `proc` (`core/proc.py`) | ejecución de comandos robusta en Windows (shims `.cmd`) | interno |
| `render` / `menu` (`cli/`) | salida Rich-o-plano y menú interactivo | interno |

## Externas — orquestadas (no se reimplementan)

Cada una se invoca como **proceso separado** (CLI/MCP). Por eso **sus licencias no condicionan la de Tramalia**. Cómo instalar e integrar cada una: [Integraciones](interop.md).

### Bootstrap

La **base que instalas a mano primero** (no pueden instalarse solas); el resto lo trae `mise install`. Ver [Glosario](glosario.md).

| Herramienta | Rol / alcance | Runtime | Licencia |
|---|---|---|---|
| **mise** | versiones de tools + entorno + runner de gates | binario (Rust) | MIT |
| **git** | versionado de memoria, skills, evidencia | binario | GPL-2.0 |
| **uv** | instala tools Python (copier, serena…) | binario (Rust) | MIT / Apache-2.0 |

### Estructura y reglas

| Herramienta | Rol / alcance | Runtime | Licencia |
|---|---|---|---|
| **copier** | scaffolding con `update` (futuro) | Python | MIT |
| **rulesync** | fan-out de `AGENTS.md` a otros agentes | Node | MIT |
| **Spec Kit** | spec-driven development (`specify`, detectado por doctor) | Python | MIT |
| **Ponytail** | ruleset de minimalismo + MCP propio (vía `tramalia skills`) | Node (MCP) | ver repo |

### Contexto / inteligencia de código

| Herramienta | Rol / alcance | Runtime | Licencia |
|---|---|---|---|
| **Repomix** | snapshot empaquetado del repo para IA | Node | MIT |
| **Serena** | navegación/edición semántica (LSP, MCP) | Python | MIT |
| **codebase-memory-mcp** | grafo estructural del código (158 lenguajes) | binario (C/C++) | ver repo |
| **CodeGraph** | grafo pre-indexado con auto-sync (CLI + MCP) | binario | ver repo |

### Seguridad y base de datos (gates)

| Herramienta | Rol / alcance | Runtime | Licencia |
|---|---|---|---|
| **Semgrep** (CE) | SAST (gate seguridad) | Python | **LGPL-2.1** |
| **Gitleaks** | secret scanning (gate seguridad) | binario (Go) | MIT |
| **SQLFluff** | lint SQL (gate base de datos) | Python | MIT |

### UX/UI (gates)

| Herramienta | Rol / alcance | Runtime | Licencia |
|---|---|---|---|
| **Lighthouse CI** | rendimiento + a11y + best practices | Node | Apache-2.0 |
| **Playwright** | regresión visual + e2e | Node | Apache-2.0 |
| **axe-core** | accesibilidad | Node | **MPL-2.0** |
| **pa11y** | accesibilidad | Node | **LGPL-3.0** |
| **Storybook** | estados de componentes | Node | MIT |

### Memoria y eficiencia (interop opcional)

| Herramienta | Rol / alcance | Runtime | Licencia |
|---|---|---|---|
| **Engram** | memoria persistente N2 entre sesiones | binario (Go) | ver repo |
| **basic-memory / mem0** | memoria persistente alternativa | Python | ver repo |
| **Headroom** | compresión de contexto/outputs (token-saver) | Python/Node | ver repo |

### Dependencias Python de Tramalia (las únicas que se instalan/importan)

| Paquete | Uso | Licencia |
|---|---|---|
| **rich** | salida con color/tablas (incluida por defecto) | MIT |
| **questionary** | menús interactivos (incluida por defecto) | MIT |
| **mcp** | SDK de la fachada MCP (auto-oferta en `tramalia mcp` · `[full]`) | MIT |
| **textual** | dashboard TUI (auto-oferta en `tramalia ui` · `[full]`) | MIT |
| **pytest** | tests (extra `dev`) | MIT |
| mkdocs-material · mkdocs-static-i18n | solo para construir esta documentación | MIT |

!!! note "Lo importante"
    Las **copyleft** de la lista (Semgrep LGPL-2.1, pa11y LGPL-3.0, axe MPL-2.0, git GPL-2.0) son herramientas que Tramalia **invoca**, no enlaza ni redistribuye. No afectan la licencia de Tramalia. Las únicas que sí cuentan —las dependencias Python— son **todas MIT**.
