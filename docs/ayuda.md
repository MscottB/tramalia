# Ayuda (FAQ y solución de problemas)

Respuestas a los tropiezos reales más comunes. Si el tuyo no está: [abre un issue](https://github.com/MscottB/tramalia/issues).

## Instalación y doctor

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
