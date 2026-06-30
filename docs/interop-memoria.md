# Memoria y eficiencia

Memoria persistente entre sesiones (**N2**) y compresión de tokens. Ambas son **interop opcional**: el núcleo de Tramalia ya tiene memoria en archivos (N0) y la fachada MCP (N1).

## Los 3 niveles de memoria

| Nivel | Qué es | Herramienta |
|---|---|---|
| **N0** | archivos del repo (`AGENTS.md`, `docs/ai/`) + CLI | núcleo de Tramalia |
| **N1** | fachada MCP de Tramalia | `tramalia mcp` |
| **N2** | memoria persistente real (grafo/semántica) | **Engram** · basic-memory · mem0 |

## Engram — memoria persistente N2 (recomendada)

- **Qué es / alcance:** recuerdo entre sesiones (decisiones, observaciones) en SQLite, con MCP, CLI, TUI y git-sync.
- **Requiere:** nada (binario, Go).
- **Instalar:** `brew install gentleman-programming/tap/engram` (otros SO: ver repo).
- **Tramalia la usa en:** `doctor` la detecta; `init` la cablea en `.mcp.json` **si está instalada**; `close`/`handoff --engram` exportan el cierre (opt-in).
- **Interactúa con / regla:** export **opt-in**, nunca secretos por defecto. No reemplaza la evidencia del repo; la complementa con recuerdo entre sesiones.

## basic-memory — memoria N2 en Markdown local

- **Qué es / alcance:** memoria persistente como archivos Markdown locales, vía MCP. Encaja con la filosofía repo-first.
- **Requiere:** Python (uv).
- **Instalar:** `uvx basic-memory` · `pip install basic-memory`.
- **Tramalia la usa en:** alternativa a Engram en `.mcp.json` (no por defecto).

## mem0 — memoria N2 semántica

- **Qué es / alcance:** capa de memoria semántica para agentes.
- **Requiere:** Python.
- **Instalar:** `pip install mem0ai`.
- **Tramalia la usa en:** alternativa N2 (no por defecto).

## Headroom — compresión / eficiencia de tokens

- **Qué es / alcance:** comprime tool outputs, logs y contexto antes de llegar al LLM (60-95% menos tokens). Modos librería, proxy, wrapper y MCP.
- **Requiere:** Python (o Node).
- **Instalar:** `pip install "headroom-ai[all]"` · MCP: `headroom mcp install`.
- **Tramalia la usa en:** **solo con `tramalia init --with-headroom`** (opt-in; por su modo proxy, nunca por defecto). `doctor` la detecta.
- **Interactúa con / REGLA DURA DEL MOAT:** *compresión ≠ evidencia*. El output crudo (`*-output.txt`) y `metadata.json` siempre se conservan en `.tramalia/evidence/`. Headroom **nunca** los modifica, reemplaza ni omite — solo genera vistas derivadas (`review-summary.md`). Su `headroom learn` debe redirigirse a `docs/ai/06-intentos-fallidos.md`, no escribir libre.

## Cómo encajan

**Engram/basic-memory/mem0** recuerdan *entre sesiones*; **Headroom** abarata *el contexto*. Ninguna toca el núcleo de gobierno (`close`, `log`, evidence pack). Tramalia las detecta y las cablea opt-in; tú decides si las montas.
