# Referencia de comandos

Los nombres públicos de algunos comandos (`close`, `evidence`, `handoff`) se
conservan por compatibilidad. La documentación, los modelos y el esquema v1 usan
terminología española: **cierre**, **evidencia**, **traspaso**, `metadatos.json` y
estados formales en español ASCII.

El núcleo de gobierno funciona con Python. Las integraciones hacen llamadas
transparentes a herramientas externas y devuelven estados explícitos; no
ocultan errores ni convierten una ausencia en aprobación.

## Resumen

| Comando | Función | Tipo |
|---|---|---|
| `tramalia menu` | menú interactivo en bucle | núcleo |
| `tramalia ui` | panel TUI de resumen, skills, auditoría y cierre | núcleo + extra `[tui]` |
| `tramalia init` | genera la convención de forma idempotente | núcleo |
| `tramalia upgrade` | agrega archivos nuevos de la convención sin sobrescribir | núcleo |
| `tramalia doctor [--fix]` | diagnostica o instala herramientas seleccionadas | núcleo |
| `tramalia detect` | detecta stack y puertas de calidad aplicables | núcleo |
| **`tramalia close [TAREA]`** | **evalúa puertas y publica un cierre formal** | **núcleo** |
| **`tramalia log`** | **lee la bitácora estructurada v1** | **núcleo** |
| `tramalia evidence [TAREA]` | crea un paquete de evidencia | núcleo |
| `tramalia handoff [TAREA]` | registra un traspaso; alias público compatible | núcleo |
| `tramalia gates` | ejecuta puertas de calidad directamente | integración `mise` |
| `tramalia context [build\|list\|set <backend>]` | genera contexto y selecciona su backend | integración |
| `tramalia agents [list\|cap <nivel>]` | consulta o limita modelos de subagentes | núcleo |
| `tramalia sync [--to --features]` | propaga reglas y subagentes compatibles | integración `rulesync` |
| `tramalia skills [sync [<n>]\|list\|outdated\|enable\|disable\|add]` | administra el catálogo de skills | integración Git |
| `tramalia update` | actualiza herramientas orquestadas y skills | integración |
| `tramalia mcp` | inicia la fachada MCP | núcleo + SDK MCP |

## close — cierre gobernado

Una **puerta de calidad** (*quality gate*) es un comando automatizado que
verifica una condición necesaria: build, tests, lint, seguridad, base de datos,
UX u otra validación del dominio. `close` descubre las puertas declaradas en
`mise.toml`, ejecuta sus comandos exactos y registra resultados y salidas.

```bash
tramalia close              # tarea actual; agente/revisor desde config.json
tramalia close TASK-001     # ID explícito y seguro
```

Cadena de resolución:

| Dato | 1.º | 2.º | 3.º | Alternativa final |
|---|---|---|---|---|
| tarea | argumento posicional | `--task` | `.tramalia/current-task.md` | prompt interactivo o `TASK-000` en scripts |
| agente | `--agent` | `config.json → agents.primary` | — | valor vacío |
| revisor | `--reviewer` | `config.json → agents.reviewer` | — | valor vacío |
| modelo | `--model` | — | — | `null` en los metadatos |

La identidad declarada es información de auditoría, no una firma. `close` no
invoca al agente indicado: ejecuta puertas, evalúa política y persiste el mismo
resultado que consumen CLI, TUI y MCP.

### Estados formales

Las puertas agregadas usan:

- `aprobado`
- `fallido`
- `ejecutor_no_disponible`
- `sin_configurar`
- `configuracion_invalida`
- `error_ejecucion`

El cierre sólo puede quedar `aprobado`, `aprobado_con_excepciones` o
`bloqueado`. En particular, faltar `mise` produce
`ejecutor_no_disponible` y bloquea; no existe un estado aprobatorio implícito por
no haber ejecutado puertas.

### Excepciones

Una excepción completa debe indicar razón, riesgo aceptado, control afectado,
referencia, revisor y una expiración o condición de remediación. Cada excepción
sólo cubre su control; los fallos restantes mantienen el cierre `bloqueado`.

`--allow-fail` se conserva como alias de compatibilidad, pero no acepta una
excepción vacía ni transforma automáticamente un fallo en éxito. Cuando todos
los fallos están cubiertos por excepciones completas y vigentes, el resultado es
`aprobado_con_excepciones`.

### Resultado persistido

El paquete se publica atómicamente bajo una identidad única:

```text
.tramalia/evidencia/20260713T183012.123456Z-a1b2c3d4/
├── metadatos.json
├── traspaso.md
├── build-salida.txt
└── test-salida.txt
```

`metadatos.json` v1 contiene, entre otras, estas claves estables:

```json
{
  "version_esquema": 1,
  "id_paquete": "20260713T183012.123456Z-a1b2c3d4",
  "id_tarea": "TASK-001",
  "operacion": "cierre",
  "inicio_utc": "2026-07-13T18:30:12.123456Z",
  "fin_utc": "2026-07-13T18:30:18.123456Z",
  "entorno": {"tramalia": "0.34.0b1", "python": "3.13.5", "sistema_operativo": "Windows-11", "cadena_herramientas": {}},
  "git": {"commit": null, "rama": null, "limpio": null, "base_comparacion": null, "rastreados": [], "preparados": [], "no_rastreados": [], "renombrados": [], "eliminados": []},
  "comandos": [],
  "puertas": {"estado": "sin_configurar", "descubiertas": [], "ejecutadas": [], "omitidas": [], "fallidas": [], "errores_validacion": []},
  "estado_cierre": "bloqueado",
  "agente": "codex",
  "modelo": null,
  "metricas": {},
  "umbrales": {},
  "errores_validacion": [],
  "excepciones": [],
  "vinculo_traspaso": "traspaso.md"
}
```

Las salidas crudas se guardan fuera del JSON y se enlazan desde cada comando con
`archivo_salida` y `hash_salida`. Las marcas de tiempo son UTC; rutas inseguras,
hashes inválidos y números no finitos se rechazan antes de publicar.

### Métricas y umbrales

Si existe `.tramalia/metrics.json`, el cierre incorpora sus valores en
`metricas`. Si también existe `.tramalia/thresholds.json`, los límites se
registran en `umbrales`. Una métrica ausente o fuera de rango bloquea igual que
una puerta fallida. Un JSON malformado o un esquema incorrecto es un error de
configuración; no publica una falsa aprobación.

## log — bitácora estructurada

```bash
tramalia log
```

Lee exclusivamente `.tramalia/evidencia/*/metadatos.json`, ignora directorios
temporales y ordena los paquetes por ID descendente. Valida el esquema completo,
la coincidencia entre ID y directorio, tiempos, enums, comandos, hashes, archivos
de salida, excepciones y `vinculo_traspaso`.

Un paquete correcto aparece como entrada `valida`. Uno corrupto aparece como
`invalida` con un error seguro y no impide listar los demás. `log` nunca deduce
un resultado desde un Markdown histórico.

## evidence y handoff — evidencia y traspaso

Los nombres de comando siguen disponibles para no romper automatizaciones:

```bash
tramalia evidence TASK-001
tramalia handoff TASK-001
```

- `evidence` crea un paquete formal en `.tramalia/evidencia/<id_paquete>/`.
- `handoff` registra el concepto denominado **traspaso**. Su fuente canónica es
  el `traspaso.md` dentro del paquete.
- `docs/ai/07-traspaso-agentes.md` es sólo una proyección del traspaso más
  reciente, enlazada mediante una ruta relativa. Un fallo al proyectarla no
  modifica ni invalida el paquete.

## doctor

`tramalia doctor` agrupa requisitos por base, stack, contexto, memoria,
seguridad, base de datos, UX/UI, analítica, convención y agentes CLI. Distingue
`instalada`, `no instalada (opcional)` y `no instalada (requerida)`, e incluye
instrucciones según el sistema operativo.

`tramalia doctor --fix` construye un plan y permite seleccionar qué herramientas
automatizables instalar. Las manuales se muestran por separado.

## init y upgrade

`tramalia init` genera de forma idempotente `AGENTS.md`, `CLAUDE.md`, `docs/ai/`,
`specs/`, subagentes, skills, `mise.toml`, `.mcp.json` y `.tramalia/`. Con
`--adopt`, integra el bloque de gobierno en archivos existentes mediante
marcadores y conserva el contenido del usuario.

Después de actualizar el paquete:

```bash
pip install -U tramalia-cli
tramalia upgrade
```

`upgrade` agrega archivos nuevos que falten, refresca el bloque administrado de
`.gitignore` y registra la versión. No sobrescribe documentos ya personalizados.

## ui

`tramalia ui` abre cuatro vistas: **Resumen**, **Skills**, **Auditoría** y
**Cierre**. Auditoría muestra la bitácora formal y el contenido de
`metadatos.json`; Cierre llama al mismo núcleo y presenta su estado definitivo.
La TUI no mantiene una política paralela.

## agents

`tramalia agents list` muestra subagentes, modelos y tope actual.
`tramalia agents cap <fable|opus|sonnet|haiku|none>` fija un máximo portable; los
roles inferiores se conservan y `inherit` no se altera.

## context

- `tramalia context` o `tramalia context build`: genera `.tramalia/context/`.
- `tramalia context list`: compara backends compatibles.
- `tramalia context set <backend>`: guarda un único backend activo en la
  configuración del proyecto.

El contexto es memoria derivada y regenerable. No reemplaza la evidencia formal
ni participa en la decisión de cierre.

## sync, skills y update

- `sync` propaga `AGENTS.md` y formatos compatibles mediante `rulesync`.
- `skills` administra fuentes, versiones, activación y actualización de skills.
- `update` actualiza herramientas orquestadas y skills; no instala una versión
  nueva del paquete de PyPI ni publica documentación.

## mcp — fachada de nivel 1

`tramalia mcp` expone herramientas como `project_status`, `get_agent_rules`,
`get_failed_attempts`, `get_current_task`, `doctor`, `record_handoff`,
`build_evidence` y `build_context`:

```json
{
  "mcpServers": {
    "tramalia": {"command": "tramalia", "args": ["mcp"]}
  }
}
```

`record_handoff` conserva el nombre interoperable, pero registra un traspaso
canónico y proyecta `docs/ai/07-traspaso-agentes.md`.
