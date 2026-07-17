# Diseno del Plan 05: recetas, auditoria y remediacion guiada

**Fecha:** 2026-07-16

**Estado:** aprobado; 05a cuenta con plan ejecutable y conserva su puerta de entrada

**Dependencias:** Plan 03a, Plan 03c, Plan 03b, Plan 04 y base estabilizada con
`v1.0.0b1` publicada

## 1. Objetivo

El Plan 05 convertira las combinaciones de herramientas instaladas en flujos
reproducibles, explicables y gobernados. La primera aplicacion de referencia sera
una evaluacion de seguridad basada en controles versionados, con hallazgos,
evidencia y remediacion seleccionada manualmente.

La remediacion forma parte del alcance desde la primera entrega. Toda modalidad
aplica `seleccion_humana_obligatoria`: el usuario elige de forma explicita que
hallazgos se van a tratar, revisa el plan y confirma su huella antes de cualquier
mutacion. La correccion puede realizarla el equipo, una transformacion
determinista propia o, en una fase posterior, un agente autorizado. Una
remediacion puede ejecutarse en la sesion actual, convertirse en trabajo para una
etapa posterior o quedar documentada como riesgo aceptado mediante la politica de
excepciones.

El Plan 05 se implementa despues de estabilizar y publicar la BETA. El diseno se
versiona antes para evitar que 03c, 03b o 04 introduzcan APIs provisionales o
pantallas sin motor real.

## 2. Vocabulario y limites de dominio

- **Puerta o gate:** comprobacion acotada que aprueba, bloquea o deja
  indeterminado un cierre. Una puerta no equivale a una auditoria completa.
- **Auditoria de cierres:** pista historica de evidence packs ya existente en
  Tramalia.
- **Auditoria de habilidades:** revision de procedencia, integridad, permisos y
  riesgos de habilidades prevista en el Plan 03c.
- **Evaluacion de seguridad:** aplicacion versionada de controles a un proyecto,
  con aplicabilidad, evidencia, hallazgos y limitaciones.
- **Remediacion:** trabajo aprobado para reducir o eliminar un hallazgo y volver a
  verificar el control afectado.
- **Receta:** grafo declarativo y versionado de capacidades, herramientas,
  precondiciones, pasos, limites, puertas y evidencia.

La documentacion y la interfaz pueden usar "Auditoria de seguridad" como nombre
comprensible, pero los modelos internos emplearan `evaluacion_seguridad` para no
confundirla con la bitacora de cierres ni con `auditoria_habilidades`.

## 3. Descomposicion del programa

El alcance es demasiado amplio para una sola implementacion monolitica. Se divide
en cuatro subplanes secuenciales, cada uno con su propio plan de implementacion,
pruebas y revision:

### 05a. Motor de recetas

Introduce modelos puros para catalogar, resolver, planificar, simular y ejecutar
recetas. Detecta capacidades disponibles a traves del inventario de herramientas
de Tramalia y produce un plan con huella antes de ejecutar.

### 05b. Evaluacion de seguridad como corte vertical

Define el esquema de catalogos de controles, perfiles de aplicabilidad,
ejecuciones, evidencia y hallazgos. Integra primero capacidades locales como
Semgrep, Gitleaks, pruebas, metadatos del repositorio y controles manuales. Incluye
CLI, una TUI minima para planificar, ejecutar y consultar hallazgos, y su
documentacion ES/EN; no entrega un motor sin superficie utilizable.

### 05c. Remediacion guiada como corte vertical

Permite seleccionar hallazgos, agruparlos, decidir entre ejecutar o diferir,
asignar una etapa objetivo, construir un plan de remediacion, aplicar solamente
acciones autorizadas y verificar el resultado. Incluye el ciclo completo en CLI y
TUI, junto con tutoriales y referencia. Conserva trazabilidad entre control,
hallazgo, cambio, puerta y evidencia.

### 05d. Consolidacion, interoperabilidad y documentacion final

Endurece accesibilidad y adaptabilidad de CLI/TUI, incorpora importacion y
exportacion saneadas, y expone un servidor MCP de auditoria separado y opcional.
Completa la documentacion transversal, arquitectura, seguridad, extensibilidad y
referencia API sin postergar la documentacion funcional de 05a, 05b o 05c.

El Plan 05 no reimplementa procesos, locks, confinamiento de rutas, evidence
packs, perfiles de habilidades ni coordinacion de operaciones. Consume los
contratos estables de 03a, 03c, 03b y 04.

## 4. Arquitectura

La arquitectura elegida es hibrida y separa politica, datos y superficies:

```text
Catalogos de controles y recetas declarativas
        |
        v
Resolver y planificador puros ----> simulacion + huella
        |                                  |
        |                           confirmacion explicita
        v                                  |
Ejecutor local acotado <-------------------+
        |
        +--> evidence pack de seguridad
        +--> hallazgos normalizados
        +--> candidatos de remediacion
                         |
                         v
               seleccion manual + plan
                         |
             +-----------+-----------+
             |           |           |
          manual   determinista   asistida
             |           |           |
             +-----------+-----------+
                         |
                         v
                 verificacion y cierre
```

### 4.1 Nucleo incluido en Tramalia

El repositorio principal contiene:

- modelos y validadores del esquema;
- motor generico de recetas;
- aplicabilidad y planificacion;
- ejecucion local acotada;
- hallazgos, planes de remediacion y evidencia;
- adaptadores CLI/TUI;
- adaptador MCP opcional;
- un catalogo generico saneado con controles propios y mapeos versionados.

### 4.2 Packs separados

Los catalogos corporativos, reglas internas, conectores empresariales y plantillas
de informe comerciales viven en packs privados versionados. Un pack contiene
datos declarativos; no puede ejecutar Python arbitrario ni aportar comandos de
shell libres.

Los libros V2.2 y V3.0 sirven como fuente de diseno e importacion. No se publican
ni se convierten literalmente hasta completar una auditoria de titularidad,
confidencialidad y licencias. El catalogo generico redacta sus propios controles y
referencia identificadores externos sin copiar de forma indiscriminada textos
protegidos.

## 5. Modelos de dominio

### 5.1 Catalogo y control

Cada catalogo declara al menos:

- identificador y version inmutables;
- licencia, origen, fecha de revision y hash;
- compatibilidad de esquema;
- perfiles o modulos que puede activar;
- firma o mecanismo de integridad cuando este disponible.

Cada control declara:

- `id_control`, revision, modulo y dominio;
- titulo y descripcion propios;
- prioridad y severidad orientativa;
- referencias versionadas;
- regla de aplicabilidad;
- comprobaciones automaticas disponibles;
- evidencia manual requerida;
- criterio de exito;
- limitaciones y riesgo residual;
- recetas de remediacion admitidas.

Los requisitos de OWASP ASVS se referencian como
`v<version>-<identificador>`. OWASP Top 10, API Security, Agentic Skills y MCP se
registran siempre con version o nivel de madurez. La herramienta no afirma
certificacion ni cumplimiento general.

### 5.2 Ejecucion y resultado de control

Una ejecucion fija:

- raiz gobernada e identidad Git inicial;
- perfil y modulos aplicables;
- versiones de catalogos, recetas y herramientas;
- plan y huella confirmada;
- limites de tiempo, salida, concurrencia y red;
- resultados y evidencia por control;
- identidad Git final y drift detectado.

Los estados de evaluacion son:

- `cumple`;
- `cumple_parcial`;
- `no_cumple`;
- `no_aplica`;
- `no_evaluable`;
- `error_ejecucion`.

Una herramienta ausente, un timeout o una salida indeterminada nunca se convierten
en `cumple`.

### 5.3 Hallazgo

El hallazgo conserva:

- identificador estable dentro de la ejecucion;
- control, evidencia y ubicaciones relacionadas;
- severidad, confianza e impacto;
- descripcion saneada;
- recomendacion y opciones de tratamiento;
- responsable y etapa objetivo cuando se asignen;
- estado de remediacion;
- historial de decisiones y verificaciones.

Los estados de remediacion del hallazgo son:

- `detectado`;
- `seleccionado`;
- `planificado`;
- `en_progreso`;
- `diferido`;
- `pendiente_verificacion`;
- `verificado`;
- `fallido`;
- `bloqueado`;
- `riesgo_aceptado`;
- `descartado`.

`descartado` exige una razon, por ejemplo falso positivo. `riesgo_aceptado`
consume la politica tipada de excepciones y nunca equivale a corregido. Las
acciones del plan usan una maquina separada: `pendiente`, `ejecutando`,
`aplicada`, `fallida`, `revertida` o `bloqueada`. El estado agregado del plan se
deriva de sus acciones y no oculta fallos bajo `en_progreso`.

### 5.4 Plan de remediacion

Un plan contiene solamente hallazgos seleccionados y especifica por accion:

- tipo de remediacion;
- archivos, configuraciones o procesos afectados;
- precondiciones;
- cambio propuesto o procedimiento manual;
- decision de ejecucion y etapa objetivo;
- responsable;
- dependencias y conflictos;
- puertas de verificacion;
- estrategia de rollback;
- riesgos y permisos;
- estimacion de tiempo y, si aplica, tokens;
- huella de confirmacion.

`decision_ejecucion` acepta `ejecutar_ahora` o `diferir`. `etapa_objetivo` acepta
`diseno`, `implementacion`, `pruebas`, `pre_lanzamiento` u `operacion`. Las
organizaciones pueden mostrar etiquetas propias, pero deben mapearlas a una etapa
base para conservar interoperabilidad.

## 6. Tipos de remediacion

### 6.1 Remediacion documentada por el equipo

Tramalia crea una tarea gobernada con pasos, evidencia requerida, etapa objetivo y
puertas de verificacion. El usuario o su equipo realiza el cambio. Es la opcion
obligatoria para decisiones de arquitectura, procesos, proveedores, politicas o
controles que no pueden probarse de forma segura con una edicion automatica.

### 6.2 Determinista

Una receta propia y confiable puede aplicar una transformacion acotada y
reversible. Antes de escribir, Tramalia muestra el diff o plan equivalente,
comprueba la huella, crea respaldo transaccional cuando corresponda y exige
confirmacion. Un pack externo no puede inyectar codigo ejecutable en esta ruta.

### 6.3 Asistida por agente

Tramalia genera una tarea estructurada con alcance, archivos permitidos, criterios
de aceptacion y puertas. El host o agente se invoca solamente por una accion
explicita, con presupuesto de tokens y permisos declarados. El resultado vuelve al
mismo flujo de verificacion; una respuesta textual del modelo no cierra el
hallazgo.

La primera entrega funcional soporta remediacion documentada por el equipo y un
conjunto pequeno de remediaciones deterministas propias. El esquema conserva los
campos necesarios para una modalidad asistida posterior, pero la ejecucion por
agente no forma parte de los criterios de aceptacion iniciales ni aparece como
fallback automatico.

## 7. Flujo de datos y operacion

1. El usuario elige una receta y un perfil.
2. Tramalia resuelve controles, herramientas y pasos sin red ni escritura.
3. La simulacion presenta alcance, exclusiones, tiempo estimado y huella.
4. El usuario confirma y se ejecutan solamente los pasos planificados.
5. Se genera un evidence pack con resultados, limitaciones y hallazgos.
6. El usuario filtra y selecciona hallazgos para remediar.
7. Tramalia propone acciones y etapas; el usuario puede ajustarlas.
8. Se crea un plan de remediacion con nueva huella.
9. El usuario elige `ejecutar_ahora` o `diferir` y asigna una etapa objetivo.
10. Una remediacion diferida entra en una cola persistente con responsable,
    precondiciones, fecha de revision y huella de su contexto original.
11. Al entrar en una etapa, Tramalia muestra los pendientes aplicables; el
    usuario puede reanudarlos, replanificarlos, volver a diferirlos o tratarlos.
12. Reanudar siempre comprueba drift de Git, catalogos, recetas y herramientas;
    cualquier cambio relevante invalida la huella y obliga a replanificar.
13. Cada accion ejecutada corre sus puertas de verificacion.
14. Un cambio aplicado pasa a `pendiente_verificacion`; solo una verificacion
    satisfactoria cambia el hallazgo a `verificado`.
15. El cierre conserva decisiones, excepciones, cambios y riesgo residual.

Si el repositorio, catalogo, receta o inventario de herramientas cambia entre
planificacion y ejecucion, la huella queda obsoleta y se exige volver a planificar.

## 8. Persistencia y evidencia

Cada ejecucion guarda un directorio confinado dentro del sistema de evidencia de
Tramalia con, como minimo:

- `manifiesto.json`;
- `aplicabilidad.json`;
- `resultados-controles.jsonl`;
- `hallazgos.jsonl`;
- `plan-remediacion.json`, cuando exista;
- `eventos-remediacion.jsonl`;
- `cola-remediaciones.json`, cuando existan acciones diferidas;
- `resumen.md`;
- salidas crudas acotadas y saneadas.

Los informes `informe.xlsx` e `informe.html` son proyecciones opcionales de los
modelos canonicos, no nuevas fuentes de verdad. La importacion XLSX solo acepta la
plantilla versionada de Tramalia, valida celdas y neutraliza formula injection. El
HTML es estatico, autocontenido y saneado. Los libros corporativos originales no
se leen como catalogos de ejecucion.

Catalogos y recetas son inmutables por version. Respuestas, justificaciones y
evidencia pertenecen a la ejecucion y nunca modifican el catalogo original. Las
actualizaciones preservan la posibilidad de reproducir auditorias anteriores.

Los secretos se redactan antes de entrar en JSON, Markdown, TUI o MCP. Para un
secreto se conserva tipo, hash estable acotado y ubicacion permitida, nunca su
valor.

## 9. CLI

La CLI usa nombres espanoles y salida textual/JSON producida desde los mismos
modelos. El catalogo inicial de comandos es:

- `tramalia recetas listar`;
- `tramalia recetas planificar <id>`;
- `tramalia recetas simular <id>`;
- `tramalia recetas ejecutar <id> --confirmar-huella <huella>`;
- `tramalia seguridad perfiles`;
- `tramalia seguridad planificar --perfil <id>`;
- `tramalia seguridad simular --plan <id>`;
- `tramalia seguridad ejecutar --plan <id> --confirmar-huella <huella>`;
- `tramalia seguridad auditar --plan <id> --confirmar-huella <huella>` como alias
  explicito de `ejecutar`;
- `tramalia seguridad hallazgos listar`;
- `tramalia seguridad hallazgos mostrar <id>`;
- `tramalia seguridad remediar seleccionar <id>...`;
- `tramalia seguridad remediar planificar --etapa <etapa>`;
- `tramalia seguridad remediar iniciar --plan <id>`;
- `tramalia seguridad remediar evidencia registrar --plan <id>`;
- `tramalia seguridad remediar lista-verificacion --plan <id>`;
- `tramalia seguridad remediar diferir --plan <id> --etapa <etapa>`;
- `tramalia seguridad remediar pendientes --etapa <etapa>`;
- `tramalia seguridad remediar reanudar --plan <id>`;
- `tramalia seguridad remediar descartar --hallazgo <id> --razon <texto>`;
- `tramalia seguridad remediar aceptar-riesgo --hallazgo <id> --excepcion <id>`;
- `tramalia seguridad remediar aplicar --plan <id> --confirmar-huella <huella>`;
- `tramalia seguridad remediar verificar --plan <id>`.

La seleccion admite IDs y filtros visibles, pero nunca interpreta la ausencia de
IDs como "todos". La salida JSON incluye version de esquema y errores tipados.

## 10. TUI

La TUI incorpora un area **Seguridad** distinta de la pestaña historica
**Auditoria**. Debe ser la superficie principal para seleccionar y gestionar
remediaciones.

El recorrido incluye:

1. perfil y alcance;
2. simulacion de la evaluacion;
3. progreso y cancelacion;
4. resumen por modulo y estado;
5. tabla paginada de hallazgos;
6. detalle con evidencia y limitaciones;
7. seleccion multiple explicita;
8. bandeja de remediacion;
9. decision de ejecutar o diferir, etapa objetivo y responsable;
10. vista previa del plan o diff;
11. confirmacion de huella;
12. progreso, rollback y verificacion;
13. cola de pendientes por etapa, reanudacion y replanificacion;
14. registro de evidencia para trabajo realizado fuera de Tramalia;
15. enlace al evidence pack.

La interfaz conserva foco visible, teclado completo, contraste, movimiento
reducido, reflow y equivalentes semanticos comprobables con Pilot. Acciones
destructivas o con red muestran impacto y requieren confirmacion. Un refresco no
pierde selecciones ni decisiones ya persistidas.

## 11. MCP opcional

La auditoria no se registra en el servidor MCP general. Usa un extra y punto de
entrada propios, por ejemplo `tramalia[auditoria]` y `tramalia mcp auditoria`, para
que sus esquemas no ocupen contexto cuando la capacidad no se necesita. `init`,
`setup` y `sync` nunca lo agregan automaticamente a la configuracion del host.
Habilitarlo o revocarlo exige una operacion explicita que muestra el diff de
configuracion. Los contratos comprueban que el listado del MCP general no contiene
estas herramientas y que, tras revocarlas, el proceso de auditoria no queda
registrado ni activo.

Las herramientas minimas son:

- `planificar_evaluacion_seguridad`;
- `ejecutar_evaluacion_seguridad`;
- `estado_evaluacion_seguridad`;
- `listar_hallazgos_seguridad`;
- `obtener_hallazgo_seguridad`;
- `planificar_remediacion_seguridad`;
- `aplicar_remediacion_seguridad`;
- `verificar_remediacion_seguridad`.

Planificar y consultar son operaciones puras o de lectura. Ejecutar y aplicar
requieren raiz fijada al iniciar el servidor, huella vigente, IDs seleccionados y
consentimiento explicito del anfitrion. Las respuestas MCP son paginadas y
acotadas; los datos crudos quedan en el evidence pack local.

El servidor no solicita sampling ni invoca otro modelo por defecto. Los campos
reservados para modalidad asistida no se exponen como operacion ejecutable hasta
que un subplan futuro defina `analisis_ia=true`, presupuesto de tokens, alcance y
confirmacion independiente.

## 12. Seguridad y manejo de errores

- Todo proceso usa argumentos estructurados, nunca shell libre.
- Cada paso declara timeout, limite de salida, concurrencia y politica de red.
- Offline es el valor por defecto.
- Las rutas se confinan y se rechazan escapes, symlinks o junctions inseguros.
- Catalogos, recetas, salidas y documentos se tratan como datos no confiables.
- Un pack invalido, no compatible o sin integridad falla antes de ejecutar.
- Un paso cancelado detiene sus descendientes y conserva evidencia parcial
  honesta.
- Una remediacion determinista publica de forma transaccional o revierte.
- Una accion fallida queda `fallida` o `bloqueada`, y un rollback exitoso queda
  `revertida`; el plan y el hallazgo nunca ocultan ese resultado como
  `en_progreso`, `diferido` o `verificado`.
- Las puertas de verificacion fallan cerrado ante timeout, herramienta ausente o
  resultado indeterminado.
- Los planes registran permisos, red, datos sensibles y presupuesto antes de la
  confirmacion.
- Logs, TUI, JSON y MCP aplican redaccion y limites de tamano.

## 13. Documentacion

La documentacion forma parte de cada subplan, no una tarea final separada. Se
mantiene MkDocs Material con navegacion, paleta y diagramas coherentes con el sitio
existente, y mkdocstrings para las APIs publicas.

Cada capacidad nueva debe actualizar simultaneamente:

- guia conceptual en espanol e ingles;
- tutorial de principio a fin;
- guia practica por tarea;
- referencia CLI, JSON, Python y MCP;
- glosario de puerta, control, hallazgo, auditoria y remediacion;
- modelo de amenazas y matriz de controles;
- guia para crear y versionar packs;
- politica de privacidad, redaccion y retencion;
- solucion de problemas y recuperacion;
- capturas o snapshots deterministas de CLI/TUI;
- changelog y notas de migracion.

Los ejemplos usan proyectos ficticios y datos saneados. Ninguna documentacion
expone nombres, endpoints, hallazgos o normativa interna de los libros fuente.

## 14. Pruebas y verificacion

Todo comportamiento nuevo sigue RED-GREEN-REFACTOR. No se fija una cantidad de
pruebas; se justifican por contrato y riesgo.

La cobertura incluye:

- modelos, esquemas y migraciones;
- resolucion y aplicabilidad deterministas;
- hashes, drift y replanificacion;
- procesos, timeouts, cancelacion y limites;
- packs maliciosos, traversal y contenido no confiable;
- redaccion de secretos y salida acotada;
- controles documentados por el equipo, no aplicables e indeterminados;
- seleccion, conflictos, cola, reanudacion y etapas de remediacion;
- rollback y verificacion posterior;
- importacion XLSX validada, neutralizacion de formulas y exportacion XLSX/HTML;
- paridad CLI, TUI, JSON, Python y MCP;
- TUI con Pilot, teclado, foco, reflow y snapshots semanticos;
- documentacion estricta, enlaces, ejemplos y mkdocstrings;
- wheel/sdist con catalogos, licencias y entry points correctos;
- ejecuciones E2E sobre repositorios de ejemplo sin secretos reales.

## 15. Licencias y modelo comercial

El motor sigue el corte de licencia definido en el Plan 04: codigo nuevo del
motor y superficies bajo PolyForm Noncommercial con licencia comercial
alternativa; plantillas reutilizables claramente separadas bajo Apache-2.0.

El pack generico incluido declara sus fuentes, atribuciones y licencia por
archivo. ASVS y otros materiales CC se usan mediante referencias versionadas y
contenido propio o se aislan con las obligaciones correspondientes. El OWASP MCP
Top 10, que declara condiciones no comerciales, no se copia en un pack comercial;
solo se mapean identificadores y riesgos factuales despues de revision legal.

Los packs corporativos, conectores, informes avanzados y servicio alojado pueden
distribuirse de forma privada y comercial. Antes de derivar un pack de los Excel
se exige evidencia de titularidad y autorizacion de uso.

## 16. Secuencia de entrega

1. Completar 03a y sus correcciones de seguridad.
2. Implementar 03c para obtener catalogo, perfiles y activacion de habilidades.
3. Implementar 03b para obtener coordinacion y TUI adaptable.
4. Ejecutar 04, sanear el repositorio, aplicar licencias, documentar y publicar
   `v1.0.0b1`.
5. Implementar y revisar 05a.
6. Implementar y revisar 05b.
7. Implementar y revisar 05c.
8. Implementar y revisar 05d.
9. Publicar una BETA posterior del Plan 05 solamente cuando paquetes, documentos,
   CLI, TUI y MCP reproduzcan el mismo contrato.

La puerta de entrada a 05a exige que 03a, 03c, 03b y 04 esten cerrados; la suite
aprobada en las versiones de Python y sistemas soportados; wheel, sdist y
documentacion reproducibles; auditoria de titularidad y licencias resuelta; y
`v1.0.0b1` publicada sin bloqueantes abiertos. Una BETA publicada constituye la
base estabilizada de entrada, no una declaracion de estabilidad SemVer final.

## 17. Criterios de aceptacion

### 17.1 Aceptacion de 05a

- Ninguna receta se ejecuta por inferencia o por activar una habilidad.
- Listar y planificar son operaciones puras, sin red ni escritura.
- El usuario puede simular alcance, permisos, limites y coste antes de ejecutar.
- Toda ejecucion mutable exige una huella vigente y detecta drift.
- El motor produce evidencia reproducible y dispone de CLI y documentacion
  minimas desde su primer corte vertical.

### 17.2 Aceptacion de 05b

- Catalogos, perfiles, controles, ejecuciones y hallazgos tienen esquema
  versionado.
- Aplicabilidad, controles automaticos, documentados por el equipo y no
  evaluables se muestran honestamente.
- Semgrep, Gitleaks y las primeras capacidades locales producen evidencia
  acotada sin afirmar cobertura total.
- CLI y TUI permiten planificar, simular, ejecutar y consultar una evaluacion.
- La documentacion ES/EN explica perfil, control, hallazgo, limitacion y evidencia.

### 17.3 Aceptacion de 05c

- Solo se remedian hallazgos seleccionados explicitamente.
- `decision_ejecucion` y `etapa_objetivo` son dimensiones separadas.
- La cola persistente permite diferir, listar, reanudar y replanificar con control
  de drift.
- La remediacion documentada por el equipo y la determinista comparten
  trazabilidad, evidencia y puertas de verificacion.
- El esquema es compatible con una modalidad asistida futura, pero no la presenta
  como ejecutable ni la usa como fallback.
- Acciones y planes exponen estados fallidos, bloqueados, revertidos y pendientes
  de verificacion sin maquillarlos.
- Ningun hallazgo se marca `verificado` por una respuesta textual o por aplicar un
  cambio sin ejecutar sus puertas.
- CLI y TUI permiten seleccionar, planificar, aplicar o registrar trabajo externo,
  diferir, reanudar, aceptar riesgo, descartar y verificar.

### 17.4 Aceptacion de 05d

- La TUI es navegable por teclado, adaptable y recuperable tras cancelaciones.
- El MCP de auditoria usa extra y registro separados, permanece ausente por
  defecto y puede habilitarse o revocarse mediante un diff explicito.
- Importar XLSX valida plantilla y neutraliza formulas; XLSX y HTML exportados son
  proyecciones saneadas del modelo canonico.
- CLI, TUI, JSON, Python, MCP e informes conservan el mismo contrato.
- La documentacion completa conceptos, tutoriales, tareas, referencia,
  extensibilidad, seguridad, privacidad, recuperacion y migracion.

### 17.5 Puerta global de la siguiente BETA

- La ejecucion local determinista no consume tokens de IA.
- Catalogos, planes, hallazgos y evidencia son versionados y reproducibles.
- Wheel, sdist, documentacion, ejemplos, CLI, TUI y MCP pasan sus puertas
  reproducibles.
- Ningun activo publico contiene informacion corporativa de los Excel fuente.
- Ninguna salida afirma certificacion OWASP o ausencia total de vulnerabilidades.

## 18. Fuera de alcance inicial

- Remediacion autonoma sin seleccion ni confirmacion humana.
- Ejecucion de codigo aportado por packs de terceros.
- Certificacion formal OWASP, ASVS, ISO, NIST, CSA o normativa corporativa.
- Servicio cloud multi-tenant dentro del repositorio principal.
- Marketplace remoto de packs.
- Firma criptografica universal de terceros sin infraestructura de confianza.
- Soporte de todos los scanners existentes en la primera entrega.
