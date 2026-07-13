# Núcleo, Puertas y Evidencia Formal v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir un núcleo fail-closed único para estado de proyecto, puertas, excepciones, cierre, evidencia formal v1 y traspaso, consumible sin recalcular política desde CLI, TUI o MCP.

**Architecture:** Modelos de dominio inmutables y errores estables separan política de presentación. `operaciones.py` orquesta la guardia de proyecto, `puertas_calidad.py`, `politica_cierre.py` y el writer transaccional de `evidencia.py`; cada pack contiene el traspaso canónico y la bitácora sólo interpreta `metadatos.json` v1. Los módulos históricos en inglés se eliminan después de migrar todos sus consumidores en la misma tarea.

**Tech Stack:** Python 3.11 stdlib (`dataclasses`, `datetime`, `enum.StrEnum`, `hashlib`, `json`, `os`, `pathlib`, `platform`, `secrets`, `subprocess`, `tomllib`, `uuid`), pytest 8.

## Global Constraints

- Python 3.11 será la versión mínima de la BETA.
- La compatibilidad objetivo será Python 3.11, 3.12, 3.13 y 3.14.
- El núcleo debe seguir funcionando sin Node, servicios cloud ni herramientas externas.
- Las integraciones opcionales no serán necesarias para usar el núcleo repo-first.
- No se incorporará una base de datos, event sourcing ni un framework de persistencia.
- No se implementará un lector de compatibilidad para el formato de evidencia previo porque no tiene consumidores externos.
- Las escrituras deben ser seguras en Windows, Linux y macOS.
- Los cambios de comportamiento se implementarán con TDD: test fallando, implementación mínima y refactor posterior.
- Las APIs públicas nuevas deben tener tipos, docstring y pruebas de contrato.
- Los comentarios internos se escribirán en español y explicarán motivos, invariantes y riesgos; no repetirán el código.
- Los docstrings de la API pública se escribirán en inglés y con estilo Google.
- Los nombres propios de archivos, módulos, clases, funciones, métodos, variables, auxiliares de pytest y marcadores se escribirán en español ASCII; `n` sustituirá a `ñ`.
- Se conservarán en inglés únicamente nombres impuestos por Python, GitHub, PyPI, MkDocs, MCP, formatos externos o comandos públicos ya establecidos.
- El éxito se medirá por contratos protegidos, no por mantener una cifra fija de tests.
- Este plan se ejecuta después del plan 01: ya existen `tests/unidad`, `tests/contratos` y `tests/integracion`; este plan mueve allí los tests históricos de gobierno, métricas, evidence y handoff.

---

## File map

- Create `tramalia/core/errores.py`: jerarquía de errores serializable y saneamiento recursivo de detalles.
- Create `tramalia/core/modelos.py`: enums, dataclasses inmutables y contratos compartidos.
- Create `tramalia/core/proyecto.py`: clasificación `listo/heredado/parcial/ausente` y única guardia mutante.
- Create `tramalia/core/puertas_calidad.py`: carga TOML estricta y ejecución de gates.
- Create `tramalia/core/politica_cierre.py`: umbrales, cobertura de excepciones y estado definitivo.
- Create `tramalia/core/evidencia.py`: identidad segura, inventario Git, serialización v1, staging y publicación atómica.
- Create `tramalia/core/traspaso.py`: Markdown canónico dentro del pack y proyección global atómica.
- Create `tramalia/core/operaciones.py`: únicas entradas mutantes públicas.
- Modify `tramalia/core/project.py:16-18`: retirar `is_initialized`; los consumidores pasan a `proyecto.py`.
- Delete `tramalia/core/governance.py:1-257`, `tramalia/core/evidence.py:1-53` y `tramalia/core/handoff.py:1-38` después de migrar todos los imports.
- Modify `tramalia/cli/commands.py:322-430`, `tramalia/mcp_server.py:15-82` y `tramalia/tui.py:27-742`: enrutar provisionalmente a los modelos/operaciones nuevos; el plan 03 separará `ServicioTablero` sin cambiar estos contratos.
- Move and rewrite `tests/test_governance.py`, `tests/test_metadata.py`, `tests/test_evidence_handoff.py`, `tests/test_v016.py`, `tests/test_headroom.py`, `tests/test_speckit_ui.py` y los casos de gobierno de `tests/test_v012.py`, `tests/test_v030.py` y `tests/test_agentes_modelo.py` bajo la arquitectura nueva.

### Task 1: Errores de dominio y modelos inmutables en español ASCII

**Files:**
- Create: `tramalia/core/errores.py`
- Create: `tramalia/core/modelos.py`
- Create: `tests/unidad/test_errores_modelos.py`

**Interfaces:**
- Consumes: sólo tipos stdlib de Python 3.11.
- Produces: `ErrorTramalia.como_dict()`, `EstadoProyecto`, `PuertaCalidad`, `ResultadoPuerta`, `EjecucionPuertas`, `ExcepcionFallo`, `ResultadoCierre`, `MetadatosPaqueteEvidencia`, `PaqueteEvidencia`, `EntradaBitacora` y `EstadoIntegracion` con los campos exactos mostrados en el Step 3.

- [ ] **Step 1: Write the failing contracts for stable errors, required exceptions and integration success**

```python
# tests/unidad/test_errores_modelos.py
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tramalia.core.errores import ErrorExcepcionInvalida, ErrorTramalia
from tramalia.core.modelos import EstadoIntegracion, ExcepcionFallo


def test_error_sanea_secretos_recursivos() -> None:
    class ErrorPrueba(ErrorTramalia):
        codigo = "fallo"

    error = ErrorPrueba(
        mensaje="fallo humano",
        sugerencia="reintenta",
        ruta=Path("mise.toml"),
        detalles={"token": "abc", "git": {"branch": "main", "password": "x"}},
    )
    assert error.como_dict() == {
        "codigo": "fallo",
        "mensaje": "fallo humano",
        "sugerencia": "reintenta",
        "ruta": "mise.toml",
        "detalles": {"token": "[REDACTADO]", "git": {"branch": "main", "password": "[REDACTADO]"}},
    }


def test_excepcion_exige_todos_los_datos_y_remediacion() -> None:
    with pytest.raises(ErrorExcepcionInvalida) as capturada:
        ExcepcionFallo("", "riesgo", "test", "ISSUE-1", "ana")
    assert capturada.value.codigo == "excepcion_invalida"

    excepcion = ExcepcionFallo(
        razon="runner en mantenimiento",
        riesgo_aceptado="la regresion puede detectarse tarde",
        control_afectado="ejecutor",
        referencia="ISSUE-123",
        revisor="ana",
        expira_en=datetime(2026, 7, 13, tzinfo=UTC),
    )
    assert excepcion.vigente(datetime(2026, 7, 12, tzinfo=UTC)) is True


def test_degradado_solo_es_exitoso_con_adaptador_efectivo() -> None:
    with pytest.raises(ValueError, match="utilizado"):
        EstadoIntegracion("degradado", "memoria", "engram", None, "fallback", "sin memoria", "instalar")
    estado = EstadoIntegracion("degradado", "memoria", "engram", "archivo", "fallback", "local", "instalar")
    assert estado.exitoso is True
```

- [ ] **Step 2: Run the contracts and verify missing modules fail**

Run: `uv run pytest tests/unidad/test_errores_modelos.py -q`

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'tramalia.core.errores'`.

- [ ] **Step 3: Implement the complete public error and model contracts**

```python
# tramalia/core/errores.py
"""Domain errors shared by every Tramalia surface."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

_SECRETOS = {"token", "secret", "password", "contrasena", "api_key", "authorization"}


def _sanear(valor: object, clave: str = "") -> object:
    if clave.lower() in _SECRETOS:
        return "[REDACTADO]"
    if isinstance(valor, Mapping):
        return {str(k): _sanear(v, str(k)) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_sanear(elemento) for elemento in valor]
    return valor


class ErrorTramalia(Exception):
    """Represent a stable, recoverable domain failure.

    Args:
        mensaje: Human-readable description.
        sugerencia: Concrete recovery action.
        ruta: Related path, if any.
        detalles: Structured context; secret-looking fields are redacted.
    """

    codigo = "error_tramalia"

    def __init__(self, mensaje: str, sugerencia: str,
                 ruta: Path | None = None,
                 detalles: Mapping[str, object] | None = None) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.sugerencia = sugerencia
        self.ruta = ruta
        self.detalles = _sanear(detalles or {})

    def como_dict(self) -> dict[str, object]:
        """Return a secret-safe representation for CLI, TUI and MCP."""
        return {"codigo": self.codigo, "mensaje": self.mensaje,
                "sugerencia": self.sugerencia,
                "ruta": str(self.ruta) if self.ruta else None,
                "detalles": self.detalles}


class ErrorProyectoNoGobernado(ErrorTramalia):
    codigo = "proyecto_no_gobernado"


class ErrorConfiguracionPuertas(ErrorTramalia):
    codigo = "configuracion_puertas_invalida"


class ErrorConfiguracionMetricas(ErrorTramalia):
    codigo = "configuracion_metricas_invalida"


class ErrorIdentificadorInseguro(ErrorTramalia):
    codigo = "id_tarea_inseguro"


class ErrorExcepcionInvalida(ErrorTramalia):
    codigo = "excepcion_invalida"


class ErrorPersistenciaEvidencia(ErrorTramalia):
    codigo = "persistencia_evidencia_fallida"
```

```python
# tramalia/core/modelos.py
"""Typed domain contracts for Tramalia core operations."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from tramalia.core.errores import ErrorExcepcionInvalida


class ValorEstadoProyecto(StrEnum):
    LISTO = "listo"
    HEREDADO = "heredado"
    PARCIAL = "parcial"
    AUSENTE = "ausente"


class ValorEstadoPuertas(StrEnum):
    APROBADO = "aprobado"
    FALLIDO = "fallido"
    EJECUTOR_NO_DISPONIBLE = "ejecutor_no_disponible"
    SIN_CONFIGURAR = "sin_configurar"
    CONFIGURACION_INVALIDA = "configuracion_invalida"
    ERROR_EJECUCION = "error_ejecucion"


class ValorResultadoPuerta(StrEnum):
    APROBADO = "aprobado"
    FALLIDO = "fallido"
    OMITIDO = "omitido"
    ERROR_EJECUCION = "error_ejecucion"


class ValorEstadoCierre(StrEnum):
    APROBADO = "aprobado"
    APROBADO_CON_EXCEPCIONES = "aprobado_con_excepciones"
    BLOQUEADO = "bloqueado"


class ValorEstadoIntegracion(StrEnum):
    COMPLETO = "completo"
    DEGRADADO = "degradado"
    NO_DISPONIBLE = "no_disponible"
    FALLIDO = "fallido"


class ValorEstadoBitacora(StrEnum):
    VALIDA = "valida"
    INVALIDA = "invalida"


@dataclass(frozen=True, slots=True)
class EstadoProyecto:
    estado: ValorEstadoProyecto
    raiz: Path
    problemas: tuple[str, ...] = ()
    comando_reparacion: str | None = None

    @property
    def listo(self) -> bool:
        return self.estado is ValorEstadoProyecto.LISTO


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

    def __post_init__(self) -> None:
        faltantes = [nombre for nombre in ("razon", "riesgo_aceptado", "control_afectado", "referencia", "revisor")
                     if not str(getattr(self, nombre)).strip()]
        if not self.expira_en and not (self.condicion_remediacion or "").strip():
            faltantes.append("expira_en_o_condicion_remediacion")
        if self.expira_en and self.expira_en.tzinfo is None:
            faltantes.append("expira_en_con_zona_horaria")
        if faltantes:
            raise ErrorExcepcionInvalida("La excepcion no cumple el contrato.",
                                         "Completa razon, riesgo, control, referencia, revisor y expiracion o remediacion.",
                                         detalles={"campos": faltantes})

    def vigente(self, ahora: datetime) -> bool:
        return self.expira_en is None or ahora <= self.expira_en


@dataclass(frozen=True, slots=True)
class EstadoGit:
    commit: str | None
    rama: str | None
    limpio: bool | None
    base_comparacion: str | None
    rastreados: tuple[str, ...] = ()
    preparados: tuple[str, ...] = ()
    no_rastreados: tuple[str, ...] = ()
    renombrados: tuple[str, ...] = ()
    eliminados: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MetadatosPaqueteEvidencia:
    version_esquema: int
    id_paquete: str
    id_tarea: str
    operacion: str
    inicio_utc: datetime
    fin_utc: datetime
    version_tramalia: str
    version_python: str
    sistema_operativo: str
    cadena_herramientas: Mapping[str, str | None]
    git: EstadoGit
    ejecucion: EjecucionPuertas
    estado_cierre: ValorEstadoCierre
    agente: str | None
    modelo: str | None
    metricas: Mapping[str, object]
    umbrales: Mapping[str, object]
    errores_validacion: tuple[str, ...]
    excepciones: tuple[ExcepcionFallo, ...]
    vinculo_traspaso: str


@dataclass(frozen=True, slots=True)
class PaqueteEvidencia:
    id_paquete: str
    ruta: Path
    metadatos: MetadatosPaqueteEvidencia


@dataclass(frozen=True, slots=True)
class ResultadoCierre:
    estado: ValorEstadoCierre
    id_tarea: str
    id_paquete: str | None
    ruta_paquete: Path | None
    ruta_traspaso: Path | None
    ejecucion: EjecucionPuertas
    excepciones: tuple[ExcepcionFallo, ...] = ()
    bloqueos: tuple[str, ...] = ()

    @property
    def aprobado(self) -> bool:
        return self.estado in {ValorEstadoCierre.APROBADO, ValorEstadoCierre.APROBADO_CON_EXCEPCIONES}


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


@dataclass(frozen=True, slots=True)
class EstadoIntegracion:
    estado: ValorEstadoIntegracion
    capacidad: str
    solicitado: str | None
    utilizado: str | None
    motivo: str
    impacto: str
    remediacion: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "estado", ValorEstadoIntegracion(self.estado))
        if self.estado is ValorEstadoIntegracion.DEGRADADO and not self.utilizado:
            raise ValueError("utilizado es obligatorio para un fallback degradado exitoso")

    @property
    def exitoso(self) -> bool:
        return self.estado in {ValorEstadoIntegracion.COMPLETO, ValorEstadoIntegracion.DEGRADADO}
```

- [ ] **Step 4: Run the model contracts**

Run: `uv run pytest tests/unidad/test_errores_modelos.py -q`

Expected: `3 passed`.

- [ ] **Step 5: Commit the domain vocabulary**

```bash
git add tramalia/core/errores.py tramalia/core/modelos.py tests/unidad/test_errores_modelos.py
git commit -m "feat: define modelos y errores del nucleo"
```

### Task 2: Estado de proyecto y guardia mutante única

**Files:**
- Create: `tramalia/core/proyecto.py`
- Create: `tests/unidad/test_proyecto_gobernado.py`
- Modify: `tramalia/core/project.py:16-18`
- Modify: `tramalia/templates/project/AGENTS.md.jinja` (delimitar la convención nueva con `tramalia:gobierno`)
- Modify: `tests/test_convencion_completa.py` (todo proyecto nuevo incluye el marcador)
- Modify: `tests/test_v012.py:34-54` (mover los casos de guardia al archivo nuevo y borrar los originales)
- Modify: `tests/test_v030.py:88` (reemplazar el consumidor TUI de `project.is_initialized` por el estado tipado)

**Interfaces:**
- Consumes: `EstadoProyecto`, `ValorEstadoProyecto`, `ErrorProyectoNoGobernado`.
- Produces: `inspeccionar_estado_proyecto(raiz: Path) -> EstadoProyecto`, `exigir_proyecto_gobernado(raiz: Path) -> EstadoProyecto` y `exigir_proyecto_actualizable(raiz: Path) -> EstadoProyecto`.

- [ ] **Step 1: Write the four-state matrix and mutation guard tests**

```python
# tests/unidad/test_proyecto_gobernado.py
import json

import pytest

from tramalia.core.errores import ErrorProyectoNoGobernado
from tramalia.core.modelos import ValorEstadoProyecto
from tramalia.core.proyecto import (
    exigir_proyecto_actualizable,
    exigir_proyecto_gobernado,
    inspeccionar_estado_proyecto,
)


def _escribir_listo(raiz) -> None:
    (raiz / ".tramalia").mkdir()
    (raiz / ".tramalia" / "config.json").write_text(json.dumps({"projectName": "demo"}), encoding="utf-8")
    (raiz / ".tramalia" / "version").write_text("0.33.0\n", encoding="utf-8")
    (raiz / "AGENTS.md").write_text(
        "<!-- tramalia:gobierno inicio -->\ntramalia close\n<!-- tramalia:gobierno fin -->\n",
        encoding="utf-8",
    )
    (raiz / "mise.toml").write_text("[tasks.test]\nrun = \"pytest\"\n", encoding="utf-8")


def test_distingue_ausente_heredado_parcial_y_listo(tmp_path) -> None:
    assert inspeccionar_estado_proyecto(tmp_path).estado is ValorEstadoProyecto.AUSENTE
    (tmp_path / ".tramalia").mkdir()
    assert inspeccionar_estado_proyecto(tmp_path).estado is ValorEstadoProyecto.PARCIAL
    (tmp_path / ".tramalia" / "config.json").write_text(
        json.dumps({"projectName": "demo"}), encoding="utf-8",
    )
    (tmp_path / "AGENTS.md").write_text("tramalia close", encoding="utf-8")
    (tmp_path / "mise.toml").write_text("[tasks.test]\nrun='pytest'", encoding="utf-8")
    assert inspeccionar_estado_proyecto(tmp_path).estado is ValorEstadoProyecto.HEREDADO
    (tmp_path / ".tramalia" / "version").write_text("0.33.0", encoding="utf-8")
    assert inspeccionar_estado_proyecto(tmp_path).estado is ValorEstadoProyecto.HEREDADO
    (tmp_path / "AGENTS.md").write_text(
        "<!-- tramalia:gobierno inicio -->\ntramalia close\n<!-- tramalia:gobierno fin -->\n",
        encoding="utf-8",
    )
    assert inspeccionar_estado_proyecto(tmp_path).estado is ValorEstadoProyecto.LISTO


@pytest.mark.parametrize("marcador", ["agentes", "directorio"])
def test_marcador_aislado_no_habilita_mutaciones(tmp_path, marcador) -> None:
    if marcador == "agentes":
        (tmp_path / "AGENTS.md").write_text("reglas", encoding="utf-8")
    else:
        (tmp_path / ".tramalia").mkdir()
    with pytest.raises(ErrorProyectoNoGobernado) as capturada:
        exigir_proyecto_gobernado(tmp_path)
    assert capturada.value.codigo == "proyecto_no_gobernado"


def test_configuracion_json_invalida_es_parcial(tmp_path) -> None:
    _escribir_listo(tmp_path)
    (tmp_path / ".tramalia" / "config.json").write_text("{", encoding="utf-8")
    estado = inspeccionar_estado_proyecto(tmp_path)
    assert estado.estado is ValorEstadoProyecto.PARCIAL
    assert "config.json invalido" in estado.problemas


def test_configuracion_vacia_es_parcial(tmp_path) -> None:
    _escribir_listo(tmp_path)
    (tmp_path / ".tramalia" / "config.json").write_text("{}", encoding="utf-8")
    estado = inspeccionar_estado_proyecto(tmp_path)
    assert estado.estado is ValorEstadoProyecto.PARCIAL
    assert "config.json sin projectName valido" in estado.problemas


def test_archivo_agentes_sin_contrato_de_cierre_es_parcial(tmp_path) -> None:
    _escribir_listo(tmp_path)
    (tmp_path / "AGENTS.md").write_text("reglas locales", encoding="utf-8")
    estado = inspeccionar_estado_proyecto(tmp_path)
    assert estado.estado is ValorEstadoProyecto.PARCIAL
    assert "AGENTS.md sin contrato tramalia close" in estado.problemas


@pytest.mark.parametrize("contenido", [
    "<!-- tramalia:gobierno inicio -->\ntramalia close\n",
    "tramalia close\n<!-- tramalia:gobierno fin -->\n",
    "<!-- tramalia:gobierno fin -->\ntramalia close\n<!-- tramalia:gobierno inicio -->\n",
    "tramalia:gobierno\ntramalia close\n",
    "<!-- tramalia:gobierno inicio -->\n<!-- tramalia:gobierno fin -->\ntramalia close\n",
    "tramalia close\n<!-- tramalia:gobierno inicio -->\ntexto\n<!-- tramalia:gobierno fin -->\n",
])
def test_marcadores_de_gobierno_incompletos_o_desordenados_no_estan_listos(
    tmp_path, contenido,
) -> None:
    _escribir_listo(tmp_path)
    (tmp_path / "AGENTS.md").write_text(contenido, encoding="utf-8")
    assert inspeccionar_estado_proyecto(tmp_path).estado is ValorEstadoProyecto.PARCIAL


def test_mencion_previa_no_invalida_un_bloque_gobernado_correcto(tmp_path) -> None:
    _escribir_listo(tmp_path)
    (tmp_path / "AGENTS.md").write_text(
        "Referencia historica a tramalia close.\n"
        "<!-- tramalia:gobierno inicio -->\n"
        "Cierre obligatorio: tramalia close --task TASK-1\n"
        "<!-- tramalia:gobierno fin -->\n",
        encoding="utf-8",
    )
    assert inspeccionar_estado_proyecto(tmp_path).estado is ValorEstadoProyecto.LISTO


def test_mise_invalido_se_delega_al_cargador_de_puertas(tmp_path) -> None:
    _escribir_listo(tmp_path)
    (tmp_path / "mise.toml").write_text("[tasks", encoding="utf-8")
    assert inspeccionar_estado_proyecto(tmp_path).estado is ValorEstadoProyecto.LISTO


def test_upgrade_acepta_heredado_y_rechaza_ausente(tmp_path) -> None:
    _escribir_listo(tmp_path)
    (tmp_path / ".tramalia" / "version").unlink()
    assert exigir_proyecto_actualizable(tmp_path).estado is ValorEstadoProyecto.HEREDADO
    with pytest.raises(ErrorProyectoNoGobernado):
        exigir_proyecto_actualizable(tmp_path / "ausente")
```

- [ ] **Step 2: Run the project-state tests and see the missing API**

Run: `uv run pytest tests/unidad/test_proyecto_gobernado.py -q`

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'tramalia.core.proyecto'`.

- [ ] **Step 3: Implement exact classification and the single guard**

En `AGENTS.md.jinja`, delimitar la sección que contiene el contrato de cierre con `<!-- tramalia:gobierno inicio -->` y `<!-- tramalia:gobierno fin -->`; no envolver todo el archivo. Ampliar `tests/test_convencion_completa.py` para exigir ambos marcadores y `tramalia close` en todo scaffold nuevo. Un AGENTS heredado que contiene el comando pero no el marcador se clasifica `HEREDADO` y sólo puede pasar por `tramalia upgrade`; texto arbitrario nunca es suficiente.

```python
# tramalia/core/proyecto.py
"""Inspect and enforce Tramalia project governance state."""
from __future__ import annotations

import json
from pathlib import Path

from tramalia.core.errores import ErrorProyectoNoGobernado
from tramalia.core.modelos import EstadoProyecto, ValorEstadoProyecto


def inspeccionar_estado_proyecto(raiz: Path) -> EstadoProyecto:
    """Classify a repository without changing it.

    Args:
        raiz: Repository root.

    Returns:
        A typed state with repair diagnostics.
    """
    # LISTO confirma la estructura de gobierno; cargar_puertas valida el TOML.
    raiz = raiz.resolve()
    directorio = raiz / ".tramalia"
    agentes = raiz / "AGENTS.md"
    configuracion = directorio / "config.json"
    version = directorio / "version"
    mise = raiz / "mise.toml"
    marcadores = (directorio.exists(), agentes.exists(), configuracion.exists(), version.exists(), mise.exists())
    if not any(marcadores):
        return EstadoProyecto(ValorEstadoProyecto.AUSENTE, raiz, (), "tramalia init")

    problemas: list[str] = []
    herencia: list[str] = []
    if not directorio.is_dir():
        problemas.append("falta .tramalia")
    if not agentes.is_file():
        problemas.append("falta AGENTS.md")
    else:
        try:
            texto_agentes = agentes.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            problemas.append("AGENTS.md invalido")
        else:
            if "tramalia close" not in texto_agentes:
                problemas.append("AGENTS.md sin contrato tramalia close")
            else:
                marcador_inicio = "<!-- tramalia:gobierno inicio -->"
                marcador_fin = "<!-- tramalia:gobierno fin -->"
                tiene_inicio = marcador_inicio in texto_agentes
                tiene_fin = marcador_fin in texto_agentes
                if not tiene_inicio and not tiene_fin:
                    if "tramalia:gobierno" in texto_agentes:
                        problemas.append("AGENTS.md con marcador tramalia:gobierno invalido")
                    else:
                        # Una convención anterior reconocible entra a upgrade, nunca a LISTO.
                        herencia.append("AGENTS.md sin marcadores tramalia:gobierno")
                elif not tiene_inicio or not tiene_fin:
                    problemas.append("AGENTS.md con marcadores tramalia:gobierno invalidos")
                else:
                    indice_inicio = texto_agentes.index(marcador_inicio)
                    indice_fin = texto_agentes.index(marcador_fin)
                    bloque_gobierno = texto_agentes[
                        indice_inicio + len(marcador_inicio):indice_fin
                    ]
                    if indice_inicio >= indice_fin or "tramalia close" not in bloque_gobierno:
                        problemas.append("AGENTS.md con bloque tramalia:gobierno invalido")
    if not configuracion.is_file():
        problemas.append("falta .tramalia/config.json")
    else:
        try:
            datos_configuracion = json.loads(configuracion.read_text(encoding="utf-8"))
            if not isinstance(datos_configuracion, dict):
                problemas.append("config.json invalido")
            elif not isinstance(datos_configuracion.get("projectName"), str) or not datos_configuracion["projectName"].strip():
                problemas.append("config.json sin projectName valido")
        except (OSError, UnicodeError, json.JSONDecodeError):
            problemas.append("config.json invalido")
    if not mise.is_file():
        problemas.append("falta mise.toml")

    if not version.is_file():
        herencia.append("falta .tramalia/version")
    elif not version.read_text(encoding="utf-8").strip():
        problemas.append(".tramalia/version vacio")
    if problemas:
        return EstadoProyecto(ValorEstadoProyecto.PARCIAL, raiz, tuple(problemas), "tramalia init --adopt")
    if herencia:
        return EstadoProyecto(ValorEstadoProyecto.HEREDADO, raiz, tuple(herencia), "tramalia upgrade")
    return EstadoProyecto(ValorEstadoProyecto.LISTO, raiz)


def exigir_proyecto_gobernado(raiz: Path) -> EstadoProyecto:
    """Return a ready project or reject a mutating operation.

    Raises:
        ErrorProyectoNoGobernado: If initialization is absent, legacy or partial.
    """
    estado = inspeccionar_estado_proyecto(raiz)
    if estado.listo:
        return estado
    raise ErrorProyectoNoGobernado(
        f"El proyecto esta {estado.estado}; la operacion mutante fue bloqueada.",
        estado.comando_reparacion or "tramalia init",
        ruta=estado.raiz,
        detalles={"estado": estado.estado, "problemas": estado.problemas},
    )


def exigir_proyecto_actualizable(raiz: Path) -> EstadoProyecto:
    """Allow upgrade only for a ready or structurally valid legacy project."""
    estado = inspeccionar_estado_proyecto(raiz)
    if estado.estado in {ValorEstadoProyecto.LISTO, ValorEstadoProyecto.HEREDADO}:
        return estado
    raise ErrorProyectoNoGobernado(
        f"El proyecto esta {estado.estado}; upgrade no puede repararlo de forma segura.",
        estado.comando_reparacion or "tramalia init",
        ruta=estado.raiz,
        detalles={"estado": estado.estado, "problemas": estado.problemas},
    )
```

- [ ] **Step 4: Remove `is_initialized` and migrate every direct caller to the typed inspection**

```python
# Reemplazar lecturas booleanas en tramalia/cli/commands.py, tramalia/tui.py y
# tests/test_v030.py; importar la API española desde tramalia.core.proyecto.
estado_proyecto = inspeccionar_estado_proyecto(raiz)
inicializado = estado_proyecto.listo

# Reemplazar las guardias mutantes ordinarias de CLI/TUI/MCP por esta llamada exacta.
exigir_proyecto_gobernado(raiz)

# El comando público upgrade es la única excepción: debe poder migrar HEREDADO.
exigir_proyecto_actualizable(raiz)
```

Run: `rg -n "is_initialized|_require_init" tramalia tests`

Expected: no matches. Delete `tramalia/core/project.py:16-18`; retain the remaining configuration/default helpers until a later naming migration replaces that module.

- [ ] **Step 5: Run the state tests and current suite**

Run: `uv run pytest tests/unidad/test_proyecto_gobernado.py -q`

Expected: PASS; configuración vacía o AGENTS arbitrario quedan `PARCIAL`, la convención reconocible sin marcador queda `HEREDADO` y sólo el contrato marcado queda `LISTO`.

Run: `uv run pytest -q`

Expected: PASS; historical assertions that an empty `.tramalia` is initialized have been removed, not weakened.

- [ ] **Step 6: Commit the fail-closed project guard**

```bash
git add tramalia/core/proyecto.py tramalia/core/project.py tramalia/cli/commands.py tramalia/tui.py tramalia/templates/project/AGENTS.md.jinja tests/unidad/test_proyecto_gobernado.py tests/test_convencion_completa.py tests/test_v012.py tests/test_v030.py
git commit -m "feat: exigir proyecto gobernado para mutaciones"
```

### Task 3: Carga y ejecución fail-closed de puertas

**Files:**
- Create: `tramalia/core/puertas_calidad.py`
- Create: `tests/unidad/test_puertas_calidad.py`
- Rename: `tramalia/templates/project/docs/ai/09-quality-gates.md` → `tramalia/templates/project/docs/ai/09-puertas-calidad.md`
- Modify: `tests/test_v012.py:108` y `tests/test_v016.py:98` (mover las comprobaciones de `_GATE_ORDER` al contrato público de carga y borrar los accesos a la constante privada)
- Delete after migration: `tests/test_governance.py:15-29`

**Interfaces:**
- Consumes: `PuertaCalidad`, `ResultadoPuerta`, `EjecucionPuertas`, `proc.which()` and `proc.run()`.
- Produces: `cargar_puertas(raiz: Path) -> tuple[PuertaCalidad, ...]` and `ejecutar_puertas(raiz: Path, puertas: Sequence[PuertaCalidad]) -> EjecucionPuertas`.

- [ ] **Step 1: Write failing tests for invalid TOML, missing runner, no gates, failures and distinct outputs**

```python
# tests/unidad/test_puertas_calidad.py
import subprocess

import pytest

from tramalia.core import puertas_calidad
from tramalia.core.detect import enabled_features
from tramalia.core.errores import ErrorConfiguracionPuertas
from tramalia.core.modelos import ValorEstadoPuertas
from tramalia.core.scaffold import build_mise_toml


def test_toml_invalido_no_se_convierte_en_lista_vacia(tmp_path) -> None:
    (tmp_path / "mise.toml").write_text("[tasks", encoding="utf-8")
    with pytest.raises(ErrorConfiguracionPuertas) as capturada:
        puertas_calidad.cargar_puertas(tmp_path)
    assert capturada.value.codigo == "configuracion_puertas_invalida"


def test_mise_ausente_y_sin_puertas_son_estados_bloqueantes(tmp_path, monkeypatch) -> None:
    (tmp_path / "mise.toml").write_text("[tasks.test]\nrun='pytest'", encoding="utf-8")
    cargadas = puertas_calidad.cargar_puertas(tmp_path)
    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: None)
    assert puertas_calidad.ejecutar_puertas(tmp_path, cargadas).estado is ValorEstadoPuertas.EJECUTOR_NO_DISPONIBLE
    assert puertas_calidad.ejecutar_puertas(tmp_path, ()).estado is ValorEstadoPuertas.SIN_CONFIGURAR


def test_error_de_ejecucion_y_puerta_roja_no_son_exito(tmp_path, monkeypatch) -> None:
    (tmp_path / "mise.toml").write_text("[tasks.test]\nrun='pytest'\n[tasks.lint]\nrun='ruff check'", encoding="utf-8")
    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: "mise")
    respuestas = iter([subprocess.CompletedProcess([], 1, "tests rojos", ""), TimeoutError("timeout")])
    monkeypatch.setattr(puertas_calidad.proc, "run", lambda *a, **k: next(respuestas))
    ejecucion = puertas_calidad.ejecutar_puertas(tmp_path, puertas_calidad.cargar_puertas(tmp_path))
    assert ejecucion.estado is ValorEstadoPuertas.ERROR_EJECUCION
    assert ejecucion.fallidas == ("test", "lint")
    assert {r.archivo_salida for r in ejecucion.resultados} == {"test-salida.txt", "lint-salida.txt"}


def test_lint_y_format_nunca_comparten_salida(tmp_path) -> None:
    (tmp_path / "mise.toml").write_text("[tasks.lint]\nrun='ruff check'\n[tasks.format]\nrun='ruff format --check'", encoding="utf-8")
    archivos = [p.archivo_salida for p in puertas_calidad.cargar_puertas(tmp_path)]
    assert archivos == ["lint-salida.txt", "format-salida.txt"]


def test_catalogo_publico_incluye_bundle_y_notebooks(tmp_path) -> None:
    (tmp_path / "mise.toml").write_text(
        "[tasks.bundle]\nrun='databricks bundle validate'\n"
        "[tasks.notebooks]\nrun='nbstripout --verify'\n",
        encoding="utf-8",
    )
    assert tuple(puerta.nombre for puerta in puertas_calidad.cargar_puertas(tmp_path)) == (
        "bundle", "notebooks")


def test_ejecucion_de_notebooks_sigue_siendo_opt_in() -> None:
    base = {
        "stacks": ["python", "notebooks"],
        "features": enabled_features(["python", "notebooks"]),
    }
    assert "jupyter execute" not in build_mise_toml(base)
    activada = {**base, "with_notebook_exec": True}
    assert "jupyter execute notebooks/*.ipynb" in build_mise_toml(activada)
```

- [ ] **Step 2: Run and verify the missing gate module fails**

Run: `uv run pytest tests/unidad/test_puertas_calidad.py -q`

Expected: FAIL during collection with `ImportError: cannot import name 'puertas_calidad'`.

- [ ] **Step 3: Implement strict loading and honest process states**

Ejecutar primero `git mv tramalia/templates/project/docs/ai/09-quality-gates.md tramalia/templates/project/docs/ai/09-puertas-calidad.md` y actualizar referencias del scaffold/tests; el nombre visible del documento nuevo queda en español ASCII.

```python
# tramalia/core/puertas_calidad.py
"""Load and execute quality gates without fail-open fallbacks."""
from __future__ import annotations

import hashlib
import tomllib
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

from tramalia.core import proc
from tramalia.core.errores import ErrorConfiguracionPuertas
from tramalia.core.modelos import (EjecucionPuertas, PuertaCalidad, ResultadoPuerta,
                                   ValorEstadoPuertas, ValorResultadoPuerta)

_ORDEN = ("build", "test", "lint", "format", "security", "database", "bundle", "notebooks", "ux")


def cargar_puertas(raiz: Path) -> tuple[PuertaCalidad, ...]:
    """Load applicable gates from mise.toml.

    Raises:
        ErrorConfiguracionPuertas: If TOML or a gate declaration is invalid.
    """
    ruta = raiz / "mise.toml"
    if not ruta.is_file():
        return ()
    try:
        datos = tomllib.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ErrorConfiguracionPuertas("mise.toml no es valido.",
                                        "Corrige el TOML y ejecuta de nuevo.", ruta,
                                        {"tipo": type(error).__name__}) from error
    tareas = datos.get("tasks", {})
    if not isinstance(tareas, dict):
        raise ErrorConfiguracionPuertas("tasks debe ser una tabla TOML.",
                                        "Define [tasks.<gate>] con run.", ruta)
    puertas: list[PuertaCalidad] = []
    for nombre in _ORDEN:
        if nombre not in tareas:
            continue
        declaracion = tareas[nombre]
        if not isinstance(declaracion, dict) or not isinstance(declaracion.get("run"), (str, list)):
            raise ErrorConfiguracionPuertas(f"El gate {nombre} no tiene run valido.",
                                            f"Corrige [tasks.{nombre}].run.", ruta, {"gate": nombre})
        puertas.append(PuertaCalidad(nombre, ("mise", "run", nombre), f"{nombre}-salida.txt"))
    return tuple(puertas)


def ejecutar_puertas(raiz: Path, puertas: Sequence[PuertaCalidad]) -> EjecucionPuertas:
    """Execute discovered gates and preserve every raw output."""
    nombres = tuple(p.nombre for p in puertas)
    if not puertas:
        return EjecucionPuertas(ValorEstadoPuertas.SIN_CONFIGURAR)
    if proc.which("mise") is None:
        return EjecucionPuertas(ValorEstadoPuertas.EJECUTOR_NO_DISPONIBLE, descubiertas=nombres,
                                omitidas=nombres)
    resultados: list[ResultadoPuerta] = []
    hubo_error = False
    for puerta in puertas:
        inicio = datetime.now(UTC)
        marca = monotonic()
        try:
            proceso = proc.run(list(puerta.comando), cwd=raiz, capture_output=True,
                               text=True, timeout=900)
            salida = (proceso.stdout or "") + (proceso.stderr or "")
            estado = ValorResultadoPuerta.APROBADO if proceso.returncode == 0 else ValorResultadoPuerta.FALLIDO
            codigo = proceso.returncode
        except Exception as error:
            salida = f"{type(error).__name__}: {error}"
            estado = ValorResultadoPuerta.ERROR_EJECUCION
            codigo = None
            hubo_error = True
        fin = datetime.now(UTC)
        resultados.append(ResultadoPuerta(puerta.nombre, puerta.comando, estado, codigo, salida,
                                          inicio, fin, monotonic() - marca,
                                          hashlib.sha256(salida.encode("utf-8")).hexdigest(),
                                          puerta.archivo_salida))
    fallidas = tuple(r.nombre for r in resultados if r.estado is not ValorResultadoPuerta.APROBADO)
    estado_final = (ValorEstadoPuertas.ERROR_EJECUCION if hubo_error else
                    ValorEstadoPuertas.FALLIDO if fallidas else ValorEstadoPuertas.APROBADO)
    return EjecucionPuertas(estado_final, nombres, nombres, (), fallidas, tuple(resultados))
```

- [ ] **Step 4: Run the gate matrix**

Run: `uv run pytest tests/unidad/test_puertas_calidad.py -q`

Expected: `6 passed`.

- [ ] **Step 5: Commit strict gates**

```bash
git add tramalia/core/puertas_calidad.py tramalia/templates/project/docs/ai/09-puertas-calidad.md tests/unidad/test_puertas_calidad.py tests/test_governance.py tests/test_v012.py tests/test_v016.py
git commit -m "feat: ejecutar puertas con politica fail closed"
```

### Task 4: Política de cierre, métricas y cobertura explícita de excepciones

**Files:**
- Create: `tramalia/core/politica_cierre.py`
- Create: `tests/unidad/test_politica_cierre.py`
- Create: `tests/unidad/test_metricas_cierre.py` extrayendo y reescribiendo sólo los casos puros de política/métricas de `tests/test_v016.py`; conservar temporalmente allí los E2E de `close` hasta Task 8
- Delete after migration: `tests/test_metadata.py:20-40`

**Interfaces:**
- Consumes: `EjecucionPuertas`, `ExcepcionFallo`, `ValorEstadoPuertas`, `ErrorConfiguracionMetricas`.
- Produces: `evaluar_metricas(metricas: Mapping[str, object], umbrales: Mapping[str, object]) -> tuple[str, ...]` and `evaluar_cierre(ejecucion: EjecucionPuertas, incumplimientos: Sequence[str], excepciones: Sequence[ExcepcionFallo], ahora: datetime) -> tuple[ValorEstadoCierre, tuple[str, ...]]`. Una regla sin `min`/`max`, con claves desconocidas, valores no numéricos o límites invertidos lanza el error tipado antes de evaluar excepciones.

- [ ] **Step 1: Write the complete fail-closed decision table**

```python
# tests/unidad/test_politica_cierre.py
from datetime import UTC, datetime, timedelta

import pytest

from tramalia.core.errores import ErrorConfiguracionMetricas, ErrorExcepcionInvalida
from tramalia.core.modelos import EjecucionPuertas, ExcepcionFallo, ValorEstadoCierre, ValorEstadoPuertas
from tramalia.core.politica_cierre import evaluar_cierre, evaluar_metricas

AHORA = datetime(2026, 7, 12, tzinfo=UTC)


def _excepcion(control: str, expirada: bool = False) -> ExcepcionFallo:
    return ExcepcionFallo("bloqueo conocido", "riesgo aceptado", control, "ISSUE-8", "ana",
                          AHORA + (-timedelta(days=1) if expirada else timedelta(days=1)))


@pytest.mark.parametrize("estado,control", [
    (ValorEstadoPuertas.EJECUTOR_NO_DISPONIBLE, "ejecutor"),
    (ValorEstadoPuertas.SIN_CONFIGURAR, "puertas"),
    (ValorEstadoPuertas.ERROR_EJECUCION, "ejecucion"),
    (ValorEstadoPuertas.FALLIDO, "test"),
])
def test_bloqueo_solo_pasa_con_excepcion_vigente(estado, control) -> None:
    ejecucion = EjecucionPuertas(estado, fallidas=("test",) if estado is ValorEstadoPuertas.FALLIDO else ())
    assert evaluar_cierre(ejecucion, (), (), AHORA)[0] is ValorEstadoCierre.BLOQUEADO
    assert evaluar_cierre(ejecucion, (), (_excepcion(control),), AHORA)[0] is ValorEstadoCierre.APROBADO_CON_EXCEPCIONES


def test_cada_bloqueo_necesita_su_excepcion() -> None:
    ejecucion = EjecucionPuertas(ValorEstadoPuertas.FALLIDO, fallidas=("test", "lint"))
    estado, pendientes = evaluar_cierre(ejecucion, (), (_excepcion("test"),), AHORA)
    assert estado is ValorEstadoCierre.BLOQUEADO
    assert pendientes == ("lint",)


def test_error_mixto_exige_excepcion_por_cada_puerta_fallida() -> None:
    ejecucion = EjecucionPuertas(
        ValorEstadoPuertas.ERROR_EJECUCION,
        fallidas=("test", "lint"),
    )
    estado, pendientes = evaluar_cierre(
        ejecucion,
        (),
        (_excepcion("test"),),
        AHORA,
    )
    assert estado is ValorEstadoCierre.BLOQUEADO
    assert pendientes == ("lint",)


def test_excepcion_expirada_se_rechaza_antes_de_persistir() -> None:
    with pytest.raises(ErrorExcepcionInvalida, match="vigente"):
        evaluar_cierre(EjecucionPuertas(ValorEstadoPuertas.SIN_CONFIGURAR), (), (_excepcion("puertas", True),), AHORA)


def test_metricas_ausentes_o_fuera_de_umbral_bloquean() -> None:
    assert evaluar_metricas({"metrics": {}}, {"accuracy": {"min": 0.9}}) == ("metrica:accuracy",)
    assert evaluar_metricas({"metrics": {"drift": 0.2}}, {"drift": {"max": 0.1}}) == ("metrica:drift",)


@pytest.mark.parametrize("umbrales", [
    {"coverage": {"minimum": 80}},
    {"coverage": {}},
    {"coverage": {"min": "80"}},
    {"coverage": {"min": 90, "max": 80}},
    {"coverage": {"min": float("nan")}},
    {"coverage": {"min": float("inf")}},
    {"coverage": {"max": -float("inf")}},
    {"coverage": {"min": 10**400}},
])
def test_esquema_de_umbrales_invalido_es_error_no_sobreescribible(umbrales) -> None:
    with pytest.raises(ErrorConfiguracionMetricas):
        evaluar_metricas({"metrics": {"coverage": 85}}, umbrales)


def test_configuracion_de_puertas_invalida_no_admite_excepcion() -> None:
    ejecucion = EjecucionPuertas(ValorEstadoPuertas.CONFIGURACION_INVALIDA)
    estado, pendientes = evaluar_cierre(
        ejecucion, (), (_excepcion("configuracion"),), AHORA,
    )
    assert estado is ValorEstadoCierre.BLOQUEADO
    assert pendientes == ("configuracion",)
```

- [ ] **Step 2: Run and verify the policy API is absent**

Run: `uv run pytest tests/unidad/test_politica_cierre.py -q`

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'tramalia.core.politica_cierre'`.

- [ ] **Step 3: Implement metrics and one-exception-per-blocker evaluation**

```python
# tramalia/core/politica_cierre.py
"""Evaluate closure policy independently from presentation and persistence."""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import datetime

from tramalia.core.errores import ErrorConfiguracionMetricas, ErrorExcepcionInvalida
from tramalia.core.modelos import (EjecucionPuertas, ExcepcionFallo, ValorEstadoCierre,
                                   ValorEstadoPuertas)


def _validar_regla_umbral(nombre: object, regla: object) -> Mapping[str, float]:
    if not isinstance(nombre, str) or not nombre.strip() or not isinstance(regla, Mapping):
        raise ErrorConfiguracionMetricas(
            "La regla de umbral no tiene el esquema requerido.",
            "Usa un nombre no vacio y un objeto con min, max o ambos.",
            detalles={"metrica": nombre},
        )
    claves = set(regla)
    if not claves or not claves <= {"min", "max"}:
        raise ErrorConfiguracionMetricas(
            "La regla de umbral contiene claves desconocidas o esta vacia.",
            "Usa exclusivamente min, max o ambos.",
            detalles={"metrica": nombre, "claves": sorted(map(str, claves))},
        )
    for clave in claves:
        valor = regla[clave]
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ErrorConfiguracionMetricas(
                "Los limites del umbral deben ser numericos.",
                "Corrige el valor antes de cerrar la tarea.",
                detalles={"metrica": nombre, "limite": clave},
            )
    try:
        limites = {str(clave): float(regla[clave]) for clave in claves}
    except (OverflowError, ValueError) as error_limite:
        raise ErrorConfiguracionMetricas(
            "Los limites del umbral no se pueden representar de forma finita.",
            "Usa numeros JSON finitos dentro del rango de Python.",
            detalles={"metrica": nombre},
        ) from error_limite
    if not all(math.isfinite(limite) for limite in limites.values()):
        raise ErrorConfiguracionMetricas(
            "Los limites del umbral deben ser finitos.",
            "Reemplaza NaN o infinito por un numero finito.",
            detalles={"metrica": nombre},
        )
    if "min" in limites and "max" in limites and limites["min"] > limites["max"]:
        raise ErrorConfiguracionMetricas(
            "El minimo del umbral supera al maximo.",
            "Ajusta los limites para que min sea menor o igual que max.",
            detalles={"metrica": nombre},
        )
    return limites


def evaluar_metricas(metricas: Mapping[str, object],
                     umbrales: Mapping[str, object]) -> tuple[str, ...]:
    """Return stable blocker identifiers for missing or failed metrics."""
    valores = metricas.get("metrics", metricas)
    valores = valores if isinstance(valores, Mapping) else {}
    fallos: list[str] = []
    for nombre, regla in umbrales.items():
        regla = _validar_regla_umbral(nombre, regla)
        if nombre not in valores:
            fallos.append(f"metrica:{nombre}")
            continue
        valor = valores[nombre]
        try:
            if ("min" in regla and valor < regla["min"]) or ("max" in regla and valor > regla["max"]):
                fallos.append(f"metrica:{nombre}")
        except TypeError:
            fallos.append(f"metrica:{nombre}")
    return tuple(fallos)


def evaluar_cierre(ejecucion: EjecucionPuertas, incumplimientos: Sequence[str],
                   excepciones: Sequence[ExcepcionFallo],
                   ahora: datetime) -> tuple[ValorEstadoCierre, tuple[str, ...]]:
    """Compute the final state and uncovered blockers.

    Raises:
        ErrorExcepcionInvalida: If any declared exception has expired.
    """
    for excepcion in excepciones:
        if not excepcion.vigente(ahora):
            raise ErrorExcepcionInvalida("La excepcion ya no esta vigente.",
                                         "Renueva la aprobacion o corrige el bloqueo.",
                                         detalles={"control": excepcion.control_afectado})
    if ejecucion.estado is ValorEstadoPuertas.CONFIGURACION_INVALIDA:
        # La configuración inválida requiere reparación; ninguna excepción puede cubrirla.
        return ValorEstadoCierre.BLOQUEADO, ("configuracion",)
    controles: list[str] = list(incumplimientos)
    if ejecucion.estado is ValorEstadoPuertas.EJECUTOR_NO_DISPONIBLE:
        controles.append("ejecutor")
    elif ejecucion.estado is ValorEstadoPuertas.SIN_CONFIGURAR:
        controles.append("puertas")
    elif ejecucion.estado is ValorEstadoPuertas.ERROR_EJECUCION:
        controles.extend(ejecucion.fallidas or ("ejecucion",))
    elif ejecucion.estado is ValorEstadoPuertas.FALLIDO:
        controles.extend(ejecucion.fallidas)
    if not controles and ejecucion.estado is ValorEstadoPuertas.APROBADO and ejecucion.ejecutadas:
        return ValorEstadoCierre.APROBADO, ()
    cubiertos = {e.control_afectado for e in excepciones}
    pendientes = tuple(dict.fromkeys(control for control in controles if control not in cubiertos))
    if pendientes:
        return ValorEstadoCierre.BLOQUEADO, pendientes
    if controles:
        return ValorEstadoCierre.APROBADO_CON_EXCEPCIONES, ()
    return ValorEstadoCierre.BLOQUEADO, ("puertas",)
```

- [ ] **Step 4: Run policy and migrated metric tests**

Run: `uv run pytest tests/unidad/test_politica_cierre.py tests/unidad/test_metricas_cierre.py -q`

Expected: PASS; every prior `no_gates` or `allow_fail=True` success assertion is replaced by a blocked result or a fully populated `ExcepcionFallo`.

- [ ] **Step 5: Commit closure policy**

```bash
git add tramalia/core/politica_cierre.py tests/unidad/test_politica_cierre.py tests/unidad/test_metricas_cierre.py tests/test_v016.py tests/test_metadata.py
git commit -m "feat: evaluar cierre y excepciones razonadas"
```

### Task 5: Identidad segura, metadata formal v1 e inventario Git completo

**Files:**
- Create: `tramalia/core/evidencia.py`
- Create: `tests/unidad/test_identidad_evidencia.py`
- Create: `tests/contratos/test_metadatos_evidencia_v1.py`
- Modify: `.gitignore` (sustituir `.tramalia/evidence/` por `.tramalia/evidencia/`)
- Modify: `tests/conftest.py` (add reusable formal-pack factories shown below)
- Move and rewrite: `tests/test_metadata.py` -> `tests/contratos/test_metadatos_evidencia_v1.py`

**Interfaces:**
- Consumes: all metadata models from Task 1.
- Produces: `validar_id_tarea(id_tarea: str) -> str`, `crear_id_paquete(ahora: datetime | None = None) -> str`, `capturar_estado_git(raiz: Path) -> EstadoGit`, `publicar_paquete(raiz: Path, metadatos: MetadatosPaqueteEvidencia, archivos: Mapping[str, bytes]) -> PaqueteEvidencia`.

- [ ] **Step 1: Write path, Windows-name, uniqueness, schema and Git inventory contracts**

```python
# tests/unidad/test_identidad_evidencia.py
from datetime import UTC, datetime

import pytest

from tramalia.core.errores import ErrorIdentificadorInseguro
from tramalia.core.evidencia import crear_id_paquete, validar_id_tarea


@pytest.mark.parametrize("id_tarea", ["../x", "a/b", "a\\b", "a..b", "CON", "con.txt", "A\nB", "x" * 65, "tarea-ñ"])
def test_rechaza_id_inseguro_en_todas_las_plataformas(id_tarea) -> None:
    with pytest.raises(ErrorIdentificadorInseguro):
        validar_id_tarea(id_tarea)


def test_dos_ids_en_el_mismo_microsegundo_son_distintos(monkeypatch) -> None:
    ahora = datetime(2026, 7, 12, 20, 30, 1, 123456, tzinfo=UTC)
    sufijos = iter(["a1b2c3d4", "e5f6a7b8"])
    monkeypatch.setattr("tramalia.core.evidencia.secrets.token_hex", lambda _: next(sufijos))
    assert crear_id_paquete(ahora) != crear_id_paquete(ahora)
```

```python
# tests/contratos/test_metadatos_evidencia_v1.py
import json
import subprocess
from pathlib import Path

from tramalia.core.evidencia import _serializar, capturar_estado_git


def test_gitignore_usa_directorio_de_evidencia_espanol() -> None:
    raiz = Path(__file__).resolve().parents[2]
    contenido = (raiz / ".gitignore").read_text(encoding="utf-8")
    assert ".tramalia/evidencia/" in contenido
    assert ".tramalia/evidence/" not in contenido


def _ejecutar_git(raiz, *argumentos):
    return subprocess.run(["git", *argumentos], cwd=raiz, check=True, text=True, capture_output=True)


def test_git_distingue_rastreados_preparados_no_rastreados_y_cambios(tmp_path) -> None:
    _ejecutar_git(tmp_path, "init")
    _ejecutar_git(tmp_path, "config", "user.email", "test@example.com")
    _ejecutar_git(tmp_path, "config", "user.name", "Test")
    for nombre in ("rastreado.txt", "renombrar.txt", "eliminar.txt"):
        (tmp_path / nombre).write_text(nombre, encoding="utf-8")
    _ejecutar_git(tmp_path, "add", ".")
    _ejecutar_git(tmp_path, "commit", "-m", "base")
    (tmp_path / "rastreado.txt").write_text("cambio", encoding="utf-8")
    _ejecutar_git(tmp_path, "mv", "renombrar.txt", "renombrado.txt")
    (tmp_path / "eliminar.txt").unlink()
    (tmp_path / "preparado.txt").write_text("preparado", encoding="utf-8")
    _ejecutar_git(tmp_path, "add", "preparado.txt")
    (tmp_path / "no-rastreado.txt").write_text("nuevo", encoding="utf-8")
    estado = capturar_estado_git(tmp_path)
    assert "rastreado.txt" in estado.rastreados
    assert "preparado.txt" in estado.preparados
    assert "no-rastreado.txt" in estado.no_rastreados
    assert any("renombrar.txt -> renombrado.txt" in ruta for ruta in estado.renombrados)
    assert "eliminar.txt" in estado.eliminados


def test_metadatos_serializados_tienen_claves_formales(metadatos_v1) -> None:
    datos = json.loads(_serializar(metadatos_v1))
    assert datos["version_esquema"] == 1
    assert {"id_paquete", "id_tarea", "operacion", "inicio_utc", "fin_utc",
            "entorno", "git", "comandos", "puertas", "metricas", "umbrales",
            "errores_validacion", "excepciones", "vinculo_traspaso"} <= datos.keys()
    for comando in datos["comandos"]:
        assert {"comando", "duracion_segundos", "codigo_salida", "hash_salida", "archivo_salida"} <= comando.keys()
```

Add these exact shared factories to `tests/conftest.py`; later tasks consume the same definitions rather than inventing pack shapes:

```python
import json
from datetime import UTC, datetime

import pytest

from tramalia import __version__
from tramalia.core.evidencia import crear_id_paquete
from tramalia.core.modelos import (EjecucionPuertas, EstadoGit, MetadatosPaqueteEvidencia,
                                   ValorEstadoCierre, ValorEstadoPuertas)


@pytest.fixture
def fabrica_metadatos_v1():
    def fabricar():
        ahora = datetime.now(UTC)
        return MetadatosPaqueteEvidencia(
            1, crear_id_paquete(ahora), "TASK-1", "cierre", ahora, ahora,
            __version__, "3.11.9", "test", {"mise": "test"},
            EstadoGit(None, None, None, None),
            EjecucionPuertas(ValorEstadoPuertas.SIN_CONFIGURAR),
            ValorEstadoCierre.BLOQUEADO, "codex", "test", {}, {},
            ("puertas",), (), "traspaso.md")
    return fabricar


@pytest.fixture
def metadatos_v1(fabrica_metadatos_v1):
    return fabrica_metadatos_v1()


@pytest.fixture
def paquete_v1(tmp_path, metadatos_v1):
    from tramalia.core.evidencia import publicar_paquete
    traspaso = (f"id_paquete: {metadatos_v1.id_paquete}\n"
                f"id_tarea: {metadatos_v1.id_tarea}\n"
                f"resultado: {metadatos_v1.estado_cierre.value}\n").encode()
    return publicar_paquete(tmp_path, metadatos_v1, {"traspaso.md": traspaso})


@pytest.fixture
def proyecto_listo(tmp_path):
    (tmp_path / ".tramalia").mkdir()
    (tmp_path / ".tramalia" / "config.json").write_text(json.dumps({"projectName": "demo"}), encoding="utf-8")
    (tmp_path / ".tramalia" / "version").write_text("0.33.0\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(
        "<!-- tramalia:gobierno inicio -->\ntramalia close\n<!-- tramalia:gobierno fin -->\n",
        encoding="utf-8",
    )
    (tmp_path / "mise.toml").write_text("[tasks.test]\nrun = 'pytest'\n", encoding="utf-8")
    return tmp_path
```

- [ ] **Step 2: Run the new contracts and verify they fail before the writer exists**

Run: `uv run pytest tests/unidad/test_identidad_evidencia.py tests/contratos/test_metadatos_evidencia_v1.py -q`

Expected: FAIL because `tramalia.core.evidencia` and `_serializar` do not exist.

- [ ] **Step 3: Implement validation and exact JSON serialization before persistence**

```python
# Añadir a tramalia/core/evidencia.py
"""Create immutable evidence packs using same-filesystem atomic publication."""
from __future__ import annotations

import json
import math
import os
import re
import secrets
import subprocess
import uuid
from collections.abc import Mapping
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from tramalia.core.errores import ErrorIdentificadorInseguro, ErrorPersistenciaEvidencia
from tramalia.core.modelos import (EstadoGit, MetadatosPaqueteEvidencia, PaqueteEvidencia)

_ID_SEGURO = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_RESERVADOS_WINDOWS = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def validar_id_tarea(id_tarea: str) -> str:
    """Validate a task identifier before any filesystem write.

    Raises:
        ErrorIdentificadorInseguro: If the identifier is unsafe on any target OS.
    """
    nombre_base_windows = id_tarea.split(".", 1)[0].upper()
    if (not _ID_SEGURO.fullmatch(id_tarea) or ".." in id_tarea or id_tarea.endswith(".") or
            nombre_base_windows in _RESERVADOS_WINDOWS):
        raise ErrorIdentificadorInseguro("El ID de tarea no es seguro.",
                                         "Usa 1-64 letras ASCII, numeros, punto, guion o guion bajo.",
                                         detalles={"id_tarea": id_tarea})
    return id_tarea


def crear_id_paquete(ahora: datetime | None = None) -> str:
    instante = (ahora or datetime.now(UTC)).astimezone(UTC)
    return f"{instante.strftime('%Y%m%dT%H%M%S.%fZ')}-{secrets.token_hex(4)}"


def _consultar_git(raiz: Path, *argumentos: str) -> str | None:
    try:
        proceso = subprocess.run(["git", *argumentos], cwd=raiz, text=True,
                                 capture_output=True, timeout=10, check=False)
        return proceso.stdout.strip() if proceso.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def capturar_estado_git(raiz: Path) -> EstadoGit:
    """Capture tracked, staged, untracked, renamed and deleted paths."""
    rastreados = tuple(filter(None, (_consultar_git(raiz, "diff", "--name-only") or "").splitlines()))
    preparados = tuple(filter(None, (_consultar_git(raiz, "diff", "--cached", "--name-only") or "").splitlines()))
    no_rastreados = tuple(filter(None, (_consultar_git(raiz, "ls-files", "--others", "--exclude-standard") or "").splitlines()))
    estado = (_consultar_git(raiz, "status", "--porcelain=v1") or "").splitlines()
    renombrados = tuple(line[3:] for line in estado if line[:2].strip().startswith("R"))
    eliminados = tuple(line[3:] for line in estado if "D" in line[:2])
    rama = _consultar_git(raiz, "branch", "--show-current")
    commit = _consultar_git(raiz, "rev-parse", "HEAD")
    return EstadoGit(commit, rama, not bool(estado) if commit else None,
                     _consultar_git(raiz, "merge-base", "HEAD", "main"), rastreados, preparados,
                     no_rastreados, renombrados, eliminados)


def _serializar(metadatos: MetadatosPaqueteEvidencia) -> bytes:
    datos = asdict(metadatos)
    datos["inicio_utc"] = metadatos.inicio_utc.isoformat()
    datos["fin_utc"] = metadatos.fin_utc.isoformat()
    datos["estado_cierre"] = metadatos.estado_cierre.value
    datos["entorno"] = {"tramalia": datos.pop("version_tramalia"),
                        "python": datos.pop("version_python"),
                        "sistema_operativo": datos.pop("sistema_operativo"),
                        "cadena_herramientas": datos.pop("cadena_herramientas")}
    datos.pop("ejecucion")
    datos["puertas"] = {
        "estado": metadatos.ejecucion.estado.value,
        "descubiertas": list(metadatos.ejecucion.descubiertas),
        "ejecutadas": list(metadatos.ejecucion.ejecutadas),
        "omitidas": list(metadatos.ejecucion.omitidas),
        "fallidas": list(metadatos.ejecucion.fallidas),
        "errores_validacion": list(metadatos.ejecucion.errores_validacion),
    }
    datos["comandos"] = [{"comando": list(r.comando), "duracion_segundos": r.duracion_segundos,
                           "codigo_salida": r.codigo_salida, "hash_salida": r.hash_salida,
                           "archivo_salida": r.archivo_salida}
                          for r in metadatos.ejecucion.resultados]
    for excepcion in datos["excepciones"]:
        if excepcion["expira_en"]:
            excepcion["expira_en"] = excepcion["expira_en"].isoformat()
    return (json.dumps(datos, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
```

- [ ] **Step 4: Run identity and Git tests**

Run: `uv run pytest tests/unidad/test_identidad_evidencia.py tests/contratos/test_metadatos_evidencia_v1.py -q`

Expected: PASS.

- [ ] **Step 5: Commit identity and schema contracts**

```bash
git add .gitignore tramalia/core/evidencia.py tests/conftest.py tests/unidad/test_identidad_evidencia.py tests/contratos/test_metadatos_evidencia_v1.py tests/test_metadata.py
git commit -m "feat: definir metadata formal de evidencia v1"
```

### Task 6: Writer atómico, containment, concurrencia y cero packs parciales

**Files:**
- Modify: `tramalia/core/evidencia.py` (append atomic publication functions)
- Create: `tests/integracion/test_evidencia_atomica.py`
- Move and rewrite: `tests/test_evidence_handoff.py:10-15` -> `tests/integracion/test_evidencia_atomica.py`

**Interfaces:**
- Consumes: `validar_id_tarea`, `crear_id_paquete`, `_serializar`.
- Produces: `publicar_paquete(raiz, metadatos, archivos) -> PaqueteEvidencia`; final paths are new and staging is always removed on failure.

- [ ] **Step 1: Write atomicity, injected failure, containment and concurrency tests**

```python
# tests/integracion/test_evidencia_atomica.py
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from tramalia.core.errores import ErrorPersistenciaEvidencia
from tramalia.core.evidencia import publicar_paquete


def test_fallo_intermedio_no_deja_paquete_final_ni_temporal(tmp_path, metadatos_v1, monkeypatch) -> None:
    real = __import__("os").replace
    monkeypatch.setattr("tramalia.core.evidencia.os.replace",
                        lambda origen, destino: (_ for _ in ()).throw(OSError("inyectado")))
    with pytest.raises(ErrorPersistenciaEvidencia):
        publicar_paquete(tmp_path, metadatos_v1, {"traspaso.md": b"ok"})
    base = tmp_path / ".tramalia" / "evidencia"
    assert not [ruta for ruta in base.iterdir() if ruta.is_dir()]
    monkeypatch.setattr("tramalia.core.evidencia.os.replace", real)


def test_dos_publicaciones_simultaneas_son_distintas(tmp_path, fabrica_metadatos_v1) -> None:
    def publicar(_):
        metadatos = fabrica_metadatos_v1()
        return publicar_paquete(tmp_path, metadatos, {"traspaso.md": b"ok"})
    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        paquetes = list(ejecutor.map(publicar, range(2)))
    assert paquetes[0].id_paquete != paquetes[1].id_paquete
    assert all(p.ruta.is_dir() for p in paquetes)


def test_ruta_resuelta_permanece_bajo_evidencia(tmp_path, metadatos_v1) -> None:
    paquete = publicar_paquete(tmp_path, metadatos_v1, {"traspaso.md": b"ok"})
    base = (tmp_path / ".tramalia" / "evidencia").resolve()
    assert paquete.ruta.resolve().is_relative_to(base)


def test_fallo_al_crear_directorio_base_es_error_de_dominio(
    tmp_path, metadatos_v1, monkeypatch
) -> None:
    crear_directorio = Path.mkdir

    def fallar(ruta, *argumentos, **opciones):
        if ruta.name == "evidencia":
            raise PermissionError("solo lectura")
        return crear_directorio(ruta, *argumentos, **opciones)

    monkeypatch.setattr(Path, "mkdir", fallar)
    with pytest.raises(ErrorPersistenciaEvidencia) as capturada:
        publicar_paquete(tmp_path, metadatos_v1, {"traspaso.md": b"ok"})
    assert capturada.value.codigo == "persistencia_evidencia_fallida"
```

- [ ] **Step 2: Run and verify publication is not implemented**

Run: `uv run pytest tests/integracion/test_evidencia_atomica.py -q`

Expected: FAIL during collection with `ImportError: cannot import name 'publicar_paquete'`.

- [ ] **Step 3: Append the complete staging/publication implementation**

```python
# Añadir `shutil` al bloque superior de imports y estas funciones a evidencia.py.
def _bajo_base(ruta: Path, base: Path) -> bool:
    try:
        return ruta.resolve().is_relative_to(base.resolve())
    except (OSError, RuntimeError):
        return False


def _escribir_archivo(ruta: Path, contenido: bytes) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("xb") as archivo:
        archivo.write(contenido)
        archivo.flush()
        os.fsync(archivo.fileno())


def publicar_paquete(raiz: Path, metadatos: MetadatosPaqueteEvidencia,
                     archivos: Mapping[str, bytes]) -> PaqueteEvidencia:
    """Publish a complete evidence pack atomically.

    Raises:
        ErrorPersistenciaEvidencia: If containment, staging, validation or rename fails.
    """
    validar_id_tarea(metadatos.id_tarea)
    base = raiz.absolute() / ".tramalia" / "evidencia"
    final = base / metadatos.id_paquete
    temporal = base / f".tmp-{uuid.uuid4().hex}"
    try:
        base = raiz.resolve() / ".tramalia" / "evidencia"
        base.mkdir(parents=True, exist_ok=True)
        final = base / metadatos.id_paquete
        temporal = base / f".tmp-{uuid.uuid4().hex}"
        if not _bajo_base(final, base) or not _bajo_base(temporal, base) or final.exists():
            raise ErrorPersistenciaEvidencia(
                "La ruta del paquete no es nueva o segura.",
                "Reintenta con un ID de paquete nuevo.",
                final,
            )
        temporal.mkdir()
        contenido = dict(archivos)
        contenido["metadatos.json"] = _serializar(metadatos)
        if "traspaso.md" not in contenido:
            raise ValueError("falta traspaso.md canonico")
        for nombre, datos in contenido.items():
            destino = temporal / nombre
            if Path(nombre).is_absolute() or not _bajo_base(destino, temporal):
                raise ValueError(f"ruta interna insegura: {nombre}")
            _escribir_archivo(destino, datos)
        json.loads((temporal / "metadatos.json").read_text(encoding="utf-8"))
        os.replace(temporal, final)
        return PaqueteEvidencia(metadatos.id_paquete, final, metadatos)
    except ErrorPersistenciaEvidencia:
        shutil.rmtree(temporal, ignore_errors=True)
        raise
    except Exception as error:
        shutil.rmtree(temporal, ignore_errors=True)
        raise ErrorPersistenciaEvidencia(
            "No se pudo publicar el paquete atomico.",
            "Revisa permisos y soporte de renombrado atomico en el sistema de archivos.",
            final,
            {"tipo": type(error).__name__},
        ) from error
```

- [ ] **Step 4: Run atomicity tests repeatedly to expose collisions**

Run: `uv run pytest tests/integracion/test_evidencia_atomica.py -q --count=20`

Expected: PASS with `pytest-repeat` from the reproducible dev environment created in plan 01; fallos de permisos y publicación son `ErrorPersistenciaEvidencia` y no quedan directorios `.tmp-*`.

- [ ] **Step 5: Commit the atomic writer**

```bash
git add tramalia/core/evidencia.py tests/integracion/test_evidencia_atomica.py tests/test_evidence_handoff.py
git commit -m "feat: publicar evidence packs de forma atomica"
```

### Task 7: Traspaso canónico, proyección atómica y bitácora estructurada

**Files:**
- Create: `tramalia/core/traspaso.py`
- Modify: `tramalia/core/evidencia.py` (append `leer_bitacora`)
- Rename: `tramalia/templates/project/docs/ai/07-handoff-agentes.md` → `tramalia/templates/project/docs/ai/07-traspaso-agentes.md`
- Modify: `docs/flujo-completo.md`, `docs/flujo-completo.en.md`, `docs/comandos.md`, `docs/comandos.en.md` y la descripción MCP que enlaza la proyección
- Create: `tests/integracion/test_traspaso_bitacora.py`
- Delete after migration: `tests/test_evidence_handoff.py:17-22`, `tests/test_speckit_ui.py:30-42`, `tests/test_governance.py:32-38`

**Interfaces:**
- Consumes: `ResultadoCierre`, `MetadatosPaqueteEvidencia`, `EntradaBitacora`.
- Produces: `construir_traspaso(resultado: ResultadoCierre, agente: str, revisor: str) -> bytes`, `proyectar_traspaso(raiz: Path, paquete: PaqueteEvidencia) -> Path`, `leer_bitacora(raiz: Path) -> list[EntradaBitacora]`.

- [ ] **Step 1: Write canonical agreement, projection-failure and corrupt metadata tests**

```python
# tests/integracion/test_traspaso_bitacora.py
import json
import re
from pathlib import Path

from tramalia.core.evidencia import leer_bitacora
from tramalia.core.modelos import ValorEstadoBitacora
from tramalia.core.traspaso import proyectar_traspaso


def test_metadatos_y_traspaso_coinciden(paquete_v1) -> None:
    metadatos = json.loads((paquete_v1.ruta / "metadatos.json").read_text(encoding="utf-8"))
    texto = (paquete_v1.ruta / "traspaso.md").read_text(encoding="utf-8")
    assert metadatos["id_paquete"] in texto
    assert metadatos["id_tarea"] in texto
    assert metadatos["estado_cierre"] in texto


def test_bitacora_valida_conserva_modelo_y_resultado(paquete_v1) -> None:
    raiz = paquete_v1.ruta.parents[2]
    entrada = leer_bitacora(raiz)[0]
    assert entrada.estado is ValorEstadoBitacora.VALIDA
    assert entrada.id_paquete == paquete_v1.id_paquete
    assert entrada.modelo == paquete_v1.metadatos.modelo
    assert entrada.resultado is paquete_v1.metadatos.estado_cierre


def test_enlace_proyectado_resuelve_al_traspaso_canonico(tmp_path, paquete_v1) -> None:
    ruta = proyectar_traspaso(tmp_path, paquete_v1)
    coincidencia = re.search(r"\]\(([^)]+)\)", ruta.read_text(encoding="utf-8"))
    assert coincidencia is not None
    assert not Path(coincidencia.group(1)).is_absolute()
    assert (ruta.parent / coincidencia.group(1)).resolve() == (
        paquete_v1.ruta / "traspaso.md"
    ).resolve()


def test_fallo_de_proyeccion_no_modifica_paquete_canonico(tmp_path, paquete_v1, monkeypatch) -> None:
    antes = (paquete_v1.ruta / "traspaso.md").read_bytes()
    monkeypatch.setattr("tramalia.core.traspaso.os.replace",
                        lambda *args: (_ for _ in ()).throw(OSError("bloqueado")))
    ruta = proyectar_traspaso(tmp_path, paquete_v1)
    assert ruta == tmp_path / "docs" / "ai" / "07-traspaso-agentes.md"
    assert (paquete_v1.ruta / "traspaso.md").read_bytes() == antes


def test_fallo_al_crear_directorio_de_proyeccion_tambien_es_no_fatal(
    tmp_path, paquete_v1, monkeypatch
) -> None:
    crear_directorio = Path.mkdir

    def fallar(ruta, *argumentos, **opciones):
        if ruta.name == "ai":
            raise PermissionError("documentacion de solo lectura")
        return crear_directorio(ruta, *argumentos, **opciones)

    antes = (paquete_v1.ruta / "traspaso.md").read_bytes()
    monkeypatch.setattr(Path, "mkdir", fallar)
    ruta = proyectar_traspaso(tmp_path, paquete_v1)
    assert ruta == tmp_path / "docs" / "ai" / "07-traspaso-agentes.md"
    assert (paquete_v1.ruta / "traspaso.md").read_bytes() == antes


def test_metadatos_corruptos_aparecen_invalidos_sin_alternativa_markdown(tmp_path) -> None:
    paquete_corrupto = tmp_path / ".tramalia" / "evidencia" / "paquete-corrupto"
    paquete_corrupto.mkdir(parents=True)
    (paquete_corrupto / "metadatos.json").write_text("{", encoding="utf-8")
    (paquete_corrupto / "estado-puertas.md").write_text("aprobado", encoding="utf-8")
    entrada = leer_bitacora(tmp_path)[0]
    assert entrada.estado == "invalida"
    assert entrada.resultado is None


def test_metadatos_v1_truncados_no_se_marcan_validos(tmp_path) -> None:
    ruta = tmp_path / ".tramalia" / "evidencia" / "paquete-truncado"
    ruta.mkdir(parents=True)
    (ruta / "metadatos.json").write_text(
        json.dumps({
            "version_esquema": 1,
            "id_paquete": ruta.name,
            "id_tarea": "TASK-1",
            "estado_cierre": "bloqueado",
            "fin_utc": "2026-07-12T20:30:00+00:00",
        }),
        encoding="utf-8",
    )
    entrada = leer_bitacora(tmp_path)[0]
    assert entrada.estado is ValorEstadoBitacora.INVALIDA
    assert "faltan claves" in (entrada.error or "")


def test_id_paquete_debe_coincidir_con_directorio(paquete_v1) -> None:
    ruta_metadatos = paquete_v1.ruta / "metadatos.json"
    datos = json.loads(ruta_metadatos.read_text(encoding="utf-8"))
    datos["id_paquete"] = "paquete-distinto"
    ruta_metadatos.write_text(json.dumps(datos), encoding="utf-8")
    entrada = leer_bitacora(paquete_v1.ruta.parents[2])[0]
    assert entrada.estado is ValorEstadoBitacora.INVALIDA
    assert "no coincide" in (entrada.error or "")


def test_metadatos_completos_pero_semanticamente_corruptos_son_invalidos(
    paquete_v1,
) -> None:
    datos_base = json.loads(
        (paquete_v1.ruta / "metadatos.json").read_text(encoding="utf-8"),
    )
    casos: dict[str, dict[str, object]] = {}

    puertas_invalidas = json.loads(json.dumps(datos_base))
    puertas_invalidas["puertas"]["estado"] = None
    casos["puertas-invalidas"] = puertas_invalidas

    entorno_invalido = json.loads(json.dumps(datos_base))
    entorno_invalido["entorno"]["cadena_herramientas"] = None
    casos["entorno-invalido"] = entorno_invalido

    git_invalido = json.loads(json.dumps(datos_base))
    git_invalido["git"]["rastreados"] = None
    casos["git-invalido"] = git_invalido

    comando_valido = {
        "comando": ["pytest"],
        "duracion_segundos": 0.1,
        "codigo_salida": 0,
        "hash_salida": "0" * 64,
        "archivo_salida": "test-salida.txt",
    }
    comando_invalido = json.loads(json.dumps(datos_base))
    comando_invalido["comandos"] = [{**comando_valido, "hash_salida": "x"}]
    casos["comando-invalido"] = comando_invalido

    duracion_invalida = json.loads(json.dumps(datos_base))
    duracion_invalida["comandos"] = [{
        **comando_valido, "duracion_segundos": 10**400,
    }]
    casos["duracion-invalida"] = duracion_invalida

    for nombre_archivo in (".", ".."):
        archivo_invalido = json.loads(json.dumps(datos_base))
        archivo_invalido["comandos"] = [{
            **comando_valido, "archivo_salida": nombre_archivo,
        }]
        casos[f"archivo-invalido-{len(casos)}"] = archivo_invalido

    base = paquete_v1.ruta.parent
    for id_paquete, datos in casos.items():
        datos["id_paquete"] = id_paquete
        ruta = base / id_paquete
        ruta.mkdir()
        (ruta / "metadatos.json").write_text(json.dumps(datos), encoding="utf-8")

    entradas = {entrada.id_paquete: entrada for entrada in leer_bitacora(base.parents[1])}
    for id_paquete in casos:
        assert entradas[id_paquete].estado is ValorEstadoBitacora.INVALIDA
```

- [ ] **Step 2: Run and verify traspaso/bitácora APIs are absent**

Run: `uv run pytest tests/integracion/test_traspaso_bitacora.py -q`

Expected: FAIL during collection with missing `tramalia.core.traspaso` or `leer_bitacora`.

- [ ] **Step 3: Implement canonical handoff and non-authoritative projection**

Ejecutar `git mv tramalia/templates/project/docs/ai/07-handoff-agentes.md tramalia/templates/project/docs/ai/07-traspaso-agentes.md` y actualizar todas las referencias ES/EN, tests migrados y la descripción MCP antes de implementar la proyección. Al finalizar, `rg -n "07-handoff-agentes|\.tramalia/evidence|metadata\.json" tramalia/core/evidencia.py tramalia/core/traspaso.py tramalia/mcp_server.py tramalia/templates/project tests/integracion/test_traspaso_bitacora.py docs/flujo-completo.md docs/flujo-completo.en.md docs/comandos.md docs/comandos.en.md` no devuelve coincidencias. La limpieza del resto de la documentación activa corresponde al plan 04; los documentos históricos y los propios planes no forman parte de este chequeo. Los módulos históricos ingleses se revisan y eliminan en Task 8:

```python
# tramalia/core/traspaso.py
"""Build canonical handoffs and best-effort global projections."""
from __future__ import annotations

import os
import uuid
from contextlib import suppress
from pathlib import Path

from tramalia.core.modelos import PaqueteEvidencia, ResultadoCierre


def construir_traspaso(resultado: ResultadoCierre, agente: str, revisor: str) -> bytes:
    """Render the already-computed closure result without re-evaluating policy."""
    excepciones = ", ".join(e.control_afectado for e in resultado.excepciones) or "ninguna"
    texto = (f"# Traspaso canonico\n\n- id_paquete: {resultado.id_paquete}\n"
             f"- id_tarea: {resultado.id_tarea}\n- resultado: {resultado.estado.value}\n"
             f"- agente: {agente or 'no declarado'}\n- revisor: {revisor or 'no declarado'}\n"
             f"- excepciones: {excepciones}\n")
    return texto.encode("utf-8")


def proyectar_traspaso(raiz: Path, paquete: PaqueteEvidencia) -> Path:
    """Atomically project the canonical handoff; projection failure is non-fatal."""
    destino = raiz / "docs" / "ai" / "07-traspaso-agentes.md"
    temporal = destino.with_name(f".{destino.name}.tmp-{uuid.uuid4().hex}")
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        relativo = paquete.ruta.relative_to(raiz).as_posix()
        enlace = Path(
            os.path.relpath(paquete.ruta / "traspaso.md", destino.parent)
        ).as_posix()
        contenido = (
            f"# 07 - Traspaso de agentes\n\n- id_paquete: {paquete.id_paquete}\n"
            f"- paquete canonico: [{relativo}/traspaso.md]({enlace})\n"
        )
        temporal.write_text(contenido, encoding="utf-8")
        os.replace(temporal, destino)
    except (OSError, RuntimeError, ValueError):
        with suppress(OSError):
            temporal.unlink(missing_ok=True)
    return destino
```

- [ ] **Step 4: Append structured v1-only log reading**

```python
# Ampliar el import de tramalia.core.modelos situado al inicio de evidencia.py con
# EntradaBitacora, ValorEstadoBitacora, ValorEstadoCierre y ValorEstadoPuertas.
# No insertar imports
# debajo de funciones.


_CLAVES_METADATOS_V1 = frozenset({
    "version_esquema", "id_paquete", "id_tarea", "operacion", "inicio_utc",
    "fin_utc", "entorno", "git", "comandos", "puertas", "estado_cierre",
    "agente", "modelo", "metricas", "umbrales", "errores_validacion",
    "excepciones", "vinculo_traspaso",
})


def _exigir_lista_textos(valor: object, nombre: str) -> list[str]:
    if not isinstance(valor, list) or any(not isinstance(elemento, str) for elemento in valor):
        raise ValueError(f"{nombre} debe ser una lista de textos")
    return valor


def _validar_metadatos_bitacora(
    datos: object,
    id_directorio: str,
) -> Mapping[str, object]:
    if not isinstance(datos, Mapping):
        raise ValueError("metadatos.json debe contener un objeto")
    faltantes = sorted(_CLAVES_METADATOS_V1 - set(datos))
    if faltantes:
        raise ValueError(f"faltan claves formales: {', '.join(faltantes)}")
    if type(datos["version_esquema"]) is not int or datos["version_esquema"] != 1:
        raise ValueError("version_esquema no soportada")
    if datos["id_paquete"] != id_directorio:
        raise ValueError("id_paquete no coincide con el directorio")
    for clave in ("id_paquete", "id_tarea", "operacion"):
        if not isinstance(datos[clave], str) or not datos[clave].strip():
            raise ValueError(f"{clave} debe ser texto no vacio")
    if datos["operacion"] not in {"cierre", "evidencia", "traspaso"}:
        raise ValueError("operacion no soportada")
    inicio = datetime.fromisoformat(str(datos["inicio_utc"]))
    fin = datetime.fromisoformat(str(datos["fin_utc"]))
    desfase_inicio = inicio.utcoffset()
    desfase_fin = fin.utcoffset()
    if (
        desfase_inicio is None
        or desfase_fin is None
        or desfase_inicio.total_seconds() != 0
        or desfase_fin.total_seconds() != 0
        or fin < inicio
    ):
        raise ValueError("las marcas de tiempo deben estar en UTC y ordenadas")
    ValorEstadoCierre(str(datos["estado_cierre"]))

    entorno = datos["entorno"]
    claves_entorno = {"tramalia", "python", "sistema_operativo", "cadena_herramientas"}
    if not isinstance(entorno, Mapping) or not claves_entorno <= set(entorno):
        raise ValueError("estructura entorno incompleta")
    for nombre in ("tramalia", "python", "sistema_operativo"):
        if not isinstance(entorno[nombre], str) or not entorno[nombre].strip():
            raise ValueError(f"entorno.{nombre} debe ser texto no vacio")
    cadena_herramientas = entorno["cadena_herramientas"]
    if not isinstance(cadena_herramientas, Mapping) or any(
        not isinstance(clave, str) or (valor is not None and not isinstance(valor, str))
        for clave, valor in cadena_herramientas.items()
    ):
        raise ValueError("entorno.cadena_herramientas invalida")

    git = datos["git"]
    claves_git = {
        "commit", "rama", "limpio", "base_comparacion", "rastreados",
        "preparados", "no_rastreados", "renombrados", "eliminados",
    }
    if not isinstance(git, Mapping) or not claves_git <= set(git):
        raise ValueError("estructura git incompleta")
    for nombre in ("commit", "rama", "base_comparacion"):
        if git[nombre] is not None and not isinstance(git[nombre], str):
            raise ValueError(f"git.{nombre} debe ser texto o nulo")
    if git["limpio"] is not None and not isinstance(git["limpio"], bool):
        raise ValueError("git.limpio debe ser booleano o nulo")
    for nombre in ("rastreados", "preparados", "no_rastreados", "renombrados", "eliminados"):
        _exigir_lista_textos(git[nombre], f"git.{nombre}")

    puertas = datos["puertas"]
    claves_puertas = {
        "estado", "descubiertas", "ejecutadas", "omitidas", "fallidas",
        "errores_validacion",
    }
    if not isinstance(puertas, Mapping) or not claves_puertas <= set(puertas):
        raise ValueError("estructura puertas incompleta")
    ValorEstadoPuertas(str(puertas["estado"]))
    for nombre in ("descubiertas", "ejecutadas", "omitidas", "fallidas", "errores_validacion"):
        _exigir_lista_textos(puertas[nombre], f"puertas.{nombre}")

    for nombre in ("metricas", "umbrales"):
        if not isinstance(datos[nombre], Mapping):
            raise ValueError(f"{nombre} debe ser un objeto")
    _exigir_lista_textos(datos["errores_validacion"], "errores_validacion")
    comandos = datos["comandos"]
    if not isinstance(comandos, list):
        raise ValueError("comandos debe ser una lista")
    for comando in comandos:
        requeridas = {
            "comando", "duracion_segundos", "codigo_salida", "hash_salida",
            "archivo_salida",
        }
        if not isinstance(comando, Mapping) or not requeridas <= set(comando):
            raise ValueError("entrada de comando incompleta")
        _exigir_lista_textos(comando["comando"], "comando.comando")
        if not comando["comando"]:
            raise ValueError("comando.comando no puede estar vacio")
        duracion = comando["duracion_segundos"]
        if (
            isinstance(duracion, bool)
            or not isinstance(duracion, (int, float))
            or duracion < 0
        ):
            raise ValueError("comando.duracion_segundos invalida")
        try:
            duracion_finita = math.isfinite(float(duracion))
        except (OverflowError, ValueError) as error_duracion:
            raise ValueError("comando.duracion_segundos fuera de rango") from error_duracion
        if not duracion_finita:
            raise ValueError("comando.duracion_segundos debe ser finita")
        codigo_salida = comando["codigo_salida"]
        if codigo_salida is not None and (
            isinstance(codigo_salida, bool) or not isinstance(codigo_salida, int)
        ):
            raise ValueError("comando.codigo_salida invalido")
        if not isinstance(comando["hash_salida"], str) or not re.fullmatch(
            r"[0-9a-f]{64}", comando["hash_salida"],
        ):
            raise ValueError("comando.hash_salida invalido")
        archivo_salida = comando["archivo_salida"]
        if (
            not isinstance(archivo_salida, str)
            or archivo_salida in {".", ".."}
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", archivo_salida)
        ):
            raise ValueError("comando.archivo_salida invalido")

    excepciones = datos["excepciones"]
    if not isinstance(excepciones, list):
        raise ValueError("excepciones debe ser una lista")
    claves_excepcion = {
        "razon", "riesgo_aceptado", "control_afectado", "referencia", "revisor",
        "expira_en", "condicion_remediacion",
    }
    for excepcion in excepciones:
        if not isinstance(excepcion, Mapping) or not claves_excepcion <= set(excepcion):
            raise ValueError("entrada de excepcion incompleta")
        for nombre in ("razon", "riesgo_aceptado", "control_afectado", "referencia", "revisor"):
            if not isinstance(excepcion[nombre], str) or not excepcion[nombre].strip():
                raise ValueError(f"excepcion.{nombre} debe ser texto no vacio")
        expiracion = excepcion["expira_en"]
        condicion = excepcion["condicion_remediacion"]
        if expiracion is not None:
            if not isinstance(expiracion, str) or datetime.fromisoformat(expiracion).utcoffset() is None:
                raise ValueError("excepcion.expira_en invalida")
        if condicion is not None and not isinstance(condicion, str):
            raise ValueError("excepcion.condicion_remediacion invalida")
        if expiracion is None and not (isinstance(condicion, str) and condicion.strip()):
            raise ValueError("excepcion sin vigencia")

    if datos["vinculo_traspaso"] != "traspaso.md":
        raise ValueError("vinculo_traspaso no es canonico")
    for nombre in ("agente", "modelo"):
        if datos[nombre] is not None and not isinstance(datos[nombre], str):
            raise ValueError(f"{nombre} debe ser texto o nulo")
    return datos


def leer_bitacora(raiz: Path) -> list[EntradaBitacora]:
    """Read formal metadata; corrupt entries remain explicitly invalid."""
    base = raiz / ".tramalia" / "evidencia"
    if not base.is_dir():
        return []
    entradas: list[EntradaBitacora] = []
    for ruta in sorted((p for p in base.iterdir() if p.is_dir() and not p.name.startswith(".tmp-")), reverse=True):
        try:
            datos = _validar_metadatos_bitacora(
                json.loads((ruta / "metadatos.json").read_text(encoding="utf-8")),
                ruta.name,
            )
            agente = datos["agente"] if isinstance(datos["agente"], str) else None
            modelo = datos["modelo"] if isinstance(datos["modelo"], str) else None
            entradas.append(EntradaBitacora(
                ruta.name, ruta, ValorEstadoBitacora.VALIDA, str(datos["id_tarea"]),
                ValorEstadoCierre(str(datos["estado_cierre"])),
                agente, modelo,
                datetime.fromisoformat(str(datos["fin_utc"])), None))
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            entradas.append(EntradaBitacora(ruta.name, ruta, ValorEstadoBitacora.INVALIDA,
                                            None, None, None, None, None, str(error)))
    return entradas
```

- [ ] **Step 5: Run traspaso and bitácora tests**

Run: `uv run pytest tests/integracion/test_traspaso_bitacora.py -q`

Expected: PASS; la bitácora v1 válida conserva modelo/resultado; metadata truncada, con identidad divergente, enums inválidos, colecciones nulas o hashes malformados queda inválida. Los metadatos corruptos nunca se infieren desde `estado-puertas.md`, el enlace proyectado resuelve al paquete canónico y cualquier fallo esperado de ruta/sistema de archivos deja intacto el paquete.

- [ ] **Step 6: Commit canonical handoff and structured log**

```bash
git add tramalia/core/traspaso.py tramalia/core/evidencia.py tramalia/mcp_server.py tramalia/templates/project/docs/ai/07-traspaso-agentes.md docs/flujo-completo.md docs/flujo-completo.en.md docs/comandos.md docs/comandos.en.md tests/integracion/test_traspaso_bitacora.py tests/test_evidence_handoff.py tests/test_speckit_ui.py tests/test_governance.py
git commit -m "feat: registrar traspaso canonico y bitacora v1"
```

### Task 8: Operaciones compartidas, pack completo y retirada del núcleo histórico

**Files:**
- Create: `tramalia/core/operaciones.py`
- Create: `tests/integracion/test_operaciones.py`
- Create: `tests/contratos/test_operaciones_superficies.py`
- Modify: `tramalia/cli/commands.py:322-430`
- Modify: `tramalia/mcp_server.py:15-82`
- Modify: `tramalia/tui.py:27-742`
- Modify: `tests/test_headroom.py:42-55` and `tests/test_agentes_modelo.py:46-60` (move their core assertions to the new integration tests)
- Delete: `tramalia/core/governance.py`, `tramalia/core/evidence.py`, `tramalia/core/handoff.py`
- Delete after moving remaining cases: `tests/test_governance.py`, `tests/test_metadata.py`, `tests/test_evidence_handoff.py`
- Delete after moving remaining E2E cases: `tests/test_v016.py`

**Interfaces:**
- Consumes: `exigir_proyecto_gobernado`, `cargar_puertas`, `ejecutar_puertas`, `evaluar_metricas`, `evaluar_cierre`, `publicar_paquete`, `construir_traspaso`, `proyectar_traspaso`.
- Produces: `cerrar_proyecto(raiz: Path, id_tarea: str, *, agente: str = "", revisor: str = "", modelo: str = "", excepciones: Sequence[ExcepcionFallo] = ()) -> ResultadoCierre`; `crear_evidencia(raiz: Path, id_tarea: str, *, agente: str = "", revisor: str = "", modelo: str = "") -> PaqueteEvidencia`; `registrar_traspaso(raiz: Path, id_tarea: str, *, agente: str = "", revisor: str = "") -> PaqueteEvidencia`.

- [ ] **Step 1: Write end-to-end acceptance tests before orchestration exists**

```python
# tests/integracion/test_operaciones.py
import hashlib
import json
import subprocess

import pytest

from tramalia.core import operaciones, puertas_calidad
from tramalia.core.errores import (
    ErrorConfiguracionMetricas,
    ErrorConfiguracionPuertas,
    ErrorPersistenciaEvidencia,
)
from tramalia.core.evidencia import leer_bitacora
from tramalia.core.modelos import ExcepcionFallo, ValorEstadoCierre


def test_sin_mise_bloquea_y_no_aprueba(proyecto_listo, monkeypatch) -> None:
    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: None)
    resultado = operaciones.cerrar_proyecto(proyecto_listo, "TASK-1")
    assert resultado.estado is ValorEstadoCierre.BLOQUEADO
    assert resultado.aprobado is False


def test_toml_invalido_es_error_tipado_y_no_escribe(proyecto_listo) -> None:
    (proyecto_listo / "mise.toml").write_text("[tasks", encoding="utf-8")
    with pytest.raises(ErrorConfiguracionPuertas):
        operaciones.cerrar_proyecto(proyecto_listo, "TASK-2")
    assert not (proyecto_listo / ".tramalia" / "evidencia").exists()


def test_umbrales_corruptos_son_error_tipado_y_no_aprobacion(proyecto_listo) -> None:
    (proyecto_listo / ".tramalia" / "thresholds.json").write_text("{", encoding="utf-8")
    with pytest.raises(ErrorConfiguracionMetricas):
        operaciones.cerrar_proyecto(proyecto_listo, "TASK-2B")
    assert not (proyecto_listo / ".tramalia" / "evidencia").exists()


def test_umbrales_validos_como_json_pero_invalidos_como_esquema_no_escriben(
    proyecto_listo,
) -> None:
    (proyecto_listo / ".tramalia" / "thresholds.json").write_text(
        json.dumps({"coverage": {"minimum": 80}}), encoding="utf-8",
    )
    with pytest.raises(ErrorConfiguracionMetricas):
        operaciones.cerrar_proyecto(proyecto_listo, "TASK-2C")
    assert not (proyecto_listo / ".tramalia" / "evidencia").exists()


def test_puerta_roja_con_excepcion_completa_publica_resultado_honesto(proyecto_listo, monkeypatch) -> None:
    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: "mise")
    monkeypatch.setattr(puertas_calidad.proc, "run", lambda *a, **k: subprocess.CompletedProcess([], 1, "rojo", ""))
    excepcion = ExcepcionFallo("falso positivo", "se acepta el riesgo", "test", "ISSUE-2", "ana",
                               condicion_remediacion="corregir antes del release")
    resultado = operaciones.cerrar_proyecto(
        proyecto_listo,
        "TASK-3",
        modelo="gpt-5",
        excepciones=(excepcion,),
    )
    assert resultado.estado is ValorEstadoCierre.APROBADO_CON_EXCEPCIONES
    metadatos = json.loads((resultado.ruta_paquete / "metadatos.json").read_text(encoding="utf-8"))
    traspaso = (resultado.ruta_paquete / "traspaso.md").read_text(encoding="utf-8")
    assert metadatos["estado_cierre"] == "aprobado_con_excepciones"
    assert metadatos["modelo"] == "gpt-5"
    assert "aprobado_con_excepciones" in traspaso
    salida = (resultado.ruta_paquete / "test-salida.txt").read_bytes()
    assert salida == b"rojo"
    comando = metadatos["comandos"][0]
    assert comando["archivo_salida"] == "test-salida.txt"
    assert comando["hash_salida"] == hashlib.sha256(salida).hexdigest()
    entrada = leer_bitacora(proyecto_listo)[0]
    assert entrada.modelo == "gpt-5"
    assert entrada.resultado is ValorEstadoCierre.APROBADO_CON_EXCEPCIONES


def test_umbral_incumplido_bloquea_y_se_registra(proyecto_listo, monkeypatch) -> None:
    (proyecto_listo / ".tramalia" / "metrics.json").write_text(
        json.dumps({"metrics": {"coverage": 70}}),
        encoding="utf-8",
    )
    (proyecto_listo / ".tramalia" / "thresholds.json").write_text(
        json.dumps({"coverage": {"min": 80}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: "mise")
    monkeypatch.setattr(
        puertas_calidad.proc,
        "run",
        lambda *argumentos, **opciones: subprocess.CompletedProcess([], 0, "ok", ""),
    )
    resultado = operaciones.cerrar_proyecto(proyecto_listo, "TASK-3B")
    assert resultado.estado is ValorEstadoCierre.BLOQUEADO
    assert resultado.bloqueos == ("metrica:coverage",)
    metadatos = json.loads(
        (resultado.ruta_paquete / "metadatos.json").read_text(encoding="utf-8")
    )
    assert metadatos["metricas"] == {"metrics": {"coverage": 70}}
    assert metadatos["umbrales"] == {"coverage": {"min": 80}}


def test_fallo_de_persistencia_no_devuelve_resultado_aprobado(proyecto_listo, monkeypatch) -> None:
    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: "mise")
    monkeypatch.setattr(puertas_calidad.proc, "run", lambda *a, **k: subprocess.CompletedProcess([], 0, "ok", ""))
    monkeypatch.setattr("tramalia.core.evidencia.os.replace",
                        lambda *a: (_ for _ in ()).throw(OSError("disco")))
    with pytest.raises(ErrorPersistenciaEvidencia):
        operaciones.cerrar_proyecto(proyecto_listo, "TASK-4")
```

```python
# tests/contratos/test_operaciones_superficies.py
import ast
import inspect
from pathlib import Path

from tramalia.core.operaciones import cerrar_proyecto, crear_evidencia, registrar_traspaso


def test_firmas_publicas_compartidas() -> None:
    assert str(inspect.signature(cerrar_proyecto)) == "(raiz: 'Path', id_tarea: 'str', *, agente: 'str' = '', revisor: 'str' = '', modelo: 'str' = '', excepciones: 'Sequence[ExcepcionFallo]' = ()) -> 'ResultadoCierre'"
    assert inspect.signature(crear_evidencia).return_annotation == "PaqueteEvidencia"
    assert inspect.signature(registrar_traspaso).return_annotation == "PaqueteEvidencia"


def test_no_quedan_imports_del_nucleo_historico() -> None:
    modulos = {"governance", "evidence", "handoff"}
    for base in (Path("tramalia"), Path("tests")):
        for ruta in base.rglob("*.py"):
            arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
            for nodo in ast.walk(arbol):
                if isinstance(nodo, ast.Import):
                    assert not any(
                        alias.name in {f"tramalia.core.{nombre}" for nombre in modulos}
                        for alias in nodo.names
                    ), ruta
                if isinstance(nodo, ast.ImportFrom):
                    assert nodo.module not in {f"tramalia.core.{nombre}" for nombre in modulos}, ruta
                    if nodo.module == "tramalia.core":
                        assert not ({alias.name for alias in nodo.names} & modulos), ruta
```

- [ ] **Step 2: Run and verify the missing operations API fails**

Run: `uv run pytest tests/integracion/test_operaciones.py tests/contratos/test_operaciones_superficies.py -q`

Expected: FAIL during collection with `ImportError: cannot import name 'operaciones'`.

- [ ] **Step 3: Implement the orchestration helpers and three public operations**

```python
# tramalia/core/operaciones.py
"""Shared mutating operations for CLI, TUI and MCP."""
from __future__ import annotations

import json
import platform
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from tramalia import __version__
from tramalia.core.errores import ErrorConfiguracionMetricas
from tramalia.core.evidencia import (capturar_estado_git, crear_id_paquete,
                                     publicar_paquete, validar_id_tarea)
from tramalia.core.modelos import (EjecucionPuertas, ExcepcionFallo, MetadatosPaqueteEvidencia,
                                   PaqueteEvidencia, ResultadoCierre, ValorEstadoCierre,
                                   ValorEstadoPuertas)
from tramalia.core.politica_cierre import evaluar_cierre, evaluar_metricas
from tramalia.core.proyecto import exigir_proyecto_gobernado
from tramalia.core.puertas_calidad import cargar_puertas, ejecutar_puertas
from tramalia.core.traspaso import construir_traspaso, proyectar_traspaso


def _leer_json(ruta: Path) -> Mapping[str, object]:
    if not ruta.is_file():
        return {}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ErrorConfiguracionMetricas(
            "La configuracion de metricas no es JSON valido.",
            "Corrige el archivo antes de cerrar la tarea.",
            ruta,
            {"tipo": type(error).__name__},
        ) from error
    if not isinstance(datos, dict):
        raise ErrorConfiguracionMetricas(
            "La configuracion de metricas debe ser un objeto JSON.",
            "Usa pares nombre/valor para metricas y umbrales.",
            ruta,
        )
    return datos


def _construir_metadatos(raiz: Path, id_paquete: str, id_tarea: str, operacion: str,
              inicio: datetime, fin: datetime, ejecucion: EjecucionPuertas,
              estado: ValorEstadoCierre, agente: str, modelo: str,
              metricas: Mapping[str, object], umbrales: Mapping[str, object],
              bloqueos: Sequence[str], excepciones: Sequence[ExcepcionFallo]) -> MetadatosPaqueteEvidencia:
    return MetadatosPaqueteEvidencia(
        1, id_paquete, id_tarea, operacion, inicio, fin, __version__,
        platform.python_version(), platform.platform(), {"mise": None},
        capturar_estado_git(raiz), ejecucion, estado, agente or None, modelo or None,
        metricas, umbrales, tuple(bloqueos), tuple(excepciones), "traspaso.md")


def _publicar(raiz: Path, metadatos: MetadatosPaqueteEvidencia,
              resultado: ResultadoCierre, agente: str, revisor: str) -> PaqueteEvidencia:
    archivos = {r.archivo_salida: r.salida.encode("utf-8") for r in metadatos.ejecucion.resultados}
    archivos["traspaso.md"] = construir_traspaso(resultado, agente, revisor)
    if metadatos.metricas:
        archivos["metricas.json"] = (json.dumps(metadatos.metricas, ensure_ascii=False, indent=2) + "\n").encode()
    paquete = publicar_paquete(raiz, metadatos, archivos)
    proyectar_traspaso(raiz, paquete)
    return paquete


def cerrar_proyecto(raiz: Path, id_tarea: str, *, agente: str = "", revisor: str = "",
                    modelo: str = "", excepciones: Sequence[ExcepcionFallo] = ()) -> ResultadoCierre:
    """Run gates, evaluate policy and atomically publish one closure pack.

    Raises:
        ErrorTramalia: For unsafe input, invalid configuration or persistence failure.
    """
    exigir_proyecto_gobernado(raiz)
    validar_id_tarea(id_tarea)
    inicio = datetime.now(UTC)
    puertas = cargar_puertas(raiz)
    ejecucion = ejecutar_puertas(raiz, puertas)
    metricas = _leer_json(raiz / ".tramalia" / "metrics.json")
    umbrales = _leer_json(raiz / ".tramalia" / "thresholds.json")
    incumplimientos = evaluar_metricas(metricas, umbrales) if umbrales else ()
    estado, bloqueos = evaluar_cierre(ejecucion, incumplimientos, excepciones, datetime.now(UTC))
    id_paquete = crear_id_paquete()
    provisional = ResultadoCierre(estado, id_tarea, id_paquete, None, None,
                                  ejecucion, tuple(excepciones), bloqueos)
    metadatos = _construir_metadatos(raiz, id_paquete, id_tarea, "cierre", inicio,
                          datetime.now(UTC), ejecucion, estado, agente,
                          modelo, metricas, umbrales, bloqueos, excepciones)
    paquete = _publicar(raiz, metadatos, provisional, agente, revisor)
    return replace(provisional, ruta_paquete=paquete.ruta,
                   ruta_traspaso=paquete.ruta / "traspaso.md")


def crear_evidencia(raiz: Path, id_tarea: str, *, agente: str = "", revisor: str = "",
                    modelo: str = "") -> PaqueteEvidencia:
    """Publish a formal non-closure evidence pack with a blocked result."""
    exigir_proyecto_gobernado(raiz)
    validar_id_tarea(id_tarea)
    ahora = datetime.now(UTC)
    ejecucion = EjecucionPuertas(ValorEstadoPuertas.SIN_CONFIGURAR)
    id_paquete = crear_id_paquete(ahora)
    resultado = ResultadoCierre(ValorEstadoCierre.BLOQUEADO, id_tarea, id_paquete,
                                None, None, ejecucion, (), ("operacion_evidencia",))
    metadatos = _construir_metadatos(raiz, id_paquete, id_tarea, "evidencia", ahora, ahora,
                          ejecucion, resultado.estado, agente, modelo, {}, {},
                          resultado.bloqueos, ())
    return _publicar(raiz, metadatos, resultado, agente, revisor)


def registrar_traspaso(raiz: Path, id_tarea: str, *, agente: str = "",
                       revisor: str = "") -> PaqueteEvidencia:
    """Publish a standalone canonical handoff in a new immutable pack."""
    exigir_proyecto_gobernado(raiz)
    validar_id_tarea(id_tarea)
    ahora = datetime.now(UTC)
    ejecucion = EjecucionPuertas(ValorEstadoPuertas.SIN_CONFIGURAR)
    id_paquete = crear_id_paquete(ahora)
    resultado = ValorEstadoCierre.BLOQUEADO
    cierre = ResultadoCierre(resultado, id_tarea, id_paquete, None, None,
                             ejecucion, (), ("operacion_traspaso",))
    metadatos = _construir_metadatos(raiz, id_paquete, id_tarea, "traspaso", ahora, ahora,
                          ejecucion, resultado, agente, "", {}, {}, cierre.bloqueos, ())
    return _publicar(raiz, metadatos, cierre, agente, revisor)
```

- [ ] **Step 4: Route CLI, MCP and TUI without translating policy**

```text
# tramalia/cli/commands.py: núcleo de cmd_close; el renderizado permanece en el comando.
resultado = cerrar_proyecto(
    Path.cwd(), id_tarea, agente=agente, revisor=revisor,
    modelo=getattr(args, "model", None) or "", excepciones=excepciones,
)
return 0 if resultado.aprobado else 1

# tramalia/mcp_server.py: las tools devuelven modelos; nunca recalculan una segunda política.
resultado = cerrar_proyecto(Path.cwd(), task, agente=agent, revisor=reviewer,
                            excepciones=excepciones)
return {"estado": resultado.estado.value, "id_paquete": resultado.id_paquete,
        "bloqueos": list(resultado.bloqueos)}

# tramalia/tui.py: el worker existente llama la misma operación hasta que el plan 03 extraiga ServicioTablero.
resultado = cerrar_proyecto(Path.cwd(), id_tarea, agente=agente,
                            revisor=revisor, modelo=modelo)
self.call_from_thread(self._mostrar_resultado_cierre, resultado)
```

Para `--allow-fail`, conservar ese alias público inglés durante una versión como disparador deprecado, pero añadir un único juego de flags explícitas en español: `--razon-excepcion`, `--riesgo-aceptado`, `--control-afectado`, `--referencia-excepcion`, `--revisor-excepcion`, `--expira-en` y `--condicion-remediacion`. Construir `ExcepcionFallo` sólo cuando estén todos los campos requeridos; de lo contrario lanzar `ErrorExcepcionInvalida` antes de `cerrar_proyecto`. MCP expone los mismos campos. La TUI puede omitir el formulario en este plan y por tanto permanece bloqueada de forma segura; el plan 03 añade su formulario tipado.

- [ ] **Step 5: Remove historical modules and prove all imports are gone**

Run: `rg -n "tramalia\.core\.(governance|evidence|handoff)|from tramalia\.core import (governance|evidence|handoff)" tramalia tests`

Expected: no matches.

Delete: `tramalia/core/governance.py`, `tramalia/core/evidence.py`, `tramalia/core/handoff.py` y, después de trasladar sus E2E restantes a `tests/integracion/test_operaciones.py`, `tests/test_v016.py`.

- [ ] **Step 6: Run focused and complete verification**

Run: `uv run pytest tests/unidad/test_errores_modelos.py tests/unidad/test_proyecto_gobernado.py tests/unidad/test_puertas_calidad.py tests/unidad/test_politica_cierre.py tests/unidad/test_metricas_cierre.py tests/unidad/test_identidad_evidencia.py tests/contratos/test_metadatos_evidencia_v1.py tests/contratos/test_operaciones_superficies.py tests/integracion/test_evidencia_atomica.py tests/integracion/test_traspaso_bitacora.py tests/integracion/test_operaciones.py -q`

Expected: PASS.

Run: `uv run pytest -q`

Expected: PASS with no assertions for `passed`, `passed_with_exceptions`, `no_gates`, `CloseResult`, Markdown log fallback, empty `.tramalia` initialization, or shared `lint`/`format` output.

Run: `uv run ruff check . --fix && uv run ruff format . && uv run ruff check . && uv run ruff format --check .`

Expected: PASS sin imports tardíos/sin usar ni incumplimientos `E`, `F`, `I` o `UP`.

Run: `uv run --no-sync python -m compileall -q tramalia`

Expected: exit code 0 and no output.

- [ ] **Step 7: Commit the shared operations and breaking removal**

```bash
git add tramalia/core/operaciones.py tramalia/cli/commands.py tramalia/mcp_server.py tramalia/tui.py tramalia/__main__.py tests
git rm tramalia/core/governance.py tramalia/core/evidence.py tramalia/core/handoff.py
git commit -m "feat: unificar cierre evidencia y traspaso"
```

### Task 9: Auditoría final de contratos del núcleo

**Files:**
- Modify only if an audit fails: files named by the failing command above.

**Interfaces:**
- Consumes: every public contract introduced in Tasks 1-8.
- Produces: a green, executable core milestone ready for the integrations/TUI plan.

- [ ] **Step 1: Check Spanish ASCII ownership and forbidden legacy vocabulary**

Run: `rg -n "class CloseResult|def (close|build_evidence|new_handoff|gate_tasks|run_gates|read_log|is_initialized)|_GATE_ORDER" tramalia tests`

Run: `rg -n "def _git|\b(tokens|base_windows)\b" tramalia/core/evidencia.py tests/unidad/test_identidad_evidencia.py tests/contratos/test_metadatos_evidencia_v1.py`

Run: `rg -n "\b(build_cmds|test_cmds|lint_cmds)\b" tramalia/core/scaffold.py`

Expected: no matches.

Run: `uv run --no-sync python -c "import ast,pathlib; malos=[]; [malos.extend((str(ruta),nodo.name) for nodo in ast.walk(ast.parse(ruta.read_text(encoding='utf-8'))) if isinstance(nodo,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and any(ord(caracter)>127 for caracter in nodo.name)) for ruta in pathlib.Path('tramalia').rglob('*.py')]; assert not malos, malos"`

Expected: exit code 0.

- [ ] **Step 2: Prove no approved result can be constructed by an uncovered gate path**

Run: `uv run pytest tests/unidad/test_politica_cierre.py tests/integracion/test_operaciones.py -q`

Expected: PASS, including missing mise, missing gates, red gates, runtime errors and thresholds.

- [ ] **Step 3: Prove formal evidence is immutable and structured**

Run: `uv run pytest tests/contratos/test_metadatos_evidencia_v1.py tests/integracion/test_evidencia_atomica.py tests/integracion/test_traspaso_bitacora.py -q`

Expected: PASS, including concurrent close IDs, injected rename failure, containment and corrupt metadata.

- [ ] **Step 4: Run the full suite one final time**

Run: `uv run pytest -q`

Expected: PASS.

- [ ] **Step 5: Commit audit-only corrections if any test required a change**

```bash
git add tramalia tests
git commit -m "test: cerrar contratos del nucleo fail closed"
```

If no file changed during the audit, skip this commit.
