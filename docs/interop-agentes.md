# Reglas, skills y agentes

Cómo Tramalia propaga reglas a múltiples agentes, scaffolding y spec-driven, y la relación con los agentes IA y con configuradores externos como Gentle-AI.

## rulesync — fan-out de reglas

- **Qué es / alcance:** convierte `AGENTS.md` a los formatos propios de cada agente (Cursor, Copilot, Cline…), manteniendo **una sola fuente**.
- **Requiere:** **Node**.
- **Instalar:** `mise use npm:rulesync` · `npm i -g rulesync` · `npx rulesync`.
- **Tramalia la usa en:** `tramalia sync` → `rulesync convert --from agentsmd --to copilot,cursor,cline`.
- **Interactúa con:** `AGENTS.md` (la fuente única). Evita copias divergentes entre agentes.

## copier — scaffolding con `update`

- **Qué es / alcance:** motor de plantillas de proyecto; su superpoder es `copier update` (re-aplica mejoras de la plantilla sin pisar tu trabajo).
- **Requiere:** Python (uv).
- **Instalar:** `uv tool install copier` · `pipx install copier`.
- **Tramalia la usa en:** `init` (la convención es copier-compatible) y, a futuro, `update` → `copier update`.

## Spec Kit — spec-driven development (opcional)

- **Qué es / alcance:** toolkit para desarrollo guiado por especificaciones (constitution/spec/plan/tasks, slash-commands `/speckit.*` en los agentes). **No tiene MCP** (verificado).
- **Requiere:** Python (uv).
- **Instalar:** `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`.
- **Tramalia la usa en:** `doctor` detecta el binario `specify` (feature `specs`, opcional); complementa la carpeta `specs/` que `init` genera (tasks ↔ `close --task`, checklist ↔ evidence pack). Tramalia no la reimplementa.

## Ponytail — ruleset de minimalismo + MCP propio

- **Qué es / alcance:** el principio Ponytail (código mínimo necesario) empaquetado como skill/ruleset, **con servidor MCP propio** (`ponytail-mcp`): expone la tool `ponytail_instructions` y el prompt `ponytail` (modos lite/full/ultra).
- **Requiere:** git (para clonarlo) y **Node** (para su MCP). No está en npm: se usa desde su repo.
- **Instalar / cablear (3 pasos):**
  1. `tramalia skills` — lo clona a `.tramalia/skills/ponytail/` (ya viene declarado en `skills.toml`).
  2. `npm install` dentro de `.tramalia/skills/ponytail/ponytail-mcp/`.
  3. `tramalia init --with-ponytail` — agrega su servidor a `.mcp.json` (`node …/ponytail-mcp/index.js`).
- **Tramalia la usa en:** el principio ya va como regla en `AGENTS.md` y como skill `04-minimalist-engineering`; el ruleset completo clonado queda legible para los agentes, y el MCP es la vía nativa opcional.
- **Interactúa con:** todos los agentes (mismo ruleset por cualquier host); refuerza el gate de calidad.

## Gentle-AI — setup/onboarding de agentes (externo)

- **Qué es / alcance:** configura *con qué* agentes trabajas (modelos, skills, perfiles, memoria, MCP). Es un "bootstrap" de tu estación de trabajo IA.
- **Requiere:** ver su repo (Go).
- **Instalar:** según su documentación oficial.
- **Relación con Tramalia:** **onboarding externo, NO núcleo.** Gentle-AI deja tu máquina lista; Tramalia gobierna lo que esos agentes hacen *dentro del repo*. Se usan por separado para evitar doble ownership de configs/prompts.

## Subagentes por rol con ruteo de modelo

`tramalia init` genera `.claude/agents/` con **5 roles de gobierno** que Claude Code lee nativamente; cada uno declara su `model:` en el frontmatter:

| Agente | `model:` | Anclado a |
|---|---|---|
| `planificador` | opus | `specs/` + skill 01-spec-governance |
| `ejecutor` | **inherit** (respeta TU selección en la app) | `specs/tasks.md` + `tramalia close` |
| `revisor` | opus | evidence pack + skill 12-multi-agent-review |
| `documentador` | haiku | `docs/ai/` + skill 13-documentation-handoff |
| `resolutor-profundo` | fable (solo invocación explícita) | casos excepcionales + docs/ai/06 |

**Cómo funciona el ruteo:** tu `/model` controla la conversación principal *siempre*; el `model:` del agente aplica solo dentro de la tarea delegada (contexto aislado, se factura al precio de su propio modelo). Precedencia: override en la invocación > frontmatter > `inherit`.

**¿No tienes opus/fable, o quieres bajar costo?** Los 5 archivos son **tuyos** (editables; `init` no los pisa), y hay un **tope opcional**: `tramalia agents cap sonnet` baja a sonnet todo lo que esté por encima y conserva lo de abajo (haiku), sin tocar `inherit`. Es portable a otros hosts como convención — ver [Modelos y esfuerzo por host → Tope de modelos](multi-host.md#tope-de-modelos-portable-entre-proveedores).

**Multi-host:** `tramalia sync` propaga los subagentes vía rulesync (`--features rules,subagents`) a Copilot, Cursor, Cline y otros targets soportados. Es idempotente: si ya tienes tus propios agentes, `init` no los pisa.

**Auditoría:** `tramalia close --model <modelo>` registra en `metadata.json` qué modelo cerró la tarea — clave cuando ruteas modelos baratos y quieres saber qué cierres revisar con más ojo.

## Catálogo de skills externas (verificadas)

Además de las 16 skills propias ([administración y criterio](skills-guia.md)), `skills.toml` trae un **catálogo comentado** de fuentes externas en formato SKILL.md estándar — descomenta las que quieras y `tramalia skills` las clona:

| Fuente | Qué aporta | Encaja con |
|---|---|---|
| [anthropics/skills](https://github.com/anthropics/skills) (oficial) | document skills (PDF/DOCX/XLSX), creativas, técnicas | uso general |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | react-best-practices (40+ reglas) · **web-design-guidelines (100+ reglas a11y/UX)** · writing-guidelines | **gate ux** + docs |
| [superpowers](https://github.com/obra/superpowers) | TDD, debugging sistemático, planificación | skills 05/08 |
| [mattpocock/skills](https://github.com/mattpocock/skills) | TypeScript avanzado (incluye **grill-me**: preguntas rigurosas antes de implementar) | proyectos TS + skill 01 |
| [caveman](https://github.com/JuliusBrussee/caveman) | reduce ~65-75% los tokens de salida — usa el nivel **`lite`** (los agresivos pierden contexto); Ponytail va primero: [criterio de eficiencia](interop-memoria.md#el-criterio-cual-montar-y-cual-usar) | skill 03 (token-saver) |
| [Ponytail](https://github.com/DietrichGebert/ponytail) (activa por defecto) | minimalismo + MCP propio | skill 04 |

Otras fuentes de diseño/UX que puedes referenciar igual: [impeccable](https://github.com/pbakaus/impeccable), [ui-ux-pro-max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill), [emilkowalski/skills](https://github.com/emilkowalski/skills) (animación/UI). El marketplace oficial de plugins de Claude Code es [claude-plugins-official](https://github.com/anthropics/claude-plugins-official). [gstack](https://github.com/garrytan/gstack) es un pack de 31 skills que simulan un equipo completo (CEO, Designer, QA, Security OWASP+STRIDE, Release) — mismo espíritu que los subagentes de Tramalia, a otra escala; referencia útil, no se instala como dependencia.

## Revisión cruzada entre proveedores

[codex-plugin-cc](https://github.com/openai/codex-plugin-cc) (oficial de OpenAI) permite invocar **Codex desde dentro de Claude Code** para review o delegación (`/codex:review`, `/codex:transfer`). Encaja directo con el rol `revisor` de Tramalia: dos modelos distintos revisando el mismo evidence pack.

## Memoria personal vs. memoria de proyecto

[ai-second-brain](https://github.com/charlie947/ai-second-brain) construye una memoria personal buscable desde tu historial de chats (ChatGPT/Claude). Es un ángulo **distinto** al de Engram/N2: Engram recuerda *decisiones del proyecto* entre cierres; ai-second-brain recuerda *tu* historial de conversaciones. No se solapan; pueden convivir.

## Orquestación multiagente (externa)

Tramalia **no** lanza agentes en paralelo — eso es un slot aparte del ecosistema. Si lo necesitas: [Multica](https://github.com/multica-ai/multica) (agentes como "compañeros de equipo": asignas issues y ejecutan con daemon local + dashboard), Vibe Kanban o Conductor. Conviven bien: el orquestador reparte el trabajo, **Tramalia audita cada cierre** (`close`/`log` con agente y modelo).

### El patrón Ralph loop

[Ralph](https://ghuntley.com/ralph/) (Geoffrey Huntley) es un patrón, no una herramienta que se instala: un loop bash que re-alimenta el mismo prompt a un agente, iteración tras iteración, hasta completar un PRD. La clave es que **el progreso vive en archivos y git, no en el context window** — cada vuelta arranca con contexto limpio.

Encaja de forma casi literal con la estructura de Tramalia:

- **`specs/tasks.md`** = el PRD que Ralph necesita como fuente de verdad.
- **Los 5 subagentes** = el patrón "el contexto principal es un scheduler, delega el trabajo caro" que Ralph recomienda.
- **`.tramalia/evidence/`** = el estado que persiste fuera del context window entre iteraciones.
- **`tramalia close`** = el punto de "handoff" natural al final de cada vuelta del loop.

Si corres Tramalia en un loop tipo Ralph, cada iteración sería: leer `specs/tasks.md` → trabajar la siguiente tarea con el `ejecutor` → `tramalia close --task <ID>` → el loop continúa con la siguiente tarea, sin que el contexto crezca sin control.

## Tips para Claude Code (host más común)

- **`/model opusplan`** — Opus para planear, Sonnet para ejecutar: combina perfecto con los subagentes de arriba.
- **"ultrathink"** en el prompt — activa el razonamiento extendido máximo **para un solo turno**, sin cambiar la sesión (útil antes de delegar al `resolutor-profundo`).
- **`ultracode` / `/effort ultracode`** — a diferencia de ultrathink, es un modo de **sesión completa**: fija esfuerzo xhigh y auto-orquesta subagentes en paralelo para cada tarea sustancial. Resérvalo para trabajo grande (varias tareas de `specs/tasks.md` a la vez); es caro para ediciones rutinarias.
- **`/compact`** — compacta la conversación cuando el contexto crece; hazlo tras un `tramalia close` (el evidence pack ya conserva lo importante).

## Agentes IA — los consumidores

- **Quiénes:** Claude Code, OpenAI Codex, Cursor, Antigravity, Copilot, Cline, OpenCode, OpenClaw, Hermes, etc.
- **Requiere:** la instalación oficial de cada uno (Tramalia **no** los configura; sí puede facilitar la instalación del binario, ver abajo).
- **Cómo interactúan con Tramalia:** **leen** `AGENTS.md` + `docs/ai/` (la convención que `init` deja), trabajan, y al cerrar usan `tramalia close` (por shell o vía la fachada MCP `tramalia mcp`). Tramalia no razona ni genera código: **gobierna** lo que ellos hacen.
- **¿Cuáles tienes instalados?** `tramalia doctor` (y la pestaña Resumen de `tramalia ui`) **detecta las CLIs de agentes presentes** en tu máquina — solo informativo, nunca las configura. Matriz de modelo/esfuerzo por host: [Modelos y esfuerzo por host](multi-host.md).

> Los roles en la tabla de `doctor` dicen explícitamente **"CLI"** (Claude Code, OpenAI Codex…) para que no se confundan con las apps de escritorio del mismo nombre.

### Instalación que `doctor`/`ui` facilitan

| Host | Comando en PATH | Cómo se instala/detecta |
|---|---|---|
| **Claude Code CLI** | `claude` | instalación oficial (informativo) |
| **OpenAI Codex CLI** | `codex` | `npm i -g @openai/codex` (requiere Node) |
| **OpenCode** | `opencode` | `npm i -g opencode-ai` (requiere Node) |
| **OpenClaw** | `openclaw` | `npm i -g openclaw` (requiere Node) — el `onboard`/daemon es config tuya |
| **Hermes Agent** | `hermes` | solo por script `curl … \| bash` → **manual** (Tramalia nunca ejecuta pipes); se muestra el comando exacto |
| **Antigravity CLI** | `agy` | Windows: `winget install Google.AntigravityCLI` (automatizable); mac/linux: script oficial (manual) |
| **Antigravity IDE** | *(app de escritorio)* | `winget install Google.AntigravityIDE` — se detecta por `winget list` |
| **Antigravity 2.0** | *(app de escritorio)* | `winget install Google.Antigravity` — se detecta por `winget list` |

Antigravity trae **tres superficies** (2.0 desktop, IDE, y CLI `agy`); el binario del CLI se llama `agy`, no `antigravity` (reemplazó a Gemini CLI, descontinuado el 2026-06-18). Las apps de escritorio no tienen comando en PATH, así que `doctor` las verifica con `winget list` en vez de con un `--version`.

## En una frase

rulesync **propaga** las reglas, copier/Spec Kit **estructuran**, Gentle-AI **prepara** los agentes, y los **agentes** ejecutan — todo bajo la convención que Tramalia mantiene y audita.
