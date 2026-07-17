# Plan de implementacion 05a: motor generico de recetas

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task by task.

Steps use checkbox (`- [ ]`) syntax for tracking.

**Objetivo:** Entregar un motor generico, determinista y gobernado para catalogar, explicar, planificar, simular y ejecutar recetas declarativas sobre cualquier proyecto adoptado por Tramalia, sin depender de su tecnologia, con inventario inmutable de capacidades, confirmacion por huella, cancelacion, evidencia reproducible, CLI y documentacion ES/EN.

**Arquitectura:** El nucleo separa datos declarativos, acciones confiables registradas desde codigo, inventario observado, resolucion pura, planificacion reproducible, simulacion, ejecucion acotada, evidencia y superficies. Una receta TOML nunca aporta Python ni shell libre: solo referencia un `id_accion` conocido. `ServicioRecetas` es la unica fachada de aplicacion; al ejecutar vuelve a cargar todos los insumos dentro del bloqueo interproceso, compara la huella confirmada y despues revalida cada paso contra un estado esperado que solo avanza por efectos propios declarados.

**Tecnologias:** Python 3.11-3.14, `dataclasses`, `enum.StrEnum`, `typing.Protocol`, `tomllib`, JSON canonico, SHA-256, `pathlib`, `tramalia.core.procesos`, contratos de cancelacion/eventos de 03b, publicador de evidencia de Tramalia, pytest 8, Ruff, mypy, Semgrep, Gitleaks, MkDocs Material y mkdocstrings.

**Dependencias bloqueantes:** Plan 03a cerrado, Plan 03c cerrado, Plan 03b cerrado, Plan 04 cerrado y `v1.0.0b1` publicada y verificada. La Task 0 falla cerrado si falta cualquiera de estas condiciones. Planificar 05a antes de ese corte es valido; implementarlo no.

## Limite estricto de 05a

05a incluye:

- esquema TOML v1 y catalogo local de recetas;
- registro cerrado de acciones confiables;
- inventario inmutable de herramientas y capacidades;
- resolucion del DAG, plan reproducible y simulacion;
- ejecucion local acotada, observable y cancelable;
- evidencia de operacion v2 retrocompatible con paquetes v1;
- CLI `recetas`, JSON v1 y documentacion ES/EN;
- receta propia de referencia `inventario-proyecto`, completamente offline.

05a no incluye:

- controles OWASP, perfiles de seguridad, hallazgos ni afirmaciones de cumplimiento;
- Semgrep o Gitleaks como pasos de evaluacion; se integran en 05b;
- seleccion, cola, aplicacion o verificacion de remediaciones; se integran en 05c;
- TUI de seguridad, MCP de auditoria, XLSX o HTML; se integran en 05b-05d;
- marketplace remoto, descarga de packs, plugins ejecutables o ejecucion por IA;
- aislamiento de red a nivel del sistema operativo.

## Reglas globales

- Todo comportamiento se implementa con RED-GREEN-REFACTOR y un commit acotado por Task.
- Modulos, clases, funciones, variables, tests y archivos nuevos usan espanol ASCII.
- Comentarios internos en espanol explican invariantes, riesgos y limites; no narran sintaxis obvia.
- APIs publicas mantienen docstrings ingleses estilo Google y se incorporan al inventario mkdocstrings de 04.
- Listar, explicar, planificar y simular no escriben ni abren red. Capturar el inventario puede ejecutar localmente `--version`; es observacion local de solo lectura y se inyecta en las funciones puras.
- Activar, desactivar o actualizar una habilidad nunca ejecuta una receta.
- Ninguna ausencia de ID significa “todas”. Toda ejecucion exige receta explicita y huella vigente.
- Las recetas externas son datos: claves desconocidas, acciones desconocidas, shell libre, Python embebido, traversal, symlink, junction, colision Unicode/case-insensitive o exceso de limites fallan cerrado.
- Los argumentos de procesos son secuencias estructuradas y se delegan exclusivamente a `tramalia.core.procesos.ejecutar()`.
- `requiere_red` y la politica de red describen y bloquean por politica dentro del motor; no se documentan como sandbox de red del sistema operativo.
- El motor conserva una huella logica estable separada de IDs y timestamps volatiles de ejecucion.
- Un paso fallido bloquea sus descendientes. Las ramas independientes pueden terminar segun la politica de fallo; las acciones mutantes siempre se serializan.
- Secretos y texto hostil se sanea antes de eventos, JSON, Markdown y evidencia. No se conserva una copia “cruda” secreta.
- Los paquetes v1 siguen leyendose sin migracion ni reinterpretacion. Una receta publica un paquete v2 `tipo_paquete="receta"`, nunca un cierre ficticio.
- El catalogo propio y el codigo del motor siguen el corte PolyForm Noncommercial/comercial de 04; las plantillas emitidas a proyectos conservan Apache-2.0.
- No se fija una cantidad de pruebas. Cada prueba protege un contrato o riesgo documentado.

## Flujo contractual

```text
catalogo TOML + registro de acciones + inventario + insumos del proyecto
                              |
                              v
                    resolucion y plan puro
                              |
                    huella + simulacion
                              |
                       confirmacion humana
                              |
                 replanificar dentro del lock
                              |
             comparar huella y cruzar frontera mutable
                              |
                  ejecutar + eventos + cancelar
                              |
                   evidencia v2 reproducible
```

## Mapa final de archivos

| Ruta | Responsabilidad |
|---|---|
| `tramalia/core/serializacion.py` | Valores JSON seguros, serializacion formal/canonica y SHA-256 compartidos. |
| `tramalia/core/insumos.py` | Huellas de archivos/ausencias y contexto gobernado sin duplicar confinamiento de 03a. |
| `tramalia/core/bloqueo_operaciones.py` | Primitiva interproceso raiz-global extraida del bloqueo de 03c. |
| `tramalia/core/modelos_recetas.py` | Enums y dataclasses inmutables del dominio de recetas. |
| `tramalia/core/esquema_recetas.py` | Parser TOML cerrado y serializacion canonica del esquema 1. |
| `tramalia/core/catalogo_recetas.py` | Descubrimiento, procedencia, versiones, colisiones e integridad. |
| `tramalia/core/acciones_recetas.py` | Protocolo, descripciones y registro cerrado de acciones permitidas. |
| `tramalia/core/perfiles_procesos_recetas.py` | Perfiles de proceso confiables con argv y opciones allowlisted desde codigo. |
| `tramalia/core/acciones_recetas_propias.py` | Acciones propias `tramalia.inventario.registrar` y `tramalia.proceso.ejecutar`. |
| `tramalia/core/inventario_recetas.py` | Snapshot inmutable y huellable de herramientas/capacidades. |
| `tramalia/core/resolucion_recetas.py` | Validacion del DAG, dependencias, acciones, capacidades, permisos y red. |
| `tramalia/core/planificacion_recetas.py` | Contexto, plan puro, orden estable y huella reproducible. |
| `tramalia/core/simulacion_recetas.py` | Proyeccion pura de alcance, limites, permisos y coste tecnico. |
| `tramalia/core/ejecucion_recetas.py` | Ejecutor observable, cancelacion, concurrencia y frontera mutable. |
| `tramalia/core/redaccion.py` | Redaccion compartida sobre el saneamiento entregado por 03a. |
| `tramalia/core/modelos_evidencia.py` | Sobre v2 discriminado y artefactos genericos, conservando modelos v1. |
| `tramalia/core/evidencia_recetas.py` | Proyeccion determinista y publicacion atomica de ejecuciones de receta. |
| `tramalia/core/servicio_recetas.py` | Fachada unica de listar, explicar, planificar, simular y ejecutar. |
| `tramalia/core/errores.py` | Errores tipados de catalogo, resolucion, huella y operacion en curso. |
| `tramalia/core/evidencia.py` | Reutilizacion del escritor atomico y lectura discriminada v1/v2. |
| `tramalia/core/modelos.py` | Extensiones opcionales y finales de bitacora, sin romper constructores v1. |
| `tramalia/core/tablero.py` | Lectura y resumen honesto de paquetes `cierre` y `receta`. |
| `tramalia/catalogo/recetas_propias/inventario-proyecto/receta.toml` | Receta propia minima, util, offline y de solo lectura. |
| `tramalia/catalogo/recetas_propias/inventario-proyecto/LICENCIA.txt` | Licencia y procedencia explicitas de la receta incluida. |
| `tramalia/cli/recetas.py` | Manejadores delgados y serializadores explicitos de recetas. |
| `tramalia/cli/catalogo_comandos.py` | Registro canonico de `recetas` y sus cinco subcomandos. |
| `tramalia/cli/comandos.py` | Enlace de IDs de manejador, sin parser paralelo. |
| `tramalia/cli/salida_estructurada.py` | Registro de serializadores JSON v1 para modelos de receta. |
| `tramalia/i18n/es.json`, `tramalia/i18n/en.json` | Nombres, ayuda, errores y siguientes acciones con paridad. |
| `docs/recetas.md`, `docs/recetas.en.md` | Conceptos, limites y modelo mental. |
| `docs/tutorial-recetas.md`, `docs/tutorial-recetas.en.md` | Recorrido completo con `inventario-proyecto`. |
| `docs/guias/recetas.md`, `docs/guias/recetas.en.md` | Tareas, recuperacion y solucion de problemas. |
| `docs/referencia/recetas.md`, `docs/referencia/recetas.en.md` | CLI, JSON y esquema TOML. |
| `docs/desarrollo/recetas.md`, `docs/desarrollo/recetas.en.md` | API mkdocstrings, arquitectura y extensibilidad segura. |
| `docs/desarrollo/crear-recetas.md`, `docs/desarrollo/crear-recetas.en.md` | Autoria, versionado, pruebas y licencia de packs/recetas. |
| `docs/privacidad-recetas.md`, `docs/privacidad-recetas.en.md` | Datos sensibles, redaccion, retencion y borrado de evidencia. |
| `docs/migracion-recetas.md`, `docs/migracion-recetas.en.md` | Versiones de esquema, compatibilidad y migracion futura. |
| `scripts/generar_capturas_cli_recetas.py` | Capturas SVG deterministas del recorrido CLI, sin datos de la maquina. |
| `docs/assets/cli/recetas-*.svg` | Activos documentales generados y revisados. |
| `docs/desarrollo/inventario_api.toml` | Propiedad documental de los modulos publicos 05a. |
| `mkdocs.yml`, `pyproject.toml`, `CHANGELOG.md` | Navegacion, contenido del paquete y notas del corte. |
| `tests/recursos/recetas/` | Recetas validas, limites y casos hostiles sin secretos reales. |
| `tests/unidad/test_*recetas*.py` | Modelos, parser, inventario, resolucion, plan y simulacion. |
| `tests/integracion/test_*recetas*.py` | Procesos, cancelacion, lock, drift, evidencia y CLI. |
| `tests/contratos/test_entrega_05a.py` | Limite de dominio, API, paquete, documentacion y no acoplamiento con 05b/05c. |

## Contratos congelados

Los bloques Python/TOML de esta seccion son el codigo normativo minimo de la implementacion. Las pruebas RED construyen exactamente estos tipos y firmas; una Task no puede cambiarlos silenciosamente. Si una incompatibilidad real con 03a/03c/03b/04 obliga a variar una firma, primero se actualizan este plan, `test_prerrequisitos_05a.py` y el contrato consumidor en un commit documental separado.

### Infraestructura compartida

05a consume `resolver_ruta_confinada()`, `leer_texto_confinado()` y `sanear_texto_externo()` de 03a. Extrae codigo ya caracterizado; no crea implementaciones paralelas.

```python
# tramalia/core/serializacion.py
ValorJSON: TypeAlias = str | int | float | bool | None | list["ValorJSON"] | dict[str, "ValorJSON"]

class ErrorSerializacionSegura(ValueError):
    pass

def proyectar_json_publico(
    valor: object,
    *,
    raiz: Path | None = None,
) -> ValorJSON: ...

def normalizar_detalle_error_compatible(valor: object) -> ValorJSON: ...

def serializar_json_formal(valor: ValorJSON, *, indentado: bool = True) -> bytes: ...

def serializar_json_canonico(valor: ValorJSON) -> bytes: ...

def calcular_huella_json(valor: ValorJSON) -> str: ...


# tramalia/core/insumos.py
@dataclass(frozen=True, slots=True)
class HuellaInsumo:
    nombre: str
    ruta_relativa: str
    estado: Literal["presente", "ausente"]
    bytes_totales: int
    sha256: str | None

def capturar_huella_insumo(
    raiz: Path,
    ruta_relativa: Path,
    *,
    nombre: str,
    maximo_bytes: int = 4_194_304,
) -> HuellaInsumo: ...


# tramalia/core/bloqueo_operaciones.py
@dataclass(frozen=True, slots=True)
class BloqueoOperacion:
    id_operacion: str
    nombre: str

@contextmanager
def adquirir_bloqueo_operacion(
    raiz: Path,
    *,
    id_operacion: str,
    nombre: str,
    limite_segundos: float = 0.0,
) -> Iterator[BloqueoOperacion]: ...
```

`serializar_json_canonico()` y `calcular_huella_json()` son lossless sobre `ValorJSON`: no redactan ni sustituyen valores, por lo que dos insumos permitidos distintos nunca colisionan por saneamiento. Solo reciben proyecciones explicitas de modelos que prohíben secretos. `proyectar_json_publico()` aplica confinamiento y redaccion para CLI/eventos/evidencia; un `Path` sin `raiz` falla y, con `raiz`, solo una ruta confinada se vuelve relativa. `normalizar_detalle_error_compatible()` conserva los marcadores historicos de errores para no cambiar JSON v1. `serializacion.py` importa solo stdlib y define `ErrorSerializacionSegura`; `errores.py` depende de el, nunca al reves, y las fachadas traducen el error al `ErrorEntradaInsegura` publico cuando corresponde. Una huella nunca contiene ruta absoluta, `mtime`, timestamp de ejecucion, PID o UUID. El bloqueo es raiz-global, interproceso, confinado, fail-closed y compartido por habilidades y recetas; `CoordinadorOperaciones` sigue siendo coordinacion en memoria para UI y no lo reemplaza.

### Modelos de recetas

```python
# tramalia/core/modelos_recetas.py
class ValorOrigenReceta(StrEnum):
    PROPIA = "propia"
    PROYECTO = "proyecto"

class ValorMutabilidadReceta(StrEnum):
    LECTURA = "lectura"
    MUTACION = "mutacion"

class ValorPoliticaRedReceta(StrEnum):
    SIN_RED = "sin_red"
    SOLO_LOCAL = "solo_local"
    PERMITIDA = "permitida"

class ValorPoliticaFalloReceta(StrEnum):
    CONTINUAR_RAMAS_INDEPENDIENTES = "continuar_ramas_independientes"
    DETENER_TODO = "detener_todo"

class ValorEstadoHerramientaReceta(StrEnum):
    PRESENTE = "presente"
    AUSENTE = "ausente"
    INDETERMINADA = "indeterminada"

class ValorTipoPrecondicionReceta(StrEnum):
    CAPACIDAD = "capacidad"
    HERRAMIENTA_PRESENTE = "herramienta_presente"
    ARCHIVO_PRESENTE = "archivo_presente"
    ARCHIVO_AUSENTE = "archivo_ausente"

class ValorFuenteEvidenciaReceta(StrEnum):
    PLAN = "plan"
    INVENTARIO = "inventario"
    RESULTADO_PASO = "resultado_paso"
    EVENTOS = "eventos"
    TRANSICIONES = "transiciones"

class ValorDatosSensiblesReceta(StrEnum):
    NINGUNO = "ninguno"
    METADATOS_PROYECTO = "metadatos_proyecto"
    CODIGO_FUENTE = "codigo_fuente"
    SECRETOS = "secretos"
class ValorModoEjecucionAccionReceta(StrEnum):
    INTERNA_ACOTADA = "interna_acotada"
    PROCESO_GOBERNADO = "proceso_gobernado"


class ValorEstadoPasoReceta(StrEnum):
    COMPLETADO = "completado"
    FALLIDO = "fallido"
    CANCELADO = "cancelado"
    BLOQUEADO = "bloqueado"
    OMITIDO = "omitido"

class ValorEstadoEjecucionReceta(StrEnum):
    EJECUTADA = "ejecutada"
    COMPLETADA = "completada"
    FALLIDA = "fallida"
    CANCELADA = "cancelada"
    BLOQUEADA = "bloqueada"

ValorArgumentoReceta = str | tuple[str, ...]

@dataclass(frozen=True, slots=True)
class LimitesPasoReceta:
    limite_segundos: float = 60.0
    limite_salida_bytes_por_canal: int = 8_388_608

@dataclass(frozen=True, slots=True)
class PrecondicionReceta:
    id_precondicion: str
    tipo: ValorTipoPrecondicionReceta
    valor: str

@dataclass(frozen=True, slots=True)
class PuertaReceta:
    id_puerta: str
    pasos: tuple[str, ...]
    estados_aceptados: tuple[ValorEstadoPasoReceta, ...]
    bloqueante: bool = True

@dataclass(frozen=True, slots=True)
class DeclaracionEvidenciaReceta:
    id_evidencia: str
    fuente: ValorFuenteEvidenciaReceta
    paso: str | None = None
    obligatoria: bool = True

@dataclass(frozen=True, slots=True)
class PasoReceta:
    id_paso: str
    id_accion: str
    dependencias: tuple[str, ...] = ()
    argumentos: tuple[tuple[str, ValorArgumentoReceta], ...] = ()
    insumos: tuple[str, ...] = ()
    efectos: tuple[str, ...] = ()
    limites: LimitesPasoReceta = LimitesPasoReceta()

@dataclass(frozen=True, slots=True)
class Receta:
    version_esquema: int
    id_receta: str
    version: str
    titulo: str
    descripcion: str
    origen: ValorOrigenReceta
    referencia_origen: str
    licencia: str
    sha256_fuente: str
    hash_contenido: str
    politica_fallo: ValorPoliticaFalloReceta
    politica_red: ValorPoliticaRedReceta
    permisos: tuple[str, ...]
    datos_sensibles: tuple[ValorDatosSensiblesReceta, ...]
    concurrencia_maxima: int
    precondiciones: tuple[PrecondicionReceta, ...]
    puertas: tuple[PuertaReceta, ...]
    evidencias: tuple[DeclaracionEvidenciaReceta, ...]
    pasos: tuple[PasoReceta, ...]

@dataclass(frozen=True, slots=True)
class SolicitudReceta:
    id_receta: str
    version: str | None = None
    id_tarea: str | None = None

@dataclass(frozen=True, slots=True)
class PoliticaEjecucionRecetas:
    id_politica: str
    procedencia: str
    permisos_admitidos: tuple[str, ...]
    datos_sensibles_admitidos: tuple[ValorDatosSensiblesReceta, ...]
    politica_red_maxima: ValorPoliticaRedReceta
    concurrencia_maxima: int = 1

def crear_politica_recetas_predeterminada() -> PoliticaEjecucionRecetas: ...

@dataclass(frozen=True, slots=True)
class HerramientaInventarioReceta:
    clave: str
    comando: str
    estado: ValorEstadoHerramientaReceta
    identidad_ejecutable: str | None
    sha256_ejecutable: str | None
    version: str | None
    capacidades: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class InventarioRecetas:
    version_esquema: int
    herramientas: tuple[HerramientaInventarioReceta, ...]
    capacidades_nucleo: tuple[str, ...]
    capacidades_habilidades: tuple[str, ...]
    huella_habilidades: str | None
    huella: str

@dataclass(frozen=True, slots=True)
class BloqueoReceta:
    codigo: str
    paso: str | None
    mensaje: str
    sugerencia: str

@dataclass(frozen=True, slots=True)
class PasoPlanReceta:
    id_paso: str
    id_accion: str
    version_accion: str
    modo_ejecucion: ValorModoEjecucionAccionReceta
    id_perfil_proceso: str | None
    version_perfil_proceso: str | None
    hash_perfil_proceso: str | None
    descripcion_accion: str
    capacidades_requeridas: tuple[str, ...]
    dependencias: tuple[str, ...]
    argumentos: tuple[tuple[str, ValorArgumentoReceta], ...]
    insumos: tuple[HuellaInsumo, ...]
    efectos: tuple[str, ...]
    huellas_efectos_iniciales: tuple[HuellaInsumo, ...]
    mutabilidad: ValorMutabilidadReceta
    permisos: tuple[str, ...]
    datos_sensibles: tuple[ValorDatosSensiblesReceta, ...]
    politica_red: ValorPoliticaRedReceta
    herramienta: str | None
    version_herramienta: str | None
    identidad_ejecutable: str | None
    sha256_ejecutable: str | None
    limites: LimitesPasoReceta

@dataclass(frozen=True, slots=True)
class PlanReceta:
    version_esquema: int
    solicitud: SolicitudReceta
    receta: Receta
    inventario: InventarioRecetas
    politica: PoliticaEjecucionRecetas
    identidad_git_inicial: EstadoGit
    pasos: tuple[PasoPlanReceta, ...]
    bloqueos: tuple[BloqueoReceta, ...]
    advertencias: tuple[str, ...]
    huella: str

    @property
    def ejecutable(self) -> bool: ...

    @property
    def huellas_insumos(self) -> tuple[HuellaInsumo, ...]: ...

    @property
    def huellas_rutas_gobernadas(self) -> tuple[HuellaInsumo, ...]: ...

@dataclass(frozen=True, slots=True)
class EstadoEsperadoEjecucionReceta:
    huella_componentes_inmutables: str
    identidad_git: EstadoGit
    rutas_git_modificadas: tuple[str, ...]
    huellas_rutas_gobernadas: tuple[HuellaInsumo, ...]
    efectos_aplicados: tuple[str, ...]
    huella: str

@dataclass(frozen=True, slots=True)
class TransicionContextoReceta:
    id_paso: str
    aprobada: bool
    huella_antes: str
    huella_despues: str
    efectos_observados: tuple[str, ...]
    efectos_aceptados: tuple[str, ...]
    motivo: str

@dataclass(frozen=True, slots=True)
class SimulacionReceta:
    id_receta: str
    version_receta: str
    huella: str
    pasos: tuple[PasoPlanReceta, ...]
    bloqueos: tuple[BloqueoReceta, ...]
    permisos: tuple[str, ...]
    datos_sensibles: tuple[ValorDatosSensiblesReceta, ...]
    politicas_red: tuple[ValorPoliticaRedReceta, ...]
    duracion_maxima_segundos: float
    maximo_salida_bytes: int
    concurrencia_maxima: int
    mutante: bool
    tokens_estimados: int

@dataclass(frozen=True, slots=True)
class ResultadoPasoReceta:
    id_paso: str
    estado: ValorEstadoPasoReceta
    inicio_utc: datetime | None
    fin_utc: datetime | None
    duracion_segundos: float | None
    proceso: ResultadoProceso | None
    motivo: str

@dataclass(frozen=True, slots=True)
class ResultadoPuertaReceta:
    id_puerta: str
    aprobada: bool
    bloqueante: bool
    motivo: str

@dataclass(frozen=True, slots=True)
class ResultadoEjecucionReceta:
    id_operacion: str
    estado: ValorEstadoEjecucionReceta
    plan: PlanReceta
    codigo: str
    motivo: str
    resultados: tuple[ResultadoPasoReceta, ...]
    resultados_puertas: tuple[ResultadoPuertaReceta, ...]
    transiciones_contexto: tuple[TransicionContextoReceta, ...]
    deriva_detectada: bool
    id_paquete: str | None = None
    advertencias: tuple[str, ...] = ()
    ruta_paquete: Path | None = None
```

Solo las colecciones con semantica de conjunto —permisos, capacidades, efectos e inventarios— se deduplican y ordenan al construir. Pasos, resultados, transiciones y eventos conservan orden topologico u observado. Los modelos rechazan IDs no portables, versiones vacias, claves duplicadas, NaN/infinito, limites fuera de rango, tiempos no UTC, fin anterior al inicio, dependencias invalidas e incoherencia entre estado, proceso y paquete. Un paso `BLOQUEADO|OMITIDO` exige tiempos y duracion `None`; un paso iniciado exige los tres valores. `PlanReceta.huellas_insumos` y `huellas_rutas_gobernadas` son uniones canonicas derivadas de pasos; la segunda incluye tambien el estado inicial de cada ruta de efecto, de modo que crear, reemplazar o borrar un destino entre confirmar y ejecutar invalida la huella. La raiz fisica no forma parte de `PlanReceta`; el servicio la conserva como contexto y el plan contiene solo rutas relativas portables.
`ResultadoEjecucionReceta` siempre lleva un `codigo` estable. Los estados `FALLIDA`, `CANCELADA` y `BLOQUEADA` exigen ademas `motivo` no vacio y saneado; `EJECUTADA` y `COMPLETADA` pueden usar motivo vacio. Un fallo de publicacion produce `codigo="evidencia_publicacion_fallida"`, estado `FALLIDA`, paquete/ruta `None` y conserva resultados y advertencias, por lo que nunca puede presentarse como exito.

`EstadoEsperadoEjecucionReceta` es interno y evolutivo; no reemplaza ni modifica la huella del plan que confirmo la persona. Su huella separa componentes inmutables —receta, acciones/perfiles, politica, inventario y HEAD/rama Git— del estado permitido de rutas gobernadas y del conjunto de efectos ya aplicados. Cada avance genera una `TransicionContextoReceta` que se conserva en resultado, eventos y evidencia.


Para un insumo ausente, `estado="ausente"`, `bytes_totales=0` y `sha256=None`; la huella agregada sigue cambiando porque serializa conjuntamente nombre, ruta, estado, bytes y SHA. No se inventa un digest que pueda confundirse con un archivo vacio.

`crear_politica_recetas_predeterminada()` devuelve `id_politica="05a-local-segura"`, `procedencia="nucleo:05a"`, permisos `("leer_proyecto",)`, datos `("metadatos_proyecto",)`, red `SIN_RED` y concurrencia 1. La CLI usa esa fabrica salvo que un consumidor interno aporte una politica gobernada mas restrictiva o explicitamente ampliada; nunca deriva autorizaciones desde la receta. `SECRETOS` no esta admitido por ninguna politica o accion propia de 05a.

### Catalogo, acciones e inventario

```python
# tramalia/core/esquema_recetas.py
def analizar_receta_toml(
    contenido: bytes,
    *,
    origen: ValorOrigenReceta,
    referencia: str,
) -> Receta: ...

def serializar_receta_toml(receta: Receta) -> bytes: ...


# tramalia/core/catalogo_recetas.py
@dataclass(frozen=True, slots=True)
class FuenteCatalogoRecetas:
    raiz: Path
    origen: ValorOrigenReceta

@dataclass(frozen=True, slots=True)
class CatalogoRecetas:
    recetas: tuple[Receta, ...]
    huella: str

@dataclass(frozen=True, slots=True)
class ReferenciaReceta:
    id_receta: str
    version: str | None

def separar_referencia_receta(valor: str) -> ReferenciaReceta: ...

def cargar_catalogo_recetas(
    fuentes: Sequence[FuenteCatalogoRecetas],
) -> CatalogoRecetas: ...

def obtener_receta(
    catalogo: CatalogoRecetas,
    id_receta: str,
    version: str | None = None,
) -> Receta: ...


# tramalia/core/acciones_recetas.py
@dataclass(frozen=True, slots=True)
class DefinicionAccionReceta:
    id_accion: str
    version: str
    descripcion: str
    capacidades_requeridas: tuple[str, ...]
    datos_sensibles: tuple[ValorDatosSensiblesReceta, ...]
    modo_ejecucion: ValorModoEjecucionAccionReceta

@dataclass(frozen=True, slots=True)
class DescripcionPasoAccionReceta:
    definicion: DefinicionAccionReceta
    mutabilidad: ValorMutabilidadReceta
    permisos: tuple[str, ...]
    politica_red: ValorPoliticaRedReceta
    herramienta: str | None
    id_perfil_proceso: str | None
    version_perfil_proceso: str | None
    hash_perfil_proceso: str | None

@dataclass(frozen=True, slots=True)
class ContextoAccionReceta:
    raiz: Path
    paso: PasoPlanReceta
    estado_esperado: EstadoEsperadoEjecucionReceta
    inventario: InventarioRecetas
    id_operacion: str
    senal_cancelacion: SenalCancelacion
    al_linea: Callable[[str, str], None] | None

    reloj_monotono: Callable[[], float]
    plazo_monotono: float

    def comprobar_cancelacion_y_plazo(self) -> None: ...

@dataclass(frozen=True, slots=True)
class ResultadoAccionReceta:
    estado: ValorEstadoPasoReceta
    proceso: ResultadoProceso | None
    motivo: str
    efectos_observados: tuple[str, ...] = ()

class ProtocoloAccionReceta(Protocol):
    @property
    def definicion(self) -> DefinicionAccionReceta: ...

    def describir_paso(
        self,
        argumentos: tuple[tuple[str, ValorArgumentoReceta], ...],
    ) -> DescripcionPasoAccionReceta: ...
    def ejecutar(self, contexto: ContextoAccionReceta) -> ResultadoAccionReceta: ...

class RegistroAccionesReceta:
    def registrar(self, accion: ProtocoloAccionReceta) -> None: ...
    def obtener(self, id_accion: str) -> ProtocoloAccionReceta: ...
    def definiciones(self) -> tuple[DefinicionAccionReceta, ...]: ...


# tramalia/core/perfiles_procesos_recetas.py
class ValorTipoOpcionProcesoReceta(StrEnum):
    ELECCION = "eleccion"
    RUTA_CONFINADA = "ruta_confinada"
    ENTERO_ACOTADO = "entero_acotado"
    TEXTO_PORTABLE = "texto_portable"

@dataclass(frozen=True, slots=True)
class OpcionPerfilProcesoReceta:
    clave: str
    bandera: str | None
    tipo: ValorTipoOpcionProcesoReceta
    valores_permitidos: tuple[str, ...] = ()
    minimo: int | None = None
    maximo: int | None = None

@dataclass(frozen=True, slots=True)
class PerfilProcesoReceta:
    id_perfil: str
    herramienta: str
    version: str
    argumentos_fijos: tuple[str, ...]
    opciones: tuple[OpcionPerfilProcesoReceta, ...]
    mutabilidad: ValorMutabilidadReceta
    permisos: tuple[str, ...]
    datos_sensibles: tuple[ValorDatosSensiblesReceta, ...]
    politica_red: ValorPoliticaRedReceta


    @property
    def hash_definicion(self) -> str: ...
class RegistroPerfilesProcesoReceta:
    def registrar(self, perfil: PerfilProcesoReceta) -> None: ...
    def obtener(self, id_perfil: str) -> PerfilProcesoReceta: ...
    def listar(self) -> tuple[PerfilProcesoReceta, ...]: ...


# tramalia/core/inventario_recetas.py
def capturar_inventario_recetas(
    herramientas: Sequence[Herramienta],
    *,
    estados_habilidades: Sequence[EstadoHabilidad] = (),
    huella_habilidades: str | None = None,
    sondeador: Callable[[Herramienta], EstadoHerramienta] = sondear,
) -> InventarioRecetas: ...
```

`PerfilProcesoReceta.hash_definicion` es SHA-256 de una proyeccion JSON canonica con ID, version, herramienta logica, argumentos fijos, definiciones completas de opciones, mutabilidad, permisos, datos sensibles y politica de red; nunca contiene la ruta fisica observada. `tramalia.proceso.ejecutar` exige `perfil=<id registrado>` y solo acepta las opciones nombradas por ese perfil. El perfil confiable fija herramienta, argv base, flags, validadores, mutabilidad, permisos y red; una receta TOML no puede escoger ejecutable, verbos o flags libres. Asi `node -e`, `python -c`, `git push`, `uv run`, carga de plugins, scripts arbitrarios y opciones de red quedan imposibles salvo que codigo propio registre un perfil especifico que los declare y gobierne. No acepta `shell`, operadores, cadena de comando ni entorno arbitrario. `tramalia.inventario.registrar` produce el manifiesto de inventario de la receta propia sin red ni mutacion del proyecto.

Inmediatamente antes de iniciar un proceso, la accion propia vuelve a obtener el perfil confiable, recalcula su hash canonico y compara ID/version/hash con `PasoPlanReceta`; despues resuelve la herramienta y compara identidad/version/SHA-256 con `HerramientaInventarioReceta`. Solo entonces entrega la ruta absoluta efimera y argv allowlisted a `procesos.ejecutar()`. El runner 03b sigue drenando ambos pipes y calcula bytes/SHA completos con su tope interno de 8 MiB por canal; la accion envuelve `al_linea` y el resultado para publicar como maximo `limite_salida_bytes_por_canal` en stdout y stderr, sin dejar de drenar ni perder contadores/SHA. El limite de receta nunca puede superar el tope 03b. La proyeccion publica de `ResultadoProceso.comando` sustituye el ejecutable fisico por la identidad logica de herramienta y conserva solo opciones declaradas ya saneadas; rutas absolutas, argumentos secretos y argv crudo no entran a modelos publicos, huellas, eventos o evidencia. Un cambio de perfil o reemplazo de ejecutable entre planificacion y lanzamiento falla como drift y no inicia el proceso.

05a distingue `PROCESO_GOBERNADO`, cuyo timeout duro siempre lo aplica `procesos.ejecutar()`, de `INTERNA_ACOTADA`. Esta ultima queda limitada a acciones propias incluidas, con algoritmo terminante, sin subprocess, red ni E/S bloqueante, y recibe reloj monotono, plazo absoluto y cancelacion; debe llamar `comprobar_cancelacion_y_plazo()` antes de trabajar y en cada bucle acotado. No se admiten acciones internas de terceros en 05a. El pool no promete matar Python bloqueado: violar este contrato de codigo confiable es un defecto de programacion fuera del aislamiento ofrecido; las pruebas cubren plazo cooperativo interno y timeout duro de procesos por separado.

La fuente propia esta bajo `tramalia/catalogo/recetas_propias/`; la fuente de proyecto opcional bajo `.tramalia/recetas/`. Cada archivo `receta.toml` tiene maximo 1 MiB, 128 pasos, 32 dependencias por paso, 64 argumentos por paso y concurrencia de 1 a 4. No hay fuentes remotas en 05a. `sha256_fuente` cubre los bytes UTF-8 originales, incluidos comentarios/formato; `hash_contenido` cubre la proyeccion semantica canonica. El round-trip del serializador compara igualdad semantica excluyendo `sha256_fuente`, salvo cuando la entrada ya era canonica. Ambos hashes entran en la huella, por lo que cualquier cambio de bytes invalida confirmacion aunque conserve semantica. El indice usa `(id_receta, version)`; `separar_referencia_receta()` es el unico parser de `id@version` para catalogo y CLI. Si existen varias versiones y se omite `version`, se devuelve un error tipado en lugar de elegir “la ultima”.

### Resolucion, planificacion y simulacion

```python
# tramalia/core/resolucion_recetas.py
@dataclass(frozen=True, slots=True)
class PasoResueltoReceta:
    id_paso: str
    id_accion: str
    version_accion: str
    dependencias: tuple[str, ...]
    argumentos: tuple[tuple[str, ValorArgumentoReceta], ...]
    rutas_insumos: tuple[str, ...]
    efectos: tuple[str, ...]
    descripcion_accion: DescripcionPasoAccionReceta
    limites: LimitesPasoReceta

@dataclass(frozen=True, slots=True)
class ResolucionReceta:
    pasos: tuple[PasoResueltoReceta, ...]
    bloqueos: tuple[BloqueoReceta, ...]
    advertencias: tuple[str, ...]

def resolver_receta(
    receta: Receta,
    registro: RegistroAccionesReceta,
    politica: PoliticaEjecucionRecetas,
    contexto: "ContextoPlanificacionReceta",
) -> ResolucionReceta: ...


# tramalia/core/planificacion_recetas.py
@dataclass(frozen=True, slots=True)
class ContextoPlanificacionReceta:
    identidad_git: EstadoGit
    inventario: InventarioRecetas
    rutas_git_modificadas: tuple[str, ...]
    huellas_rutas_gobernadas: tuple[HuellaInsumo, ...]

def capturar_contexto_planificacion_receta(
    raiz: Path,
    receta: Receta,
    inventario: InventarioRecetas,
) -> ContextoPlanificacionReceta: ...

def planificar_receta(
    receta: Receta,
    solicitud: SolicitudReceta,
    resolucion: ResolucionReceta,
    contexto: ContextoPlanificacionReceta,
    politica: PoliticaEjecucionRecetas,
) -> PlanReceta: ...

def crear_estado_esperado_ejecucion_receta(
    plan: PlanReceta,
) -> EstadoEsperadoEjecucionReceta: ...


# tramalia/core/simulacion_recetas.py
def simular_receta(plan: PlanReceta) -> SimulacionReceta: ...
```

El orden topologico usa desempate lexicografico por `id_paso`. La huella SHA-256 cubre esquema, `sha256_fuente`/`hash_contenido` de receta, solicitud, versiones/definiciones/modos de acciones, ID/version/hash canonico de cada perfil de proceso, inventario, politica efectiva, identidad Git logica, rutas Git modificadas, insumos, estado inicial de rutas de efecto, pasos, permisos, red, politica de fallo y limites. La raiz absoluta, IDs de operacion y tiempo quedan fuera. Los insumos y efectos son rutas relativas exactas en 05a; no se aceptan globs.

La receta declara lo que solicita; `PoliticaEjecucionRecetas` representa lo que el proyecto/anfitrion admite. Resolver exige que permisos y categorias de datos de cada accion sean subconjunto de receta y politica, y compara red mediante un orden explicito `SIN_RED < SOLO_LOCAL < PERMITIDA`: accion <= receta <= politica maxima. Ningun pack puede ampliar la politica del anfitrion. La politica y su procedencia entran en el plan y la huella; la simulacion muestra datos sensibles y presupuesto tecnico antes de confirmar.

La simulacion se deriva solo de `PlanReceta`: presenta pasos, bloqueos, capacidades, permisos, red, mutaciones, tiempo maximo, salida maxima y concurrencia. `tokens_estimados` es siempre `0` porque 05a no invoca IA. No inventa coste monetario.

### Ejecucion observable

```python
# tramalia/core/ejecucion_recetas.py
def ejecutar_plan_receta(
    raiz: Path,
    plan: PlanReceta,
    registro: RegistroAccionesReceta,
    *,
    id_operacion: str,
    reloj_utc: Callable[[], datetime],
    estado_esperado_inicial: EstadoEsperadoEjecucionReceta,
    revalidar_antes_de_paso: Callable[
        [PasoPlanReceta, EstadoEsperadoEjecucionReceta],
        None,
    ],
    avanzar_contexto_despues_de_paso: Callable[
        [PasoPlanReceta, EstadoEsperadoEjecucionReceta],
        tuple[EstadoEsperadoEjecucionReceta | None, TransicionContextoReceta],
    ],
    senal_cancelacion: SenalCancelacion | None = None,
    al_evento: Callable[[EventoOperacion], None] | None = None,
    al_cruzar_limite_mutacion: Callable[[EventoOperacion], None] | None = None,
) -> ResultadoEjecucionReceta: ...
```

La concurrencia predeterminada es 1 y el rango permitido es 1-4. Solo ramas independientes compuestas por acciones de lectura pueden ejecutarse en paralelo. El ejecutor mantiene `estado_esperado` desde el snapshot confirmado. Antes de invocar cada paso llama obligatoriamente `revalidar_antes_de_paso(paso, estado_esperado)`; el servicio recaptura componentes inmutables, HEAD/rama, rutas Git modificadas y todas las rutas gobernadas, y exige igualdad con ese estado. Si falla, ese paso y cualquier nuevo despacho se abortan sin invocar la accion.

Despues de cada accion, una seccion serializada llama `avanzar_contexto_despues_de_paso()`. Para lectura exige que el contexto siga identico. Para mutacion compara antes/despues, exige HEAD/rama y componentes inmutables sin cambios, y solo acepta cambios de contenido/estado Git cuya ruta relativa pertenezca a `paso.efectos`. El callback siempre devuelve una transicion: si hay deriva, marca `aprobada=False`, conserva huella/efectos observados saneados y entrega estado nuevo `None`; el ejecutor falla y no despacha otro paso. Una mutacion valida devuelve `aprobada=True`, actualiza las huellas de rutas —incluidos insumos de pasos posteriores—, agrega sus efectos aplicados y recalcula la huella esperada, sin alterar `plan.huella`. Los conflictos escritura-lectura y escritura-escritura deben estar ordenados por dependencias del DAG; resolver bloquea una receta que no declare esa relacion. Asi una mutacion legitima seguida de un consumidor puede continuar sin confundirse con deriva externa.

Para una accion mutante, primero espera que no haya otra accion activa, revalida inmediatamente antes de `MUTANDO` y exige que `al_cruzar_limite_mutacion` termine correctamente una sola vez antes del primer efecto. La cancelacion previa a esa frontera no escribe; despues conserva resultados y transiciones parciales y no inicia pasos nuevos. El lock coordina procesos Tramalia, pero no es un sandbox contra editores externos: aun queda un intervalo TOCTOU minimo; un cambio externo dentro de una ruta de efecto durante la accion no se puede atribuir con certeza y se documenta como riesgo residual. El perfil/ejecutable se comprueba otra vez al lanzar procesos. `procesos.ejecutar()` es el unico ejecutor de procesos y sus codigos 127, 124, 130, timeout, cancelacion o salida no cero nunca se traducen a exito.

Los eventos reutilizan `EventoOperacion` y los tipos finales de 03b: `INICIADA`, `PASO_INICIADO`, `SALIDA`, `PASO_TERMINADO`, `PUBLICANDO`, `COMPLETADA`, `CANCELADA` y `FALLIDA`. Se agrega solamente `MUTANDO="mutando"` para la frontera previa al primer efecto, porque `PUBLICANDO` conserva su significado de inicio de publicacion de evidencia. `PASO_TERMINADO` incluye, cuando corresponde, huellas anterior/posterior y rutas aceptadas ya saneadas; no se agrega otro tipo para la transicion. El ejecutor emite hasta los eventos de pasos y devuelve `EJECUTADA|FALLIDA|CANCELADA|BLOQUEADA`; `ServicioRecetas` emite `PUBLICANDO` y el evento terminal solo despues de publicar o fallar de forma definitiva. No se crea un segundo bus. Los eventos en memoria conservan orden real; al persistir se normalizan por ordinal topologico/fase y no por timestamp sujeto a carreras.

### Evidencia v2 y redaccion

```python
# tramalia/core/modelos_evidencia.py
class ValorTipoPaqueteEvidencia(StrEnum):
    CIERRE = "cierre"
    RECETA = "receta"

@dataclass(frozen=True, slots=True)
class ArtefactoEvidencia:
    ruta_relativa: str
    bytes_totales: int
    sha256: str

@dataclass(frozen=True, slots=True)
class MetadatosPaqueteEvidenciaV2:
    version_esquema: Literal[2]
    tipo_paquete: Literal[ValorTipoPaqueteEvidencia.RECETA]
    id_paquete: str
    id_tarea: str
    id_operacion: str
    inicio_utc: datetime
    fin_utc: datetime
    resultado_operacion: str
    huella_contenido: str
    artefactos: tuple[ArtefactoEvidencia, ...]
    identidad_git_inicial: EstadoGit
    identidad_git_final: EstadoGit
    cadena_herramientas: tuple[tuple[str, str | None], ...]

@dataclass(frozen=True, slots=True)
class SobrePaqueteEvidenciaV1:
    version_esquema: Literal[1]
    tipo_paquete: Literal[ValorTipoPaqueteEvidencia.CIERRE]
    metadatos: MetadatosPaqueteEvidencia

@dataclass(frozen=True, slots=True)
class SobrePaqueteEvidenciaV2:
    version_esquema: Literal[2]
    tipo_paquete: Literal[ValorTipoPaqueteEvidencia.RECETA]
    metadatos: MetadatosPaqueteEvidenciaV2

SobrePaqueteEvidencia: TypeAlias = SobrePaqueteEvidenciaV1 | SobrePaqueteEvidenciaV2

@dataclass(frozen=True, slots=True)
class PaqueteEvidenciaV2:
    metadatos: MetadatosPaqueteEvidenciaV2
    ruta: Path


# tramalia/core/evidencia.py
def publicar_paquete_v2(
    raiz: Path,
    metadatos: MetadatosPaqueteEvidenciaV2,
    archivos: Mapping[str, bytes],
) -> PaqueteEvidenciaV2: ...

def leer_sobre_paquete(
    raiz: Path,
    id_paquete: str,
) -> SobrePaqueteEvidencia: ...


# tramalia/core/evidencia_recetas.py
def construir_archivos_evidencia_receta(
    plan: PlanReceta,
    resultado: ResultadoEjecucionReceta,
    eventos: Sequence[EventoOperacion],
    *,
    reloj_utc: Callable[[], datetime],
) -> Mapping[str, bytes]: ...

def publicar_evidencia_receta(
    raiz: Path,
    plan: PlanReceta,
    resultado: ResultadoEjecucionReceta,
    eventos: Sequence[EventoOperacion],
    *,
    id_paquete: str,
    id_tarea: str,
    reloj_utc: Callable[[], datetime],
) -> PaqueteEvidenciaV2: ...
```

El escritor atomico privado de `evidencia.py` se extrae y comparte; no se crea otro arbol ni otra convencion de publicacion. Los paquetes v1 conservan su `metadatos.json`, `traspaso.md`, `estado_cierre` y comportamiento byte por byte. El paquete v2 de receta contiene como minimo:

- `metadatos.json` con discriminador y hashes de todos los artefactos;
- `manifiesto.json` con receta, plan, inventario, huella y resultado;
- `plan.json`;
- `inventario.json`;
- `resultados.jsonl`;
- `transiciones.jsonl`;
- `eventos.jsonl`;
- `resumen.md`.

La bitacora acepta `operacion="receta"` y campos opcionales finales de texto `tipo_paquete` y `resultado_operacion`; no rellena `estado_cierre` ni `EjecucionPuertas` ficticios. `modelos.py` no importa `modelos_evidencia.py`: el modulo v2 depende de los tipos hoja v1, y el lector devuelve la union discriminada, evitando el ciclo. `artefactos` enumera los archivos de contenido y excluye `metadatos.json` para evitar un hash circular; la integridad de metadatos se valida por esquema/publicacion atomica. Lectores antiguos de v1 siguen funcionando. Un resultado completado solo se devuelve despues de publicar y releer/verificar el paquete. Si falla la publicacion, el resultado es fallido y no contiene ruta o ID de paquete valido.

```python
# tramalia/core/redaccion.py
def redactar_texto_evidencia(
    valor: object,
    *,
    maximo_bytes: int = 131_072,
    maximo_linea: int = 8_192,
) -> str: ...
```

`redactar_texto_evidencia()` envuelve `sanear_texto_externo()` de 03a y agrega deteccion de bearer, claves privadas y campos sensibles estructurados. Para contenido truncado conserva bytes totales y SHA-256 completo calculado durante el drenaje del proceso, no una copia secreta sin truncar.

### Servicio de aplicacion

```python
# tramalia/core/servicio_recetas.py
@dataclass(frozen=True, slots=True)
class ResumenReceta:
    id_receta: str
    version: str
    titulo: str
    origen: ValorOrigenReceta
    hash_contenido: str

class ServicioRecetas:
    def __init__(
        self,
        raiz: Path,
        *,
        politica: PoliticaEjecucionRecetas,
        reloj_utc: Callable[[], datetime],
        generar_id: Callable[[], str],
        fuentes: Sequence[FuenteCatalogoRecetas] | None = None,
        registro: RegistroAccionesReceta | None = None,
        capturador_inventario: Callable[[], InventarioRecetas] | None = None,
    ) -> None: ...

    def listar(self) -> tuple[ResumenReceta, ...]: ...

    def explicar(self, id_receta: str, version: str | None = None) -> Receta: ...

    def planificar(self, solicitud: SolicitudReceta) -> PlanReceta: ...

    def simular(self, solicitud: SolicitudReceta) -> SimulacionReceta: ...

    def ejecutar(
        self,
        solicitud: SolicitudReceta,
        *,
        confirmar_huella: str,
        senal_cancelacion: SenalCancelacion | None = None,
        al_evento: Callable[[EventoOperacion], None] | None = None,
        al_cruzar_limite_mutacion: Callable[[EventoOperacion], None] | None = None,
    ) -> ResultadoEjecucionReceta: ...
```

`ejecutar()` no recibe ni confia en un `PlanReceta` reconstruido por una superficie. Adquiere `adquirir_bloqueo_operacion()`, vuelve a cargar catalogo, registro, inventario, Git e insumos desde `SolicitudReceta`, calcula el plan vigente y exige `confirmar_huella == plan_vigente.huella` antes de ejecutar o publicar. La confirmacion ausente, mal formada u obsoleta no crea directorios, eventos persistentes ni evidencia. Activar una habilidad solo puede cambiar el inventario de una planificacion posterior; nunca llama este servicio.

### CLI y JSON

El catalogo final de 03b registra:

- `tramalia recetas listar`;
- `tramalia recetas explicar <id[@version]>`;
- `tramalia recetas planificar <id[@version]> [--tarea <id>]`;
- `tramalia recetas simular <id[@version]> [--tarea <id>]`;
- `tramalia recetas ejecutar <id[@version]> [--tarea <id>] --confirmar-huella <sha256>`.

`<id>` siempre identifica una receta, no un plan persistido. Cada invocacion planifica desde fuentes vigentes. `--tarea` usa la tarea gobernada actual solo si existe una seleccion inequivoca; en otro caso es obligatorio para ejecutar. No hay alias que interprete ausencia de ID como lote.

Cada subcomando es `DefinicionSubcomando` de `tramalia/cli/catalogo_comandos.py`, con manejador y serializador por ID. La salida estructurada conserva el sobre 03b:

```json
{"version_esquema":1,"ok":true,"comando":"recetas","datos":{"operacion":"planificar"},"advertencias":[]}
```

Los serializadores de `ResumenReceta`, `Receta`, `PlanReceta`, `SimulacionReceta`, `ResultadoEjecucionReceta` y errores son explicitos. No usan `asdict()`, `repr()`, `default=str` ni diccionarios libres. JSON contiene un unico documento UTF-8, `allow_nan=False`, sin ANSI/OSC/markup; stderr queda reservado a diagnosticos tecnicos.

## Plan de implementacion

### Task 0: Verificar la base estable y congelar contratos de entrada

**Files:**

- Verify: `docs/superpowers/plans/2026-07-14-03a-seguridad-calidad-superficies.md`
- Verify: `tests/contratos/test_entrega_03c.py`
- Verify: `tests/contratos/test_importaciones_habilidades_03b.py`
- Verify: `tests/contratos/test_catalogo_cli.py`
- Verify: `tests/contratos/test_salida_estructurada_cli.py`
- Verify: `tests/contratos/test_paridad_operaciones_terminal.py`
- Verify: `tests/integracion/test_procesos.py`
- Verify: `tests/publicacion/test_licencia.py`
- Verify: `tests/publicacion/test_lanzamiento.py`
- Verify: `scripts/verificar_lanzamiento.py`
- Create: `tests/contratos/test_prerrequisitos_05a.py`
- Modify after the gate: `pyproject.toml`, `tramalia/__init__.py`, `uv.lock`, `CHANGELOG.md`

**Interfaces:** Ninguna interfaz nueva. Esta Task solo caracteriza las firmas finales y bloquea la implementacion sobre contratos provisionales.

- [ ] **Step 1: Escribir el contrato de prerrequisitos**

`test_prerrequisitos_05a.py` importa e inspecciona las firmas finales de confinamiento, procesos, cancelacion, eventos, catalogo CLI, salida JSON, servicio de habilidades, publicador de evidencia e inventario API. Exige una version no anterior a `1.0.0b1` y la licencia aplicada. No consulta red, no depende del estado dirty/clean ni prohíbe los modulos 05a despues de crearlos; el tag/release exacto se verifica fuera de pytest en Step 3.

- [ ] **Step 2: Ejecutar las puertas locales heredadas**

Run:

```powershell
uv sync --python 3.11 --locked --group desarrollo --group seguridad --all-extras
uv run --no-sync pytest tests/contratos/test_prerrequisitos_05a.py tests/contratos/test_entrega_03c.py tests/contratos/test_importaciones_habilidades_03b.py tests/contratos/test_catalogo_cli.py tests/contratos/test_salida_estructurada_cli.py tests/contratos/test_paridad_operaciones_terminal.py tests/integracion/test_procesos.py tests/publicacion/test_licencia.py tests/publicacion/test_lanzamiento.py -q
uv run --no-sync mkdocs build --strict
```

Expected: todo PASS.

- [ ] **Step 3: Verificar la BETA publicada sin alterar el candidato**

Run:

```powershell
$release_beta = gh release view v1.0.0b1 --repo MscottB/tramalia --json isDraft,isPrerelease,tagName,targetCommitish,assets,url | ConvertFrom-Json
if ($release_beta.isDraft) { throw "La release sigue en borrador." }
if (-not $release_beta.isPrerelease) { throw "La release no esta marcada como prerelease." }
if ($release_beta.tagName -ne "v1.0.0b1") { throw "La release apunta a otro tag." }
$nombres_activos = @($release_beta.assets | ForEach-Object name)
if ("SHA256SUMS" -notin $nombres_activos) { throw "Falta SHA256SUMS." }
if (-not ($nombres_activos | Where-Object { $_ -like "*.whl" })) { throw "Falta wheel." }
if (-not ($nombres_activos | Where-Object { $_ -like "*.tar.gz" })) { throw "Falta sdist." }
if (-not ($nombres_activos | Where-Object { $_ -like "*.zip" }) -or -not ($nombres_activos | Where-Object { $_ -like "*.zip.sha256" })) { throw "Falta documentacion sin conexion o su hash." }
$sha_beta = git rev-list -n 1 "v1.0.0b1^{commit}"
$sha_remoto = (git ls-remote origin "refs/tags/v1.0.0b1^{}" | ForEach-Object { ($_ -split "\s+")[0] })
if ($sha_beta -ne $sha_remoto) { throw "El tag remoto no coincide con el commit local." }
$descarga = Join-Path $env:TEMP ("tramalia-v1.0.0b1-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $descarga | Out-Null
gh release download v1.0.0b1 --repo MscottB/tramalia --dir $descarga
uv run --no-sync python scripts/verificar_lanzamiento.py verificar --distribuciones $descarga --manifiesto (Join-Path $descarga "SHA256SUMS")
$zip_sin_conexion = Get-ChildItem -LiteralPath $descarga -File -Filter "*.zip" | Select-Object -First 1
if (-not $zip_sin_conexion) { throw "Falta la documentacion sin conexion." }
$archivo_sha_zip = "$($zip_sin_conexion.FullName).sha256"
$sha_zip_esperado = ((Get-Content -LiteralPath $archivo_sha_zip -Raw).Trim() -split "\s+")[0].ToLowerInvariant()
$sha_zip_observado = (Get-FileHash -LiteralPath $zip_sin_conexion.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
if ($sha_zip_esperado -ne $sha_zip_observado) { throw "Hash invalido para documentacion sin conexion." }
Get-ChildItem -LiteralPath $descarga -File | Where-Object { $_.Name -like "*.whl" -or $_.Name -like "*.tar.gz" -or $_.Name -like "*.zip" } | ForEach-Object { gh attestation verify $_.FullName --repo MscottB/tramalia --source-ref refs/tags/v1.0.0b1 }
```

Expected: release publicada, no draft, marcada prerelease, con wheel, sdist, `SHA256SUMS`, documentacion sin conexion, hashes y atestaciones validas; tag local/remoto y activos corresponden al mismo SHA. Si falta publicacion o hay bloqueo abierto, detener 05a y volver al Plan 04.

- [ ] **Step 4: Registrar la caracterizacion, ejecutar y confirmar**

Run:

```powershell
uv run --no-sync pytest tests/contratos/test_prerrequisitos_05a.py -q
git diff --check
```

Expected: PASS y sin whitespace invalido.

- [ ] **Step 5: Commit**

```bash
git add tests/contratos/test_prerrequisitos_05a.py
git commit -m "test: bloquear prerrequisitos del motor de recetas"
git status --short -- tests/contratos/test_prerrequisitos_05a.py
```

Expected: commit creado y ninguna salida para ese archivo. Si habia cambios previos ajenos, mantenerlos fuera del stage y comprobar el alcance con `git diff --cached --name-only`; no exigir limpiar trabajo del usuario.

- [ ] **Step 6: Abrir la linea de desarrollo de la siguiente BETA**

Actualizar de forma atomica `project.version`, `tramalia.__version__`, `uv.lock` y el encabezado de changelog a `1.0.0b2.dev0`. Esta version permanece de desarrollo durante 05a-05d; solo 05d puede preparar `v1.0.0b2` despues de la puerta global. El contrato de prerrequisitos acepta esta version porque es posterior a la base publicada.

Run:

```powershell
uv lock --python 3.11
uv lock --check --python 3.11
uv run --no-sync pytest tests/contratos/test_prerrequisitos_05a.py tests/publicacion/test_lanzamiento.py -q
```

Expected: PASS con una unica version `1.0.0b2.dev0` en codigo, metadata y lock.

```bash
git add pyproject.toml tramalia/__init__.py uv.lock CHANGELOG.md
git commit -m "chore: abrir desarrollo 1.0.0b2"
```

### Task 1: Compartir serializacion canonica y huellas de insumos

**Files:**

- Create: `tramalia/core/serializacion.py`
- Create: `tramalia/core/insumos.py`
- Create: `tramalia/core/redaccion.py`
- Modify: `tramalia/core/errores.py`
- Modify: `tramalia/core/operaciones.py`
- Modify: `tramalia/core/evidencia.py`
- Modify: `tramalia/mcp_server.py`
- Create: `tests/unidad/test_serializacion.py`
- Create: `tests/unidad/test_insumos.py`
- Create: `tests/unidad/test_redaccion.py`
- Modify: `tests/unidad/test_errores_modelos.py`
- Modify: `tests/integracion/test_operaciones.py`
- Modify: `tests/integracion/test_evidencia_atomica.py`
- Modify: `tests/contratos/test_metadatos_evidencia_v1.py`
- Modify: `tests/integracion/test_mcp_operaciones.py`

**Interfaces:** Produce `ValorJSON`, `ErrorSerializacionSegura`, `proyectar_json_publico()`, `normalizar_detalle_error_compatible()`, `serializar_json_formal()`, `serializar_json_canonico()`, `calcular_huella_json()`, `HuellaInsumo`, `capturar_huella_insumo()` y `redactar_texto_evidencia()`. Consume las funciones de confinamiento/saneamiento de 03a.

- [ ] **Step 1: Escribir RED de JSON canonico y tipos inseguros**

En `test_serializacion.py`, demostrar:

- permutar claves o pares de entrada conserva bytes canonicos y huella;
- lista y tupla se normalizan solo mediante adaptadores explicitos; pasos/eventos no se reordenan;
- NaN, infinito, `datetime`, dataclass no registrada y objetos arbitrarios fallan con `ErrorSerializacionSegura`;
- un `Path` sin `raiz` falla; con `raiz`, una ruta interna se proyecta relativa y una externa falla;
- formal usa salto final; canonico no usa indentacion ni espacios;
- dos textos distintos, incluso si parecen secretos, producen hashes canonicos distintos: la ruta de huella no redacta;
- `proyectar_json_publico()` y `redactar_texto_evidencia()` eliminan bearer, token, password, clave privada, ANSI, OSC, NUL y controles antes de una superficie;
- `normalizar_detalle_error_compatible()` conserva exactamente campos, codigos y marcadores historicos de `Path`, fechas, NaN y objetos admitidos por errores v1.

- [ ] **Step 2: Escribir RED de insumos gobernados**

En `test_insumos.py`, cubrir archivo presente, ausente, reemplazado entre resolucion/lectura, exceso de 4 MiB, traversal, symlink, junction/reparse point, dispositivo Windows, nombre no portable y colision case-insensitive. Probar que contenido igual bajo dos clones produce igual `HuellaInsumo` y que crear, cambiar o eliminar cambia su estado/huella.

- [ ] **Step 3: Ejecutar RED**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_serializacion.py tests/unidad/test_insumos.py tests/unidad/test_redaccion.py -q
```

Expected: FAIL por modulos ausentes.

- [ ] **Step 4: Extraer, no duplicar, las primitivas existentes**

Extraer por separado la proyeccion publica estricta y la compatibilidad de detalles ya usada por errores/operaciones/MCP; `serializacion.py` no importa `errores.py`. Crear `redaccion.py` sobre `sanear_texto_externo()` para que ejecutores posteriores puedan sanear antes del callback. Mover la captura/hash privado de insumos de cierre a `insumos.py`. `capturar_huella_insumo()` usa `resolver_ruta_confinada()` y lectura verificada de 03a; no llama `Path.resolve()` como unica defensa ni sigue enlaces. Documentar en comentario espanol por que ausencia participa como estado, con SHA `None`, en la huella agregada.

- [ ] **Step 5: Ejecutar GREEN y caracterizacion**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_serializacion.py tests/unidad/test_insumos.py tests/unidad/test_redaccion.py tests/unidad/test_errores_modelos.py tests/integracion/test_operaciones.py tests/integracion/test_evidencia_atomica.py tests/integracion/test_mcp_operaciones.py tests/contratos/test_metadatos_evidencia_v1.py -q
uv run --no-sync mypy tramalia/core/serializacion.py tramalia/core/insumos.py tramalia/core/redaccion.py
```

Expected: PASS; cierres y paquetes v1 conservan comportamiento.

- [ ] **Step 6: Refactor y commit**

Eliminar implementaciones privadas duplicadas solo despues de que las pruebas de caracterizacion pasen. Ejecutar `rg -n "json.dumps|sha256" tramalia/core` y justificar cada uso restante; no reemplazar hashing de archivos en streaming por lectura completa.

```bash
git add tramalia/core/serializacion.py tramalia/core/insumos.py tramalia/core/redaccion.py tramalia/core/errores.py tramalia/core/operaciones.py tramalia/core/evidencia.py tramalia/mcp_server.py tests/unidad/test_serializacion.py tests/unidad/test_insumos.py tests/unidad/test_redaccion.py tests/unidad/test_errores_modelos.py tests/integracion/test_operaciones.py tests/integracion/test_evidencia_atomica.py tests/integracion/test_mcp_operaciones.py tests/contratos/test_metadatos_evidencia_v1.py
git commit -m "refactor: compartir huellas de insumos gobernados"
```

### Task 2: Extraer el bloqueo interproceso raiz-global

**Files:**

- Create: `tramalia/core/bloqueo_operaciones.py`
- Modify: `tramalia/core/materializacion_habilidades.py`
- Modify: `tramalia/core/errores.py`
- Create: `tests/unidad/test_bloqueo_operaciones.py`
- Create: `tests/integracion/test_bloqueo_operaciones.py`
- Modify: `tests/integracion/test_materializacion_habilidades.py`

**Interfaces:** Produce `BloqueoOperacion`, `adquirir_bloqueo_operacion()` y `ErrorOperacionEnCurso(codigo="operacion_en_curso")`. Habilidades pasa a consumir la misma primitiva; no conserva un lock paralelo.

- [ ] **Step 1: Escribir RED multiplataforma del lock**

Cubrir adquisicion/liberacion, nombre portable, raiz gobernada, timeout finito, segunda adquisicion desde otro proceso, dos hilos, excepcion dentro del contexto, proceso que termina abruptamente y reintento posterior. Rechazar traversal, symlink/junction hacia el archivo de lock, raiz reemplazada, PID/metadata hostil y timeout negativo/NaN. Un lock activo de habilidades bloquea una mutacion de receta y viceversa porque ambos usan el mismo nombre global `mutacion-proyecto`.

- [ ] **Step 2: Ejecutar RED**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_bloqueo_operaciones.py tests/integracion/test_bloqueo_operaciones.py -q
```

Expected: FAIL por primitiva ausente.

- [ ] **Step 3: Extraer el lock ya probado en 03c**

Extraer la implementacion final de `materializacion_habilidades.py` a `bloqueo_operaciones.py`, mantener su estrategia Windows/Linux/macOS y reusar las rutas confinadas de 03a. El archivo de lock no se interpreta como autorizacion y sus metadatos son solo diagnosticos saneados. El bloqueo es de exclusion mutua, no journal transaccional; la recuperacion de cada dominio permanece en su publicador.

- [ ] **Step 4: Migrar habilidades y ejecutar GREEN**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_bloqueo_operaciones.py tests/integracion/test_bloqueo_operaciones.py tests/integracion/test_materializacion_habilidades.py tests/contratos/test_entrega_03c.py -q
```

Expected: PASS; el contrato publico de habilidades no cambia.

- [ ] **Step 5: Commit**

```bash
git add tramalia/core/bloqueo_operaciones.py tramalia/core/materializacion_habilidades.py tramalia/core/errores.py tests/unidad/test_bloqueo_operaciones.py tests/integracion/test_bloqueo_operaciones.py tests/integracion/test_materializacion_habilidades.py
git commit -m "refactor: compartir bloqueo de operaciones mutantes"
```

### Task 3: Definir modelos y errores tipados de recetas

**Files:**

- Create: `tramalia/core/modelos_recetas.py`
- Modify: `tramalia/core/errores.py`
- Create: `tests/unidad/test_modelos_recetas.py`
- Create: `tests/unidad/test_errores_recetas.py`

**Interfaces:** Implementa exactamente los enums/dataclasses de “Modelos de recetas” y los errores `ErrorCatalogoRecetas`, `ErrorRecetaNoEncontrada`, `ErrorResolucionReceta`, `ErrorPlanRecetaBloqueado`, `ErrorHuellaRecetaObsoleta` y `ErrorEjecucionReceta`.

- [ ] **Step 1: Escribir RED de invariantes**

Probar:

- IDs ASCII-portables, versiones no vacias y SHA-256 minusculo de 64 caracteres;
- `concurrencia_maxima` solo 1-4 y limites finitos/positivos dentro de maximos documentados;
- argumentos, capacidades, dependencias, insumos y efectos sin duplicados y en orden canonico;
- precondiciones solo de enum cerrado, puertas/evidencias con referencias validas y categorias de datos sensibles declaradas;
- dataclasses `frozen=True, slots=True` y sin `Mapping` mutable almacenado;
- tiempos UTC, fin no anterior a inicio y duracion coherente;
- un paso completado exige resultado exitoso; timeout/cancelacion/no-cero no puede ser completado;
- `EJECUTADA` exige todos los pasos ejecutables completados y ningun paquete; es el estado interno entre ejecutor y publicador;
- `COMPLETADA` exige los mismos pasos y un paquete v2 ya publicado y revalidado;
- todo resultado lleva codigo estable; estados fallido, cancelado y bloqueado conservan motivo no vacio, y un fallo de publicacion queda `FALLIDA` sin paquete pero con resultados/advertencias;
- transiciones aprobadas encadenan `huella_despues` con la siguiente `huella_antes`; una rechazada exige motivo y efectos observados saneados y debe ser la ultima;
- `como_dict()` de cada error incluye codigo estable, mensaje y sugerencia, sin secretos ni rutas absolutas.

- [ ] **Step 2: Ejecutar RED**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_modelos_recetas.py tests/unidad/test_errores_recetas.py -q
```

Expected: FAIL por modelos ausentes.

- [ ] **Step 3: Implementar modelos sin logica de IO**

Usar auxiliares privados pequenos para validar identificadores, tuplas ordenadas, limites y coherencia. `PlanReceta.ejecutable` es `not bloqueos`. Mantener modelos libres de filesystem, red, proceso, Rich y Textual. Docstrings publicos en ingles Google style; comentarios de invariantes en espanol.

- [ ] **Step 4: Implementar errores y GREEN**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_modelos_recetas.py tests/unidad/test_errores_recetas.py tests/unidad/test_errores_modelos.py -q
uv run --no-sync ruff check tramalia/core/modelos_recetas.py tests/unidad/test_modelos_recetas.py tests/unidad/test_errores_recetas.py
uv run --no-sync mypy tramalia/core/modelos_recetas.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tramalia/core/modelos_recetas.py tramalia/core/errores.py tests/unidad/test_modelos_recetas.py tests/unidad/test_errores_recetas.py
git commit -m "feat: definir dominio tipado de recetas"
```

### Task 4: Implementar esquema TOML v1 y catalogo estricto

**Files:**

- Create: `tramalia/core/esquema_recetas.py`
- Create: `tramalia/core/catalogo_recetas.py`
- Create: `tests/unidad/test_esquema_recetas.py`
- Create: `tests/unidad/test_catalogo_recetas.py`
- Create: `tests/integracion/test_catalogo_recetas.py`
- Create: `tests/recursos/recetas/valida/receta.toml`
- Create: `tests/recursos/recetas/hostiles/clave-desconocida.toml`
- Create: `tests/recursos/recetas/hostiles/shell-libre.toml`
- Create: `tests/recursos/recetas/hostiles/traversal.toml`
- Create: `tests/recursos/recetas/hostiles/limites-excedidos.toml`
- Create: `tests/recursos/recetas/hostiles/ciclo.toml`

**Interfaces:** Produce `analizar_receta_toml()`, `serializar_receta_toml()`, `FuenteCatalogoRecetas`, `ReferenciaReceta`, `separar_referencia_receta()`, `CatalogoRecetas`, `cargar_catalogo_recetas()` y `obtener_receta()`.

- [ ] **Step 1: Escribir RED del esquema cerrado**

La receta valida cubre metadatos, permisos/datos/red, politica de fallo, concurrencia, precondiciones cerradas, DAG, argumentos, insumos, efectos, puertas, evidencia declarada y limites. El test construye en memoria bytes UTF-8 invalidos, BOM y >1 MiB para no versionar basura/binarios enormes; los fixtures TOML enumerados cubren esquema distinto de 1, clave desconocida, shell, limites estructurales, ID/version duplicados, precondicion desconocida, puerta sin paso/estado, evidencia sin fuente/paso, dependencia inexistente, ciclo, rutas absolutas, `..`, barras Windows ambiguas, globs y nombres reservados.

Rechazar explicitamente campos `comando`, `shell`, `python`, `codigo`, `script`, `callable`, `entorno` y cualquier intento de interpolacion de proceso. Los argumentos son texto o listas de texto; se normalizan a `ValorArgumentoReceta` y se validan por la accion registrada en una Task posterior.

- [ ] **Step 2: Escribir RED del catalogo y procedencia**

Cubrir catalogo propio, catalogo de proyecto, orden de directorios permutado, mismo `(id, version)` repetido aun con bytes iguales, dos versiones, omision ambigua de version, `separar_referencia_receta()` con `id@version`, symlink, junction, archivo reemplazado, traversal, colision Unicode NFC/NFD y case-insensitive. Un catalogo invalido falla completo; nunca se convierte en lista vacia ni omite silenciosamente una receta.

- [ ] **Step 3: Ejecutar RED**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_esquema_recetas.py tests/unidad/test_catalogo_recetas.py tests/integracion/test_catalogo_recetas.py -q
```

Expected: FAIL por parser y catalogo ausentes.

- [ ] **Step 4: Implementar parser y round-trip canonico**

Implementar las firmas congeladas `analizar_receta_toml(contenido, origen, referencia)` y `serializar_receta_toml(receta)`. Usar `tomllib.loads()` sobre texto UTF-8 verificado y validar claves antes de construir modelos. El serializador propio solo emite el esquema admitido; parsear esos bytes conserva todos los campos semanticos y recalcula `sha256_fuente` para la forma canonica. Una fuente no canonica puede cambiar ese SHA en round-trip, pero conserva `hash_contenido`. `hash_contenido` se calcula sobre la proyeccion canonica sin incluir ninguno de los dos hashes recursivamente.

- [ ] **Step 5: Implementar descubrimiento confinado y GREEN**

La carga recibe fuentes explicitas, deriva las dos fuentes estandar en el servicio y usa las funciones de 03a. Ordena por origen, ID y version; registra `referencia_origen` relativa. No usa `rglob()` sobre arbol no validado ni sigue enlaces.

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_esquema_recetas.py tests/unidad/test_catalogo_recetas.py tests/integracion/test_catalogo_recetas.py -q
uv run --no-sync ruff check tramalia/core/esquema_recetas.py tramalia/core/catalogo_recetas.py tests/unidad/test_esquema_recetas.py tests/unidad/test_catalogo_recetas.py tests/integracion/test_catalogo_recetas.py
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tramalia/core/esquema_recetas.py tramalia/core/catalogo_recetas.py tests/unidad/test_esquema_recetas.py tests/unidad/test_catalogo_recetas.py tests/integracion/test_catalogo_recetas.py tests/recursos/recetas/valida/receta.toml tests/recursos/recetas/hostiles/clave-desconocida.toml tests/recursos/recetas/hostiles/shell-libre.toml tests/recursos/recetas/hostiles/traversal.toml tests/recursos/recetas/hostiles/limites-excedidos.toml tests/recursos/recetas/hostiles/ciclo.toml
git commit -m "feat: cargar catalogo estricto de recetas"
```

### Task 5: Registrar acciones confiables y capturar inventario inmutable

**Files:**

- Create: `tramalia/core/acciones_recetas.py`
- Create: `tramalia/core/perfiles_procesos_recetas.py`
- Create: `tramalia/core/acciones_recetas_propias.py`
- Create: `tramalia/core/inventario_recetas.py`
- Create: `tests/unidad/test_acciones_recetas.py`
- Create: `tests/unidad/test_perfiles_procesos_recetas.py`
- Create: `tests/unidad/test_inventario_recetas.py`
- Create: `tests/integracion/test_inventario_recetas.py`
- Create: `tests/contratos/test_aislamiento_recetas_habilidades.py`

**Interfaces:** Produce `DefinicionAccionReceta`, `DescripcionPasoAccionReceta`, `ContextoAccionReceta`, `ResultadoAccionReceta`, `ProtocoloAccionReceta`, `RegistroAccionesReceta`, `PerfilProcesoReceta`, `RegistroPerfilesProcesoReceta`, `crear_registro_acciones_propias()` y `capturar_inventario_recetas()`.

- [ ] **Step 1: Escribir RED del registro cerrado**

Probar registro vacio, alta y consulta; rechazar ID/version/modo invalido, ID duplicado, definicion mutable, descripcion/capacidades vacias, accion desconocida y objeto que no cumple el protocolo. Cargar TOML nunca registra callables. `describir_paso()` valida argumentos sin ejecutar. Registrar una accion no puede escribir, abrir red ni sondear herramientas; obtiene ID/version/modo desde `definicion` y no inventa argumentos para describir un paso. `INTERNA_ACOTADA` solo admite acciones propias, sin E/S bloqueante, y sus fixtures demuestran checkpoints de cancelacion/plazo; `PROCESO_GOBERNADO` exige perfil registrado y timeout duro delegado al runner.

La accion `tramalia.proceso.ejecutar` acepta `perfil` mas opciones declaradas en ese perfil. Rechaza perfil desconocido, ID/version/hash de perfil invalido, opcion no allowlisted, cadena de comando, shell, metacaracteres tratados como sintaxis, ejecutable absoluto, entorno arbitrario y directorio externo. Cambiar argumentos fijos, opciones, mutabilidad, permisos, datos o red cambia `hash_definicion`. Probar expresamente `node -e`, `python -c`, `git push`, `uv run`, `--config` externo y flags de red. Las listas estructuradas nunca pasan por `shlex.split()`.

- [ ] **Step 2: Escribir RED del inventario**

Cubrir herramienta presente, ausente e indeterminada; version, identidad logica y SHA-256 del ejecutable saneados; capacidades `nucleo:*`, `herramienta:*` y `habilidad:*` con procedencia separada; permutaciones estables; cambio de identidad/hash/version/estado/capacidad cambia la huella. El sondeador se inyecta y el test demuestra que capturar no escribe ni abre red. Una habilidad activa aporta capacidades a un snapshot posterior, pero activar/desactivar mediante `ServicioHabilidades` nunca llama `ServicioRecetas.ejecutar()`.

- [ ] **Step 3: Ejecutar RED**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_acciones_recetas.py tests/unidad/test_perfiles_procesos_recetas.py tests/unidad/test_inventario_recetas.py tests/integracion/test_inventario_recetas.py tests/contratos/test_aislamiento_recetas_habilidades.py -q
```

Expected: FAIL por registro e inventario ausentes.

- [ ] **Step 4: Implementar registro, adaptadores y acciones propias**

Construir registros de acciones y perfiles desde codigo propio en orden explicito. La accion de proceso resuelve el perfil, valida cada opcion, construye argv sin interpolacion, compara de nuevo ID/version/hash canonico del perfil e identidad/version/SHA del ejecutable inmediatamente antes del lanzamiento y delega a `procesos.ejecutar()`; la accion de inventario es `INTERNA_ACOTADA`, comprueba cancelacion/plazo y devuelve un resultado tipado. El inventario congelado se incorpora desde `PlanReceta` al paquete, sin escribir directamente. Las versiones de accion/perfil y el hash de toda definicion de perfil son constantes semanticas del plan y forman parte de la huella.

- [ ] **Step 5: Implementar snapshot y GREEN**

Adaptar `Herramienta`/`EstadoHerramienta` de integraciones y consultas de solo lectura de `ServicioHabilidades`; no replicar su politica. Normalizar la ubicacion observada a identidad logica portable y SHA-256 para el snapshot; una ruta absoluta necesaria para invocar queda solo en un contexto efimero privado y nunca entra al plan, huella, evento o evidencia. Diferenciar ausencia de error de sondeo.

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_acciones_recetas.py tests/unidad/test_perfiles_procesos_recetas.py tests/unidad/test_inventario_recetas.py tests/integracion/test_inventario_recetas.py tests/contratos/test_aislamiento_recetas_habilidades.py -q
uv run --no-sync mypy tramalia/core/acciones_recetas.py tramalia/core/perfiles_procesos_recetas.py tramalia/core/acciones_recetas_propias.py tramalia/core/inventario_recetas.py
```

Expected: PASS y ninguna llamada de red/escritura en captura.

- [ ] **Step 6: Commit**

```bash
git add tramalia/core/acciones_recetas.py tramalia/core/perfiles_procesos_recetas.py tramalia/core/acciones_recetas_propias.py tramalia/core/inventario_recetas.py tests/unidad/test_acciones_recetas.py tests/unidad/test_perfiles_procesos_recetas.py tests/unidad/test_inventario_recetas.py tests/integracion/test_inventario_recetas.py tests/contratos/test_aislamiento_recetas_habilidades.py
git commit -m "feat: registrar acciones e inventario de recetas"
```

### Task 6: Resolver el DAG y construir un plan reproducible

**Files:**

- Create: `tramalia/core/resolucion_recetas.py`
- Create: `tramalia/core/planificacion_recetas.py`
- Create: `tests/unidad/test_resolucion_recetas.py`
- Create: `tests/unidad/test_planificacion_recetas.py`
- Create: `tests/integracion/test_planificacion_recetas.py`

**Interfaces:** Produce `ResolucionReceta`, `resolver_receta()`, `ContextoPlanificacionReceta`, `capturar_contexto_planificacion_receta()`, `planificar_receta()` y `crear_estado_esperado_ejecucion_receta()`.

- [ ] **Step 1: Escribir RED de resolucion fail-closed**

Cubrir DAG valido, orden de entrada permutado, ciclo directo/indirecto, dependencia ausente, accion desconocida, argumentos invalidos para la accion, precondicion incumplida, herramienta ausente/indeterminada, capacidad ausente, permiso/dato sensible no admitido, politica de red incompatible, puerta/evidencia que referencia paso inexistente, efecto fuera de raiz y ruta de efecto que atraviesa symlink/junction. Si un efecto de un paso coincide con insumo o efecto de otro, el segundo debe depender transitivamente del primero; bloquear conflictos escritura-lectura/escritura-escritura no ordenados. Un plan bloqueado enumera todos los bloqueos deterministas sin intentar ejecutar.

Una accion `PERMITIDA` queda bloqueada si la receta/politica solicitada es `SIN_RED`; `SOLO_LOCAL` no habilita Internet. El mensaje documenta que la politica no es sandbox de SO. Ningun bloqueo se convierte en advertencia para permitir ejecucion.

- [ ] **Step 2: Escribir RED de huella y drift**

Probar que receta, version/modo de accion, ID/version/hash de perfil de proceso, presencia/version de herramienta, capacidades, identidad Git, rutas Git modificadas, contenido/ausencia de insumo, contenido/ausencia inicial de cada efecto, permisos, efectos, limites y politica cambian la huella. Probar que orden de entrada, ruta absoluta del clon, `mtime`, PID, reloj, UUID y orden de directorio no la cambian. `id_plan` no existe como estado persistido: `huella` identifica el plan logico.

Crear parametrizaciones para crear/cambiar/eliminar/reemplazar cada insumo. Repetir la misma planificacion 20 veces y exigir bytes canonicos/huella iguales.

Construir el estado esperado inicial dos veces desde el mismo plan y exigir igualdad byte a byte. Debe incluir la union de insumos/efectos y separar la huella de componentes inmutables; nunca incorpora reloj, ID de operacion ni ruta fisica.

- [ ] **Step 3: Ejecutar RED**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_resolucion_recetas.py tests/unidad/test_planificacion_recetas.py tests/integracion/test_planificacion_recetas.py -q
```

Expected: FAIL por resolvedor y planificador ausentes.

- [ ] **Step 4: Implementar resolucion y orden topologico estable**

Primero capturar `ContextoPlanificacionReceta` con una sola lectura confinada de la union de insumos y efectos; luego describir cada accion una sola vez con argumentos canonicos, evaluar solo los cuatro tipos cerrados de precondicion contra ese snapshot, resolver capacidades/datos/permisos/red contra politica, validar puertas/evidencias/rutas exactas y dependencias de recursos, y construir `PasoResueltoReceta` con rutas, no hashes. Usar Kahn con cola lexicografica por `id_paso`. `resolver_receta()` no vuelve a leer filesystem ni ejecuta acciones, sondas, Git remoto o procesos.

- [ ] **Step 5: Implementar contexto y huella**

Capturar identidad Git mediante la API final existente, huellas de todas las rutas declaradas por receta/precondiciones mediante `insumos.py` e inventario inyectado. `planificar_receta()` combina `PasoResueltoReceta` con esas huellas para crear `PasoPlanReceta`; la propiedad global deriva su union y valida que no falte ninguna ruta. Proyectar cada modelo a `ValorJSON` con funciones explicitas y calcular SHA-256 canonico. Revalidar identidad fisica de la raiz antes/despues de capturar. Planificar no crea `.tramalia`, temporales, caches ni evidencia.

- [ ] **Step 6: Ejecutar GREEN y prueba de repeticion**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_resolucion_recetas.py tests/unidad/test_planificacion_recetas.py tests/integracion/test_planificacion_recetas.py -q
uv run --no-sync pytest tests/unidad/test_planificacion_recetas.py --count=20 -q
uv run --no-sync mypy tramalia/core/resolucion_recetas.py tramalia/core/planificacion_recetas.py
```

Expected: PASS y cero archivos creados por planificar.

- [ ] **Step 7: Commit**

```bash
git add tramalia/core/resolucion_recetas.py tramalia/core/planificacion_recetas.py tests/unidad/test_resolucion_recetas.py tests/unidad/test_planificacion_recetas.py tests/integracion/test_planificacion_recetas.py
git commit -m "feat: planificar recetas con huella reproducible"
```

### Task 7: Proyectar una simulacion pura y explicable

**Files:**

- Create: `tramalia/core/simulacion_recetas.py`
- Create: `tests/unidad/test_simulacion_recetas.py`

**Interfaces:** Produce `simular_receta(plan: PlanReceta) -> SimulacionReceta`.

- [ ] **Step 1: Escribir RED de alcance y coste tecnico**

Probar que la simulacion expone receta/version/huella, pasos ordenados, bloqueos, herramientas, permisos, categorias de datos sensibles, politicas de red, rutas mutadas, tiempo maximo conservador, suma acotada de salida, concurrencia maxima y si cruza frontera mutable. `tokens_estimados == 0` y no existe campo de precio.

Para ramas paralelas, `duracion_maxima_segundos` suma los limites de todos los pasos como cota superior segura aun con un solo worker; no usa la ruta critica, que seria una cota inferior con concurrencia acotada. `maximo_salida_bytes` suma dos canales por cada tope de paso. Plan bloqueado conserva detalles y `mutante` segun alcance, sin fingir ejecutabilidad.

- [ ] **Step 2: Escribir RED de pureza observable**

Parchear/instrumentar filesystem, red, proceso, registro de acciones y reloj: `simular_receta()` solo lee el modelo recibido. La pureza de la fachada completa se prueba en Task 12, cuando existe `ServicioRecetas`.

- [ ] **Step 3: Ejecutar RED**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_simulacion_recetas.py -q
```

Expected: FAIL por simulador ausente.

- [ ] **Step 4: Implementar proyeccion desde el plan**

No volver a resolver ni consultar inventario. Deduplicar permisos/red con orden lexicografico. Sumar limites de todos los pasos y ambos canales con comprobacion de overflow; no usar ruta critica como maximo. Los mensajes explicativos se representan por codigos/datos; traduccion pertenece a superficies.

- [ ] **Step 5: Ejecutar GREEN y commit**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_simulacion_recetas.py -q
```

Expected: PASS.

```bash
git add tramalia/core/simulacion_recetas.py tests/unidad/test_simulacion_recetas.py
git commit -m "feat: simular alcance y coste de recetas"
```

### Task 8: Implementar el ejecutor secuencial observable

**Files:**

- Create: `tramalia/core/ejecucion_recetas.py`
- Create: `tests/unidad/test_ejecucion_recetas.py`
- Create: `tests/integracion/test_ejecucion_recetas.py`
- Create: `tests/recursos/recetas/acciones_prueba.py`

**Interfaces:** Produce la primera version de `ejecutar_plan_receta()` con `concurrencia_maxima=1`, eventos compartidos y resultados honestos.

- [ ] **Step 1: Escribir RED de orden y politica de fallo**

Acciones de prueba registradas desde codigo permiten completar, fallar y registrar orden sin acceder a red. Un perfil de proceso prueba timeout duro; una accion interna propia prueba el plazo cooperativo con reloj monotono inyectado y checkpoints, sin pretender matar un hilo Python arbitrario. Cubrir:

- orden topologico estable y una sola invocacion por paso;
- plan bloqueado no invoca ninguna accion;
- fallo bloquea todos los descendientes con motivo que referencia el ancestro;
- `CONTINUAR_RAMAS_INDEPENDIENTES` termina la rama no relacionada;
- `DETENER_TODO` bloquea todos los pasos aun no iniciados;
- puertas se evaluan desde estados de pasos sin ejecutar codigo; una puerta bloqueante rechazada vuelve la ejecucion `FALLIDA` y una no bloqueante queda como advertencia explicita;
- herramienta ausente, 127, 124, 130, timeout duro de proceso, plazo cooperativo interno, cancelacion y no-cero nunca son exito;
- un perfil de prueba que produce mas de 20 MiB por canal con limite 1 MiB drena el proceso, entrega como maximo 1 MiB por canal a callbacks/resultado y conserva `bytes_*_total`/SHA completos;
- excepcion inesperada se convierte en resultado fallido saneado y no traceback persistido;
- resultado y eventos comparten `id_operacion`;
- el ejecutor entrega el estado esperado vigente a cada revalidacion, llama el avance posterior una vez por accion terminada y conserva transiciones en orden;
- una mutacion declarada que cambia `salida.json`, seguida por un paso dependiente que la consume, completa con transicion aprobada y sin cambiar `plan.huella`; una ruta fuera de efectos devuelve estado nuevo `None`, transicion rechazada con motivo/efectos observados saneados, resultado fallido y ningun paso posterior.

- [ ] **Step 2: Escribir RED de eventos**

Exigir secuencia del ejecutor `INICIADA`, `PASO_INICIADO` y `PASO_TERMINADO`; campos acotados y saneados antes del callback. El servicio agrega `PUBLICANDO` y el evento terminal despues de intentar la evidencia. Igual que 03b, una excepcion de `al_evento` se captura, se sanea y se registra como advertencia sin abortar la operacion; ese observador no concede autoridad. `revalidar_antes_de_paso` falla cerrado antes de cualquier accion y `al_cruzar_limite_mutacion` falla cerrado antes de un efecto. Ningun callback puede cambiar el modelo congelado.

- [ ] **Step 3: Ejecutar RED**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_ejecucion_recetas.py tests/integracion/test_ejecucion_recetas.py -q
```

Expected: FAIL por ejecutor ausente.

- [ ] **Step 4: Implementar scheduler secuencial minimo**

Calcular pasos listos desde dependencias, mantener una unica referencia al `EstadoEsperadoEjecucionReceta`, invocar revalidacion antes y avance despues de cada accion, y llamar solo `RegistroAccionesReceta`. Construir `ContextoAccionReceta` con ese estado vigente para que un consumidor vea las huellas actualizadas, mientras `PasoPlanReceta` conserva el snapshot inicial confirmado. Medir con reloj monotono para duracion y `reloj_utc` para timestamps. Al terminar pasos, evaluar `PuertaReceta` sobre estados y construir `ResultadoPuertaReceta`; nunca interpretar expresiones o scripts. Los procesos reales pasan por `procesos.ejecutar()` final de 03b. No importar `subprocess`, Rich, Textual o CLI. Tratar fallos esperados como `ResultadoPasoReceta`, no como excepciones estructurales.

- [ ] **Step 5: Ejecutar GREEN y escaneo de ejecutores paralelos**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_ejecucion_recetas.py tests/integracion/test_ejecucion_recetas.py tests/integracion/test_procesos.py -q
rg -n "subprocess|Popen|os.system|shell=True" tramalia/core/ejecucion_recetas.py tramalia/core/acciones_recetas_propias.py
```

Expected: pruebas PASS y `rg` sin coincidencias de ejecucion alternativa.

- [ ] **Step 6: Commit**

```bash
git add tramalia/core/ejecucion_recetas.py tests/unidad/test_ejecucion_recetas.py tests/integracion/test_ejecucion_recetas.py tests/recursos/recetas/acciones_prueba.py
git commit -m "feat: ejecutar recetas de forma observable"
```

### Task 9: Acotar cancelacion, concurrencia y frontera mutable

**Files:**

- Modify: `tramalia/core/ejecucion_recetas.py`
- Modify: `tramalia/core/modelos_operacion.py` para agregar solo `MUTANDO`
- Create: `tests/unidad/test_concurrencia_recetas.py`
- Create: `tests/integracion/test_cancelacion_recetas.py`
- Create: `tests/integracion/test_frontera_mutable_recetas.py`

**Interfaces:** Completa `ejecutar_plan_receta()` con concurrencia 1-4, `SenalCancelacion`, `al_evento` y `al_cruzar_limite_mutacion`.

- [ ] **Step 1: Escribir RED de concurrencia acotada**

Usar barreras y contadores, no `sleep` como unica sincronizacion. Probar maximo 1, 2 y 4; nunca superar el limite; solo paralelizar ramas independientes de lectura; nunca solapar dos mutaciones ni una mutacion con una lectura activa; mantener resultados en orden topologico canonico aunque terminen en otro orden. Un fallo concurrente conserva las ramas ya terminadas y aplica la politica sin carreras.

- [ ] **Step 2: Escribir RED de cancelacion real**

Cancelar antes de iniciar, durante accion de lectura y durante proceso con hijo. Exigir que `procesos.ejecutar()` termine el arbol, no inicie descendientes, marque pendientes como bloqueados/cancelados de forma coherente y preserve resultados completos. La prueba multiplataforma usa el fixture de arbol de procesos de 03b.

- [ ] **Step 3: Escribir RED de frontera mutable**

Antes de cada paso, incluso de lectura y en ramas concurrentes, `revalidar_antes_de_paso` se invoca de forma serializada contra el estado esperado vigente y una excepcion impide llamar la accion. El avance posterior tambien se serializa: lecturas no pueden cambiarlo y solo una mutacion exclusiva puede producir una transicion. Para plan de solo lectura el callback de frontera no se invoca. Para plan mutante, tras drenar lecturas se repite la revalidacion y la frontera se invoca exactamente una vez junto al evento `MUTANDO`, sincronamente antes del primer efecto. Probar una cadena mutar→leer y mutar→mutar ordenada que avanza, y el mismo solapamiento sin dependencia que queda bloqueado al resolver. Si la barrera falla o solicita cancelacion, ninguna accion mutante inicia. Si una accion registrada como lectura devuelve `efectos_observados`, el resultado falla cerrado. Esto valida codigo confiable, no demuestra ausencia de escrituras externas: 05a no es un sandbox de filesystem y documenta el TOCTOU residual.

- [ ] **Step 4: Ejecutar RED**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_concurrencia_recetas.py tests/integracion/test_cancelacion_recetas.py tests/integracion/test_frontera_mutable_recetas.py -q
```

Expected: FAIL porque el ejecutor aun es secuencial y no implementa toda la frontera.

- [ ] **Step 5: Implementar scheduler acotado**

Usar un pool con maximo 4 workers y una cola determinista de pasos listos. Antes de despachar, separar lectura/mutacion y respetar dependencia/fallo/cancelacion. Los callbacks reciben el orden observado; la proyeccion persistente usa un ordinal estable derivado de orden topologico y fase del evento, con la secuencia observada solo como dato volatil excluido de `huella_contenido`. No usar timestamps para ordenar evidencia. `CoordinadorOperaciones` no se importa en el nucleo: la futura TUI conecta eventos/permiso desde fuera.

- [ ] **Step 6: Ejecutar GREEN, repeticion y commit**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_concurrencia_recetas.py tests/integracion/test_cancelacion_recetas.py tests/integracion/test_frontera_mutable_recetas.py tests/integracion/test_procesos.py -q
uv run --no-sync pytest tests/unidad/test_concurrencia_recetas.py --count=20 -q
```

Expected: PASS sin flakes.

```bash
git add tramalia/core/ejecucion_recetas.py tramalia/core/modelos_operacion.py tests/unidad/test_concurrencia_recetas.py tests/integracion/test_cancelacion_recetas.py tests/integracion/test_frontera_mutable_recetas.py
git commit -m "feat: acotar concurrencia y cancelacion de recetas"
```

### Task 10: Generalizar evidencia con un sobre v2 discriminado

**Files:**

- Create: `tramalia/core/modelos_evidencia.py`
- Modify: `tramalia/core/evidencia.py`
- Modify: `tramalia/core/modelos.py`
- Modify: `tramalia/core/tablero.py`
- Modify: `tramalia/core/operaciones.py`
- Create: `tests/unidad/test_modelos_evidencia_v2.py`
- Create: `tests/integracion/test_evidencia_v2.py`
- Create: `tests/contratos/test_compatibilidad_evidencia_v1.py`

**Interfaces:** Produce `ValorTipoPaqueteEvidencia`, `ArtefactoEvidencia`, `MetadatosPaqueteEvidenciaV2`, `SobrePaqueteEvidencia`, lectura discriminada y una primitiva atomica compartida. Conserva `publicar_paquete()` y todos los modelos v1.
Las entradas publicas nuevas son `publicar_paquete_v2()` y `leer_sobre_paquete()`; la primitiva de staging permanece interna.


- [ ] **Step 1: Escribir caracterizacion RED/GREEN de v1 antes del cambio**

Congelar fixtures de paquetes v1 validos e invalidos y bytes de `metadatos.json`/bitacora. Probar que lectura, hashes, `traspaso.md`, estados y errores actuales no cambian. Esta caracterizacion debe pasar antes de tocar produccion.

- [ ] **Step 2: Escribir RED del discriminador v2**

Cubrir paquete `tipo_paquete="receta"`, artefactos portables, hashes/tamanos, identidad Git, resultado e ID de operacion. Rechazar version desconocida, discriminador ausente, campos de cierre en receta, `estado_cierre` falso, artefacto duplicado, traversal, archivo no declarado, declarado ausente, hash/tamano distinto, timestamp no UTC y resultado vacio.

La bitacora acepta `operacion="receta"`, `tipo_paquete="receta"` y `resultado_operacion`; lectores de entradas antiguas con campos ausentes conservan defaults. Tablero muestra una operacion de receta separada de cierre y no la suma como cierre fallido.

- [ ] **Step 3: Escribir RED de publicacion atomica/concurrente**

Probar fallo entre cada fase de staging/publicacion, recuperacion, dos publicaciones del mismo ID, dos IDs distintos, symlink/junction, raiz reemplazada y relectura verificada. Debe existir un solo paquete valido por ID y ningun parcial visible.

- [ ] **Step 4: Ejecutar RED v2**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_modelos_evidencia_v2.py tests/integracion/test_evidencia_v2.py tests/contratos/test_compatibilidad_evidencia_v1.py -q
```

Expected: caracterizacion v1 PASS y casos v2 FAIL por modelo ausente.

- [ ] **Step 5: Extraer escritor y agregar lectura discriminada**

Extraer del publicador actual una primitiva interna que recibe metadatos/archivos ya validados, realiza staging, fsync, `os.replace` y verificacion final. `publicar_paquete()` v1 delega sin cambiar bytes. El publicador v2 crea su sobre real; no fabrica `EjecucionPuertas`, `estado_cierre` ni `traspaso.md`.

- [ ] **Step 6: Extender bitacora/tablero de forma aditiva y ejecutar GREEN**

Agregar campos opcionales al final de dataclasses/JSON compatibles. Toda rama lee por `version_esquema` y `tipo_paquete`; no infiere tipo por nombres de archivos.

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_modelos_evidencia_v2.py tests/integracion/test_evidencia_v2.py tests/contratos/test_compatibilidad_evidencia_v1.py tests/integracion/test_evidencia_atomica.py tests/unidad/test_tablero.py tests/integracion/test_operaciones.py tests/contratos/test_metadatos_evidencia_v1.py -q
```

Expected: PASS, incluidos fixtures v1 byte por byte.

- [ ] **Step 7: Commit**

```bash
git add tramalia/core/modelos_evidencia.py tramalia/core/evidencia.py tramalia/core/modelos.py tramalia/core/tablero.py tramalia/core/operaciones.py tests/unidad/test_modelos_evidencia_v2.py tests/integracion/test_evidencia_v2.py tests/contratos/test_compatibilidad_evidencia_v1.py
git commit -m "feat: admitir evidencia tipada de recetas"
```

### Task 11: Redactar y publicar evidencia parcial de recetas

**Files:**

- Modify: `tramalia/core/redaccion.py`
- Modify: `tramalia/core/ejecucion_recetas.py`
- Modify: `tramalia/core/acciones_recetas_propias.py`
- Create: `tramalia/core/evidencia_recetas.py`
- Modify: `tests/unidad/test_redaccion.py`
- Create: `tests/unidad/test_proyeccion_evidencia_recetas.py`
- Create: `tests/integracion/test_evidencia_recetas.py`
- Create: `tests/recursos/recetas/salidas_hostiles/secretos.txt`
- Create: `tests/recursos/recetas/salidas_hostiles/control-terminal.txt`

**Interfaces:** Produce `redactar_texto_evidencia()`, `construir_archivos_evidencia_receta()` y `publicar_evidencia_receta()`.

- [ ] **Step 1: Escribir RED de redaccion en todas las salidas**

Fixtures separados contienen asignaciones token/secret/password/contrasena/api_key/authorization, bearer, PEM de clave privada, URL con credenciales, ANSI, OSC, NUL, bidi y lineas/total excesivos. Probar que el valor no aparece en:

- `ResultadoPasoReceta` expuesto;
- datos de `EventoOperacion` entregados al callback;
- JSON formal y salida CLI;
- `resultados.jsonl`, `eventos.jsonl`, `manifiesto.json` y `resumen.md`;
- error tipado por fallo inesperado.
- `ResultadoProceso.comando` proyectado: contiene identidad logica y opciones allowlisted saneadas, pero ninguna ruta absoluta, argv crudo, entorno o valor secreto.

La prueba busca el secreto original y variantes escapadas/base64 obvias. Conserva marcador de tipo, bytes totales y hash completo solo cuando ya lo entrega `ResultadoProceso`; nunca recalcula leyendo una copia cruda persistida.

- [ ] **Step 2: Escribir RED de proyeccion reproducible**

Con reloj, IDs, raiz logica y modelos congelados, dos proyecciones deben ser byte a byte iguales. JSONL usa una entrada por linea, UTF-8 y salto final; Markdown no contiene HTML activo. Cada `DeclaracionEvidenciaReceta` se resuelve a uno de los artefactos canonicos; una evidencia obligatoria ausente hace fallar publicacion y una declaracion de paso inexistente ya fue bloqueada al resolver. `transiciones.jsonl` enlaza huella anterior/posterior, decision, motivo y efectos observados/aceptados saneados sin persistir contenido crudo. `huella_contenido` excluye solo `id_paquete`, `id_operacion` y timestamps declarados volatiles, pero incluye plan, inventario, resultados, puertas, transiciones, eventos, redacciones y hashes.

Probar resultado completado, fallido, cancelado y bloqueado; los tres ultimos publican lo completado y explican pasos pendientes/bloqueados. Salida truncada conserva banderas, bytes y SHA. Ningun resultado parcial se presenta como `COMPLETADA`.

- [ ] **Step 3: Escribir RED de publicacion y fallo**

Exigir los ocho archivos minimos, metadatos v2, bitacora `receta`, verificacion posterior y confinamiento. Inyectar fallo antes/durante/despues de escritura: nunca devolver `COMPLETADA` con paquete ausente o corrupto. Publicar con mismo `id_paquete` falla cerrado; otro ID no sobrescribe.

- [ ] **Step 4: Ejecutar RED**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_redaccion.py tests/unidad/test_proyeccion_evidencia_recetas.py tests/integracion/test_evidencia_recetas.py -q
```

Expected: FAIL por modulos ausentes.

- [ ] **Step 5: Implementar saneamiento antes de observar/persistir**

Componer `sanear_texto_externo()` de 03a con patrones adicionales acotados. Aplicar redaccion al crear el resultado/evento, no solo al serializar; asi ninguna superficie recibe secreto. Construir cada archivo mediante proyecciones explicitas a `ValorJSON`; no usar `asdict()`.

- [ ] **Step 6: Implementar publicacion y GREEN**

Delegar en la primitiva v2 de Task 10 y releer el paquete antes de devolver su ruta. Publicar incluso fallo/cancelacion cuando ya hubo ejecucion; si el plan se rechazo por huella antes de ejecutar, no crear evidencia.

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_redaccion.py tests/unidad/test_proyeccion_evidencia_recetas.py tests/integracion/test_evidencia_recetas.py tests/integracion/test_evidencia_v2.py -q
uv run --no-sync semgrep scan --config configuracion/semgrep/seguridad-python.yml --error --metrics=off --disable-version-check tramalia/core/redaccion.py tramalia/core/evidencia_recetas.py
```

Expected: PASS y sin hallazgos Semgrep.

- [ ] **Step 7: Commit**

```bash
git add tramalia/core/redaccion.py tramalia/core/ejecucion_recetas.py tramalia/core/acciones_recetas_propias.py tramalia/core/evidencia_recetas.py tests/unidad/test_redaccion.py tests/unidad/test_proyeccion_evidencia_recetas.py tests/integracion/test_evidencia_recetas.py tests/recursos/recetas/salidas_hostiles/secretos.txt tests/recursos/recetas/salidas_hostiles/control-terminal.txt
git commit -m "feat: publicar evidencia saneada de recetas"
```

### Task 12: Orquestar replanificacion, huella y drift en ServicioRecetas

**Files:**

- Create: `tramalia/core/servicio_recetas.py`
- Create: `tests/unidad/test_servicio_recetas.py`
- Create: `tests/integracion/test_servicio_recetas.py`
- Create: `tests/integracion/test_drift_recetas.py`
- Create: `tests/contratos/test_pureza_consultas_recetas.py`
- Modify: `tests/contratos/test_aislamiento_recetas_habilidades.py`

**Interfaces:** Implementa exactamente `ResumenReceta` y `ServicioRecetas` definidos en “Servicio de aplicacion”.

- [ ] **Step 1: Escribir RED de consultas y errores**

`listar()` devuelve resumenes estables; `explicar()` exige ID/version inequivocos; `planificar()` y `simular()` comparten la misma huella y la misma resolucion de `id_tarea`. Probar tarea explicita valida/invalida y ausencia con cero/una/varias tareas gobernadas; el ID efectivo queda en `SolicitudReceta` antes de huellar. Proyecto no gobernado, receta ausente/ambigua o catalogo estructuralmente invalido producen errores tipados. Una resolucion por capacidades/permisos/red devuelve `PlanReceta` con bloqueos y `ejecutable=False`; solo intentar ejecutarlo produce `ErrorPlanRecetaBloqueado` antes de una accion. Instrumentar disco/red y calcular la huella del arbol antes/despues de `listar`, `explicar`, `planificar` y `simular`: las consultas no escriben ni abren red.

- [ ] **Step 2: Escribir RED de confirmacion y replanificacion**

Confirmacion vacia, no SHA, incorrecta u obsoleta falla antes de adquirir acciones, cruzar frontera o crear evidencia. Con huella correcta, `ejecutar()` adquiere lock, vuelve a cargar las mismas fuentes y construye un plan nuevo; ejecuta ese plan vigente exactamente una vez.

Entre planificar y ejecutar, variar de forma parametrizada:

- bytes/version de receta;
- version/descripcion/modo de accion e ID/version/hash de perfil de proceso;
- presencia/version/ruta logica de herramienta;
- capacidad de nucleo o habilidad;
- huella de habilidades;
- HEAD/estado Git relevante;
- crear/cambiar/eliminar/reemplazar insumo;
- permiso, politica de red, efecto o limite.

Cada cambio previo a una accion produce `ErrorHuellaRecetaObsoleta`, incluye huella esperada/observada saneadas y cero efectos de ese paso. Parametrizar deriva antes de pasos de lectura o mutacion: la revalidacion impide invocarlos. En contraste, una accion mutante de prueba cambia solo su efecto declarado, el avance actualiza el estado esperado y un consumidor dependiente se ejecuta; si cambia otra ruta, HEAD/rama, perfil, herramienta o politica, el avance falla, no inicia otro paso y conserva una transicion/reporte honesto de lo ocurrido. Un cambio solo en ruta absoluta del clon, PID, `mtime` o reloj no invalida. Una prueba de carrera documenta el intervalo externo residual sin prometer aislamiento de filesystem.

- [ ] **Step 3: Escribir RED de lock y cierre de operacion**

Dos servicios en procesos distintos intentan mutar: uno obtiene `mutacion-proyecto`, el otro recibe `ErrorOperacionEnCurso`. Una receta de lectura tambien se revalida, pero solo adquiere lock si va a publicar evidencia; definir y probar que ninguna planificacion se bloquea por una mutacion activa. Excepcion de accion, cancelacion o fallo de publicacion libera el lock.

- [ ] **Step 4: Ejecutar RED**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_servicio_recetas.py tests/integracion/test_servicio_recetas.py tests/integracion/test_drift_recetas.py tests/contratos/test_pureza_consultas_recetas.py tests/contratos/test_aislamiento_recetas_habilidades.py -q
```

Expected: FAIL por servicio ausente.

- [ ] **Step 5: Implementar fachada e inyecciones**

El constructor exige `politica`; reloj UTC/monotono, generador de ID, fuentes, registro e inventario son inyectables. La CLI aporta `crear_politica_recetas_predeterminada()`, no una politica inferida del TOML. Los metodos publicos no renderizan. Todos los metodos que reciben `SolicitudReceta` validan el `id_tarea` explicito o resuelven una unica tarea gobernada actual antes de capturar el contexto; ausencia/ambiguedad falla, de modo que planificar, simular y ejecutar usan la misma solicitud resuelta y huella. `ejecutar()` deriva `id_operacion`, adquiere el lock, replantea y compara la huella con `hmac.compare_digest`, y crea `estado_esperado_inicial` desde el plan.

El callback `revalidar_antes_de_paso` recaptura dentro del lock y compara componentes inmutables y contexto mutable contra el estado esperado vigente. `avanzar_contexto_despues_de_paso` vuelve a capturar despues de toda accion invocada, incluso fallida: para lectura exige igualdad; para mutacion calcula el delta. Una transicion aprobada devuelve el nuevo estado; una ruta no declarada o cambio inmutable devuelve estado `None` y transicion rechazada, que obliga a detenerse pero preserva evidencia. El servicio no “replanifica” contra el snapshot inicial despues de efectos propios ni cambia la huella confirmada. Finalmente publica evidencia con todas las transiciones, emite el evento terminal y devuelve el resultado enriquecido. No acepta un `PlanReceta` aportado por CLI/TUI.

- [ ] **Step 6: Ejecutar GREEN y prueba de aislamiento**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_servicio_recetas.py tests/integracion/test_servicio_recetas.py tests/integracion/test_drift_recetas.py tests/contratos/test_pureza_consultas_recetas.py tests/contratos/test_aislamiento_recetas_habilidades.py -q
uv run --no-sync mypy tramalia/core/servicio_recetas.py
```

Expected: PASS; activar habilidad nunca dispara receta.

- [ ] **Step 7: Commit**

```bash
git add tramalia/core/servicio_recetas.py tests/unidad/test_servicio_recetas.py tests/integracion/test_servicio_recetas.py tests/integracion/test_drift_recetas.py tests/contratos/test_pureza_consultas_recetas.py tests/contratos/test_aislamiento_recetas_habilidades.py
git commit -m "feat: orquestar recetas con revalidacion"
```

### Task 13: Exponer recetas en CLI y JSON v1

**Files:**

- Create: `tramalia/cli/recetas.py`
- Modify: `tramalia/cli/catalogo_comandos.py`
- Modify: `tramalia/cli/comandos.py`
- Modify: `tramalia/cli/salida_estructurada.py`
- Modify: `tramalia/i18n/es.json`
- Modify: `tramalia/i18n/en.json`
- Create: `tests/contratos/test_cli_recetas.py`
- Modify: `tests/contratos/test_catalogo_cli.py`
- Modify: `tests/contratos/test_salida_estructurada_cli.py`
- Modify: `tests/contratos/test_paridad_operaciones_terminal.py`
- Create: `tests/integracion/test_cli_recetas_subproceso.py`

**Interfaces:** Agrega `recetas listar|explicar|planificar|simular|ejecutar` al catalogo de 03b, con manejadores/serializadores explicitos y mismo `ServicioRecetas`.

- [ ] **Step 1: Escribir RED del catalogo y ayuda bilingue**

Exigir un `DefinicionComandoPublico` visible en ayuda/menu/automatizacion, categoria adecuada y cinco `DefinicionSubcomando`. Cada uno declara capacidad, operacion, manejador, serializador, 2-3 ejemplos, salida y siguiente accion; claves ES/EN tienen paridad. `--help` en ambos idiomas explica receta, simulacion, huella, red y que ejecutar crea evidencia.

La CLI reutiliza `separar_referencia_receta()`; ID vacio, mas de un `@`, version vacia o caracteres no portables fallan con codigo 2. Omitir ID nunca lista/ejecuta todas.

- [ ] **Step 2: Escribir RED de comandos de consulta**

Probar texto y JSON para listar, explicar, planificar y simular. JSON mantiene sobre v1 y `datos.operacion`; serializa todos los campos contractuales sin rutas absolutas/ANSI. Plan bloqueado se representa como respuesta exitosa de planificacion con `ejecutable=false`, no como ejecucion exitosa. Hash del arbol antes/despues es identico.

- [ ] **Step 3: Escribir RED de ejecucion no interactiva**

En `--formato json` o stdin no TTY, omitir `--confirmar-huella` es uso invalido, codigo 2 y cero mutacion. En texto con TTY, la CLI muestra simulacion/huella y puede solicitar que el usuario confirme exactamente esa huella; cancelar el prompt no ejecuta. Una huella aportada pero mal formada usa codigo 2; una huella bien formada y obsoleta devuelve error de dominio no cero. Con huella vigente, el subproceso ejecuta `inventario-proyecto`, JSON/texto son coherentes y el paquete v2 es verificable. Cancelacion produce el codigo documentado y evidencia parcial si ya habia ejecucion.

- [ ] **Step 4: Ejecutar RED**

Run:

```powershell
uv run --no-sync pytest tests/contratos/test_cli_recetas.py tests/contratos/test_catalogo_cli.py tests/contratos/test_salida_estructurada_cli.py tests/contratos/test_paridad_operaciones_terminal.py tests/integracion/test_cli_recetas_subproceso.py -q
```

Expected: FAIL por comando ausente.

- [ ] **Step 5: Implementar adaptador delgado y serializadores**

La CLI crea `ServicioRecetas` con `crear_politica_recetas_predeterminada()`; nunca deriva permisos desde el TOML.

Registrar claves de manejador, no callables, en catalogo. El controlador construye `SolicitudReceta`, llama `ServicioRecetas` y entrega modelos al renderizador. Serializadores por operacion convierten modelos a `ValorJSON` explicitamente. Reusar las validaciones globales `--formato`, `--plain`, `NO_COLOR` y errores de 03b; no crear parser, consola Rich ni estado global paralelos.

- [ ] **Step 6: Ejecutar GREEN y smokes**

Run:

```powershell
uv run --no-sync pytest tests/contratos/test_cli_recetas.py tests/contratos/test_catalogo_cli.py tests/contratos/test_salida_estructurada_cli.py tests/contratos/test_paridad_operaciones_terminal.py tests/integracion/test_cli_recetas_subproceso.py -q
uv run --no-sync tramalia recetas listar --formato json
uv run --no-sync tramalia recetas explicar inventario-proyecto --formato json
```

Expected: PASS y cada stdout contiene exactamente un JSON valido.

- [ ] **Step 7: Commit**

```bash
git add tramalia/cli/recetas.py tramalia/cli/catalogo_comandos.py tramalia/cli/comandos.py tramalia/cli/salida_estructurada.py tramalia/i18n/es.json tramalia/i18n/en.json tests/contratos/test_cli_recetas.py tests/contratos/test_catalogo_cli.py tests/contratos/test_salida_estructurada_cli.py tests/contratos/test_paridad_operaciones_terminal.py tests/integracion/test_cli_recetas_subproceso.py
git commit -m "feat: exponer recetas en cli"
```

### Task 14: Incorporar receta de referencia, paquete, documentacion y E2E

**Files:**

- Create: `tramalia/catalogo/recetas_propias/inventario-proyecto/receta.toml`
- Create: `tramalia/catalogo/recetas_propias/inventario-proyecto/LICENCIA.txt`
- Create: `docs/recetas.md`, `docs/recetas.en.md`
- Create: `docs/tutorial-recetas.md`, `docs/tutorial-recetas.en.md`
- Create: `docs/guias/recetas.md`, `docs/guias/recetas.en.md`
- Create: `docs/referencia/recetas.md`, `docs/referencia/recetas.en.md`
- Create: `docs/desarrollo/recetas.md`, `docs/desarrollo/recetas.en.md`
- Create: `docs/desarrollo/crear-recetas.md`, `docs/desarrollo/crear-recetas.en.md`
- Create: `docs/privacidad-recetas.md`, `docs/privacidad-recetas.en.md`
- Create: `docs/migracion-recetas.md`, `docs/migracion-recetas.en.md`
- Create: `scripts/generar_capturas_cli_recetas.py`
- Create: `docs/assets/cli/recetas-listar.svg`, `docs/assets/cli/recetas-simular.svg`, `docs/assets/cli/recetas-ejecutar.svg`
- Modify: `docs/desarrollo/inventario_api.toml`
- Modify: `docs/conceptos-basicos.md`, `docs/conceptos-basicos.en.md`
- Modify: `docs/glosario.md`, `docs/glosario.en.md`
- Modify: `docs/seguridad/modelo-amenazas.md`
- Create: `docs/seguridad/modelo-amenazas.en.md`
- Modify: `docs/comandos.md`, `docs/comandos.en.md`
- Modify: `mkdocs.yml`
- Modify: `pyproject.toml`
- Modify: `tramalia/__init__.py`
- Modify: `uv.lock`
- Modify: `CHANGELOG.md`
- Modify: `.github/workflows/validacion.yml`
- Create: `tests/contratos/test_entrega_05a.py`
- Create: `tests/contratos/test_capturas_cli_recetas.py`
- Create: `tests/publicacion/test_paquete_recetas.py`
- Create: `tests/integracion/test_receta_inventario_proyecto.py`
- Create: `tests/integracion/test_wheel_recetas.py`
- Modify: `tests/publicacion/test_flujos_github.py`

**Interfaces:** Entrega la receta propia, navegacion Material/mkdocstrings, contenido de wheel/sdist y corte E2E de listar-planificar-simular-confirmar-ejecutar-evidenciar.

- [ ] **Step 1: Escribir RED de la receta propia**

El fixture esperado es equivalente a este esquema canonico; el serializador determina el formato final exacto:

```toml
version_esquema = 1
id_receta = "inventario-proyecto"
version = "1.0.0"
titulo = "Inventario del proyecto"
descripcion = "Registra herramientas y capacidades observadas sin usar red."
licencia = "PolyForm-Noncommercial-1.0.0"
politica_fallo = "detener_todo"
politica_red = "sin_red"
permisos = ["leer_proyecto"]
datos_sensibles = ["metadatos_proyecto"]
concurrencia_maxima = 1

[[precondiciones]]
id_precondicion = "proyecto-adoptado"
tipo = "capacidad"
valor = "nucleo:proyecto_adoptado"

[[pasos]]
id_paso = "registrar-inventario"
id_accion = "tramalia.inventario.registrar"
dependencias = []
insumos = ["pyproject.toml"]
efectos = []

[pasos.argumentos]
formato = "json"

[pasos.limites]
limite_segundos = 30.0
limite_salida_bytes_por_canal = 1048576

[[puertas]]
id_puerta = "inventario-completado"
pasos = ["registrar-inventario"]
estados_aceptados = ["completado"]
bloqueante = true

[[evidencias]]
id_evidencia = "inventario-observado"
fuente = "inventario"
obligatoria = true
```

Probar que es propia, offline, lectura, licencia presente, planificable aun si `pyproject.toml` esta ausente —la ausencia queda huellada—, simula cero tokens y ejecuta sin red. El resultado refleja herramientas presentes/ausentes sin afirmar que todas fueron auditadas.

- [ ] **Step 2: Escribir RED de paquete y licencia**

Construir wheel/sdist en temporal e inspeccionar sus miembros. Exigir todos los TOML/licencias reales del catalogo, modulos publicos, i18n y metadata legal; no fijar cantidad de recetas. Instalar el wheel en entorno aislado sin checkout/PYTHONPATH y ejecutar listar, explicar, planificar, simular y receta de referencia. El sdist reconstruye el mismo wheel.

- [ ] **Step 3: Escribir RED documental ES/EN y de limite de dominio**

`test_entrega_05a.py` exige:

- paginas ES/EN, navegacion Material y mkdocstrings desde `inventario_api.toml`;
- diagrama coherente planificar -> simular -> confirmar -> ejecutar -> evidenciar;
- explicacion en espanol llano de receta, accion, capacidad, inventario, huella, drift, simulacion, frontera mutable, evidencia y puerta/gate;
- tutorial reproducible sin red ni secretos;
- referencia TOML/CLI/JSON/Python, codigos de error, recuperacion y troubleshooting;
- guia de autoria/versionado/licencia/pruebas de recetas y packs declarativos, sin codigo ejecutable externo;
- politica ES/EN de categorias de datos, redaccion, retencion, borrado y limites de evidencia;
- notas de compatibilidad/migracion del esquema 1 y evidencia v1/v2;
- tres capturas CLI SVG generadas desde escenarios congelados, con texto alternativo traducido y sin datos de la maquina;
- modelo de amenazas para packs hostiles, proceso, red declarativa, symlinks, secretos, concurrencia y supply chain;
- declaracion honesta de que politica de red no es aislamiento del SO;
- no importar `controles_seguridad`, `hallazgos`, `remediacion`, TUI de seguridad, MCP de auditoria, XLSX o HTML desde modulos 05a;
- ningun texto afirma certificacion, cumplimiento total o ausencia de vulnerabilidades.

- [ ] **Step 4: Ejecutar RED**

Run:

```powershell
uv run --no-sync pytest tests/integracion/test_receta_inventario_proyecto.py tests/publicacion/test_paquete_recetas.py tests/integracion/test_wheel_recetas.py tests/contratos/test_entrega_05a.py tests/contratos/test_capturas_cli_recetas.py -q
uv run --no-sync mkdocs build --strict
```

Expected: FAIL por receta, package-data y paginas ausentes.

- [ ] **Step 5: Implementar receta y empaquetado**

Agregar package-data de forma recursiva y verificable, sin lista fragil de cantidades. Declarar licencia por archivo conforme al corte de 04. El catalogo de proyecto no se empaqueta. Mantener `1.0.0b2.dev0` en `pyproject.toml`, `tramalia.__version__` y `uv.lock`; actualizar changelog bajo esa seccion de desarrollo sin crear tag ni publicar una BETA parcial del Plan 05.

Extender `validacion.yml` para ejecutar `test_entrega_05a.py`, CLI subprocess y smoke del wheel en la matriz final de Python 3.11-3.14 y Windows/Linux/macOS sin duplicar jobs. Conservar como regresiones obligatorias de 04 la instalacion con hashes de `requisitos-documentacion.txt`, el proyecto generado validado por Semgrep/Gitleaks, las capturas TUI y la comparacion Playwright dentro de la imagen Docker fijada. `test_flujos_github.py` comprueba esos comandos, acciones fijadas, digest Docker y permisos de solo lectura; los equivalentes POSIX viven en CI, no en interpolaciones PowerShell.

- [ ] **Step 6: Escribir documentacion Material y referencia API**

Mantener paleta, tipografia, Mermaid vendorizado, contraste y breakpoints del sitio. Los diagramas usan las clases/colores ya definidas por 04 y conservan alternativa textual. Mkdocstrings documenta solo APIs publicas del inventario; paginas no duplican docstrings. `generar_capturas_cli_recetas.py` usa servicio/reloj/inventario falsos congelados, exporta los tres SVG desde el renderizador CLI real y el contrato regenera en temporal para comparar bytes/nombres. Explicar que 05a sirve a cualquier proyecto adoptado/gobernado por Tramalia, independientemente de su tecnologia, y que seguridad/remediacion son consumidores separados de 05b/05c.

- [ ] **Step 7: Ejecutar GREEN, build y smoke aislado**

Run:

```powershell
uv run --no-sync python scripts/generar_capturas_cli_recetas.py --salida .artefactos/capturas-cli-recetas
uv run --no-sync pytest tests/integracion/test_receta_inventario_proyecto.py tests/publicacion/test_paquete_recetas.py tests/integracion/test_wheel_recetas.py tests/contratos/test_entrega_05a.py tests/contratos/test_capturas_cli_recetas.py tests/contratos/test_documentacion.py -q
uv run --no-sync mkdocs build --strict
uv run --no-sync python scripts/construir_documentacion_sin_conexion.py
$salida = Join-Path $env:TEMP ("tramalia-05a-" + [guid]::NewGuid().ToString("N"))
uv build --out-dir $salida
$distribuciones = Get-ChildItem -LiteralPath $salida -File | Where-Object { $_.Name -like "*.whl" -or $_.Name -like "*.tar.gz" } | ForEach-Object FullName
uv run --no-sync twine check $distribuciones
uv run --no-sync pytest tests/integracion/test_wheel_recetas.py -q
```

Expected: PASS; wheel/sdist contienen receta/licencia y el smoke no depende del checkout.

- [ ] **Step 8: Commit**

```bash
git add tramalia/catalogo/recetas_propias/inventario-proyecto/receta.toml tramalia/catalogo/recetas_propias/inventario-proyecto/LICENCIA.txt tramalia/__init__.py docs/recetas.md docs/recetas.en.md docs/tutorial-recetas.md docs/tutorial-recetas.en.md docs/guias/recetas.md docs/guias/recetas.en.md docs/referencia/recetas.md docs/referencia/recetas.en.md docs/desarrollo/recetas.md docs/desarrollo/recetas.en.md docs/desarrollo/crear-recetas.md docs/desarrollo/crear-recetas.en.md docs/privacidad-recetas.md docs/privacidad-recetas.en.md docs/migracion-recetas.md docs/migracion-recetas.en.md docs/desarrollo/inventario_api.toml docs/conceptos-basicos.md docs/conceptos-basicos.en.md docs/glosario.md docs/glosario.en.md docs/seguridad/modelo-amenazas.md docs/seguridad/modelo-amenazas.en.md docs/comandos.md docs/comandos.en.md docs/assets/cli/recetas-listar.svg docs/assets/cli/recetas-simular.svg docs/assets/cli/recetas-ejecutar.svg scripts/generar_capturas_cli_recetas.py mkdocs.yml pyproject.toml uv.lock CHANGELOG.md .github/workflows/validacion.yml tests/contratos/test_entrega_05a.py tests/contratos/test_capturas_cli_recetas.py tests/publicacion/test_paquete_recetas.py tests/publicacion/test_flujos_github.py tests/integracion/test_receta_inventario_proyecto.py tests/integracion/test_wheel_recetas.py
git commit -m "docs: documentar motor de recetas"
```

## Puerta final de 05a

Ejecutar desde arbol limpio y entorno Python 3.11. Repetir la matriz remota de Python 3.11-3.14 y Windows/Linux/macOS antes de integrar.

```powershell
uv lock --check --python 3.11
uv sync --python 3.11 --locked --group desarrollo --group seguridad --all-extras
uv pip install --require-hashes -r requisitos-documentacion.txt
uv run --no-sync pytest
uv run --no-sync pytest tests/unidad/test_planificacion_recetas.py tests/unidad/test_concurrencia_recetas.py --count=20 -q
uv run --no-sync pytest tests/contratos/test_entrega_03c.py tests/contratos/test_prerrequisitos_05a.py tests/contratos/test_entrega_05a.py -q
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy tramalia
uv run --no-sync actionlint
uv run --no-sync semgrep scan --test --config configuracion/semgrep/seguridad-python.yml --metrics=off --disable-version-check tests/recursos/semgrep/inseguro.py
uv run --no-sync semgrep scan --config configuracion/semgrep/seguridad-python.yml --error --metrics=off --disable-version-check --exclude tests/recursos/semgrep tramalia scripts tests
uv run --no-sync python scripts/generar_proyecto_prueba_seguridad.py --salida .artefactos/seguridad/proyecto-generado
uv run --no-sync semgrep scan --config configuracion/semgrep/seguridad-python.yml --error --metrics=off --disable-version-check .artefactos/seguridad/proyecto-generado
$ruta_gitleaks = uv run --no-sync python scripts/instalar_gitleaks.py --destino "$HOME/.local/bin" | Select-Object -Last 1
& $ruta_gitleaks git --redact --no-banner --config .gitleaks.toml --exit-code 1
& $ruta_gitleaks dir . --redact --no-banner --config .gitleaks.toml --max-target-megabytes 10 --exit-code 1
& $ruta_gitleaks dir .artefactos/seguridad/proyecto-generado --redact --no-banner --config .gitleaks.toml --exit-code 1
uv run --no-sync mkdocs build --strict
uv run --no-sync python scripts/construir_documentacion_sin_conexion.py
uv run --no-sync python scripts/generar_capturas_cli_recetas.py --salida .artefactos/capturas-cli-recetas-final
uv run --no-sync python scripts/generar_capturas_tui.py --salida .artefactos/capturas-tui-final
uv run --no-sync pytest tests/contratos/test_capturas_tui.py -q
uv run --no-sync pytest tests/contratos/test_capturas_cli_recetas.py -q
npm ci --ignore-scripts
npm run prueba:guardia-capturas
npm run prueba:servidor-documentacion
npx playwright install chromium
npm run prueba:ux
docker run --rm --ipc=host --env CI=1 --env TRAMALIA_COMPARAR_CAPTURAS=1 --volume "${PWD}:/trabajo" --workdir /trabajo mcr.microsoft.com/playwright:v1.61.1-noble@sha256:5b8f294aff9041b7191c34a4bab3ac270157a28774d4b0660e9743297b697e48 bash -lc "npm ci --ignore-scripts && npm run prueba:ux"
npm run prueba:lighthouse
$salida = Join-Path $env:TEMP ("tramalia-puerta-05a-" + [guid]::NewGuid().ToString("N"))
uv build --out-dir $salida
$distribuciones = Get-ChildItem -LiteralPath $salida -File | Where-Object { $_.Name -like "*.whl" -or $_.Name -like "*.tar.gz" } | ForEach-Object FullName
uv run --no-sync twine check $distribuciones
uv run --no-sync pytest tests/integracion/test_wheel_recetas.py -q
git diff --check
git status --porcelain
```

En Linux/macOS, `validacion.yml` ejecuta los mismos contratos con sintaxis POSIX; el bloque minimo que protege las diferencias de shell es:

```bash
uv sync --python 3.11 --locked --group desarrollo --group seguridad --all-extras
uv pip install --require-hashes -r requisitos-documentacion.txt
uv run --no-sync pytest
uv run --no-sync mkdocs build --strict
uv run --no-sync python scripts/construir_documentacion_sin_conexion.py
salida="$(mktemp -d)"
uv build --out-dir "$salida"
find "$salida" -maxdepth 1 -type f \( -name '*.whl' -o -name '*.tar.gz' \) -print0 | xargs -0 uv run --no-sync twine check
uv run --no-sync pytest tests/integracion/test_wheel_recetas.py -q
```

La matriz CI, no el bloque local PowerShell, es la evidencia autoritativa de Python 3.11-3.14 y Windows/Linux/macOS.

Expected:

- toda la suite y las repeticiones pasan sin flakes;
- Semgrep, Gitleaks, Actionlint, Ruff y mypy pasan;
- MkDocs Material ES/EN, Playwright/axe y Lighthouse pasan;
- wheel/sdist son validos, contienen catalogo/licencias y funcionan aislados;
- `git diff --check` y `git status --porcelain` no muestran salida;
- planificar/simular no escriben ni abren red;
- toda deriva respecto del estado esperado vigente aborta antes del paso; efectos propios declarados avanzan el contexto sin alterar la huella confirmada, deltas no declarados fallan y el TOCTOU externo residual queda documentado;
- una receta no se ejecuta por inferencia, activacion de habilidad, visita de CLI/TUI ni carga de documentacion;
- fallos, cancelaciones y publicaciones parciales conservan evidencia honesta;
- v1 se lee igual y v2 nunca se interpreta como cierre;
- 05a no importa ni adelanta evaluacion de seguridad o remediacion.

## Matriz de trazabilidad de aceptacion

| Criterio aprobado | Tasks que lo demuestran |
|---|---|
| Motor aplicable a cualquier proyecto adoptado y separado de seguridad/remediacion | 3-7, 12-14 y `test_entrega_05a.py` |
| Ninguna receta por inferencia o activacion de habilidad | 5, 12, 13 y `test_aislamiento_recetas_habilidades.py` |
| Listar/planificar/simular sin red ni escritura | 5-7, 12-13 y `test_pureza_consultas_recetas.py` |
| Simulacion explica alcance, permisos, limites y coste | 7 y contratos CLI/documentales de 13-14 |
| Ejecucion exige huella vigente y detecta drift | 6, 9, 12-13 |
| Procesos acotados, cancelacion y concurrencia | 8-9 |
| Evidencia reproducible y parcial honesta | 10-12 |
| Compatibilidad byte a byte con evidence pack v1 | 10 |
| CLI/JSON desde el mismo servicio | 12-13 |
| MkDocs Material, mkdocstrings y diagramas coherentes | 14 |
| Wheel/sdist con receta y licencia | 14 |
| Sin cantidad artificial de tests | todas; la seleccion se justifica por contrato/riesgo |

## Secuencia posterior

Una vez cerrada y revisada 05a, crear planes ejecutables separados para 05b, 05c y 05d. 05b consume `ServicioRecetas` para evaluar controles; 05c consume resultados/hallazgos de 05b para remediacion seleccionada manualmente; 05d consolida TUI, MCP opcional e importacion/exportacion. Ninguno modifica la independencia del motor generico ni convierte la activacion de habilidades en ejecucion.
