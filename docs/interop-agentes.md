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

- **Qué es / alcance:** toolkit para desarrollo guiado por especificaciones (constitution/spec/plan/tasks).
- **Requiere:** Python (uv).
- **Instalar:** `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`.
- **Tramalia la usa en:** opcional; complementa la carpeta `specs/` que `init` genera. Tramalia no la reimplementa.

## Gentle-AI — setup/onboarding de agentes (externo)

- **Qué es / alcance:** configura *con qué* agentes trabajas (modelos, skills, perfiles, memoria, MCP). Es un "bootstrap" de tu estación de trabajo IA.
- **Requiere:** ver su repo (Go).
- **Instalar:** según su documentación oficial.
- **Relación con Tramalia:** **onboarding externo, NO núcleo.** Gentle-AI deja tu máquina lista; Tramalia gobierna lo que esos agentes hacen *dentro del repo*. Se usan por separado para evitar doble ownership de configs/prompts.

## Agentes IA — los consumidores

- **Quiénes:** Claude Code, OpenAI Codex, Cursor, Antigravity, Gemini CLI, Copilot, Cline, etc.
- **Requiere:** la instalación oficial de cada uno (Tramalia **no** los instala).
- **Cómo interactúan con Tramalia:** **leen** `AGENTS.md` + `docs/ai/` (la convención que `init` deja), trabajan, y al cerrar usan `tramalia close` (por shell o vía la fachada MCP `tramalia mcp`). Tramalia no razona ni genera código: **gobierna** lo que ellos hacen.

## En una frase

rulesync **propaga** las reglas, copier/Spec Kit **estructuran**, Gentle-AI **prepara** los agentes, y los **agentes** ejecutan — todo bajo la convención que Tramalia mantiene y audita.
