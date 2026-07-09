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
Su única vía automatizable necesita ese runtime, que no tienes. Desde v0.23 el selector (tecla `i`) te **ofrece instalar el runtime** (⬇ instalar Go → habilita engram): instálalo, vuelve a pulsar `i` y la herramienta ya es automatizable. En CLI: `tramalia doctor --fix` incluye el runtime en el plan. Runtimes que habilitan automatización: **Node.js** (herramientas npm) y **Go** (engram).

**¿Dónde veo la versión de Tramalia?**
En el título de la cabecera de `tramalia ui`, en el panel de `tramalia doctor`/`detect`, y con `tramalia --version`. Actualiza el CLI con `pip install -U tramalia-cli`.

**CodeGraph aparecía como "solo manual" y no se podía automatizar.**
Era un error nuestro: sí tiene paquete npm (`@colbymchenry/codegraph`). Desde v0.24 se automatiza igual que repomix/opencode — si Node falta, el selector ofrece instalarlo primero.

**Antigravity aparece como "falta" aunque lo instalé.**
El binario real que queda en el PATH se llama **`agy`**, no `antigravity` (Antigravity CLI reemplazó a Gemini CLI, descontinuado el 18-06-2026). La detección buscaba el nombre equivocado — corregido en v0.24. La instalación (script oficial `curl`/`irm`) sigue siendo manual a propósito: nunca ejecutamos scripts remotos automatizados, y además requiere login interactivo con Google después.

## Contexto: cuál herramienta de navegación usar

**Tengo Serena, CodeGraph, codebase-memory-mcp y Graphify instalados — ¿cuál usa el agente?**
La que fija `.tramalia/config.json → context.backend` (default `serena`). Es un valor **por proyecto**, no una decisión que el agente tome cada vez — evita que alterne entre índices inconsistentes. Cámbialo con `tramalia context set <backend>` o la tecla `b` en `tramalia ui` (te muestra el alcance y el caso de uso ideal de cada uno antes de elegir). Ver `tramalia context list` para el detalle completo.

**¿Repomix y markitdown también hay que elegirlos?**
No — son utilidades puntuales (snapshot completo / ingesta de documentos), no compiten por el backend activo. Se usan cuando corresponde, sin importar cuál sea el backend de navegación.

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
Sí — leen `AGENTS.md` y ejecutan shell igual que sus CLI; `tramalia close` corre idéntico. Ver [Modelos y esfuerzo por host](multi-host.md).

## Interfaz e idioma

**La TUI sale en el idioma equivocado.**
Resolución: `TRAMALIA_LANG` > `config.json → language` > locale del sistema. Fuerza con `TRAMALIA_LANG=es tramalia ui`.

**¿Cómo actualizo Tramalia?**
`pip install -U tramalia-cli` (el CLI). `tramalia update` actualiza *lo orquestado* (tools de mise + skills), no el paquete.

## Skills

**Agregué una skill por URL y no aparece clonada.**
`add` solo la declara en el manifiesto; clónala con `tramalia skills` (o tecla `s` en la TUI).

**Enter sobre una skill no hace nada.**
Solo las **externas** se activan/desactivan; las propias (01–16) siempre están instaladas. Si el bloque del TOML fue editado a mano con otro formato, el toggle conservador no lo toca — ajústalo manualmente.
