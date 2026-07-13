# Integraciones, superficies compartidas y TUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hacer que integraciones, CLI, TUI y MCP comuniquen fallos honestos y compartan las operaciones de gobierno, con skills Git reproducibles y una TUI que mantenga toda sonda o proceso externo fuera del event loop.

**Architecture:** `tramalia.core.integraciones` será el registro de herramientas y el contrato de selección por capacidad, mientras `tramalia.core.procesos` normalizará código de salida, timeout y cancelación. `tramalia.core.habilidades` resolverá referencias Git y locks por SHA; CLI, MCP y `ServicioTablero` invocarán exclusivamente las operaciones del plan 02. `tramalia.interfaz_terminal` quedará como capa Textual inyectable que representa una `InstantaneaTablero` inmutable y despacha trabajo bloqueante mediante workers con hilo.

**Tech Stack:** Python 3.11+, `dataclasses`, `typing`, `subprocess`, Git CLI, `argparse`, Textual 1.x, FastMCP/MCP 1.2+, pytest 8, GitHub Actions.

## Global Constraints

- Python 3.11 será la versión mínima de la BETA.
- La compatibilidad objetivo será Python 3.11, 3.12, 3.13 y 3.14.
- Se aplicará una estabilización estructural incremental; no una sucesión de parches aislados ni una reescritura total.
- CLI, TUI y MCP serán fachadas delgadas sobre una única capa de operaciones.
- Las integraciones opcionales no serán necesarias para usar el núcleo repo-first.
- Los comentarios internos se escribirán en español.
- Los docstrings de la API pública se escribirán en inglés y con estilo Google.
- Los nombres propios creados o renombrados en archivos, módulos, clases, funciones, métodos, variables, auxiliares de pytest y marcadores se escribirán en español ASCII. La letra `ñ` se representará como `n`; las interfaces públicas heredadas que se conserven se documentan expresamente como excepción de compatibilidad.
- Se conservarán en inglés únicamente nombres impuestos por Python, GitHub, PyPI, MkDocs, MCP, formatos externos o comandos públicos ya establecidos.
- El núcleo debe seguir funcionando sin Node, servicios cloud ni herramientas externas.
- Las integraciones pueden degradar una capacidad opcional, pero nunca ocultar un intento fallido.
- No se incorporará una base de datos, event sourcing ni un framework de persistencia.
- Las escrituras deben ser seguras en Windows, Linux y macOS.
- Los cambios de comportamiento se implementarán con TDD: test fallando, implementación mínima y refactor posterior.
- Las APIs públicas nuevas deben tener tipos, docstring y pruebas de contrato.
- Los comentarios deben explicar motivos, invariantes y riesgos; no repetir el código.

---

## Dependencias y contratos consumidos del plan 02

Este plan se ejecuta después de `2026-07-12-02-nucleo-puertas-evidencia.md`. No redefine ni duplica política de cierre, validación de excepciones, escritura de evidencia o lectura de bitácora. Los bloques siguientes son stubs de consumo: las implementaciones y enums exactos son los creados por el plan 02 y no se vuelven a declarar.

```python
# tramalia/core/errores.py
class ErrorTramalia(Exception):
    codigo: str
    mensaje: str
    sugerencia: str
    ruta: Path | None
    detalles: Mapping[str, object]

    def como_dict(self) -> dict[str, object]: ...

class ErrorProyectoNoGobernado(ErrorTramalia): ...       # proyecto_no_gobernado
class ErrorConfiguracionPuertas(ErrorTramalia): ...       # configuracion_puertas_invalida
class ErrorConfiguracionMetricas(ErrorTramalia): ...      # configuracion_metricas_invalida
class ErrorIdentificadorInseguro(ErrorTramalia): ...      # id_tarea_inseguro
class ErrorExcepcionInvalida(ErrorTramalia): ...          # excepcion_invalida
class ErrorPersistenciaEvidencia(ErrorTramalia): ...      # persistencia_evidencia_fallida
```

```python
# tramalia/core/modelos.py
@dataclass(frozen=True, slots=True)
class EstadoProyecto:
    estado: ValorEstadoProyecto
    raiz: Path
    problemas: tuple[str, ...] = ()
    comando_reparacion: str | None = None

    @property
    def listo(self) -> bool: ...

@dataclass(frozen=True, slots=True)
class PuertaCalidad:
    nombre: str
    comando: tuple[str, ...]
    archivo_salida: str

@dataclass(frozen=True, slots=True)
class ResultadoPuerta:
    nombre: str
    comando: tuple[str, ...]
    estado: ValorResultadoPuerta
    codigo_salida: int | None
    salida: str
    inicio_utc: datetime
    fin_utc: datetime
    duracion_segundos: float
    hash_salida: str
    archivo_salida: str

@dataclass(frozen=True, slots=True)
class EjecucionPuertas:
    estado: ValorEstadoPuertas
    descubiertas: tuple[str, ...] = ()
    ejecutadas: tuple[str, ...] = ()
    omitidas: tuple[str, ...] = ()
    fallidas: tuple[str, ...] = ()
    resultados: tuple[ResultadoPuerta, ...] = ()
    errores_validacion: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class ExcepcionFallo:
    razon: str
    riesgo_aceptado: str
    control_afectado: str
    referencia: str
    revisor: str
    expira_en: datetime | None = None
    condicion_remediacion: str | None = None

    def vigente(self, ahora: datetime) -> bool: ...

@dataclass(frozen=True, slots=True)
class EstadoIntegracion:
    estado: ValorEstadoIntegracion
    capacidad: str
    solicitado: str | None
    utilizado: str | None
    motivo: str
    impacto: str
    remediacion: str

    @property
    def exitoso(self) -> bool: ...

@dataclass(frozen=True, slots=True)
class ResultadoCierre:
    estado: ValorEstadoCierre
    id_tarea: str
    id_paquete: str | None
    ruta_paquete: Path | None
    ruta_traspaso: Path | None
    ejecucion: EjecucionPuertas
    excepciones: tuple[ExcepcionFallo, ...]
    bloqueos: tuple[str, ...]

    @property
    def aprobado(self) -> bool: ...

@dataclass(frozen=True, slots=True)
class PaqueteEvidencia:
    id_paquete: str
    ruta: Path
    metadatos: MetadatosPaqueteEvidencia

@dataclass(frozen=True, slots=True)
class EntradaBitacora:
    id_paquete: str
    ruta: Path
    estado: ValorEstadoBitacora
    id_tarea: str | None
    resultado: ValorEstadoCierre | None
    agente: str | None
    modelo: str | None
    cerrado_utc: datetime | None
    error: str | None = None
```

```python
# tramalia/core/proyecto.py
def inspeccionar_estado_proyecto(raiz: Path) -> EstadoProyecto: ...
def exigir_proyecto_gobernado(raiz: Path) -> EstadoProyecto: ...
def exigir_proyecto_actualizable(raiz: Path) -> EstadoProyecto: ...

# tramalia/core/puertas_calidad.py
def cargar_puertas(raiz: Path) -> tuple[PuertaCalidad, ...]: ...
def ejecutar_puertas(
    raiz: Path,
    puertas: Sequence[PuertaCalidad],
) -> EjecucionPuertas: ...

# tramalia/core/operaciones.py
def cerrar_proyecto(
    raiz: Path,
    id_tarea: str,
    *,
    agente: str = "",
    revisor: str = "",
    modelo: str = "",
    excepciones: Sequence[ExcepcionFallo] = (),
) -> ResultadoCierre: ...

def crear_evidencia(
    raiz: Path,
    id_tarea: str,
    *,
    agente: str = "",
    revisor: str = "",
    modelo: str = "",
) -> PaqueteEvidencia: ...

def registrar_traspaso(
    raiz: Path,
    id_tarea: str,
    *,
    agente: str = "",
    revisor: str = "",
) -> PaqueteEvidencia: ...

# tramalia/core/evidencia.py
def leer_bitacora(raiz: Path) -> list[EntradaBitacora]: ...
```

`ErrorTramalia` se captura sólo en las superficies. `ResultadoCierre` se representa sin recalcular estado, excepciones o bloqueos. `crear_evidencia()` crea un pack nuevo de operación `evidencia`; `registrar_traspaso()` crea otro pack nuevo de operación `traspaso` con resultado `bloqueado`, `traspaso.md` canónico y sólo después proyecta `docs/ai/07-traspaso-agentes.md`; ninguno reabre un pack publicado. Ninguna operación standalone se presenta como cierre aprobado.

## Mapa de archivos y responsabilidades finales

| Ruta | Acción | Responsabilidad única |
|---|---|---|
| `tramalia/core/integraciones.py` | Crear desde `tools.py` y ampliar | Registro de herramientas, sondas, adaptadores por capacidad y `EstadoIntegracion`. |
| `tramalia/core/procesos.py` | Crear desde `proc.py` | Ejecución cross-platform con salida, código, timeout y cancelación explícitos. |
| `tramalia/core/habilidades.py` | Crear desde `skills.py` | Manifiesto de skills, resolución Git, lock por SHA y estados honestos. |
| `tramalia/core/contexto.py` | Crear desde `context.py` | Construcción de contexto derivado usando integraciones tipadas. |
| `tramalia/core/proveedor_contexto.py` | Crear desde `context_backend.py` | Proveedores que compiten por la capacidad `navegacion_codigo`. |
| `tramalia/core/configuracion.py` | Crear desde los helpers restantes de `project.py` | Lectura y escritura de configuración, proveedor de contexto y modo de trabajo. |
| `tramalia/core/tablero.py` | Crear | `InstantaneaTablero`, filas inmutables y `ServicioTablero`. |
| `tramalia/cli/comandos.py` | Crear desde `commands.py` | Adaptación de argparse a operaciones y códigos de salida. |
| `tramalia/cli/renderizado.py` | Crear desde `render.py` | Conversión de modelos y errores a texto de terminal. |
| `tramalia/interfaz_terminal.py` | Crear desde `tui.py` | Widgets, bindings, navegación, mensajes y workers Textual. |
| `tramalia/mcp_server.py` | Modificar | Tools MCP delgadas con respuestas estructuradas. |
| `tramalia/__main__.py` | Modificar | Parser público existente y despacho a `cli.comandos`. |
| `tramalia/core/doctor.py` | Modificar | Consumir `integraciones` sin redefinir sondas. |
| `tramalia/core/installer.py` | Modificar | Consumir `Herramienta`/`procesos`; conservar instalación en workers. |
| `tramalia/core/scaffold.py` | Modificar | Importar `habilidades` y generar manifiesto compatible. |
| `tramalia/templates/project/.tramalia/habilidades.toml` | Renombrar desde `skills.toml` | Documentar resolución fija reproducible y usar claves españolas nuevas. |
| `tramalia/i18n/es.json` | Modificar | Copia española para estados, fallos y remediaciones. |
| `tramalia/i18n/en.json` | Modificar | Copia inglesa equivalente. |
| `tests/unidad/test_integraciones.py` | Crear | Contrato de procesos y selección por capacidad. |
| `tests/integracion/test_habilidades_git.py` | Crear | Clone/pull no cero, timeout, ref inválida y lock/SHA. |
| `tests/contratos/test_operaciones_superficies.py` | Ampliar | El único contrato de planes 02/03 prueba que CLI y MCP delegan en las operaciones compartidas. |
| `tests/integracion/test_mcp_operaciones.py` | Crear | Sesión MCP pública real, incluido proyecto sin init. |
| `tests/unidad/test_tablero.py` | Crear | Instantáneas inmutables y delegación del servicio. |
| `tests/interfaz/test_interfaz_terminal.py` | Crear | Flujos públicos `pilot`: corrupción, cancelación, timeout y degradación. |
| `tests/contratos/test_nombres_espanol.py` | Crear | Rutas finales españolas y ausencia de módulos retirados. |
| `.github/workflows/validacion.yml` | Modificar | Añadir jobs `plataformas` y `opcionales` al workflow del plan 01. |

Los módulos `tramalia/core/tools.py`, `tramalia/core/proc.py`, `tramalia/core/skills.py`, `tramalia/core/context.py`, `tramalia/core/context_backend.py`, `tramalia/core/project.py`, `tramalia/cli/commands.py`, `tramalia/cli/render.py` y `tramalia/tui.py` se eliminan en la misma tarea que migra todos sus imports. No se dejan módulos puente en inglés.

### Task 1: Contrato de procesos e integraciones por capacidad

**Files:**
- Create: `tramalia/core/procesos.py`
- Create: `tramalia/core/integraciones.py`
- Delete: `tramalia/core/proc.py`
- Delete: `tramalia/core/tools.py`
- Modify: `tramalia/core/doctor.py`
- Modify: `tramalia/core/installer.py`
- Modify: `tramalia/core/puertas_calidad.py`
- Modify: todos los imports actuales de `tramalia.core.proc` y `tramalia.core.tools` encontrados con `rg`
- Create: `tests/unidad/test_integraciones.py`
- Modify: tests históricos que importan `Tool`, `Status`, `REGISTRY`, `probe`, `relevant_tools` o `proc`

**Interfaces:**
- Consumes: `EstadoIntegracion` y su propiedad `exitoso` del contrato del plan 02.
- Produces: `ResultadoProceso`, `AdaptadorCapacidad`, `ResultadoIntentoIntegracion`, `ejecutar_integracion()`, `Herramienta`, `EstadoHerramienta`, `REGISTRO`, `sondear()`, `herramientas_relevantes()`, `detectar_agentes_predeterminados()`.

- [ ] **Step 1: Escribir primero los tests de proceso y fallback**

```python
# tests/unidad/test_integraciones.py
from tramalia.core.integraciones import (
    AdaptadorCapacidad,
    ejecutar_integracion,
)
from tramalia.core.procesos import ResultadoProceso, ejecutar


def _resultado(codigo: int) -> ResultadoProceso:
    return ResultadoProceso(
        comando=("adaptador",),
        codigo_salida=codigo,
        salida="salida",
        error="error" if codigo else "",
        agotado_tiempo=codigo == 124,
        cancelado=codigo == 130,
    )


def test_proceso_con_salida_no_cero_no_se_convierte_en_exito() -> None:
    resultado = ejecutar(
        ["python", "-c", "import sys; print('fallo'); sys.exit(7)"],
        limite_segundos=5,
    )
    assert resultado.codigo_salida == 7
    assert resultado.salida.strip() == "fallo"
    assert not resultado.exitoso


def test_proceso_agotado_conserva_estado_124() -> None:
    resultado = ejecutar(
        ["python", "-c", "import time; time.sleep(2)"],
        limite_segundos=0.05,
    )
    assert resultado.codigo_salida == 124
    assert resultado.agotado_tiempo
    assert not resultado.cancelado


def test_alternativa_exitosa_es_degradada() -> None:
    llamados: list[str] = []
    adaptadores = (
        AdaptadorCapacidad("preferido", frozenset({"memoria"}), lambda: False),
        AdaptadorCapacidad("local", frozenset({"memoria"}), lambda: True),
    )

    intento = ejecutar_integracion(
        capacidad="memoria",
        solicitado="preferido",
        adaptadores=adaptadores,
        operacion=lambda nombre: llamados.append(nombre) or _resultado(0),
        impacto_degradado="sin sincronización remota",
        remediacion="instala preferido",
    )

    assert llamados == ["local"]
    assert intento.estado.estado == "degradado"
    assert intento.estado.solicitado == "preferido"
    assert intento.estado.utilizado == "local"


def test_intento_fallido_no_se_oculta_con_otra_alternativa() -> None:
    llamados: list[str] = []
    adaptadores = (
        AdaptadorCapacidad("preferido", frozenset({"memoria"}), lambda: True),
        AdaptadorCapacidad("local", frozenset({"memoria"}), lambda: True),
    )

    intento = ejecutar_integracion(
        capacidad="memoria",
        solicitado="preferido",
        adaptadores=adaptadores,
        operacion=lambda nombre: llamados.append(nombre) or _resultado(9),
        impacto_degradado="sin sincronización remota",
        remediacion="revisa el adaptador preferido",
    )

    assert llamados == ["preferido"]
    assert intento.estado.estado == "fallido"
    assert intento.estado.motivo == "proceso_salida_no_cero"
    assert intento.proceso is not None and intento.proceso.codigo_salida == 9


def test_capacidad_opcional_sin_adaptador_es_no_disponible() -> None:
    intento = ejecutar_integracion(
        capacidad="memoria",
        solicitado=None,
        adaptadores=(),
        operacion=lambda _nombre: _resultado(0),
        impacto_degradado="sin memoria persistente",
        remediacion="instala un adaptador de memoria",
    )
    assert intento.estado.estado == "no_disponible"
    assert intento.estado.motivo == "capacidad_opcional_no_solicitada"
    assert intento.proceso is None
```

- [ ] **Step 2: Ejecutar los tests y comprobar que fallan por los módulos nuevos**

Run: `uv run pytest tests/unidad/test_integraciones.py -q`

Expected: FAIL durante colección con `ModuleNotFoundError: No module named 'tramalia.core.integraciones'`.

- [ ] **Step 3: Renombrar los módulos y definir el contrato mínimo completo**

Usar `git mv tramalia/core/proc.py tramalia/core/procesos.py` y `git mv tramalia/core/tools.py tramalia/core/integraciones.py`. En `procesos.py`, reemplazar la API anterior por:

```python
"""Run external processes with explicit cross-platform outcomes."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ResultadoProceso:
    """Describe one external process without hiding failure states."""

    comando: tuple[str, ...]
    codigo_salida: int
    salida: str
    error: str
    agotado_tiempo: bool = False
    cancelado: bool = False

    @property
    def exitoso(self) -> bool:
        """Return whether the process completed successfully."""
        return self.codigo_salida == 0 and not self.agotado_tiempo and not self.cancelado


def encontrar(comando: str) -> str | None:
    """Locate an executable using the current process PATH."""
    return shutil.which(comando)


def _resolver(comando: Sequence[str]) -> list[str]:
    ejecutable = shutil.which(comando[0])
    if ejecutable is None:
        raise FileNotFoundError(comando[0])
    argumentos = [ejecutable, *comando[1:]]
    if os.name == "nt" and ejecutable.lower().endswith((".cmd", ".bat")):
        return ["cmd", "/c", *argumentos]
    return argumentos


def ejecutar(
    comando: Sequence[str],
    *,
    raiz: Path | None = None,
    limite_segundos: float = 60.0,
) -> ResultadoProceso:
    """Run a command and normalize absence, timeout, output and exit status.

    Args:
        comando: Executable and arguments without shell interpolation.
        raiz: Working directory for the child process.
        limite_segundos: Maximum runtime before termination.

    Returns:
        A stable result. Missing executables use exit 127 and timeouts use 124.
    """
    original = tuple(str(parte) for parte in comando)
    try:
        completado = subprocess.run(
            _resolver(original),
            cwd=raiz,
            capture_output=True,
            text=True,
            timeout=limite_segundos,
            check=False,
        )
    except FileNotFoundError as error:
        return ResultadoProceso(original, 127, "", str(error))
    except subprocess.TimeoutExpired as error:
        salida = error.stdout.decode(errors="replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode(errors="replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
        return ResultadoProceso(original, 124, salida, stderr, agotado_tiempo=True)
    return ResultadoProceso(
        comando=original,
        codigo_salida=completado.returncode,
        salida=completado.stdout or "",
        error=completado.stderr or "",
    )
```

Conservar en `integraciones.py` todas las entradas actuales del registro, cambiando exactamente esta API: `Tool → Herramienta`, `Status → EstadoHerramienta`, `REGISTRY → REGISTRO`, `DOCS → DOCUMENTACION`, `docs_url → url_documentacion`, `probe → sondear`, `detect_default_agents → detectar_agentes_predeterminados`, `relevant_tools → herramientas_relevantes`. Renombrar los campos propios así: `key → clave`, `cmd → comando`, `role → rol`, `category → categoria`, `version_args → argumentos_version`, `managed_by_mise → administrada_por_mise`, `install_hint → sugerencia_instalacion`, `stacks → tecnologias`, `feature → capacidad`, `runtime → entorno_ejecucion`, `ephemeral → efimera`, `winget_id → id_winget`, `tool → herramienta`, `present → presente`, `version → version`. Los nombres de ejecutables, categorías y formatos externos conservan sus valores actuales.

Añadir `Callable` y `Sequence` al bloque superior de imports desde `collections.abc`, y `EstadoIntegracion`, `ValorEstadoIntegracion` y `ResultadoProceso` al bloque superior de imports internos, respetando el orden de Ruff. No insertar imports debajo de declaraciones existentes. Añadir luego estos modelos:

```python
@dataclass(frozen=True, slots=True)
class AdaptadorCapacidad:
    """Declare which capability an optional adapter can provide."""

    nombre: str
    capacidades: frozenset[str]
    disponible: Callable[[], bool]


@dataclass(frozen=True, slots=True)
class ResultadoIntentoIntegracion:
    """Pair an integration state with the external process that produced it."""

    estado: EstadoIntegracion
    proceso: ResultadoProceso | None


def ejecutar_integracion(
    *,
    capacidad: str,
    solicitado: str | None,
    adaptadores: Sequence[AdaptadorCapacidad],
    operacion: Callable[[str], ResultadoProceso],
    impacto_degradado: str,
    remediacion: str,
) -> ResultadoIntentoIntegracion:
    """Execute one adapter selected by capability without hiding failed attempts.

    A missing preferred adapter may fall back to the first available adapter that
    declares the same capability. Once any adapter is executed, a non-zero exit,
    timeout or cancellation is final and no second adapter is attempted.
    """
    candidatos = [a for a in adaptadores if capacidad in a.capacidades]
    if solicitado is None:
        return ResultadoIntentoIntegracion(
            EstadoIntegracion(
                ValorEstadoIntegracion.NO_DISPONIBLE, capacidad, None, None,
                "capacidad_opcional_no_solicitada", impacto_degradado, remediacion,
            ),
            None,
        )

    preferidos = [a for a in candidatos if a.nombre == solicitado]
    restantes = [a for a in candidatos if a.nombre != solicitado]
    elegido = next((a for a in (*preferidos, *restantes) if a.disponible()), None)
    if elegido is None:
        return ResultadoIntentoIntegracion(
            EstadoIntegracion(
                ValorEstadoIntegracion.NO_DISPONIBLE, capacidad, solicitado, None,
                "adaptador_no_instalado", impacto_degradado, remediacion,
            ),
            None,
        )

    proceso = operacion(elegido.nombre)
    if not proceso.exitoso:
        motivo = (
            "proceso_agotado" if proceso.agotado_tiempo
            else "proceso_cancelado" if proceso.cancelado
            else "proceso_salida_no_cero"
        )
        return ResultadoIntentoIntegracion(
            EstadoIntegracion(
                ValorEstadoIntegracion.FALLIDO, capacidad, solicitado, elegido.nombre,
                motivo, impacto_degradado, remediacion,
            ),
            proceso,
        )

    degradado = elegido.nombre != solicitado
    return ResultadoIntentoIntegracion(
        EstadoIntegracion(
            ValorEstadoIntegracion.DEGRADADO if degradado else ValorEstadoIntegracion.COMPLETO,
            capacidad,
            solicitado,
            elegido.nombre,
            "alternativa_completada" if degradado else "adaptador_completado",
            impacto_degradado if degradado else "sin impacto",
            remediacion if degradado else "ninguna",
        ),
        proceso,
    )
```

- [ ] **Step 4: Migrar imports y usos sin dejar alias ingleses**

Aplicar el mapa de símbolos anterior a `doctor.py`, `installer.py`, `puertas_calidad.py`, `context.py`, `context_backend.py`, `skills.py`, CLI, TUI, tests y cualquier resultado de:

Run: `rg -n "core\.(tools|proc)|from tramalia\.core import (tools|proc)|\b(Tool|Status|REGISTRY|probe|relevant_tools|detect_default_agents)\b" tramalia tests`

Expected antes de editar: coincidencias en los archivos históricos listados en el mapa. Expected después de editar: ninguna coincidencia, salvo texto histórico deliberado en documentación de release.

Los callers que requieren streaming (`installer.run_install_streaming`) conservan `subprocess.Popen`, pero importan `_resolver` desde `procesos` sólo dentro de `installer.py`; puertas, Git, contexto y superficies usan `ResultadoProceso`.

- [ ] **Step 5: Ejecutar tests de unidad y regresión**

Run: `uv run pytest tests/unidad/test_integraciones.py tests/test_doctor.py tests/test_v013.py tests/test_v015.py tests/test_v017.py tests/test_v020.py tests/test_v027.py tests/test_v032.py -q`

Expected: PASS; los tests de proceso prueban códigos 7 y 124 y la regresión no importa módulos retirados.

- [ ] **Step 6: Ejecutar la suite completa para validar el rename atómico**

Run: `uv run pytest -q`

Expected: PASS sin `ModuleNotFoundError` y sin skips nuevos fuera de extras opcionales ya marcados.

- [ ] **Step 7: Commit**

```bash
git add tramalia/core/integraciones.py tramalia/core/procesos.py tramalia/core/doctor.py tramalia/core/installer.py tramalia/core/puertas_calidad.py tramalia tests
git commit -m "refactor: tipar procesos e integraciones por capacidad"
```

### Task 2: Habilidades Git reproducibles, bloqueos y contexto por capacidad

**Files:**
- Create: `tramalia/core/habilidades.py`
- Create: `tramalia/core/contexto.py`
- Create: `tramalia/core/proveedor_contexto.py`
- Create: `tramalia/core/configuracion.py`
- Delete: `tramalia/core/skills.py`
- Delete: `tramalia/core/context.py`
- Delete: `tramalia/core/context_backend.py`
- Delete: `tramalia/core/project.py`
- Modify: `tramalia/core/scaffold.py`
- Rename: `tramalia/templates/project/.tramalia/skills.toml` → `tramalia/templates/project/.tramalia/habilidades.toml`
- Rename: `tramalia/templates/project/.tramalia/skills/` → `tramalia/templates/project/.tramalia/habilidades/` (los identificadores internos de habilidades se conservan por compatibilidad)
- Modify: `tramalia/templates/project/AGENTS.md.jinja`
- Modify: `tramalia/templates/project/docs/ai/11-reglas-ux-ui.md.jinja`
- Modify: `docs/herramientas.md`, `docs/herramientas.en.md` y mensajes i18n/ayuda que muestran la ruta del manifiesto
- Modify: imports en `tramalia/cli/commands.py`, `tramalia/tui.py`, `tramalia/mcp_server.py` y tests históricos
- Create: `tests/integracion/test_habilidades_git.py`
- Modify: `tests/test_tools_and_skills.py`
- Modify: `tests/test_v019.py`
- Modify: `tests/test_v021.py`
- Modify: `tests/test_v024.py`
- Modify: `tests/test_v028.py`
- Modify: `tests/test_v029.py`
- Modify: `tests/test_v031.py`

**Interfaces:**
- Consumes: `EstadoIntegracion`, `ResultadoProceso`, `AdaptadorCapacidad`, `ejecutar_integracion()` y la configuración heredada de `project.py` sólo como fuente de migración.
- Produces: `HabilidadDeclarada`, `BloqueoHabilidad`, `ResolucionHabilidad`, `ResultadoSincronizacionHabilidades`, `leer_habilidades()`, `sincronizar_habilidades()`, `consultar_habilidades()`, `ResultadoContexto`, `construir_contexto()`, `PROVEEDORES`, `proveedor_disponible()`, `leer_configuracion()`, `guardar_configuracion()`, `id_tarea_actual()`, `agentes_predeterminados()`, `proveedor_contexto()`, `fijar_proveedor_contexto()` y `modo_trabajo()`.

- [ ] **Step 1: Escribir tests herméticos para fallo de clone/pull/timeout/ref y lock Team**

```python
# tests/integracion/test_habilidades_git.py
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from tramalia.core import habilidades
from tramalia.core.procesos import ResultadoProceso


def _ejecutar_git(raiz: Path, *argumentos: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(raiz), *argumentos],
        capture_output=True,
        text=True,
        check=False,
    )


def _remoto(tmp_path: Path) -> Path:
    remoto = tmp_path / "remoto"
    remoto.mkdir()
    if _ejecutar_git(remoto, "init", "-b", "main").returncode != 0:
        assert _ejecutar_git(remoto, "init").returncode == 0
        assert _ejecutar_git(remoto, "checkout", "-b", "main").returncode == 0
    (remoto / "SKILL.md").write_text("v1\n", encoding="utf-8")
    assert _ejecutar_git(remoto, "add", "SKILL.md").returncode == 0
    assert _ejecutar_git(
        remoto, "-c", "user.email=test@example.com", "-c", "user.name=Test",
        "commit", "-m", "v1",
    ).returncode == 0
    return remoto


def _proyecto(tmp_path: Path, remoto: Path, *, modo: str = "team") -> Path:
    raiz = tmp_path / "proyecto"
    (raiz / ".tramalia").mkdir(parents=True)
    (raiz / ".tramalia" / "config.json").write_text(
        json.dumps({"mode": modo}), encoding="utf-8"
    )
    (raiz / ".tramalia" / "habilidades.toml").write_text(
        "[[habilidad]]\n"
        "nombre = \"demo\"\n"
        f"fuente = \"{remoto.as_uri()}\"\n"
        "referencia = \"main\"\n",
        encoding="utf-8",
    )
    return raiz


def test_resolver_sha_normaliza_prefijo_git_sin_cambiar_fuente_canonica(
    tmp_path: Path, monkeypatch,
) -> None:
    llamadas: list[tuple[str, ...]] = []

    def ejecutar(argumentos, **_opciones):
        llamadas.append(tuple(argumentos))
        return ResultadoProceso(
            tuple(argumentos), 0, f"{'a' * 40}\trefs/heads/main\n", "", False, False,
        )

    monkeypatch.setattr(habilidades, "_ejecutar_git", ejecutar)
    sha, resultado = habilidades._resolver_sha(
        "git+https://example.com/equipo/habilidad.git", "main", tmp_path,
    )

    assert resultado.exitoso
    assert sha == "a" * 40
    assert llamadas == [(
        "git", "ls-remote", "--exit-code",
        "https://example.com/equipo/habilidad.git", "main",
    )]


@pytest.mark.skipif(not habilidades.git_disponible(), reason="requiere git")
def test_modo_equipo_rehidrata_sha_fijado_sin_seguir_main(tmp_path: Path) -> None:
    remoto = _remoto(tmp_path)
    raiz = _proyecto(tmp_path, remoto)

    inicial = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    sha_fijado = inicial.resoluciones[0].sha_resuelto
    assert inicial.estado.estado == "completo"
    assert len(sha_fijado) == 40

    (remoto / "SKILL.md").write_text("v2\n", encoding="utf-8")
    assert _ejecutar_git(remoto, "add", "SKILL.md").returncode == 0
    assert _ejecutar_git(
        remoto, "-c", "user.email=test@example.com", "-c", "user.name=Test",
        "commit", "-m", "v2",
    ).returncode == 0
    destino = raiz / ".tramalia" / "habilidades" / "demo"
    sha_nuevo = _ejecutar_git(remoto, "rev-parse", "HEAD").stdout.strip()
    assert sha_nuevo != sha_fijado
    assert _ejecutar_git(destino, "fetch", "origin", sha_nuevo).returncode == 0
    assert _ejecutar_git(destino, "checkout", "--detach", sha_nuevo).returncode == 0
    assert _ejecutar_git(destino, "rev-parse", "HEAD").stdout.strip() == sha_nuevo

    rehidratado = habilidades.sincronizar_habilidades(raiz)
    assert rehidratado.resoluciones[0].sha_resuelto == sha_fijado
    assert _ejecutar_git(destino, "rev-parse", "HEAD").stdout.strip() == sha_fijado


@pytest.mark.skipif(not habilidades.git_disponible(), reason="requiere git")
def test_modo_equipo_recrea_checkout_ausente_desde_sha_fijado(tmp_path: Path) -> None:
    remoto = _remoto(tmp_path)
    raiz = _proyecto(tmp_path, remoto)
    inicial = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    sha_fijado = inicial.resoluciones[0].sha_resuelto
    ruta_bloqueo = raiz / ".tramalia" / "habilidades.lock.json"
    bloqueo_original = ruta_bloqueo.read_bytes()
    destino = raiz / ".tramalia" / "habilidades" / "demo"

    (remoto / "SKILL.md").write_text("v2\n", encoding="utf-8")
    assert _ejecutar_git(remoto, "add", "SKILL.md").returncode == 0
    assert _ejecutar_git(
        remoto, "-c", "user.email=test@example.com", "-c", "user.name=Test",
        "commit", "-m", "v2",
    ).returncode == 0
    sha_nuevo = _ejecutar_git(remoto, "rev-parse", "HEAD").stdout.strip()
    assert sha_nuevo != sha_fijado

    # Simula un clon fresco del proyecto: se conserva el lock, no el checkout externo.
    shutil.rmtree(destino)
    rehidratado = habilidades.sincronizar_habilidades(raiz)

    assert rehidratado.estado.estado == "completo"
    assert rehidratado.resoluciones[0].sha_resuelto == sha_fijado
    assert _ejecutar_git(destino, "rev-parse", "HEAD").stdout.strip() == sha_fijado
    assert ruta_bloqueo.read_bytes() == bloqueo_original


@pytest.mark.skipif(not habilidades.git_disponible(), reason="requiere git")
def test_actualizacion_explicita_mueve_el_bloqueo(tmp_path: Path) -> None:
    remoto = _remoto(tmp_path)
    raiz = _proyecto(tmp_path, remoto)
    anterior = habilidades.sincronizar_habilidades(raiz, actualizar=True).resoluciones[0].sha_resuelto
    (remoto / "SKILL.md").write_text("v2\n", encoding="utf-8")
    _ejecutar_git(remoto, "add", "SKILL.md")
    _ejecutar_git(
        remoto, "-c", "user.email=test@example.com", "-c", "user.name=Test",
        "commit", "-m", "v2",
    )

    actualizado = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    nuevo = actualizado.resoluciones[0].sha_resuelto
    bloqueo = json.loads((raiz / ".tramalia" / "habilidades.lock.json").read_text(encoding="utf-8"))
    assert nuevo != anterior
    assert bloqueo["habilidades"]["demo"] == {
        "fuente": remoto.as_uri(), "referencia": "main", "sha_resuelto": nuevo,
    }


def test_clonacion_no_cero_es_fallida_y_no_escribe_bloqueo(tmp_path: Path, monkeypatch) -> None:
    raiz = _proyecto(tmp_path, tmp_path / "ausente")
    monkeypatch.setattr(habilidades, "_ejecutar_git", lambda *_a, **_k: ResultadoProceso(
        ("git", "clone"), 128, "", "fatal: clone", False, False,
    ))
    resultado = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    assert resultado.estado.estado == "fallido"
    assert resultado.resoluciones[0].estado.motivo == "git_salida_no_cero"
    assert not (raiz / ".tramalia" / "habilidades.lock.json").exists()


def test_pull_no_cero_no_declara_actualizada(tmp_path: Path, monkeypatch) -> None:
    raiz = _proyecto(tmp_path, tmp_path / "remoto", modo="local-first")
    destino = raiz / ".tramalia" / "habilidades" / "demo" / ".git"
    destino.mkdir(parents=True)
    monkeypatch.setattr(habilidades, "_ejecutar_git", lambda *_a, **_k: ResultadoProceso(
        ("git", "pull"), 1, "", "non-fast-forward", False, False,
    ))
    resultado = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    assert resultado.estado.estado == "fallido"
    assert resultado.resoluciones[0].accion == "fallida"


def test_tiempo_agotado_git_es_fallido_explicito(tmp_path: Path, monkeypatch) -> None:
    raiz = _proyecto(tmp_path, tmp_path / "remoto")
    monkeypatch.setattr(habilidades, "_ejecutar_git", lambda *_a, **_k: ResultadoProceso(
        ("git", "ls-remote"), 124, "", "", True, False,
    ))
    resultado = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    assert resultado.estado.estado == "fallido"
    assert resultado.resoluciones[0].estado.motivo == "git_tiempo_agotado"


@pytest.mark.skipif(not habilidades.git_disponible(), reason="requiere git")
def test_referencia_invalida_no_mueve_bloqueo(tmp_path: Path) -> None:
    remoto = _remoto(tmp_path)
    raiz = _proyecto(tmp_path, remoto)
    manifiesto = raiz / ".tramalia" / "habilidades.toml"
    manifiesto.write_text(
        manifiesto.read_text(encoding="utf-8").replace("main", "no-existe"),
        encoding="utf-8",
    )
    resultado = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    assert resultado.estado.estado == "fallido"
    assert resultado.resoluciones[0].estado.motivo == "referencia_no_resuelta"
    assert not (raiz / ".tramalia" / "habilidades.lock.json").exists()
```

- [ ] **Step 2: Ejecutar la prueba y confirmar la ausencia del módulo español**

Run: `uv run pytest tests/integracion/test_habilidades_git.py -q`

Expected: FAIL en colección con `ImportError: cannot import name 'habilidades' from 'tramalia.core'`.

- [ ] **Step 3: Renombrar módulos y definir los modelos públicos de habilidades**

Ejecutar `git mv tramalia/core/skills.py tramalia/core/habilidades.py`, `git mv tramalia/core/context.py tramalia/core/contexto.py` y `git mv tramalia/core/context_backend.py tramalia/core/proveedor_contexto.py`. En `habilidades.py` conservar el parser conservador de bloques y el managed block de `.gitignore`, pero exponer estos modelos y firmas:

```python
@dataclass(frozen=True, slots=True)
class HabilidadDeclarada:
    """Describe one external skill declared by a project manifest."""

    nombre: str
    fuente: str
    referencia: str
    habilitada: bool
    instalada: bool


@dataclass(frozen=True, slots=True)
class BloqueoHabilidad:
    """Pin a skill source and reference to one immutable Git commit."""

    fuente: str
    referencia: str
    sha_resuelto: str


@dataclass(frozen=True, slots=True)
class ResolucionHabilidad:
    """Report the resolved Git identity and resulting integration state."""

    nombre: str
    fuente: str
    referencia: str
    sha_resuelto: str | None
    accion: Literal["clonada", "rehidratada", "actualizada", "sin_cambios", "fallida"]
    estado: EstadoIntegracion


@dataclass(frozen=True, slots=True)
class ResultadoSincronizacionHabilidades:
    """Aggregate a requested skill synchronization without losing item failures."""

    estado: EstadoIntegracion
    resoluciones: tuple[ResolucionHabilidad, ...]


def leer_habilidades(raiz: Path) -> tuple[HabilidadDeclarada, ...]: ...
def catalogo_habilidades(raiz: Path) -> tuple[HabilidadDeclarada, ...]: ...
def fijar_habilitada(raiz: Path, nombre: str, habilitada: bool) -> bool: ...
def agregar_habilidad(raiz: Path, fuente: str, nombre: str | None = None) -> tuple[bool, str]: ...
def habilidades_propias(raiz: Path) -> tuple[dict[str, str], ...]: ...
def habilidades_externas_rastreadas(raiz: Path) -> tuple[str, ...]: ...
def git_disponible() -> bool: ...
def referencia_instalada(raiz: Path, nombre: str) -> str | None: ...
def consultar_habilidades(raiz: Path, consultar_remoto: bool = False) -> tuple[ResolucionHabilidad, ...]: ...
def sincronizar_habilidades(
    raiz: Path,
    solo: str | None = None,
    *,
    actualizar: bool = False,
) -> ResultadoSincronizacionHabilidades: ...
```

El lector acepta durante esta BETA el archivo heredado `.tramalia/skills.toml` y sus claves `[[skill]]/name/source/ref`, además del nuevo `.tramalia/habilidades.toml` con `[[habilidad]]/nombre/fuente/referencia`. Toda escritura nueva usa el archivo y las claves españolas; una mutación sobre el formato heredado lo migra atómicamente y retira el archivo antiguo después de validar el nuevo. El lock se llama `.tramalia/habilidades.lock.json`, siempre tiene esta forma y se publica con un `.tmp-<uuid>` hermano seguido de `Path.replace()`:

```json
{
  "version_esquema": 1,
  "habilidades": {
    "demo": {
      "fuente": "https://example.com/demo.git",
      "referencia": "main",
      "sha_resuelto": "0123456789abcdef0123456789abcdef01234567"
    }
  }
}
```

Implementar la decisión de resolución exactamente así. El manifiesto y el lock conservan la fuente canónica completa; únicamente se retira el prefijo de transporte `git+` en el argumento entregado al ejecutable Git:

```python
def _fuente_para_git(fuente: str) -> str:
    """Return a source URL accepted by the Git executable."""
    # `git+` identifica el tipo de fuente en Tramalia, pero no forma parte de la URL de Git.
    return fuente.removeprefix("git+")


def _resolver_sha(fuente: str, referencia: str, raiz: Path) -> tuple[str | None, ResultadoProceso]:
    if referencia == "latest":
        return None, ResultadoProceso(("git", "ls-remote"), 2, "", "latest no permitido")
    resultado = _ejecutar_git(
        ["git", "ls-remote", "--exit-code", _fuente_para_git(fuente), referencia],
        raiz=raiz,
        limite_segundos=20,
    )
    if not resultado.exitoso:
        return None, resultado
    primera = resultado.salida.splitlines()[0].split() if resultado.salida.splitlines() else []
    sha = primera[0] if primera else ""
    return (sha if re.fullmatch(r"[0-9a-fA-F]{40}", sha) else None), resultado
```

| Modo/configuración | `actualizar=False` | `actualizar=True` | Escritura del lock |
|---|---|---|---|
| `team`, lock presente y checkout presente | fetch/checkout detached del `sha_resuelto`; nunca `pull` | resolver `referencia`, fetch/checkout detached | sólo después de checkout y `rev-parse HEAD` exitosos |
| `team`, lock presente y checkout ausente | inicializar o clonar desde la fuente canónica, fetch del `sha_resuelto` y checkout detached; nunca resolver la referencia | resolver `referencia`, clonar/fetch/checkout detached | conserva el lock byte por byte sin actualización; sólo falla si no puede verificar el SHA |
| `team`, sin lock | resolver `referencia`, clone/fetch/checkout detached | igual | crea lock tras verificar SHA |
| `team`, `referencia=latest` | `fallido/referencia_no_resuelta` | `fallido/referencia_no_resuelta` | nunca |
| cualquier modo, `ls-remote --exit-code` devuelve 2 | `fallido/referencia_no_resuelta` | `fallido/referencia_no_resuelta` | nunca |
| `local-first`, destino ausente | clone de `referencia`, luego `rev-parse HEAD` | igual | tras clone exitoso |
| `local-first`, destino presente | sin cambios | `git pull --ff-only`, luego `rev-parse HEAD` | sólo tras pull exitoso |

Clasificar el resultado en este orden para que los motivos no se solapen: código 124 produce `git_tiempo_agotado`; `git ls-remote --exit-code` con código 2 produce `referencia_no_resuelta`; cualquier otro código no cero produce `git_salida_no_cero`; y una salida cero sin SHA verificable produce `sha_no_verificado`. Un fallo conserva el lock anterior byte por byte. El agregado queda `fallido` si una resolución falla, `degradado` si alguna resolución lo está, `completo` si todas completaron y `no_disponible` con motivo `sin_habilidades_declaradas` si no hay ninguna. Git ausente produce `no_disponible/git_no_instalado`; el comando CLI solicitado devolverá código 1 porque `exitoso` es falso.

- [ ] **Step 4: Convertir contexto y proveedor a APIs españolas basadas en capacidades**

```python
# tramalia/core/proveedor_contexto.py
PROVEEDORES: dict[str, dict[str, str]] = {
    "serena": {
        "herramienta": "serena", "etiqueta": "Serena — navegación semántica viva",
        "alcance": "Lee el símbolo exacto mediante LSP, sin índice persistente.",
        "ideal": "Proyectos que cambian seguido y no mantienen un índice separado.",
        "capacidad": "navegacion_codigo",
    },
    "codegraph": {
        "herramienta": "codegraph", "etiqueta": "CodeGraph — grafo pre-indexado",
        "alcance": "Índice SQLite con impacto y relaciones de código.",
        "ideal": "Repos grandes de un lenguaje principal usados a diario.",
        "capacidad": "navegacion_codigo",
    },
    "codebase-memory-mcp": {
        "herramienta": "codebase-memory-mcp",
        "etiqueta": "codebase-memory-mcp — grafo estructural políglota",
        "alcance": "Grafo persistente con LSP y tree-sitter.",
        "ideal": "Repos políglotas que requieren vistas de arquitectura.",
        "capacidad": "navegacion_codigo",
    },
    "graphify": {
        "herramienta": "graphify", "etiqueta": "Graphify — grafo multi-formato",
        "alcance": "Relaciona código, documentación, SQL y schemas.",
        "ideal": "Proyectos cuyo contexto cruza código y documentos.",
        "capacidad": "navegacion_codigo",
    },
}
PREDETERMINADO = "serena"
UTILIDADES: dict[str, dict[str, str]] = {
    "repomix": {
        "herramienta": "repomix", "etiqueta": "Repomix — snapshot empaquetado",
        "alcance": "Empaqueta el repositorio para una entrega puntual de contexto.",
        "ideal": "Onboarding o análisis que necesita el repositorio completo.",
    },
    "markitdown": {
        "herramienta": "markitdown", "etiqueta": "markitdown — ingesta documental",
        "alcance": "Convierte PDF, Office e imágenes a Markdown.",
        "ideal": "Conocimiento del proyecto que vive fuera del código.",
    },
}


def proveedor_disponible(nombre: str) -> bool:
    """Return whether a context provider can supply code navigation."""
    metadatos = PROVEEDORES.get(nombre)
    if metadatos is None:
        return False
    herramienta = next((h for h in REGISTRO if h.clave == metadatos["herramienta"]), None)
    return sondear(herramienta).presente if herramienta else encontrar(metadatos["herramienta"]) is not None
```

Mover los helpers restantes de `project.py` a `configuracion.py`, renombrando `read_config → leer_configuracion`, `write_config → guardar_configuracion`, `current_task_id → id_tarea_actual`, `default_agents → agentes_predeterminados`, `context_backend → proveedor_contexto` y `set_context_backend → fijar_proveedor_contexto`. Añadir `modo_trabajo(raiz: Path) -> Literal["local-first", "team"]`, devolviendo `team` sólo para ese valor exacto y `local-first` para configuración ausente o heredada. Migrar todos los imports y eliminar `project.py` sin dejar un módulo puente.

`contexto.py` expone:

```python
@dataclass(frozen=True, slots=True)
class ResultadoContexto:
    """Return generated context files and optional adapter state."""

    archivos: tuple[Path, ...]
    integracion: EstadoIntegracion


def construir_contexto(raiz: Path) -> ResultadoContexto:
    """Build local context and report whether Repomix completed or fell back."""
```

La función siempre escribe `tech-stack.md` y `project-map.md` primero. Si Repomix está disponible, lo ejecuta con `procesos.ejecutar`; código no cero/timeout devuelve `fallido` y no añade `repomix-output.md`. Si no está disponible, el árbol stdlib ya escrito cuenta como fallback completado y devuelve `degradado` con `solicitado="repomix"`, `utilizado="arbol_stdlib"` y motivo `alternativa_completada`.

- [ ] **Step 5: Migrar manifiesto, imports y pruebas históricas**

Ejecutar `git mv tramalia/templates/project/.tramalia/skills.toml tramalia/templates/project/.tramalia/habilidades.toml` y `git mv tramalia/templates/project/.tramalia/skills tramalia/templates/project/.tramalia/habilidades`; cambiar la plantilla a `[[habilidad]]`, `nombre`, `fuente`, `referencia`, y añadir al encabezado: `# habilidades.lock.json fija cada referencia a un sha_resuelto; tramalia skills update es la única operación que mueve el bloqueo en modo team.` Actualizar todos los imports y símbolos encontrados por:

Run: `rg -n "core\.(skills|context_backend|context)|from tramalia\.core import (skills|context)|\b(BACKENDS|DEFAULT|backend_installed|sync_skills|external_status)\b" tramalia tests`

Expected después: ninguna coincidencia con módulos retirados ni APIs propias inglesas.

Actualizar también toda ruta visible al usuario a `.tramalia/habilidades.toml`, `.tramalia/habilidades/` y `.tramalia/habilidades.lock.json` en plantillas, ayuda, i18n y documentación ES/EN. Las cadenas heredadas `.tramalia/skills.toml` sólo pueden permanecer dentro del lector/migrador de compatibilidad y sus tests explícitos. Comprobar sus coincidencias con dos comandos que funcionan igual en PowerShell: `rg -n "\.tramalia/(skills\.toml|skills/)|skills\.lock\.json" tramalia tests docs` y `rg -n -g 'README*' "\.tramalia/(skills\.toml|skills/)|skills\.lock\.json" .`; justificar cada coincidencia en el test de migración.

Como parte de la migración de `tests/test_v029.py` y `tests/test_v031.py`, renombrar los auxiliares propios `_git → _ejecutar_git`, `_git_repo → _crear_repositorio_git`, `root → raiz` y `args → argumentos`; `tmp_path` y `monkeypatch` permanecen por ser fixtures impuestas por pytest. Verificar esos dos archivos con `rg -n "def _git|\b(root|args)\b" tests/test_v029.py tests/test_v031.py`, que debe quedar sin salida.

- [ ] **Step 6: Ejecutar las pruebas Git y de contexto**

Run: `uv run pytest tests/integracion/test_habilidades_git.py tests/test_context.py tests/test_tools_and_skills.py tests/test_v019.py tests/test_v021.py tests/test_v024.py tests/test_v028.py tests/test_v029.py tests/test_v031.py -q`

Expected: PASS; tests con Git real sólo se omiten si Git no está instalado, y los tests inyectados de clone/pull/timeout siempre se ejecutan.

- [ ] **Step 7: Ejecutar la suite completa**

Run: `uv run pytest -q`

Expected: PASS y cero imports de `skills.py`, `context.py` o `context_backend.py`.

- [ ] **Step 8: Commit**

```bash
git add tramalia/core/habilidades.py tramalia/core/contexto.py tramalia/core/proveedor_contexto.py tramalia/core/configuracion.py tramalia/core/project.py tramalia/core/scaffold.py tramalia/templates/project/.tramalia/habilidades.toml tramalia tests docs/herramientas.md docs/herramientas.en.md
git commit -m "feat: fijar habilidades git por sha reproducible"
```

### Task 3: CLI delgada sobre operaciones compartidas

**Files:**
- Create: `tramalia/cli/comandos.py`
- Create: `tramalia/cli/renderizado.py`
- Delete: `tramalia/cli/commands.py`
- Delete: `tramalia/cli/render.py`
- Modify: `tramalia/__main__.py`
- Modify: `tramalia/cli/menu.py`
- Modify: imports de CLI en `tramalia/tui.py` y tests históricos
- Modify: `tests/contratos/test_operaciones_superficies.py`

**Interfaces:**
- Consumes: `cerrar_proyecto()`, `crear_evidencia()`, `registrar_traspaso()`, `ExcepcionFallo`, `ErrorTramalia`, `ResultadoCierre`, `PaqueteEvidencia`, `ResultadoSincronizacionHabilidades`, `construir_contexto()`.
- Produces: `despachar(comando: str, argumentos: argparse.Namespace) -> int`, `construir_excepciones(argumentos, revisor_predeterminado) -> tuple[ExcepcionFallo, ...]`, `renderizar_error(error: ErrorTramalia) -> None`.

- [ ] **Step 1: Escribir contratos CLI que demuestran delegación y error estable**

```python
# tests/contratos/test_operaciones_superficies.py
from pathlib import Path

from tramalia.__main__ import main
from tramalia.core.errores import ErrorIdentificadorInseguro
from tramalia.core.modelos import (
    EjecucionPuertas,
    ResultadoCierre,
    ValorEstadoCierre,
    ValorEstadoPuertas,
)


def test_cli_evidencia_delega_en_crear_evidencia(tmp_path, monkeypatch, capsys) -> None:
    llamadas: list[tuple[Path, str]] = []

    class Paquete:
        id_paquete = "paquete-1"
        ruta = tmp_path / ".tramalia" / "evidencia" / "paquete-1"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "tramalia.cli.comandos.crear_evidencia",
        lambda raiz, id_tarea, **_opciones: llamadas.append((raiz, id_tarea)) or Paquete(),
    )
    assert main(["--plain", "evidence", "TASK-1"]) == 0
    assert llamadas == [(tmp_path, "TASK-1")]
    assert "paquete-1" in capsys.readouterr().out


def test_cli_traspaso_delega_y_crea_paquete_nuevo(tmp_path, monkeypatch, capsys) -> None:
    class Paquete:
        id_paquete = "traspaso-1"
        ruta = tmp_path / ".tramalia" / "evidencia" / "traspaso-1"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("tramalia.cli.comandos.registrar_traspaso", lambda *_a, **_k: Paquete())
    assert main(["--plain", "handoff", "TASK-2"]) == 0
    assert "traspaso-1" in capsys.readouterr().out


def test_cli_error_de_dominio_conserva_codigo(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    def fallar(*_args, **_kwargs):
        raise ErrorIdentificadorInseguro(
            mensaje="ID inseguro",
            sugerencia="usa letras ASCII",
            ruta=None,
            detalles={"id_tarea": "../x"},
        )

    monkeypatch.setattr("tramalia.cli.comandos.crear_evidencia", fallar)
    assert main(["--plain", "evidence", "../x"]) == 2
    salida = capsys.readouterr().out
    assert "id_tarea_inseguro" in salida
    assert "usa letras ASCII" in salida


def test_cli_cierre_bloqueado_devuelve_uno_sin_recalcular(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    resultado = ResultadoCierre(
        estado=ValorEstadoCierre.BLOQUEADO,
        id_tarea="TASK-3",
        id_paquete="paquete-3",
        ruta_paquete=tmp_path / "paquete-3",
        ruta_traspaso=None,
        ejecucion=EjecucionPuertas(estado=ValorEstadoPuertas.SIN_CONFIGURAR),
        excepciones=(),
        bloqueos=("sin_configurar",),
    )
    monkeypatch.setattr("tramalia.cli.comandos.cerrar_proyecto", lambda *_a, **_k: resultado)
    assert main(["--plain", "close", "TASK-3"]) == 1


def test_alias_allow_fail_sin_campos_es_rechazado_antes_de_operar(tmp_path, monkeypatch) -> None:
    llamado = False

    def cerrar(*_args, **_kwargs):
        nonlocal llamado
        llamado = True

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("tramalia.cli.comandos.cerrar_proyecto", cerrar)
    assert main(["--plain", "close", "TASK-4", "--allow-fail"]) == 2
    assert not llamado
```

- [ ] **Step 2: Ejecutar el contrato y observar que aún importa el módulo inglés**

Run: `uv run pytest tests/contratos/test_operaciones_superficies.py -q`

Expected: FAIL al resolver `tramalia.cli.comandos`.

- [ ] **Step 3: Renombrar CLI y mantener sólo los comandos públicos existentes en inglés**

Ejecutar `git mv tramalia/cli/commands.py tramalia/cli/comandos.py` y `git mv tramalia/cli/render.py tramalia/cli/renderizado.py`. En `__main__.py`, renombrar `build_parser → construir_parser`, importar `renderizado`, llamar `renderizado.fijar_plano(True)` y terminar con `return comandos.despachar(argumentos.command or "menu", argumentos)`.

Aplicar este mapa interno completo: `dispatch → despachar`, `cmd_doctor → comando_doctor`, `cmd_detect → comando_detectar`, `cmd_init → comando_inicializar`, `cmd_upgrade → comando_actualizar_proyecto`, `cmd_gates → comando_puertas`, `cmd_context → comando_contexto`, `cmd_agents → comando_agentes`, `cmd_evidence → comando_evidencia`, `cmd_handoff → comando_traspaso`, `cmd_close → comando_cerrar`, `cmd_log → comando_bitacora`, `cmd_sync → comando_sincronizar`, `cmd_skills → comando_habilidades`, `cmd_update → comando_actualizar`, `cmd_mcp → comando_mcp`, `cmd_ui → comando_interfaz`. El diccionario de despacho conserva las claves públicas `doctor`, `detect`, `init`, `upgrade`, `gates`, `context`, `agents`, `evidence`, `handoff`, `close`, `log`, `sync`, `skills`, `update`, `mcp`, `ui`.

En `renderizado.py`, renombrar `set_plain → fijar_plano`, `header → cabecera`, `info → informar`, `warn → advertir`, `err → error`, `ok → exito`, `group_of → grupo_de`, `group_statuses → agrupar_estados`. Añadir:

```python
def renderizar_error(error_dominio: ErrorTramalia) -> None:
    """Render a stable domain error without exposing an implementation traceback."""
    error(f"[{error_dominio.codigo}] {error_dominio.mensaje}")
    informar(error_dominio.sugerencia)
    if error_dominio.ruta is not None:
        informar(f"ruta: {error_dominio.ruta}")
```

- [ ] **Step 4: Conservar y migrar los campos de excepción razonada del parser**

Al renombrar la CLI, conservar exactamente el único juego de flags definido por el plan 02 después de `--allow-fail`; eliminar cualquier alias interno inglés que no sea el comando público establecido:

```python
cl.add_argument("--razon-excepcion", default="")
cl.add_argument("--riesgo-aceptado", default="")
cl.add_argument("--control-afectado", default="")
cl.add_argument("--referencia-excepcion", default="")
cl.add_argument("--revisor-excepcion", default="")
cl.add_argument("--expira-en", default="", help="fecha ISO 8601 de expiración")
cl.add_argument("--condicion-remediacion", default="")
```

En `comandos.py` implementar:

```python
_CODIGO_SALIDA_ERROR = {
    "proyecto_no_gobernado": 2,
    "configuracion_puertas_invalida": 2,
    "configuracion_metricas_invalida": 2,
    "id_tarea_inseguro": 2,
    "excepcion_invalida": 2,
    "persistencia_evidencia_fallida": 1,
}


def construir_excepciones(argumentos, revisor_predeterminado: str) -> tuple[ExcepcionFallo, ...]:
    """Build the deprecated allow-fail alias as one fully reasoned exception."""
    if not getattr(argumentos, "allow_fail", False):
        return ()
    expiracion_texto = getattr(argumentos, "expira_en", "").strip()
    try:
        expiracion = datetime.fromisoformat(expiracion_texto) if expiracion_texto else None
    except ValueError as error_fecha:
        raise ErrorExcepcionInvalida(
            mensaje="La expiración no es ISO 8601.",
            sugerencia="Usa --expira-en 2026-08-01T00:00:00+00:00.",
            ruta=None,
            detalles={"expira_en": expiracion_texto},
        ) from error_fecha
    datos = {
        "razon": getattr(argumentos, "razon_excepcion", "").strip(),
        "riesgo_aceptado": getattr(argumentos, "riesgo_aceptado", "").strip(),
        "control_afectado": getattr(argumentos, "control_afectado", "").strip(),
        "referencia": getattr(argumentos, "referencia_excepcion", "").strip(),
        "revisor": getattr(argumentos, "revisor_excepcion", "").strip() or revisor_predeterminado,
    }
    faltantes = tuple(nombre for nombre, valor in datos.items() if not valor)
    condicion = getattr(argumentos, "condicion_remediacion", "").strip() or None
    if faltantes or (expiracion is None and condicion is None):
        raise ErrorExcepcionInvalida(
            mensaje="--allow-fail requiere una excepción completa.",
            sugerencia="Completa razón, riesgo, control, referencia, revisor y expiración o remediación.",
            ruta=None,
            detalles={"faltantes": faltantes, "requiere_vigencia": expiracion is None and condicion is None},
        )
    return (ExcepcionFallo(**datos, expira_en=expiracion, condicion_remediacion=condicion),)


def _capturar_error(operacion: Callable[[], int]) -> int:
    try:
        return operacion()
    except ErrorTramalia as error_dominio:
        renderizado.renderizar_error(error_dominio)
        return _CODIGO_SALIDA_ERROR.get(error_dominio.codigo, 1)
```

La CLI valida sólo que el alias deprecado traiga su estructura mínima antes de invocar la operación. `cerrar_proyecto()` vuelve a validar contenido, vigencia y correspondencia con cada bloqueo; esa política no se replica en la superficie.

- [ ] **Step 5: Reemplazar los tres handlers mutantes por operaciones compartidas**

```python
def comando_evidencia(argumentos) -> int:
    raiz = Path.cwd()
    id_tarea, agente, revisor = _resolver(argumentos)
    paquete = crear_evidencia(raiz, id_tarea, agente=agente, revisor=revisor)
    renderizado.exito(f"paquete de evidencia creado: {paquete.ruta.relative_to(raiz)}")
    return 0


def comando_traspaso(argumentos) -> int:
    raiz = Path.cwd()
    id_tarea, agente, revisor = _resolver(argumentos)
    paquete = registrar_traspaso(raiz, id_tarea, agente=agente, revisor=revisor)
    renderizado.exito(f"traspaso registrado en paquete: {paquete.id_paquete}")
    return 0


def comando_cerrar(argumentos) -> int:
    raiz = Path.cwd()
    id_tarea, agente, revisor = _resolver(argumentos)
    resultado = cerrar_proyecto(
        raiz,
        id_tarea,
        agente=agente,
        revisor=revisor,
        modelo=getattr(argumentos, "model", None) or "",
        excepciones=construir_excepciones(argumentos, revisor),
    )
    renderizado.resultado_cierre(resultado)
    return 0 if resultado.aprobado else 1
```

Eliminar `_require_init`; la única guardia mutante es `exigir_proyecto_gobernado()` dentro de operaciones. `comando_puertas` usa `cargar_puertas()` y `ejecutar_puertas()`; `comando_contexto` usa `construir_contexto()`; `comando_habilidades` usa `sincronizar_habilidades()` y devuelve 1 para `fallido` o `git_no_instalado`. Ningún handler importa `governance`, `evidence` o `handoff` históricos.

- [ ] **Step 6: Ejecutar contratos CLI y regresión de parser**

Run: `uv run pytest tests/contratos/test_operaciones_superficies.py tests/test_comandos_simples.py tests/test_v012.py tests/test_v023.py tests/test_v024.py tests/test_v025.py tests/test_v031.py -q`

Expected: PASS; comandos públicos conservan nombres y errores de dominio retornan 1 o 2, nunca traceback.

- [ ] **Step 7: Verificar ausencia de módulos CLI ingleses y correr suite**

Run: `rg -n "tramalia\.cli\.(commands|render)|from tramalia\.cli import (commands|render)" tramalia tests`

Expected: sin salida.

Run: `uv run pytest -q`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add tramalia/__main__.py tramalia/cli/comandos.py tramalia/cli/renderizado.py tramalia/cli/menu.py tests
git commit -m "refactor: delegar cli en operaciones compartidas"
```

### Task 4: MCP real, ServicioTablero, TUI pública y jobs opcionales

**Files:**
- Modify: `tramalia/mcp_server.py`
- Create: `tramalia/core/tablero.py`
- Create: `tramalia/interfaz_terminal.py`
- Delete: `tramalia/tui.py`
- Modify: `tramalia/cli/comandos.py`
- Modify: `tramalia/i18n/es.json`
- Modify: `tramalia/i18n/en.json`
- Create: `tests/integracion/test_mcp_operaciones.py`
- Create: `tests/unidad/test_tablero.py`
- Create: `tests/interfaz/test_interfaz_terminal.py`
- Create: `tests/contratos/test_nombres_espanol.py`
- Modify: `.github/workflows/validacion.yml`
- Modify: tests históricos que importan `tramalia.tui`

**Interfaces:**
- Consumes: todas las operaciones y modelos declarados en “Dependencias y contratos consumidos del plan 02”, `sincronizar_habilidades()`, `consultar_habilidades()`, `construir_contexto()`, `diagnose()`, `inspeccionar_estado_proyecto()`, `cargar_puertas()` y `proveedor_contexto()`.
- Produces: tools MCP `record_handoff`, `build_evidence` y `cerrar_proyecto`; `InstantaneaTablero`, `ServicioTablero`, `construir_aplicacion(servicio: ServicioTablero | None = None)` y `ejecutar()`.

- [ ] **Step 1: Escribir una prueba MCP por transporte público real**

```python
# tests/integracion/test_mcp_operaciones.py
import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("mcp")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def _invocar(nombre: str, argumentos: dict[str, object], raiz: Path) -> dict[str, object]:
    raiz_codigo = Path(__file__).parents[2]
    parametros = StdioServerParameters(
        command=sys.executable,
        args=["-m", "tramalia.mcp_server"],
        env={**os.environ, "PYTHONPATH": str(raiz_codigo)},
        cwd=str(raiz),
    )
    async with stdio_client(parametros) as (lector, escritor):
        async with ClientSession(lector, escritor) as sesion:
            await sesion.initialize()
            resultado = await sesion.call_tool(nombre, argumentos)
    return json.loads(resultado.content[0].text)


@pytest.mark.integracion
@pytest.mark.opcional
def test_herramienta_mcp_evidencia_sin_inicializar_devuelve_error_tipado(tmp_path: Path) -> None:
    respuesta = asyncio.run(_invocar("build_evidence", {"task": "TASK-1"}, tmp_path))
    assert respuesta["ok"] is False
    assert respuesta["error"]["codigo"] == "proyecto_no_gobernado"


@pytest.mark.integracion
@pytest.mark.opcional
def test_herramienta_mcp_real_crea_evidencia_via_operacion(proyecto_listo: Path) -> None:
    respuesta = asyncio.run(
        _invocar("build_evidence", {"task": "TASK-2"}, proyecto_listo)
    )
    assert respuesta["ok"] is True
    ruta = proyecto_listo / respuesta["resultado"]["ruta"]
    assert ruta.is_dir()
    assert json.loads((ruta / "metadatos.json").read_text(encoding="utf-8"))["id_tarea"] == "TASK-2"
```

- [ ] **Step 2: Ejecutar MCP y verificar que el test de ejecución falla con respuestas de texto antiguas**

Run: `uv run pytest tests/integracion/test_mcp_operaciones.py -q`

Expected: FAIL porque `build_evidence` aún llama directamente al writer histórico y no devuelve `{ok, resultado|error}`.

- [ ] **Step 3: Convertir MCP en adaptador de operaciones con JSON seguro**

En `mcp_server.py`, mantener los nombres MCP existentes impuestos por compatibilidad, añadir `cerrar_proyecto` y reemplazar imports de `context`, `evidence` y `handoff` por `contexto` y `operaciones`. Usar:

```python
def _valor_publico(valor: object) -> object:
    if is_dataclass(valor):
        return {campo.name: _valor_publico(getattr(valor, campo.name)) for campo in fields(valor)}
    if isinstance(valor, Path):
        try:
            return valor.relative_to(Path.cwd()).as_posix()
        except ValueError:
            return str(valor)
    if isinstance(valor, datetime):
        return valor.isoformat()
    if isinstance(valor, Mapping):
        return {str(clave): _valor_publico(dato) for clave, dato in valor.items()}
    if isinstance(valor, (tuple, list)):
        return [_valor_publico(dato) for dato in valor]
    return valor


def _respuesta(operacion: Callable[[], object]) -> dict[str, object]:
    try:
        return {"ok": True, "resultado": _valor_publico(operacion())}
    except ErrorTramalia as error_dominio:
        return {"ok": False, "error": _valor_publico(error_dominio.como_dict())}
```

Registrar las mutaciones así:

```python
@servidor.tool(name="record_handoff")
def registrar_traspaso_mcp(task: str, agent: str = "", reviewer: str = "") -> dict[str, object]:
    """Create a canonical handoff pack and update its global projection."""
    return _respuesta(lambda: registrar_traspaso(Path.cwd(), task, agente=agent, revisor=reviewer))


@servidor.tool(name="build_evidence")
def construir_evidencia(task: str = "TASK-000") -> dict[str, object]:
    """Create a formal evidence pack without claiming an approved close."""
    return _respuesta(lambda: crear_evidencia(Path.cwd(), task))


@servidor.tool(name="cerrar_proyecto")
def cerrar(
    id_tarea: str,
    agente: str = "",
    revisor: str = "",
    modelo: str = "",
    razon_excepcion: str = "",
    riesgo_aceptado: str = "",
    control_afectado: str = "",
    referencia_excepcion: str = "",
    revisor_excepcion: str = "",
    expira_en: str = "",
    condicion_remediacion: str = "",
) -> dict[str, object]:
    """Close a governed task with the same policy used by CLI and TUI."""
    def operacion() -> ResultadoCierre:
        excepciones: tuple[ExcepcionFallo, ...] = ()
        campos = (
            razon_excepcion, riesgo_aceptado, control_afectado,
            referencia_excepcion, revisor_excepcion, expira_en,
            condicion_remediacion,
        )
        if any(campos):
            try:
                expiracion = datetime.fromisoformat(expira_en) if expira_en else None
            except ValueError as error_fecha:
                raise ErrorExcepcionInvalida(
                    "La expiración MCP no es ISO 8601.",
                    "Usa una fecha con zona horaria o una condición de remediación.",
                    detalles={"expira_en": expira_en},
                ) from error_fecha
            excepciones = (ExcepcionFallo(
                razon_excepcion,
                riesgo_aceptado,
                control_afectado,
                referencia_excepcion,
                revisor_excepcion or revisor,
                expiracion,
                condicion_remediacion or None,
            ),)
        return cerrar_proyecto(
            Path.cwd(), id_tarea, agente=agente, revisor=revisor,
            modelo=modelo, excepciones=excepciones,
        )

    return _respuesta(operacion)
```

Añadir al test por transporte una invocación de `cerrar_proyecto` con sólo `razon_excepcion`; debe devolver `ok=false` y `error.codigo="excepcion_invalida"`, demostrando que los campos no desaparecen en la fachada. Renombrar la factory propia `build_server → construir_servidor` y `run → ejecutar`; actualizar `tramalia mcp` y tests. Los nombres de tools MCP y sus argumentos heredados (`task`, `agent`, `reviewer`) permanecen en inglés por ser interfaz pública establecida; los campos nuevos propios se publican en español ASCII.

- [ ] **Step 4: Escribir el contrato unitario de snapshot y delegación**

```python
# tests/unidad/test_tablero.py
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from tramalia.core.modelos import (
    EjecucionPuertas,
    EstadoProyecto,
    ResultadoCierre,
    ValorEstadoCierre,
    ValorEstadoProyecto,
    ValorEstadoPuertas,
)
from tramalia.core.tablero import InstantaneaTablero, ServicioTablero


def test_instantanea_es_inmutable(tmp_path: Path) -> None:
    instantanea = InstantaneaTablero.vacia(
        tmp_path, EstadoProyecto(ValorEstadoProyecto.AUSENTE, tmp_path)
    )
    with pytest.raises(FrozenInstanceError):
        instantanea.id_tarea = "TASK-1"  # type: ignore[misc]


def test_servicio_cerrar_delega_sin_recalcular(tmp_path: Path) -> None:
    esperado = ResultadoCierre(
        estado=ValorEstadoCierre.BLOQUEADO,
        id_tarea="TASK-1",
        id_paquete=None,
        ruta_paquete=None,
        ruta_traspaso=None,
        ejecucion=EjecucionPuertas(estado=ValorEstadoPuertas.SIN_CONFIGURAR),
        excepciones=(),
        bloqueos=("sin_configurar",),
    )
    llamadas: list[tuple[Path, str]] = []
    servicio = ServicioTablero(
        tmp_path,
        operacion_cerrar=lambda raiz, id_tarea, **_k: llamadas.append((raiz, id_tarea)) or esperado,
    )
    assert servicio.cerrar("TASK-1") is esperado
    assert llamadas == [(tmp_path, "TASK-1")]
```

- [ ] **Step 5: Implementar `InstantaneaTablero` y `ServicioTablero`**

```python
# tramalia/core/tablero.py
"""Provide immutable dashboard snapshots and shared operations for Textual."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from tramalia.core import doctor
from tramalia.core.configuracion import (
    agentes_predeterminados,
    id_tarea_actual,
    proveedor_contexto,
)
from tramalia.core.detect import detect_stack
from tramalia.core.errores import ErrorTramalia
from tramalia.core.evidencia import leer_bitacora
from tramalia.core.habilidades import (
    ResolucionHabilidad,
    ResultadoSincronizacionHabilidades,
    consultar_habilidades,
    sincronizar_habilidades,
)
from tramalia.core.modelos import (
    EntradaBitacora,
    EstadoIntegracion,
    EstadoProyecto,
    ExcepcionFallo,
    ResultadoCierre,
    ValorEstadoIntegracion,
)
from tramalia.core.operaciones import cerrar_proyecto
from tramalia.core.proyecto import inspeccionar_estado_proyecto
from tramalia.core.puertas_calidad import cargar_puertas


@dataclass(frozen=True, slots=True)
class HerramientaTablero:
    comando: str
    proposito: str
    estado: str
    detalle: str


@dataclass(frozen=True, slots=True)
class InstantaneaTablero:
    """Contain all immutable data needed to render one dashboard frame."""

    raiz: Path
    proyecto: EstadoProyecto
    tecnologias: tuple[str, ...]
    puertas: tuple[str, ...]
    herramientas: tuple[HerramientaTablero, ...]
    habilidades: tuple[ResolucionHabilidad, ...]
    bitacora: tuple[EntradaBitacora, ...]
    integraciones: tuple[EstadoIntegracion, ...]
    id_tarea: str | None
    agente: str
    revisor: str
    proveedor_contexto: str

    @classmethod
    def vacia(cls, raiz: Path, proyecto: EstadoProyecto) -> InstantaneaTablero:
        """Create a renderable snapshot when no optional data is available."""
        return cls(raiz, proyecto, (), (), (), (), (), (), None, "", "", "serena")


class ServicioTablero:
    """Obtain dashboard snapshots and execute shared core operations."""

    def __init__(
        self,
        raiz: Path,
        *,
        operacion_cerrar: Callable[..., ResultadoCierre] = cerrar_proyecto,
    ) -> None:
        self.raiz = raiz
        self._operacion_cerrar = operacion_cerrar

    def obtener_instantanea(self) -> InstantaneaTablero:
        proyecto = inspeccionar_estado_proyecto(self.raiz)
        reporte = doctor.diagnose(self.raiz)
        agente, revisor = agentes_predeterminados(self.raiz)
        integraciones: list[EstadoIntegracion] = []
        try:
            puertas = tuple(p.nombre for p in cargar_puertas(self.raiz))
        except ErrorTramalia as error_dominio:
            puertas = ()
            integraciones.append(EstadoIntegracion(
                ValorEstadoIntegracion.FALLIDO, "puertas_calidad", "mise", "mise",
                error_dominio.codigo, "no se puede cerrar", error_dominio.sugerencia,
            ))
        herramientas = tuple(
            HerramientaTablero(
                estado.herramienta.comando,
                estado.herramienta.rol,
                "completo" if estado.presente else "no_disponible",
                estado.version or estado.herramienta.sugerencia_instalacion,
            )
            for estado in reporte.statuses
        )
        return InstantaneaTablero(
            raiz=self.raiz,
            proyecto=proyecto,
            tecnologias=tuple(detect_stack(self.raiz)),
            puertas=puertas,
            herramientas=herramientas,
            habilidades=consultar_habilidades(self.raiz),
            bitacora=tuple(leer_bitacora(self.raiz)),
            integraciones=tuple(integraciones),
            id_tarea=id_tarea_actual(self.raiz),
            agente=agente,
            revisor=revisor,
            proveedor_contexto=proveedor_contexto(self.raiz),
        )

    def cerrar(
        self,
        id_tarea: str,
        *,
        agente: str = "",
        revisor: str = "",
        modelo: str = "",
        excepciones: Sequence[ExcepcionFallo] = (),
    ) -> ResultadoCierre:
        return self._operacion_cerrar(
            self.raiz, id_tarea, agente=agente, revisor=revisor,
            modelo=modelo, excepciones=excepciones,
        )

    def sincronizar_habilidades(
        self, solo: str | None = None, *, actualizar: bool = False,
    ) -> ResultadoSincronizacionHabilidades:
        return sincronizar_habilidades(self.raiz, solo, actualizar=actualizar)
```

- [ ] **Step 6: Escribir tests Textual sólo con `run_test()` y `pilot` públicos**

```python
# tests/interfaz/test_interfaz_terminal.py
import asyncio
from pathlib import Path

import pytest

pytest.importorskip("textual")

from tramalia.core.modelos import (
    EntradaBitacora,
    EjecucionPuertas,
    EstadoIntegracion,
    EstadoProyecto,
    ExcepcionFallo,
    ResultadoCierre,
    ValorEstadoBitacora,
    ValorEstadoCierre,
    ValorEstadoIntegracion,
    ValorEstadoProyecto,
    ValorEstadoPuertas,
)
from tramalia.core.tablero import InstantaneaTablero
from tramalia.interfaz_terminal import construir_aplicacion


def resultado_cierre_falso(id_tarea: str) -> ResultadoCierre:
    return ResultadoCierre(
        estado=ValorEstadoCierre.BLOQUEADO,
        id_tarea=id_tarea,
        id_paquete=None,
        ruta_paquete=None,
        ruta_traspaso=None,
        ejecucion=EjecucionPuertas(ValorEstadoPuertas.SIN_CONFIGURAR),
        excepciones=(),
        bloqueos=("puertas_sin_configurar",),
    )


class ServicioFalso:
    def __init__(self, instantanea: InstantaneaTablero) -> None:
        self.instantanea = instantanea
        self.llamadas_cierre: list[tuple[str, tuple[ExcepcionFallo, ...]]] = []

    def obtener_instantanea(self) -> InstantaneaTablero:
        return self.instantanea

    def cerrar(
        self,
        id_tarea: str,
        *,
        agente: str = "",
        revisor: str = "",
        modelo: str = "",
        excepciones: tuple[ExcepcionFallo, ...] = (),
    ) -> ResultadoCierre:
        self.llamadas_cierre.append((id_tarea, excepciones))
        return resultado_cierre_falso(id_tarea)


def _instantanea(tmp_path: Path, *, motivo: str = "proceso_agotado") -> InstantaneaTablero:
    entrada = EntradaBitacora(
        id_paquete="paquete-roto", ruta=tmp_path / "paquete-roto",
        estado=ValorEstadoBitacora.INVALIDA,
        id_tarea=None, resultado=None, agente=None, modelo=None, cerrado_utc=None,
        error="archivo metadatos.json corrupto",
    )
    integracion = EstadoIntegracion(
        ValorEstadoIntegracion.FALLIDO, "instalacion", "mise", "mise", motivo,
        "herramienta no instalada", "reintenta o instala manualmente",
    )
    return InstantaneaTablero(
        tmp_path, EstadoProyecto(ValorEstadoProyecto.LISTO, tmp_path),
        ("python",), ("test",), (), (),
        (entrada,), (integracion,), "TASK-1", "codex", "claude", "serena",
    )


@pytest.mark.interfaz
@pytest.mark.opcional
def test_interfaz_muestra_metadatos_invalidos_y_tiempo_agotado(tmp_path: Path) -> None:
    async def escenario() -> None:
        app = construir_aplicacion(ServicioFalso(_instantanea(tmp_path)))
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert "archivo metadatos.json corrupto" in app.query_one("#detalle-log").render().plain
            assert "tiempo agotado" in app.query_one("#estado-integraciones").render().plain.lower()

    asyncio.run(escenario())


@pytest.mark.interfaz
@pytest.mark.opcional
def test_interfaz_distingue_cancelacion_de_degradacion(tmp_path: Path) -> None:
    cancelada = _instantanea(tmp_path, motivo="proceso_cancelado")
    degradada = EstadoIntegracion(
        ValorEstadoIntegracion.DEGRADADO, "memoria", "engram", "archivo_local",
        "alternativa_completada", "sin memoria compartida", "instala engram",
    )
    cancelada = InstantaneaTablero(
        cancelada.raiz, cancelada.proyecto, cancelada.tecnologias, cancelada.puertas,
        cancelada.herramientas, cancelada.habilidades, cancelada.bitacora,
        (cancelada.integraciones[0], degradada), cancelada.id_tarea,
        cancelada.agente, cancelada.revisor, cancelada.proveedor_contexto,
    )
    async def escenario() -> None:
        app = construir_aplicacion(ServicioFalso(cancelada))
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            texto = app.query_one("#estado-integraciones").render().plain.lower()
            assert "cancelada" in texto
            assert "degradada" in texto
            assert "sin memoria compartida" in texto

    asyncio.run(escenario())
```

No llamar `_on_backend_chosen`, `_run_close`, `_show_close_result` ni ningún método privado desde tests. Para acciones, usar `pilot.press()`, `pilot.click()` e inputs por selector.

Añadir `test_interfaz_formulario_excepcion_es_tipado_y_cierre_seguro` usando el helper y el espía mostrados: activar `#permitir-excepcion`, completar primero sólo `#razon-excepcion` y pulsar `#cerrar`; `llamadas_cierre` debe seguir vacío y `#error-cierre` debe mostrar que faltan riesgo, control, referencia, revisor y vigencia. Después completar `#riesgo-aceptado`, `#control-afectado`, `#referencia-excepcion`, `#revisor-excepcion` y `#condicion-remediacion`, volver a pulsar `#cerrar` y esperar el worker; `llamadas_cierre` contiene exactamente una tupla con un `ExcepcionFallo` de esos valores. Usar únicamente widgets obtenidos por selector y la API pública de `pilot`.

Añadir además `test_interfaz_fecha_excepcion_invalida_no_inicia_cierre`: completar todos los campos requeridos, escribir `fecha-no-iso` en `#expira-en` y pulsar `#cerrar`. Debe mostrarse el mensaje tipado de fecha inválida en `#error-cierre`, `llamadas_cierre` debe permanecer vacío y no debe arrancar ningún worker de cierre.

- [ ] **Step 7: Renombrar TUI y retirar orquestación de `build_app()`**

Ejecutar `git mv tramalia/tui.py tramalia/interfaz_terminal.py`; renombrar `build_app → construir_aplicacion`, `TramaliaApp → AplicacionTramalia`, `run → ejecutar`, `action_refresh → action_actualizar` y `_install_worker → _trabajador_instalacion`. Renombrar también el id histórico `#btn-close` a `#cerrar` en el widget, CSS, handlers y pruebas. Actualizar el binding `r` para invocar `actualizar`. Mantener los imports runtime de Textual dentro de `construir_aplicacion()` (y usar `TYPE_CHECKING` para tipos si hace falta), de modo que importar `tramalia` o la CLI sin el extra `tui` siga funcionando. La firma es:

```python
def construir_aplicacion(servicio: ServicioTablero | None = None) -> App:
    """Build the Textual app around an injectable dashboard service."""
    servicio_elegido = servicio if servicio is not None else ServicioTablero(Path.cwd())
    return AplicacionTramalia(servicio_elegido)
```

`AplicacionTramalia.__init__(servicio_tablero: ServicioTablero)` debe llamar a `super().__init__()` y guardar `self._servicio_tablero = servicio_tablero`. No se usa una variable libre ni se crea un segundo servicio dentro de la aplicación. `on_mount()` y el binding `r` sólo programan:

```python
def action_actualizar(self) -> None:
    self.query_one("#estado", Static).update(t("tui.estado.cargando"))
    self.run_worker(
        self._cargar_instantanea,
        thread=True,
        exclusive=True,
        group="instantanea",
    )


def _cargar_instantanea(self) -> None:
    try:
        instantanea = self._servicio_tablero.obtener_instantanea()
    except ErrorTramalia as error_dominio:
        self.call_from_thread(self._mostrar_error, error_dominio)
        return
    self.call_from_thread(self._mostrar_instantanea, instantanea)
```

El panel de cierre incorpora `#permitir-excepcion` y los siete inputs con los mismos IDs de la prueba. `_construir_excepciones_formulario()` devuelve `()` si el switch está apagado; si está encendido, convierte `#expira-en` con `datetime.fromisoformat()` dentro de un bloque `try/except ValueError` que vuelve a lanzar `ErrorExcepcionInvalida(mensaje="La expiracion no es ISO 8601.", sugerencia="Usa una fecha como 2026-08-01T00:00:00+00:00.", detalles={"expira_en": texto_expiracion}) from error_fecha`. Después construye `ExcepcionFallo`, dejando que el modelo común rechace campos incompletos o vigencia inválida. El callback captura `ErrorExcepcionInvalida`, actualiza `#error-cierre` y no inicia el worker; con datos válidos pasa la tupla al método `self._servicio_tablero.cerrar(..., excepciones=excepciones)`.

`_mostrar_instantanea()` es la única función que rellena tablas. Para cada `EntradaBitacora(estado="invalida")`, muestra `error` sin intentar reinterpretar Markdown. Para cada integración muestra estado, capacidad, motivo, impacto y remediación; traduce `proceso_agotado`, `proceso_cancelado`, `alternativa_completada`, `git_tiempo_agotado` y `git_salida_no_cero` mediante i18n. Cierre y sincronización llaman respectivamente `self._servicio_tablero.cerrar()` y `self._servicio_tablero.sincronizar_habilidades()` dentro de `run_worker(thread=True)`; los botones se rehabilitan en callbacks tanto de éxito como de error. Las instalaciones existentes siguen en `_trabajador_instalacion`, que ya corre con `thread=True`; no se mueve ninguna sonda a `compose()`, `on_mount()` ni handlers del event loop.

Actualizar `comando_interfaz` para `from tramalia.interfaz_terminal import ejecutar`. Añadir las claves exactas `tui.estado.cargando`, `tui.integracion.fallida`, `tui.integracion.degradada`, `tui.integracion.tiempo_agotado`, `tui.integracion.cancelada`, `tui.auditoria.invalida` a ambos JSON, con textos naturales español/inglés y los mismos placeholders `{capacidad}`, `{impacto}`, `{remediacion}`.

- [ ] **Step 8: Proteger nombres finales y eliminar módulos ingleses**

```python
# tests/contratos/test_nombres_espanol.py
from importlib import import_module
from pathlib import Path


def test_modulos_finales_en_espanol_y_antiguos_ausentes() -> None:
    raiz = Path(__file__).parents[2]
    nuevos = (
        "tramalia.core.integraciones", "tramalia.core.procesos",
        "tramalia.core.habilidades", "tramalia.core.contexto",
        "tramalia.core.proveedor_contexto", "tramalia.core.configuracion",
        "tramalia.core.tablero",
        "tramalia.cli.comandos", "tramalia.cli.renderizado",
        "tramalia.interfaz_terminal",
    )
    for modulo in nuevos:
        import_module(modulo)
    assert (raiz / "tramalia/templates/project/.tramalia/habilidades.toml").is_file()
    assert (raiz / "tramalia/templates/project/.tramalia/habilidades").is_dir()
    antiguos = (
        "tramalia/core/tools.py", "tramalia/core/proc.py", "tramalia/core/skills.py",
        "tramalia/core/context.py", "tramalia/core/context_backend.py", "tramalia/core/project.py",
        "tramalia/cli/commands.py", "tramalia/cli/render.py", "tramalia/tui.py",
        "tramalia/templates/project/.tramalia/skills.toml",
        "tramalia/templates/project/.tramalia/skills",
    )
    assert all(not (raiz / ruta).exists() for ruta in antiguos)
```

Run: `rg -n "tramalia\.(tui|core\.(tools|proc|skills|context|context_backend|project)|cli\.(commands|render))" tramalia tests`

Expected: sin salida.

- [ ] **Step 9: Ampliar `validacion.yml` con plataformas y opcionales**

Añadir `uv run --no-sync mypy tramalia` al final del job `calidad` y reemplazar en ese mismo job la sincronización por `uv sync --locked --group desarrollo --extra tui --extra mcp`: mypy analiza todo `tramalia`, por lo que Textual y MCP deben estar instalados aunque sus pruebas vivan también en el job `opcionales`. Antes de editar el workflow, ejecutar `uv sync --locked --group desarrollo --extra tui --extra mcp` y luego `uv run --no-sync mypy tramalia`; corregir todos los errores reales en los módulos tocados por los planes 02/03, sin `ignore_errors`, `Any` masivo ni exclusiones de paquetes propios. Marcar también todas las regresiones históricas que importen MCP o Textual con `opcional` y, según corresponda, `integracion` o `interfaz`; comprobar con `uv run pytest --collect-only -m "opcional or interfaz"` que no sólo se seleccionan los tests nuevos. Añadir además al nivel `jobs` del workflow creado por el plan 01:

```yaml
  plataformas:
    name: integración / ${{ matrix.os }} / py3.11
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0
        with:
          python-version: "3.11"
      - uses: astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990 # v8.3.2
        with:
          version: "0.11.28"
          enable-cache: true
      - run: uv sync --locked --group desarrollo
      - run: uv run --no-sync pytest -m integracion -q

  opcionales:
    name: TUI y MCP / py${{ matrix.python-version }}
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.14"]
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0
        with:
          python-version: ${{ matrix.python-version }}
      - uses: astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990 # v8.3.2
        with:
          version: "0.11.28"
          enable-cache: true
      - run: uv sync --locked --group desarrollo --extra tui --extra mcp
      - run: uv run --no-sync pytest -m "opcional or interfaz" -q
```

Usar los mismos SHA completos en los cinco jobs; no introducir tags flotantes.

- [ ] **Step 10: Ejecutar verificación pública completa**

Run: `uv run pytest tests/unidad/test_tablero.py tests/integracion/test_mcp_operaciones.py tests/interfaz/test_interfaz_terminal.py tests/contratos/test_nombres_espanol.py -q`

Expected: PASS; los tests MCP/TUI se ejecutan con extras y sólo se omiten en una instalación deliberadamente mínima.

Run: `uv run pytest -q`

Expected: PASS.

Run: `uv run pytest -m integracion -q`

Expected: PASS en Windows, Linux y macOS; Git local no usa red.

Run: `uv run pytest -m "opcional or interfaz" -q`

Expected: PASS con `.[dev,tui,mcp]`.

Run: `uv run --no-sync mypy tramalia`

Expected: PASS sin errores ni nuevas exclusiones de código propio.

Run: `uv run ruff check . --fix && uv run ruff format . && uv run ruff check . && uv run ruff format --check .`

Expected: PASS sin imports tardíos/sin usar ni incumplimientos de formato.

- [ ] **Step 11: Commit**

```bash
git add tramalia/mcp_server.py tramalia/core/tablero.py tramalia/interfaz_terminal.py tramalia/cli/comandos.py tramalia/i18n/es.json tramalia/i18n/en.json tests .github/workflows/validacion.yml
git commit -m "feat: separar superficies y servicio tui"
```

## Verificación final de aceptación

- [ ] CLI, TUI y MCP invocan `cerrar_proyecto`, `crear_evidencia` o `registrar_traspaso`; ninguna superficie importa writers o política histórica.
- [ ] Un proceso no cero queda `fallido`; sólo un fallback que terminó con código cero queda `degradado`.
- [ ] Cada resolución de skill conserva `fuente`, `referencia` y `sha_resuelto`; Team nunca ejecuta `pull` ni instala `latest`.
- [ ] Clone/pull no cero, timeout y ref inválida no mueven `habilidades.lock.json` ni se presentan como éxito.
- [ ] `InstantaneaTablero` es inmutable y toda sonda, cierre, sync o instalación se ejecuta en un worker con hilo.
- [ ] Metadata corrupta, cancelación, timeout y degradación aparecen como estados distintos en tests públicos `pilot`.
- [ ] Los módulos finales propios usan español ASCII y los ocho módulos ingleses retirados no existen ni se importan.
- [ ] `plataformas` ejecuta integración en Windows/Linux/macOS y `opcionales` ejecuta TUI/MCP en Python 3.11 y 3.14.
- [ ] Los docstrings públicos nuevos están en inglés, estilo Google; los comentarios internos explican invariantes en español.

Plan complete and saved to `docs/superpowers/plans/2026-07-12-03-integraciones-superficies-tui.md`.
