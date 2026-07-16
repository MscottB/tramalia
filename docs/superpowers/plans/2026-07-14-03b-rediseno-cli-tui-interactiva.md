# Experiencia CLI/TUI interactiva Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir la CLI y la TUI de Tramalia en superficies coherentes, agradables, accesibles y seguras para una BETA: CLI automatizable con texto/JSON, menú guiado estable y TUI Textual completamente interactiva, adaptable y observable, sin duplicar la política del núcleo.

**Architecture:** `tramalia.interfaz_terminal` queda como fachada compatible. La TUI real se divide en aplicación, pantallas, componentes, presentadores, tema, seguridad de texto y coordinación de operaciones. CLI y menú consumen un catálogo público inmutable, pero mantienen registros de manejadores/acciones separados para evitar ejecutar funciones por introspección. Habilidades consume exclusivamente `ServicioHabilidades` y los modelos, planes y resultados públicos entregados por el Plan 03c; esta superficie no interpreta TOML, locks, perfiles ni política de resolución. El cierre gana una ruta observable y cancelable sobre el mismo núcleo; `cerrar_proyecto()` conserva su firma y resultado síncrono. Rich y Textual comparten tokens puros de presentación derivados de la identidad MkDocs Material.

**Tech Stack:** Python 3.11–3.14, argparse, Rich 15.x, Questionary 2.1.x, Textual `>=8.2,<9` (lock inicial 8.2.8), pytest 8, Pilot, `pytest-textual-snapshot` 1.1.0, subprocess de stdlib y MkDocs Material.

## Global Constraints

- Ejecutar después de completar los planes 03a y 03c, y antes del Plan 04.
- El contrato de habilidades canónico es `docs/superpowers/plans/2026-07-16-03c-habilidades-gobernadas.md` y su prueba `tests/contratos/test_entrega_03c.py`; 03b no redefine modelos, resolución, perfiles, materialización, auditoría ni reglas de seguridad de habilidades.
- La especificación canónica es `docs/superpowers/specs/2026-07-14-rediseno-cli-tui-interactiva-design.md`; este plan no puede reducir sus estados, seguridad o criterios de aceptación.
- No migrar a Typer, Click, prompt-toolkit, una GUI web ni Figma.
- Mantener `argparse`, Rich, Questionary y Textual; la interactividad completa vive en `tramalia ui`.
- Preservar comandos/opciones públicos ingleses, destinos argparse, códigos de salida y las fachadas `construir_parser()`, `construir_aplicacion()` y `ejecutar()`.
- CLI, TUI y MCP siguen siendo adaptadores de `tramalia.core`; ninguna superficie reimplementa política de gates, evidencia, excepciones o habilidades.
- CLI y TUI usan los mismos IDs de operación y métodos de `ServicioHabilidades`; toda diferencia de disponibilidad queda declarada y probada, nunca inferida por nombre de función.
- Una única operación mutante puede estar activa. Puede haber lecturas simultáneas de grupos distintos, pero como máximo una lectura activa por grupo; solicitudes rápidas del mismo grupo se coalescen y sólo la generación más reciente actualiza la pantalla.
- Cancelar antes de `publicando` detiene el árbol de procesos y no publica evidencia parcial. Desde `publicando` hasta terminar `os.replace`, cancelar y salir quedan bloqueados.
- Salidas externas son contenido hostil: nunca se interpretan como markup, enlaces, comandos, estados o acciones.
- La TUI debe funcionar en 50×18. Por debajo muestra sólo aviso de tamaño y Salir; no monta formularios ni permite mutaciones.
- `NO_COLOR` fuerza monocromo. Precedencia de tema: `NO_COLOR`, `--tema`, `TRAMALIA_TEMA`, oscuro.
- No guardar preferencia de tema en el repositorio ni globalmente durante la BETA.
- No buscar una cifra de pruebas. Se conservan contratos por riesgo y se eliminan duplicados históricos sólo después de demostrar equivalencia.
- Los comandos, subcomandos, aliases y conteos visibles se derivan del catálogo canónico; ningún contrato o documento fija una cantidad manual.
- Nombres propios nuevos en español ASCII; comentarios internos en español; docstrings públicos en inglés estilo Google.
- TDD obligatorio por tarea: test rojo, implementación mínima, refactor, regresión y commit pequeño.

---

## Baseline y riesgos reproducidos

- `tramalia/interfaz_terminal.py` tiene 1090 líneas, clases locales, CSS embebido, modales de ancho fijo y paleta deshabilitada.
- La aplicación permite mutaciones simultáneas si pertenecen a grupos Textual distintos.
- Un refresco cancelado puede aplicar una instantánea antigua porque el worker de hilo sigue terminando.
- La cancelación de instalación se limpia dentro del bucle y puede continuar con pasos pendientes; sólo termina el proceso directo.
- El cierre no es observable ni cancelable.
- La salida de herramientas entra en markup; `webbrowser.open()` no valida esquema.
- Auditoría carga todos los metadatos al construir cada snapshot.
- Estado `parcial` puede caer en inicialización directa sin plan/confirmación.
- `TRAMALIA_LANG=en tramalia --help` sigue en español; `--formato` no existe.
- `renderizado.py` conserva `_PLANO`/`_consola` globales y una ejecución plana contamina la siguiente.
- `tramalia menu` sin TTY puede lanzar traceback de Questionary en Windows.
- Colección actual medida: 662 casos parametrizados. Es una medición, no una cuota.
- Baseline TUI aislado: 4 pruebas pasan. Combinada con tablero/puertas/operaciones apareció un fallo dependiente del orden; la Task 1 lo aísla antes de refactorizar.

## File map

```text
tramalia/
  interfaz_terminal.py                 # fachada compatible
  presentacion/
    __init__.py
    variables_tema.py                  # tokens puros, sin Rich/Textual
  interfaz/
    __init__.py
    aplicacion.py
    tema.py
    adaptabilidad.py
    acciones.py
    coordinador_operaciones.py
    canal_eventos.py
    texto_seguro.py
    presentadores.py
    pantallas/
      __init__.py
      resumen.py
      herramientas.py
      habilidades.py
      auditoria.py
      cierre.py
      inicializacion.py
      proveedor_contexto.py
    componentes/
      __init__.py
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
      tramalia.tcss
  cli/
    catalogo_comandos.py
    tema.py
    ayuda.py
    salida_estructurada.py
    renderizado.py                      # fachada compatible
```

Core nuevo/modificado:

```text
tramalia/core/cancelacion.py
tramalia/core/modelos_operacion.py
tramalia/core/preparacion_proyecto.py
tramalia/core/procesos.py
tramalia/core/instalador.py
tramalia/core/installer.py              # shim BETA, sin lógica ni referencia mkdocstrings
tramalia/core/puertas_calidad.py
tramalia/core/operaciones.py
tramalia/core/tablero.py
tramalia/core/evidencia.py
```

Dependencias públicas de 03c consumidas sin modificación de dominio:

```text
tramalia/core/modelos_habilidades.py
tramalia/core/auditoria_habilidades.py
tramalia/core/servicio_habilidades.py
tests/contratos/test_entrega_03c.py
```

Pruebas canónicas nuevas:

```text
tests/unidad/test_modelos_operacion.py
tests/integracion/test_procesos.py
tests/unidad/test_preparacion_proyecto.py
tests/integracion/test_preparacion_proyecto.py
tests/unidad/test_coordinador_operaciones.py
tests/unidad/test_texto_seguro.py
tests/unidad/test_adaptabilidad.py
tests/contratos/test_tema_terminal.py
tests/contratos/test_catalogo_cli.py
tests/contratos/test_salida_estructurada_cli.py
tests/interfaz/test_presentacion_cli.py
tests/interfaz/test_menu_cli.py
tests/integracion/test_cli_subproceso.py
tests/interfaz/test_aplicacion_terminal.py
tests/interfaz/test_cierre_terminal.py
tests/interfaz/test_adaptabilidad_terminal.py
tests/interfaz/test_seguridad_terminal.py
tests/interfaz/test_habilidades_terminal.py
tests/contratos/test_paridad_operaciones_terminal.py
tests/interfaz/snapshots/
```

## Contratos públicos que deben preservarse

```python
# tramalia/__main__.py
def construir_parser() -> argparse.ArgumentParser: ...
def main(argv: Sequence[str] | None = None) -> int: ...

# tramalia/interfaz_terminal.py
def construir_aplicacion(servicio: ServicioTablero | None = None) -> App: ...
def ejecutar() -> None: ...

# tramalia/core/procesos.py
@dataclass(frozen=True, slots=True)
class ResultadoProceso:
    comando: tuple[str, ...]
    codigo_salida: int
    salida: str
    error: str
    agotado_tiempo: bool = False
    cancelado: bool = False
    salida_truncada: bool = False
    error_truncado: bool = False
    bytes_salida_total: int = 0
    bytes_error_total: int = 0
    sha256_salida_completa: str = ""
    sha256_error_completo: str = ""

def ejecutar(comando: Sequence[str], *,
             raiz: Path | None = None,
             limite_segundos: float = 60.0,
             senal_cancelacion: SenalCancelacion | None = None,
             al_linea: Callable[[str, str], None] | None = None) -> ResultadoProceso: ...

# tramalia/core/operaciones.py
def cerrar_proyecto(raiz: Path, id_tarea: str, *, agente: str = "",
                    revisor: str = "", modelo: str = "",
                    excepciones: Sequence[ExcepcionFallo] = ()) -> ResultadoCierre: ...

# tramalia/core/tablero.py
class ServicioTablero:
    def __init__(self, raiz: Path, *,
                 operacion_cerrar: Callable[..., ResultadoCierre] = cerrar_proyecto): ...
    def cerrar(self, id_tarea: str, *, agente: str = "", revisor: str = "",
               modelo: str = "", excepciones: Sequence[ExcepcionFallo] = ()) -> ResultadoCierre: ...
```

No reordenar los campos de `ResultadoProceso`: existen usos posicionales. Añadir sólo kwargs opcionales a `ejecutar`. `InstantaneaTablero` continúa `frozen=True, slots=True`; cualquier campo nuevo va al final con valor predeterminado.

Cada canal de `ResultadoProceso` conserva como máximo 8 MiB (cabecera + cola con
marca intermedia) mientras sigue drenando el pipe para evitar bloqueos; los dos
booleanos indican pérdida del excedente. En paralelo cuenta todos los bytes y
calcula SHA-256 incremental de la salida completa. Cada llamada `al_linea` recibe
como máximo 8192 caracteres y una marca explícita de truncamiento. Así una
herramienta hostil no convierte el resultado ni la cola de UI en memoria
ilimitada sin ocultar que faltan bytes.

Cuando una puerta supera el límite, su archivo de evidencia contiene el extracto
acotado con marcador y `metadatos.json` registra truncamiento, bytes totales y
SHA-256 de cada canal completo; nunca presenta el extracto como salida cruda
íntegra. Estos campos opcionales amplían v1 de forma compatible y la
documentación explica el límite. La prueba de >20 MiB verifica hash/contadores
contra el productor y el pack publicado.

```python
# campos nuevos al final de tramalia.core.modelos.ResultadoPuerta
salida_estandar_truncada: bool = False
error_estandar_truncado: bool = False
bytes_salida_estandar_total: int = 0
bytes_error_estandar_total: int = 0
bytes_salida_estandar_publicados: int = 0
bytes_error_estandar_publicados: int = 0
sha256_salida_estandar_completa: str = ""
sha256_error_estandar_completo: str = ""
```

`hash_salida` conserva exactamente su significado v1: SHA-256 de los bytes del
archivo/extracto combinado que sí se publica en el pack. Los ocho campos nuevos
describen la corriente original por canal. En JSON viven bajo
`comandos[].salida_proceso.stdout|stderr` con claves `truncada`, `bytes_total`,
`bytes_publicados` y `sha256_completa`. Validar enteros no negativos,
`bytes_publicados <= bytes_total`, coherencia del booleano y SHA-256 hexadecimal
de 64 caracteres. Un pack v1 histórico sin `salida_proceso` sigue leyendo con
defaults; si el objeto existe debe estar completo y válido, nunca parcialmente.

## Interfaces nuevas

```python
# tramalia/core/cancelacion.py
class OperacionCancelada(Exception):
    pass

class SenalCancelacion:
    def solicitar(self) -> None: ...
    @property
    def solicitada(self) -> bool: ...
    def esperar(self, segundos: float | None = None) -> bool: ...
    def exigir_no_cancelada(self) -> None: ...
```

La señal es one-shot. No expone `limpiar()`; cada operación crea una señal nueva.

```python
# tramalia/core/modelos_operacion.py
class ValorTipoEventoOperacion(StrEnum):
    INICIADA = "iniciada"
    PASO_INICIADO = "paso_iniciado"
    SALIDA = "salida"
    PASO_TERMINADO = "paso_terminado"
    PUBLICANDO = "publicando"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"
    FALLIDA = "fallida"

class ValorEstadoOperacionCierre(StrEnum):
    COMPLETADA = "completada"
    CANCELADA = "cancelada"
    FALLIDA = "fallida"

@dataclass(frozen=True, slots=True)
class HuellaInsumoCierre:
    ruta_relativa: str
    existe: bool
    sha256: str | None

@dataclass(frozen=True, slots=True)
class PlanCierre:
    id_operacion: str
    raiz: Path
    id_tarea: str
    agente: str
    revisor: str
    modelo: str
    excepciones: tuple[ExcepcionFallo, ...]
    puertas: tuple[PuertaCalidad, ...]
    bloqueos_previos: tuple[str, ...]
    limite_cancelacion: ValorTipoEventoOperacion
    insumos: tuple[HuellaInsumoCierre, ...]
    huella_insumos: str

@dataclass(frozen=True, slots=True)
class EventoOperacion:
    id_operacion: str
    tipo: ValorTipoEventoOperacion
    instante_utc: datetime
    paso: str | None = None
    datos: Mapping[str, str | int | float | bool | None] = field(default_factory=dict)

@dataclass(frozen=True, slots=True)
class ResultadoOperacionCierre:
    estado: ValorEstadoOperacionCierre
    resultado: ResultadoCierre | None = None
    error: Exception | None = None
```

Invariantes: `COMPLETADA` tiene `resultado` y no `error`; `CANCELADA` no tiene ninguno; `FALLIDA` tiene `error` y no resultado.

`PlanCierre.limite_cancelacion` vale `PUBLICANDO`: la señal se comprueba antes de
emitir ese evento y deja de aceptarse desde ese punto. Todos los eventos de una
ejecución usan exactamente el `id_operacion` del plan. `datos` se copia a una
vista inmutable de escalares JSON; `SALIDA` exige `canal` (`stdout` o `stderr`) y
`texto`, y los eventos de paso usan `actual` y `total`. Las pruebas rechazan IDs,
canales o datos incongruentes y prueban correlación con dos operaciones
intercaladas.

`insumos` inventaría por ruta portable todos los archivos que
`preparar_cierre()` leyó para decidir proyecto, tarea, puertas, métricas y
política (incluida la ausencia esperada); `huella_insumos` agrega
determinísticamente esas entradas. La ejecución vuelve a construir el inventario
y exige igualdad antes de iniciar puertas y otra vez antes de cruzar
`PUBLICANDO`. Creación, borrado o cambio de cualquier insumo falla tipado y no
publica; no se usa mtime como identidad.

```python
# tramalia/core/instalador.py
class ValorEstadoPlanInstalacion(StrEnum):
    COMPLETADA = "completada"
    CANCELADA = "cancelada"
    FALLIDA = "fallida"

@dataclass(frozen=True, slots=True)
class PasoPlanInstalacion:
    id_paso: str
    herramienta: str
    etiqueta: str
    opcion: OpcionInstalacion
    prerrequisitos: tuple[str, ...]
    efectos: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class PlanInstalacion:
    id_operacion: str
    sistema: str
    pasos: tuple[PasoPlanInstalacion, ...]
    instrucciones_manuales: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class ResultadoPasoInstalacion:
    id_paso: str
    resultado: ResultadoProceso

@dataclass(frozen=True, slots=True)
class ResultadoPlanInstalacion:
    id_operacion: str
    estado: ValorEstadoPlanInstalacion
    total_pasos: int
    resultados: tuple[ResultadoPasoInstalacion, ...]

def preparar_instalacion(
    herramientas: Sequence[Herramienta], *, sistema: str | None = None
) -> PlanInstalacion: ...
def ejecutar_instalacion_observable(
    plan: PlanInstalacion, *,
    senal_cancelacion: SenalCancelacion | None = None,
    al_evento: Callable[[EventoOperacion], None] | None = None,
) -> ResultadoPlanInstalacion: ...
```

La preparación es pura y sólo incorpora opciones automatizables ya resueltas;
los comandos manuales quedan informativos. La ejecución usa
`core.procesos.ejecutar`, conserva resultados terminados, no inicia pasos después
de cancelar/fallar y emite eventos con el ID del plan. `tramalia/core/instalador.py`
es el módulo canónico en español y contiene toda la implementación nueva.
`tramalia/core/installer.py` queda durante la BETA como shim documentado y
deprecado que sólo reexporta nombres históricos —incluido `InstallOption` como
alias de `OpcionInstalacion`— y delega sin lógica propia. Código nuevo y pruebas
activas importan `tramalia.core.instalador`; el shim se prueba sólo mediante un
contrato de compatibilidad y se excluye de la navegación/API de mkdocstrings.
Ninguna pantalla vuelve a usar `_RUNTIME_NAME`, `_resolver` ni `Popen`.

Invariantes: IDs de paso únicos y no vacíos; `COMPLETADA` contiene exactamente
`total_pasos` resultados exitosos; `CANCELADA` termina en un
`ResultadoProceso(cancelado=True, codigo_salida=130)` y puede conservar éxitos
anteriores; `FALLIDA` termina en un resultado no exitoso y no cancelado. Ningún
estado contiene resultados de pasos posteriores al primero cancelado/fallido y
el `id_operacion` del resultado coincide con plan/eventos.

```python
# tramalia/core/evidencia.py
@dataclass(frozen=True, slots=True)
class AnomaliaRaizBitacora:
    nombre_seguro: str
    codigo: str

@dataclass(frozen=True, slots=True)
class PaginaBitacora:
    entradas: tuple[EntradaBitacora, ...]
    siguiente_cursor: str | None
    anomalias_raiz: tuple[AnomaliaRaizBitacora, ...] = ()
    total_anomalias_raiz: int = 0

def leer_bitacora(raiz: Path) -> list[EntradaBitacora]: ...
def leer_pagina_bitacora(
    raiz: Path, *, limite: int = 50, cursor: str | None = None
) -> PaginaBitacora: ...
```

Los paquetes paginables son directorios cuyo nombre cumple `_ID_PAQUETE`, aunque
sus metadatos estén ausentes o corruptos. Ese ID formal ya contiene UTC con
microsegundos y un sufijo aleatorio, por lo que el orden canónico es
`id_paquete` descendente y no depende de `cerrado_utc` (que es `None` en una
entrada inválida) ni de `mtime`. En la primera llamada el cursor opaco y
versionado guarda `corte_superior` (el mayor ID formal observado) y
`despues_de` (el último ID devuelto); las continuaciones aceptan sólo
`id_paquete <= corte_superior` e `id_paquete < despues_de`. Así, un paquete más
nuevo publicado durante la navegación no causa duplicados ni saltos y aparece
sólo al refrescar. El cursor se valida antes de leer y nunca contiene rutas.

Los nombres de directorio que no cumplen `_ID_PAQUETE` no se presentan como
paquetes inventados: la primera página los resume en `anomalias_raiz`, con
nombre base saneado/truncado, código tipado y conteo total. Se excluyen staging
`.tmp-*`; la lista visible se limita a 50 anomalías para mantener memoria y UI
acotadas. `leer_bitacora()` conserva exactamente su firma y retorno históricos,
incluida su representación actual de entradas inválidas; la TUI usa
exclusivamente la API paginada.

```python
# tramalia/core/tablero.py
@dataclass(frozen=True, slots=True)
class PuertaDetalleBitacora:
    nombre: str
    estado: ValorResultadoPuerta
    codigo_salida: int | None

@dataclass(frozen=True, slots=True)
class ExcepcionDetalleBitacora:
    control: str
    justificacion: str

@dataclass(frozen=True, slots=True)
class FalloLecturaBitacora:
    codigo: str
    mensaje: str
    sugerencia: str

@dataclass(frozen=True, slots=True)
class DetalleBitacoraTablero:
    id_paquete: str
    id_tarea: str | None
    resultado: ValorEstadoCierre | None
    puertas: tuple[PuertaDetalleBitacora, ...]
    excepciones: tuple[ExcepcionDetalleBitacora, ...]
    agente: str
    revisor: str
    modelo: str
    ruta_evidencia: str
    ruta_traspaso: str | None
    fallo_lectura: FalloLecturaBitacora | None = None
    texto_crudo: str | None = None
```

El detalle nunca lanza datos persistidos sin validar a la UI. Las rutas son
portables/confinadas, el texto crudo es opt-in y <=1 MiB, y un pack inválido se
representa con `fallo_lectura` tipado sin inventar tarea/resultado. Las pruebas
cubren todos los campos de un pack válido, JSON inválido, traversal/symlink,
archivo enorme, pack desaparecido y `incluir_crudo=False` predeterminado.

```python
# tramalia/core/preparacion_proyecto.py
class ValorTipoPreparacionProyecto(StrEnum):
    INICIALIZAR = "inicializar"
    ADOPTAR = "adoptar"
    ACTUALIZAR = "actualizar"
    REPARAR = "reparar"

class ValorAccionArchivo(StrEnum):
    CREAR = "crear"
    ACTUALIZAR = "actualizar"
    CONSERVAR = "conservar"

@dataclass(frozen=True, slots=True)
class CambioPreparacionProyecto:
    ruta: Path
    accion: ValorAccionArchivo
    descripcion: str
    hash_antes: str | None
    hash_despues: str

@dataclass(frozen=True, slots=True)
class PlanPreparacionProyecto:
    raiz: Path
    tipo: ValorTipoPreparacionProyecto
    version_objetivo: str
    estado_origen: ValorEstadoProyecto
    cambios: tuple[CambioPreparacionProyecto, ...]
    huella_origen: str

@dataclass(frozen=True, slots=True)
class ResultadoPreparacionProyecto:
    tipo: ValorTipoPreparacionProyecto
    creados: tuple[Path, ...]
    actualizados: tuple[Path, ...]
    conservados: tuple[Path, ...]

def preparar_proyecto(raiz: Path, tipo: ValorTipoPreparacionProyecto,
                      version_objetivo: str) -> PlanPreparacionProyecto: ...
def aplicar_preparacion(
    plan: PlanPreparacionProyecto, *,
    senal_cancelacion: SenalCancelacion | None = None,
    al_cruzar_limite_cancelacion: Callable[[], None] | None = None,
) -> ResultadoPreparacionProyecto: ...
```

`preparar_proyecto` no escribe. `aplicar_preparacion` vuelve a verificar estado/huella y bytes renderizados, confina rutas, no sobrescribe código de usuario y usa el mismo renderizado canónico del scaffold; una vista previa nunca es autorización para aplicar sobre archivos que cambiaron. Es cancelable durante revalidación/preparación de temporales. Inmediatamente antes del primer `os.replace` comprueba la señal y llama sincrónicamente `al_cruzar_limite_cancelacion`; desde ahí no vuelve a cancelar y salida queda bloqueada hasta completar o terminar rollback. Si el callback falla, limpia temporales y no escribe.

```python
# Contratos producidos y verificados por el Plan 03c. Este plan sólo los importa.
from tramalia.core.auditoria_habilidades import ResultadoAuditoriaHabilidad
from tramalia.core.modelos_habilidades import (
    ConfiguracionHabilidadesProyecto,
    EstadoHabilidad,
    EventoOperacionHabilidades,
    PlanCambioHabilidades,
    PlanResolucionHabilidades,
    ResultadoCambioHabilidades,
    SolicitudCambioHabilidades,
    ValorActivacionHabilidad,
    ValorActualizacionHabilidad,
    ValorCompatibilidadHabilidad,
    ValorInstalacionHabilidad,
    ValorIntegridadHabilidad,
    ValorObligatoriedadHabilidad,
)
from tramalia.core.servicio_habilidades import ServicioHabilidades
```

`ServicioHabilidades` es la única entrada de las superficies para `listar`,
`explicar`, `planificar`, `activar`, `desactivar`, `aplicar_perfil`, `auditar`,
`rehidratar` y `actualizar`. Las firmas y resultados exactos son los aprobados
por `tests/contratos/test_entrega_03c.py`; 03b no crea un segundo protocolo ni
adapta los datos mediante diccionarios libres. `listar` y `explicar` entregan
`EstadoHabilidad`, que compone metadata, decisión, observación y procedencia. La
UI presenta por separado las seis dimensiones: activación, obligatoriedad,
compatibilidad, instalación, integridad y actualización.

Toda intención mutante se expresa como `SolicitudCambioHabilidades` y se entrega
a `planificar()` para obtener `PlanCambioHabilidades`. Su `huella`, sus huellas
de insumos y su diff de materialización son la confirmación estable. Ejecutar el
método correspondiente de `ServicioHabilidades` devuelve
`ResultadoCambioHabilidades`; sólo ese resultado contiene `aplicada`. Los
eventos de progreso son `EventoOperacionHabilidades` y se traducen al canal de
interfaz sin convertirlos en eventos de dominio genéricos ni reconstruirlos desde
texto. Bloqueos, dependencias, conflictos, herramientas faltantes, permisos,
riesgo, razón y origen se muestran desde los modelos recibidos, nunca se
recalculan en widgets o presentadores.

Las consultas `listar`, `explicar`, `planificar` y `auditar` son puras y sin red;
sólo rehidratar/actualizar pueden usar red por consentimiento explícito. Visitar
la pantalla, filtrar o cambiar selección nunca consulta la red. Activar,
desactivar y aplicar perfil siempre siguen solicitud, plan, diff, confirmación
por huella, ejecución tipada y relectura real. Una habilidad obligatoria sólo
ofrece desactivación cuando el usuario completa la `ExcepcionHabilidad` que
valida 03c; la TUI no relaja esa regla ni fabrica una excepción predeterminada.

```python
# tramalia/core/configuracion.py
@dataclass(frozen=True, slots=True)
class PlanCambioProveedorContexto:
    id_operacion: str
    proveedor: str
    ruta_configuracion: Path
    sha256_antes: str
    contenido_despues: bytes

@dataclass(frozen=True, slots=True)
class ResultadoCambioProveedorContexto:
    id_operacion: str
    proveedor: str
    cambiado: bool

def preparar_cambio_proveedor_contexto(
    raiz: Path, proveedor: str
) -> PlanCambioProveedorContexto: ...

def aplicar_cambio_proveedor_contexto(
    plan: PlanCambioProveedorContexto,
    *,
    senal_cancelacion: SenalCancelacion | None = None,
    al_cruzar_limite_cancelacion: Callable[[EventoOperacion], None] | None = None,
) -> ResultadoCambioProveedorContexto: ...
```

El plan de proveedor confina `ruta_configuracion`, serializa JSON determinista y
no escribe. Aplicar exige SHA original idéntico, comprueba señal, invoca una vez
la frontera y hace un único reemplazo atómico; callback fallido o drift deja los
bytes originales. Resultado `cambiado=False` sólo es válido si los bytes ya eran
idénticos y aun así revalida la huella.

```python
# tramalia/core/operaciones.py
def preparar_cierre(
    raiz: Path,
    id_tarea: str,
    *,
    agente: str = "",
    revisor: str = "",
    modelo: str = "",
    excepciones: Sequence[ExcepcionFallo] = (),
) -> PlanCierre: ...
def ejecutar_cierre_observable(
    plan: PlanCierre,
    *,
    senal_cancelacion: SenalCancelacion | None = None,
    al_evento: Callable[[EventoOperacion], None] | None = None,
    al_cruzar_limite_cancelacion: Callable[[EventoOperacion], None] | None = None,
) -> ResultadoOperacionCierre: ...
```

`al_cruzar_limite_cancelacion` no es un observador best-effort: se invoca de
forma síncrona exactamente una vez con el evento `PUBLICANDO`, después de la
última comprobación de señal y antes de cualquier escritura publicable. Debe
marcar el coordinador como bloqueado antes de retornar; si falla, el núcleo
aborta antes de publicar. Los demás eventos usan `al_evento` y sus fallos no
alteran el dominio.

```python
# tramalia/interfaz/coordinador_operaciones.py
@dataclass(frozen=True, slots=True)
class PermisoMutacion:
    id_operacion: str
    nombre: str
    senal_cancelacion: SenalCancelacion

@dataclass(frozen=True, slots=True)
class SolicitudLectura:
    grupo: str
    generacion: int
    iniciar_ahora: bool

class CoordinadorOperaciones:
    def iniciar_mutacion(self, nombre: str) -> PermisoMutacion: ...
    def marcar_publicando(self, permiso: PermisoMutacion) -> None: ...
    def finalizar_mutacion(self, permiso: PermisoMutacion) -> None: ...
    def solicitar_cancelacion(self) -> bool: ...
    def solicitar_lectura(self, grupo: str) -> SolicitudLectura: ...
    def finalizar_lectura(self, grupo: str, generacion: int) -> SolicitudLectura | None: ...
    def es_lectura_vigente(self, grupo: str, generacion: int) -> bool: ...
    def cerrar_lecturas(self) -> None: ...
    @property
    def estado_salida(self) -> Literal["libre", "confirmar_cancelacion", "bloqueada"]: ...
```

```python
# tramalia/interfaz/texto_seguro.py
def normalizar_texto_externo(valor: object, *, maximo_linea: int = 8192) -> str: ...
def validar_url_externa(url: str, *, permitir_http: bool = False) -> str: ...

class BuferCircularTexto:
    def __init__(self, maximo_bytes: int = 1_048_576) -> None: ...
    def agregar(self, texto: object) -> None: ...
    def obtener(self) -> str: ...
```

```python
# tramalia/interfaz/canal_eventos.py
class CanalEventosInterfaz:
    def __init__(self, maximo_eventos_salida: int = 256) -> None: ...
    def publicar(self, evento: EventoOperacion) -> None: ...
    def extraer_disponibles(self) -> tuple[EventoOperacion, ...]: ...
```

El canal nunca descarta eventos de ciclo de vida. Sólo coalesce eventos
`SALIDA` cuando alcanza el límite y agrega un evento resumen con cantidad de
líneas/bytes omitidos; el texto conservado sigue pasando por el buffer circular
de 1 MiB. No usar `queue.Queue()` sin `maxsize` ni una lista creciente.

```python
# tramalia/interfaz/adaptabilidad.py
@dataclass(frozen=True, slots=True)
class PerfilTerminal:
    ancho: int
    alto: int
    perfil_ancho: Literal["compacto", "medio", "ancho"]
    perfil_alto: Literal["bajo", "normal", "alto"]
    soportado: bool

def resolver_perfil_terminal(ancho: int, alto: int) -> PerfilTerminal: ...
```

---

### Task 1: Estabilizar el baseline TUI y fijar dependencias compatibles

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Modify if the new contracts fail: `tramalia/mcp_server.py`, `tramalia/core/tablero.py`
- Modify: `tests/interfaz/test_interfaz_terminal.py`
- Create: `tests/interfaz/test_hermeticidad_terminal.py`
- Modify: `tests/integracion/test_mcp_operaciones.py`, `tests/unidad/test_tablero.py`

**Interfaces:**
- Consumes: Textual 8.2.8 actualmente resuelto.
- Produces: rango compatible `<9`, snapshot plugin fijo, reproducción estable del fallo dependiente del orden, transporte MCP sin stdout ajeno y una sola sonda por dato de snapshot.

- [ ] **Step 1: Reproducir el fallo combinado sin ocultarlo con reintentos**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_tablero.py tests/unidad/test_puertas_calidad.py tests/integracion/test_operaciones.py tests/interfaz/test_interfaz_terminal.py -q -x
uv run --no-sync pytest tests/interfaz/test_interfaz_terminal.py -q --count=10
```

Expected: documentar el primer estado divergente del formulario/foco. No añadir `sleep`, `flaky`, retry ni timeout mayor.

- [ ] **Step 2: Crear una prueba roja de hermeticidad y espera por condición**

La prueba ejecuta dos aplicaciones consecutivas con servicios falsos distintos y verifica que workers, foco, inputs, eventos y estado de clase no atraviesan instancias. Reemplazar esperas temporales por una utilidad local que espera una condición observable mediante `pilot.pause()` con límite.

- [ ] **Step 3: Cerrar los dos contratos residuales de Task 4**

Ampliar el test MCP por transporte stdio para invocar `doctor` y `build_context` con implementaciones falsas que intentan escribir un diagnóstico: stdout debe seguir siendo JSON-RPC válido y todo diagnóstico propio se redirige a stderr/logger. No envolver el transporte entero con `redirect_stdout`, porque ocultaría el protocolo; corregir el productor concreto que imprime.

En `test_tablero.py`, inyectar contadores en `doctor.diagnose`, detección de stack, estado de proyecto, proveedor y lectura de bitácora. Cada dato de una instantánea se obtiene una sola vez y se reutiliza; no volver a sondear mediante helpers que ya están contenidos en `Report`. Corregir únicamente duplicaciones demostradas por el test.

Run: `uv run --no-sync pytest tests/integracion/test_mcp_operaciones.py tests/unidad/test_tablero.py -q`

Expected: PASS y ninguna salida propia contamina stdout del servidor MCP.

- [ ] **Step 4: Fijar dependencias sin hacer Textual obligatoria**

```toml
[project.optional-dependencies]
tui = ["textual>=8.2,<9"]
full = ["mcp>=1.2", "textual>=8.2,<9"]
dev = ["pytest>=8", "mcp>=1.2", "textual>=8.2,<9"]

[dependency-groups]
desarrollo = [
    "pytest>=8",
    "pytest-cov>=6",
    "pytest-timeout>=2",
    "pytest-repeat>=0.9",
    "ruff>=0.12",
    "mypy>=1.16",
    "build>=1.2",
    "twine>=6",
    "pytest-textual-snapshot==1.1.0",
]
```

Run: `uv lock --python 3.11 && uv sync --locked --group desarrollo --all-extras`

Expected: Textual permanece 8.2.8 o una 8.x compatible; nunca 9.x.

- [ ] **Step 5: Corregir la fuga causal y verificar baseline**

No modularizar aún. Corregir sólo la fuga demostrada: estado por instancia, worker pendiente o condición de foco. Ejecutar ambos comandos del Step 1 y el archivo nuevo.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock tramalia/mcp_server.py tramalia/core/tablero.py tests/interfaz tests/integracion/test_mcp_operaciones.py tests/unidad/test_tablero.py
git commit -m "test: estabilizar contratos de interfaz textual"
```

### Task 2: Modelar cancelación one-shot y terminar árboles de procesos

**Files:**
- Create: `tramalia/core/cancelacion.py`
- Create: `tramalia/core/modelos_operacion.py`
- Modify: `tramalia/core/procesos.py`
- Create: `tests/unidad/test_modelos_operacion.py`
- Create: `tests/integracion/test_procesos.py`

**Interfaces:**
- Consumes: contrato posicional de `ResultadoProceso`.
- Produces: señal one-shot, eventos/resultados tipados y cancelación de proceso + descendientes.

- [ ] **Step 1: Escribir pruebas rojas de invariantes y señal**

Probar que llamadas repetidas a `solicitar()` son idempotentes, `esperar(0)` refleja el estado, `exigir_no_cancelada()` lanza `OperacionCancelada` y no existe método `limpiar`. Parametrizar las 12 combinaciones estado×presencia de resultado×presencia de error de `ResultadoOperacionCierre`: sólo tres son válidas y las otras nueve fallan en `__post_init__`. Probar además que un evento exige ID no vacío, UTC con zona, canal válido en `SALIDA`, datos JSON escalares e inmutables, y que `PlanCierre.limite_cancelacion` es `PUBLICANDO`.

- [ ] **Step 2: Implementar modelos puros**

No importar Textual, Rich, subprocess ni UI en estos módulos. Usar `threading.Event` internamente y UTC con zona en eventos creados por operaciones.

- [ ] **Step 3: Escribir prueba de integración padre/nieto**

Un helper Python padre crea un hijo de larga duración, escribe ambos PID y produce líneas parciales. La prueba cancela y otra agota timeout; ambas verifican que padre e hijo terminaron, que la salida previa se conserva y que los códigos son 130/cancelado y 124/agotado respectivamente. Otro helper emite más de 20 MiB por stdout/stderr, incluida una línea única enorme: el proceso no se bloquea, cada resultado ocupa <=8 MiB, marca truncamiento, conserva bytes/hash completos y cada callback ocupa <=8192 caracteres. Un callback que lanza en la primera línea se registra, ambos pipes se drenan y el proceso termina con su resultado de dominio; nunca se propaga desde el hilo lector.

- [ ] **Step 4: Cambiar `ejecutar` a Popen con grupo propio**

Firma final:

```python
def ejecutar(
    comando: Sequence[str],
    *,
    raiz: Path | None = None,
    limite_segundos: float = 60.0,
    senal_cancelacion: SenalCancelacion | None = None,
    al_linea: Callable[[str, str], None] | None = None,
) -> ResultadoProceso:
```

POSIX: `start_new_session=True`, `os.killpg(SIGTERM)`, espera breve y `SIGKILL`. Windows: `CREATE_NEW_PROCESS_GROUP` y `taskkill /PID <pid> /T /F` sin `shell=True`; `.cmd/.bat` conserva resolución por `cmd /c`. Drenar ambos pipes concurrentemente, contar/hashar bytes y conservar buffers acotados aunque se descarte el excedente; stdout y stderr permanecen separados en el resultado. Los callbacks reciben fragmentos acotados y nunca retienen la salida completa. Capturar sus `Exception` dentro del lector, registrar sin stdout y continuar drenando; no capturar `BaseException`.

- [ ] **Step 5: Verificar regresiones de procesos/integraciones**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_modelos_operacion.py tests/integracion/test_procesos.py tests/unidad/test_integraciones.py tests/test_v017.py -q
```

Expected: PASS en Windows; `test_procesos.py` se marcará `integracion` para la matriz Windows/Linux/macOS.

- [ ] **Step 6: Commit**

```bash
git add tramalia/core/cancelacion.py tramalia/core/modelos_operacion.py tramalia/core/procesos.py tests
git commit -m "feat: cancelar arboles de procesos de forma observable"
```

### Task 3: Hacer puertas y cierre observables sin romper la fachada síncrona

**Files:**
- Modify: `tramalia/core/puertas_calidad.py`
- Modify: `tramalia/core/operaciones.py`
- Modify: `tramalia/core/modelos.py`
- Modify: `tramalia/core/evidencia.py`
- Modify: `tests/unidad/test_puertas_calidad.py`
- Modify: `tests/integracion/test_operaciones.py`
- Modify: `tests/integracion/test_evidencia.py`
- Modify: `tests/contratos/test_operaciones_superficies.py`

**Interfaces:**
- Consumes: señal/modelos de Task 2 y publicación atómica existente.
- Produces: callbacks de puertas, `preparar_cierre`, `ejecutar_cierre_observable`; fachada intacta.

- [ ] **Step 1: Escribir pruebas rojas de puertas observables**

Ampliar `ejecutar_puertas` sólo con kwargs:

```python
def ejecutar_puertas(
    raiz: Path,
    puertas: Sequence[PuertaCalidad],
    *,
    verificar_configuracion: Callable[[], None] | None = None,
    senal_cancelacion: SenalCancelacion | None = None,
    al_iniciar_puerta: Callable[[PuertaCalidad, int, int], None] | None = None,
    al_linea: Callable[[PuertaCalidad, str, str], None] | None = None,
    al_terminar_puerta: Callable[[PuertaCalidad, ResultadoPuerta], None] | None = None,
) -> EjecucionPuertas:
```

Probar secuencia exacta iniciar→salidas→terminar, que el kwarg histórico `verificar_configuracion` se invoca antes y después de cada proceso, cancelación que no inicia pendientes, timeout conservado y continuación tras excepción ordinaria. `OperacionCancelada` se captura antes de `Exception` y se vuelve a lanzar; no se convierte en puerta roja.

- [ ] **Step 2: Implementar callbacks manteniendo contratos históricos**

Conservar orden de puertas, timeout 900, guardias antes/después, hashes, UTC, duración y concatenación final. Ejecutar todo `tests/unidad/test_puertas_calidad.py`.

- [ ] **Step 3: Escribir pruebas rojas de cierre observable**

Cubrir:

1. completada: `iniciada`, cada paso, `publicando`, `completada`, mismo `ResultadoCierre`, un único ID correlacionado y datos exactos de paso/canal;
2. cancelada durante una puerta: sin `publicando`, sin directorio nuevo en `.tramalia/evidencia`;
3. señal solicitada desde callback `publicando`: termina completada, porque la publicación ya es indivisible;
4. creación/borrado/cambio de un insumo entre `preparar_cierre()` y ejecución, o durante una puerta antes de publicar: la huella portable falla tipada y no publica;
5. un observador que falla no ejecuta puertas dos veces ni altera la decisión/publicación; el fallo del observador se registra por logger y el resultado de dominio prevalece;
6. `cerrar_proyecto()` sigue retornando el objeto esperado y propagando `ErrorTramalia` existente.
7. una barrera dentro de `al_cruzar_limite_cancelacion` demuestra que el coordinador ya responde `bloqueada` antes de que el núcleo pueda iniciar la publicación; una señal solicitada después de cruzarla no interrumpe el reemplazo atómico.

- [ ] **Step 4: Implementar una única ruta de cierre**

`cerrar_proyecto()` construye plan, llama a la ruta observable sin callback y:

- retorna `resultado` cuando completa;
- vuelve a lanzar el mismo `error` cuando falla.

La fachada síncrona no acepta ni crea un token externo cancelable: conserva su
firma exacta, consume internamente los eventos y sólo puede finalizar completa o
fallida conforme al contrato histórico. La cancelación cooperativa existe
exclusivamente en `ejecutar_cierre_observable()`.

Toda validación se repite al ejecutar; el plan es vista previa, no autorización duradera. La última comprobación de cancelación ocurre inmediatamente antes de crear `PUBLICANDO`; luego se ejecuta el callback síncrono de cruce y sólo al retornar comienza `_publicar()`. No comprobar la señal dentro de `_publicar()` ni entre escritura temporal y `os.replace`.

Los callbacks `al_evento` y los callbacks informativos de puertas son observadores: invocarlos mediante un helper que captura `Exception`, registra el error sin escribir stdout y continúa; nunca capturar `KeyboardInterrupt`/`SystemExit`. Esta regla **no** aplica a `al_cruzar_limite_cancelacion`: es una barrera síncrona fail-closed y su excepción aborta antes de publicar. La TUI entrega eventos informativos al `CanalEventosInterfaz` acotado y no modifica widgets desde el hilo del núcleo.

- [ ] **Step 5: Verificar integración y superficies**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_puertas_calidad.py tests/integracion/test_operaciones.py tests/integracion/test_evidencia.py tests/contratos/test_operaciones_superficies.py -q
```

Expected: PASS; ninguna superficie importa `_publicar` ni `ejecutar_puertas` directamente.

- [ ] **Step 6: Commit**

```bash
git add tramalia/core/puertas_calidad.py tramalia/core/operaciones.py tramalia/core/modelos.py tramalia/core/evidencia.py tests
git commit -m "feat: observar y cancelar el cierre gobernado"
```

### Task 4: Acotar auditoría y ampliar ServicioTablero sin recalcular política

**Files:**
- Modify: `tramalia/core/evidencia.py`
- Modify: `tramalia/core/tablero.py`
- Modify: `tests/unidad/test_tablero.py`
- Modify: `tests/integracion/test_traspaso_bitacora.py`

**Interfaces:**
- Consumes: `preparar_cierre`, `ejecutar_cierre_observable`, bitácora canónica.
- Produces: detalle lazy/paginado, métodos observables y compatibilidad de `cerrar` por identidad.

- [ ] **Step 1: Escribir pruebas rojas de carga lazy**

El snapshot sólo enumera IDs y abre `metadatos.json` de los elementos de la
primera `PaginaBitacora`, no de todos los packs. Los metadatos corruptos siguen
produciendo una `EntradaBitacora` inválida dentro del mismo orden formal.
`obtener_detalle_bitacora(id_paquete)` carga una entrada seleccionada, valida
confinamiento y limita contenido. `leer_bitacora(raiz)` mantiene exactamente
firma/retorno; `leer_pagina_bitacora(raiz, *, limite=50, cursor=None)` devuelve
entradas, anomalías raíz y cursor siguiente. Probar límites 1/50/200, cursor
malformado/fuera de rango, mezcla de paquetes válidos e inválidos, directorios
no formales reportados como anomalía, e inserción concurrente de un ID formal
más nuevo entre páginas. Concatenar todas las páginas debe producir exactamente
el snapshot inicial, en orden descendente y sin duplicados ni saltos; el nuevo
ID sólo aparece después de refrescar sin cursor.

- [ ] **Step 2: Ampliar servicio por delegación**

```python
class ServicioTablero:
    def preparar_cierre(self, id_tarea: str, *, agente: str = "", revisor: str = "",
                        modelo: str = "", excepciones: Sequence[ExcepcionFallo] = ()) -> PlanCierre: ...
    def cerrar_observable(self, plan: PlanCierre, *,
                          senal_cancelacion: SenalCancelacion | None = None,
                          al_evento: Callable[[EventoOperacion], None] | None = None,
                          al_cruzar_limite_cancelacion: Callable[[EventoOperacion], None] | None = None) -> ResultadoOperacionCierre: ...
    def leer_pagina_bitacora(self, *, limite: int = 50,
                             cursor: str | None = None) -> PaginaBitacora: ...
    def obtener_detalle_bitacora(self, id_paquete: str, *,
                                 incluir_crudo: bool = False) -> DetalleBitacoraTablero: ...
```

`cerrar()` conserva el callable inyectado y retorna exactamente el mismo objeto para mantener el test de identidad. `cerrar_observable()` delega también el callback síncrono de cruce sin envolverlo como observador; una prueba con barrera demuestra que llega al núcleo. Los métodos nuevos aceptan callables inyectables en `__init__` al final, con defaults. `InstantaneaTablero` añade al final `siguiente_cursor_bitacora: str | None = None`; no precarga detalles y la pantalla solicita páginas sólo mediante el servicio.

- [ ] **Step 3: Verificar servicio y bitácora**

Run: `uv run --no-sync pytest tests/unidad/test_tablero.py tests/integracion/test_traspaso_bitacora.py -q`

Expected: PASS; snapshot no crece linealmente en lecturas de metadatos.

- [ ] **Step 4: Commit**

```bash
git add tramalia/core/evidencia.py tramalia/core/tablero.py tests
git commit -m "perf: cargar auditoria y cierre bajo demanda"
```

### Task 5: Crear coordinación global, adaptabilidad y seguridad de texto

**Files:**
- Create: `tramalia/interfaz/__init__.py`
- Create: `tramalia/interfaz/coordinador_operaciones.py`
- Create: `tramalia/interfaz/canal_eventos.py`
- Create: `tramalia/interfaz/adaptabilidad.py`
- Create: `tramalia/interfaz/texto_seguro.py`
- Modify: `tramalia/cli/renderizado.py`
- Create: `tests/unidad/test_coordinador_operaciones.py`
- Create: `tests/unidad/test_canal_eventos.py`
- Create: `tests/unidad/test_adaptabilidad.py`
- Create: `tests/unidad/test_texto_seguro.py`
- Create: `tests/interfaz/test_seguridad_cli.py`

**Interfaces:**
- Consumes: `SenalCancelacion`.
- Produces: primitivas puras usadas por todas las pantallas y presentadores.

- [ ] **Step 1: Escribir pruebas rojas del coordinador**

Probar exclusión global de segunda mutación aunque el nombre difiera,
cancelación idempotente, publicación que cambia `estado_salida` a bloqueada y
finalización con permiso incorrecto rechazada. Para lecturas, lanzar diez
solicitudes rápidas del mismo grupo con barreras: la primera inicia, las ocho
intermedias se reemplazan por una única pendiente, la generación 1 deja de ser
vigente, y al finalizarla se devuelve sólo la solicitud 10 para iniciar. Medir
que la concurrencia máxima por grupo sea 1 y que únicamente la décima pueda
actualizar la pantalla. Dos grupos distintos sí pueden ejecutar a la vez. Para
el canal, publicar varios MiB/10 000 eventos de salida y verificar
memoria/eventos acotados, resumen de omisiones y entrega exacta de todos los
eventos de ciclo de vida en orden.

Con una lectura activa bloqueada y otra pendiente, llamar
`cerrar_lecturas()`: debe invalidar todas las generaciones, descartar pendientes
y hacer que la finalización tardía devuelva `None`. El hilo activo puede terminar,
pero no agenda otro worker ni ejecuta callbacks de UI. Una prueba con barrera
desmonta una App que sólo tiene lecturas, exige salida inmediata y cero escrituras
sobre widgets después de `on_unmount`.

- [ ] **Step 2: Implementar coordinador con lock interno**

Usar `threading.Lock`; no importar Textual. Los IDs se crean con `uuid4().hex`.
Por cada grupo mantener una activa y, como máximo, la generación pendiente más
reciente. `solicitar_lectura()` nunca arranca un segundo worker del mismo grupo;
`finalizar_lectura()` consume atómicamente la pendiente final y devuelve el
permiso que la capa UI debe lanzar. Exponer una instantánea inmutable de estado
para renderizar, no campos mutables. `cerrar_lecturas()` es idempotente, marca el
coordinador cerrado para lecturas e invalida todo bajo el mismo lock; después de
cerrar, una solicitud nueva se rechaza con error de dominio y nunca crea worker.

- [ ] **Step 3: Escribir matriz roja de breakpoints**

Casos exactos: 49/50 columnas, 17/18 filas, 79/80/119/120 columnas y 23/24/35/36 filas. Rechazar dimensiones negativas.

- [ ] **Step 4: Escribir pruebas hostiles de texto/URL/buffer**

Cubrir markup `[link=...]`, escapes ANSI CSI/OSC, BEL/C0, surrogate aislado, línea UTF-8 de 9 KiB, entrada total de 2 MiB y URLs `javascript:`, `file:`, credenciales incrustadas, hostname vacío y `http` no autorizado. Permitir `https`; permitir `http` sólo con flag explícito. Capturar Rich desde `cli/renderizado.py` con nombres/rutas/mensajes hostiles y demostrar que se crean `Text` literales sin estilos, hipervínculos, ANSI ni acciones inyectadas.

- [ ] **Step 5: Implementar normalización acotada**

Eliminar ANSI/CSI/OSC antes de controles; preservar sólo tab y salto de línea; normalizar Unicode con reemplazo; truncar por bytes sin cortar carácter; añadir marca `… [truncado]`. El buffer cuenta bytes UTF-8 y descarta líneas antiguas completas. `cli/renderizado.py` aplica la misma función a todo dato externo y entrega objetos `rich.text.Text`; sólo constantes internas pueden habilitar markup.

- [ ] **Step 6: Verificar y commit**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_coordinador_operaciones.py tests/unidad/test_canal_eventos.py tests/unidad/test_adaptabilidad.py tests/unidad/test_texto_seguro.py tests/interfaz/test_seguridad_cli.py -q
```

```bash
git add tramalia/interfaz tests/unidad
git commit -m "feat: coordinar y proteger operaciones de interfaz"
```

### Task 6: Compartir tokens visuales entre MkDocs, Rich y Textual

**Files:**
- Create: `tramalia/presentacion/__init__.py`
- Create: `tramalia/presentacion/variables_tema.py`
- Create: `tramalia/cli/tema.py`
- Create: `tramalia/interfaz/tema.py`
- Create: `tests/contratos/test_tema_terminal.py`
- Modify: `docs/stylesheets/extra.css` sólo si el contrato revela drift real.

**Interfaces:**
- Consumes: variables canónicas `--tramalia-*` de MkDocs.
- Produces: `TemaTerminal`, temas Rich/Textual y resolución de precedencia.

- [ ] **Step 1: Escribir contrato rojo CSS↔Python**

Extraer del CSS y comparar estos valores oscuros exactos: `#05031c`, `#010319`, `#0f0a4c`, `#1c1060`, `#623abf`, `#8c68d9`, `#b3e448`, `#f7f5ff`, `#b7b3cb`, `#7fe36a`, `#f5c451`, `#ff6178`, `#62c6ff`, `#46d6c7`.

Probar cuatro temas (`oscuro`, `claro`, `alto-contraste`, `monocromo`), contraste de texto normal >=4.5:1, rechazo localizado de cualquier otro valor y precedencia `NO_COLOR` > argumento > env > oscuro. Cualquier presencia de `NO_COLOR` fuerza `monocromo`; `TRAMALIA_TEMA` sólo acepta los cuatro valores públicos.

- [ ] **Step 2: Implementar módulo puro**

`variables_tema.py` sólo usa dataclasses/enums/stdlib. Adaptadores Rich/Textual importan sus librerías opcionales en sus propios módulos. El lima se reserva a acción/foco; estados incluyen símbolo y palabra, nunca sólo color. No se persiste la elección y ningún tema incorpora animaciones no esenciales.

- [ ] **Step 3: Verificar ausencia de dependencia opcional en wheel mínimo**

Run:

```powershell
uv run --no-sync pytest tests/contratos/test_tema_terminal.py -q
python -c "import tramalia.presentacion.variables_tema"
```

Expected: PASS sin importar `textual`.

- [ ] **Step 4: Commit**

```bash
git add tramalia/presentacion tramalia/cli/tema.py tramalia/interfaz/tema.py tests/contratos/test_tema_terminal.py docs/stylesheets/extra.css
git commit -m "style: compartir identidad visual de terminal"
```

### Task 7: Centralizar catálogo CLI, parser, menú y ayuda localizada

**Files:**
- Create: `tramalia/cli/catalogo_comandos.py`
- Create: `tramalia/cli/ayuda.py`
- Modify: `tramalia/__main__.py`
- Modify: `tramalia/cli/comandos.py`
- Modify: `tramalia/cli/menu.py`
- Modify: `tramalia/i18n/es.json`
- Modify: `tramalia/i18n/en.json`
- Create: `tests/contratos/test_catalogo_cli.py`
- Create: `tests/interfaz/test_presentacion_cli.py`
- Create: `tests/interfaz/test_menu_cli.py`

**Interfaces:**
- Consumes: comandos, subcomandos, aliases y destinos argparse entregados por 03c.
- Produces: catálogo canónico inmutable, IDs de operación compartidos, seis grupos de intención y menú seguro.

- [ ] **Step 1: Congelar paridad actual antes de mover definiciones**

La prueba obtiene choices de `_SubParsersAction`, aliases, claves de
`_CONTROLADORES`, IDs de operación y opciones del menú. Exige igualdad de
conjuntos con las definiciones descubiertas en el catálogo, preserva
destinos/required/defaults/nargs y prueba Namespaces representativos
antes/después. El menú exige exactamente
`{definición.nombre | definición.visible_menu}` más la acción Salir, en el orden
del catálogo; los no interactivos/avanzados quedan fuera de forma deliberada.
Para Habilidades, español e inglés resuelven el mismo ID de operación y el mismo
método de `ServicioHabilidades`; el contrato no infiere paridad contando entradas.

- [ ] **Step 2: Definir catálogo sin callables**

```python
class ValorCategoriaComando(StrEnum):
    EMPEZAR_ADOPTAR = "empezar_y_adoptar"
    VERIFICAR = "verificar"
    CONTEXTO_INTEGRACIONES = "contexto_e_integraciones"
    EVIDENCIA_CIERRE = "evidencia_y_cierre"
    MANTENIMIENTO = "mantenimiento"
    AVANZADO = "avanzado"

@dataclass(frozen=True, slots=True)
class DefinicionArgumento:
    clave_publica: str
    banderas: tuple[str, ...]
    destino: str | None
    clave_nombre: str
    clave_ayuda: str
    obligatorio: bool = False
    valores_permitidos: tuple[str, ...] = ()
    opciones_argparse: Mapping[str, object] = field(default_factory=dict)

@dataclass(frozen=True, slots=True)
class DefinicionSubcomando:
    clave_publica: str
    nombre: str
    clave_nombre: str
    clave_resumen: str
    clave_ayuda: str
    clave_salida: str
    clave_siguiente_accion: str
    categoria: ValorCategoriaComando
    ejemplos: tuple[str, ...]
    visible_ayuda: bool
    visible_menu: bool
    visible_automatizacion: bool
    acepta_interaccion: bool
    acepta_salida_estructurada: bool
    extra_requerido: str | None
    capacidad: str
    operacion: str
    clave_manejador: str
    argumentos: tuple[DefinicionArgumento, ...] = ()
    serializador_json: str | None = None
    aliases_publicos: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class DefinicionComandoPublico:
    clave_publica: str
    nombre: str
    clave_nombre: str
    clave_resumen: str
    clave_ayuda: str
    clave_salida: str
    clave_siguiente_accion: str
    categoria: ValorCategoriaComando
    ejemplos: tuple[str, ...]
    visible_ayuda: bool
    visible_menu: bool
    visible_automatizacion: bool
    acepta_interaccion: bool
    acepta_salida_estructurada: bool
    extra_requerido: str | None
    capacidad: str
    operacion: str
    clave_manejador: str
    argumentos: tuple[DefinicionArgumento, ...] = ()
    subcomandos: tuple[DefinicionSubcomando, ...] = ()
    serializador_json: str | None = None
    aliases_publicos: tuple[str, ...] = ()
```

Guardar claves de manejador, no funciones, para evitar ciclo catálogo↔comandos.
Resolver traducciones al renderizar, no al importar. Copiar
`opciones_argparse` a una vista inmutable y validar al construir: nombres y
aliases públicos únicos y sin colisiones, 2–3 ejemplos por comando visible,
salida y siguiente acción no vacías, serializador requerido cuando
`acepta_salida_estructurada`, extra conocido, capacidad/operación no vacías y
paridad de todas las claves i18n ES/EN. Los aliases `skills` y sus subcomandos
históricos apuntan a las operaciones españolas equivalentes entregadas por 03c.

- [ ] **Step 3: Generar parser/menú desde catálogo**

`construir_parser()` sigue devolviendo `ArgumentParser`. `_CONTROLADORES` continúa
como registro explícito y un contrato exige paridad con las definiciones del
catálogo. Cada variante de Habilidades declara su ID de operación y delega en el
adaptador delgado de `ServicioHabilidades` creado por 03c; no conserva un parser
o despachador alternativo. Después de congelar la paridad histórica, el catálogo
añade a `ui` la opción pública
`--tema {oscuro,claro,alto-contraste,monocromo}` con `default=None`; el
controlador entrega ese valor al resolvedor de Task 6 para respetar `NO_COLOR` y
`TRAMALIA_TEMA`. `menu` deriva opciones visibles, valida `stdin.isatty()` y
`stdout.isatty()` antes de importar/usar Questionary y devuelve código 2 con
mensaje claro si no hay TTY.

- [ ] **Step 4: Construir ayuda localizada por intención**

Categorías canónicas: empezar y adoptar, verificar, contexto e integraciones,
evidencia y cierre, mantenimiento y avanzado. Ayuda raíz incluye propósito,
sintaxis, comandos agrupados, 2–3 ejemplos y siguiente acción. Parametrizar cada
comando, alias y subcomando descubierto en ES/EN: cada ayuda conserva opciones
argparse y muestra entradas obligatorias (o «ninguna»), salida producida,
interactividad, disponibilidad JSON, capacidad/extra opcional, 2–3 ejemplos y
siguiente acción. Español e inglés deben tener las mismas claves y ningún campo
del catálogo puede quedar sin renderizar ni probar.

- [ ] **Step 5: Ejecutar contratos y subprocess no-TTY**

Run:

```powershell
uv run --no-sync pytest tests/contratos/test_catalogo_cli.py tests/interfaz/test_presentacion_cli.py tests/interfaz/test_menu_cli.py -q
uv run --no-sync pytest tests/contratos/test_operaciones_superficies.py tests/test_comandos_simples.py -q
```

Expected: PASS; ayuda en inglés realmente inglesa; no traceback sin TTY.

- [ ] **Step 6: Commit**

```bash
git add tramalia/__main__.py tramalia/cli tramalia/i18n tests
git commit -m "refactor: centralizar experiencia de comandos"
```

### Task 8: Añadir salida JSON v1 y renderizado aislado por invocación

**Files:**
- Create: `tramalia/cli/salida_estructurada.py`
- Modify: `tramalia/cli/renderizado.py`
- Modify: `tramalia/cli/comandos.py`
- Modify: `tramalia/__main__.py`
- Create: `tests/contratos/test_salida_estructurada_cli.py`
- Create: `tests/integracion/test_cli_subproceso.py`

**Interfaces:**
- Consumes: modelos de doctor, detect, bitácora, contexto y los modelos/planes/resultados de `ServicioHabilidades` entregados por 03c.
- Produces: `--formato texto|json`, sobre estable v1, serializadores por ID de operación y estado Rich no global.

- [ ] **Step 1: Escribir pruebas rojas de validación previa**

Aceptar `--formato` y `--plain` antes o después del subcomando. `--formato json
--plain`, `menu/ui --formato json`, variante sin serializador y `doctor --fix
--formato json` fallan con código 2 antes de prompt/mutación. Toda mutación de
Habilidades en JSON es no interactiva: sin `--confirmar-huella` devuelve sólo el
plan tipado y no escribe; con una huella vigente ejecuta mediante
`ServicioHabilidades`. Una huella ausente, inválida u obsoleta jamás abre un
prompt ni aplica parcialmente.

Sobre de éxito:

```json
{"version_esquema":1,"ok":true,"comando":"doctor","datos":{},"advertencias":[]}
```

Error:

```json
{"version_esquema":1,"ok":false,"comando":"doctor","error":{"codigo":"proyecto_no_gobernado","mensaje":"El proyecto no esta inicializado.","sugerencia":"Ejecuta tramalia init."},"advertencias":[]}
```

Stdout debe contener exactamente un JSON y salto final; stderr sólo diagnósticos técnicos. Probar `json.loads`, ausencia de ANSI/markup y `allow_nan=False`.

- [ ] **Step 2: Implementar serializadores explícitos**

La cobertura inicial incluye `doctor` sin fix, `detect`, `log`, `context list` y
todas las operaciones públicas de Habilidades entregadas por 03c: listar,
planificar, explicar, auditar, activar, desactivar y aplicar perfil, incluidos
sus aliases ingleses. Rehidratar y actualizar reutilizan el serializador de
resultado tipado cuando su variante declara automatización. Declarar el
serializador por ID de operación en el catálogo; alias español/inglés produce el
mismo esquema y conserva en `comando` el nombre público invocado.

Serializar `EstadoHabilidad`, `PlanResolucionHabilidades`,
`PlanCambioHabilidades`, `ResultadoCambioHabilidades`,
`EventoOperacionHabilidades` y `ResultadoAuditoriaHabilidad` con funciones
explícitas. Listar y explicar incluyen por separado activación, obligatoriedad,
compatibilidad, instalación, integridad y actualización, además de origen,
razón, procedencia, dependencias, conflictos, herramientas faltantes, permisos y
riesgo.

El JSON de resolución contiene `version_esquema`, `perfiles`, `decisiones`,
`orden_activacion`, `bloqueos`, `huellas_insumos`, `huella` y `aplicable`; nunca
contiene `aplicada`. El JSON de cambio contiene solicitud, resolución, diff,
huellas, bloqueos y huella del `PlanCambioHabilidades`. Sólo la respuesta de
`ResultadoCambioHabilidades` contiene `aplicada`, junto al plan confirmado y los
estados compuestos posteriores. Una explicación no copia el contenido completo
de `SKILL.md`. Convertir Enum con `.value`, datetime ISO 8601 con zona y Path
relativa/portable cuando esté dentro de raíz; nunca dataclass genérica, `repr` ni
`default=str`.

- [ ] **Step 3: Aislar Rich por contexto de invocación**

Eliminar `_PLANO`/`_consola` mutables globales. Crear consola contra el stream actual por ejecución. Un context manager restaura configuración incluso al fallar. `NO_COLOR`, ASCII forzado y ancho estrecho se prueban en subprocesos reales.

Parametrizar la matriz CLI canónica en 60, 80, 120 y 160 columnas, para salida
Rich, `--plain` y `NO_COLOR`, tanto TTY como no-TTY (24 combinaciones). Verificar
sin snapshots frágiles que no hay overflow/ANSI indebido, que etiquetas y
siguiente acción permanecen visibles y que cada invocación restaura su consola.

- [ ] **Step 4: Ejecutar JSON/presentación/regresión**

Run:

```powershell
uv run --no-sync pytest tests/contratos/test_salida_estructurada_cli.py tests/integracion/test_cli_subproceso.py -q
uv run --no-sync pytest tests/contratos/test_operaciones_superficies.py tests/test_comandos_simples.py tests/test_v012.py tests/test_v023.py tests/test_v024.py tests/test_v025.py tests/test_v031.py -q
```

Expected: PASS y mismos códigos de salida de texto.

- [ ] **Step 5: Commit**

```bash
git add tramalia/__main__.py tramalia/cli tests
git commit -m "feat: ofrecer salida cli estructurada"
```

### Task 9: Extraer la aplicación Textual manteniendo la fachada pública

**Files:**
- Create: `tramalia/interfaz/aplicacion.py`
- Create: `tramalia/interfaz/acciones.py`
- Create: `tramalia/interfaz/presentadores.py`
- Create: `tramalia/interfaz/estilos/tramalia.tcss`
- Create: todos los módulos `componentes/` del mapa
- Modify: `tramalia/interfaz_terminal.py`
- Create: `tests/interfaz/test_aplicacion_terminal.py`
- Create: `tests/contratos/test_wheel_minimo.py`
- Create: `tests/contratos/test_paridad_operaciones_terminal.py`
- Modify: `tests/interfaz/test_interfaz_terminal.py`

**Interfaces:**
- Consumes: servicio, coordinador, temas, perfiles y texto seguro.
- Produces: `AplicacionTramalia`, `RegistroAccionesInterfaz` y componentes sin política.

- [ ] **Step 1: Escribir pruebas estructurales rojas de fachada y wheel**

Exigir que `interfaz_terminal.py` conserve sólo imports diferidos, `construir_aplicacion()` y `ejecutar()`, no contenga `class`, `CSS =`, widgets ni operaciones de dominio. Construir un wheel, comprobar por ZIP que incluye `tramalia/interfaz/estilos/tramalia.tcss`, instalarlo en un venv limpio sin `[tui]` y verificar que Textual no existe, CLI/núcleo/parser importan y `tramalia ui` devuelve el error opcional guiado. La prueba no puede importar desde el árbol fuente: ejecuta el proceso con cwd temporal y `PYTHONPATH` vacío.

- [ ] **Step 2: Crear registro explícito de acciones TUI**

`RegistroAccionesInterfaz` relaciona IDs estables con callbacks controlados. La
paleta combina navegación, acciones contextuales y una allowlist de comandos
públicos seguros; nunca descubre automáticamente MCP, `_CONTROLADORES` ni
funciones por nombre. `test_paridad_operaciones_terminal.py` deriva del catálogo
los IDs de operación visibles en TUI, exige que el registro contenga exactamente
ese conjunto y comprueba que los callbacks de Habilidades delegan en el mismo
`ServicioHabilidades` que el adaptador CLI. Las exclusiones deliberadas —por
ejemplo una operación sólo automatizable— se declaran en el catálogo con causa y
se prueban; no se mantienen dos listas manuales.

- [ ] **Step 3: Extraer App y CSS sin cambiar selectores históricos aún**

Mover clases locales por partes. Cargar `tramalia.tcss` como recurso del paquete. Actualizar `[tool.hatch.build.targets.wheel].artifacts` si es necesario para incluir TCSS. Mantener IDs usados por pruebas durante esta tarea.

- [ ] **Step 4: Activar paleta, ayuda y coordinación de salida**

`ENABLE_COMMAND_PALETTE=True`; `Ctrl+P` abre la paleta con nombres y ayuda localizados, F1 abre ayuda y `?` sólo actúa fuera de `Input`. La paleta permite cambiar entre los cuatro temas durante la sesión sin persistir la preferencia. `q` consulta `coordinador.estado_salida`: sale, confirma cancelación o muestra bloqueo de publicación. `on_unmount` llama primero `coordinador.cerrar_lecturas()`, solicita cancelación de una mutación si aún es segura y sólo espera el límite publicable de esa mutación sin congelar UI; nunca espera lecturas ni permite que su finalización escriba widgets desmontados.

La matriz Pilot de teclado y ratón exige foco inicial en el encabezado operativo
o primer control, retorno al invocador al cerrar un modal, salto al primer campo
inválido y recorrido completo por tabulación sin trampas de foco. `Enter` activa
el control enfocado; `Esc` cierra el modal o retrocede un nivel sin mutar el
dominio; flechas navegan tablas y grupos de opciones; y un clic ejecuta cada
control primario sólo cuando está habilitado. En vista compacta el pie muestra
únicamente acciones aplicables; las imposibles se ocultan o quedan deshabilitadas
con una causa accesible. Probarlo con operaciones permitidas/bloqueadas y afirmar
que el estado de dominio permanece intacto tras `Esc`. El foco permanece visible
en los cuatro temas.

- [ ] **Step 5: Verificar fachada y regresión TUI**

Run:

```powershell
uv run --no-sync pytest tests/interfaz/test_aplicacion_terminal.py tests/interfaz/test_interfaz_terminal.py tests/contratos/test_paridad_operaciones_terminal.py tests/contratos/test_nombres_espanol.py -q
uv run --no-sync pytest tests/contratos/test_wheel_minimo.py -q
python -c "from tramalia.interfaz_terminal import construir_aplicacion; print(construir_aplicacion)"
```

Expected: PASS; el módulo fachada no importa Textual hasta construir.

- [ ] **Step 6: Commit**

```bash
git add tramalia/interfaz_terminal.py tramalia/interfaz pyproject.toml tests
git commit -m "refactor: modularizar aplicacion textual"
```

### Task 10: Construir shell adaptable, navegación y estados iniciales seguros

**Files:**
- Create: `tramalia/interfaz/pantallas/resumen.py`
- Create: `tramalia/interfaz/pantallas/inicializacion.py`
- Create: `tramalia/interfaz/pantallas/herramientas.py`
- Modify: componentes y `aplicacion.py`
- Create: `tramalia/core/preparacion_proyecto.py`
- Modify: `tramalia/core/tablero.py`, `tramalia/core/scaffold.py`
- Create: `tests/unidad/test_preparacion_proyecto.py`
- Create: `tests/integracion/test_preparacion_proyecto.py`
- Create: `tests/interfaz/test_adaptabilidad_terminal.py`

**Interfaces:**
- Consumes: `EstadoProyecto`, `PerfilTerminal`, snapshots y renderizado canónico del scaffold.
- Produces: planes tipados de inicialización/adopción/actualización/reparación, shell 5 áreas, mínimo seguro y mutaciones siempre previsualizadas.

- [ ] **Step 1: Escribir pruebas funcionales de tamaños límite**

Pilot funcional de Resumen en 50×18 y resize 79→80→119→120; conservar sección, selección, campos, scroll y foco sin volver a llamar al servicio. Probar por separado 49×18, 50×17, 49×24 y 80×17 para detectar errores AND/OR: sólo aparece `AvisoTamanoMinimo` con tamaño actual/mínimo y Salir; ningún botón mutante ni formulario se monta. Al volver desde ese aviso o desde cualquier modal se restaura por ID estable el control invocador; si ya no existe, se enfoca el encabezado operativo.

- [ ] **Step 2: Implementar breakpoints declarativos**

```python
HORIZONTAL_BREAKPOINTS = [(0, "-compacto"), (80, "-medio"), (120, "-ancho")]
VERTICAL_BREAKPOINTS = [(0, "-bajo"), (24, "-normal"), (36, "-alto")]
```

Compacto usa selector + Alt+1…5; medio/ancho pestañas visibles. Las áreas exactas: Resumen, Herramientas, Habilidades, Auditoría, Cierre. Modales usan porcentaje + max-width y nunca superan viewport.

- [ ] **Step 3: Escribir contratos rojos de preparación sin escritura**

Probar que planificar no crea archivos; cada cambio tiene ruta confinada, acción, hashes y descripción. En estado `ausente`, inicializar admite directorio vacío o con código siempre que sea no destructivo: conserva archivos existentes y falla si una ruta que debería crear ya existe con contenido divergente. Adoptar es la recomendación cuando detecta código/AGENTS y tampoco los sobrescribe, pero la UI permite elegir Inicializar. Actualizar sólo admite heredado; reparar sólo admite parcial y enumera piezas inválidas/ausentes. Modificar un archivo afectado después del preview hace que aplicar falle antes de la primera escritura.

La integración inyecta un fallo durante publicación de archivos y verifica restauración de los archivos existentes y ausencia de temporales. Los archivos nuevos todavía no publicados se eliminan; no se toca código fuera del conjunto del plan.

- [ ] **Step 4: Implementar planificación sobre el scaffold canónico**

Separar en `scaffold.py` el renderizado puro de la escritura. `preparar_proyecto` compara bytes renderizados con el disco y calcula la huella del conjunto afectado. `aplicar_preparacion` renderiza otra vez, exige la misma `huella_origen` **y** que el SHA-256 de cada byte nuevo siga siendo exactamente `CambioPreparacionProyecto.hash_despues`; así un cambio de plantilla, versión o entrada del render entre preview/aplicación falla antes de escribir. Luego prepara temporales en la misma raíz y publica con `os.replace`; si un paso falla antes de completar, restaura desde copias privadas verificadas. No aceptar rutas enlazadas/reparse fuera de raíz.

Ampliar `ServicioTablero` por delegación, sin strings libres ni interpretación en widgets:

```python
def preparar_proyecto(
    self,
    tipo: ValorTipoPreparacionProyecto,
    version_objetivo: str,
) -> PlanPreparacionProyecto: ...
def aplicar_preparacion(
    self,
    plan: PlanPreparacionProyecto,
    *,
    senal_cancelacion: SenalCancelacion | None = None,
    al_cruzar_limite_cancelacion: Callable[[], None] | None = None,
) -> ResultadoPreparacionProyecto: ...
```

Las pruebas exhaustivas validan los cuatro valores del enum, combinaciones de
estado de origen inválidas, rutas/hashes, plan inmutable, revalidación y rollback
atómico. También cubren cancelar antes de la frontera, callback de frontera que
falla sin escritura y una barrera que demuestra `q`/`on_unmount` bloqueados
durante reemplazos/rollback. Un fallo o cancelación antes de aplicar no produce
un “resultado parcial”: lanza el error tipado y deja el filesystem igual al
estado revalidado.

Run: `uv run --no-sync pytest tests/unidad/test_preparacion_proyecto.py tests/integracion/test_preparacion_proyecto.py tests/test_scaffold.py -q`

Expected: PASS y filesystem intacto tras preview/cancelación/fallo.

- [ ] **Step 5: Escribir matriz roja de estado inicial TUI**

Probar:

- `ausente` vacío → recomendar inicializar;
- `ausente` con código/config/AGENTS → recomendar adoptar, permitiendo cambiar opción;
- `heredado` → actualizar convención;
- `parcial` → reparar piezas concretas, nunca `inicializar()`;
- `listo` con tarea → revisar cierre;
- `listo` sin tarea → seleccionar/declarar tarea.

Toda acción muestra `ConfirmacionPlan` con archivos/cambios antes de mutar. Cancelar no cambia filesystem.

Para los cuatro tipos, confirmar debe adquirir el mismo `PermisoMutacion`
global, pasar `permiso.senal_cancelacion` a `aplicar_preparacion` y entregar un
callback de frontera que llama `coordinador.marcar_publicando(permiso)`. Una
segunda acción —aunque tenga otro nombre— queda deshabilitada/rechazada; cancelar
o fallar finaliza exactamente ese permiso. Pilots con barrera prueban exclusión
contra otra preparación y contra un permiso simulado de instalación/cierre, `q`
antes/durante la frontera y ausencia de escritura parcial.

- [ ] **Step 6: Implementar cabecera/resumen sin ruido**

Cabecera: versión, proyecto abreviado, estado, tarea e indicador de operación. Resumen responde estado, tarea, puertas, bloqueo/degradación y siguiente acción; una sola acción primaria. No usar logo ASCII grande. Al terminar la preparación, finalizar el permiso y pedir una instantánea real coalescida; nunca promover el estado del proyecto sólo por el resultado visual del modal.

- [ ] **Step 7: Verificar tamaños y estado inicial**

Run: `uv run --no-sync pytest tests/interfaz/test_adaptabilidad_terminal.py tests/interfaz/test_aplicacion_terminal.py tests/unidad/test_preparacion_proyecto.py tests/integracion/test_preparacion_proyecto.py -q`

Expected: PASS en todos los límites.

- [ ] **Step 8: Commit**

```bash
git add tramalia/interfaz tramalia/core/preparacion_proyecto.py tramalia/core/tablero.py tramalia/core/scaffold.py tests
git commit -m "feat: adaptar navegacion y resumen textual"
```

### Task 11A: Completar Herramientas e instalación observable

**Files:**
- Modify: `tramalia/interfaz/pantallas/herramientas.py`
- Modify: `tramalia/interfaz/presentadores.py`
- Create: `tramalia/core/instalador.py`
- Modify: `tramalia/core/installer.py` como shim BETA de compatibilidad
- Modify: `tramalia/core/tablero.py`
- Create: `tests/unidad/test_instalador_observable.py`
- Create: `tests/integracion/test_instalador_observable.py`
- Create: `tests/contratos/test_shim_installer.py`
- Create: `tests/interfaz/test_herramientas_terminal.py`

**Interfaces:**
- Consumes: `PlanInstalacion`, `ResultadoPlanInstalacion`, snapshots y URLs validadas.
- Produces: filtros combinables, preview exacto e instalación planificada/cancelable.

- [ ] **Step 1: Escribir RED del plan y de la pantalla**

Probar `preparar_instalacion()` y `ejecutar_instalacion_observable()` con plan
puro, IDs/pasos/prerrequisitos/efectos, eventos correlacionados, salida separada,
éxito, fallo que no inicia pendientes, cancelación que conserva terminados y
código 130. En Pilot, filtrar por texto, categoría y estado de forma combinable,
conservar selección al refrescar y exigir plan/confirmación antes de instalar.
Los ejecutables helper cubren Windows, Linux y macOS sin instalar paquetes reales.
Las pruebas activas importan `tramalia.core.instalador`; el contrato separado del
shim verifica que los imports históricos conservan identidad y emiten la
deprecación documentada sin duplicar lógica.

- [ ] **Step 2: Implementar la ruta observable compartida**

Mover la implementación propia desde `tramalia.core.installer` a
`tramalia.core.instalador` y refactorizar `run_install_streaming` para delegar en
`core.procesos.ejecutar` sin romper su retorno histórico. `installer.py` sólo
reexporta/delega las APIs BETA históricas y documenta la migración; no mantiene
constantes, resolución, subprocess ni modelos propios. Excluir explícitamente el
shim de la navegación de referencia mkdocstrings y documentar únicamente
`tramalia.core.instalador`. Ampliar `ServicioTablero` sólo por delegación:

```python
def preparar_instalacion(
    self, herramientas: Sequence[Herramienta]
) -> PlanInstalacion: ...

def instalar_observable(
    self, plan: PlanInstalacion, *,
    senal_cancelacion: SenalCancelacion | None = None,
    al_evento: Callable[[EventoOperacion], None] | None = None,
) -> ResultadoPlanInstalacion: ...
```

Widgets, presentadores, código propio y pruebas activas importan únicamente
`instalador.py`, no crean
procesos y no cambian estados de forma optimista.

- [ ] **Step 3: Coordinar la mutación y el refresco real**

Confirmar adquiere un `PermisoMutacion`; cancelar solicita la señal del plan
completo, conserva pasos terminados y no inicia pendientes. Al terminar, siempre
finaliza el permiso y solicita una instantánea nueva del grupo diagnóstico. Un
Pilot entrega primero un diagnóstico obsoleto y luego otro real distinto; sólo
el segundo puede determinar el estado mostrado.

- [ ] **Step 4: Verificar Herramientas**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_instalador_observable.py tests/integracion/test_instalador_observable.py tests/contratos/test_shim_installer.py -q
uv run --no-sync pytest tests/interfaz/test_herramientas_terminal.py tests/interfaz/test_seguridad_terminal.py -q
```

Expected: PASS; código 130 se presenta como cancelación y no queda proceso vivo.

- [ ] **Step 5: Commit**

```bash
git add tramalia/interfaz/pantallas/herramientas.py tramalia/interfaz/presentadores.py tramalia/core/instalador.py tramalia/core/installer.py tramalia/core/tablero.py tests
git commit -m "feat: instalar herramientas desde planes observables"
```

### Task 11B: Adaptar Habilidades gobernadas a CLI y TUI

**Files:**
- Create: `tramalia/interfaz/pantallas/habilidades.py`
- Create: `tramalia/interfaz/componentes/resumen_perfil_habilidades.py`
- Create: `tramalia/interfaz/componentes/detalle_habilidad.py`
- Create: `tramalia/interfaz/componentes/confirmacion_habilidades.py`
- Modify: `tramalia/interfaz/aplicacion.py`
- Modify: `tramalia/interfaz/acciones.py`
- Modify: `tramalia/interfaz/presentadores.py`
- Modify: `tramalia/cli/catalogo_comandos.py`
- Modify: `tramalia/cli/salida_estructurada.py`
- Create: `tests/interfaz/test_habilidades_terminal.py`
- Create: `tests/contratos/test_importaciones_habilidades_03b.py`
- Modify: `tests/contratos/test_catalogo_cli.py`
- Modify: `tests/contratos/test_salida_estructurada_cli.py`
- Modify: `tests/contratos/test_paridad_operaciones_terminal.py`

**Interfaces:**
- Consumes: `ServicioHabilidades`, `EstadoHabilidad`, `SolicitudCambioHabilidades`, `PlanCambioHabilidades`, `ResultadoCambioHabilidades`, `EventoOperacionHabilidades`, `PlanResolucionHabilidades`, `ConfiguracionHabilidadesProyecto` y `ResultadoAuditoriaHabilidad` de 03c.
- Produces: catálogo/perfiles explicables, plan/diff, confirmación por huella y paridad CLI/TUI sin política duplicada.

- [ ] **Step 1: Verificar la entrega 03c antes de importar**

Run:

```powershell
uv run --no-sync pytest tests/contratos/test_entrega_03c.py tests/contratos/test_superficies_habilidades.py tests/contratos/test_cli_habilidades.py -q
```

Expected: PASS; si una firma pública difiere, actualizar este plan antes de tocar
la pantalla, no crear un wrapper incompatible.

Crear `test_importaciones_habilidades_03b.py` con una importación explícita —sin
`getattr`, `import *` ni fallback— de todos los símbolos anteriores y de los seis
enums dimensionales. La prueba compara sus `__module__` con
`tramalia.core.modelos_habilidades`, `tramalia.core.auditoria_habilidades` o
`tramalia.core.servicio_habilidades`, y se ejecuta siempre junto a
`test_entrega_03c.py`. Así una renombrada o un tipo paralelo falla antes de
implementar la superficie.

- [ ] **Step 2: Escribir RED del modelo visual y contenido hostil**

Construir un `ServicioHabilidades` falso con `EstadoHabilidad` compuestos que
cubran activación activa/inactiva; obligatoriedad obligatoria/recomendada/opcional;
compatibilidad compatible/pendiente/incompatible/conflicto; instalación
instalada/no instalada; integridad no verificada/verificada/modificada/inválida;
y actualización no consultada/actual/disponible/error. Probar que la vista no
colapsa estas seis dimensiones en un único badge y conserva además origen, razón,
perfiles, dependencias, conflictos, herramientas faltantes, permisos, riesgo,
fuente, referencia, SHA, hash, licencia y resultado de auditoría.
Inyectar markup, ANSI/OSC, URL `javascript:`, Unicode inválido y texto enorme;
verificar texto literal, URL rechazada y buffers acotados. Ningún widget infiere
estado desde la presencia de un directorio o un SHA.

- [ ] **Step 3: Implementar Catálogo, Perfiles y Plan dentro de Habilidades**

Mantener una sola área principal con tres subvisiones accesibles:

- **Catálogo:** filtros independientes por texto, categoría, activación,
  obligatoriedad, compatibilidad, instalación, integridad, actualización, origen
  y riesgo; selección estable y detalle bajo demanda.
- **Perfiles:** perfiles activos, obligatorias/recomendadas y razón de cada
  decisión; aplicar perfil abre preview, nunca ejecuta desde la fila.
- **Plan:** diff de activar, desactivar, conservar y bloquear, orden de activación,
  dependencias/conflictos y huella confirmable.

En 50×18 usar selector y detalle en una pantalla secundaria; en 120×36 mostrar
lista y detalle sin duplicar texto. Abrir la pantalla, cambiar filtros, navegar o
explicar usa sólo consultas puras de `ServicioHabilidades` y nunca consulta red.
`Auditar` y `Actualizar remoto` son acciones explícitas con progreso y resultado.

- [ ] **Step 4: Implementar mutaciones con plan y desactivación protegida**

Activar, desactivar, aplicar perfil, rehidratar y actualizar construyen primero
una `SolicitudCambioHabilidades`, llaman a `planificar(solicitud)`, muestran el
`PlanCambioHabilidades` con resolución, diff, huellas de insumos, bloqueos y
huella confirmable. Cada ejecución adquiere el mismo `PermisoMutacion` global que
preparación, instalación, proveedor y cierre; entrega la huella al método exacto
de `ServicioHabilidades` y usa `ResultadoCambioHabilidades` como único resultado
definitivo. Después relee `listar` y `planificar` para representar el estado real.
La UI no edita TOML/lock/cache, no materializa rutas y no promueve el estado por
el resultado visual del modal.

Adaptar `PermisoMutacion.senal_cancelacion` a la callable `cancelada` esperada por
03c y publicar `EventoOperacionHabilidades` en el canal acotado mediante un
adaptador de presentación. No convertir estos eventos en `EventoOperacion`, no
interpretar `mensaje` como estado y no recrear progreso desde stdout. Al recibir
`PUBLICANDO`, bloquear cancelación/salida según el evento y el resultado del
servicio; cancelar antes solicita la señal compartida y espera el
`ResultadoCambioHabilidades` tipado.

Si una decisión obligatoria se desactiva, el modal exige razón, riesgo aceptado,
referencia, revisor y expiración; enfoca el primer campo inválido y entrega la
`ExcepcionHabilidad` completa al servicio. Cancelar no crea selección ni
excepción. Una excepción vencida, huella obsoleta, dependencia inactiva o
conflicto conserva el plan bloqueado y muestra la remediación tipada. Actualizar
y rehidratar mantienen IDs, textos y resultados distintos.

- [ ] **Step 5: Probar paridad CLI/TUI y JSON por ID de operación**

Derivar del catálogo todas las variantes cuya capacidad sea `habilidades` y
comparar sus IDs con `RegistroAccionesInterfaz`. Para listar, planificar,
explicar, auditar, activar, desactivar y aplicar perfil, inyectar el mismo servicio
espía y exigir una única llamada al método correspondiente desde cada superficie.
Los aliases ingleses realizan la misma llamada.

En JSON, listar/explicar serializan `EstadoHabilidad` con sus seis dimensiones;
planificar serializa `PlanCambioHabilidades` y nunca incluye `aplicada`; auditar
serializa sus resultados. Activar, desactivar y aplicar perfil sin
`--confirmar-huella` devuelven el plan y cero escrituras. Con huella vigente
devuelven `ResultadoCambioHabilidades`, donde `aplicada` es obligatoria y los
estados posteriores conservan las seis dimensiones. Probar `json.loads`,
`allow_nan=False`, ausencia de ANSI/prompt y código 2 para huella obsoleta antes
de mutar.

- [ ] **Step 6: Verificar Habilidades**

Run:

```powershell
uv run --no-sync pytest tests/interfaz/test_habilidades_terminal.py tests/interfaz/test_seguridad_terminal.py -q
uv run --no-sync pytest tests/contratos/test_entrega_03c.py tests/contratos/test_importaciones_habilidades_03b.py tests/contratos/test_catalogo_cli.py tests/contratos/test_salida_estructurada_cli.py tests/contratos/test_paridad_operaciones_terminal.py tests/contratos/test_cli_habilidades.py -q
```

Expected: PASS; sólo `ServicioHabilidades` recibe las operaciones y una habilidad
inactiva nunca se presenta como instrucción materializada para agentes.

- [ ] **Step 7: Commit**

```bash
git add tramalia/interfaz tramalia/cli/catalogo_comandos.py tramalia/cli/salida_estructurada.py tests/interfaz/test_habilidades_terminal.py tests/contratos
git commit -m "feat: gestionar perfiles de habilidades desde cli y tui"
```

### Task 11C: Coordinar el proveedor de contexto

**Files:**
- Create: `tramalia/interfaz/pantallas/proveedor_contexto.py`
- Modify: `tramalia/core/configuracion.py`
- Modify: `tramalia/core/tablero.py`
- Create: `tests/unidad/test_cambio_proveedor_contexto.py`
- Create: `tests/interfaz/test_proveedor_contexto_terminal.py`

**Interfaces:**
- Consumes: `PlanCambioProveedorContexto`, coordinador y diagnóstico real.
- Produces: selección, preview y cambio atómico sin solapar mutaciones.

- [ ] **Step 1: Escribir RED de plan, drift y exclusión**

Probar que planificar no escribe; hash original distinto, cancelación antes de la
frontera o callback fallido conservan bytes; reemplazo exitoso cambia una sola
vez. En Pilot, mantener activas preparación, instalación, habilidades y cierre e
intentar cambiar proveedor: el servicio no se invoca.

- [ ] **Step 2: Implementar plan y aplicación atómica**

`fijar_proveedor_contexto()` mantiene firma/retorno y delega en un plan puro que
contiene proveedor, hash de `config.json` y bytes de destino. Aplicar revalida,
escribe un temporal confinado, llama al callback síncrono de frontera y hace un
único `os.replace`. `ServicioTablero` expone preparar/aplicar por delegación.

- [ ] **Step 3: Conectar modal y refresco**

El modal adquiere `PermisoMutacion`, pasa su señal, marca publicación en la
frontera y finaliza aun ante error. `q` cancela antes de escritura o queda
bloqueado durante el replace. Al terminar relee el diagnóstico y no supone que
el ejecutable esté disponible por guardar la preferencia.

- [ ] **Step 4: Verificar proveedor**

Run: `uv run --no-sync pytest tests/unidad/test_cambio_proveedor_contexto.py tests/interfaz/test_proveedor_contexto_terminal.py -q`

Expected: PASS y archivo idéntico tras cancelar, drift o callback fallido.

- [ ] **Step 5: Commit**

```bash
git add tramalia/interfaz/pantallas/proveedor_contexto.py tramalia/core/configuracion.py tramalia/core/tablero.py tests
git commit -m "feat: cambiar proveedor de contexto con preview"
```

### Task 11D: Construir Auditoría lazy y paginada

**Files:**
- Create: `tramalia/interfaz/pantallas/auditoria.py`
- Modify: `tramalia/interfaz/presentadores.py`
- Create: `tests/interfaz/test_auditoria_terminal.py`
- Modify: `tests/interfaz/test_aplicacion_terminal.py`
- Modify: `tests/interfaz/test_habilidades_terminal.py`

**Interfaces:**
- Consumes: `PaginaBitacora`, `DetalleBitacoraTablero` y lecturas coalescidas.
- Produces: lista paginada, detalle bajo demanda y navegación estable.

- [ ] **Step 1: Escribir RED de carga acotada y datos hostiles**

Crear más paquetes que el límite de página, entradas inválidas, un paquete que
desaparece y detalle con markup/ANSI/OSC/Unicode inválido. Abrir Auditoría debe
leer sólo la primera página; seleccionar una fila carga exactamente su detalle;
`Siguiente` usa cursor y no duplica entradas. Toda salida se presenta como texto
literal y el detalle crudo sigue opt-in y limitado a 1 MiB.

- [ ] **Step 2: Implementar lista, detalle y filtros locales**

En perfil ancho compartir lista/detalle; en compacto y medio abrir detalle como
nivel secundario y devolver foco a la fila. Filtros y navegación local continúan
durante otras mutaciones. Las lecturas usan el grupo `auditoria`, respetan
generación vigente y nunca precargan todos los packs.

- [ ] **Step 3: Verificar Auditoría y regresiones históricas**

Run:

```powershell
uv run --no-sync pytest tests/interfaz/test_auditoria_terminal.py tests/interfaz/test_aplicacion_terminal.py tests/interfaz/test_seguridad_terminal.py -q
uv run --no-sync pytest tests/test_v021b.py tests/test_v023.py tests/test_v024.py tests/test_v028.py tests/test_v030.py tests/test_v031.py -q
```

Expected: PASS; la cantidad de metadatos leídos queda acotada por la página y el
detalle seleccionado.

- [ ] **Step 4: Commit**

```bash
git add tramalia/interfaz/pantallas/auditoria.py tramalia/interfaz/presentadores.py tests
git commit -m "feat: navegar auditoria de forma paginada"
```

### Task 12: Implementar cierre progresivo, observable y cancelable

**Files:**
- Create: `tramalia/interfaz/pantallas/cierre.py`
- Modify: `tramalia/interfaz/componentes/registro_proceso.py`
- Modify: `tramalia/interfaz/aplicacion.py`
- Create: `tests/interfaz/test_cierre_terminal.py`
- Create: `tests/interfaz/test_exclusion_mutaciones_terminal.py`
- Modify: `tests/interfaz/test_interfaz_terminal.py`

**Interfaces:**
- Consumes: `PlanCierre`, eventos, coordinador y `ServicioTablero.cerrar_observable`.
- Produces: preview, progreso por puerta, cancelación segura, publicación bloqueada y resultado definitivo.

- [ ] **Step 1: Escribir flujos Pilot rojos**

Cubrir:

- identidad/tarea y puertas en preview;
- excepción colapsada y validación del primer campo inválido;
- progreso eventos en orden y salida circular;
- cancelar durante gate: no pack, pendientes no inician, UI vuelve a estado cancelado;
- cancelar/salir durante `publicando`: controles deshabilitados y mensaje de espera;
- completar: resultado usa el `ResultadoCierre` recibido, no recalcula;
- fallo: código/mensaje/sugerencia tipados sin traceback por defecto.

En una matriz parametrizada, mantener con barrera activa cada familia mutante
(preparación de proyecto, instalación, declarar/agregar/actualizar/rehidratar
habilidad, cambio de proveedor y cierre) e intentar todas las demás desde su
control real. Exactamente una conserva el `PermisoMutacion`; la segunda no llama
al servicio ni escribe. Liberar/cancelar la primera habilita la siguiente y cada
resultado final dispara un solo refresco diagnóstico real. Esta prueba
end-to-end impide que una pantalla omita el coordinador aunque sus unit tests
aislados pasen.

Ejecutar además en viewport exacto 50×18 el flujo funcional completo de Cierre:
editar/validar, enfocar el primer error, confirmar preview, observar progreso,
cancelar durante una puerta y completar en otra ejecución. No sustituir estos
casos por snapshots.

- [ ] **Step 2: Implementar secciones progresivas**

Orden: tarea/identidades, preflight, excepción colapsada, ejecución, resultado. Confirmar vuelve a preparar/validar plan para detectar drift. Entregar a `cerrar_observable` un `al_cruzar_limite_cancelacion` que llama síncronamente `coordinador.marcar_publicando()`; el evento visual puede llegar después por la cola, pero `q`/Cancelar ya leen estado bloqueado.

- [ ] **Step 3: Conectar cancelación real al worker/core**

`Worker.cancel()` sólo evita callbacks de UI; la acción Cancelar debe además llamar `senal.solicitar()`. Esperar el resultado del núcleo. No publicar resultado final si el worker se canceló visualmente pero el core aún corre.

- [ ] **Step 4: Verificar cierre UI + núcleo**

Run:

```powershell
uv run --no-sync pytest tests/interfaz/test_cierre_terminal.py tests/interfaz/test_interfaz_terminal.py tests/integracion/test_operaciones.py tests/integracion/test_procesos.py -q
uv run --no-sync pytest tests/interfaz/test_exclusion_mutaciones_terminal.py -q
```

Expected: PASS; no evidencia parcial tras cancelación.

- [ ] **Step 5: Commit**

```bash
git add tramalia/interfaz tests
git commit -m "feat: cerrar tareas con progreso y cancelacion tui"
```

### Task 13: Fijar snapshots representativos, consolidar pruebas y documentar superficies

**Files:**
- Create/Modify: `tests/interfaz/snapshots/`
- Modify: `tests/interfaz/test_aplicacion_terminal.py`
- Create: `scripts/soporte_capturas_tui.py`
- Create: `scripts/generar_capturas_tui.py`
- Create: `tests/contratos/test_capturas_tui.py`
- Create/Modify: `docs/assets/tui/*.svg`
- Modify: `tests/AUDITORIA.md`
- Modify/Delete: duplicados históricos demostrados en `tests/test_v021b.py`, `test_v023.py`, `test_v024.py`, `test_v028.py`, `test_v030.py`, `test_v031.py`
- Modify: `docs/comandos.md`, `docs/comandos.en.md`
- Modify: `docs/interfaz.md`, `docs/interfaz.en.md`
- Modify: `docs/skills-guia.md`, `docs/skills-guia.en.md`
- Modify: `docs/perfiles-habilidades.md`, `docs/perfiles-habilidades.en.md`
- Modify: `.github/workflows/validacion.yml`

**Interfaces:**
- Consumes: interfaz final y catálogo CLI.
- Produces: regresión visual pequeña, documentación derivada y matriz CI final.

- [ ] **Step 1: Crear la matriz canónica explícita**

Crear estas capturas mediante servicios falsos deterministas y la aplicación
real:

| Estado | Tamaño |
|---|---|
| resumen sin inicializar | 80×24 |
| resumen listo | 120×36 |
| herramientas con detalle | 160×48 |
| habilidades con perfil y decisiones | 120×36 |
| habilidades con plan/diff y conflicto | 80×24 |
| cierre con excepción plegada | 80×24 |
| cierre con excepción expandida | 120×36 |
| auditoría y evidencia | 120×36 |
| modal de proveedor | 50×18 |
| resumen compacto | 50×18 |
| cierre compacto | 50×18 |

No crear producto cartesiano de tema×estado×tamaño; alto
contraste/monocromo se prueban funcionalmente. Sólo añadir otra captura si
protege una diferencia real documentada.

Además de snapshots, ejecutar recorridos Pilot completos: aplicar un perfil con
preview/huella/resultado/refresco; activar una habilidad con dependencia;
rechazar un conflicto; desactivar una obligatoria sin excepción; corregir los
campos de excepción y confirmar; cancelar un plan sin escrituras. Repetir el
recorrido de consulta y plan en 50×18. Las capturas no sustituyen estas aserciones
de dominio y foco.

Run local deliberado: `uv run --no-sync pytest tests/interfaz --snapshot-update`

Revisar SVG uno a uno. CI nunca ejecuta `--snapshot-update`.

- [ ] **Step 2: Ejecutar reemplazos junto a históricos antes de borrar**

Por cada test histórico candidato, anotar en `tests/AUDITORIA.md` el contrato canónico equivalente y ejecutar ambos en el mismo comando. Sólo entonces eliminar duplicado. Conservar casos con entradas/riesgos distintos. Registrar colección/cobertura/duración medidas sin meta numérica.

- [ ] **Step 3: Generar capturas documentales reales y derivar documentación**

`soporte_capturas_tui.py` define escenarios falsos, congelados y sin sondas de la
máquina. `generar_capturas_tui.py --salida <directorio>` monta
`AplicacionTramalia` real, navega con Pilot y exporta SVG deterministas para
Resumen, Herramientas, Habilidades —incluido perfil y plan—, Auditoría, Cierre y
vista compacta. El contrato genera en un temporal, compara bytes/nombres con
`docs/assets/tui/` y exige que
`docs/interfaz.md` y `docs/interfaz.en.md` referencien los mismos activos con
texto alternativo traducido. No se editan SVG a mano ni se capturan datos del
equipo del autor.

Actualizar tablas ES/EN desde el catálogo descubierto, incluidos aliases e IDs
de operación, `--formato`, temas, cinco áreas, paleta, F1,
cancelación/publicación y tamaños. Las guías de Habilidades explican perfil,
estado, origen, razón, dependencias, conflictos, permisos, riesgo, plan, huella,
excepción y diferencia entre actualizar/rehidratar. Explicar “puerta de calidad”
en español llano y enlazar conceptos MkDocs. No copiar el plan interno a
navegación pública.

- [ ] **Step 4: Asegurar CI Textual y subprocess multiplataforma**

`opcionales` ejecuta interfaz/snapshots en Python 3.11 y 3.14 sobre Linux.
`plataformas` incluye `tests/integracion/test_procesos.py` en
Windows/Linux/macOS. Windows ejecuta además un smoke Pilot sin snapshots de
arranque, navegación, Habilidades y 50×18 para detectar diferencias del sistema
objetivo. Las acciones siguen fijadas por SHA. El job mínimo sin extra TUI
verifica que importar CLI/núcleo no requiere Textual.

- [ ] **Step 5: Verificación completa**

Run:

```powershell
uv sync --locked --group desarrollo --all-extras
uv run --no-sync pytest
uv run --no-sync pytest -m integracion -q
uv run --no-sync pytest -m "opcional or interfaz" -q
uv run --no-sync python scripts/generar_capturas_tui.py --salida .artefactos/capturas-tui
uv run --no-sync pytest tests/contratos/test_capturas_tui.py -q
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy tramalia
uv run --no-sync mkdocs build --strict
git diff --check
```

Expected: PASS; documentación ES/EN y snapshots coherentes; `git diff --check` sin salida.

- [ ] **Step 6: Commit**

```bash
git add tramalia tests docs .github/workflows/validacion.yml pyproject.toml uv.lock
git commit -m "test: cerrar experiencia terminal para beta"
```

## Final verification checklist

- [ ] `tramalia --help` y ayudas de comando son claras en ES/EN y agrupadas por intención.
- [ ] `--plain` no contamina ejecuciones posteriores; `NO_COLOR` no emite ANSI.
- [ ] JSON v1 es puro y estable para doctor, detect, log, context list y todas las operaciones automatizables de Habilidades; ninguna mutación pregunta en JSON.
- [ ] `menu` sin TTY falla con código 2 y mensaje, nunca traceback.
- [ ] `interfaz_terminal.py` es fachada y el wheel mínimo no necesita Textual.
- [ ] Cinco áreas navegables, paleta activa, F1 y foco visible.
- [ ] Habilidades muestra perfil, estado, origen, razón, dependencias, conflictos, permisos, riesgo, fuente, referencia y SHA desde modelos 03c.
- [ ] Listar, planificar, explicar, auditar, activar, desactivar y aplicar perfil comparten IDs y `ServicioHabilidades` en CLI/TUI.
- [ ] Activar, desactivar y aplicar perfil muestran plan/diff y exigen huella; una habilidad obligatoria requiere excepción completa y vigente.
- [ ] Filtrar o navegar Habilidades no consulta red; auditar o refrescar remoto son acciones explícitas y acotadas.
- [ ] 50×18 funciona; bajo el mínimo no hay mutaciones.
- [ ] Resize conserva estado/foco y no consulta de nuevo al núcleo.
- [ ] Una única mutación global; máximo una lectura activa por grupo, coalescing de solicitudes y ningún refresco obsoleto sobrescribe estado reciente.
- [ ] Cancelar termina padre/descendientes y no inicia pasos pendientes.
- [ ] Cancelar cierre antes de publicación no crea evidencia; durante publicación queda bloqueado.
- [ ] Markup/ANSI/OSC/Unicode/URLs hostiles no crean estilos, enlaces ni acciones.
- [ ] Auditoría y logs son lazy, paginados y acotados.
- [ ] Temas Rich/Textual coinciden con MkDocs y conservan contraste/símbolos.
- [ ] No se conservaron pruebas para alcanzar una cifra; cada una cubre un riesgo documentado.
