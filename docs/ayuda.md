# Ayuda (FAQ y solución de problemas)

Respuestas a los tropiezos reales más comunes. Si el tuyo no está: [abre un issue](https://github.com/MscottB/tramalia/issues).

## Instalación y doctor

**Al actualizar (`pip install -U tramalia-cli`) aparece "WARNING: Ignoring invalid distribution ~ramalia-cli".**
No es un problema de Tramalia — es un artefacto de pip en Windows. Si `tramalia ui` (u otro proceso) tenía el paquete en uso durante una actualización *anterior*, pip no pudo borrar la versión vieja y la dejó **renombrada con `~`** en tu carpeta `site-packages` (`~ramalia` y `~ramalia_cli-X.YY.Z.dist-info`, donde `X.YY.Z` es la versión que quedó a medio borrar) en vez de eliminarla del todo. La instalación **nueva queda sana igual** — confírmalo con `tramalia --version` — el warning es solo ruido de esas carpetas huérfanas.

Para limpiarlo: cierra cualquier `tramalia ui` abierto y borra las carpetas `~ramalia*` de tu `site-packages` (la ruta exacta la ves en el propio warning):
```powershell
Remove-Item -Recurse -Force "<ruta-a-site-packages>\~ramalia"
Remove-Item -Recurse -Force "<ruta-a-site-packages>\~ramalia_cli-X.YY.Z.dist-info"
```
Sustituye `X.YY.Z` por el número de versión real que aparece en el nombre de la carpeta.

**Instalé una herramienta con uv y sigue apareciendo como "falta", incluso tras reiniciar la terminal.**
`uv tool install` deja los binarios en `~/.local/bin`, que en Windows **no entra al PATH** (ni reiniciando) salvo que corras `uv tool update-shell`. Desde v0.20 el doctor revisa esa carpeta directamente y la marca *"instalada vía uv"*; para usarla desde tu shell, corre `uv tool update-shell` una vez.

**Instalé con mise y `doctor` no la veía.**
Las herramientas de mise viven tras sus *shims*, fuera del PATH hasta `mise activate` o reiniciar la terminal. El doctor las detecta igual (`mise which`) y te lo indica.

**Una instalación se queda pegada (p. ej. headroom-ai).**
En la TUI la salida corre en vivo: si no avanza, **`c` la cancela** y sigue con la siguiente; además cada herramienta tiene tiempo límite. Si el error menciona acceso denegado, ábrela desde una **terminal como administrador**.

**winget/choco falla con un error 0x8…**
Casi siempre es elevación: terminal como administrador y reintenta. El panel de instalación te lo avisa cuando lo detecta.

**Serena aparece como "no requiere instalación", ¿es un error?**
No: Serena corre vía `uvx` (efímera). Con uv presente, está lista — `init` ya la cabló en `.mcp.json`.

**¿Se puede instalar engram en Windows? / no aparecía en el selector.**
Sí. brew es solo macOS, pero engram se instala en **cualquier SO con `go install github.com/Gentleman-Programming/engram/cmd/engram@latest`** — desde v0.22.1 el selector (tecla `i`) lo ofrece automatizado si tienes **Go** instalado (si no, muestra la vía manual: binario de sus *releases*). El binario queda en `~/go/bin`; el doctor lo detecta ahí aunque no esté en tu PATH (`instalada vía go`). Si tu shell no lo encuentra, agrega `~/go/bin` al PATH.

**En el selector de instalar (`i`) no aparecían algunas herramientas (engram, codegraph, hermes…).**
Desde v0.22 el selector muestra **todas** las faltantes: las automatizables como marcables y las que solo tienen vía manual listadas aparte con su comando. Antes se omitían en silencio las que no tenían instalador automático en tu sistema.

**Una herramienta dice "○ no instalada (opcional)": ¿está o no?**
No está instalada. "Opcional" solo significa que no la necesitas salvo que uses su gate/feature. El estado siempre dice explícito: `✓ instalada` · `○ no instalada (opcional)` · `✗ no instalada (requerida)`.

**Una herramienta dice "requiere Go" (o Node) y no la puedo instalar automático.**
Su única vía automatizable necesita ese runtime, que no tienes. Desde v0.23 el selector (tecla `i`) te **ofrece instalar el runtime** (⬇ instalar Go → habilita engram): márcalo junto con lo demás y desde **v0.27** Tramalia instala el runtime **y encadena** la herramienta que desbloquea en la misma corrida, **sin reiniciar la terminal** (refresca el PATH del proceso para ver el Go/Node recién instalado). En CLI: `tramalia doctor --fix` incluye el runtime en el plan. Runtimes que habilitan automatización: **Node.js** (herramientas npm) y **Go** (engram).

**Instalé Go pero engram no se instaló en la misma sesión.**
Corregido en **v0.27**. El problema: winget agrega Go al PATH del *usuario*, no al del proceso de la TUI en marcha, así que engram seguía viéndose "bloqueado por Go" hasta reiniciar. Ahora, al terminar de instalar un runtime, Tramalia agrega su carpeta de binarios (`C:\Program Files\Go\bin`, `~/go/bin`, `C:\Program Files\nodejs`) al PATH del proceso y **encadena** engram automáticamente. Si aun así falla, reinicia la terminal y vuelve a pulsar `i`.

**¿Dónde veo la versión de Tramalia?**
En el título de la cabecera de `tramalia ui`, en el panel de `tramalia doctor`/`detect`, y con `tramalia --version`. Actualiza el CLI con `pip install -U tramalia-cli`.

**CodeGraph aparecía como "solo manual" y no se podía automatizar.**
Era un error nuestro: sí tiene paquete npm (`@colbymchenry/codegraph`). Desde v0.24 se automatiza igual que repomix/opencode — si Node falta, el selector ofrece instalarlo primero.

**Antigravity aparece como "falta" aunque lo instalé.**
El binario real del CLI que queda en el PATH se llama **`agy`**, no `antigravity` (Antigravity CLI reemplazó a Gemini CLI, descontinuado el 18-06-2026). La detección buscaba el nombre equivocado — corregido en v0.24. Desde **v0.27** el CLI se **automatiza en Windows vía winget** (`Google.AntigravityCLI`); en mac/linux sigue siendo el script oficial `curl`, manual a propósito (nunca ejecutamos scripts remotos automatizados).

**¿Puedo instalar el IDE de Antigravity y Antigravity 2.0, no solo el CLI?**
Sí, desde **v0.27**. Antigravity tiene **tres superficies**: el **CLI** (`agy`), el **IDE** (fork de VS Code) y **Antigravity 2.0** (plataforma de agentes, app de escritorio). El doctor las lista las tres; en Windows se instalan por winget (`Google.AntigravityCLI` · `Google.AntigravityIDE` · `Google.Antigravity`). Como el IDE y 2.0 son apps de escritorio sin comando en el PATH, Tramalia las **detecta con `winget list`** (no con un `--version`).

**OpenClaw y Hermes: ¿se pueden automatizar?**
Desde **v0.27**: **OpenClaw** sí — es un CLI en npm (`npm i -g openclaw`, requiere Node); el `onboard`/daemon posterior es config tuya. **Hermes Agent** no: solo se instala por script (`curl … | bash`), que Tramalia nunca ejecuta automatizado — te muestra el comando exacto para que lo corras tú. Antes ambos decían solo "ver documentación".

## Contexto: cuál herramienta de navegación usar

**Tengo Serena, CodeGraph, codebase-memory-mcp y Graphify instalados — ¿cuál usa el agente?**
La que fija `.tramalia/config.json → context.backend` (default `serena`). Es un valor **por proyecto**, no una decisión que el agente tome cada vez — evita que alterne entre índices inconsistentes. Cámbialo con `tramalia context set <backend>` o la tecla `b` en `tramalia ui` (te muestra el alcance y el caso de uso ideal de cada uno antes de elegir). Ver `tramalia context list` para el detalle completo.

**¿Repomix y markitdown también hay que elegirlos?**
No — son utilidades puntuales (snapshot completo / ingesta de documentos), no compiten por el backend activo. Se usan cuando corresponde, sin importar cuál sea el backend de navegación.

**En el selector de backend (`b`), Serena aparecía con ○ aunque la tengo, y CodeGraph/Graphify con ✓.**
Corregido en **v0.28**. El ✓/○ usaba `shutil.which`, que no ve a **Serena** porque corre efímera vía `uvx` (nunca queda como binario en el PATH). Ahora usa la **misma sonda que `doctor`** (`probe`), así Serena se muestra instalada si tienes `uv`. También se ve claro cuál es el **backend activo** ("activo") y el estado instalado/no de cada uno.

**No podía cerrar el panel de backend con ESC, solo con Cancelar.**
Corregido en **v0.28**: **ESC cierra** el panel (equivale a Cancelar). Lo mismo aplica al panel de instalar (`i`).

**¿Qué pasa si elijo un backend que no tengo instalado?**
Se **fija igual** — el backend es una *preferencia del proyecto*, no una comprobación. Tramalia te **avisa** que no está instalado y te dice cómo obtenerlo (tecla `i` para instalarlo, o elige otro). Así declaras la intención del proyecto aunque aún no lo hayas instalado en tu máquina.

## Cierre y gates

**`close` me da exit 1 con "proyecto no está inicializado".**
Es la [guardia de inicialización](arquitectura.md#invariante-de-inicializacion): no hay gobierno sin convención. Corre `tramalia init` (o `--adopt` si ya tienes `AGENTS.md` propio).

**Cerró "con EXCEPCIÓN documentada" en vez de ✓.**
Significa que mise no está: los gates **no corrieron** y el estado honesto es `no_gates`. Instala mise (`tramalia doctor --fix`) para validación real.

**Un gate falla y necesito cerrar igual.**
`--allow-fail` — pero queda como `passed_with_exceptions` con la razón en `risks.md`, nunca como `passed`. La auditoría no se maquilla.

**El cierre se bloqueó por métricas.**
Definiste `.tramalia/thresholds.json` y una métrica de `.tramalia/metrics.json` lo incumple (o falta). Ver [Analítica](analitica.md#metricas-y-umbrales-en-la-evidencia-mlanalitica).

## Agentes

**Mi agente intenta usar herramientas que no están instaladas.**
Corre `tramalia doctor`: genera `.tramalia/context/tools.json` y la regla de `AGENTS.md` le indica al agente consultarlo antes de invocar — si `installed` es false, usa la alternativa o continúa sin ella.

**¿Sirve con Claude Code desktop / Codex desktop / Antigravity IDE?**
Sí — leen `AGENTS.md` y ejecutan shell igual que sus CLI; `tramalia close` corre idéntico (no hay versión "para app" y otra "para CLI": todo vive en el repo). Ver [Modelos y esfuerzo por host](multi-host.md).

**Solo quiero usar Sonnet — los subagentes están en opus/fable y no los tengo.**
`tramalia agents cap sonnet`: baja a sonnet todo lo que esté por encima (planificador, revisor, resolutor-profundo) y **conserva lo de abajo** (documentador sigue en haiku); `ejecutor` (inherit) sigue tu sesión. Default es `none` (sin tope). `tramalia agents cap none` restaura el ruteo original. También `tramalia init --model-cap sonnet` de entrada.

**¿Los 5 archivos de `.claude/agents/` los puedo editar?**
Sí, son **tuyos** — `tramalia init` es idempotente y nunca los pisa. Edita el `model:` o el cuerpo a mano si quieres; `agents cap` solo gestiona la línea `model:` de los 5 roles.

**Tengo el tope en Claude pero uso Codex/Antigravity — ¿se respeta?**
En esos hosts no hay ruteo por rol que Tramalia pueda reescribir (y no tocamos tu `~/.codex/config.toml` — eso es territorio de Gentle-AI). El tope viaja como **regla en `AGENTS.md`** (que el agente lee) + `model_cap` en `tools.json`; y `agents cap` te imprime la equivalencia por nivel de capacidad para que la pegues. Ver la matriz por host en [Modelos y esfuerzo por host → Tope de modelos](multi-host.md#tope-de-modelos-portable-entre-proveedores).

## Interfaz e idioma

**La TUI sale en el idioma equivocado.**
Resolución: `TRAMALIA_LANG` > `config.json → language` > locale del sistema. Fuerza con `TRAMALIA_LANG=es tramalia ui`.

**¿Cómo actualizo Tramalia?**
`pip install -U tramalia-cli` (el CLI). `tramalia update` actualiza *lo orquestado* (tools de mise + skills), no el paquete.

## Skills

**Agregué una skill por URL y no aparece clonada.**
`add` solo la declara en el manifiesto. En la TUI, **Enter** sobre una skill externa la **declara y la clona en un paso** (desde v0.29); por CLI, `tramalia skills` clona todas las declaradas. La tecla `s` sigue sincronizando todas; la tecla `d` abre la documentación (repo) de la skill seleccionada.

**¿Tenía que apretar Enter y luego sincronizar? No estaba claro.**
Antes sí eran dos pasos (declarar, luego sync) y no se explicaba. Desde **v0.29**, en la TUI **Enter instala en un paso** (declara + clona); si la skill ya está, Enter la desactiva. La leyenda de la pestaña Skills ahora muestra los 3 estados y qué hace cada tecla.

**Las skills externas pesan mucho y no quiero subirlas al repo — pero tampoco perderlas.**
Desde **v0.29** `tramalia init` deja un bloque en `.gitignore` que **excluye** las skills externas de `.tramalia/skills/` y **conserva** las propias (numeradas `NN-*`). No se pierden: el manifiesto `.tramalia/skills.toml` (sí versionado) las **re-hidrata** — quien clone el repo corre `tramalia skills` y se le descargan localmente. Cubre `.gitignore` nuevo y existente (append idempotente, sin pisar lo tuyo).

**Ya había commiteado las skills externas antes de esto.**
`.gitignore` no destrackea lo ya subido. `tramalia skills` (y `list`/`update`) **avisa** si detecta skills externas commiteadas y te da el remedio: `git rm -r --cached .tramalia/skills/<nombre>` (las saca del índice, no del disco; el `.gitignore` evita que se re-agreguen).

**Enter sobre una skill propia (01–16) no hace nada.**
Correcto: las propias siempre están instaladas y versionadas. Enter solo aplica a las **externas** (instalar/actualizar).

**¿Qué es una skill "declarada" (`◍`)?**
Está **anotada en el manifiesto** `.tramalia/skills.toml` (su bloque `[[skill]]` está activo) pero **aún no se clonó a disco**. Es el paso intermedio entre `○ disponible` (solo en el catálogo) y `✓ instalada` (ya en `.tramalia/skills/`). Tras clonar el repo, las externas arrancan declaradas (el manifiesto viaja, las carpetas no); un `tramalia skills` las trae.

**¿Cómo sé si una skill externa tiene una versión más nueva, y cómo la actualizo?**
Cada instalada muestra su **versión** como `@sha` (el commit corto). `tramalia skills outdated` (o la tecla **`u`** en la TUI) compara tu versión con el remoto (`git ls-remote`) y marca las atrasadas (`instalada → disponible`). Actualiza **una** con `tramalia skills sync <nombre>` (o Enter sobre ella en la TUI) o **todas** con `tramalia skills` (tecla `s`). Es un `git pull --ff-only` por skill; no toca nada más.

## Actualizar y estructura del repo

**Actualicé Tramalia (`pip install -U`) — ¿mi repo ya generado se pone al día solo?**
No. Corre **`tramalia upgrade`** (desde v0.30): agrega los archivos nuevos que tu versión no tenía y refresca el bloque de `.gitignore`, **sin tocar** ningún archivo que ya exista (nunca pisa tu trabajo). Te reporta el balance (`N nuevos, M sin cambios`) y apunta al CHANGELOG por cambios de plantilla que quizás quieras adoptar a mano. La versión con que se generó/actualizó queda en `.tramalia/version`.

**`init` deja `.claude/` pero no carpeta de Codex/Cursor/otros — ¿es un error?**
No. `.claude/agents/` se genera porque Claude Code lo lee **nativamente**; los demás agentes consumen la **fuente única `AGENTS.md`** y Tramalia la propaga a sus formatos con **`tramalia sync`** (rulesync) cuando lo pides — `init` te lo sugiere si detecta esos agentes. No se generan carpetas por-agente "por si acaso" (Ponytail/YAGNI). Para sumar tu propio agente: `tramalia sync --to <target>`. Ver [Por qué init solo genera .claude](interop-agentes.md).

**¿Puedo mover `docs/`, `specs/`, `.mcp.json` o `mise.toml` dentro de `.tramalia/` para ordenar?**
`AGENTS.md`, `.mcp.json` y `mise.toml` **deben quedar en la raíz**: es donde Claude Code, el estándar AGENTS.md y mise los leen — moverlos los rompe (ese es el punto de "repo-first"). `specs/` lo espera Spec Kit ahí. Tu preocupación de "que algo los pise" ya está cubierta sin mover nada: `init` es **idempotente** (no sobrescribe) y `AGENTS.md`/`CLAUDE.md`/`.gitignore` usan **bloques con marcadores** que solo se tocan a sí mismos. Lo que sí vive ordenado bajo `.tramalia/` es lo propio de Tramalia: `config.json`, `version`, `current-task.md`, `skills.toml`, `skills/`, `evidence/`, `context/`.
