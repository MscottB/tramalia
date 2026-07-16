# Modelo de amenazas de Tramalia

Este documento fija los activos, actores, fronteras e invariantes que orientan los
controles de seguridad de la beta. Describe condiciones que deben demostrarse con
pruebas concretas; la implementación y el estado de cada control se registran en la
[matriz de controles](matriz-controles.md).

## Activos protegidos

- **Código y plantillas:** fuentes que Tramalia ejecuta, copia o publica, incluidas las
  plantillas que modifican proyectos consumidores.
- **Manifiestos y locks:** declaraciones de dependencias, habilidades, herramientas y
  versiones que determinan qué contenido se incorpora o ejecuta.
- **Evidencia cruda:** stdout, stderr, resultados de puertas, metadatos y trazas que
  sustentan decisiones de cierre sin ser sustituidos por resúmenes.
- **Credenciales del entorno:** tokens, claves, cookies, variables y archivos de
  autenticación disponibles en estaciones locales o runners.
- **Configuración MCP:** servidores, herramientas, nombres, argumentos, permisos y
  contexto que Tramalia expone a clientes MCP.
- **Historial Git:** commits, referencias, objetos y árbol de trabajo, incluidos
  secretos borrados de la revisión visible pero aún recuperables del historial.
- **Artefactos de release:** distribuciones, documentación, metadatos y procedencia
  que se entregan como una versión pública de Tramalia.

## Actores y capacidades

| Actor | Capacidades relevantes | Suposición inicial |
|---|---|---|
| Autor del proyecto | Edita configuración, fuentes, plantillas y excepciones; ejecuta puertas locales. | Puede equivocarse o introducir datos no confiables sin intención. |
| Colaborador de PR | Propone código, workflows, dependencias, enlaces, pruebas y archivos con nombres controlados. | El contenido del PR no es confiable hasta superar revisión y puertas. |
| Repositorio Git remoto | Entrega objetos, ramas, tags, submódulos y cambios posteriores bajo una referencia conocida. | Puede estar comprometido, cambiar o contener rutas y contenido hostiles. |
| Autor de habilidad | Define instrucciones, scripts, dependencias, permisos y actualizaciones de una habilidad. | Puede ser desconocido, malicioso o sufrir compromiso posterior. |
| Servidor MCP/proceso externo | Recibe argumentos y devuelve datos, errores, volumen y tiempos bajo su control. | Su salida es no confiable y puede incluir secretos, instrucciones o datos excesivos. |
| Dependencia de build | Ejecuta código durante resolución, instalación, construcción o publicación. | Su origen o cadena de distribución puede ser alterado. |

Un mismo participante puede ocupar más de un rol. La identidad conocida de un actor
no convierte automáticamente sus entradas o salidas en confiables.

## Fronteras de confianza

1. **Entrada de repositorio a parser/configuración.** Nombres, rutas y contenido del
   árbol entran a parsers y modelos internos. Antes de leer o escribir se exige esquema,
   tipo, normalización y confinamiento bajo una raíz permitida.
2. **Git remoto a cuarentena de habilidad.** Clones, referencias y objetos remotos se
   reciben en un área no activa. La procedencia declarada no habilita ejecución ni
   visibilidad automática.
3. **Cuarentena validada a directorio activo.** Sólo se promueve una habilidad tras
   validar estructura, referencia fijada, integridad, permisos, nombres y ausencia de
   colisiones; la promoción debe ser atómica.
4. **MCP/proceso a salida pública.** Stdout, stderr, respuestas MCP y contexto externo
   cruzan hacia CLI, TUI, logs o artefactos. Deben acotarse, etiquetarse como datos no
   confiables y filtrarse antes de hacerse públicos.
5. **Código de PR a runner de GitHub Actions.** El runner evalúa código y workflows de
   una contribución no confiable. Los jobs deben operar con permisos mínimos, acciones
   fijadas y sin secretos disponibles para código del PR.
6. **Herramienta descargada a ejecución local.** Un binario, paquete o script externo
   pasa de la red al host del autor. La versión, procedencia e integridad se verifican
   antes de otorgarle capacidad de ejecución.
7. **Árbol fuente a documentación/artefacto publicado.** El build transforma fuentes
   en material distribuible. La publicación debe corresponder a un árbol revisado,
   reproducible y enlazado con su evidencia, sin incorporar residuos locales.

## Invariantes verificables

- Toda ruta controlada por una entrada se resuelve antes del acceso; su destino real y
  cualquier symlink permanecen dentro de la raíz autorizada, o la operación se rechaza.
- Todo proceso automatizado recibe ejecutable y argumentos estructurados, nunca una
  cadena de shell; además tiene timeout y límites explícitos para stdout y stderr.
- Un remoto o una habilidad recién descargada permanece en cuarentena hasta validar
  referencia, contenido, permisos e identidad local sin colisiones.
- El árbol de trabajo y todo el historial Git alcanzable se examinan en busca de
  secretos; un fallo, timeout o resultado indeterminado no se interpreta como éxito.
- Herramientas, acciones y artefactos externos se fijan a una versión o identidad
  inmutable y se verifica su integridad antes de ejecutarlos o publicarlos.
- Los servidores y herramientas MCP tienen nombres únicos, alcance mínimo y salida
  acotada; credenciales y contexto privado no pasan a una superficie pública.
- Las puertas locales y de CI son reproducibles y cierran con bloqueo ante dependencia
  ausente, error de ejecución, timeout o evidencia incompleta.
- El código de un PR se ejecuta con privilegio mínimo y sin secretos; una publicación
  sólo parte de un árbol revisado y conserva vínculo con la evidencia que la autorizó.
- Ningún control cambia a `cubierto_por_prueba` sin enlazar la prueba exacta que demuestra
  el invariante y mantener explícita cualquier limitación residual.

## Casos de abuso

| Caso | Recorrido de ataque | Resultado que debe impedirse | Controles |
|---|---|---|---|
| Escape de ruta | Un manifiesto aporta `../`, una ruta absoluta o un symlink que sale de la raíz. | Lectura, sobrescritura o publicación de archivos ajenos al proyecto. | `TRM-SEC-001` |
| Habilidad remota hostil | Un remoto presenta scripts o instrucciones maliciosas, o cambia después de la primera revisión. | Activación o ejecución antes de validar y fijar el contenido. | `TRM-SEC-004`, `TRM-SEC-005`, `TRM-SEC-007` |
| Inyección de comandos | Una ruta, nombre o salida externa introduce metacaracteres en una orden construida como texto. | Ejecución de una orden distinta de la operación permitida. | `TRM-SEC-002` |
| Agotamiento por proceso | Un servidor o herramienta no termina o produce salida ilimitada. | Bloqueo del flujo, consumo descontrolado o contaminación de evidencia. | `TRM-SEC-002`, `TRM-SEC-006` |
| Exposición de secretos | Una clave llega a un commit, log, respuesta MCP, stdout o artefacto. | Persistencia o publicación de credenciales recuperables. | `TRM-SEC-003`, `TRM-SEC-006`, `TRM-SEC-010` |
| Colisión o sobrealcance MCP | Una herramienta suplanta un nombre conocido, amplía permisos o comparte contexto de otra tarea. | Operaciones con autoridad inesperada o fuga entre ámbitos. | `TRM-SEC-006`, `TRM-SEC-007` |
| Alteración de suministro | Una dependencia, acción o binario descargado cambia bajo una referencia mutable. | Ejecución o distribución de contenido distinto del revisado. | `TRM-SEC-004`, `TRM-SEC-010` |
| PR con privilegios | Código de una contribución intenta leer secretos o modificar recursos desde CI. | Acceso de código no confiable a credenciales o permisos de escritura. | `TRM-SEC-010` |
| Publicación divergente | Archivos locales no revisados o un build no reproducible entran al release. | Artefactos sin correspondencia demostrable con el árbol aprobado. | `TRM-SEC-004`, `TRM-SEC-008`, `TRM-SEC-010` |

## Riesgo residual y no objetivos

Persisten falsos negativos de detectores, vulnerabilidades desconocidas, compromisos de
un origen previamente confiable y diferencias entre sistemas operativos. Los límites de
tiempo y salida reducen impacto, pero no reemplazan aislamiento. La revisión humana puede
fallar y una referencia inmutable puede fijar contenido malicioso; por eso procedencia,
validación, privilegio mínimo y evidencia deben combinarse.

Este modelo no es una auditoría externa, una certificación ni una garantía de ausencia de
vulnerabilidades. Las referencias OWASP y W3C sirven para trazar riesgos y requisitos; no
implican aval, conformidad global ni cobertura exhaustiva. Tampoco se pretende construir
en esta tarea un sandbox universal, evaluar la seguridad interna de servicios de terceros
o sustituir pruebas de penetración específicas. Esta tarea fija el contrato; las Tasks 1–7
deben implementar, probar y actualizar cada control sin ocultar sus limitaciones.
