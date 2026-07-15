# Diseño de la CLI y TUI interactiva para la Beta de Tramalia

**Fecha:** 2026-07-14

**Estado:** Aprobado en conversación

**Rama de trabajo:** `codex/beta-implementation`

## 1. Objetivo

Convertir la experiencia de terminal de Tramalia en un centro de control
interactivo, claro y adaptable, sin reemplazar el núcleo ya estabilizado ni
cambiar la semántica de las operaciones de gobierno.

La Beta tendrá tres superficies complementarias:

1. **CLI automatizable:** comandos directos, salida estable y códigos de salida
   confiables para personas, scripts y CI.
2. **Menú guiado:** acceso sencillo a las operaciones principales cuando se usa
   una terminal interactiva.
3. **TUI de pantalla completa:** navegación con teclado y ratón, estado en vivo,
   formularios, tablas, selección, progreso y cancelación.

`tramalia ui` continuará siendo genuinamente interactiva. El rediseño no la
convertirá en una colección de reportes estáticos ni en una interfaz web.

## 2. Contexto y diagnóstico

La base funcional actual es aprovechable:

- `ServicioTablero` concentra la obtención de instantáneas y las operaciones
  compartidas.
- `InstantaneaTablero` entrega datos inmutables a Textual.
- Las tareas bloqueantes se despachan a trabajadores con hilo de Textual.
- La CLI ya dispone de Rich, modo plano y códigos de salida.
- La interfaz ya usa los catálogos ES/EN del proyecto.

La auditoría visual y estructural detectó problemas que justifican una
reestructuración real:

- `tramalia/interfaz_terminal.py` supera las mil líneas y define aplicación,
  pantallas, estilos, presentación y parte de la coordinación en una sola
  función.
- Los modales principales usan anchos absolutos de 96 y 100 columnas.
- No existe un perfil de diseño para terminales estrechas o de poca altura.
- El resumen dedica gran parte de la pantalla a espacios vacíos mientras la
  tabla principal queda truncada.
- La barra inferior intenta mostrar demasiados atajos simultáneamente.
- La paleta de comandos de Textual está desactivada.
- El formulario de cierre muestra demasiados campos y usa placeholders extensos
  en lugar de etiquetas persistentes.
- La tabla de herramientas mezcla diagnóstico, explicación, instalación y
  detalle en una única vista densa.
- La CLI, el menú y el parser mantienen catálogos de comandos separados.
- La TUI y la CLI usan colores predeterminados que no representan el sistema
  visual ya definido en MkDocs Material.

## 3. Decisiones aprobadas

- Se conservará **Textual** como biblioteca base de la TUI.
- Se conservarán **argparse**, **Rich** y **Questionary** en sus responsabilidades
  actuales; no se migrará la CLI a Typer, Click o prompt-toolkit.
- La TUI será un **centro de control híbrido**: resumen operativo para uso diario
  y recorridos guiados para inicialización, instalación y cierre.
- La identidad visual partirá de las variables visuales existentes en
  `docs/stylesheets/extra.css`.
- La aplicación será utilizable con teclado y ratón, pero ninguna operación
  dependerá exclusivamente del ratón.
- Las acciones importantes tendrán controles visibles y atajos; conocer una
  tecla no será requisito para descubrirlas.
- El color nunca será el único portador de estado.
- Los comandos públicos en inglés se conservarán por compatibilidad.
- Los módulos, clases, funciones, métodos y variables propios nuevos usarán
  nombres en español ASCII.
- No se añadirá un gran logo ASCII ni decoración que reduzca el espacio útil.
- La futura interfaz de flujos deterministas se apoyará en esta arquitectura,
  pero no se mostrará una pantalla vacía antes de implementar el Plan 05.

## 4. Enfoques considerados

### 4.1 Centro de control Textual — elegido

Reutiliza la biblioteca base y el servicio actuales, agrega un tema propio, separa
pantallas y componentes, y rediseña los recorridos con divulgación progresiva.

Ventajas:

- conserva la inversión funcional y las pruebas existentes;
- ofrece tablas, formularios, trabajadores, pantallas y paleta de comandos;
- permite una experiencia rica sin abandonar la terminal;
- mantiene el extra `[tui]` aislado del núcleo.

### 4.2 Asistente lineal completo — descartado como estructura principal

Un asistente paso a paso sería fácil para una primera inicialización, pero haría
lento el trabajo diario, dificultaría comparar estados y escondería la auditoría.
Se conservarán recorridos guiados sólo donde reducen errores: inicialización,
instalación y cierre.

### 4.3 Reconstrucción sobre prompt-toolkit o Rich — descartada

Estas bibliotecas son adecuadas para preguntas guiadas y presentación, pero obligarían a
recrear navegación, composición, trabajadores, tablas, pruebas y gestión de foco que
Textual ya proporciona. El coste y el riesgo no aportan valor a la Beta.

## 5. Arquitectura objetivo

### 5.1 Límites

La política de gates, evidencia, excepciones, habilidades e integraciones seguirá
en `tramalia/core`. Las superficies sólo presentarán modelos tipados y solicitarán
operaciones al servicio correspondiente.

La TUI no importará APIs privadas de instaladores ni construirá política de
dominio. La preparación de planes de instalación, la validación de excepciones y
la resolución de comandos vivirán en servicios del núcleo o de aplicación.

### 5.2 Módulos

La estructura objetivo será:

```text
tramalia/
  interfaz_terminal.py               # fachada compatible
  presentacion/
    variables_tema.py                 # variables puras, sin importar Rich ni Textual
  interfaz/
    aplicacion.py                     # aplicación, navegación y ciclo de vida
    tema.py                           # temas Textual construidos desde las variables
    adaptabilidad.py                  # perfil por tamaño de terminal
    acciones.py                       # acciones contextuales y paleta de comandos
    coordinador_operaciones.py        # exclusión, generaciones y cancelación
    texto_seguro.py                   # normalización de contenido externo
    presentadores.py                  # modelos tipados -> contenido visual
    pantallas/
      resumen.py
      herramientas.py
      habilidades.py
      auditoria.py
      cierre.py
      inicializacion.py
      proveedor_contexto.py
    componentes/
      cabecera_proyecto.py
      tarjeta_estado.py
      estado_vacio.py
      barra_acciones.py
      detalle_lateral.py
      formulario_campo.py
      registro_proceso.py
      selector_seccion.py
      confirmacion_plan.py
      aviso_tamano_minimo.py
    estilos/
      tramalia.tcss                   # reglas visuales y clases de densidad
  cli/
    catalogo_comandos.py              # metadatos canónicos de comandos
    tema.py                           # tema Rich construido desde las variables
    ayuda.py                          # ayuda agrupada y ejemplos
    renderizado.py                    # representación de resultados
```

`tramalia/interfaz_terminal.py` conservará `construir_aplicacion()` y
`ejecutar()` como fachada de compatibilidad. No contendrá widgets ni política.
Las reglas visuales vivirán en TCSS, no en cadenas extensas dentro de Python.

### 5.3 Comandos públicos y acciones de interfaz

`catalogo_comandos.py` definirá cada comando, subcomando y argumento público
mediante modelos `DefinicionComandoPublico`, `DefinicionSubcomando` y
`DefinicionArgumento`. Cada definición incluirá:

- clave pública estable;
- categoría de uso;
- claves i18n para nombre, resumen y ayuda;
- argumentos, flags, valores permitidos y obligatoriedad;
- ejemplos;
- visibilidad en ayuda, menú y automatización;
- si acepta interacción o salida estructurada;
- extra requerido;
- capacidad u operación que invoca;
- clave de manejador, resuelta por un registro separado.

El parser, `tramalia menu` y la ayuda enriquecida consumirán ese catálogo. Los
manejadores permanecerán fuera para evitar ciclos y mezcla de presentación con
ejecución. Las traducciones se resolverán al representar, nunca al importar el
módulo, para que el idioma no quede congelado.

`RegistroAccionesInterfaz` será un contrato distinto para acciones contextuales
como refrescar, cambiar tema, abrir ayuda o cancelar. La paleta combinará acciones
de interfaz aplicables con un subconjunto explícito de comandos públicos; no
expondrá automáticamente operaciones como `mcp` sólo porque existan en argparse.

### 5.4 Operaciones observables y coordinación

La interacción en vivo requiere ampliar el servicio compartido sin romper las
fachadas actuales.

`preparar_cierre()` devolverá un `PlanCierre` inmutable con tarea, puertas,
bloqueos previos, excepción solicitada y límite de cancelación. La ejecución
publicará `EventoOperacion` tipados:

- `iniciada`;
- `paso_iniciado`;
- `salida`;
- `paso_terminado`;
- `publicando`;
- `completada`;
- `cancelada`;
- `fallida`.

Cada evento incluirá identificador de operación, instante, paso y datos
estructurados. Las líneas de herramientas viajarán como texto externo sin marcado.
`ejecutar_cierre_observable()` devolverá `ResultadoOperacionCierre`, cuyo estado
será `completada`, `cancelada` o `fallida` y que sólo contendrá un
`ResultadoCierre` en estado `completada`; `cancelada` no tendrá resultado de
cierre y `fallida` conservará el error tipado. `cerrar_proyecto()` seguirá siendo la
fachada síncrona pública: ejecutará sin token externo, consumirá los eventos y
devolverá el mismo `ResultadoCierre` actual.

Una `SenalCancelacion` cooperativa podrá detener una ejecución durante las
puertas. La cancelación terminará el árbol del proceso, producirá
`ResultadoOperacionCierre(cancelada)` —código 130 cuando una superficie CLI lo
exponga— y no publicará evidencia final. Al emitir
`publicando`, la cancelación y la salida de la aplicación quedarán deshabilitadas
hasta terminar el renombrado atómico. La terminación de árboles se probará en Windows,
Linux y macOS sin añadir `psutil` salvo evidencia de que las primitivas nativas no
son suficientes.

`Worker.cancel()` de Textual no se considerará cancelación de una operación en
hilo. El trabajador solicitará la señal del núcleo y el servicio de procesos cerrará
el grupo o árbol correspondiente; sólo entonces se publicará el evento
`cancelada`.

`CoordinadorOperaciones` aplicará estas reglas:

- una sola operación mutante a la vez;
- refrescos de lectura identificados por generación, aplicando sólo la respuesta
  más reciente;
- filtros y navegación local sin bloqueo;
- cierre de la TUI inmediato si sólo hay lecturas cancelables;
- confirmación para cancelar y salir si hay una mutación cancelable;
- bloqueo temporal de salida durante publicación atómica.

Cancelar una instalación detendrá el plan completo, conservará los pasos ya
terminados y no iniciará los pendientes. La Beta no mezclará ese concepto con
«omitir este paso».

### 5.5 Contenido externo seguro

Rutas, metadata, nombres del proyecto y salidas de procesos se tratarán como
contenido hostil. Antes de mostrarlos se:

- escapará el marcado de Rich y Textual;
- eliminarán secuencias ANSI, CSI, OSC y controles no permitidos;
- reemplazará Unicode inválido sin interrumpir la aplicación;
- limitará cada línea a 8 KiB;
- mantendrá cada registro en un búfer circular de hasta 1 MiB;
- validarán URLs abiertas desde la TUI, permitiendo sólo `https` y, cuando una
  integración oficial lo requiera de forma explícita, `http`.

Los límites se indicarán con una marca textual de truncamiento. Nunca se
interpretará salida de una herramienta como marcado, enlace de acción o estado de
Tramalia.

## 6. Sistema visual compartido

### 6.1 Tema oscuro predeterminado

| Uso | Token |
|---|---|
| fondo | `#05031c` |
| fondo profundo y logs | `#010319` |
| panel | `#0f0a4c` |
| superficie elevada | `#1c1060` |
| primario | `#623abf` |
| secundario | `#8c68d9` |
| acción y foco | `#b3e448` |
| texto principal | `#f7f5ff` |
| texto secundario | `#b7b3cb` |
| éxito | `#7fe36a` |
| advertencia | `#f5c451` |
| error | `#ff6178` |
| información | `#62c6ff` |
| evidencia y traspaso | `#46d6c7` |

### 6.2 Temas adicionales

- **Tramalia claro:** usará las variables claras existentes; el acento textual será
  `#567d14`, no el lima oscuro, para conservar contraste.
- **Alto contraste:** reducirá superficies decorativas, aumentará bordes y foco,
  y usará colores de texto que superen el contraste requerido.
- **Monocromático:** se activará con `NO_COLOR` o una opción explícita. Conservará
  símbolos, etiquetas y jerarquía tipográfica.

La precedencia será `NO_COLOR`, `tramalia ui --tema`, `TRAMALIA_TEMA` y, por
último, `tramalia-oscuro`. `--tema` y la variable aceptarán `oscuro`, `claro`,
`alto-contraste` o `monocromo`. La paleta podrá cambiar el tema durante la sesión. La
Beta no guardará esta preferencia en el repositorio ni en configuración global;
esa persistencia queda fuera de alcance para evitar mezclar gobierno de proyecto
con preferencias personales. No habrá animaciones no esenciales, por lo que el
comportamiento de movimiento reducido será el predeterminado.

Textual y Rich construirán sus temas desde
`tramalia/presentacion/variables_tema.py`, un
módulo puro que no importará ninguna dependencia opcional. Un contrato comparará
sus valores con las variables canónicas publicadas en `extra.css`. Los colores
semánticos de modo claro se ajustarán para alcanzar al menos 4.5:1 en texto
normal; no se reutilizarán sin adaptación los colores luminosos del tema oscuro.

### 6.3 Reglas visuales

- El lima se reservará para la acción principal, selección y foco.
- El violeta definirá estructura y navegación.
- Éxito, advertencia, error y degradación siempre tendrán símbolo y texto.
- Los paneles usarán bordes discretos; no todas las secciones serán cajas.
- Los títulos serán cortos y orientados a una acción o estado.
- La ruta completa del proyecto aparecerá en detalle o ayuda; la cabecera usará
  nombre y ruta abreviada para evitar saltos innecesarios.
- Animaciones o transiciones serán mínimas y respetarán movimiento reducido.

## 7. Adaptabilidad

La aplicación usará `HORIZONTAL_BREAKPOINTS` y `VERTICAL_BREAKPOINTS` de Textual
8.2.8 para asignar clases de perfil sin mantener un manejador manual del cambio de
tamaño. Los
breakpoints horizontales serán `[(0, "-compacto"), (80, "-medio"),
(120, "-ancho")]`; los verticales distinguirán menos de 24, 24–35 y 36 o más
filas.

| Perfil | Ancho | Comportamiento |
|---|---:|---|
| compacto | hasta 79 columnas | una columna, cabecera reducida, tablas con columnas esenciales y detalle al seleccionar |
| medio | 80–119 columnas | una columna amplia, tarjetas agrupadas y detalle debajo |
| ancho | 120 columnas o más | dos columnas cuando aporten contexto y panel lateral de detalle |

Con 23 filas o menos, la cabecera y el pie usarán su variante compacta y el
contenido principal tendrá desplazamiento propio. Ningún bloque reservará altura
vacía sólo para completar `1fr`.

Los modales usarán un ancho relativo al viewport y un máximo razonable; nunca
serán más anchos que la terminal. Los formularios, tablas y registros tendrán su
propio desplazamiento, sin generar desplazamiento horizontal de toda la pantalla.

El cambio de tamaño actualizará clases de densidad y composición sin reiniciar la
aplicación ni perder la selección o los campos escritos.

Las clases de breakpoint modificarán composición y visibilidad, pero las columnas
de `DataTable` se adaptarán mediante un presentador de tabla. Si es necesario
reconstruirlas, se conservarán claves estables de fila, selección, scroll y foco;
ningún cambio de tamaño volverá a consultar el núcleo ni reiniciará formularios.

El tamaño mínimo soportado será 50×18. Por debajo se mostrará únicamente un aviso
seguro con el tamaño actual, el mínimo requerido y la acción Salir; no se montarán
formularios ni se permitirán mutaciones. Resumen y Cierre tendrán pruebas
funcionales, no sólo capturas, exactamente en 50×18.

## 8. Arquitectura de información de la TUI

### 8.1 Cabecera

Mostrará sólo:

- Tramalia y versión;
- nombre del proyecto;
- estado de gobierno;
- tarea actual, si existe;
- indicador de operación en curso.

La ruta completa, stack y proveedor activo quedarán disponibles en el resumen y
en el detalle contextual.

### 8.2 Navegación principal

Las áreas serán:

1. **Resumen**
2. **Herramientas**
3. **Habilidades**
4. **Auditoría**
5. **Cierre**

El doctor dejará de ocupar la mayor parte del Resumen y se convertirá en la
pantalla **Herramientas/Diagnóstico**; no se añadirá una sexta área. La navegación
será accesible mediante controles visibles, teclas y paleta de comandos.

En los perfiles medio y ancho se usarán pestañas visibles. En el perfil compacto,
las cinco pestañas se reemplazarán por un selector de sección con el nombre de la
vista actual; `Enter` abrirá la lista y `Alt+1` a `Alt+5` permitirá saltar de forma
directa. La paleta ofrecerá las mismas cinco rutas. Así la navegación no quedará
truncada en 50 u 80 columnas.

### 8.3 Resumen

El primer viewport responderá cinco preguntas:

1. ¿Está gobernado el proyecto?
2. ¿Qué tarea está activa?
3. ¿Las puertas están configuradas?
4. ¿Existe algún bloqueo o degradación?
5. ¿Cuál es la siguiente acción recomendada?

La pantalla contendrá tarjetas compactas para proyecto, puertas, herramientas,
habilidades y último cierre. Sólo una acción será primaria. Para un proyecto no
inicializado será **Inicializar proyecto**; para uno listo con tarea activa será
**Revisar y cerrar tarea**.

La primera acción dependerá del estado tipado:

| Estado | Acción primaria | Vista previa obligatoria |
|---|---|---|
| `ausente` | inicializar o adoptar | archivos que se crearán o integrarán |
| `heredado` | actualizar convención | migraciones y archivos nuevos |
| `parcial` | reparar configuración | piezas inválidas o ausentes, sin cierre |
| `listo` con tarea | revisar y cerrar | tarea, puertas y posibles bloqueos |
| `listo` sin tarea | seleccionar o declarar tarea | origen en `specs/tasks.md` |

Inicializar, adoptar, actualizar y reparar serán operaciones distintas. Ninguna
mutación se ejecutará desde una tarjeta sin mostrar primero su plan y solicitar
confirmación.

En estado `ausente`, un directorio vacío o mínimo recomendará Inicializar. Si ya
hay código, configuración o un `AGENTS.md`, recomendará Adoptar y explicará la
diferencia; la persona podrá elegir la otra vía antes de confirmar. El estado
`parcial` nunca caerá silenciosamente en `init`: mostrará cada pieza que debe
repararse.

### 8.4 Herramientas

La tabla mostrará en su vista principal:

- herramienta;
- propósito corto;
- estado;
- requisito o siguiente acción.

La explicación extensa, versión, comando de instalación, capacidad y dependencia
de runtime se mostrarán en un panel de detalle. Se podrá filtrar por texto,
categoría y estado.

La instalación seguirá este recorrido:

1. seleccionar herramientas;
2. revisar el plan exacto y los prerrequisitos;
3. confirmar;
4. observar salida en vivo;
5. cancelar el plan sin perder el resultado de pasos terminados ni iniciar los
   pendientes;
6. refrescar el diagnóstico real.

Nunca se instalará una herramienta por visitar la pantalla o seleccionar una
fila.

### 8.5 Habilidades

Conservará declaración, sincronización, actualización y apertura de documentación.
La vista distinguirá de forma explícita:

- propia;
- disponible;
- declarada;
- instalada con SHA;
- actualizable;
- rastreada incorrectamente por Git.

Actualizar y rehidratar serán acciones distintas tanto en el texto como en los
controles. La selección conservará el detalle de fuente, referencia y SHA.

### 8.6 Auditoría

La lista y el detalle compartirán pantalla sólo en perfil ancho. En perfiles
compacto y medio, seleccionar una entrada abrirá su detalle en la misma pila de
navegación.

El detalle priorizará:

- tarea y resultado;
- puertas ejecutadas;
- excepciones;
- agente, revisor y modelo registrados;
- rutas a evidencia y traspaso;
- errores de lectura, si la entrada es inválida.

Los metadatos crudos seguirán disponibles, pero no serán la única presentación.

### 8.7 Cierre guiado

El cierre se organizará en secciones progresivas:

1. **Tarea e identidades:** tarea, agente, revisor y modelo opcional.
2. **Validaciones previstas:** puertas que se ejecutarán y bloqueos previos.
3. **Excepción revisada:** plegada por defecto y visible sólo al activarla o
   cuando un resultado requiera remediación.
4. **Ejecución:** salida puerta por puerta, progreso, duración y cancelación
   mientras se ejecutan puertas. Al comenzar la publicación atómica la acción de
   cancelar se deshabilitará hasta obtener el resultado final.
5. **Resultado:** aprobado, aprobado con excepciones o bloqueado, con enlace a la
   evidencia y siguiente acción.

Cada campo tendrá una etiqueta persistente, ayuda breve y error junto al campo.
Los placeholders se reservarán para ejemplos. Antes de ejecutar, la interfaz
mostrará un resumen de tarea, puertas y excepción solicitada.

## 9. Interacción y descubribilidad

- `Tab` y `Shift+Tab` recorrerán controles en orden lógico.
- `Enter` activará la acción enfocada y `Esc` cerrará el nivel actual sin mutar
  estado.
- Las flechas navegarán tablas y opciones.
- Los controles principales aceptarán ratón.
- `Ctrl+P` abrirá la paleta de comandos con nombre y ayuda traducidos.
- `F1` abrirá ayuda contextual de la pantalla activa. `?` podrá ser un alias sólo
  cuando el foco no esté en un campo editable.
- El pie será compacto y mostrará sólo acciones aplicables al contexto.
- Los atajos secundarios permanecerán disponibles aunque no quepan en el pie,
  mediante la paleta y la ayuda.
- Las acciones temporalmente imposibles se ocultarán o deshabilitarán de forma
  coherente con su causa.

Al abrir una pantalla el foco irá a su encabezado operativo o primer control; al
abrir un modal, al primer control seguro. Al cerrarlo volverá al invocador. Un
error de formulario enfocará el primer campo inválido. Las acciones esperables
pero temporalmente imposibles permanecerán deshabilitadas con explicación; sólo
se ocultarán acciones irrelevantes para ese contexto.

## 10. Experiencia de la CLI

### 10.1 Ayuda

La ayuda agrupará comandos por intención:

- empezar y adoptar;
- verificar;
- contexto e integraciones;
- evidencia y cierre;
- mantenimiento;
- avanzado.

Los encabezados, resúmenes y ejemplos respetarán el idioma resuelto por Tramalia.
La implementación conservará argparse y usará Rich cuando esté disponible; el
modo plano seguirá siendo texto estable sin códigos ANSI.

Cada comando principal mostrará:

- propósito en una frase;
- sintaxis;
- dos o tres ejemplos reales;
- opciones agrupadas;
- siguiente acción habitual.

### 10.2 Salidas

- El texto enriquecido seguirá siendo la salida predeterminada en una TTY.
- `--plain` y `NO_COLOR` producirán salida legible y determinista.
- Las tablas reducirán columnas según el ancho; el detalle no quedará cortado en
  celdas ilegibles.
- Los errores incluirán código estable, mensaje y remediación, sin traceback para
  errores de dominio.
- Los comandos respaldados por modelos tipados ofrecerán una salida JSON estable
  mediante `--formato json`; `--formato texto` será el valor predeterminado. La
  primera cobertura incluirá `doctor`, `detect`, `log`, `context list` y
  `skills list`; otros comandos se añadirán sólo cuando exista un contrato
  estructurado real.
- La salida JSON nunca incluirá decoración, preguntas interactivas ni mensajes
  mezclados por la salida estándar (`stdout`); los diagnósticos técnicos irán a
  la salida de errores (`stderr`).

El sobre JSON inicial será:

```json
{
  "version_esquema": 1,
  "ok": true,
  "comando": "doctor",
  "datos": {},
  "advertencias": []
}
```

Un error de dominio reemplazará `datos` por `error`, con `codigo`, `mensaje`,
`sugerencia` y `ruta` opcional. La forma será idéntica con y sin TTY.

Las claves, enums, fechas y rutas se serializarán de forma explícita y serán
independientes del idioma. `--formato json` conservará los códigos de salida del
comando. Su combinación con `--plain` será un error de uso con código 2, y se
rechazará también en `menu`, `ui` o cualquier comando que aún no declare un
serializador estructurado. La opción global se aceptará antes o después del
subcomando, como ocurre con `--plain`.

### 10.3 Menú

`tramalia menu` será un selector guiado de operaciones, no una segunda
implementación del producto. Consumirá el catálogo canónico y delegará en los
mismos manejadores. En una entrada o salida no interactiva deberá terminar con una
explicación clara, nunca esperar indefinidamente por una respuesta.

## 11. Estados, errores y operaciones largas

Cada operación visible tendrá estados diferenciados:

- pendiente;
- en curso;
- completa;
- degradada;
- cancelada;
- tiempo agotado;
- fallida.

La TUI mostrará primero la estructura y un estado de carga; las sondas no
bloquearán el bucle de eventos (*event loop*). Sólo habrá un refresco de
instantánea activo por grupo.
Cerrar la aplicación solicitará cancelación cooperativa y no dejará callbacks
intentando escribir en widgets desmontados.

Los registros de procesos y los detalles de auditoría usarán carga acotada y
búferes circulares. Una auditoría extensa se paginará o cargará por selección; no
se leerán ni montarán en widgets todos los archivos de evidencia al iniciar la
aplicación.

Un fallo deberá conservar:

- capacidad afectada;
- herramienta solicitada y utilizada;
- motivo estable;
- impacto;
- remediación.

La interfaz no reinterpretará un código no cero como ausencia ni como éxito.

## 12. Accesibilidad

- Todo estado combinará texto, símbolo y color.
- El foco será visible en todos los temas.
- Los formularios tendrán etiquetas persistentes y orden de tabulación lógico.
- Los símbolos tendrán alternativa textual y no dependerán de emoji a color.
- El tema claro y el de alto contraste cumplirán contraste mínimo para texto.
- Se respetarán `NO_COLOR`, terminales de 256 colores y terminales sin Unicode
  completo mediante degradación explícita.
- Español e inglés tendrán el mismo contenido y recorrido.
- Las anchuras de prueba incluirán textos traducidos para detectar truncamiento.

La accesibilidad de lectores de pantalla depende también del emulador de
terminal. La Beta verificará etiquetas visibles, foco, navegación por teclado y
salida plana, y documentará una matriz manual de emuladores probados. No afirmará
compatibilidad universal ni soporte de lector de pantalla sin evidencia
específica por emulador y sistema operativo.

## 13. Dependencias

- Textual permanecerá en el extra `[tui]`.
- Rich y Questionary permanecerán en el núcleo de presentación de la CLI.
- No se añadirá una biblioteca alternativa de TUI.
- La primera implementación validará Textual 8.2.8 y expresará el rango
  `textual>=8.2,<9`; mover ese límite requerirá actualizar el archivo de bloqueo,
  las capturas y CI.
- CI y el archivo de bloqueo usarán la misma versión probada.
- `pytest-textual-snapshot` se incorporará sólo al grupo de desarrollo para las
  regresiones visuales y quedará fijado en el archivo de bloqueo.

## 14. Estrategia de pruebas

### 14.1 Funcionalidad

Se conservarán y migrarán las regresiones valiosas actuales. Las pruebas públicas
con `Pilot` cubrirán:

- navegación por pestañas, paleta y teclado;
- proyecto ausente, parcial, heredado y listo;
- selección y plan de instalación;
- cancelación, tiempo agotado y fallo externo;
- actualización y rehidratación de habilidades;
- auditoría válida e inválida;
- cierre aprobado, con excepción y bloqueado;
- cierre cancelado durante una puerta, sin evidencia final ni procesos hijos;
- validación de formularios antes de iniciar trabajadores;
- cambio de tamaño sin perder estado;
- exclusión de dos mutaciones simultáneas y descarte de refrescos obsoletos;
- foco inicial, retorno desde modal y foco en primer campo inválido;
- contenido hostil con marcado, ANSI, OSC, línea enorme y Unicode inválido;
- tema y paleta traducidos;
- importación y wheel base sin Textual instalado.

### 14.2 Regresión visual

Las capturas canónicas mínimas serán:

| Estado | Tamaño |
|---|---|
| resumen sin inicializar | 80×24 |
| resumen listo | 120×36 |
| herramientas con detalle | 160×48 |
| cierre con excepción plegada | 80×24 |
| cierre con excepción expandida | 120×36 |
| auditoría y evidencia | 120×36 |
| modal de proveedor | 50×18 |
| resumen compacto | 50×18 |
| cierre compacto | 50×18 |

Se añadirán capturas equivalentes sólo cuando protejan una diferencia real de
idioma, tema o estado. No se construirá el producto cartesiano de todas las
combinaciones.

Las instantáneas visuales se aprobarán manualmente. CI nunca ejecutará una
actualización automática de capturas.

### 14.3 CLI

Se probarán anchos de 60, 80, 120 y 160 columnas, con Rich, `--plain`,
`NO_COLOR`, TTY y no-TTY. Los contratos verificarán que parser, catálogo, menú,
documentación y despachador exponen el mismo conjunto de comandos aplicable.
También cubrirán JSON puro, serialización estable, rechazo de combinaciones no
admitidas y terminación de `tramalia menu` sin TTY.

### 14.4 Número de tests

No existe una meta de 250 pruebas. Se conservará cada contrato de riesgo y se
retirarán duplicados históricos cuando su comportamiento esté protegido en la
nueva organización. Las capturas no reemplazarán pruebas funcionales.

## 15. Documentación

El Plan 04 actualizará:

- `docs/interfaz.md` y su par inglés con capturas regenerables de la TUI real;
- `docs/comandos.md` y su par inglés con la nueva agrupación y formatos de salida;
- el glosario para explicar TUI, CLI, puerta, degradación y paleta de comandos;
- el sistema Mermaid compartido, con títulos y descripciones accesibles;
- el modo claro para corregir contrastes insuficientes;
- los activos de marca para evitar archivos redundantes o excesivos.

Las capturas documentales se generarán desde servicios falsos deterministas, no
desde el estado particular de la máquina que construye la documentación.

## 16. Relación con los planes

### Plan 03

Se añadirán dos tareas diferenciadas:

1. **Tarea 5 — seguridad y calidad de superficies:** Semgrep, Gitleaks,
   Playwright, axe y Lighthouse;
2. **Tarea 6 — experiencia de terminal:** reestructuración de CLI/TUI descrita en
   esta especificación.

La segunda tarea se ejecutará después de cerrar las verificaciones pendientes de
la separación actual de superficies y después de la Tarea 5. La Tarea 6 podrá
tocar procesos y puertas únicamente para añadir observabilidad y cancelación
segura; no cambiará la política de aprobación definida en el Plan 02.

### Plan 04

Consumirá la interfaz terminada para publicar capturas reales, corregir el sistema
visual, sanear documentos heredados y completar documentación, licencia y
lanzamiento.

### Plan 05

Añadirá la pantalla de recetas y flujos deterministas sólo cuando existan los
modelos `listar`, `planificar`, `simular` y `ejecutar`. La TUI se limitará a
presentar el plan resuelto y sus resultados.

## 17. Secuencia de implementación

1. Crear catálogo de comandos, variables de tema y presentadores compartidos.
2. Separar la fachada `interfaz_terminal.py` del paquete `interfaz`.
3. Mejorar ayuda, tablas, modo plano y salida estructurada de la CLI.
4. Construir la carcasa adaptable de la TUI y su navegación.
5. Implementar Resumen y Herramientas.
6. Implementar Habilidades y Auditoría.
7. Implementar Cierre guiado y resultados.
8. Añadir pruebas funcionales, accesibles y visuales.
9. Actualizar documentación ES/EN y capturas.

Cada paso preservará comandos públicos y deberá dejar la suite verde antes de
continuar.

## 18. Criterios de aceptación

- `tramalia ui` sigue siendo interactiva con teclado y ratón.
- La interfaz es utilizable en 50×18 y no presenta desbordamiento horizontal de
  toda la pantalla.
- Por debajo de 50×18 sólo aparece el aviso de tamaño mínimo y ninguna acción
  mutante.
- En 80×24 se ven estado, siguiente acción y contenido principal sin que el pie
  o espacios vacíos consuman la pantalla.
- En 120 columnas o más se aprovecha el espacio con detalle contextual sin
  duplicar información.
- Ningún modal excede el ancho o alto disponible.
- El cierre no muestra campos de excepción mientras estén desactivados.
- Todos los campos tienen etiqueta, ayuda y error accesibles.
- La paleta permite descubrir las acciones importantes.
- El foco inicial, el retorno desde modales y el salto al primer error funcionan
  sólo con teclado y sin trampas de foco.
- Herramientas y habilidades distinguen selección, plan, confirmación, ejecución
  y resultado.
- Sólo una operación mutante puede ejecutarse a la vez y un refresco obsoleto no
  reemplaza una instantánea más reciente.
- Cancelar durante una puerta termina su árbol de procesos, devuelve estado
  cancelado y no publica evidencia final; durante publicación atómica la
  cancelación queda deshabilitada.
- CLI, menú y TUI consumen el mismo catálogo de comandos y las mismas operaciones.
- Los comandos y flags públicos actuales conservan compatibilidad.
- Importar `tramalia`, construir el parser y ejecutar cualquier comando de núcleo
  funciona sin instalar el extra `[tui]`.
- `--plain`, `NO_COLOR` y JSON no mezclan códigos ANSI ni preguntas interactivas.
- Markup, ANSI, OSC, líneas enormes o Unicode inválido provenientes del proyecto
  o de herramientas no pueden crear acciones, falsificar estados ni crecer sin
  límite en memoria.
- Los estados nunca dependen únicamente del color.
- Toda operación externa se ejecuta fuera del bucle de eventos y puede terminar,
  cancelar o agotar tiempo sin bloquear la aplicación.
- Los temas Textual y Rich comparten variables semánticas con MkDocs Material.
- `--tema`, `TRAMALIA_TEMA` y `NO_COLOR` resuelven el tema con precedencia
  documentada y sin escribir preferencias globales.
- Las pruebas visuales cubren terminales compacta, media y ancha sin sustituir
  pruebas funcionales.
- La documentación ES/EN muestra capturas reales y regenerables.
- Los módulos propios nuevos usan nombres en español ASCII y las APIs públicas
  mantienen docstrings en inglés estilo Google.

## 19. Fuera de alcance

- Migrar a una interfaz gráfica de escritorio o web.
- Reemplazar Textual por otra biblioteca base.
- Cambiar la semántica del núcleo de gates, evidencia o cierre.
- Instalar herramientas automáticamente sin plan y confirmación.
- Añadir telemetría remota.
- Implementar el motor de flujos deterministas del Plan 05.
- Afirmar compatibilidad universal con todos los lectores de pantalla de terminal.

## 20. Riesgos y mitigaciones

- **Refactor visual demasiado amplio:** dividir por pantallas y mantener una
  fachada compatible mientras migran las pruebas.
- **Snapshots frágiles:** proteger sólo estados representativos y combinar
  capturas con aserciones semánticas.
- **Sobrecarga de la paleta:** mostrar por defecto sólo acciones aplicables a la
  pantalla y buscar el resto bajo demanda.
- **Pérdida de densidad para usuarios expertos:** conservar atajos, filtros y
  paneles de detalle en perfil ancho.
- **Dependencia excesiva de color:** validar todos los estados en tema
  monocromático y alto contraste.
- **Deriva entre CLI, TUI y documentación:** generar metadatos y capturas desde
  catálogos y servicios compartidos.
- **Cambios incompatibles de Textual:** fijar la familia probada y actualizarla de
  forma deliberada mediante archivo de bloqueo y CI.
