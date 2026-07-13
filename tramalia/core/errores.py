"""Domain errors shared by every Tramalia surface."""

from __future__ import annotations

import base64
import json
import math
from collections.abc import Mapping
from datetime import date, datetime, time
from enum import Enum
from pathlib import Path
from typing import TypeAlias, TypeVar

_SECRETOS = {"token", "secret", "password", "contrasena", "api_key", "authorization"}
_TipoClave = TypeVar("_TipoClave")
_ValorJSON: TypeAlias = (
    str | int | float | bool | None | list["_ValorJSON"] | dict[str, "_ValorJSON"]
)


def _etiqueta_tipo(valor: object) -> str:
    tipo = type(valor)
    return f"<objeto_no_serializable:{tipo.__module__}.{tipo.__qualname__}>"


def _texto_bytes(valor: bytes | bytearray) -> str:
    contenido = base64.b64encode(bytes(valor)).decode("ascii")
    return f"base64:{contenido}"


def _clave_orden_json(valor: _ValorJSON) -> str:
    return json.dumps(
        valor,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _normalizar_clave_json(valor: object) -> str:
    normalizado = _normalizar_json(valor)
    if isinstance(normalizado, str):
        return normalizado
    return _clave_orden_json(normalizado)


def _normalizar_json(
    valor: object,
    clave: str = "",
    visitados: set[int] | None = None,
) -> _ValorJSON:
    """Return deterministic JSON data without exposing arbitrary object state.

    Secret fields are redacted before their values are inspected. Unsupported leaves are
    replaced by a stable type-only marker; their ``str`` and ``repr`` methods are never used.
    Cycles are represented by a stable marker instead of recursing indefinitely.
    """
    if clave.lower() in _SECRETOS:
        return "[REDACTADO]"
    if visitados is None:
        visitados = set()
    if isinstance(valor, Enum):
        return _normalizar_json(valor.value, visitados=visitados)
    if valor is None or isinstance(valor, (str, bool)):
        return valor
    if isinstance(valor, int):
        return int(valor)
    if isinstance(valor, float):
        if math.isnan(valor):
            return "NaN"
        if math.isinf(valor):
            return "Infinity" if valor > 0 else "-Infinity"
        return float(valor)
    if isinstance(valor, Path):
        return str(valor)
    if isinstance(valor, (datetime, date, time)):
        return valor.isoformat()
    if isinstance(valor, (bytes, bytearray)):
        return _texto_bytes(valor)
    if isinstance(valor, Mapping):
        identificador = id(valor)
        if identificador in visitados:
            return "<referencia_ciclica>"
        return _normalizar_mapeo(valor, visitados)
    if isinstance(valor, (list, tuple)):
        identificador = id(valor)
        if identificador in visitados:
            return "<referencia_ciclica>"
        visitados.add(identificador)
        try:
            return [_normalizar_json(elemento, visitados=visitados) for elemento in valor]
        finally:
            visitados.remove(identificador)
    if isinstance(valor, (set, frozenset)):
        identificador = id(valor)
        if identificador in visitados:
            return "<referencia_ciclica>"
        visitados.add(identificador)
        try:
            elementos = [_normalizar_json(elemento, visitados=visitados) for elemento in valor]
            return sorted(elementos, key=_clave_orden_json)
        finally:
            visitados.remove(identificador)
    return _etiqueta_tipo(valor)


def _normalizar_mapeo(
    valores: Mapping[_TipoClave, object],
    visitados: set[int] | None = None,
) -> dict[str, _ValorJSON]:
    if visitados is None:
        visitados = set()
    identificador = id(valores)
    visitados.add(identificador)
    try:
        pares = []
        for llave, elemento in valores.items():
            clave = _normalizar_clave_json(llave)
            pares.append((clave, _normalizar_json(elemento, clave, visitados)))
        pares.sort(key=lambda par: (par[0], _clave_orden_json(par[1])))
        return dict(pares)
    finally:
        visitados.remove(identificador)


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
        self.detalles: dict[str, _ValorJSON] = _normalizar_mapeo(detalles or {})

    def como_dict(self) -> dict[str, _ValorJSON]:
        """Return deterministic, secret-safe JSON data for CLI, TUI, and MCP.

        Arbitrary unsupported leaves become stable type-only markers so callers can pass the
        result directly to ``json.dumps`` without a custom ``default`` function.
        """
        return _normalizar_mapeo(
            {
                "codigo": self.codigo,
                "mensaje": self.mensaje,
                "sugerencia": self.sugerencia,
                "ruta": self.ruta,
                "detalles": self.detalles,
            }
        )


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


class ErrorArgumentosMCPConflictivos(ErrorTramalia):
    """Report contradictory legacy and Spanish MCP argument aliases."""

    codigo = "argumentos_mcp_conflictivos"


class ErrorPersistenciaEvidencia(ErrorTramalia):
    """Report a failure while persisting an evidence package."""

    codigo = "persistencia_evidencia_fallida"
