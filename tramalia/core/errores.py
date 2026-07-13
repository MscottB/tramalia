"""Domain errors shared by every Tramalia surface."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TypeVar

_SECRETOS = {"token", "secret", "password", "contrasena", "api_key", "authorization"}
_TipoClave = TypeVar("_TipoClave")


def _sanear(valor: object, clave: str = "") -> object:
    if clave.lower() in _SECRETOS:
        return "[REDACTADO]"
    if isinstance(valor, Mapping):
        return _sanear_mapeo(valor)
    if isinstance(valor, (list, tuple)):
        return [_sanear(elemento) for elemento in valor]
    return valor


def _sanear_mapeo(valores: Mapping[_TipoClave, object]) -> dict[str, object]:
    return {str(llave): _sanear(elemento, str(llave)) for llave, elemento in valores.items()}


class ErrorTramalia(Exception):
    """Represent a stable, recoverable domain failure.

    Args:
        mensaje: Human-readable description.
        sugerencia: Concrete recovery action.
        ruta: Related path, if any.
        detalles: Structured context; secret-looking fields are redacted.
    """

    codigo = "error_tramalia"

    def __init__(
        self,
        mensaje: str,
        sugerencia: str,
        ruta: Path | None = None,
        detalles: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.sugerencia = sugerencia
        self.ruta = ruta
        self.detalles = _sanear_mapeo(detalles or {})

    def como_dict(self) -> dict[str, object]:
        """Return a secret-safe representation for CLI, TUI, and MCP."""
        return {
            "codigo": self.codigo,
            "mensaje": self.mensaje,
            "sugerencia": self.sugerencia,
            "ruta": str(self.ruta) if self.ruta else None,
            "detalles": self.detalles,
        }


class ErrorProyectoNoGobernado(ErrorTramalia):
    """Report that a project lacks the required governance contract."""

    codigo = "proyecto_no_gobernado"


class ErrorConfiguracionPuertas(ErrorTramalia):
    """Report an invalid quality-gate configuration."""

    codigo = "configuracion_puertas_invalida"


class ErrorConfiguracionMetricas(ErrorTramalia):
    """Report an invalid metrics configuration."""

    codigo = "configuracion_metricas_invalida"


class ErrorIdentificadorInseguro(ErrorTramalia):
    """Report a task identifier that is unsafe for persistence."""

    codigo = "id_tarea_inseguro"


class ErrorExcepcionInvalida(ErrorTramalia):
    """Report an exception waiver that does not satisfy its contract."""

    codigo = "excepcion_invalida"


class ErrorPersistenciaEvidencia(ErrorTramalia):
    """Report a failure while persisting an evidence package."""

    codigo = "persistencia_evidencia_fallida"
