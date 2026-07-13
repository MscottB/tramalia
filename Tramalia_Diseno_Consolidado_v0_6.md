# Tramalia — Documento de diseño consolidado v0.6

> Documento que reemplaza y unifica el *Documento de Producto v0.5* y el *Manual Técnico v0.5*.
> Recoge todas las decisiones de rediseño: pasar de "construir" a "orquestar", apoyarse en herramientas externas completas que se actualizan solas, y dejar como código propio únicamente lo que nadie más hace bien.

| Campo | Valor |
|---|---|
| Producto | Tramalia |
| Versión de diseño | v0.6 (consolidado) |
| Tipo | CLI local-first en Python (capa fina de orquestación) |
| Fecha | 2026-06-27 |
| Audiencia | Desarrolladores, líderes técnicos, arquitectos, equipos que usan agentes IA |
| Estado | Diseño funcional/técnico, previo a implementación |
| Relación con v0.5 | Mismo alcance funcional; cambia radicalmente *cómo* se implementa |

---

## 1. Resumen ejecutivo

Tramalia sigue siendo lo mismo que en la v0.5: una herramienta para proyectos de software trabajados con **múltiples agentes IA** (Codex, Claude Code, Antigravity, ChatGPT, Cursor, Copilot…), que les da una base común — memoria, contexto, reglas, skills, quality gates y evidencia — usando **el repositorio como fuente de verdad**.

Lo que cambia es la **estrategia de implementación**. El diseño v0.5 describía construir en Python casi todo: un runner de quality gates, un instalador de herramientas, adaptadores por agente, un exportador de skills, un menú propio, etc. Pero en 2026 buena parte de eso **ya existe, ya está estandarizado y ya es multiagente**. Reconstruirlo sería violar el propio principio de minimalismo de Tramalia (la skill `04-minimalist-engineering` / Ponytail).

La decisión central de este documento:

> **Tramalia no implementa capacidades; las orquesta.** Es un *manifiesto + un actualizador + una convención*, no una reimplementación. Igual que `package.json` no contiene el código de React pero lo declara y `npm update` trae las mejoras, Tramalia declara su toolchain de IA y un solo comando la mantiene al día.

El valor de Tramalia deja de estar en "hacer X" (cada X está delegada) y pasa a estar en tres cosas:

1. **Una cara única** — un CLI memorable para no aprender 9 herramientas por separado.
2. **Una convención opinada** — la estructura de memoria, evidencia y handoff (esto es conocimiento de diseño, no código).
3. **Dos piezas propias** que el ecosistema no cubre bien: el **evidence pack** y el **handoff** multiagente.

Todo lo demás se apoya en herramientas externas completas, consumidas desde sus repositorios, de modo que **cuando ellas mejoran, Tramalia mejora**.

---

## 2. El cambio de filosofía: de construir a orquestar

### 2.1 El modelo "manifiesto + actualizador"

Tramalia no copia (no *vendoriza*) el código de las herramientas dentro de tu proyecto. Las **referencia por origen y versión**, y ofrece un comando que las actualiza todas. Hay dos ejes de actualización, deliberadamente separados:

| Qué se actualiza | Mecanismo | Comando |
|---|---|---|
| Las **herramientas externas** (Semgrep, Repomix, SQLFluff, rulesync…) | `mise` las gestiona por versión desde sus repos | `mise upgrade` |
| La **convención de Tramalia** (plantillas de AGENTS.md, docs/ai, mise.toml) | `copier` re-aplica la plantilla nueva sin pisar tu trabajo | `copier update` |
| Las **skills** que vienen de otros repos | submódulo git o manifiesto + sync | `tramalia skills sync` |

### 2.2 La regla de las tres naturalezas

No todo "lo externo" es del mismo tipo. Distinguirlas es lo que evita confusión:

| Naturaleza | Ejemplos | Cómo lo "incluye" Tramalia |
|---|---|---|
| Se **ejecuta** (CLI externo) | mise, copier, Repomix, Serena, Semgrep, Gitleaks, SQLFluff, rulesync, Spec Kit, Lighthouse, axe, Playwright | `doctor` verifica que esté; nunca se reescribe |
| Se **lee** (principio/convención) | Ponytail, YAGNI, OWASP | Línea de regla dentro de `AGENTS.md` (texto) |
| Se **deriva** (del código) | mapa del proyecto, contrato de API, contexto de BD | Se genera con un comando; nunca se escribe a mano |
| Tramalia lo **aporta** (código propio, poco) | detector de stack, `init`, evidence, handoff | Es lo único que se programa |

El criterio práctico: **delega lo difícil y mantenido** (gestión de versiones, SAST, fan-out de reglas), **escribe-como-texto lo trivial** (plantillas Markdown), **genera lo derivable** (no lo dupliques a mano) y **construye solo el moat**.

---

## 3. Qué es Tramalia (y qué no es)

### 3.1 Identidad

Tramalia es, físicamente, tres cosas en capas:

1. **Un paquete instalable** (`pip install tramalia-cli`) que da el comando `tramalia`. Es lo que descargas.
2. **Un conjunto de archivos de texto que quedan en tu repo** al correr `tramalia init` (AGENTS.md, docs/ai/, mise.toml, etc.). Es lo que Tramalia deja, y es la capa principal.
3. **(Opcional) un puente MCP** para que los agentes consulten memoria/código en vivo.

La clave conceptual: **la "interfaz de usuario" real de Tramalia son tus propios agentes IA leyendo esos archivos.** El 90% del tiempo no ejecutas Tramalia; usas Claude/Codex, que leen el `AGENTS.md` y los `docs/ai/` que Tramalia dejó. Tramalia reaparece para `init`, `doctor`, `gates`, `evidence`, `handoff` y `update`.

### 3.2 Qué no es

| No es | Aclaración |
|---|---|
| Una IA | No razona ni genera código; prepara contexto, reglas, validaciones y evidencia. |
| Un IDE | Su núcleo es la terminal local; se integra con CLIs/IDEs. |
| Un orquestador autónomo | No lanza agentes en paralelo ni hace merge solo (se delega a Vibe Kanban/Conductor/worktrees si se quiere). |
| Un servicio cloud | Local-first; no depende de plataformas externas para funcionar. |
| Un motor de memoria | Si hace falta memoria seria, se monta Engram/basic-memory/mem0; no se reescribe. |
| Un marketplace de skills | Administra referencias a skills; no publica ni descarga de terceros sin control. |

### 3.3 Posicionamiento frente a Gentle-AI, Engram y Headroom

Existen proyectos con tesis cercana. La distinción es **configurar agentes** (su máquina) vs **gobernar el repo** (lo que hace Tramalia). Cada uno ocupa un espacio distinto y complementario:

| Proyecto | Rol | Relación con Tramalia |
|---|---|---|
| **Gentle-AI** | prepara el ecosistema de agentes (modelos, skills, memoria, perfiles, config) | onboarding externo, no núcleo |
| **Engram** | memoria persistente entre sesiones | interop N2 opcional (memoria) |
| **Headroom** | comprime contexto y outputs para ahorrar tokens | interop opcional (eficiencia) |
| **Tramalia** | **gobierna el trabajo en el repo: reglas, gates, evidencia, handoff, auditoría e intentos fallidos** | el núcleo |

Decisión: Tramalia **no debe convertirse en un Gentle-AI chico**. Se especializa en control, trazabilidad y continuidad del proyecto; **delega la memoria avanzada en Engram** (N2 opcional) y la **compresión en Headroom** (eficiencia opcional), y deja a Gentle-AI como onboarding externo. Riesgos a vigilar:

- **Engram** — definir qué se puede persistir (no secretos); export `--engram` opt-in.
- **Gentle-AI** — evitar doble ownership de configs/prompts/skills/MCP.
- **Headroom** — *compresión ≠ evidencia*: el output crudo siempre se conserva en `.tramalia/evidence/`; Headroom solo genera una vista comprimida para consumo de agentes. Su `headroom learn` debe redirigirse a `docs/ai/06-intentos-fallidos.md`, no escribir libre en varios archivos. En modo proxy/wrapper requiere aprobación (local-first).

---

## 4. Arquitectura en capas

```
┌─ Capa 1 · Lo que tú ejecutas (poco código propio) ──────────────┐
│  tramalia init · detect · doctor · gates · context · evidence ·   │
│  handoff · update · menu     (CLI fino: argparse + Rich opc.)    │
└──────────────────────────────────────────────────────────────────┘
                 │ init genera y cablea
                 ▼
┌─ Capa 2 · Lo que queda en tu repo = la convención (el valor) ───┐
│  AGENTS.md · docs/ai/ · mise.toml · .mcp.json · .tramalia/        │
└──────────────────────────────────────────────────────────────────┘
     ▲ leen                                   │ corren / consultan
     │                                         ▼
┌─ Capa 3 · Lo externo (se actualiza desde sus repos) ────────────┐
│  agentes IA (Claude·Codex·Cursor…) · mise · Repomix · Serena ·   │
│  Semgrep · Gitleaks · SQLFluff · rulesync · Lighthouse · axe ·   │
│  Playwright · Spec Kit · basic-memory                            │
└──────────────────────────────────────────────────────────────────┘
```

- **Capa 1 — CLI fino:** una cara única que hace *shell-out* a las herramientas reales. No reimplementa nada; orquesta.
- **Capa 2 — convención:** archivos de texto versionados, fuente de verdad del proyecto. Es lo más valioso.
- **Capa 3 — externo:** herramientas completas y los agentes. Se actualizan solas.

---

## 5. Cobertura: build vs. delegar vs. curar

Recorrido de **cada** capacidad de los documentos v0.5, para garantizar que nada se perdió:

| Capacidad pedida en v0.5 | Dónde queda ahora | Tipo |
|---|---|---|
| Init / estructura | copier (plantilla) | construir fino |
| Detección de stack | código propio | construir fino |
| Quality gates (build/test/lint/format) | `mise` tasks | delegar |
| tools install / doctor / latest-locked | `mise` + `doctor` fino | delegar |
| Security scan | Semgrep / Gitleaks | delegar |
| DB check | SQLFluff | delegar |
| Token-saver / snapshot de contexto | Repomix + Serena + `context build` | delegar + fino |
| **Evidence pack** | código propio | **construir (moat)** |
| **Handoff multiagente** | código propio | **construir (moat)** |
| Memoria federada | AGENTS.md + docs/ai (texto) + MCP opcional | convención |
| Skills: list/validate/export | manifiesto + rulesync / submódulo | delegar |
| Adaptadores y prompts por agente | AGENTS.md (estándar) + rulesync | delegar |
| Spec-driven | Spec Kit (opcional) o plantillas md | delegar/convención |
| Modos latest/locked/detect-only | `mise` (pinning) | delegar |
| Aviso antes de leer .env/secretos | regla en AGENTS.md + Gitleaks | convención |
| Registro de comandos | logging del CLI → evidence | construir fino |
| `config.json` | respuestas de copier + `mise.toml` | convención |
| Menú interactivo | el CLI único (`tramalia menu`) | construir fino |
| Preparación MCP / allowlist | `.mcp.json` generado | construir fino |
| **(nuevo) Gate UX/UI** | Lighthouse/axe/Playwright/Storybook + reglas 11 | delegar + convención |

Fuera del producto (diferido, y correctamente):

| Diferido | A quién se delega |
|---|---|
| Orquestación multiagente en paralelo | Vibe Kanban / Conductor / git worktrees |
| CI/CD | GitHub Actions / GitLab CI |
| Dashboards locales | diferido (a lo sumo una TUI mínima con Textual) |
| Marketplace / extensiones firmadas | excluido por riesgo supply-chain |

---

## 6. La convención: archivos que quedan en tu repo

Esto es lo que `tramalia init` deja instalado. Cada archivo tiene un propósito y un consumidor.

```
tu-proyecto/
├── AGENTS.md                 fuente única de reglas (Ponytail incluido)
├── CLAUDE.md                 → @AGENTS.md (sin duplicar)
├── .mcp.json                 enchufa Serena (basic-memory opcional)
├── mise.toml                 tools (auto-update) + gates como tasks
├── .pre-commit-config.yaml   hooks de calidad antes de commit
├── docs/ai/                  convención completa 00–11
│   ├── 00-resumen · 01-arquitectura · 02-reglas-codigo
│   ├── 03-reglas-base-datos (gate DB) · 04-reglas-seguridad (gate seguridad)
│   ├── 05-decisiones-adr · 06-intentos-fallidos · 07-handoff-agentes
│   └── 08-comandos · 09-puertas-calidad · 10-contexto-operativo · 11-reglas-ux-ui (gate UX/UI)
├── specs/                    constitution/specification/plan/tasks/checklist
│                             (integrada con `close --task`; Spec Kit opcional la potencia)
└── .tramalia/
    ├── config.json           configuración mínima de Tramalia
    ├── current-task.md       tarea en curso
    ├── context/              GENERADO: project-map, tech-stack, db-context, api-contracts
    ├── skills.toml           manifiesto de skills (referencias, no copias)
    └── evidence/             evidence packs y handoffs (el moat)
```

### 6.1 `AGENTS.md` único

`AGENTS.md` es hoy un **estándar formal** (bajo la Agentic AI Foundation / Linux Foundation desde diciembre 2025), leído nativamente por 28+ herramientas, incluido Claude Code. Es un solo Markdown en la raíz con las instrucciones para *cualquier* agente.

"Único" significa **una sola fuente de reglas**, en vez de mantener copias divergentes (`AGENTS.md` + `CLAUDE.md` + `.cursorrules` + `GEMINI.md`). Los demás archivos se vuelven punteros: `CLAUDE.md` contiene solo `@AGENTS.md`, y el resto se genera con `rulesync`. Esto elimina de raíz el subsistema de "adaptadores por agente" que la v0.5 planeaba construir.

Contenido: objetivo del proyecto, orden de lectura obligatorio, reglas generales (incluido el principio Ponytail como una línea), prohibiciones, comandos de verificación, y los disparadores de los gates (si tocas DB → lee reglas 03; si tocas seguridad → 04; si tocas UI → 11).

### 6.2 `mise.toml`

`mise` es el gestor políglota estándar de 2026: hace **tres trabajos** que la v0.5 iba a programar (instalador + tool-lock + runner de gates). Tiene dos secciones:

```toml
# (a) herramientas externas, gestionadas por versión desde SUS repos
[tools]
node            = "22"
python          = "3.12"
"npm:repomix"   = "latest"
"pipx:semgrep"  = "latest"
"pipx:sqlfluff" = "latest"
"aqua:gitleaks" = "latest"

# (b) los gates, como tareas con grafo de dependencias
[tasks.build]    = { run = "ng build && dotnet build" }
[tasks.test]     = { run = "ng test --watch=false && dotnet test" }
[tasks.lint]     = { run = "ng lint && ruff check" }
[tasks.security] = { run = ["gitleaks detect", "semgrep scan --error"] }
[tasks.database] = { run = "sqlfluff lint database/" }
[tasks.ux]       = { run = ["lhci autorun", "playwright test"] }
[tasks.gates]    = { depends = ["build","test","lint","security","database","ux"] }
```

- `mise install` instala TODAS las herramientas desde sus repos. **Este archivo es el `tool-lock.json` de la v0.5.**
- `mise upgrade` trae las mejoras de cada una (eje de actualización de tools).
- `mise run gates` corre los quality gates. **Reemplaza el runner propio.**
- Funciona igual en Windows/Linux/macOS/WSL (requisito de multiplataforma).
- `latest` vs versión fija resuelve la tensión **latest/locked** de la v0.5: `latest` para laboratorio, versiones fijas para reproducibilidad corporativa.

### 6.3 `.mcp.json`

Declara los servidores MCP que cualquier agente compatible levantará. Tramalia solo lo *genera*; no implementa los servidores:

```jsonc
{
  "mcpServers": {
    "serena":  { "command": "uvx", "args": ["--from","git+https://github.com/oraios/serena","serena","start-mcp-server"] }
    // "basic-memory": { ... }   ← opcional, si se quiere memoria persistente más allá de los archivos
  }
}
```

### 6.4 `docs/ai/` — la memoria curada

Cada archivo es conocimiento de *intención* que ningún tool puede inventar (el "porqué"). Es texto, a mano, versionado. Ver §7 (memoria), §10–13 (gates), §14–16 (evidence/handoff/intentos fallidos).

### 6.5 `.tramalia/context/` — la memoria derivada

Lo que **sí** se puede derivar del código no se escribe a mano (se pudriría y mentiría). Se regenera con `tramalia context build`. Ver §8.

---

## 7. Memoria federada multiagente

El problema raíz de la v0.5: *los agentes pierden contexto entre sesiones, herramientas y modelos*. La solución es que la memoria viva en el repo, accesible por todos.

Hay tres tipos de memoria, separados a propósito:

- **Normativa** → `AGENTS.md` (las reglas).
- **Técnica** → `docs/ai/` (arquitectura, decisiones, intentos fallidos, handoff).
- **Consultable/viva** → opcionalmente vía MCP.

### Los 3 niveles de memoria (decisión de diseño)

Punto clave: **para leer, no necesitas MCP.** Los archivos `AGENTS.md` + `docs/ai/` ya son memoria persistente que todos los agentes leen sin infraestructura. El problema del camino de **lectura** ya está resuelto por archivos. Un servidor MCP solo aporta en el camino de **escritura estructurada** y **lectura selectiva**. Por eso la decisión es por niveles:

| Nivel | Qué usas | Cuándo |
|---|---|---|
| **N0 (empieza aquí)** | Archivos para leer + el **CLI para escribir** (el agente hace `tramalia handoff new …` por shell) | Casi siempre. Cero MCP. |
| **N1 (UX de tool nativa)** | Un **façade MCP de ~100 líneas** que solo llama al CLI/archivos existentes | Si quieres que el agente lo use como herramienta y haga lectura selectiva (`get_failed_attempts(tema)`) |
| **N2 (memoria seria)** | Montas **basic-memory** (Markdown local) o **mem0** | Si necesitas memoria semántica/grafo de verdad |

Importante: **"memoria" es commodity** (ya existen mem0, Letta, Zep, basic-memory, el servidor KG oficial, e incluso handoff-mcp). Lo diferenciador no es el almacén, sino el **esquema/flujo opinado** (handoff, intentos fallidos, evidence enlazada). Por eso no se construye un motor de memoria: a lo sumo un façade fino sobre el CLI, y el almacenamiento serio se delega.

---

## 8. Ahorro de tokens y contexto

Dos estrategias distintas y complementarias:

- **Resúmenes estáticos** (texto pre-digerido que el agente lee en vez del código). Baratos, pero se desactualizan.
- **Navegación semántica en vivo** (Serena MCP): el agente pide `find_symbol`, `find_referencing_symbols`, `get_symbols_overview` y edita **solo el símbolo exacto**, leído fresco. Ahorra tokens durante el trabajo y nunca miente.

Analogía: los resúmenes son el **índice** de la biblioteca; Serena es **ir a buscar la página exacta** sin leer todos los libros.

### Los 3 niveles de ahorro de tokens

1. **Orientar (estable, curado):** `AGENTS.md` + `docs/ai/`. Chico, se lee primero, dice el porqué y dónde mirar.
2. **Derivar (fresco, generado):** `tramalia context build` regenera lo derivable llamando por dentro a detector + Repomix + Serena. **No se escribe a mano.**
3. **Navegar quirúrgico (vivo):** Serena MCP trae solo el símbolo a editar.

### Curado vs. derivado (regla Ponytail)

| Archivo | Naturaleza | Cómo se obtiene (sin pudrirse) |
|---|---|---|
| `agent-rules` | curado | **es `AGENTS.md`** — no crear otro |
| `architecture` | curado | a mano → `docs/ai/01` |
| `decisions` | curado | ADR → `docs/ai/05` |
| `risks` | curado + auto | a mano + hallazgos de Semgrep |
| `task-state` | estado | `.tramalia/current-task.md` |
| `tech-stack` | derivable | el detector lo genera |
| `project-map` | derivable | Repomix `--no-files` o Serena overview |
| `db-context` | derivable | de migraciones/schema o Serena/SQLFluff |
| `api-contracts` | derivable | de OpenAPI/rutas o Serena |
| `touched-files` | derivable | `git diff` / `git log` |
| `skills/*` | referenciado | manifiesto + submódulo/rulesync |

Ponytail está encima como regla en `AGENTS.md`: *"antes de leer o escribir, usa el mapa y Serena para tocar lo mínimo"*.

---

## 9. Skills

La v0.5 quería 13 skills propias, un validador y un exportador por agente. En 2026 eso se simplifica:

- **Memoria como referencias, no copias:** un manifiesto `.tramalia/skills.toml` apunta a los repos de cada skill, para que se actualicen solas.

```toml
[[skill]]
name   = "ponytail"
source = "git+https://github.com/DietrichGebert/ponytail"
ref    = "v1.2.0"     # o "main" para latest
```

- **El fetch se delega**, según cuánto quieras:
  - **Cero código:** `git submodule` por skill → `git submodule update --remote` trae mejoras.
  - **Más rico:** `rulesync` (que ya maneja el formato `SKILL.md`) hace el *fan-out* a `.claude/skills`, `.cursor/`, Copilot, Gemini, etc., desde una sola fuente.
- **Skills propias:** `init` entrega **13 skills numeradas** (01-spec-governance … 13-documentation-handoff) en `.tramalia/skills/`. No son copias de conocimiento genérico: cada una es un **workflow anclado a los comandos y gates de Tramalia** (p. ej. 08-tool-execution-gate → `tramalia close`; 04-minimalist-engineering → el ruleset de Ponytail clonado). Lo genérico sigue *referenciado* (Ponytail vía skills.toml), no copiado.

Esto evita el riesgo que el propio documento v0.5 temía: mantener tres copias divergentes de cada skill.

---

## 10. Quality gates

Validaciones obligatorias antes de cerrar una tarea. Se definen como tareas de `mise` (§6.2) y se invocan con `tramalia gates run` (que hace `mise run gates`). Todo delegado salvo `evidence`.

| Gate | Cuándo aplica | Delega en | Criterio de aprobación |
|---|---|---|---|
| build | cambios compilables | mise + stack | sin errores bloqueantes |
| test | lógica modificada | mise + stack | tests críticos pasan o se documenta ausencia |
| lint | front/back con linter | eslint · ruff | sin errores nuevos |
| format | lenguajes con formatter | prettier · black · gofmt | sin cambios pendientes o aceptados |
| security | APIs, auth, datos, deps | Semgrep · Gitleaks | hallazgos analizados y documentados |
| database | SQL / migraciones | SQLFluff (+ reglas 03) | migración documentada y rollback definido |
| **ux/ui** | cambios de interfaz | Lighthouse · axe · Playwright · Storybook (+ reglas 11) | a11y AA, estados cubiertos, sin regresión visual |
| evidence | toda tarea | **propio** | comandos, resultados y riesgos registrados |

---

## 11. Gate de base de datos

Reglas curadas en `docs/ai/03-reglas-base-datos.md`, verificación delegada a SQLFluff y dry-run de migraciones.

- Toda feature que toque datos indica las tablas afectadas.
- Toda tabla nueva define PK, constraints mínimos y naming consistente.
- Toda relación define FK o justifica por qué no aplica.
- Toda migración tiene rollback o plan manual explícito.
- Todo índice se justifica por consulta, unicidad, FK o performance.
- Todo dato personal documenta finalidad, retención y exposición en logs.
- Backend y frontend se alinean con el modelo de datos (sin duplicidad semántica).

---

## 12. Gate de seguridad

Reglas en `docs/ai/04-reglas-seguridad.md`, verificación delegada a Semgrep (SAST) y Gitleaks (secretos).

- Validar entradas en backend aunque el frontend valide.
- No registrar secretos, tokens, contraseñas ni datos sensibles en logs.
- Autorización por caso de uso, no solo por pantalla.
- No introducir dependencias sin revisar necesidad y riesgo.
- No conectar MCP remotos sin allowlist.
- Los hallazgos SAST se clasifican: real, falso positivo, requiere análisis, o aceptado con mitigación.

---

## 13. Gate de UX/UI (nuevo)

La v0.5 gobernaba base de datos y seguridad pero **dejaba la interfaz sin gate** — por eso la UI suele diseñarse mal. Se agrega con el mismo patrón: reglas curadas + verificación delegada.

### Reglas curadas — `docs/ai/11-reglas-ux-ui.md`
- **Design system / tokens:** colores, tipografía, espaciado y componentes consistentes (sin valores sueltos).
- **Estados obligatorios** de cada vista: cargando, vacío, error, éxito, deshabilitado.
- **Responsive:** breakpoints definidos; sin scroll horizontal accidental.
- **Accesibilidad WCAG AA:** contraste, foco visible, navegación por teclado, etiquetas ARIA, textos alternativos.
- **Feedback ante latencia:** spinners/skeletons; nada de acciones sin respuesta.
- **Jerarquía visual** e **i18n** (sin textos hardcodeados si el proyecto es multilenguaje).

### Verificación delegada
| Qué se revisa | Herramienta |
|---|---|
| Accesibilidad | axe-core / pa11y |
| Rendimiento + a11y + best practices | Lighthouse CI |
| Regresión visual + e2e | Playwright |
| Estados de componentes | Storybook |
| Lint de UI | eslint-plugin-jsx-a11y · stylelint |

### Activación
El detector activa este gate solo si hay frontend (Angular/React/Vue/Svelte…). Agrega la tarea `mise run ux` y la skill `ux-ui-review` para el agente.

---

## 14. Evidence pack (explicado en detalle)

### Qué es y por qué
El **evidence pack** es el paquete de cierre de una tarea: la prueba *verificable* de qué se hizo, qué se ejecutó y qué resultó. Responde a un problema concreto: la IA puede *decir* que algo funciona sin haberlo probado. El evidence pack hace que **ninguna tarea se marque como terminada sin registro de comandos y resultados**. Es una de las dos piezas que Tramalia sí construye, porque casi ningún tool del ecosistema lo cubre bien.

### Cuándo se genera
Al cerrar una tarea con `tramalia close` (recomendado) o `tramalia evidence` (manual). `close` corre los gates, escribe su salida cruda en el pack y genera `metadata.json`, todo en una carpeta fechada.

### Estructura
```
.tramalia/evidence/2026-06-27-1530-TASK-001/
├── metadata.json        ★ auditoría estructurada: task, agente, reviewer,
│                          timestamps, status, gates (exit codes), rutas
├── gates-status.md      estado de gates (tabla) o excepción documentada
├── build-output.txt     salida CRUDA del build (o por qué no aplica)
├── test-output.txt      salida CRUDA de tests (o ausencia justificada)
├── lint-output.txt      salida CRUDA de lint/formato
├── security-output.txt  salida CRUDA de Semgrep/Gitleaks (o checklist)
├── database-output.txt  salida CRUDA de SQLFluff/migraciones (o checklist)
├── ux-output.txt        salida CRUDA de Lighthouse/axe/Playwright (o checklist)
├── summary.md · files-changed.md · commands.md
├── risks.md · rollback.md · next-steps.md
└── (opcional, derivado) review-summary.md · headroom-stats.md
```

**`status` honesto** en `metadata.json`: `passed` · `blocked` (gate falló) ·
`passed_with_exceptions` (forzado con `--allow-fail`) · `no_gates` (mise ausente).
Un fallo forzado **nunca** se registra como `passed` a secas.

> **Invariante del moat:** los `*-output.txt` crudos y `metadata.json` son la
> evidencia **oficial**. Ningún artefacto derivado (compresión de Headroom,
> `review-summary.md`) puede modificarlos, reemplazarlos ni omitirlos — solo
> agregar archivos auxiliares marcados como derivados.

### Para qué sirve en la práctica
- **Trazabilidad:** queda en el repo, versionado, auditable; `metadata.json` la hace consultable.
- **Confianza:** un revisor (humano u otra IA) ve *exactamente* qué se ejecutó y con qué resultado.
- **Handoff:** alimenta el traspaso al siguiente agente (§15).

---

## 15. Handoff multiagente (explicado en detalle)

### Qué es y por qué
El **handoff** es el documento de traspaso entre un agente (o sesión) y el siguiente. Resuelve el problema #1 de la v0.5: el contexto se pierde al cambiar de agente o de sesión. Es la otra pieza propia de Tramalia.

### Cuándo se genera
Con `tramalia handoff new` al terminar un bloque de trabajo. Agrega una entrada a `docs/ai/07-handoff-agentes.md` (memoria versionada) y enlaza con el evidence pack correspondiente.

### Formato
```markdown
## Handoff 2026-06-27 15:30 — TASK-001
- Agente ejecutor: Codex
- Agente revisor sugerido: Claude
- Tarea: TASK-001 — Crear migración usuarios internos
- Archivos modificados:
  - database/migrations/001_create_usuarios.sql
- Comandos ejecutados:
  - sqlfluff lint database/
  - dotnet test
- Resultado: Migración creada. Tests backend pasan.
- Riesgos: Confirmar política de retención antes de producción.
- Pendientes: Revisar índice por rut_usuario.
- Siguiente paso: Ejecutar revisión DB con otro agente.
```

### El esquema es el valor
Lo importante no es "guardar texto" (eso es commodity), sino que el handoff tenga **siempre la misma estructura tipada** — tarea → archivos → comandos → resultado → riesgos → pendientes → siguiente paso — para que cualquier agente la consuma sin ambigüedad. Por eso se escribe con el CLI (escritura estructurada garantizada), no a mano.

---

## 16. Intentos fallidos (memoria de errores)

`docs/ai/06-intentos-fallidos.md` registra lo que **no** funcionó, para que ningún otro agente repita un camino ya descartado. Cada entrada: fecha, tarea, agente, intento, error observado, causa probable, decisión y "no repetir". Es memoria barata que ahorra muchísimos tokens y vueltas: un agente lee esto antes de proponer una solución.

---

## 17. Herramientas externas

Todas se consumen completas desde sus repos y se actualizan solas. Tramalia solo las cablea y `doctor` verifica que estén. **La columna Runtime importa**: Tramalia es Python, pero varias tools son Node — `doctor` marca esas filas como "requiere Node" y avisa si Node falta.

| Herramienta | Rol | Runtime | Cómo se consume |
|---|---|---|---|
| mise | versiones de tools + env + runner de gates | binario | binario; gestiona el resto |
| copier | scaffolding con `update` | Python | `uv tool` / pipx |
| Repomix | snapshot del repo para IA | **Node** | `npm:` vía mise / npx |
| Serena | navegación/edición semántica (MCP) | Python | `uvx` desde su repo git |
| Semgrep | SAST | Python | `pipx:` vía mise |
| Gitleaks | secretos | binario | `aqua:` vía mise |
| SQLFluff | lint SQL | Python | `pipx:` vía mise |
| rulesync | fan-out de reglas/skills por agente | **Node** | `npm:` vía mise / npx |
| Lighthouse CI | rendimiento + a11y + best practices | **Node** | `npm:` |
| axe-core / pa11y | accesibilidad | **Node** | `npm:` |
| Playwright | regresión visual + e2e | **Node** | `npm:` |
| Storybook | estados de componentes | **Node** | `npm:` |
| Spec Kit | spec-driven (opcional) | Python | `uv tool install specify-cli` |
| Engram | memoria persistente para agentes (opcional, N2) | binario (Go) | `engram mcp` / `engram save` |
| basic-memory / mem0 | memoria persistente alternativa (opcional, N2) | Python | MCP desde su repo |
| Headroom | compresión de contexto/outputs (opcional, eficiencia) | — | MCP / CLI; nunca reemplaza la evidencia |

> **Node es prerequisito** solo si usas `sync` (rulesync), el gate `ux`
> (Lighthouse/Playwright) o `context` completo (Repomix). En un proyecto sin
> frontend y sin `sync`, nunca se necesita Node. Instálalo con `mise use node@22`.

---

## 18. El modelo de actualización

Un solo comando mantiene todo al día:

```
tramalia update
  ├─ mise upgrade        # mejoras de las herramientas externas
  ├─ copier update       # mejoras de la convención de Tramalia (merge, no pisa tu trabajo)
  └─ tramalia skills sync # mejoras de las skills referenciadas
```

Tensión **latest vs locked**: en `mise.toml` decides si cada tool flota (`latest`, recibes mejoras al instante) o está fija (reproducibilidad corporativa). En entornos corporativos se prefiere fijar versiones; en laboratorio, `latest`.

---

## 19. El CLI

### Stack (mínimo, con extras opcionales — Ponytail)
- **argparse (stdlib)** → comandos y `--help`, sin dependencia obligatoria (corre en terminal básica).
- **Rich** (opcional) → tablas, paneles, colores (la parte que se ve bien).
- **Questionary** (opcional) → menús interactivos con flechas ↑↓.
- **Textual** (opcional, futuro) → dashboard TUI completo.
- `--plain` → modo sin colores; el modo bonito se activa solo si Rich/Questionary están instalados.

### Superficie de comandos
Respeta los nombres de la v0.5, pero cada uno **delega**:

| Comando | Por dentro hace | Tipo |
|---|---|---|
| `tramalia close` | **ritual de gobierno: gates → evidence (con salidas) → handoff, con enforcement** | **core ★** |
| `tramalia log` | **pista de auditoría: lista los cierres registrados** | **core ★** |
| `tramalia init` | scaffolding idempotente (AGENTS.md, docs/ai, mise.toml, .mcp.json) | core |
| `tramalia detect` | detector propio → `tech-stack` | core |
| `tramalia doctor` | verifica mise/serena/semgrep/engram/etc. presentes | core |
| `tramalia evidence` / `handoff` | **código propio** | core |
| `tramalia context` | Repomix + Serena + detector → archivos derivados | interop |
| `tramalia gates` | `mise run gates` | interop |
| `tramalia sync` | rulesync: AGENTS.md → Cursor/Copilot/… | interop |
| `tramalia skills` | submódulo / rulesync | interop |
| `tramalia update` | `mise upgrade` + `copier update` + `skills sync` | interop |
| `tramalia mcp` | levanta la fachada MCP sobre el core | core |
| `tramalia menu` | menú interactivo sobre todo lo anterior | core |

El **núcleo (core)** funciona standalone solo con Python; los comandos **interop** delegan en herramientas externas opcionales y degradan con gracia si faltan.

### Regla de diseño del façade
Para que la cara única no se vuelva deuda: el CLI debe ser **delgado y transparente** — hace shell-out a la tool real, **muestra su salida tal cual, nunca esconde sus errores**, y siempre se puede saltar (puedes llamar a `mise`/`serena` directo). Es conveniencia, no muro. Si Tramalia empieza a *reinterpretar* la salida de las tools, dejó de ser fino.

---

## 20. MCP — resumen

- **Serena MCP** (externo, se actualiza solo) → código vivo.
- **basic-memory / mem0** (externo, opcional, N2) → memoria persistente seria.
- **Tramalia MCP** (propio, opcional, N1) → un façade de ~100 líneas sobre el CLI, solo si la UX de tool nativa lo justifica.
- Allowlist de servidores y nada de MCP remotos sin aprobación (gate de seguridad).

Para empezar (N0), **probablemente no necesitas ningún MCP propio**: archivos + CLI cubren el 90%.

---

## 21. Flujo de uso de extremo a extremo

```
# Una vez, en tu repo:
pip install tramalia-cli
tramalia init          # copier: deja AGENTS.md, docs/ai, mise.toml, .mcp.json
mise install          # baja todas las tools desde sus repos
tramalia doctor        # "✓ mise  ✓ serena  ✗ semgrep → mise use semgrep"

# Por tarea (camino recomendado, liderado por close):
tramalia context                  # refresca el contexto derivado (token-saver)
# … trabajas con tu agente (Claude/Codex), que lee AGENTS.md + docs/ai …
tramalia close --task TASK-001 --agent codex --reviewer claude
                                  # gates → evidence (con salidas) → handoff, con enforcement
tramalia log                      # pista de auditoría de los cierres
# revisión cruzada por otro agente o humano antes de merge

# Mantenimiento:
tramalia update                   # mise upgrade + copier update + skills sync
```

> **Camino avanzado/manual:** `tramalia gates` → `tramalia evidence` → `tramalia handoff`
> dan control paso a paso, pero `close` los une con enforcement y es la vía recomendada.

---

## 22. Estructura del repositorio de Tramalia

Dos artefactos (pueden ser uno o dos repos):

```
tramalia-template/           # la plantilla copier (la convención)
├── copier.yml              # preguntas: nombre, stack, agentes
└── template/
    ├── AGENTS.md.jinja
    ├── CLAUDE.md.jinja
    ├── mise.toml.jinja
    ├── .mcp.json.jinja
    └── docs/ai/...

tramalia/                    # el paquete CLI (la cara única)
├── pyproject.toml
├── tramalia/
│   ├── __main__.py
│   ├── cli/                # argparse + Rich/Questionary opcional
│   ├── detect/            # detector de stack (código propio)
│   ├── evidence/          # evidence + handoff (código propio)
│   └── wrappers/          # shell-out fino a mise/repomix/serena/...
└── tests/
```

---

## 23. Seguridad y gobierno

- **Local-first:** no envía archivos a servicios externos por defecto.
- **Confirmaciones y dry-run:** nada destructivo, instalación o lectura de secretos sin confirmación explícita.
- **Aviso ante secretos:** regla en AGENTS.md + Gitleaks antes de leer `.env`, certificados, etc.
- **Allowlist de MCP:** servidores MCP solo como opción avanzada y con lista permitida.
- **Modos latest/locked:** laboratorio vs. reproducibilidad corporativa.
- **Registro de comandos:** el CLI loguea lo que ejecuta → alimenta el evidence pack.
- **Separación de memoria:** normativa (AGENTS.md), técnica (docs/ai), consultable (MCP).

---

## 24. Roadmap revisado

| Versión | Objetivo |
|---|---|
| v0.5 (reenfocada) | `init` (copier) + AGENTS.md único + `mise` (gates+tools) + `doctor` + evidence/handoff + detector + fan-out con rulesync. **Suelta:** instalador propio, runner propio, adaptadores por agente, exportador de skills, menú stdlib. |
| v0.6 | gate UX/UI, `context build` (Repomix+Serena), CLI bonito (Rich+Questionary), façade MCP opcional (N1). |
| v0.7+ | memoria persistente opcional (basic-memory/mem0, N2), TUI con Textual. |
| v1.0 | integración (no reimplementación) con orquestadores multiagente (Vibe Kanban/Conductor/worktrees), CI/CD opcional, gobernanza avanzada. |

Diferidos a propósito: orquestación autónoma, CI/CD propio, dashboards, marketplace de skills.

---

## 25. Glosario

| Término | Definición |
|---|---|
| Agente IA | Herramienta que lee contexto, razona, edita archivos y/o ejecuta comandos. |
| Memoria federada | Memoria del proyecto distribuida en archivos versionados, accesible por varios agentes. |
| Quality gate | Validación obligatoria antes de cerrar una tarea. |
| Evidence pack | Paquete de cierre verificable: comandos, salidas, cambios, riesgos, rollback. |
| Handoff | Traspaso estructurado entre agentes/sesiones. |
| Façade | Capa fina que unifica el uso de varias herramientas tras un solo comando. |
| Manifiesto + actualizador | Modelo donde Tramalia declara dependencias y un comando las mantiene al día (como package.json). |
| Curado vs. derivado | Lo que se escribe a mano (intención) vs. lo que se genera del código (hechos). |

---

## 26. Fuentes y referencias (verificadas 2026)

> Las herramientas IA y sus CLI cambian con frecuencia; verificar antes de publicar versiones productivas.

| Fuente | Uso | URL |
|---|---|---|
| AGENTS.md (estándar) | formato abierto de instrucciones para agentes | https://agents.md/ |
| AGENTS.md Field Guide 2026 | estado de adopción del estándar | https://www.iuriio.com/blog/posts/2026/05/agents-md-field-guide-2026 |
| rulesync | fan-out de reglas/skills por agente | https://github.com/dyoshikawa/rulesync |
| mise | versiones + env + runner de tareas | https://mise.jdx.dev/tasks/ |
| copier | scaffolding con `update` | https://copier.readthedocs.io/ |
| Repomix | snapshot de repos para IA | https://repomix.com/ |
| Serena | navegación/edición semántica (MCP) | https://github.com/oraios/serena |
| Semgrep | SAST | https://semgrep.dev/ |
| Gitleaks | secret scanning | https://github.com/gitleaks/gitleaks |
| SQLFluff | lint/format SQL | https://docs.sqlfluff.com/ |
| Spec Kit | spec-driven development (opcional) | https://github.github.com/spec-kit/ |
| Lighthouse CI | rendimiento + a11y + best practices | https://github.com/GoogleChrome/lighthouse-ci |
| axe-core / pa11y | accesibilidad | https://github.com/dequelabs/axe-core |
| Playwright | regresión visual + e2e | https://playwright.dev/ |
| Storybook | estados de componentes | https://storybook.js.org/ |
| basic-memory | memoria MCP en Markdown local | https://www.pulsemcp.com/servers/basicmachines-memory |
| mem0 | memoria semántica (MCP) | https://mem0.ai/ |
| handoff-mcp | MCP de handoff para desarrollo | https://github.com/coladapo/handoff-mcp |
| MCP Security Best Practices | seguridad de MCP | https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices |
| Code execution with MCP (Anthropic) | preferir ejecución de código/CLI sobre acumular tools | https://www.anthropic.com/engineering/code-execution-with-mcp |
| Ponytail | principio de minimalismo | https://github.com/DietrichGebert/ponytail |
| INAPI Buscador de Marcas | validación de marca (Chile) | https://buscadormarcas.inapi.cl/ |

---

*Fin del documento de diseño consolidado v0.6. Próximo paso: implementación de la muestra (plantilla copier + CLI).*
