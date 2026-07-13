"""Typed domain contracts for Tramalia core operations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from tramalia.core.errores import ErrorExcepcionInvalida


def _tiene_desfase_utc(instante: datetime) -> bool:
    return instante.tzinfo is not None and instante.utcoffset() is not None


class ValorEstadoProyecto(StrEnum):
    """Describe whether a project satisfies the governance contract."""

    LISTO = "listo"
    HEREDADO = "heredado"
    PARCIAL = "parcial"
    AUSENTE = "ausente"


class ValorEstadoPuertas(StrEnum):
    """Describe the aggregate result of a quality-gate execution."""

    APROBADO = "aprobado"
    FALLIDO = "fallido"
    EJECUTOR_NO_DISPONIBLE = "ejecutor_no_disponible"
    SIN_CONFIGURAR = "sin_configurar"
    CONFIGURACION_INVALIDA = "configuracion_invalida"
    ERROR_EJECUCION = "error_ejecucion"


class ValorResultadoPuerta(StrEnum):
    """Describe the result of one quality gate."""

    APROBADO = "aprobado"
    FALLIDO = "fallido"
    OMITIDO = "omitido"
    ERROR_EJECUCION = "error_ejecucion"


class ValorEstadoCierre(StrEnum):
    """Describe the final state of a governed task closure."""

    APROBADO = "aprobado"
    APROBADO_CON_EXCEPCIONES = "aprobado_con_excepciones"
    BLOQUEADO = "bloqueado"


class ValorEstadoIntegracion(StrEnum):
    """Describe the availability of an optional integration."""

    COMPLETO = "completo"
    DEGRADADO = "degradado"
    NO_DISPONIBLE = "no_disponible"
    FALLIDO = "fallido"


class ValorEstadoBitacora(StrEnum):
    """Describe whether a log entry can be trusted."""

    VALIDA = "valida"
    INVALIDA = "invalida"


@dataclass(frozen=True, slots=True)
class EstadoProyecto:
    """Summarize governance readiness for a project root."""

    estado: ValorEstadoProyecto
    raiz: Path
    problemas: tuple[str, ...] = ()
    comando_reparacion: str | None = None

    @property
    def listo(self) -> bool:
        """Return whether the project is ready for governed operations."""
        return self.estado is ValorEstadoProyecto.LISTO


@dataclass(frozen=True, slots=True)
class PuertaCalidad:
    """Define one executable quality gate."""

    nombre: str
    comando: tuple[str, ...]
    archivo_salida: str


@dataclass(frozen=True, slots=True)
class ResultadoPuerta:
    """Record the immutable outcome of one quality gate."""

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
    """Aggregate discovery, execution, and validation for quality gates."""

    estado: ValorEstadoPuertas
    descubiertas: tuple[str, ...] = ()
    ejecutadas: tuple[str, ...] = ()
    omitidas: tuple[str, ...] = ()
    fallidas: tuple[str, ...] = ()
    resultados: tuple[ResultadoPuerta, ...] = ()
    errores_validacion: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExcepcionFallo:
    """Describe a reviewed and time-bound or remediable failure waiver."""

    razon: str
    riesgo_aceptado: str
    control_afectado: str
    referencia: str
    revisor: str
    expira_en: datetime | None = None
    condicion_remediacion: str | None = None

    def __post_init__(self) -> None:
        faltantes = [
            nombre
            for nombre in (
                "razon",
                "riesgo_aceptado",
                "control_afectado",
                "referencia",
                "revisor",
            )
            if not str(getattr(self, nombre)).strip()
        ]
        if not self.expira_en and not (self.condicion_remediacion or "").strip():
            faltantes.append("expira_en_o_condicion_remediacion")
        if self.expira_en is not None and not _tiene_desfase_utc(self.expira_en):
            faltantes.append("expira_en_con_zona_horaria")
        if faltantes:
            raise ErrorExcepcionInvalida(
                "La excepcion no cumple el contrato.",
                "Completa razon, riesgo, control, referencia, revisor y expiracion o remediacion.",
                detalles={"campos": faltantes},
            )

    def vigente(self, ahora: datetime) -> bool:
        """Return whether the waiver remains valid at the given instant.

        Args:
            ahora: Timezone-aware instant used for the comparison.

        Returns:
            True when no expiry exists or the expiry has not passed.
        """
        if not _tiene_desfase_utc(ahora):
            raise ErrorExcepcionInvalida(
                "El instante actual no cumple el contrato.",
                "Proporciona ahora con zona horaria y desfase UTC definido.",
                detalles={"campos": ["ahora_con_zona_horaria"]},
            )
        return self.expira_en is None or ahora <= self.expira_en


@dataclass(frozen=True, slots=True)
class EstadoGit:
    """Capture the relevant Git state for an evidence package."""

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
    """Store the complete metadata contract for an evidence package."""

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
    """Reference a persisted evidence package and its metadata."""

    id_paquete: str
    ruta: Path
    metadatos: MetadatosPaqueteEvidencia


@dataclass(frozen=True, slots=True)
class ResultadoCierre:
    """Record the result of a governed task closure."""

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
        """Return whether closure succeeded, including reviewed exceptions."""
        return self.estado in {
            ValorEstadoCierre.APROBADO,
            ValorEstadoCierre.APROBADO_CON_EXCEPCIONES,
        }


@dataclass(frozen=True, slots=True)
class EntradaBitacora:
    """Describe one evidence package entry in the audit log."""

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
    """Describe the effective adapter behind an optional capability."""

    estado: ValorEstadoIntegracion
    capacidad: str
    solicitado: str | None
    utilizado: str | None
    motivo: str
    impacto: str
    remediacion: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "estado", ValorEstadoIntegracion(self.estado))
        if self.estado is ValorEstadoIntegracion.DEGRADADO and not (self.utilizado or "").strip():
            raise ValueError("utilizado es obligatorio para un fallback degradado exitoso")

    @property
    def exitoso(self) -> bool:
        """Return whether the requested capability has an effective adapter."""
        return self.estado in {
            ValorEstadoIntegracion.COMPLETO,
            ValorEstadoIntegracion.DEGRADADO,
        }
