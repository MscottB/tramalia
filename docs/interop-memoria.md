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

## El criterio: cuál montar y cuál usar

**Memoria N2 — desempate** (elige **una**, no disperses la memoria):

- **Engram** — el default recomendado: binario sin dependencias, git-sync, y `close --engram` ya lo integra con el cierre.
- **basic-memory** — si quieres la memoria **legible dentro del repo** como Markdown (lo más repo-first); ideal cuando la memoria debe viajar con el código.
- **mem0** — solo si necesitas recuerdo **semántico** (embeddings) y aceptas más setup.
- Si hay **más de una instalada**: usa una sola como memoria activa y déjalo escrito en `AGENTS.md` — dos memorias paralelas divergen y ninguna es confiable.
- Si **no hay ninguna**: se sigue con normalidad — N0 (archivos del repo + git) ya es memoria; N2 es acelerador, no requisito.

**Eficiencia de tokens — orden de preferencia:**

1. **Ponytail** primero — es *preventivo*: el ruleset de minimalismo hace que el agente genere menos código y menos ruido desde el inicio (cero riesgo, sin infraestructura; `init --with-ponytail`). El token más barato es el que nunca se genera.
2. **caveman**, nivel **`lite`** — comprime la *salida* del agente (~65% menos tokens de salida). Tiene niveles `lite` / `full` / `ultra`: usa **`lite`** — los niveles agresivos ahorran más pero pierden contexto y claridad en las respuestas; `lite` mantiene el balance. Código, comandos y errores se conservan byte a byte en todos los niveles.
3. **Headroom** al final — el mayor ahorro (60-95%, comprime *el contexto de entrada*), pero opera como proxy: solo opt-in explícito (`--with-headroom`) y bajo la regla dura del moat (jamás toca la evidencia cruda).

Los tres atacan cosas distintas (generar menos · responder más corto · comprimir la entrada), así que **pueden convivir** — pero adopta en ese orden: cada paso siguiente agrega ahorro y también complejidad.

**Frontera con el conocimiento externo:** la memoria guarda *lo que TU proyecto aprendió* (decisiones, intentos fallidos); [notebooklm-mcp](interop-contexto.md#notebooklm-mcp-conocimiento-externo-curado-mcp-cloud) responde *lo que otros documentaron* (docs de librerías). No las mezcles: las decisiones del proyecto van a Engram/`docs/ai/`, nunca a un servicio cloud.

Ninguna toca el núcleo de gobierno (`close`, `log`, evidence pack). Tramalia las detecta y las cablea opt-in; tú decides si las montas.
