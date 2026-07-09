# Modelos y esfuerzo por host

Tramalia es **neutral al host**: la convención (`AGENTS.md` estándar), el fan-out (`sync`) y la auditoría (`close --agent/--model` registra cualquier combinación) funcionan igual con cualquier agente. Pero **cada host controla modelo y esfuerzo a su manera** — esta es la matriz:

```mermaid
flowchart LR
    classDef s fill:#eef0ff,stroke:#8a83e0,color:#26215c;
    A["AGENTS.md<br/><small>única fuente</small>"]:::s -->|tramalia sync| B["Claude Code · Codex<br/>Antigravity · Hermes · OpenClaw…"]:::s
    B -->|cada uno con su modelo/esfuerzo| C["tramalia close --agent --model"]:::s
    C --> D["metadata.json + log<br/><small>auditoría unificada</small>"]:::s
```

| Host | Lee AGENTS.md | Selección de modelo | Esfuerzo / razonamiento | Subagentes con modelo |
|---|---|---|---|---|
| **Claude Code** (CLI/app) | ✅ nativo | `/model`, `opusplan` (Opus planea, Sonnet ejecuta) | `ultrathink` (un turno) · `/effort ultracode` (sesión + auto-orquestación) | ✅ nativo (`.claude/agents/`, los 5 de Tramalia) |
| **Codex** (CLI/app) | ✅ nativo | `/model` + **perfiles** en `config.toml` (`codex --profile`) | `model_reasoning_effort`: minimal → high, por perfil | simulados vía rulesync |
| **Antigravity** (CLI/IDE, absorbe Gemini CLI) | ✅ | selector por sesión | thinking budget del modelo | targets `antigravity-cli` / `antigravity-ide` en rulesync |
| **Hermes** | vía rulesync (target `hermesagent`) | perfil del gateway | parámetros API por request | convertidos |
| **OpenClaw** y gateways multi-modelo vía API | AGENTS.md es Markdown plano: lo leen si su config lo apunta | perfiles / API keys del gateway | `reasoning_effort` / thinking budget por request | manual |

!!! tip "¿Qué agentes tienes instalados?"
    `tramalia doctor` (y la pestaña Resumen de `tramalia ui`) ahora **detecta los agentes CLI presentes** en tu máquina — claude, codex, antigravity, opencode, openclaw, hermes — con su versión. Solo detección informativa: configurarlos sigue siendo territorio de cada agente (o de Gentle-AI).

## Apps de escritorio e IDEs

Todo lo anterior aplica **igual** a las apps: Claude Code desktop usa el mismo motor que su CLI (lee `AGENTS.md`, `.mcp.json`, `.claude/agents/` y ejecuta shell → `tramalia close` corre idéntico); Codex desktop y Antigravity IDE leen `AGENTS.md` nativo y reciben reglas vía `sync`. Para GUIs sin shell, la vía universal es la **fachada MCP** (`tramalia mcp`). Es la consecuencia del diseño repo-first: el gobierno vive en el repo, no en el host.

## La estrategia en la práctica

1. **Una sola fuente**: las reglas viven en `AGENTS.md`; los roles con ruteo de modelo en `.claude/agents/`. `tramalia sync` los propaga al resto de hosts.
2. **Cada host aplica su mecanismo**: en Claude Code el ruteo por rol es nativo; en Codex usas perfiles (`--profile deep` con effort high para planear, perfil normal para ejecutar); en Antigravity seleccionas por sesión.
3. **La auditoría unifica**: da igual el host — `tramalia close --agent codex --model gpt-5.2-high` deja en `metadata.json` *quién* y *con qué* cerró. `tramalia log` muestra la historia mezclada de todos los hosts.

## Revisión cruzada entre proveedores

[codex-plugin-cc](https://github.com/openai/codex-plugin-cc) (oficial de OpenAI) trae Codex **dentro** de Claude Code:

```text
/plugin marketplace add openai/codex-plugin-cc
/codex:review      # Codex revisa tu trabajo actual
/codex:transfer    # continúa la sesión en Codex con el mismo contexto
```

Encaja directo con el rol `revisor` de Tramalia: **dos modelos de proveedores distintos revisando el mismo evidence pack**, y ambos veredictos quedan en el handoff.

### Receta: planificar con Claude, ejecutar con Codex

1. Planificas en Claude Code (subagente `planificador`) → el plan queda en `specs/tasks.md`.
2. `/codex:transfer` traslada la sesión a Codex con el mismo contexto.
3. Ejecutas la tarea en Codex.
4. Cierras con `tramalia close --agent codex --model <el-que-usaste>` — la auditoría
   registra el cruce de proveedores; `tramalia log` muestra la historia mezclada.

Es un **workflow humano** (los plugins se invocan desde la conversación, no desde
la definición de un subagente); Tramalia lo gobierna en el cierre, no lo automatiza.

## Tope de modelos, portable entre proveedores

Los 5 subagentes que genera `init` traen un ruteo por rol (planificador/revisor →
opus, ejecutor → inherit, documentador → haiku, resolutor-profundo → fable). Pero
quizás **no tienes acceso a opus/fable**, o quieres bajar costo. El tope opcional
—`tramalia agents cap <nivel>`— hace que **ningún rol use un modelo por encima del
tope**; lo inferior se conserva. Ejemplo con tope `sonnet`:

| Rol | Sin tope | Tope `sonnet` |
|---|---|---|
| planificador | opus | **sonnet** |
| revisor | opus | **sonnet** |
| resolutor-profundo | fable | **sonnet** |
| documentador | haiku | haiku (ya está debajo) |
| ejecutor | inherit | inherit (sigue tu sesión) |

Ranking de capacidad: **fable > opus > sonnet > haiku**. Default: `none` (sin tope,
el ruteo completo). Se fija con `tramalia agents cap sonnet` o `init --model-cap sonnet`,
y se guarda en `.tramalia/config.json → agents.model_cap`.

**Cómo aplica en cada host** (enforcement donde se puede, convención donde no):

| Host | Cómo recibe el tope |
|---|---|
| **Claude Code** (CLI y app) | **Aplicado**: Tramalia reescribe el `model:` de `.claude/agents/` |
| **Codex** (CLI y app) | **Convención**: la regla de `AGENTS.md` le dice que respete el tope al elegir perfil/modelo — Tramalia **no** escribe su `~/.codex/config.toml` |
| **Antigravity `agy`** | Convención, ídem (modelo por sesión) |
| **OpenClaw / Hermes / gateways / otros** | Convención — leen `AGENTS.md` plano, así que hasta hosts no contemplados quedan cubiertos |

Como no escribimos configs de terceros (frontera con Gentle-AI), `agents cap` **imprime
la equivalencia por nivel de capacidad** para que la pegues tú (o Gentle-AI):

```text
tope sonnet → nivel estándar
  Codex: perfil estándar (model_reasoning_effort = medium)
  Antigravity (agy): modelo estándar (no el de razonamiento profundo)
```

Se expresa por **nivel de capacidad**, no por nombre de modelo de terceros (que
cambia seguido) — así los servicios que aún no existen mapean solos.

!!! tip "Los 5 archivos de agentes son tuyos"
    `.claude/agents/*.md` son editables a mano; `tramalia init` es idempotente y
    **nunca los pisa**. `agents cap` solo gestiona la línea `model:`; el resto es tuyo.

## Equivalencias de esfuerzo (chuleta)

| Quieres… | Claude Code | Codex CLI |
|---|---|---|
| razonar más en ESTE problema | `ultrathink` en el prompt | perfil con `model_reasoning_effort = "high"` |
| sesión entera en modo máximo | `/effort ultracode` | `codex --profile deep` |
| planear caro / ejecutar barato | `/model opusplan` o subagentes | dos perfiles (plan/exec) |
| registrar qué se usó | `tramalia close --model <m>` | `tramalia close --model <m>` |
