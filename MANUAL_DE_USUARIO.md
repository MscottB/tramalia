# Tramalia — Manual de usuario y proceso de construcción

> Capa fina que **orquesta herramientas externas** para apoyar el desarrollo de
> software con múltiples agentes IA. Este documento explica cómo usarla (manual)
> y cómo se construyó (proceso). El diseño conceptual completo está en
> [`Tramalia_Diseno_Consolidado_v0_6.md`](./Tramalia_Diseno_Consolidado_v0_6.md).

---

## Parte 1 · Qué es, en una frase

Tramalia **no implementa capacidades, las orquesta**. Diagnostica con `doctor`,
delega la ejecución a herramientas externas (mise, copier, serena, semgrep,
rulesync…) y solo construye lo que nadie más hace bien: el **detector** de stack,
el **evidence pack**, el **handoff** y la **fachada MCP**. La "interfaz" real para
el día a día son tus agentes IA leyendo los archivos que Tramalia deja en el repo.

---

## Parte 2 · Instalación y requisitos

### 2.1 Para correr Tramalia: solo Python

Tramalia en sí **solo requiere Python 3.10+**. No tiene ninguna dependencia Node.

```bash
pip install tramalia-cli              # base — corre con solo la stdlib (terminal básica)
pip install "tramalia-cli[pretty]"    # modo bonito: Rich + Questionary (recomendado)
pip install "tramalia-cli[mcp]"       # fachada MCP (nivel 1)
```

La salida se ve bonita automáticamente si `rich`/`questionary` están instalados; si
no, cae a texto plano. `--plain` fuerza el modo plano.

¿Vas a contribuir? Clona el repo e instala en modo editable con las deps de
desarrollo: `pip install -e ".[dev]"` (ver [CONTRIBUTING.md](CONTRIBUTING.md)).

### 2.2 Para una buena experiencia: las herramientas externas

Tramalia **orquesta** herramientas externas. No las necesitas todas para empezar,
pero sí para usar cada feature. `tramalia doctor` te dice exactamente cuáles faltan
para *tu* proyecto. Importante: **algunas son Node**, no Python.

| Herramienta | Para qué | Runtime | ¿Obligatoria? | Cómo instalar |
|---|---|---|---|---|
| **Python 3.10+** | correr Tramalia | — | **sí** | python.org · uv |
| **mise** | instala/versiona el resto + corre gates | binario | recomendada (bootstrap) | https://mise.jdx.dev |
| **git** | memoria versionada, skills, evidence | binario | recomendada | git-scm.com |
| **uv** | instala tools Python (copier, serena) | binario | recomendada | astral.sh/uv |
| **Node 18+** | lo exigen `sync`, gate `ux` y `context` (repomix) | — | si usas esas features | `mise use node@22` o nodejs.org |
| rich · questionary | CLI interactiva y con color | Python | opcional | `pip install "tramalia-cli[pretty]"` |
| SDK mcp | fachada MCP | Python | opcional | `pip install "tramalia-cli[mcp]"` |
| copier | `init` avanzado / `copier update` | Python | opcional | `uv tool install copier` |
| serena | navegación semántica (MCP) | Python | opcional | `uvx … serena` |
| semgrep · gitleaks | gate seguridad | Python/binario | opcional | `mise use pipx:semgrep` · `aqua:gitleaks` |
| sqlfluff | gate base de datos | Python | opcional | `mise use pipx:sqlfluff` |
| **repomix** | snapshot de contexto (`context`) | **Node** | opcional | `mise use npm:repomix` |
| **rulesync** | fan-out de reglas (`sync`) | **Node** | opcional | `mise use npm:rulesync` |
| **lighthouse · playwright** | gate UX/UI (`ux`) | **Node** | opcional | `mise use npm:@lhci/cli` · `npm:playwright` |
| **engram** | memoria persistente N2 (`--engram`) | binario (Go) | opcional | `brew install gentleman-programming/tap/engram` |
| **headroom** | compresión de contexto/outputs (token-saver) | — | opcional | ver `github.com/headroomlabs-ai/headroom` |

### 2.3 Orden recomendado (experiencia completa)

```bash
# 1. Tramalia
pip install "tramalia-cli[pretty,mcp]"

# 2. Bootstrap (mise no se instala a sí mismo; ver enlace que da doctor)
#    instala mise, git, uv según tu SO

# 3. En tu proyecto: genera la convención y deja que mise instale el resto
tramalia init
mise install            # instala las tools declaradas en mise.toml

# 4. Si vas a usar sync / gate ux / repomix → necesitas Node
mise use node@22

# 5. Verifica que no falte nada para tu proyecto
tramalia doctor
```

> Si trabajas un proyecto sin frontend y no usas `sync`, **nunca necesitas Node**.

---

## Parte 3 · Manual de comandos

> El **núcleo de gobierno** (`init`, `doctor`, `close`, `log`, `evidence`, `handoff`)
> funciona standalone, solo con Python. El resto es interop opcional con herramientas
> externas (mise, repomix, rulesync…).

### `tramalia close [TAREA]` ★
El comando estrella, el **ritual de gobierno** en un paso:
1. Corre cada gate (`mise run <gate>`) capturando su salida.
2. La escribe **cruda dentro del evidence pack** (`*-output.txt` + `gates-status.md`)
   y genera **`metadata.json`** (task, agente, **modelo** con `--model`, reviewer,
   timestamps, exit codes, status).
3. Genera el **handoff**.
4. **Bloquea el cierre si un gate falla** (exit 1) salvo `--allow-fail` con la
   excepción anotada en `risks.md`.

El `status` en `metadata.json` es honesto: `passed` · `blocked` ·
`passed_with_exceptions` (forzado) · `no_gates` (sin mise). `tramalia log` lo lee.

Standalone: si `mise` no está, no inventa resultado — registra "gates no ejecutados"
como excepción documentada y aun así deja evidence + handoff. Con `--engram` exporta
el cierre a la memoria persistente N2.

**Forma simple** (los defaults hacen el trabajo):

```bash
tramalia close              # tarea: .tramalia/current-task.md · agentes: config.json
tramalia close TASK-001     # tarea explícita (posicional)
```

Cadena de resolución: tarea = posicional > `--task` > ID en `current-task.md` >
prompt interactivo (o `TASK-000` en scripts). Agente/revisor = flag >
`config.json → agents.primary/reviewer`. Flags avanzados: `--model`,
`--allow-fail`, `--engram`.

### `tramalia log`
Pista de auditoría: lista los cierres (un evidence pack por tarea), del más reciente
al más antiguo, indicando si los gates pasaron (`✓`), fallaron (`✗`) o no corrieron (`○`).

### `tramalia doctor [--fix]`
Diagnostica qué herramientas necesita **este** proyecto, clasificadas en:
- **bootstrap** (mise, git, uv) — Tramalia no las instala; muestra el comando oficial.
- **stack** (node, dotnet…) — según detección.
- **feature/gate** (semgrep, sqlfluff, lighthouse…) — solo si su gate aplica.

`--fix` delega en `mise install` cuando mise ya está presente. Sale con código 1
si falta algo requerido (útil en scripts).

```
stack detectado: python
herramienta   necesidad       estado       detalle / cómo obtenerla
mise          base            ✗ falta      https://mise.jdx.dev/getting-started.html
git           base            ✓ ok         git version 2.54.0
uv            base            ✓ ok         uv 0.11.23
semgrep       gate:security   ○ opcional   mise use pipx:semgrep
```

### `tramalia detect`
Detecta el stack por patrones de archivos y muestra los gates aplicables.

### `tramalia init [--with-headroom --with-ponytail]`
Genera la convención en el repo actual, **idempotente** (no pisa lo existente):
- `AGENTS.md` (fuente única) y `CLAUDE.md` (`@AGENTS.md`)
- `docs/ai/` **completo 00–11** (resumen, arquitectura, reglas de código/DB/seguridad/UX,
  ADR, intentos fallidos, handoff, comandos, quality gates, contexto operativo)
- `specs/` (constitution · specification · plan · tasks · checklist), integrada con el
  flujo: el ID de `tasks.md` es el que usa `close --task`
- **13 skills numeradas** en `.tramalia/skills/` (01-spec-governance … 13-documentation-handoff)
- **5 subagentes con ruteo de modelo** en `.claude/agents/` (planificador→opus,
  ejecutor→inherit, revisor→opus, documentador→haiku, resolutor-profundo→fable);
  tu `/model` controla la conversación principal, el `model:` de cada agente aplica
  solo dentro de la tarea delegada
- `mise.toml` **a la medida del stack** (tools auto-update + tasks de gates)
- `.mcp.json` con Serena (+ Engram si está; Headroom/Ponytail con `--with-*`)
- `.tramalia/` (config.json, current-task.md, skills.toml)

### `tramalia ui`
Dashboard TUI (Textual, extra `pip install "tramalia-cli[tui]"`): **Resumen** (doctor en
vivo), **Auditoría** (cierres navegables con su `metadata.json`) y **Cierre** guiado con
la salida de los gates. Solo lee e invoca el core.

### `tramalia menu`
Menú interactivo **en bucle** (vuelve al menú tras cada acción), muestra el último
cierre en el header, y hace **prompts guiados** (tarea/agente/revisor) al elegir
close/handoff/evidence — modo novato; los expertos usan los flags directo.

### `tramalia gates`
Ejecuta los quality gates: `mise run gates`. Pasa la salida tal cual; falla con
127 si falta `mise` (sin esconder el error).

### `tramalia context`
Genera la **memoria derivada** (no se escribe a mano): `.tramalia/context/tech-stack.md`
y `project-map.md`. Usa Repomix si está; si no, un árbol stdlib. (Serena no se
invoca aquí: es navegación en vivo del agente vía MCP.)

### `tramalia evidence [--task TASK-XXX]`
Crea el **evidence pack** de cierre en `.tramalia/evidence/<fecha>-<task>/` con:
`summary.md`, `files-changed.md` (lee `git diff`), `commands.md`, `*-output.txt`
(build/test/lint/security/database/ux), `risks.md`, `rollback.md`, `next-steps.md`.

### `tramalia handoff [--task --agent --reviewer]`
Agrega una entrada **estructurada** a `docs/ai/07-handoff-agentes.md`
(tarea → archivos → comandos → resultado → riesgos → pendientes → siguiente paso).

### `tramalia sync [--to copilot,cursor,cline] [--features rules,subagents]`
Fan-out con **rulesync** en dos pasadas: las **reglas** (`AGENTS.md`) y los
**subagentes** (`.claude/agents/` → formatos de cada host). No incluye
Claude/Codex para reglas porque ya leen AGENTS.md nativamente. Genera, p. ej.,
`.github/copilot-instructions.md` y `.cursor/rules/overview.mdc`.

### `tramalia skills [sync|list]`
Lee `.tramalia/skills.toml` (referencias, no copias) y **clona/actualiza** cada
skill desde su repo bajo `.tramalia/skills/<name>` (`git clone` / `git pull`).

### `tramalia update`
Actualiza todo: `mise upgrade` (tools) + (futuro) `copier update` + `skills sync`.

### `tramalia mcp`
Levanta la **fachada MCP** (ver Parte 4).

---

## Parte 4 · La fachada MCP (nivel 1)

`tramalia mcp` expone la convención como **herramientas MCP nativas**, para que un
agente las invoque sin shell-out ni aprender el formato de los archivos. No guarda
memoria propia: es una fachada delgada sobre el mismo core del CLI. Herramientas:
`project_status`, `get_agent_rules`, `get_failed_attempts`, `get_current_task`,
`doctor`, `record_handoff`, `build_evidence`, `build_context`.

Para conectarla, agrega Tramalia a `.mcp.json` (junto a Serena):

```jsonc
{
  "mcpServers": {
    "serena":  { "command": "uvx", "args": ["--from","git+https://github.com/oraios/serena","serena","start-mcp-server"] },
    "tramalia": { "command": "tramalia", "args": ["mcp"] }
  }
}
```

Recuerda los **3 niveles de memoria**: N0 archivos + CLI (empieza aquí, sin MCP) ·
**N1 esta fachada** (si quieres tool nativa) · N2 montar **Engram** (o basic-memory/mem0)
para memoria persistente seria.

---

## Parte 5 · Flujo de trabajo recomendado

El camino recomendado **lidera con `tramalia close`** — es el ritual de cierre que
une gates, evidencia y handoff en un paso auditable.

```bash
# una vez, en el repo:
pip install "tramalia-cli[pretty]"
tramalia init           # deja AGENTS.md, docs/ai, mise.toml, .mcp.json
tramalia doctor         # instala lo que falte (mise primero; luego `mise install`)
tramalia sync           # propaga reglas a Cursor/Copilot (interop)

# por tarea:
tramalia context        # refresca el contexto derivado (ahorra tokens)
# … trabajas con tu agente (lee AGENTS.md + docs/ai) …
tramalia close TASK-001    # agente y revisor: defaults de config.json
tramalia log            # revisa la pista de auditoría

# mantenimiento:
tramalia update
```

> **Camino avanzado/manual** (si quieres controlar cada paso): `tramalia gates` →
> `tramalia evidence --task …` → `tramalia handoff --task …`. `close` hace los tres
> con enforcement; estos comandos individuales quedan como alternativa.

---

## Parte 6 · Proceso de construcción (cómo llegamos aquí)

La herramienta se construyó de forma incremental, verificando cada paso:

1. **Esqueleto + `doctor`** — CLI con argparse (stdlib) + Rich/Questionary opcional;
   registro de herramientas por categoría; `doctor`/`detect`/`menu`. Probado en
   modo plano y bonito.
2. **`init` + plantilla** — renderizador idempotente sobre `tramalia/templates/`;
   `mise.toml` y `.mcp.json` generados según stack. Verificada la idempotencia.
3. **`evidence` + `handoff` + `context`** — las piezas propias y la memoria derivada.
   Validados contenidos y formato.
4. **`sync` + `skills` + tests + empaquetado + fachada MCP** — fan-out con rulesync
   real, clone de skills offline, 25 tests verdes, plantilla incluida en el wheel
   (verificada con instalación limpia), y la fachada MCP con 8 herramientas.

Decisiones clave (todas guiadas por el principio Ponytail / "no reconstruir"):
- **AGENTS.md como estándar** → se eliminan los adaptadores por agente; el fan-out
  lo hace rulesync.
- **mise como instalador + runner** → se eliminan el instalador y el runner propios.
- **copier-compatible** → la plantilla habilitará `copier update` al publicarse.
- **memoria/handoff por niveles** → no se construye un motor de memoria; existen
  (mem0, basic-memory, handoff-mcp). La fachada MCP es opcional y delgada.

Detalle técnico resuelto en Windows: las herramientas de npm (rulesync, repomix)
son shims `.cmd` que `subprocess` no ejecuta directo; se centralizó la ejecución en
`tramalia/core/proc.py` (resuelve la ruta y envuelve en `cmd /c`).

---

## Parte 7 · Estado y pendientes

**Implementado y verificado (v0.8):** `doctor`, `detect`, `init` (convención completa:
docs/ai 00–11, specs/, 13 skills, 5 subagentes con ruteo de modelo), `gates`, `context`,
`evidence`, `handoff`, `close` (con `--model` en la auditoría), `log`, `sync` (reglas +
subagentes), `skills`, `update`, `mcp`, `ui` (dashboard TUI), `menu` (bucle + prompts).
52 tests con pytest. Wheel construible con la plantilla incluida. Interop: Engram (N2),
Headroom (`--with-headroom`), Ponytail (`--with-ponytail`), Spec Kit (doctor).

**Pendiente (opcional):**
- Publicar `tramalia-template` como repo git para habilitar `copier update`.
- Cablear `tramalia update` con `copier update` una vez publicada la plantilla.
- Ampliar el detector (más ecosistemas) y los gates.

---

## Apéndice · Arquitectura del código

```
tramalia/
├── __main__.py          entrada (argparse, UTF-8, --plain)
├── cli/
│   ├── commands.py      un comando por handler; shell-out transparente
│   ├── menu.py          menú interactivo (questionary / stdlib)
│   └── render.py        Rich si está; texto plano si no
├── core/
│   ├── tools.py         registro de herramientas + sondeo
│   ├── detect.py        detección de stack y gates
│   ├── doctor.py        diagnóstico + fix (delega en mise)
│   ├── scaffold.py      motor de init (idempotente) + mise.toml/.mcp.json
│   ├── evidence.py      evidence pack
│   ├── handoff.py       handoff estructurado
│   ├── context.py       memoria derivada (tech-stack, project-map)
│   ├── skills.py        clone/update de skills desde sus repos
│   └── proc.py          ejecución de comandos robusta en Windows
├── mcp_server.py        fachada MCP (nivel 1)
└── templates/project/   la convención que init copia
```
