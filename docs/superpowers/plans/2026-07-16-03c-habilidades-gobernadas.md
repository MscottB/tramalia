# Plan de implementacion de habilidades gobernadas por proyecto

> **Para agentes de implementacion:** HABILIDAD AUXILIAR OBLIGATORIA: usar `superpowers:subagent-driven-development` (recomendada) o `superpowers:executing-plans` para implementar el plan Task por Task. Los Step usan casillas (`- [ ]`) para seguimiento.

**Objetivo:** Convertir las habilidades de Tramalia en un catalogo tipado, seguro y explicable, con perfiles por proyecto, activacion efectiva, resolucion reproducible, contenido metodologico ampliado y operaciones compartidas por CLI, TUI y MCP.

**Arquitectura:** `tramalia.core.habilidades` permanece como fachada compatible para la gestion Git existente. Nuevos modulos pequenos separan modelos, catalogo, configuracion, perfiles, resolucion, materializacion, auditoria y servicio. Las fuentes canonicas empacadas viven bajo `tramalia/catalogo/habilidades_propias/<id>/`; `.tramalia/habilidades/` es solo la proyeccion activa del proyecto. El proyecto declara intencion y fuentes personalizadas en `.tramalia/habilidades.toml`; el resolvedor produce un plan puro y una transaccion serializada, recuperable y protegida por lock interproceso materializa exclusivamente las habilidades activas.

**Tecnologias:** Python 3.11-3.14, `dataclasses`, `enum.StrEnum`, `datetime`, `tomllib`, serializador TOML determinista propio, JSON, `pathlib`, Git CLI mediante `tramalia.core.procesos`, pytest 8, Semgrep/Gitleaks y validadores del Plan 03a, MkDocs Material y Textual del Plan 03b.

## Restricciones globales

- El plan se ejecuta despues del Plan 03a y antes del Plan 03b.
- Todo comportamiento nuevo se implementa con RED-GREEN-REFACTOR.
- Nombres de modulos, clases, funciones, variables, tests y archivos propios usan espanol ASCII.
- Los comentarios internos estan en espanol y explican invariantes o riesgos.
- Las APIs publicas mantienen docstrings ingleses estilo Google segun el diseno BETA aprobado.
- La IA puede recomendar un plan, pero nunca activar, descargar ni conceder permisos silenciosamente.
- Planificar, listar y explicar son operaciones puras y sin red.
- Toda escritura es transaccional, serializada, recuperable, confinada a la raiz gobernada y segura en Windows, Linux y macOS; no se promete atomicidad global multiarchivo.
- No se usan enlaces simbolicos para materializar habilidades.
- Un manifiesto o catalogo invalido falla con error tipado; nunca se transforma en una coleccion vacia.
- 03c consume exactamente `ErrorConfiguracionHabilidades`, `ErrorEntradaInsegura`, `validar_nombre_habilidad()`, `validar_fuente_git()`, `resolver_ruta_confinada()`, `validar_arbol_habilidad()` y la cuarentena transaccional del Plan 03a. No crea validadores ni motores Git paralelos.
- Los limites heredados de 03a son 2.000 archivos, 4 MiB por archivo y 64 MiB totales.
- Una habilidad obligatoria solo puede desactivarse con excepcion razonada, revisada y vigente.
- Los aliases ingleses existentes se conservan durante la BETA, pero la API interna nueva usa espanol.
- Los conteos de habilidades se derivan del catalogo; ningun contrato fija 13, 16, 19 u otra cifra.
- Semgrep, Gitleaks y las matrices OWASP son controles y referencias, no una certificacion.

---

## Mapa de archivos final

| Ruta | Responsabilidad |
|---|---|
| `tramalia/core/modelos_habilidades.py` | Enums y dataclasses inmutables del dominio. |
| `tramalia/core/catalogo_habilidades.py` | Carga y validacion de `habilidad.toml` y catalogos empacados. |
| `tramalia/core/configuracion_habilidades.py` | Intencion del proyecto, migracion y excepciones. |
| `tramalia/core/perfiles_habilidades.py` | Catalogo de perfiles tipados. |
| `tramalia/core/resolucion_habilidades.py` | Precedencia, dependencias, conflictos y plan puro. |
| `tramalia/core/materializacion_habilidades.py` | Staging, activacion/desactivacion y transaccion recuperable. |
| `tramalia/core/auditoria_habilidades.py` | Procedencia, integridad, permisos y hallazgos versionados. |
| `tramalia/core/servicio_habilidades.py` | Operaciones compartidas para superficies. |
| `tramalia/core/habilidades.py` | Fachada Git compatible; delega al dominio nuevo. |
| `tramalia/catalogo/habilidades_propias/<id>/` | Fuente canonica empacada de cada habilidad propia. |
| `tramalia/catalogo/habilidades_externas.toml` | Sugerencias externas estructuradas, sin bloques comentados. |
| `tramalia/catalogo/perfiles_habilidades.toml` | Perfiles base, api, frontend, datos, legado, release, agentico, mcp y alta-seguridad. |
| `tramalia/catalogo/aliases_habilidades.toml` | Migracion de identificadores ingleses historicos. |
| `tramalia/templates/project/.tramalia/habilidades.toml` | Intencion inicial del proyecto, esquema 1. |
| `tramalia/templates/project/.tramalia/habilidades/` | Directorio inicialmente vacio; el scaffold materializa solo el plan `base`. |
| `tests/unidad/test_*habilidades*.py` | Contratos puros de modelos, catalogo, perfiles y resolucion. |
| `tests/integracion/test_*habilidades*.py` | Filesystem, Git, cuarentena, locks y atomicidad. |
| `tests/contratos/test_contenido_habilidades.py` | Contrato editorial, fuentes y nombres. |

## Interfaces compartidas

```python
# tramalia/core/modelos_habilidades.py
class ValorObligatoriedadHabilidad(StrEnum):
    OBLIGATORIA = "obligatoria"
    RECOMENDADA = "recomendada"
    OPCIONAL = "opcional"

class ValorActivacionHabilidad(StrEnum):
    ACTIVA = "activa"
    INACTIVA = "inactiva"

class ValorCompatibilidadHabilidad(StrEnum):
    COMPATIBLE = "compatible"
    PENDIENTE_HERRAMIENTA = "pendiente_herramienta"
    INCOMPATIBLE = "incompatible"
    BLOQUEADA_CONFLICTO = "bloqueada_conflicto"

class ValorInstalacionHabilidad(StrEnum):
    NO_INSTALADA = "no_instalada"
    INSTALADA = "instalada"

class ValorIntegridadHabilidad(StrEnum):
    NO_VERIFICADA = "no_verificada"
    VERIFICADA = "verificada"
    MODIFICADA = "modificada"
    INVALIDA = "invalida"

class ValorActualizacionHabilidad(StrEnum):
    NO_CONSULTADA = "no_consultada"
    ACTUAL = "actual"
    DISPONIBLE = "disponible"
    ERROR_CONSULTA = "error_consulta"

class ValorOrigenDecisionHabilidad(StrEnum):
    EXPLICITA = "explicita"
    PERFIL_OBLIGATORIO = "perfil_obligatorio"
    PERFIL_RECOMENDADO = "perfil_recomendado"
    DETECCION = "deteccion"
    PREDETERMINADA = "predeterminada"

class ValorPoliticaExcepcionHabilidad(StrEnum):
    NO_PERMITIDA = "no_permitida"
    PERMITIDA = "permitida"

class ValorOperacionCambioHabilidades(StrEnum):
    ACTIVAR = "activar"
    DESACTIVAR = "desactivar"
    APLICAR_PERFIL = "aplicar_perfil"
    REHIDRATAR = "rehidratar"
    ACTUALIZAR = "actualizar"

class ValorAccionMaterializacionHabilidad(StrEnum):
    CREAR = "crear"
    ACTUALIZAR = "actualizar"
    CONSERVAR = "conservar"
    RETIRAR = "retirar"

class ValorTipoEventoOperacionHabilidades(StrEnum):
    INICIADA = "iniciada"
    PASO = "paso"
    PUBLICANDO = "publicando"
    COMPLETADA = "completada"
    FALLIDA = "fallida"
    CANCELADA = "cancelada"

@dataclass(frozen=True, slots=True)
class FuenteHabilidad:
    id: str
    url: str
    version: str
    revisada_utc: datetime

@dataclass(frozen=True, slots=True)
class FuentePersonalizadaHabilidad:
    id: str
    fuente: str
    referencia: str
    licencia: str

@dataclass(frozen=True, slots=True)
class BloqueoHabilidad:
    version_esquema: int
    id: str
    fuente: str
    referencia: str
    sha_resuelto: str
    hash_contenido: str
    licencia: str

@dataclass(frozen=True, slots=True)
class MetadatosHabilidad:
    version_esquema: int
    id: str
    nombre: str
    version: str
    categoria: str
    obligatoriedad: ValorObligatoriedadHabilidad
    activacion_predeterminada: ValorActivacionHabilidad
    politica_excepcion: ValorPoliticaExcepcionHabilidad
    riesgo: str
    tecnologias_aplicables: tuple[str, ...]
    capacidades_aplicables: tuple[str, ...]
    tipos_proyecto_aplicables: tuple[str, ...]
    dependencias: tuple[str, ...]
    conflictos: tuple[str, ...]
    herramientas_requeridas: tuple[str, ...]
    herramientas_opcionales: tuple[str, ...]
    permisos: tuple[str, ...]
    puertas: tuple[str, ...]
    evidencias: tuple[str, ...]
    fuentes: tuple[FuenteHabilidad, ...]

@dataclass(frozen=True, slots=True)
class ExcepcionHabilidad:
    razon: str
    riesgo_aceptado: str
    referencia: str
    revisor: str
    expira_utc: datetime

@dataclass(frozen=True, slots=True)
class SeleccionHabilidad:
    id: str
    activacion: ValorActivacionHabilidad
    motivo: str
    excepcion: ExcepcionHabilidad | None = None

@dataclass(frozen=True, slots=True)
class ConfiguracionHabilidadesProyecto:
    version_esquema: int
    perfiles: tuple[str, ...]
    selecciones: tuple[SeleccionHabilidad, ...]
    fuentes_personalizadas: tuple[FuentePersonalizadaHabilidad, ...]

@dataclass(frozen=True, slots=True)
class PerfilHabilidades:
    id: str
    nombre: str
    obligatorias: tuple[str, ...]
    recomendadas: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class DecisionHabilidad:
    id: str
    activacion: ValorActivacionHabilidad
    obligatoriedad: ValorObligatoriedadHabilidad
    compatibilidad: ValorCompatibilidadHabilidad
    origen: ValorOrigenDecisionHabilidad
    razon: str
    dependencias: tuple[str, ...]
    conflictos: tuple[str, ...]
    herramientas_faltantes: tuple[str, ...]
    permisos: tuple[str, ...]
    riesgo: str

@dataclass(frozen=True, slots=True)
class ObservacionHabilidad:
    id: str
    instalacion: ValorInstalacionHabilidad
    integridad: ValorIntegridadHabilidad
    actualizacion: ValorActualizacionHabilidad
    sha_instalado: str | None
    motivo: str

@dataclass(frozen=True, slots=True)
class ProcedenciaHabilidad:
    fuente: str
    referencia: str
    sha_resuelto: str | None
    hash_contenido: str | None
    licencia: str

@dataclass(frozen=True, slots=True)
class EstadoHabilidad:
    metadatos: MetadatosHabilidad
    decision: DecisionHabilidad
    observacion: ObservacionHabilidad
    procedencia: ProcedenciaHabilidad

@dataclass(frozen=True, slots=True)
class HuellaInsumoHabilidades:
    nombre: str
    sha256: str

@dataclass(frozen=True, slots=True)
class PlanResolucionHabilidades:
    version_esquema: int
    perfiles: tuple[str, ...]
    decisiones: tuple[DecisionHabilidad, ...]
    orden_activacion: tuple[str, ...]
    bloqueos: tuple[str, ...]
    huellas_insumos: tuple[HuellaInsumoHabilidades, ...]
    huella: str

    @property
    def aplicable(self) -> bool: ...

@dataclass(frozen=True, slots=True)
class SolicitudCambioHabilidades:
    operacion: ValorOperacionCambioHabilidades
    id_habilidad: str | None = None
    id_perfil: str | None = None
    motivo: str = ""
    excepcion: ExcepcionHabilidad | None = None

@dataclass(frozen=True, slots=True)
class CambioMaterializacionHabilidad:
    id_habilidad: str
    accion: ValorAccionMaterializacionHabilidad
    hash_anterior: str | None
    hash_objetivo: str | None

@dataclass(frozen=True, slots=True)
class PlanCambioHabilidades:
    version_esquema: int
    solicitud: SolicitudCambioHabilidades | None
    resolucion: PlanResolucionHabilidades
    configuracion_objetivo: ConfiguracionHabilidadesProyecto
    cambios: tuple[CambioMaterializacionHabilidad, ...]
    huellas_insumos: tuple[HuellaInsumoHabilidades, ...]
    bloqueos: tuple[str, ...]
    huella: str

    @property
    def aplicable(self) -> bool: ...

@dataclass(frozen=True, slots=True)
class ResultadoCambioHabilidades:
    aplicada: bool
    plan: PlanCambioHabilidades
    estados: tuple[EstadoHabilidad, ...]

@dataclass(frozen=True, slots=True)
class EventoOperacionHabilidades:
    id_operacion: str
    tipo: ValorTipoEventoOperacionHabilidades
    mensaje: str
    actual: int | None = None
    total: int | None = None
```

Todos los `datetime` son conscientes y normalizados a UTC. El resolvedor recibe
`reloj_utc: Callable[[], datetime]`; las pruebas fijan el reloj. Todos los
simbolos publicos anteriores y las funciones publicas inferiores llevan tipos y
docstrings ingleses estilo Google.

```python
# tramalia/core/servicio_habilidades.py
class ServicioHabilidades:
    def __init__(
        self, raiz: Path, *, reloj_utc: Callable[[], datetime],
        consultar_remoto: Callable[..., object] | None = None,
    ) -> None: ...
    def listar(self) -> tuple[EstadoHabilidad, ...]: ...
    def explicar(self, id_habilidad: str) -> EstadoHabilidad: ...
    def planificar(
        self, solicitud: SolicitudCambioHabilidades | None = None
    ) -> PlanCambioHabilidades: ...
    def activar(
        self, id_habilidad: str, *, motivo: str, confirmacion: str,
        excepcion: ExcepcionHabilidad | None = None,
        cancelada: Callable[[], bool] | None = None,
        al_evento: Callable[[EventoOperacionHabilidades], None] | None = None,
    ) -> ResultadoCambioHabilidades: ...
    def desactivar(
        self, id_habilidad: str, *, motivo: str, confirmacion: str,
        excepcion: ExcepcionHabilidad | None = None,
        cancelada: Callable[[], bool] | None = None,
        al_evento: Callable[[EventoOperacionHabilidades], None] | None = None,
    ) -> ResultadoCambioHabilidades: ...
    def aplicar_perfil(
        self, id_perfil: str, *, motivo: str, confirmacion: str,
        cancelada: Callable[[], bool] | None = None,
        al_evento: Callable[[EventoOperacionHabilidades], None] | None = None,
    ) -> ResultadoCambioHabilidades: ...
    def auditar(
        self, ids_habilidades: tuple[str, ...] = ()
    ) -> tuple[ResultadoAuditoriaHabilidad, ...]: ...
    def rehidratar(
        self, ids_habilidades: tuple[str, ...] = (), *, confirmacion: str,
        cancelada: Callable[[], bool] | None = None,
        al_evento: Callable[[EventoOperacionHabilidades], None] | None = None,
    ) -> ResultadoCambioHabilidades: ...
    def actualizar(
        self, ids_habilidades: tuple[str, ...] = (), *, confirmacion: str,
        cancelada: Callable[[], bool] | None = None,
        al_evento: Callable[[EventoOperacionHabilidades], None] | None = None,
    ) -> ResultadoCambioHabilidades: ...
```

`listar`, `explicar`, `planificar` y `auditar` son de solo lectura y nunca usan
red. `activar`, `desactivar` y `aplicar_perfil` tampoco descargan: si falta cache
verificada, el plan queda bloqueado. `rehidratar` y `actualizar` son las unicas
operaciones de servicio que pueden usar red porque su invocacion es consentimiento
explicito. Toda mutacion recalcula la misma solicitud dentro del lock
interproceso, compara `confirmacion` con la huella vigente y emite eventos; una
huella obsoleta no escribe. `motivo` es obligatorio y no vacio para activar,
desactivar o aplicar un perfil; queda persistido en la seleccion explicita o en
el registro de cambio, nunca se sustituye por texto inventado por la superficie.

### Task 1: Modelos, identificadores y fuentes canonicas completas

**Files:**
- Create: `tramalia/core/modelos_habilidades.py`
- Create: `tramalia/core/catalogo_habilidades.py`
- Modify: `tramalia/core/errores.py`
- Create: `tramalia/catalogo/habilidades_propias/<id>/SKILL.md` y `habilidad.toml` para todo el inventario historico y las capacidades 17-19
- Create: `tramalia/catalogo/habilidades_externas.toml`
- Create: `tramalia/catalogo/aliases_habilidades.toml`
- Create: `tests/unidad/test_catalogo_habilidades.py`
- Create: `tests/contratos/test_esquema_habilidades.py`
- Modify: `tests/contratos/test_contenido_habilidades.py`
- Create: `tests/contratos/test_habilidades_especializadas.py`

**Interfaces:**
- Produces: todos los modelos superiores, fuentes propias canonicas completas, aliases, `cargar_catalogo_propio()`, `cargar_catalogo_externo()` y `validar_id_habilidad()`.
- Consumes: `ErrorTramalia` y los validadores de `tramalia.core.seguridad_entradas` entregados por 03a.

- [ ] **Step 1: Escribir RED de identificadores, esquema y fuentes completas**

Además de los casos inferiores, escribir antes de implementar los contratos de
contenido y especializacion que descubren las fuentes canonicas, validan aliases,
secciones editoriales y los IDs 17-19 sin aserciones de cantidad.

```python
@pytest.mark.parametrize("id_invalido", (
    "../escape", "a/b", r"a\\b", "C:windows", "CON", "habilidad con espacio",
    "habilidad_underscore", "", "a" * 65,
))
def test_id_habilidad_rechaza_rutas_y_nombres_no_portables(id_invalido: str) -> None:
    with pytest.raises(ErrorCatalogoHabilidades, match="identificador"):
        validar_id_habilidad(id_invalido)


def test_catalogo_toml_invalido_no_se_convierte_en_vacio(tmp_path: Path) -> None:
    ruta = tmp_path / "habilidad.toml"
    ruta.write_text("id = [", encoding="utf-8")
    with pytest.raises(ErrorCatalogoHabilidades, match="TOML"):
        cargar_metadatos_habilidad(ruta)
```

- [ ] **Step 2: Ejecutar RED**

Run: `uv run --no-sync pytest tests/unidad/test_catalogo_habilidades.py tests/contratos/test_esquema_habilidades.py tests/contratos/test_contenido_habilidades.py tests/contratos/test_habilidades_especializadas.py -q`

Expected: FAIL por modulos y errores ausentes.

- [ ] **Step 3: Implementar modelos y validacion estricta**

`validar_id_habilidad()` aplica sobre `validar_nombre_habilidad()` de 03a la
expresion canonica adicional `^[a-z0-9]+(?:-[a-z0-9]+)*$`, maximo 64 caracteres
y rechazo de dispositivos Windows. Añadir solo `ErrorCatalogoHabilidades`,
`ErrorResolucionHabilidades` y `ErrorIntegridadHabilidad` con codigos estables;
`ErrorConfiguracionHabilidades` y `ErrorEntradaInsegura` se consumen sin cambiar
sus codigos.

El loader exige todas las claves, `version_esquema == 1`, version SemVer validada
por una expresion local documentada, listas sin duplicados,
dependencias/conflictos disjuntos, permisos conocidos y al menos una fuente
versionada. Nunca captura `TOMLDecodeError` para devolver vacio.

- [ ] **Step 4: Migrar y completar las fuentes propias antes de resolver perfiles**

Mover con Git todo el inventario historico desde
`tramalia/templates/project/.tramalia/habilidades/` a
`tramalia/catalogo/habilidades_propias/`, usando los IDs espanoles ASCII
canonicos registrados en `aliases_habilidades.toml` durante este mismo Step. Crear alli tambien
`17-resiliencia-api`, `18-seguridad-habilidades-mcp` y
`19-experiencia-accesibilidad`. Cada directorio queda completo desde este Task:
metadata valida y las secciones `Objetivo`, `Cuando aplica`, `Cuando no aplica`,
`Precondiciones`, `Procedimiento`, `Puertas de calidad`, `Evidencia esperada`,
`Excepciones` y `Fuentes`. Las pruebas descubren el catalogo, verifican todos los
aliases del inventario y los tres IDs especializados por nombre; nunca usan una
asercion de cantidad.

Los IDs canonicos del inventario historico son
`01-gobierno-especificacion`, `02-memoria-federada-agentes`,
`03-ahorro-contexto-tokens`, `04-ingenieria-minimalista`,
`05-revision-calidad-codigo`, `06-seguridad-aplicacion`,
`07-ingenieria-bases-datos`, `08-ejecucion-segura-herramientas`,
`09-observabilidad-primero`, `10-evidencia-traspaso`,
`11-modernizacion-legado`, `12-revision-multiagente`,
`13-documentacion-traspaso`, `14-despliegue-lanzamiento`,
`15-gobierno-analitica` y `16-modelado-amenazas`. La lista es contenido
versionado que debe migrarse, no una asercion sobre la cantidad futura del
catalogo.

- [ ] **Step 5: Migrar el catalogo externo comentado a datos estructurados**

`habilidades_externas.toml` contiene todas las sugerencias externas vigentes
derivadas del inventario, con `id`, `fuente`, `referencia`, `licencia`, `riesgo`,
`permisos` y `estado_revision`; ninguna queda activa por estar en el catalogo y
ningun test fija su cantidad.

- [ ] **Step 6: Ejecutar GREEN y regresiones**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_catalogo_habilidades.py tests/contratos/test_esquema_habilidades.py tests/contratos/test_contenido_habilidades.py tests/contratos/test_habilidades_especializadas.py -q
uv run --no-sync pytest tests/integracion/test_habilidades_git.py tests/test_tools_and_skills.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add tramalia/core/modelos_habilidades.py tramalia/core/catalogo_habilidades.py tramalia/core/errores.py tramalia/catalogo tramalia/templates/project/.tramalia/habilidades tests
git commit -m "feat: crear catalogo canonico completo de habilidades"
```

### Task 2: Configuracion explicita y migracion del proyecto

**Files:**
- Create: `tramalia/core/configuracion_habilidades.py`
- Modify: `tramalia/templates/project/.tramalia/habilidades.toml`
- Modify: `tramalia/catalogo/aliases_habilidades.toml`
- Modify: `tramalia/core/habilidades.py`
- Create: `tests/unidad/test_configuracion_habilidades.py`
- Create: `tests/integracion/test_migracion_habilidades.py`

**Interfaces:**
- Produces: `cargar_configuracion_habilidades()`, `migrar_configuracion_habilidades()`, `publicar_configuracion_habilidades()`, `cargar_bloqueos_habilidades()`, `migrar_bloqueos_habilidades()` y serializadores TOML/JSON deterministas.
- Consumes: modelos y errores de Task 1.

- [ ] **Step 1: Escribir pruebas rojas de intencion explicita**

Definir en `tests/unidad/test_configuracion_habilidades.py` este auxiliar local;
no forma parte de la API de produccion:

`configuracion_completa_con_fuente_y_excepcion()` y
`escribir_lock_heredado_incompleto()` son tambien helpers locales que construyen
exclusivamente los modelos/bytes declarados en la prueba; no replican parsing,
serializacion ni migracion de produccion.

```python
def escribir_configuracion(raiz: Path, contenido: str) -> Path:
    ruta = raiz / ".tramalia" / "habilidades.toml"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(textwrap.dedent(contenido).lstrip(), encoding="utf-8")
    return ruta
```

```python
def test_configuracion_distingue_perfil_y_seleccion(tmp_path: Path) -> None:
    escribir_configuracion(tmp_path, """
version_esquema = 1
perfiles = ["base", "api"]

[[seleccion]]
id = "17-resiliencia-api"
estado = "activa"
motivo = "API publica"
""")
    configuracion = cargar_configuracion_habilidades(tmp_path)
    assert configuracion.perfiles == ("base", "api")
    assert configuracion.selecciones[0].activacion is ValorActivacionHabilidad.ACTIVA


def test_configuracion_invalida_falla_sin_reescribir(tmp_path: Path) -> None:
    ruta = escribir_configuracion(tmp_path, "version_esquema = [")
    antes = ruta.read_bytes()
    with pytest.raises(ErrorConfiguracionHabilidades):
        cargar_configuracion_habilidades(tmp_path)
    assert ruta.read_bytes() == antes


def test_round_trip_conserva_fuente_personalizada_y_excepcion(proyecto: Path) -> None:
    original = configuracion_completa_con_fuente_y_excepcion()
    publicar_configuracion_habilidades(proyecto, original)
    assert cargar_configuracion_habilidades(proyecto) == original


def test_lock_heredado_incompleto_falla_sin_reescribir(proyecto: Path) -> None:
    ruta = escribir_lock_heredado_incompleto(proyecto)
    antes = ruta.read_bytes()
    with pytest.raises(ErrorConfiguracionHabilidades):
        migrar_bloqueos_habilidades(proyecto)
    assert ruta.read_bytes() == antes
```

- [ ] **Step 2: Ejecutar RED**

Run: `uv run --no-sync pytest tests/unidad/test_configuracion_habilidades.py tests/integracion/test_migracion_habilidades.py -q`

Expected: FAIL por API ausente.

- [ ] **Step 3: Implementar esquema y reemplazo durable por archivo**

El template inicial usa:

```toml
version_esquema = 1
perfiles = ["base"]

# Las selecciones explicitas tienen precedencia sobre recomendaciones.
# [[seleccion]]
# id = "17-resiliencia-api"
# estado = "activa"
# motivo = "El proyecto publica una API HTTP"
```

Los estados permitidos son `activa` e `inactiva`; motivo no vacio; excepcion completa si se incluye. Implementar un serializador TOML determinista propio, limitado al esquema y probado con comillas, barras, saltos, Unicode y round-trip; no añadir una dependencia. La publicacion usa temporal hermano, `fsync` del archivo y directorio cuando la plataforma lo permite y `os.replace`.

- [ ] **Step 4: Migrar el formato heredado sin perder aliases**

La migracion lee bloques activos heredados, traduce `name/source/ref` y
`nombre/fuente/referencia`, conserva fuentes personalizadas y registra todos los
aliases descubiertos en el inventario historico. Migra tambien el lock al esquema
1 con fuente, referencia, SHA, hash y licencia; si un dato no puede derivarse de
la copia verificada y el catalogo, bloquea sin reescribir. Es idempotente y nunca
elimina un directorio activo.

- [ ] **Step 5: Ejecutar GREEN y compatibilidad**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_configuracion_habilidades.py tests/integracion/test_migracion_habilidades.py -q
uv run --no-sync pytest tests/test_v019.py tests/test_v021.py tests/test_v031.py -q
```

Expected: PASS; las fachadas inglesas siguen funcionando.

- [ ] **Step 6: Commit**

```bash
git add tramalia/core/configuracion_habilidades.py tramalia/core/habilidades.py tramalia/catalogo/aliases_habilidades.toml tramalia/templates/project/.tramalia/habilidades.toml tests
git commit -m "feat: declarar intencion de habilidades por proyecto"
```

### Task 3: Perfiles y resolvedor determinista

**Files:**
- Create: `tramalia/core/perfiles_habilidades.py`
- Create: `tramalia/core/resolucion_habilidades.py`
- Create: `tramalia/catalogo/perfiles_habilidades.toml`
- Create: `tests/unidad/test_perfiles_habilidades.py`
- Create: `tests/unidad/test_resolucion_habilidades.py`

**Interfaces:**
- Produces: `cargar_perfiles_habilidades()` y `resolver_habilidades()`.
- Consumes: catalogo canonico completo de Task 1, configuracion, bloqueos, tecnologias, capacidades, tipos de proyecto, claves de herramientas presentes y reloj UTC inyectado.

- [ ] **Step 1: Escribir RED para precedencia, dependencias y ciclos**

Las pruebas construyen `MetadatosHabilidad`, `PerfilHabilidades` y
`ConfiguracionHabilidadesProyecto` mediante factories locales tipadas. Los
auxiliares `resolver_ejemplo`, `resolver_catalogo`, `catalogo_con_ciclo` y
`por_id` solo ensamblan esos objetos y llaman a `resolver_habilidades`; no
replican ninguna regla del resolvedor. De este modo, cada asercion inferior
ejercita la API publica real y no un doble con logica propia.

```python
def test_seleccion_explicita_supera_recomendacion_de_perfil() -> None:
    plan = resolver_ejemplo(
        perfiles=("api",),
        selecciones=(SeleccionHabilidad(
            "17-resiliencia-api", ValorActivacionHabilidad.INACTIVA, "no aplica"
        ),),
    )
    decision = por_id(plan, "17-resiliencia-api")
    assert decision.activacion is ValorActivacionHabilidad.INACTIVA
    assert decision.origen is ValorOrigenDecisionHabilidad.EXPLICITA


def test_habilidad_obligatoria_exige_excepcion_vigente() -> None:
    plan = resolver_ejemplo(perfiles=("alta-seguridad",), desactivar="06-seguridad-aplicacion")
    assert not plan.aplicable
    assert "excepcion" in " ".join(plan.bloqueos)


def test_ciclo_de_dependencias_bloquea_y_es_estable() -> None:
    plan = resolver_catalogo(catalogo_con_ciclo())
    assert not plan.aplicable
    assert plan.orden_activacion == ()
    assert plan.bloqueos == tuple(sorted(plan.bloqueos))


def test_permutar_entradas_conserva_decisiones_y_huella() -> None:
    planes = resolver_todas_las_permutaciones(reloj_utc=reloj_fijo)
    assert {plan.huella for plan in planes} == {planes[0].huella}


def test_excepcion_vence_segun_reloj_inyectado() -> None:
    assert resolver_con_reloj(antes_de_expirar).aplicable
    assert not resolver_con_reloj(despues_de_expirar).aplicable
```

- [ ] **Step 2: Ejecutar RED**

Run: `uv run --no-sync pytest tests/unidad/test_perfiles_habilidades.py tests/unidad/test_resolucion_habilidades.py -q`

Expected: FAIL por modulos ausentes.

- [ ] **Step 3: Implementar perfiles estructurados**

Cada perfil declara `obligatorias` y `recomendadas`. Implementar los perfiles
`base`, `api`, `frontend`, `datos`, `legado`, `release`, `agentico`, `mcp` y
`alta-seguridad` con el contenido minimo vinculante de la especificacion. Cada ID
se valida contra el catalogo, sin IDs inexistentes ni duplicados; ninguna prueba
usa `len(...)`. `alta-seguridad` no activa habilidades incompatibles con la
tecnologia, capacidad o tipo de proyecto: quedan inactivas, explicadas como no
aplicables y sin exigir excepcion.

- [ ] **Step 4: Implementar resolucion pura**

Resolver sin filesystem ni red y con `reloj_utc` inyectado. Combinar perfiles por
obligatoriedad mas fuerte, aplicar por separado la precedencia de activacion y
bloquear una activacion explicita incompatible, en conflicto, sin dependencia o
sin herramienta requerida. Ordenar activacion con topological sort estable por
ID. Reportar herramientas faltantes, conflictos simetricos, dependencias
inactivas, excepciones vencidas y perfiles desconocidos. La huella es SHA-256 de
JSON canonico con claves ordenadas, sin rutas absolutas e incluye huellas de
catalogo, perfiles, configuracion, lock, cache verificada, deteccion y
herramientas.

- [ ] **Step 5: Ejecutar GREEN incluido determinismo temporal y por permutaciones**

Run: `uv run --no-sync pytest tests/unidad/test_perfiles_habilidades.py tests/unidad/test_resolucion_habilidades.py -q`

Expected: PASS; las pruebas de permutacion y reloj ya escritas en RED conservan huella/decisiones y bloquean excepciones vencidas.

- [ ] **Step 6: Commit**

```bash
git add tramalia/core/perfiles_habilidades.py tramalia/core/resolucion_habilidades.py tramalia/catalogo/perfiles_habilidades.toml tests/unidad
git commit -m "feat: resolver perfiles de habilidades"
```

### Task 4: Materializacion transaccional, serializada y recuperable

**Files:**
- Create: `tramalia/core/materializacion_habilidades.py`
- Modify: `tramalia/core/habilidades.py`
- Modify: `tramalia/core/scaffold.py`
- Modify: `.gitignore`
- Create: `tests/unidad/test_plan_materializacion_habilidades.py`
- Create: `tests/integracion/test_materializacion_habilidades.py`

**Interfaces:**
- Produces: `planificar_materializacion()` y `aplicar_materializacion()`.
- Consumes: `PlanResolucionHabilidades`, fuentes canonicas, configuracion, lock, cache verificada y validadores/cuarentena de 03a.

- [ ] **Step 1: Escribir RED de aislamiento y preservacion local**

El fixture `proyecto` crea un scaffold minimo gobernado en `tmp_path`. Los
auxiliares locales `activar`, `aplicar`, `plan_desactivado` y `cache_de` se
definen en el test y delegan exclusivamente en `resolver_habilidades`,
`planificar_materializacion()` y `aplicar_materializacion()`; no escriben
directamente la proyeccion que se esta probando. `huella_estado_gobernado`,
`inyectar_fallo_despues_de_mover_arbol_anterior`,
`recuperar_transaccion_habilidades` y `mantener_lock_habilidades` son fixtures o
puntos de inyeccion locales sobre las APIs publicas; ninguno implementa rollback
o locking alternativo.

```python
def test_desactivar_retira_solo_la_proyeccion_activa(proyecto: Path) -> None:
    activar(proyecto, "17-resiliencia-api")
    aplicar(proyecto, plan_desactivado("17-resiliencia-api"))
    assert not (proyecto / ".tramalia/habilidades/17-resiliencia-api").exists()
    assert cache_de(proyecto, "17-resiliencia-api").exists()


def test_desactivar_bloquea_si_el_usuario_modifico_la_habilidad(proyecto: Path) -> None:
    ruta = activar(proyecto, "17-resiliencia-api") / "SKILL.md"
    ruta.write_text(ruta.read_text(encoding="utf-8") + "\nCambio local\n", encoding="utf-8")
    with pytest.raises(ErrorIntegridadHabilidad, match="cambio local"):
        aplicar(proyecto, plan_desactivado("17-resiliencia-api"))
    assert ruta.exists()


def test_fallo_en_publicacion_se_recupera_desde_journal(proyecto: Path) -> None:
    antes = huella_estado_gobernado(proyecto)
    inyectar_fallo_despues_de_mover_arbol_anterior(proyecto)
    with pytest.raises(ErrorIntegridadHabilidad):
        aplicar(proyecto, plan_con_cambio())
    recuperar_transaccion_habilidades(proyecto)
    assert huella_estado_gobernado(proyecto) == antes


def test_lock_interproceso_rechaza_segunda_mutacion(proyecto: Path) -> None:
    with mantener_lock_habilidades(proyecto):
        with pytest.raises(ErrorIntegridadHabilidad, match="operacion en curso"):
            aplicar(proyecto, plan_con_cambio())
```

- [ ] **Step 2: Ejecutar RED**

Run: `uv run --no-sync pytest tests/unidad/test_plan_materializacion_habilidades.py tests/integracion/test_materializacion_habilidades.py -q`

Expected: FAIL por materializador ausente.

- [ ] **Step 3: Implementar plan puro y rutas confinadas**

El plan enumera crear, actualizar, conservar y retirar, con hash anterior/objetivo. Toda ruta se resuelve mediante `resolver_ruta_confinada()` de 03a y se verifica bajo `.tramalia/habilidades`; se rechazan symlinks, junctions/reparse points, dispositivos Windows, componentes no portables y colisiones Unicode/case-insensitive. El hash canonico recorre rutas POSIX ordenadas, usa bytes sin conversion de fin de linea, fija `core.autocrlf=false` y documenta si el bit ejecutable participa.

- [ ] **Step 4: Implementar transaccion serializada y recuperable**

Adquirir un lock interproceso antes de revalidar las huellas de todos los insumos.
Preparar el arbol completo en `.tramalia/.temporales/habilidades-<uuid>` dentro
del mismo volumen, validar hashes y escribir un journal durable con fases
`preparada`, `anterior_resguardado`, `proyeccion_publicada`,
`configuracion_publicada` y `lock_publicado`. Publicar mediante renames
confinados; ante fallo o al abrir un proyecto con journal pendiente, restaurar o
completar de forma idempotente. Nunca dejar lock/config nuevos con proyeccion
anterior. La garantia es transaccional y recuperable, no atomicidad global ante
crash. Cache externa vive bajo `.tramalia/cache/habilidades/` y se ignora en Git.

- [ ] **Step 5: Actualizar scaffold y AGENTS**

Los proyectos nuevos parten con `.tramalia/habilidades/` vacio y materializan el
perfil `base` desde las fuentes canonicas de Task 1. `AGENTS.md` apunta
exclusivamente a `.tramalia/habilidades/` y explica que catalogo/cache no son
instrucciones activas. Upgrade descubre todos los aliases historicos: una copia
identica se renombra a su ID canonico dentro de la transaccion; una copia
modificada bloquea con instrucciones para conservarla o moverla fuera de la ruta
activa. Nunca quedan simultaneamente el nombre historico y el canonico como dos
instrucciones activas.

- [ ] **Step 6: Verificar GREEN, fallo inyectado y plataformas**

Run: `uv run --no-sync pytest tests/unidad/test_plan_materializacion_habilidades.py tests/integracion/test_materializacion_habilidades.py tests/test_scaffold.py -q`

Expected: PASS; fallo inyectado, reapertura y dos procesos concurrentes convergen exactamente al estado anterior o al nuevo estado completo.

- [ ] **Step 7: Commit**

```bash
git add tramalia/core/materializacion_habilidades.py tramalia/core/habilidades.py tramalia/core/scaffold.py tramalia/templates .gitignore tests
git commit -m "feat: materializar habilidades con recuperacion transaccional"
```

### Task 5: Procedencia, cuarentena y auditoria Agentic/MCP

**Files:**
- Create: `tramalia/core/auditoria_habilidades.py`
- Modify: `tramalia/core/habilidades.py`
- Modify: `tramalia/core/modelos_habilidades.py`
- Create: `tests/unidad/test_auditoria_habilidades.py`
- Create: `tests/integracion/test_cuarentena_habilidades.py`
- Create: `tests/recursos/habilidades/` fixtures seguros e inseguros

**Interfaces:**
- Produces: `auditar_habilidad()`, `auditar_habilidades()` y `preparar_fuente_externa()`.
- Consumes: proceso Git, validadores, cuarentena, limites 2.000/4 MiB/64 MiB y lock esquema 1 entregados por 03a/Tasks 1-2.

- [ ] **Step 1: Escribir RED de fuentes y archivos hostiles**

Definir aqui tambien, antes de la implementacion, pruebas con reloj y jitter
inyectados para timeout, cache de 15 minutos, concurrencia maxima, `Retry-After`,
limite de intentos y ausencia de reintento durante publicacion local. Los helpers
`crear_fuente_hostil_local`, reloj y adaptadores son locales: solo preparan
entradas y delegan en APIs de produccion.

```python
@pytest.mark.parametrize("fuente", (
    "git+http://ejemplo.invalid/habilidad", "file:///tmp/habilidad", "git+ssh://host/repo",
))
def test_fuente_remota_no_aprobada_se_rechaza(fuente: str) -> None:
    with pytest.raises(ErrorEntradaInsegura):
        validar_fuente_git(fuente)


def test_cuarentena_rechaza_symlink_submodulo_y_archivo_desmesurado(tmp_path: Path) -> None:
    for fixture in ("symlink", "submodulo", "desmesurado"):
        fuente = crear_fuente_hostil_local(tmp_path, fixture)
        with pytest.raises(ErrorIntegridadHabilidad):
            preparar_fuente_externa(fuente, permitir_fuente_local_de_prueba=True)
```

- [ ] **Step 2: Ejecutar RED**

Run: `uv run --no-sync pytest tests/unidad/test_auditoria_habilidades.py tests/integracion/test_cuarentena_habilidades.py -q`

Expected: FAIL por auditor ausente.

- [ ] **Step 3: Integrar preparacion de fuentes con la cuarentena de 03a**

Aceptar remoto `git+https://` y fixtures locales solo mediante parametro de test/integracion explicito. `preparar_fuente_externa()` orquesta `validar_fuente_git()`, la cuarentena y `validar_arbol_habilidad()` de 03a; no implementa otro clonador. Resolver SHA completo; rechazar symlinks, reparse points, `.gitmodules`, mas de 2.000 archivos, archivo individual >4 MiB o total >64 MiB. Exportar contenido sin `.git`, con `core.autocrlf=false`, y calcular el hash canonico definido en Task 4.

- [ ] **Step 4: Implementar hallazgos versionados**

```python
class ValorSeveridadHallazgoHabilidad(StrEnum):
    INFORMATIVA = "informativa"
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"

@dataclass(frozen=True, slots=True)
class HallazgoAuditoriaHabilidad:
    regla: str
    severidad: ValorSeveridadHallazgoHabilidad
    mensaje: str
    ruta_relativa: str | None
    referencia: str

@dataclass(frozen=True, slots=True)
class ResultadoAuditoriaHabilidad:
    id_habilidad: str
    version_reglas: str
    hallazgos: tuple[HallazgoAuditoriaHabilidad, ...]

    @property
    def aprobada(self) -> bool: ...
```

Reglas iniciales cubren metadata/permiso desalineado, ausencia de licencia, origen mutable sin lock, instrucciones que intentan ignorar gobierno, ejecucion de shell/red no declarada, lectura de secretos no declarada y configuracion MCP peligrosa. Cada hallazgo referencia AST/MCP cuando aplica, pero el resultado dice expresamente que no certifica cumplimiento.

- [ ] **Step 5: Controlar consultas remotas y rate limits**

`consultar_habilidades(consultar_remoto=True)` pasa a un servicio con timeout, concurrencia maxima 4, cache local de 15 minutos, reloj inyectado y refresco explicito. Respeta `Retry-After` si el adaptador HTTP lo expone; Git conserva backoff acotado con jitter inyectable y maximo tres intentos para consultas idempotentes. Nunca reintenta una publicacion local.

- [ ] **Step 6: Ejecutar GREEN y escaneos del Plan 03a**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_auditoria_habilidades.py tests/integracion/test_cuarentena_habilidades.py -q
uv run --no-sync semgrep scan --config configuracion/semgrep/seguridad-python.yml --error --metrics=off --disable-version-check tramalia/core
```

Expected: PASS y cero hallazgos Semgrep no justificados.

- [ ] **Step 7: Commit**

```bash
git add tramalia/core/auditoria_habilidades.py tramalia/core/habilidades.py tramalia/core/modelos_habilidades.py tests
git commit -m "feat: auditar procedencia de habilidades"
```

### Task 6: Servicio de operaciones y compatibilidad de superficies

**Files:**
- Create: `tramalia/core/servicio_habilidades.py`
- Modify: `tramalia/core/habilidades.py`
- Modify: `tramalia/core/tablero.py`
- Modify: `tramalia/mcp_server.py`
- Create: `tests/unidad/test_servicio_habilidades.py`
- Create: `tests/contratos/test_superficies_habilidades.py`
- Create: `tests/integracion/test_mcp_habilidades.py`

**Interfaces:**
- Produces: `ServicioHabilidades` con las firmas exactas declaradas en Interfaces compartidas y operaciones observables.
- Consumes: catalogo, configuracion, resolvedor, materializador y auditor.

- [ ] **Step 1: Escribir RED de paridad y ausencia de efectos en consulta**

`huella_arbol`, `fallar_si_se_llama`, `invocar_tablero`, `invocar_mcp_listar` y
`servicio_espia` son helpers/fixtures locales sin logica de dominio. Añadir en
este Step contratos por `inspect.signature` para todas las firmas compartidas y
pruebas de huella obsoleta, cancelacion antes de `PUBLICANDO` y secuencia de
eventos; no diferirlas hasta despues de implementar.

```python
def test_planificar_y_explicar_no_escriben_ni_consultan_red(proyecto: Path) -> None:
    antes = huella_arbol(proyecto)
    servicio = ServicioHabilidades(
        proyecto, reloj_utc=reloj_fijo, consultar_remoto=fallar_si_se_llama
    )
    plan = servicio.planificar()
    detalle = servicio.explicar(plan.resolucion.decisiones[0].id)
    assert detalle.metadatos.id
    assert huella_arbol(proyecto) == antes


def test_tablero_y_mcp_delegan_en_el_mismo_servicio(servicio_espia) -> None:
    invocar_tablero(servicio_espia)
    invocar_mcp_listar(servicio_espia)
    assert servicio_espia.llamadas == ["listar", "listar"]
```

- [ ] **Step 2: Ejecutar RED**

Run: `uv run --no-sync pytest tests/unidad/test_servicio_habilidades.py tests/contratos/test_superficies_habilidades.py tests/integracion/test_mcp_habilidades.py -q`

Expected: FAIL por servicio ausente.

- [ ] **Step 3: Implementar servicio y operaciones**

Implementar sin cambiar las firmas de Interfaces compartidas. `listar`,
`explicar`, `planificar` y `auditar` devuelven modelos y no escriben ni usan red.
Las mutaciones reciben confirmacion, recalculan dentro del lock la misma
`SolicitudCambioHabilidades`, revalidan todas las huellas, respetan cancelacion
hasta `PUBLICANDO`, emiten `EventoOperacionHabilidades` y devuelven
`ResultadoCambioHabilidades`. No contienen renderizado.

- [ ] **Step 4: Adaptar fachadas existentes**

`leer_habilidades`, `catalogo_habilidades`, `fijar_habilitada`,
`agregar_habilidad`, `sincronizar_habilidades` y `consultar_habilidades`
conservan firmas/retornos publicos de la BETA y delegan. `agregar_habilidad`
publica una `FuentePersonalizadaHabilidad`; `sincronizar_habilidades` delega en
rehidratar/actualizar sin crear un segundo motor. Deprecaciones emiten una
advertencia estable solo al invocar, nunca durante imports.

- [ ] **Step 5: Restringir MCP**

MCP expone solo consultas por defecto. Mutaciones exigen raiz gobernada y parametro `confirmacion` igual a la huella del plan vigente; se rechaza una huella obsoleta. Limitar salida, sanear rutas/controles y no incluir contenido completo de SKILL.md.

- [ ] **Step 6: Ejecutar GREEN**

Run: `uv run --no-sync pytest tests/unidad/test_servicio_habilidades.py tests/contratos/test_superficies_habilidades.py tests/integracion/test_mcp_habilidades.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add tramalia/core/servicio_habilidades.py tramalia/core/habilidades.py tramalia/core/tablero.py tramalia/mcp_server.py tests
git commit -m "feat: compartir operaciones de habilidades"
```

### Task 7: Endurecer el contrato editorial de fuentes propias

**Files:**
- Modify: `tramalia/catalogo/habilidades_propias/*/SKILL.md`
- Modify: `tramalia/catalogo/habilidades_propias/*/habilidad.toml`
- Modify: `tramalia/catalogo/aliases_habilidades.toml`
- Modify: referencias en templates y docs
- Create: `tests/contratos/test_contenido_habilidades.py`

**Interfaces:**
- Consumes: loader de catalogo y aliases.
- Produces: fuentes canonicas espanolas, versionadas y uniformes ya creadas en Task 1.

- [ ] **Step 1: Escribir RED del contrato editorial sin conteo fijo**

Extender el contrato basico ya aprobado en Task 1. Para cada habilidad exigir que
cada puerta identifique herramienta o procedimiento manual, criterio de exito y
evidencia; que cada excepcion enlace su politica tipada; que las fuentes tengan
version/fecha; y que dependencias, permisos y riesgos mencionados en `SKILL.md`
coincidan con `habilidad.toml`. Ninguna ruta canonica usa nombres ingleses
historicos y todos los aliases resuelven a un ID vigente.

- [ ] **Step 2: Ejecutar RED**

Run: `uv run --no-sync pytest tests/contratos/test_contenido_habilidades.py -q`

Expected: FAIL por puertas/evidencias y referencias cruzadas todavia incompletas, no por fuentes ausentes.

- [ ] **Step 3: Verificar aliases y ausencia de renombrado tardio**

Descubrir el inventario de fuentes canonicas creado en Task 1 y exigir que cada
ruta historica tenga un alias unico hacia un ID vigente. Este Task no mueve
directorios ni crea metadata: un renombrado tardio invalidaria perfiles, hashes y
planes ya probados.

- [ ] **Step 4: Ampliar contenido metodologico**

Cada habilidad se vuelve accionable y basada en riesgo. La base incluye especificacion, ADR, TDD, cortes verticales, revision, migracion/rollback, observabilidad, release y handoff. El texto no exige una cifra de tests y distingue habilidad, herramienta, puerta y evidencia.

- [ ] **Step 5: Ejecutar GREEN y scaffold**

Run: `uv run --no-sync pytest tests/contratos/test_contenido_habilidades.py tests/test_scaffold.py tests/test_convencion_completa.py -q`

Expected: PASS sin aserciones de cantidad.

- [ ] **Step 6: Commit**

```bash
git add tramalia/templates tramalia/catalogo docs tests
git commit -m "docs: gobernar habilidades propias en espanol"
```

### Task 8: Ampliar resiliencia API, seguridad Agentic/MCP y experiencia accesible

**Files:**
- Modify: `tramalia/catalogo/habilidades_propias/17-resiliencia-api/`
- Modify: `tramalia/catalogo/habilidades_propias/18-seguridad-habilidades-mcp/`
- Modify: `tramalia/catalogo/habilidades_propias/19-experiencia-accesibilidad/`
- Modify: `tramalia/catalogo/perfiles_habilidades.toml`
- Modify: `tests/contratos/test_habilidades_especializadas.py`

**Interfaces:**
- Consumes: contrato editorial.
- Produces: tres capacidades nuevas activadas por perfiles aplicables.

- [ ] **Step 1: Escribir RED por controles concretos**

El test de resiliencia exige timeout, concurrencia acotada, idempotencia, `Retry-After`, backoff con jitter, presupuesto, deduplicacion, cache, circuit breaker, limites y escenarios 429/503. Seguridad exige OWASP 2025, API 2023, ASVS 5.0.0, Agentic Skills y MCP con version/madurez; experiencia exige WCAG 2.2 AA, teclado, foco, contraste, reflow, zoom, movimiento reducido y equivalentes Pilot.

- [ ] **Step 2: Ejecutar RED**

Run: `uv run --no-sync pytest tests/contratos/test_habilidades_especializadas.py -q`

Expected: FAIL por controles metodologicos todavia incompletos, no por fuentes ausentes.

- [ ] **Step 3: Ampliar metadata y procedimientos completos**

Cada fuente incluye URL oficial, version y fecha de revision. Agentic Skills/MCP se marcan como referencias en evolucion; el texto prohíbe afirmar certificacion. Las habilidades incluyen puertas ejecutables sugeridas y evidencia minima.

- [ ] **Step 4: Verificar la integracion temprana de perfiles**

Comprobar que el contenido creado en Task 3 conserva estas relaciones al ampliar
las fuentes: `api` recomienda 17 y obliga 06; `frontend` recomienda 19;
`agentico` y `mcp` obligan 18 y recomiendan 16; `alta-seguridad` obliga 06, 16 y
18 cuando aplican. Resolver conserva explicaciones de no aplicabilidad. Este Step
no introduce IDs tardios ni valida cantidades.

- [ ] **Step 5: Ejecutar GREEN**

Run: `uv run --no-sync pytest tests/contratos/test_habilidades_especializadas.py tests/unidad/test_perfiles_habilidades.py tests/unidad/test_resolucion_habilidades.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tramalia/catalogo/habilidades_propias tramalia/catalogo/perfiles_habilidades.toml tests
git commit -m "feat: ampliar habilidades de api seguridad y experiencia"
```

### Task 9: CLI provisional, JSON y documentacion de migracion

**Files:**
- Modify: `tramalia/__main__.py`
- Modify: `tramalia/cli/comandos.py`
- Modify: `tramalia/i18n/es.json`
- Modify: `tramalia/i18n/en.json`
- Modify: `docs/skills-guia.md`, `docs/skills-guia.en.md`
- Modify: `docs/comandos.md`, `docs/comandos.en.md`
- Create: `docs/perfiles-habilidades.md`, `docs/perfiles-habilidades.en.md`
- Create: `tests/contratos/test_cli_habilidades.py`
- Modify: `tests/contratos/test_documentacion.py`

**Interfaces:**
- Consumes: `ServicioHabilidades`.
- Produces: comandos usables antes del rediseño visual 03b.

- [ ] **Step 1: Escribir RED de aliases y modelos compartidos**

Probar `habilidades listar/planificar/explicar/activar/desactivar/auditar`,
`habilidades perfil aplicar` y todos los contratos legacy: `skills` sin accion,
`skills sync`, `skills update`, `skills outdated`, `skills list`, `skills add`,
`skills enable` y `skills disable`. Sus adaptadores delegan respectivamente en
listar, planificar, fuentes personalizadas, rehidratar o actualizar segun la
semantica historica documentada; ninguna ruta conserva un motor propio. Probar
codigos de salida y JSON estable con `ResultadoCambioHabilidades.aplicada`.

- [ ] **Step 2: Ejecutar RED**

Run: `uv run --no-sync pytest tests/contratos/test_cli_habilidades.py -q`

Expected: FAIL por parser/comandos ausentes.

- [ ] **Step 3: Implementar adaptador CLI delgado**

La CLI convierte argumentos a operaciones y renderiza modelos. Activar/desactivar/aplicar perfil primero imprime el plan; en modo no interactivo exige `--confirmar-huella`. No instala ni consulta red salvo las invocaciones explicitas `actualizar --refrescar-remoto`, `skills update`, `skills outdated` y la rehidratacion legacy solicitada por `skills`/`skills sync`.

- [ ] **Step 4: Documentar perfiles, estados y migracion**

Eliminar conteos manuales 13/16. Explicar rutas activas, cache, lock, aliases, excepciones y comandos ES/EN. Definir con ejemplos habilidad, herramienta, puerta y evidencia.

- [ ] **Step 5: Ejecutar GREEN y MkDocs**

Run:

```powershell
uv run --no-sync pytest tests/contratos/test_cli_habilidades.py tests/contratos/test_documentacion.py -q
uv run --no-sync mkdocs build --strict
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tramalia/__main__.py tramalia/cli tramalia/i18n docs tests
git commit -m "feat: exponer perfiles y planes de habilidades"
```

### Task 10: Verificacion integral y contrato para Plan 03b

**Files:**
- Modify: `docs/superpowers/plans/2026-07-14-03b-rediseno-cli-tui-interactiva.md` si una interfaz real difiere del contrato planificado
- Create: `tests/contratos/test_entrega_03c.py`

- [ ] **Step 1: Crear contrato de entrega**

Exigir modulos, modelos, los IDs de perfil declarados en la especificacion sin
comprobar su cantidad, firmas exactas del servicio, schemas JSON, aliases,
catalogo sin comentarios funcionales, ausencia de conteos fijos, docstrings
publicos ingleses estilo Google y pantalla 03b capaz de importar solo interfaces
publicas.

- [ ] **Step 2: Ejecutar todas las verificaciones de 03c**

```powershell
uv run --no-sync pytest tests/unidad -q
uv run --no-sync pytest tests/integracion -q
uv run --no-sync pytest tests/contratos -q -k habilidades
uv run --no-sync pytest tests/contratos/test_entrega_03c.py -q
uv run --no-sync ruff check tramalia tests
uv run --no-sync ruff format --check tramalia tests
uv run --no-sync mkdocs build --strict
$nombre_gitleaks = if ($IsWindows) { "gitleaks.exe" } else { "gitleaks" }
$ruta_gitleaks = Join-Path "$HOME/.local/bin" $nombre_gitleaks
& $ruta_gitleaks git --redact --no-banner --config .gitleaks.toml --exit-code 1
& $ruta_gitleaks dir . --redact --no-banner --config .gitleaks.toml --max-target-megabytes 10 --exit-code 1
git diff --check
```

Expected: todos los comandos terminan con codigo 0.

- [ ] **Step 3: Ejecutar suite completa**

Run: `uv run --no-sync pytest -q`

Expected: cero fallos; la cantidad resultante se registra, no se fija.

- [ ] **Step 4: Commit de cierre del plan**

```bash
git add docs/superpowers/plans tests/contratos/test_entrega_03c.py
git commit -m "test: cerrar contrato de habilidades gobernadas"
```

## Criterios finales

- [ ] Catalogo y configuracion invalidos fallan de forma tipada.
- [ ] Perfiles y resolucion son deterministas y explicables.
- [ ] Dependencias se ordenan; ciclos y conflictos bloquean.
- [ ] Habilidades obligatorias requieren excepcion para desactivarse.
- [ ] Solo habilidades activas aparecen en la ruta leida por agentes.
- [ ] Desactivar no borra cambios locales ni cache.
- [ ] Fuentes externas usan HTTPS, SHA completo, hash, licencia y cuarentena.
- [ ] Consultas remotas estan acotadas y no ocurren por inferencia.
- [ ] CLI, tablero y MCP delegan en un servicio compartido.
- [ ] Todos los IDs del inventario historico migran y no quedan como nombres canonicos.
- [ ] Resiliencia API, seguridad Agentic/MCP y UX accesible tienen contenido verificable.
- [ ] No existen badges, docs o tests que fijen una cantidad de habilidades o pruebas.

Plan completo guardado en `docs/superpowers/plans/2026-07-16-03c-habilidades-gobernadas.md`.
