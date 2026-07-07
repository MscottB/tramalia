# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/). Este proyecto sigue versionado semántico.

## [0.18.0] - 2026-07-07

Convención con sustancia: docs/ai stack-aware, skills de deploy/analítica/
ciberseguridad, y guía de administración de skills.

### docs/ai enriquecido y stack-aware (00–13)
- Las plantillas dejan de ser esqueletos: **checklists accionables** en
  arquitectura (reglas de dependencia, ADR obligatorio), código (errores,
  testing hermético, prohibiciones), BD (migraciones con rollback SIEMPRE,
  expansión/contracción, FK con índice), seguridad (OWASP práctico + supply
  chain + cuándo escalar a humano), gates (política de excepciones) y
  contexto operativo (entornos, credenciales).
- **Stack-aware**: `init` genera reglas específicas de lo detectado — Angular/
  React/.NET/Python en `02`; tsql/postgres/databricks en `03`; Tailwind/a11y
  en `11`. Un proyecto Python no arrastra reglas de Angular.
- **Dos archivos nuevos**: `12-deploy-release.md` (checklist pre/post deploy,
  orden BD→backend→frontend, trigger de rollback definido ANTES) y
  `13-analitica-datos.md` (notebooks, calidad de datos, metrics/thresholds).

### Skills 14–16 (ancladas al gobierno, como las 13 originales)
- **14-deploy-gate**: el release como tarea con checklist y evidencia.
- **15-analytics-governance**: cerrar datos/ML con métricas y umbrales.
- **16-threat-modeling**: STRIDE ligero antes de cambios sensibles (ciberseguridad
  más allá del SAST).

### Administración de skills
- Nueva página **Skills: administración y catálogo** (ES/EN): las 3 capas
  (reglas → skills propias → externas), la regla de oro ("skill propia solo si
  está anclada a un comando/gate/evidencia"), el flujo con `skills.toml` +
  `tramalia skills`, y la tabla **cuál instalar según necesidad**.
- Catálogo externo ampliado en `skills.toml`: gstack (Security OWASP+STRIDE,
  Release, QA), impeccable y emilkowalski-skills (UI craft), comentados.

### Calidad
- 131 tests con pytest (8 nuevos en `tests/test_v018.py`).

## [0.17.0] - 2026-07-06

Instalador personalizado por sistema + fix de la tecla `i` en la TUI.
Nace del feedback real de instalar en Windows (winget ✓, scoop ✗).

### Instalador por SO y por gestor (`core/installer.py`)
- Detecta el sistema (Windows/macOS/Linux) y qué gestores hay: para cada
  herramienta arma opciones **ordenadas** — la mejor disponible se ejecuta
  automatizada, el resto se muestra como alternativa manual.
- **mise en Windows: winget primero** (`winget install jdx.mise`, vía
  verificada); choco/scoop quedan como alternativas manuales.
- Reglas: `curl | sh` **nunca** automatizado; opciones **npm solo si Node/npm
  está presente** (verificador incluido); `pipx:` deriva a `uv tool install`.
- `doctor --fix` renovado: plan automatizado + **selección múltiple**
  interactiva (checkbox) antes de ejecutar; muestra qué requiere vía manual.

### TUI: tecla `i` arreglada de raíz
- Ya **no salta a la pestaña Cierre**: la salida corre en un panel propio
  dentro del Resumen.
- Ya no corre un `mise install` ciego: abre un **selector múltiple** con las
  faltantes instalables en tu sistema y las instala una a una por su mejor vía.
- **Fix del "no muestra diferencia"**: lo que mise instala vive tras sus
  *shims* (fuera del PATH hasta `mise activate`); el doctor ahora consulta
  `mise which` y las marca "instalada vía mise (shims)" en vez de "falta".

### Resumen agrupado
- La tabla del doctor (CLI y TUI) sale **agrupada**: base (bootstrap) · stack
  del proyecto · gates y features · agentes CLI. Hints por SO en cada fila.

### Documentación
- Instalación: nueva sección "Instalación automatizada por sistema" (tabla
  por SO) y **"Actualizar"** (`pip install -U tramalia-cli` vs
  `tramalia update` — hueco reportado); Interfaz y Comandos actualizadas.

### Calidad
- 123 tests con pytest (11 nuevos en `tests/test_v017.py`); un test de v0.16
  hecho hermético (dependía de si mise estaba instalado en la máquina).

## [0.16.0] - 2026-07-05

Analítica avanzada: métricas/umbrales en la evidencia + gate de notebooks.

### Métricas y umbrales en el cierre (ML/analítica)
- Si existe **`.tramalia/metrics.json`** (dataset, métricas, mlflow_run…), `close`
  lo **copia crudo al evidence pack** e **incrusta en `metadata.json`** bajo
  `metrics` — el cierre registra *con qué datos* y *qué números*, no solo pass/fail.
- Si además existe **`.tramalia/thresholds.json`** (`{"accuracy":{"min":0.9}}`),
  una métrica que **incumpla** su umbral (o falte) **bloquea el cierre** como un
  gate fallido (`status: blocked`), salvo `--allow-fail` →
  `passed_with_exceptions`. Detalle en `metrics-thresholds.txt` y
  `metadata.json → metric_thresholds`.
- Una regresión de accuracy que impide cerrar la tarea, con el hash del dataset
  como evidencia — gobierno de ML, no solo de código.

### Gate de ejecución de notebooks (opt-in)
- **`tramalia init --with-notebook-exec`** agrega un gate `notebooks` que
  **ejecuta** los notebooks (`jupyter execute notebooks/*.ipynb`) — el "build"
  de analítica, más allá de la higiene de `nbstripout --verify`. Opt-in porque
  requiere datos/entorno; `notebooks` se suma a `_GATE_ORDER`.

### Documentación
- Analítica (ES/EN) ampliada: ejecución de notebooks, métricas y umbrales;
  `close` en la referencia menciona el flujo de métricas.

### Calidad
- 112 tests con pytest (10 nuevos en `tests/test_v016.py`).

## [0.15.0] - 2026-07-05

Soporte por stack: matriz de gates completa + dialectos SQL + detección fina.

### Matriz de gates por stack
- **Java (Maven/Gradle), Go y Rust** ahora emiten `build`/`test` en `mise.toml`
  (antes se detectaban pero no generaban gates): `mvn -B compile/test`,
  `gradle build/test`, `go build/test ./...`, `cargo build/test`.
- `doctor` **detecta el toolchain** de esos stacks (mvn, gradle, go, cargo) y
  cómo instalarlo, además de node/.NET.

### Detección más fina
- **Next.js** (`next.config.*`, cuenta como frontend → gate `ux`), **NestJS**
  (`nest-cli.json`, usa los scripts npm) y **Tailwind** (`tailwind.config.*`).
- **SQL Server**: detectado por el driver `SqlClient` en el `.csproj` (un
  dialecto SQL no se puede inferir del `*.sql` a ojo).

### Dialectos SQL por `.sqlfluff`
- El gate `database` ahora corre `sqlfluff lint .` **sin flag**; `init` genera un
  **`.sqlfluff`** con el dialecto del motor detectado (Postgres → `postgres`,
  SQL Server → `tsql`, Databricks → `databricks`).
- **Multi-motor** (p. ej. Postgres + SQL Server en el mismo repo): el `.sqlfluff`
  raíz toma el primario y comenta cómo dar su gramática al secundario (SQLFluff
  usa el `.sqlfluff` más cercano a cada archivo).

### Documentación
- Nueva sección **Matriz de gates por stack** en Ejecución y gates (ES/EN);
  SQLFluff y Analítica actualizadas al modelo de dialecto por `.sqlfluff`.

### Calidad
- 102 tests con pytest (12 nuevos en `tests/test_v015.py`).

## [0.14.0] - 2026-07-05

Modo *adopt*: acoplarse a repos que ya tienen un agente configurado.

### Adopción de proyectos existentes
- **`tramalia init --adopt`**: en vez de saltar los archivos que un repo con
  agente ya posee, **integra el gobierno sin pisarlos** (merge no destructivo):
  - `AGENTS.md` — anexa una sección `## Gobierno (Tramalia)` entre marcadores
    (`<!-- tramalia:gobierno -->`); re-ejecutar reemplaza el bloque, nunca duplica.
  - `.mcp.json` — fusiona Serena (y Engram/Headroom/Ponytail según flags)
    respetando tus servidores; si el JSON está malformado, no lo toca.
  - `CLAUDE.md` — agrega el import `@AGENTS.md` si faltaba.
- **Aviso automático**: un `init` normal que detecta un `AGENTS.md` sin gobierno
  te indica usar `--adopt` — el hueco de onboarding queda visible.
- `mise.toml` existente **no** se fusiona (merge de TOML es riesgoso): se
  respeta y se documenta cómo agregar gates a mano.
- Nuevo estado en el reporte de `init`: `adaptado` (junto a `creado`/`existe`).

### Documentación
- Nueva página **Adoptar un repo existente** (ES/EN) con diagrama del merge.

### Calidad
- 90 tests con pytest (9 nuevos en `tests/test_v014.py`).

## [0.13.0] - 2026-07-05

Criterio explícito de selección de herramientas + dos integraciones nuevas.

### Criterio de selección (contexto, memoria y eficiencia)
- **interop-contexto** e **interop-memoria** ganan la sección "El criterio: cuál
  montar y cuál usar" — 3 ejes: *qué pregunta responde* cada herramienta,
  **local primero** (ahorro de tokens + privacidad) y **degradación normal**
  (si no está instalada, el trabajo sigue — son aceleradores, no requisitos).
- **Desempate de grafos** (CodeGraph vs codebase-memory-mcp vs Graphify): por
  frecuencia de uso, lenguajes del repo y tipo de análisis; si hay dos o más,
  la elección se deja escrita en `AGENTS.md`.
- **Desempate de memoria N2** (Engram vs basic-memory vs mem0): una sola
  memoria activa, elegida por caso; N0 (repo + git) ya es memoria si no hay ninguna.
- **Eficiencia en orden**: 1º Ponytail (preventivo, cero riesgo), 2º caveman
  nivel **`lite`** (los niveles agresivos pierden contexto), 3º Headroom
  (máximo ahorro, solo opt-in por su modo proxy).
- La plantilla **AGENTS.md** incluye ahora la sección "Criterio de herramientas
  (local primero)" para que **los agentes apliquen el criterio en runtime**.

### Integraciones nuevas
- **markitdown** (Microsoft): ingesta PDF/Office/imágenes → Markdown; `doctor`
  la detecta (feature `context`); documentada como "puerta de entrada" del slot contexto.
- **notebooklm-mcp**: conocimiento externo curado vía Google NotebookLM
  (respuestas ancladas a fuentes). Documentada con **regla dura**: solo docs
  públicas de terceros, jamás código privado ni evidencia; no va en `doctor`
  ni en `.mcp.json` por defecto (cloud + npx).

### Calidad
- 81 tests con pytest (5 nuevos en `tests/test_v013.py`).

## [0.12.0] - 2026-07-04

Interfaz coherente e internacional + estrategia multi-host + soporte analítica.
Nace del feedback real de usar `tramalia ui` desde una instalación limpia de PyPI.

### Interfaz (TUI y CLI)
- **Ruta completa del proyecto** en la cabecera (antes solo el nombre de la carpeta).
- La línea de gates muestra los **gates reales de `mise.toml`** (build, test, lint…),
  no las features internas que confundían.
- Tabla de doctor con columna **"para qué"** (rol de cada herramienta) y tipo.
- El formulario de Cierre se **prellena con los valores reales** de `config.json`
  (tarea actual, agente, revisor) — se acabaron los placeholders de ejemplo.
- Al escribir un ID de tarea se muestra su **descripción desde `specs/tasks.md`**.
- Tecla **`i` instala lo que falta** (`mise install` en vivo, salida en pantalla);
  si falta mise, hint de instalación por SO (winget/curl/brew).
- Paleta de comandos de Textual desactivada (estaba solo en inglés).

### Guardia de inicialización (coherencia)
- `close`, `evidence` y `handoff` **se bloquean con mensaje claro (exit 1)** en
  proyectos sin inicializar — antes cerraban "con éxito" sin convención.
- Cierre sin gates dice honesto: "cerrada con **EXCEPCIÓN documentada**", no "✓ verificable".
- Las pestañas Auditoría y Cierre muestran el estado sin inicializar con botón
  **"Inicializar ahora"**.

### Internacionalización (i18n)
- Catálogos JSON `es`/`en` (`tramalia/i18n/`): agregar un idioma = agregar un JSON.
- Resolución: `TRAMALIA_LANG` > `config.json → language` > locale del sistema > inglés.
- `config.json` nuevo campo `"language": "auto"`.

### Planificación por horizontes
- Plantilla `specs/tasks.md` con `Estado` (pendiente·en-progreso·cerrada) y
  `Horizonte` (ahora·próximo·después); re-planificar = editar el archivo
  (humano o subagente `planificador`); las cerradas son inmutables por evidencia.

### Multi-host y analítica
- `doctor` **detecta CLIs de agentes instaladas** (claude, codex, antigravity,
  gemini, opencode) — solo informa, nunca configura (frontera con Gentle-AI).
- Nueva página de docs **"Modelos y esfuerzo por host"**: matriz modelo/esfuerzo
  por CLI, codex-plugin-cc, opusplan/ultrathink/ultracode.
- **Soporte Databricks/notebooks**: detecta `databricks.yml` y `*.ipynb`; gates
  `databricks bundle validate`, `nbstripout --verify`, `sqlfluff --dialect databricks`.
- Nuevas páginas de docs: **La interfaz (TUI)** y **Analítica** (ES/EN).

### Calidad
- 76 tests con pytest (10 nuevos en `tests/test_v012.py`).

## [0.11.0] - 2026-07-04

Segunda pasada de revisión del ecosistema — corrige recursos descartados sin
verificar en la entrega anterior.

### Integraciones
- **Graphify** en `doctor` (feature `context`): grafo de conocimiento CLI+MCP+skill
  desde código/docs/schemas — quinta alternativa en el slot de contexto junto a
  Serena, Repomix, codebase-memory-mcp y CodeGraph.
- **caveman** agregado al catálogo de skills (`skills.toml`, comentado): reduce
  ~65-75% los tokens de salida — familia ahorro de tokens junto a Headroom.

### Documentación (interop-agentes ES/EN)
- **Patrón Ralph loop** documentado: cómo correr Tramalia en un loop tipo Ralph
  usando `specs/tasks.md` como PRD, los subagentes como scheduler, y
  `tramalia close` como punto de handoff entre iteraciones.
- **`ultracode`** agregado junto a `ultrathink` (son distintos: turno único vs.
  modo de sesión completa con auto-orquestación de subagentes).
- Referencias a codex-plugin-cc (revisión cruzada Codex↔Claude Code, encaja con
  el rol `revisor`), gstack (pack de 31 skills, mismo espíritu que los
  subagentes), y ai-second-brain (memoria personal, distinta de Engram/N2).

### Calidad
- 66 tests con pytest.

## [0.10.0] - 2026-07-03

Instalación unificada en un comando + catálogo de skills externas.

### Instalación
- **`pip install tramalia-cli` es ahora la única línea necesaria**: Rich y
  Questionary (puras-Python, diminutas) pasan a ser dependencias por defecto —
  la experiencia recomendada sin corchetes. El núcleo sigue degradando a stdlib
  si faltan (`--plain`).
- **Auto-oferta de extras**: `tramalia ui` y `tramalia mcp` ofrecen instalar
  Textual/SDK MCP ahí mismo la primera vez (solo con terminal interactiva;
  en scripts imprimen el hint). Si el entorno bloquea pip (externally-managed,
  pipx), muestran el comando manual y `pipx inject` sin traceback.
- Alias `[pretty]` queda vacío (compatibilidad); nuevo alias `[full]`
  (Textual + SDK MCP de una vez).

### Integraciones (revisión del ecosistema)
- **Catálogo de skills externas verificadas** en `skills.toml` (comentadas):
  anthropics/skills (oficial), vercel-labs/agent-skills (web-design-guidelines
  complementa el gate ux), superpowers, mattpocock/skills.
- **CodeGraph** detectado por `doctor` (feature `context`): grafo pre-indexado
  con auto-sync, alternativa a Serena/codebase-memory-mcp.
- Docs: sección de orquestación multiagente externa (Multica/Vibe Kanban) y
  tips de Claude Code (`/model opusplan`, "ultrathink", `/compact`).

### Calidad
- 65 tests con pytest.

## [0.9.1] - 2026-07-03

Primer lanzamiento a PyPI.

### Empaquetado
- `[project.urls]` en `pyproject.toml` (Homepage/Documentation → sitio mkdocs,
  Repository, Changelog, Issues) — visibles en el sidebar de la página de PyPI.
- Clasificadores de PyPI (Development Status, Python 3.10–3.13, Topics).
- Workflow `.github/workflows/publish.yml`: construye sdist+wheel y publica en
  PyPI en cada GitHub Release, vía **Trusted Publishing** (OIDC, sin tokens).
- Validado con `twine check` (PASSED) e instalación limpia del wheel en venv nuevo.

### Documentación
- Instrucciones de instalación actualizadas a `pip install "tramalia-cli[...]"`
  para usuario final (README ES/EN, manual, instalación, flujo, ejemplo completo);
  la instalación editable (`pip install -e ".[dev]"`) queda reservada para
  contribuidores, con nota explícita apuntando a `CONTRIBUTING.md`.

## [0.9.0] - 2026-07-03

Comandos simples: el cierre del día a día son dos palabras.

### CLI
- **Task posicional** en `close`/`handoff`/`evidence`: `tramalia close TASK-001`
  (los flags `--task/--agent/--reviewer` siguen funcionando como overrides).
- **Defaults desde el proyecto**: agente/revisor salen de `.tramalia/config.json`
  (`agents.primary`/`agents.reviewer`); la tarea, del ID declarado en
  `.tramalia/current-task.md`. Resultado: `tramalia close` a secas cierra la tarea
  en curso con los agentes configurados.
- Prompt interactivo solo si hay terminal (los scripts caen a `TASK-000`, nunca
  se cuelgan). El menú prellena sus preguntas con estos mismos defaults.

### Documentación
- Tabla completa de los 15 comandos con ejemplos simples en ambos README.
- Referencia de comandos reescrita "forma simple primero" (sin corchetes en los
  títulos); cadena de resolución documentada en comandos/manual/flujo/ejemplo.

### Calidad
- 60 tests con pytest.

## [0.8.0] - 2026-07-03

Subagentes por rol con ruteo de modelo y auditoría de modelo.

### Subagentes (init)
- `.claude/agents/` con **5 roles de gobierno** que Claude Code lee nativamente:
  planificador→opus, **ejecutor→inherit** (respeta la selección del usuario en la app),
  revisor→opus, documentador→haiku, resolutor-profundo→fable (solo invocación explícita).
- Cada agente ancla su workflow a skills/comandos de Tramalia; idempotente (no pisa
  agentes existentes).

### Fan-out multi-host
- `tramalia sync` gana `--features` (def. `rules,subagents`): propaga también los
  subagentes vía rulesync a Copilot, Cursor, Cline y demás targets soportados.

### Auditoría de modelo
- `tramalia close --model <modelo>` registra en `metadata.json` qué modelo cerró la
  tarea; `tramalia log` lo muestra (`codex (opus)`).

### Presentación
- README en inglés pasa a ser el principal (`README.md`); el español queda en
  `README.es.md`. El About del repo enlaza la documentación.

### Calidad
- 52 tests con pytest.

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
