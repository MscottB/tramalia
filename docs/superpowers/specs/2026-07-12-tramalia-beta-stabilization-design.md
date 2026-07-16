# Diseño de estabilización integral para la BETA de Tramalia

**Fecha:** 2026-07-12

**Estado:** Aprobado en conversación

**Rama de trabajo:** `codex/beta-stabilization`

> **Ampliacion vigente (2026-07-16):** el sistema de habilidades gobernadas,
> los activos visuales, el relanzamiento en el repositorio existente, el corte
> de licencia y la version objetivo `1.0.0b1` se definen en
> [`2026-07-16-habilidades-relanzamiento-v1-diseno.md`](2026-07-16-habilidades-relanzamiento-v1-diseno.md).
> Esa ampliacion reemplaza cualquier instruccion posterior que proponga borrar
> los tres PNG maestros o publicar `0.34.0b1`.

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
- La implementación actual de evidencia se reemplazará directamente por el primer
  esquema formal del paquete de evidencia, `version_esquema: 1`. No existen
  proyectos consumidores que requieran compatibilidad con el formato previo sin
  versión.
- Las integraciones opcionales no serán necesarias para usar el núcleo repo-first.
- No se usará Figma; la mejora visual se implementará y probará directamente en la TUI y en MkDocs Material.
- Los comentarios internos se escribirán en español.
- Los docstrings de la API pública se escribirán en inglés y con estilo Google.
- Los nombres propios creados o refactorizados en archivos, módulos, clases,
  funciones, métodos, variables, funciones auxiliares de pytest y marcadores se escribirán en español
  ASCII. La letra `ñ` se representará como `n`.
- Se conservarán en inglés únicamente nombres impuestos por Python, GitHub,
  PyPI, MkDocs, MCP, formatos externos o comandos públicos ya establecidos.
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
- No se implementará un lector de compatibilidad para el formato de evidencia
  previo porque no tiene consumidores externos.
- Las escrituras deben ser seguras en Windows, Linux y macOS.
- Los cambios de comportamiento se implementarán con TDD: test fallando,
  implementación mínima y refactor posterior.
- Las APIs públicas nuevas deben tener tipos, docstring y pruebas de contrato.
- Los comentarios deben explicar motivos, invariantes y riesgos; no repetir el
  código.

## 4. Arquitectura objetivo

### 4.1 Errores y modelos

`tramalia/core/errores.py` contendrá una jerarquía de errores de dominio con:

- `codigo`: identificador estable para automatización.
- `mensaje`: descripción humana.
- `sugerencia`: acción de recuperación.
- `ruta`: archivo relacionado, cuando corresponda.
- `detalles`: datos estructurados sin secretos.

`tramalia/core/modelos.py` contendrá modelos tipados para `EstadoProyecto`,
`ResultadoPuerta`, `EjecucionPuertas`, `ExcepcionFallo`, `ResultadoCierre`,
`EstadoIntegracion` y metadatos del paquete de evidencia formal.

Las superficies transformarán esos modelos a texto, widgets o respuestas MCP; no
recalcularán política.

### 4.2 Estado del proyecto

`inspeccionar_estado_proyecto(raiz)` distinguirá:

- `listo`: convención y configuración válidas.
- `heredado`: proyecto Tramalia anterior que puede migrarse.
- `parcial`: existen marcadores, pero faltan piezas obligatorias o son inválidas.
- `ausente`: Tramalia no está inicializada.

`exigir_proyecto_gobernado(raiz)` será la única guardia para operaciones mutantes.
La presencia aislada de `AGENTS.md` o de un directorio `.tramalia` vacío no será
suficiente.

### 4.3 Puertas de calidad y política de cierre

`tramalia/core/puertas_calidad.py` será responsable de cargar, validar y ejecutar
puertas de calidad (*gates*). Los errores de TOML no se convertirán en una lista
vacía.

`EjecucionPuertas.estado` podrá ser:

- `aprobado`
- `fallido`
- `ejecutor_no_disponible`
- `sin_configurar`
- `configuracion_invalida`
- `error_ejecucion`

`ResultadoCierre.estado` se limitará a:

- `aprobado`: existen gates aplicables, se ejecutaron y todos los controles pasaron.
- `aprobado_con_excepciones`: cada bloqueo sobreescribible tiene una excepción
  explícita y vigente.
- `bloqueado`: cualquier otro resultado.

`configuracion_invalida`, un ID inseguro, un proyecto `parcial` y un fallo de
persistencia no serán sobreescribibles. La ausencia del ejecutor, la ausencia de
puertas, una puerta fallida o un umbral incumplido sólo podrán continuar con una
excepción razonada.

### 4.4 Operaciones compartidas

`tramalia/core/operaciones.py` expondrá las únicas entradas mutantes:

- `cerrar_proyecto(...)`
- `crear_evidencia(...)`
- `registrar_traspaso(...)`

Estas operaciones aplicarán la misma validación, política, persistencia y
telemetría local para CLI, TUI y MCP.

Flujo de cierre:

1. Inspeccionar y exigir un proyecto gobernado.
2. Validar tarea, configuración y excepción solicitada.
3. Descubrir y ejecutar gates.
4. Evaluar métricas y construir el resultado definitivo.
5. Construir el paquete de evidencia completo en staging.
6. Publicar el pack de forma atómica.
7. Actualizar la proyección global de handoff.
8. Devolver el mismo `ResultadoCierre` a cualquier superficie.

## 5. Paquete de evidencia formal v1

### 5.1 Identidad y rutas

- `id_paquete`: timestamp UTC con microsegundos más sufijo aleatorio corto.
- La ruta final siempre será nueva; nunca se reabrirá para sobrescribir un pack.
- `id_tarea` tendrá un máximo de 64 caracteres y sólo admitirá letras ASCII,
  números, punto, guion y guion bajo.
- Se rechazarán separadores, `..`, controles, saltos de línea y nombres reservados
  de Windows.
- Se verificará que toda ruta resuelta permanezca bajo `.tramalia/evidencia`.

### 5.2 Escritura atómica

El writer construirá el pack en un directorio hermano `.tmp-<uuid>` dentro del
mismo filesystem. Sólo después de escribir y validar todos los archivos se
publicará mediante rename atómico. Un fallo intermedio no dejará un pack final
parcial ni modificará evidencia previa.

### 5.3 Contenido mínimo

`metadatos.json` incluirá claves en español ASCII:

- `version_esquema: 1`
- `id_paquete`, `id_tarea`, operación y marcas de tiempo UTC
- versión de Tramalia, Python, sistema operativo y cadena de herramientas
- commit, rama, estado Git y base de comparación
- comandos exactos, duración, código de salida y hashes de salidas
- puertas descubiertas, ejecutadas, omitidas y fallidas
- métricas, umbrales y errores de validación
- excepciones, referencia, revisor y expiración
- archivos rastreados, preparados en el índice, no rastreados, renombrados y eliminados
- vínculo al handoff canónico

Las salidas crudas de cada gate permanecerán separadas. `lint` y `format` nunca
compartirán archivo.

### 5.4 Traspaso y lectura estructurada

El paquete contendrá el traspaso (*handoff*) canónico con el resultado ya calculado.
El archivo global `docs/ai/07-traspaso-agentes.md` será una proyección atómica que
enlaza el `id_paquete`; un fallo de esa proyección no invalidará el traspaso
canónico.

`leer_bitacora()` leerá el esquema formal de forma estructurada. Metadata corrupta
aparecerá como `invalida`; no se reinterpretará silenciosamente desde Markdown.

## 6. Excepciones y revisión

`ExcepcionFallo` exigirá:

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

Toda integración devolverá `EstadoIntegracion` con:

- `estado`: `completo`, `degradado`, `no_disponible` o `fallido`
- `capacidad`: capacidad solicitada
- `solicitado`: adaptador preferido
- `utilizado`: adaptador efectivo
- `motivo`: causa estable
- `impacto`: limitación resultante
- `remediacion`: acción sugerida

`degradado` sólo será éxito si una alternativa (*fallback*) terminó correctamente.
`no_disponible` representará una capacidad opcional no solicitada o no instalada.
`fallido`
representará un intento fallido y propagará código de salida no cero.

Las skills Git conservarán `fuente`, `referencia` y `sha_resuelto`. El modo Team
no usará ramas flotantes ni `latest`; una actualización explícita moverá el lock.
Las dependencias de ejecución del paquete conservarán rangos compatibles, mientras CI, docs y release
usarán entornos reproducibles.

## 8. TUI

La TUI dejará de concentrar presentación y orquestación en `build_app()`.

Primera separación:

- `ServicioTablero`: obtiene instantáneas y ejecuta operaciones.
- `InstantaneaTablero`: datos inmutables para representar.
- Textual: widgets, navegación, bindings y mensajes.

Las sondas y procesos externos se ejecutarán fuera del event loop. La corrupción
de metadatos, cancelación, tiempo agotado y estados degradados tendrán representación
explícita y pruebas mediante la API pública de `pilot`.

## 9. Comentarios y docstrings

### 9.1 Convención de nombres

El código propio creado o refactorizado usará español ASCII y `snake_case` para
módulos, archivos, funciones, métodos, variables y auxiliares de pytest; las clases usarán
`PascalCase` en español ASCII. Ejemplos: `puertas_calidad.py`, `cargar_configuracion`,
`resultado_cierre`, `EstadoIntegracion` y `proyecto_inicializado`.

La `ñ` se escribirá como `n`: `tamano`, `contrasena` y `companero`. No se usarán
traducciones forzadas para nombres exigidos por librerías o protocolos, como
`METADATA`, `pyproject.toml`, `workflow_dispatch`, `MCP` o métodos especiales
de Python.

### 9.2 Política de comentarios

Los comentarios internos estarán en español y se reservarán para:

- invariantes no evidentes
- decisiones de compatibilidad
- límites de seguridad
- razones de una degradación o fallback
- comportamiento específico de plataforma

No se añadirán comentarios que sólo traduzcan una sentencia de Python.

### 9.3 Política de docstrings

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

### 10.1 Documentación conceptual en español

La navegación añadirá una página `Conceptos básicos` antes de la referencia
técnica. Explicará con lenguaje directo y ejemplos:

- **Puerta de calidad (gate):** comprobación automática que debe aprobar antes de
  cerrar una tarea, por ejemplo tests, lint o seguridad.
- **Paquete de evidencia (evidence pack):** carpeta inmutable que conserva qué se
  ejecutó, sus salidas y el resultado.
- **Traspaso (handoff):** resumen que permite a otra persona o agente continuar.
- **Ejecutor (runner):** programa que lanza las puertas configuradas.
- **Alternativa (fallback):** vía secundaria usada cuando una integración opcional
  no está disponible.
- **Degradación:** resultado válido pero con menor capacidad, siempre explicado.
- **Lock o resolución fija:** versión o commit exacto que permite reproducir una
  integración.

Toda sigla o término técnico se explicará en español en su primera aparición y
enlazará al glosario. La versión inglesa mantendrá el término internacional y una
definición equivalente.

## 11. Arquitectura de pruebas

Los 250 tests actuales se migrarán desde archivos históricos por release hacia:

```text
tests/
  unidad/
  contratos/
  integracion/
  interfaz/
  publicacion/
```

Markers:

- `unidad`: lógica pura y rápida
- `contrato`: scaffold, esquemas y superficies públicas
- `integracion`: filesystem, Git, procesos y pipeline de cierre
- `interfaz`: flujos públicos de Textual
- `opcional`: requiere extras TUI/MCP
- `publicacion`: wheel, metadata y smoke tests

Se conservarán los comportamientos de regresión valiosos, pero se parametrizarán
matrices repetidas de tecnologías, sistemas, herramientas e instaladores. Se retirarán
duplicados, pruebas de constantes privadas, pruebas que sólo afirman “no lanza” y
comprobaciones de prosa que pertenecen al pipeline documental.

Los primeros tests nuevos cubrirán:

- mise ausente, presente sin gates y TOML inválido
- error de ejecución y estado `bloqueado`
- dos cierres en el mismo instante y cierres concurrentes
- traversal, nombres Windows y containment
- fallo inyectado durante la publicación atómica
- MCP sin init y ejecución real de tools
- Git pull/clone no cero, tiempo agotado y referencia inválida
- archivos rastreados, preparados, no rastreados, renombrados y eliminados
- importación y smoke en Python 3.11–3.14
- release bloqueada si tests, versión o wheel fallan

## 12. CI, documentación, GitHub Release y PyPI

Los despliegues serán responsabilidades independientes. Compartirán validaciones y
artefactos, pero un despliegue de documentación no publicará un paquete y una
publicación PyPI no redeplegará GitHub Pages.

Workflows:

1. `validacion.yml`: PR y push; ejecuta pruebas, contratos, plataformas y paquete.
2. `documentacion.yml`: después de una `validacion` exitosa en `main`, reconstruye
   desde el SHA validado y despliega GitHub Pages con permisos sólo en el job final.
3. `documentacion-sin-conexion.yml`: genera el ZIP navegable y lo conserva como
   artefacto o asset de lanzamiento.
4. `lanzamiento-github.yml`: valida tag, versión y changelog; toma wheel, sdist,
   hashes y documentación sin conexión ya validados; atestigua procedencia y crea
   siempre un borrador de GitHub Release con notas y assets.
5. `publicar-pypi.yml`: se activa al publicar GitHub Release, descarga exactamente
   los wheel/sdist del release, verifica hashes y publica mediante Trusted
   Publishing. La verificación corre sin OIDC; el job OIDC no ejecuta código del
   repositorio. Nunca reconstruye el paquete.

Jobs obligatorios de `validacion.yml`:

1. `nucleo`: unidad y contratos en Python 3.11–3.14.
2. `calidad`: Ruff, formato y tipado estático.
3. `plataformas`: integración crítica en Windows, Linux y macOS.
4. `opcionales`: TUI y MCP con extras instalados.
5. `documentacion`: pares ES/EN, enlaces y `mkdocs build --strict`.
6. `paquete`: build reproducible sdist/wheel, `twine check`, instalación limpia y smoke CLI.

El flujo de lanzamiento y el de PyPI consumirán exactamente el artefacto del job
`paquete`. Sólo aceptarán tags `v*` cuya versión coincida con metadata interna de
wheel/sdist, `tramalia.__version__` y changelog. Tanto un tag como una ejecución
manual seleccionada sobre ese mismo tag existente crearán sólo un borrador; una persona lo revisará y publicará. Ese evento
humano activa PyPI y evita depender de eventos recursivos del `GITHUB_TOKEN`.

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
4. Paquete de evidencia formal v1 y excepciones.
5. Operaciones compartidas y migración CLI/TUI/MCP.
6. Contrato de integraciones y locks reproducibles.
7. Separación de servicios TUI.
8. Mkdocstrings, docstrings, CSS y documentación ES/EN.
9. CI, package smoke y release condicionada.
10. Piloto medido de 10–20 cierres reales.

Cada etapa deberá producir software ejecutable y pruebas verdes antes de iniciar
la siguiente.

## 15. Criterios de aceptación BETA

- Ningún camino produce `aprobado` sin puertas aplicables ejecutadas.
- TOML inválido produce error tipado y exit no cero.
- CLI, TUI y MCP devuelven la misma política y códigos de error.
- Dos cierres simultáneos de una tarea producen packs distintos.
- Un fallo de escritura deja cero packs finales parciales.
- IDs inseguros no pueden escapar del directorio administrado.
- El paquete de evidencia formal registra cambios completos, comandos, entorno y
  hashes.
- Traspaso y metadatos coinciden en tarea, paquete, resultado y excepción.
- Fallos externos nunca se presentan como éxito o ausencia silenciosa.
- La suite se ejecuta en Python 3.11–3.14 y en los tres sistemas objetivo.
- El wheel validado por CI es el mismo artefacto publicado.
- La documentación strict compila en ES/EN.
- La referencia API mantiene legibilidad en claro, oscuro, escritorio y móvil.
- Los identificadores nuevos propios del proyecto usan español ASCII y la
  convención queda protegida por revisión y tests de contrato.
- La documentación ES/EN explica puerta de calidad, paquete de evidencia,
  traspaso, ejecutor, alternativa, degradación y lock sin asumir conocimiento
  previo.
- GitHub Pages, GitHub Release y PyPI se despliegan mediante workflows separados.
- PyPI publica exactamente los assets validados y adjuntos al GitHub Release.
- El piloto registra cero falsos `aprobado` y cero colisiones de evidencia.

## 16. Riesgos y mitigaciones

- **Cambio de semántica de `no_gates`:** documentar como breaking change BETA y
  ofrecer excepción razonada durante adopción.
- **Scripts existentes con `--allow-fail`:** mantener alias deprecado durante un
  ciclo y devolver guía de migración.
- **Repos parcialmente inicializados:** `inspeccionar_estado_proyecto` ofrecerá
  diagnóstico y comando de reparación antes de bloquear.
- **Reemplazo del formato de evidencia actual:** al no existir consumidores, se
  elimina la compatibilidad heredada y se publica el primer esquema formal con una
  migración simple para el propio repositorio de Tramalia.
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
