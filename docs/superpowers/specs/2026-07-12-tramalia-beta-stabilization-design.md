# Diseño de estabilización integral para la BETA de Tramalia

**Fecha:** 2026-07-12

**Estado:** Aprobado en conversación

**Rama de trabajo:** `codex/beta-stabilization`

## 1. Objetivo

Evolucionar Tramalia desde una BETA funcional pero parcialmente *fail-open* hacia
una base confiable, reproducible y mantenible para un piloto de equipo. La
estabilización debe proteger la promesa central del producto: un cierre aprobado
siempre corresponde a reglas ejecutadas, evidencia completa y un handoff
coherente, independientemente de si la operación se invoca desde CLI, TUI o MCP.

El trabajo también debe mejorar la arquitectura interna, la suite de pruebas, la
cadena de publicación, las integraciones, la TUI y la documentación de usuario y
de código.

## 2. Decisiones aprobadas

- Python 3.11 será la versión mínima de la BETA.
- La compatibilidad objetivo será Python 3.11, 3.12, 3.13 y 3.14.
- Se aplicará una estabilización estructural incremental; no una sucesión de
  parches aislados ni una reescritura total.
- CLI, TUI y MCP serán fachadas delgadas sobre una única capa de operaciones.
- Toda escritura nueva de evidencia usará Evidence Pack v2; los packs v1
  continuarán siendo legibles.
- Las integraciones opcionales no serán necesarias para usar el núcleo repo-first.
- Los comentarios internos se escribirán en español.
- Los docstrings de la API pública se escribirán en inglés y con estilo Google.
- Las guías explicativas alrededor de la API tendrán versiones española e inglesa.
- La referencia de código se generará con MkDocs Material y
  `mkdocstrings-python`, conservando el sistema visual actual.
- El éxito se medirá por contratos protegidos, no por mantener una cifra fija de
  tests.

## 3. Restricciones globales

- El núcleo debe seguir funcionando sin Node, servicios cloud ni herramientas
  externas.
- Las integraciones pueden degradar una capacidad opcional, pero nunca ocultar un
  intento fallido.
- No se incorporará una base de datos, event sourcing ni un framework de
  persistencia.
- No se romperá la lectura del historial de evidence packs v1.
- Las escrituras deben ser seguras en Windows, Linux y macOS.
- Los cambios de comportamiento se implementarán con TDD: test fallando,
  implementación mínima y refactor posterior.
- Las APIs públicas nuevas deben tener tipos, docstring y pruebas de contrato.
- Los comentarios deben explicar motivos, invariantes y riesgos; no repetir el
  código.

## 4. Arquitectura objetivo

### 4.1 Errores y modelos

`tramalia/core/errors.py` contendrá una jerarquía de errores de dominio con:

- `code`: identificador estable para automatización.
- `message`: descripción humana.
- `hint`: acción de recuperación.
- `path`: archivo relacionado, cuando corresponda.
- `details`: datos estructurados sin secretos.

`tramalia/core/models.py` contendrá modelos tipados para `ProjectState`,
`GateResult`, `GateRun`, `FailureOverride`, `CloseOutcome`, `IntegrationStatus` y
metadatos de Evidence v2.

Las superficies transformarán esos modelos a texto, widgets o respuestas MCP; no
recalcularán política.

### 4.2 Estado del proyecto

`inspect_project_state(root)` distinguirá:

- `ready`: convención y configuración válidas.
- `legacy`: proyecto Tramalia anterior que puede migrarse.
- `partial`: existen marcadores, pero faltan piezas obligatorias o son inválidas.
- `missing`: Tramalia no está inicializada.

`require_governed_project(root)` será la única guardia para operaciones mutantes.
La presencia aislada de `AGENTS.md` o de un directorio `.tramalia` vacío no será
suficiente.

### 4.3 Gates y política de cierre

`tramalia/core/gates.py` será responsable de cargar, validar y ejecutar gates.
Los errores de TOML no se convertirán en una lista vacía.

`GateRun.state` podrá ser:

- `passed`
- `failed`
- `runner_unavailable`
- `not_configured`
- `config_invalid`
- `execution_error`

`CloseOutcome.status` se limitará a:

- `passed`: existen gates aplicables, se ejecutaron y todos los controles pasaron.
- `passed_with_exceptions`: cada bloqueo sobreescribible tiene una excepción
  explícita y vigente.
- `blocked`: cualquier otro resultado.

`config_invalid`, un ID inseguro, un proyecto `partial` y un fallo de persistencia
no serán sobreescribibles. La ausencia del runner, la ausencia de gates, un gate
fallido o un umbral incumplido sólo podrán continuar con una excepción razonada.

### 4.4 Operaciones compartidas

`tramalia/core/operations.py` expondrá las únicas entradas mutantes:

- `close_project(...)`
- `create_evidence(...)`
- `record_handoff(...)`

Estas operaciones aplicarán la misma validación, política, persistencia y
telemetría local para CLI, TUI y MCP.

Flujo de cierre:

1. Inspeccionar y exigir un proyecto gobernado.
2. Validar tarea, configuración y excepción solicitada.
3. Descubrir y ejecutar gates.
4. Evaluar métricas y construir el resultado definitivo.
5. Construir Evidence v2 completo en staging.
6. Publicar el pack de forma atómica.
7. Actualizar la proyección global de handoff.
8. Devolver el mismo `CloseOutcome` a cualquier superficie.

## 5. Evidence Pack v2

### 5.1 Identidad y rutas

- `pack_id`: timestamp UTC con microsegundos más sufijo aleatorio corto.
- La ruta final siempre será nueva; nunca se reabrirá para sobrescribir un pack.
- `task_id` tendrá un máximo de 64 caracteres y sólo admitirá letras ASCII,
  números, punto, guion y guion bajo.
- Se rechazarán separadores, `..`, controles, saltos de línea y nombres reservados
  de Windows.
- Se verificará que toda ruta resuelta permanezca bajo `.tramalia/evidence`.

### 5.2 Escritura atómica

El writer construirá el pack en un directorio hermano `.tmp-<uuid>` dentro del
mismo filesystem. Sólo después de escribir y validar todos los archivos se
publicará mediante rename atómico. Un fallo intermedio no dejará un pack final
parcial ni modificará evidencia previa.

### 5.3 Contenido mínimo

`metadata.json` incluirá:

- `schema_version: 2`
- `pack_id`, tarea, operación y timestamps UTC
- versión de Tramalia, Python, sistema operativo y toolchain
- commit, branch, estado Git y base de comparación
- comandos exactos, duración, código de salida y hashes de outputs
- gates descubiertos, ejecutados, omitidos y fallidos
- métricas, umbrales y errores de validación
- excepciones, referencia, revisor y expiración
- archivos tracked, staged, untracked, renombrados y eliminados
- vínculo al handoff canónico

Las salidas crudas de cada gate permanecerán separadas. `lint` y `format` nunca
compartirán archivo.

### 5.4 Handoff y lectura histórica

El pack contendrá el handoff canónico con el resultado ya calculado. El archivo
global `docs/ai/07-handoff-agentes.md` será una proyección atómica que enlaza el
`pack_id`; un fallo de esa proyección no invalidará el handoff canónico.

`read_log()` leerá v2 de forma estructurada y conservará un lector explícito para
v1. Metadata corrupta aparecerá como `invalid`; no se reinterpretará
silenciosamente desde Markdown.

## 6. Excepciones y revisión

`FailureOverride` exigirá:

- razón no vacía
- riesgo aceptado
- gate o control afectado
- referencia a issue, ADR o ticket
- identidad del revisor
- expiración o condición de remediación

`--allow-fail` sin datos suficientes será rechazado antes de escribir evidencia.
Durante la migración podrá mantenerse como alias deprecado que exige los nuevos
campos. La identidad declarada quedará registrada, pero no se presentará como
prueba criptográfica de aprobación.

## 7. Contrato de integraciones

Toda integración devolverá `IntegrationStatus` con:

- `state`: `full`, `degraded`, `unavailable` o `failed`
- `capability`: capacidad solicitada
- `requested`: adaptador preferido
- `used`: adaptador efectivo
- `reason`: causa estable
- `impact`: limitación resultante
- `remediation`: acción sugerida

`degraded` sólo será éxito si un fallback terminó correctamente. `unavailable`
representará una capacidad opcional no solicitada o no instalada. `failed`
representará un intento fallido y propagará código de salida no cero.

Las skills Git conservarán `source`, `ref` y SHA resuelto. El modo Team no usará
ramas flotantes ni `latest`; una actualización explícita moverá el lock. El
runtime del paquete conservará rangos compatibles, mientras CI, docs y release
usarán entornos reproducibles.

## 8. TUI

La TUI dejará de concentrar presentación y orquestación en `build_app()`.

Primera separación:

- `DashboardService`: obtiene snapshots y ejecuta operaciones.
- `DashboardSnapshot`: datos inmutables para representar.
- Textual: widgets, navegación, bindings y mensajes.

Las sondas y procesos externos se ejecutarán fuera del event loop. La corrupción
de metadata, cancelación, timeout y estados degradados tendrán representación
explícita y pruebas mediante la API pública de `pilot`.

## 9. Comentarios y docstrings

### 9.1 Política de comentarios

Los comentarios internos estarán en español y se reservarán para:

- invariantes no evidentes
- decisiones de compatibilidad
- límites de seguridad
- razones de una degradación o fallback
- comportamiento específico de plataforma

No se añadirán comentarios que sólo traduzcan una sentencia de Python.

### 9.2 Política de docstrings

Los módulos y APIs públicas tendrán docstrings en inglés, estilo Google, con:

- resumen orientado al contrato
- `Args`, `Returns`, `Raises` y `Examples` cuando apliquen
- consecuencias y side effects
- estados o errores estables relevantes

Los docstrings no serán bilingües. Las explicaciones de arquitectura y uso se
mantendrán en páginas Markdown ES/EN.

## 10. Referencia visual del código

Se añadirá `mkdocstrings-python` sólo al entorno de documentación. La nueva
navegación será `Desarrollo / Development` y contendrá:

- visión arquitectónica
- guía para contribuir
- operaciones
- gates y modelos
- evidence y handoff
- proyecto y configuración
- integraciones
- CLI y MCP
- servicios TUI

La referencia generada usará las plantillas Material soportadas por
mkdocstrings. La primera implementación no reemplazará templates HTML; sólo
añadirá CSS mantenible sobre `.doc-object`, `.doc-heading`, `.doc-signature` y
`.doc-contents`.

La apariencia debe:

- heredar la cabecera, navegación, búsqueda y paleta actual
- funcionar en modos claro y oscuro
- mostrar firmas separadas con resaltado y scroll adaptable
- mostrar parámetros, retornos y excepciones como listas legibles
- ocultar miembros privados y código fuente completo por defecto
- usar badges discretos para tipos de símbolo
- evitar tablas anchas en móvil
- conservar foco visible y movimiento reducido

La configuración usará rutas explícitas desde `mkdocs.yml`, referencias cruzadas
y docstrings estilo Google. El build se verificará en español e inglés, aunque la
referencia generada comparta docstrings ingleses.

## 11. Arquitectura de pruebas

Los 250 tests actuales se migrarán desde archivos históricos por release hacia:

```text
tests/
  unit/
  contract/
  integration/
  ui/
  release/
```

Markers:

- `unit`: lógica pura y rápida
- `contract`: scaffold, schemas y superficies públicas
- `integration`: filesystem, Git, procesos y pipeline de cierre
- `ui`: flujos públicos de Textual
- `optional`: requiere extras TUI/MCP
- `release`: wheel, metadata y smoke tests

Se conservarán los comportamientos de regresión valiosos, pero se parametrizarán
matrices repetidas de stacks, sistemas, herramientas e instaladores. Se retirarán
duplicados, pruebas de constantes privadas, pruebas que sólo afirman “no lanza” y
comprobaciones de prosa que pertenecen al pipeline documental.

Los primeros tests nuevos cubrirán:

- mise ausente, presente sin gates y TOML inválido
- error de ejecución y estado `blocked`
- dos cierres en el mismo instante y cierres concurrentes
- traversal, nombres Windows y containment
- fallo inyectado durante la publicación atómica
- MCP sin init y ejecución real de tools
- Git pull/clone no cero, timeout y ref inválido
- tracked, staged, untracked, renames y deletes
- importación y smoke en Python 3.11–3.14
- release bloqueada si tests, versión o wheel fallan

## 12. CI, documentación y release

Jobs obligatorios:

1. `core`: unit y contract en Python 3.11–3.14.
2. `platform`: integración crítica en Windows, Linux y macOS.
3. `optional`: TUI y MCP con extras instalados.
4. `docs`: pares ES/EN, enlaces y `mkdocs build --strict`.
5. `package`: build sdist/wheel, `twine check`, instalación limpia y smoke CLI.

El workflow de publicación consumirá exactamente el artefacto del job `package`.
Sólo aceptará tags `v*` cuya versión coincida con metadata y changelog. Una
ejecución manual desde una rama no publicará.

Las GitHub Actions se fijarán por SHA con comentario de versión. Las dependencias
de desarrollo, docs y release tendrán resolución reproducible y actualización
deliberada.

## 13. Fuente documental única

- MkDocs será la fuente canónica extensa.
- README ES/EN será onboarding y enlazará a la documentación.
- El manual histórico se actualizará o se marcará explícitamente como archivado.
- Conteos de tests, comandos, extras y herramientas no se duplicarán manualmente.
- Tests de contrato compararán argparse, bindings TUI, extras del proyecto y
  tablas/documentos canónicos.
- La referencia de API se generará desde docstrings; no se copiarán firmas a mano.

## 14. Secuencia de implementación

1. Entorno reproducible, baseline y reorganización inicial de tests.
2. Python 3.11 mínimo, errores y modelos tipados.
3. Política fail-closed de gates y cierre.
4. Evidence v2, lectura dual y excepciones.
5. Operaciones compartidas y migración CLI/TUI/MCP.
6. Contrato de integraciones y locks reproducibles.
7. Separación de servicios TUI.
8. Mkdocstrings, docstrings, CSS y documentación ES/EN.
9. CI, package smoke y release condicionada.
10. Piloto medido de 10–20 cierres reales.

Cada etapa deberá producir software ejecutable y pruebas verdes antes de iniciar
la siguiente.

## 15. Criterios de aceptación BETA

- Ningún camino produce `passed` sin gates aplicables ejecutados.
- TOML inválido produce error tipado y exit no cero.
- CLI, TUI y MCP devuelven la misma política y códigos de error.
- Dos cierres simultáneos de una tarea producen packs distintos.
- Un fallo de escritura deja cero packs finales parciales.
- IDs inseguros no pueden escapar del directorio administrado.
- Evidence v2 registra cambios completos, comandos, entorno y hashes.
- Handoff y metadata coinciden en tarea, pack, resultado y excepción.
- Packs v1 permanecen visibles en el log.
- Fallos externos nunca se presentan como éxito o ausencia silenciosa.
- La suite se ejecuta en Python 3.11–3.14 y en los tres sistemas objetivo.
- El wheel validado por CI es el mismo artefacto publicado.
- La documentación strict compila en ES/EN.
- La referencia API mantiene legibilidad en claro, oscuro, escritorio y móvil.
- El piloto registra cero falsos `passed` y cero colisiones de evidencia.

## 16. Riesgos y mitigaciones

- **Cambio de semántica de `no_gates`:** documentar como breaking change BETA y
  ofrecer excepción razonada durante adopción.
- **Scripts existentes con `--allow-fail`:** mantener alias deprecado durante un
  ciclo y devolver guía de migración.
- **Repos parcialmente inicializados:** `inspect_project_state` ofrecerá diagnóstico
  y comando de reparación antes de bloquear.
- **Cambio de nombres de pack:** lectores internos usarán `pack_id` opaco; se
  documentará que los nombres no son API.
- **Atomicidad en Windows o filesystem de red:** pruebas por plataforma y error
  explícito cuando el filesystem no ofrezca la garantía requerida.
- **Volumen de refactor:** migración por contratos pequeños y compatibilidad de
  lectura, sin reescritura total.
- **Complejidad visual de la API:** CSS mínimo sobre Material; no mantener forks de
  templates mientras las clases estándar sean suficientes.

## 17. Fuera de alcance de esta estabilización

- Base de datos de auditoría.
- Servicio cloud de Tramalia.
- Firma criptográfica o attestation externa de evidence packs.
- Reescritura de la CLI o TUI en otro framework.
- Generación total de toda la documentación desde un catálogo único.
- Garantía de identidad criptográfica del revisor.

Estas capacidades podrán evaluarse después del piloto si los datos demuestran su
necesidad.
