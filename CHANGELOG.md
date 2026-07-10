# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/). Este proyecto sigue versionado semántico.

## [0.32.0] - 2026-07-10

Español como idioma por defecto en README/PyPI/GitHub, y fix real en el tab
Cierre: los agentes prellenados ahora se detectan, no son un ejemplo fijo.
Primera fase (F1) del quinto entregable ampliado (rediseño + rebrand).

### README/PyPI/GitHub en español por defecto
- `README.md` (el que GitHub renderiza sin sufijo, y el que PyPI usa vía
  `pyproject.toml → readme`) es ahora la versión **en español**; el inglés
  quedó en `README.en.md`. La documentación del sitio (mkdocs) **ya** tenía
  español como default (`theme.language: es`, plugin i18n `default: true`)
  — no requirió cambios.
- Descripción del repo en GitHub ("About") actualizada a español, coherente
  con el README y con `pyproject.toml → description`.

### Fix: agentes del tab Cierre ya no son un ejemplo fijo
- `tramalia init` (y `upgrade`) grababan siempre `agents.primary = "codex"` y
  `agents.reviewer = "claude"` en `config.json`, **sin importar qué tuvieras
  instalado** — de ahí que el tab Cierre siempre precargara esos dos nombres.
- Nuevo `tools.detect_default_agents()`: detecta los agentes CLI reales
  presentes (excluye Antigravity IDE/2.0, que son apps de escritorio sin
  shell propio). Dos detectados → cross-review real (uno ejecuta, otro
  revisa); uno solo → se usa para ambos; ninguno → cae al mismo ejemplo
  editable de antes.
- Campo **Modelo** del tab Cierre: placeholder más claro (opcional, solo
  queda en `tramalia log`, no bloquea el cierre).

### Calidad
- 250 tests con pytest (6 nuevos en `tests/test_v032.py`). FAQ e interfaz
  documentadas ES/EN con el fix explicado.

## [0.31.0] - 2026-07-10

Versión de las skills externas y actualización selectiva. Primera parte (R5a)
del quinto entregable.

### Versión instalada vs. disponible
- Cada skill externa instalada muestra su **versión** (`@sha`, el commit corto)
  en `tramalia skills list` y en la pestaña Skills de la TUI.
- Nuevo **`tramalia skills outdated`** (o tecla **`u`** en la TUI): compara tu
  versión con el remoto (`git ls-remote`, sin modificar el repo) y marca las
  atrasadas con `instalada → disponible`.

### Actualizar una o todas
- **`tramalia skills sync <nombre>`** actualiza **solo esa** skill; sin nombre,
  todas (como antes). En la TUI, **Enter** sobre una skill instalada la
  **actualiza** (antes la desactivaba); sobre una no instalada, la instala.
- Nuevas funciones de core: `installed_ref`, `external_status(check_remote=…)`,
  y `sync_skills(root, only=…)`.

### Documentación
- La guía de skills explica los **3 estados** —incl. qué es una skill
  **"declarada"** (`◍`): en el manifiesto pero aún sin clonar— y trae una tabla
  **CLI ↔ TUI** con ambas vías para cada acción. FAQ e interfaz actualizadas (ES/EN).

### Calidad
- 244 tests con pytest (8 nuevos en `tests/test_v031.py`, con un repo git local
  como remoto para probar versión-instalada-vs-disponible sin red).

## [0.30.0] - 2026-07-10

Ciclo de vida del proyecto: **`tramalia upgrade`** para repos ya inicializados,
botón de init en Resumen, y fan-out multi-agente sugerido. Cuarto entregable (R4).

### `tramalia upgrade` (no-destructivo)
- Nuevo comando para poner al día un repo ya generado tras actualizar el CLI:
  **agrega** los archivos nuevos que falten y refresca el bloque de `.gitignore`,
  **sin tocar** nada existente (jamás pisa tus ediciones). Reporta el balance
  (`N nuevos, M sin cambios`) y apunta al CHANGELOG por cambios de plantilla.
- Nuevo marcador `.tramalia/version`: registra con qué versión se generó/actualizó
  el repo (lo escriben `init` y `upgrade`).
- El merge de 3 vías del contenido editado (estilo `copier update`) queda para
  el futuro; por ahora upgrade es aditivo + refresco de bloques gestionados.

### Botón de init en Resumen
- El botón **⚙ Inicializar** ahora vive también en la pestaña **Resumen**, justo
  donde dice "sin inicializar" — no había que ir a Cierre para inicializar.

### Fan-out multi-agente
- `init` (y `upgrade`) **detectan** los agentes CLI instalados y **sugieren**
  `tramalia sync` para propagar `AGENTS.md` a sus formatos (`.cursor/rules`,
  `.github/…`, `.clinerules`…). Nueva sección de docs "por qué init solo genera
  `.claude/`" + cómo **agregar tu propio agente** (`sync --to <target>`).

### Documentación
- Nueva doc de `upgrade` (comandos ES/EN), fila en las tablas de los READMEs, y
  FAQ: actualizar un repo, por qué solo `.claude/`, y **por qué `docs/`/`specs/`/
  `.mcp.json`/`mise.toml` NO se mueven a `.tramalia/`** (los leen sus consumidores
  en la raíz; repo-first). Corregidos conteos stale en READMEs (00-13, 16 skills).

### Calidad
- 236 tests con pytest (6 nuevos en `tests/test_v030.py`: upgrade recrea lo que
  falta sin pisar lo editado, marcador de versión, y botón init en Resumen con
  Pilot real).

## [0.29.0] - 2026-07-10

Skills: instalar en un paso y **skills externas fuera del repo sin perderlas**.
Tercer entregable (R3) del plan; responde directo a "las externas pesan +200MB
y no quiero subirlas, pero que no se pierdan al clonar".

### Skills externas fuera de git (re-hidratables)
- `tramalia init` deja un bloque en `.gitignore` que **excluye** las carpetas de
  skills externas de `.tramalia/skills/` y **conserva** las propias (`NN-*`).
  Cubre `.gitignore` **nuevo y existente** (append idempotente entre marcadores,
  sin pisar lo del usuario). Patrón verificado con git real.
- La fuente de verdad es el manifiesto `skills.toml` (sí versionado): un `git clone`
  + `tramalia skills` **re-hidrata** las externas localmente. Nadie pierde nada.
- **Chequeo de ya-commiteadas**: `.gitignore` no destrackea lo ya subido, así que
  `tramalia skills`/`list`/`update` **avisa** si detecta skills externas en git y
  da el remedio exacto `git rm -r --cached .tramalia/skills/<nombre>`.

### UX de skills
- En la TUI, **Enter instala en un paso** (declara + clona); si ya está, la
  desactiva. Antes eran dos pasos no señalizados (declarar, luego sync).
- Leyenda con los 3 estados y qué hace cada tecla; resumen `✓ n/total` en el sync.
- **Tecla `d`** abre la documentación (repo) de la skill seleccionada; para las
  propias, la guía de skills del sitio.

### Calidad
- 230 tests con pytest (7 nuevos en `tests/test_v029.py`: gitignore idempotente
  nuevo/existente, patrón real con git que excluye externas y conserva `NN-*`, y
  detección de externas ya commiteadas). Guía de skills, FAQ e interfaz ES/EN.

## [0.28.0] - 2026-07-10

Backend de contexto: detección correcta, ESC para cerrar, y manejo del caso
"elegí un backend que no tengo instalado". Segundo entregable (R2) del plan.

### Detección correcta (✓/○)
- El selector (tecla `b`) marcaba **Serena** como ○ (ausente) aunque estuviera
  disponible: usaba `shutil.which`, que no la ve porque corre efímera vía `uvx`.
  Ahora usa la **misma sonda que `doctor`** (`probe`) — nuevo `backend_installed()`
  en `context_backend.py` — así Serena cuenta como instalada si tienes `uv`.
- El panel muestra claro cuál es el **backend activo** ("activo") y el estado
  instalado/no de cada opción.

### Cerrar el panel con ESC
- El selector de backend (y el de instalación) ahora se cierran con **Esc**
  (antes solo con el botón Cancelar): binding `escape` en ambos `ModalScreen`.

### Backend no instalado
- Elegir un backend que no tienes instalado lo **fija igual** (es una preferencia
  de proyecto, no una comprobación) y **avisa** cómo obtenerlo (tecla `i` o elige
  otro). La línea del Resumen ahora dice **"backend de contexto: X (activo)"**.

### Calidad
- 223 tests con pytest (5 nuevos en `tests/test_v028.py`: detección de Serena
  efímera, ESC cierra el panel con Pilot real, y persistencia al elegir un backend
  no instalado). FAQ e interfaz documentadas en ES/EN.

## [0.27.0] - 2026-07-10

Instalador correcto de agentes/hosts: se arregla el caso real de "instalé Go y
engram no se instaló", se aclaran los labels CLI vs. app de escritorio, y se
cablean OpenClaw, Hermes y las **tres superficies de Antigravity**. Primer
entregable (R1) del plan de mejoras post-feedback.

### El bug principal (engram tras Go)
- winget agrega Go al PATH del **usuario**, no al del **proceso** de la TUI en
  marcha, así que engram seguía viéndose "bloqueado por Go" en la misma sesión.
- Ahora, al terminar de instalar un runtime, Tramalia **refresca el PATH del
  proceso** (`C:\Program Files\Go\bin`, `~/go/bin`, `C:\Program Files\nodejs`) y
  **encadena** en la misma corrida la herramienta que ese runtime desbloquea
  (⬇ instalar Go → engram, sin reiniciar la terminal).

### Agentes y hosts
- **Labels con "CLI" explícito** (Claude Code CLI, OpenAI Codex CLI, Antigravity
  CLI `agy`) para no confundir con las apps de escritorio homónimas.
- **OpenClaw**: automatizable por npm (`npm i -g openclaw`, requiere Node) — antes
  solo decía "ver documentación".
- **Hermes Agent**: se muestra su comando real (`curl … | bash`) como **manual**
  (Tramalia nunca ejecuta pipes) — antes solo decía "ver documentación".
- **Antigravity, tres superficies**: CLI `agy` (Windows: winget `Google.AntigravityCLI`,
  automatizable; mac/linux: script manual), **IDE** (`Google.AntigravityIDE`) y
  **2.0** (`Google.Antigravity`). Las dos apps de escritorio no tienen comando en
  PATH: se detectan con `winget list` (nuevo campo `winget_id` + sonda cacheada).

### UX de instalación
- El log muestra **progreso por ítem** `[i/total]` y el sync de skills un resumen
  `✓ n/total`. (Un % real por herramienta no existe: winget/npm/go no lo emiten.)

### Calidad
- 218 tests con pytest (9 nuevos en `tests/test_v027.py`: labels, openclaw/hermes,
  las 3 superficies de Antigravity, detección por `winget_id`, refresh de PATH y
  encadenado engram-tras-Go). `test_headroom` ahora es hermético (no depende de
  binarios en `~/.local/bin` del equipo).

## [0.26.0] - 2026-07-10

Estilo arquitectónico declarado explícitamente (no impuesto), con criterio y
guardrail anti-sobreingeniería — corrige un sesgo real que traía la plantilla.

### El hallazgo
`docs/ai/01-arquitectura.md` ya traía, sin nombrarla, una regla de dependencia
*"UI → aplicación → dominio"* **para todo proyecto por igual** — un sabor de
Domain-Driven Design/Hexagonal aplicado incluso a un CRUD simple. Eso viola el
propio Ponytail/YAGNI del producto: abstraer capas que el proyecto no pidió.

### Estilo arquitectónico: ahora es una decisión declarada
- Nueva sección **"Estilo arquitectónico de este proyecto"** en `01-arquitectura.md`
  (contenido de plantilla, sin lógica nueva — verificado que **no** depende del
  stack detectado: es decisión de negocio, no técnica, y Tramalia no la infiere).
- **Default explícito si no se declara**: el más simple que resuelva la tarea
  (CRUD/Transaction Script) — nunca DDD/Hexagonal por defecto.
- La sección "Reglas de dependencia" queda **condicionada**: solo aplica si el
  proyecto declaró Domain-Driven Design/Hexagonal/Onion.
- `AGENTS.md` gana un guardrail: *"no metas capas de dominio/hexagonal 'por si
  acaso' — eso también es YAGNI"*.
- Cambiar de estilo después (p. ej. CRUD → DDD porque el negocio creció) es
  candidato a **ADR** en `docs/ai/05` — no es un cambio silencioso.

### Nueva página: Patrones de arquitectura
- ES/EN, en Conceptos: los 4 estilos (CRUD, Transaction Script, Domain-Driven
  Design + Hexagonal/Onion, Data-Oriented Design) con alcance, cuándo usar cada
  uno, y por qué Hexagonal es compatible con DDD pero no depende de él.
- Glosario gana 6 términos: CRUD, DDD, Data-Oriented Design, Hexagonal/Onion,
  Lenguaje ubicuo, Transaction Script (ES/EN).

### Calidad
- 208 tests con pytest (10 nuevos en `tests/test_v026.py`), incluida la prueba
  de que dos stacks distintos generan el mismo texto (no se infiere del stack)
  y que `--adopt` no reescribe un `01-arquitectura.md` ya existente.

## [0.25.0] - 2026-07-09

Tope de modelos para los subagentes: opt-in, por niveles, portable entre
proveedores (Claude/Codex/Antigravity/gateways).

### `tramalia agents cap <nivel>`
- Fija un **tope**: ningún rol usa un modelo por encima; lo inferior se conserva.
  Ejemplo `cap sonnet`: planificador/revisor/resolutor → sonnet, documentador
  sigue en haiku, ejecutor (inherit) intacto. Ranking: fable > opus > sonnet > haiku.
- `tramalia agents list` muestra rol → modelo actual → default + el tope activo.
- Se guarda en `.tramalia/config.json → agents.model_cap` (default `none`) y se
  refleja en `.tramalia/context/tools.json → model_cap`.
- `init --model-cap <nivel>` para fijarlo de entrada; `cap none` restaura los defaults.

### Portabilidad multi-proveedor (enforcement donde se puede, convención donde no)
- **Claude Code**: aplicado — Tramalia reescribe el `model:` de `.claude/agents/`.
- **Codex / Antigravity (`agy`) / gateways**: regla portable en `AGENTS.md` +
  `model_cap` en `tools.json`; `agents cap` **imprime la equivalencia por nivel
  de capacidad** (no por nombre de modelo) para que el usuario/Gentle-AI la
  aplique — Tramalia NO escribe configs de terceros (frontera con Gentle-AI).

### Documentación
- Nueva sección "Tope de modelos, portable entre proveedores" en Modelos y
  esfuerzo por host (ES/EN) con la matriz por host, la receta
  "planificar con Claude → ejecutar con Codex" (codex-plugin-cc), y la
  aclaración de que los 5 archivos de agentes son editables.
- interop-agentes, comandos y Ayuda (FAQ) actualizados.

### Calidad
- 198 tests con pytest (12 nuevos en `tests/test_v025.py`).

## [0.24.0] - 2026-07-08

CodeGraph automatizable + fix de detección de Antigravity (agy) + backend de
contexto seleccionable por proyecto (CLI y TUI).

### CodeGraph: automatizable de verdad
- Tenía paquete npm real (`@colbymchenry/codegraph`) que no estábamos usando —
  quedaba marcado "solo manual" sin comprobarlo. Ahora se automatiza igual que
  repomix/opencode (con Node; si falta, el selector ofrece instalarlo).

### Antigravity: el binario se llama `agy`, no `antigravity`
- Verificado en fuentes oficiales: el comando real en PATH tras instalar
  Antigravity CLI es **`agy`** (reemplazó a Gemini CLI, descontinuada
  2026-06-18). La detección buscaba el nombre equivocado — corregido.
- La instalación sigue siendo **manual a propósito**: scripts oficiales
  `curl`/`irm` nunca se ejecutan automatizados (regla dura), y requiere login
  interactivo con Google después de instalar.

### Backend de contexto: uno activo por proyecto, elegible con info
- Nuevo `.tramalia/config.json → context.backend` (default `serena`): fija
  **cuál** de Serena/CodeGraph/codebase-memory-mcp/Graphify usan los agentes,
  para que no alternen entre índices inconsistentes dentro del mismo proyecto.
- **CLI**: `tramalia context list` (alcance + caso de uso ideal + instalada/
  activa de cada uno) y `tramalia context set <backend>`.
- **TUI**: tecla **`b`** abre un selector único con la misma información;
  línea en Resumen muestra el backend activo.
- Se refleja en `.tramalia/context/tools.json → context_backend` (que los
  agentes ya consultan) y en una regla nueva de `AGENTS.md`.
- Repomix y markitdown quedan explícitamente fuera de la selección: son
  utilidades puntuales, no compiten por el rol de backend.

### Documentación
- Interop-contexto, interfaz, comandos, instalación y Ayuda (FAQ) actualizados
  en ES/EN; corregido de paso "tres vistas" → "cuatro vistas" en `comandos.md`.

### Calidad
- 186 tests con pytest (15 nuevos en `tests/test_v024.py`, incl. 2 con el
  harness real de Textual).

## [0.23.0] - 2026-07-08

Versión visible en el UI + prerequisitos de runtime (Node/Go) transparentes.

### Versión en el UI
- La **versión de Tramalia** aparece en el título de `tramalia ui` y en el panel
  de `tramalia doctor`/`detect` (además de `tramalia --version`).

### Prerequisitos de runtime: visibles y facilitados
- Si una herramienta solo se automatiza con un runtime ausente (engram vía
  `go install` → **Go**; opencode/repomix vía npm → **Node.js**), el doctor lo
  **marca en el detalle** (*«· requiere Go»*) y el selector la lista en el bloque
  manual anotada como *«requiere Go»* — ya no parece que "no se pueda instalar".
- El selector (tecla `i`) y `doctor --fix` **ofrecen instalar el runtime**
  (⬇ instalar Go → habilita engram): lo instalas, repites `i` y la herramienta
  pasa a automatizable. **Go** ahora es instalable (winget/brew) como Node.

### Documentación
- Interfaz y Ayuda (FAQ) documentan los prerequisitos de runtime y dónde ver
  la versión. Checklist de docs ampliado (FAQ + READMEs + MkDocs).

### Calidad
- 171 tests con pytest (7 nuevos en `tests/test_v023.py`).

## [0.22.1] - 2026-07-08

engram SÍ se automatiza en Windows (`go install`) + FAQ al día.

### engram instalable en cualquier SO
- brew era solo macOS; ahora el instalador ofrece **`go install github.com/
  Gentleman-Programming/engram/cmd/engram@latest`** en Windows/mac/linux si Go
  está presente (binario de releases como respaldo manual).
- El doctor detecta engram instalado por go en `~/go/bin` (o `$GOPATH/bin`)
  aunque no esté en el PATH — estado *"instalada vía go"* (mismo patrón que uv/mise).

### Documentación
- **Ayuda (FAQ)** actualizada: engram en Windows, el selector que muestra todas
  las faltantes, y qué significa "○ no instalada (opcional)".

### Calidad
- 164 tests con pytest (1 nuevo: probe detecta go-install; engram-windows ajustado).

## [0.22.0] - 2026-07-08

Doctor por dominio, estado instalada/no claro, selector completo + PATH de uv,
y el principio "analiza antes de intervenir" como convención de primera clase.

### Doctor: grupos por dominio y estado real
- La tabla se **subdivide por dominio** (contexto · memoria · seguridad · base de
  datos · UX/UI · analítica · convención), no un genérico "features" — así sabes
  qué es de cada cosa. (CLI y TUI.)
- El estado dice **instalada o no** sin ambigüedad: `✓ instalada` /
  `○ no instalada (opcional)` / `✗ no instalada (requerida)` (antes "opcional"
  se confundía con "no está").

### Instalador: nada se omite + PATH de uv
- **Bug corregido**: el selector solo mostraba las herramientas automatizables,
  omitiendo en silencio engram/codegraph/hermes/etc. Ahora lista **todas** las
  faltantes — las automatizables marcables, las manuales visibles con su comando.
- **engram** instalable vía brew (mac/linux); **codegraph** visible como manual.
- **PATH de uv**: el doctor detecta si `~/.local/bin` está en tu PATH y ofrece
  configurarlo (`uv tool update-shell`) — en `doctor --fix` y en el selector `i`.
- `.tramalia/context/tools.json` ahora incluye `uv_bin_on_path`.

### Principio "analiza y planifica antes de intervenir código"
- Nueva regla central en la plantilla `AGENTS.md`: antes de tocar código,
  producir análisis + plan con subpuntos (en `specs/tasks.md`) + riesgos, y en
  tareas no triviales esperar confirmación. Reforzado en la skill `01-spec-governance`.
- Nueva página de docs **"Cómo trabaja una IA con Tramalia"** (ES/EN): el flujo
  analizar→plan→considerar→ejecutar→cerrar, y proyecto nuevo vs. existente.

### Documentación (revisión general)
- **Auditoría vs. Cierre** aclarado con tabla (acción que produce evidencia vs.
  lectura que la consulta).
- Conteos explícitos: `docs/ai/` son **14 archivos (00–13)**, skills son **16**.
- interfaz/comandos actualizados a los grupos por dominio y el estado nuevo.

### Calidad
- 163 tests con pytest (7 nuevos en `tests/test_v022.py`).

## [0.21.1] - 2026-07-07

Fix de la TUI reportado en uso real: la tecla `d` (docs) dejaba un panel
bloqueado, imposible de cerrar. Más una aclaración de documentación pendiente.

### Fix: panel de la tecla `d` sin forma de cerrarse
- `d` reutilizaba el panel del instalador (`#instalador`) y lo dejaba en
  `display: True` para siempre — no había ninguna acción que lo ocultara.
- Ahora `d` usa una **notificación** (toast, se cierra sola) en vez de abrir
  el panel — que debe aparecer solo durante una instalación real.
- Nueva tecla **`Esc`**: cierra el panel del instalador y el de skills si
  quedaron abiertos tras una instalación o un sync — cubre también ese caso
  simétrico (mismo patrón, mismo bug latente).
- 2 tests nuevos con el harness de Textual (`run_test`/Pilot) que verifican
  el comportamiento real de los paneles, no solo que la app construya.

### Documentación: skills propias vs. skills nativas del CLI
- Nueva sección en la guía de skills aclarando que Tramalia **no analiza ni
  toca** las skills/plugins nativos de tu CLI (p. ej. el marketplace de
  Claude Code): son sistemas separados que conviven sin sincronizarse — las
  de Tramalia viven versionadas en el repo (`.tramalia/skills/`), las
  nativas viven en la configuración de tu CLI.

### Calidad
- 156 tests con pytest (2 nuevos en `tests/test_v021b.py`).

## [0.21.0] - 2026-07-07

Agentes conscientes de las herramientas + skills por URL + página de Ayuda.

### tools.json: los agentes ya no llaman a ciegas
- `tramalia doctor` escribe **`.tramalia/context/tools.json`** (qué está
  instalado, versión, y la alternativa de cada ausente).
- La plantilla `AGENTS.md` ordena: *"antes de invocar una herramienta externa,
  consulta tools.json; si `installed` es false, usa su alternativa o continúa"*
  — se acabaron los turnos quemados invocando semgrep inexistente.

### Skills por URL
- **`tramalia skills add <url-git> [nombre]`** — declara la skill en el
  manifiesto (nombre derivado del URL; sin duplicados; URL validada).
- En la TUI: **input en la pestaña Skills** — pegar URL + Enter; `s` la clona.

### Documentación
- Nueva página **Ayuda (FAQ)** (ES/EN): los tropiezos reales resueltos — uv y
  el PATH, shims de mise, instalaciones pegadas/admin, guardia de init,
  excepciones de gates, idioma, actualizar el CLI, skills.
- **Multi-host** gana la sección *Apps de escritorio e IDEs* (Claude Code
  desktop, Codex desktop, Antigravity IDE — funcionan hoy: repo-first).

### Calidad
- 154 tests con pytest (6 nuevos en `tests/test_v021.py`).

## [0.20.0] - 2026-07-07

Instalador robusto: streaming en vivo, cancelación, y detección fiel de lo
instalado por uv/uvx. Nace del feedback real (headroom-ai pegado sin salida).

### Instalación con feedback real
- **Salida línea a línea en vivo** en un panel al costado de la tabla (layout
  tabla|log) — se acabó el "no sé si va bien" (antes: bloqueante, todo al final).
- **Tecla `c` cancela** la instalación en curso y sigue con la siguiente — una
  pegada ya no bloquea al resto de la selección.
- **Watchdog con timeout por herramienta**: un proceso pegado EN SILENCIO
  también se termina (era justo el caso reportado).
- Detección de errores de permisos (winget/choco): mensaje claro *"requiere
  terminal como ADMINISTRADOR"*.
- Las vías manuales ya no ensucian el log: viven en la columna detalle.

### Detección fiel (estados ok reales)
- **Instaladas vía uv**: `uv tool install` deja los binarios en `~/.local/bin`,
  que en Windows NO entra al PATH ni reiniciando (salvo `uv tool update-shell`)
  — el doctor ahora revisa esa carpeta directamente.
- **Serena**: estado propio `✓ vía uvx — no requiere instalación` (es efímera).

### Registro y documentación de herramientas
- **Tecla `d`**: abre la documentación oficial de la herramienta seleccionada
  (nuevo mapa `DOCS` con la URL de cada una).
- **opencode** automatizable vía npm; **openclaw** y **hermes** detectables;
  **gemini eliminado** (absorbido por Antigravity).

### Calidad
- 148 tests con pytest (9 nuevos en `tests/test_v020.py`, incl. cancelación y
  timeout de procesos mudos).

## [0.19.0] - 2026-07-07

Administración de skills desde la TUI y la CLI — la contraparte de las
herramientas (tecla `i`), ahora para skills.

### Core (`core/skills.py`)
- **`catalog()`**: el catálogo completo de skills externas, **incluidas las
  comentadas** de `skills.toml` (invisibles para tomllib; parser propio) —
  cada una con estado: instalada · declarada · disponible.
- **`set_enabled()`**: activa/desactiva el bloque de una skill comentando/
  descomentando **solo sus líneas**; conservador (si no reconoce el bloque con
  certeza no toca nada) e idempotente.
- **`own_skills()`**: las 16 propias con su descripción (frontmatter).

### TUI: pestaña Skills (nueva, cuarta)
- Tabla agrupada: **propias (01–16)** con descripción · **externas** con estado.
- **Enter** sobre una externa la activa/desactiva en `skills.toml`.
- **Tecla `s`**: sincroniza las declaradas (clona/actualiza desde sus repos)
  con resultado en vivo.

### CLI en paridad
- `tramalia skills list` muestra ahora las 16 propias + el catálogo completo
  con estados (antes solo veía las descomentadas).
- Nuevos: `tramalia skills enable <nombre>` / `disable <nombre>`.

### Documentación
- Interfaz: sección "Pestaña Skills" + atajo `s` (ES/EN); la guía de skills
  referencia las tres vías equivalentes (CLI, TUI, TOML a mano).

### Calidad
- 139 tests con pytest (8 nuevos en `tests/test_v019.py`).

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
