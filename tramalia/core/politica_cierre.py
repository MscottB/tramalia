"""Evaluate closure policy independently from presentation and persistence."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import datetime

from tramalia.core.errores import ErrorConfiguracionMetricas, ErrorExcepcionInvalida
from tramalia.core.modelos import (
    EjecucionPuertas,
    ExcepcionFallo,
    ValorEstadoCierre,
    ValorEstadoPuertas,
)


def _error_regla(
    mensaje: str,
    sugerencia: str,
    *,
    metrica: str | None = None,
    detalles: Mapping[str, object] | None = None,
) -> ErrorConfiguracionMetricas:
    contexto: dict[str, object] = dict(detalles or {})
    if metrica is not None:
        contexto["metrica"] = metrica
    return ErrorConfiguracionMetricas(
        mensaje,
        sugerencia,
        detalles=contexto,
    )


def _validar_regla_umbral(nombre: object, regla: object) -> tuple[str, dict[str, float]]:
    if not isinstance(nombre, str) or not nombre.strip():
        raise _error_regla(
            "El nombre de la metrica no cumple el contrato.",
            "Usa un nombre de metrica de texto no vacio.",
            detalles={"tipo_nombre": type(nombre).__name__},
        )
    if not isinstance(regla, Mapping):
        raise _error_regla(
            "La regla de umbral debe ser un objeto.",
            "Define min, max o ambos para la metrica.",
            metrica=nombre,
            detalles={"tipo_regla": type(regla).__name__},
        )

    claves = tuple(regla.keys())
    if not claves:
        raise _error_regla(
            "La regla de umbral esta vacia.",
            "Define min, max o ambos para la metrica.",
            metrica=nombre,
        )
    if not all(isinstance(clave, str) for clave in claves):
        raise _error_regla(
            "La regla de umbral contiene claves invalidas.",
            "Usa exclusivamente las claves min y max.",
            metrica=nombre,
            detalles={
                "tipos_clave": sorted({type(clave).__name__ for clave in claves}),
            },
        )
    claves_texto = set(claves)
    if not claves_texto <= {"min", "max"}:
        raise _error_regla(
            "La regla de umbral contiene claves desconocidas.",
            "Usa exclusivamente las claves min y max.",
            metrica=nombre,
            detalles={"claves": sorted(claves_texto)},
        )

    limites: dict[str, float] = {}
    # El orden fijo mantiene diagnosticos reproducibles aunque el TOML invierta min/max.
    for clave in ("min", "max"):
        if clave not in claves_texto:
            continue
        valor = regla[clave]
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise _error_regla(
                "Los limites del umbral deben ser numericos.",
                "Reemplaza el limite por un numero finito.",
                metrica=nombre,
                detalles={"limite": clave, "tipo_valor": type(valor).__name__},
            )
        try:
            limite = float(valor)
        except (OverflowError, TypeError, ValueError) as error:
            raise _error_regla(
                "El limite no se puede representar de forma finita.",
                "Usa un numero finito dentro del rango de Python.",
                metrica=nombre,
                detalles={"limite": clave, "tipo_error": type(error).__name__},
            ) from error
        if not math.isfinite(limite):
            raise _error_regla(
                "Los limites del umbral deben ser finitos.",
                "Reemplaza NaN o infinito por un numero finito.",
                metrica=nombre,
                detalles={"limite": clave},
            )
        limites[clave] = limite

    if "min" in limites and "max" in limites and limites["min"] > limites["max"]:
        raise _error_regla(
            "El minimo del umbral supera al maximo.",
            "Ajusta los limites para que min sea menor o igual que max.",
            metrica=nombre,
        )
    return nombre, limites


def _valor_medido_valido(valor: object) -> bool:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return False
    return not isinstance(valor, float) or math.isfinite(valor)


def _sin_duplicados(valores: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(valores))


def evaluar_metricas(
    metricas: Mapping[str, object],
    umbrales: Mapping[str, object],
) -> tuple[str, ...]:
    """Return stable blockers for missing, invalid, or out-of-range metrics.

    Args:
        metricas: Measured values, either flat or nested under ``metrics``.
        umbrales: Threshold rules keyed by metric name.

    Returns:
        Stable ``metrica:<name>`` blocker identifiers.

    Raises:
        ErrorConfiguracionMetricas: If any threshold rule is invalid.
    """
    # Se valida todo el esquema antes de mirar resultados para impedir evaluaciones parciales.
    reglas = tuple(_validar_regla_umbral(nombre, regla) for nombre, regla in umbrales.items())
    valores_candidatos = metricas.get("metrics", metricas)
    valores = valores_candidatos if isinstance(valores_candidatos, Mapping) else {}
    bloqueos: list[str] = []

    for nombre, limites in reglas:
        if nombre not in valores:
            bloqueos.append(f"metrica:{nombre}")
            continue
        valor = valores[nombre]
        if not _valor_medido_valido(valor):
            bloqueos.append(f"metrica:{nombre}")
            continue
        if ("min" in limites and valor < limites["min"]) or (
            "max" in limites and valor > limites["max"]
        ):
            bloqueos.append(f"metrica:{nombre}")

    return _sin_duplicados(bloqueos)


def _validar_instante(ahora: datetime) -> None:
    try:
        tiene_desfase = ahora.tzinfo is not None and ahora.utcoffset() is not None
    except Exception as error:
        raise ErrorExcepcionInvalida(
            "El instante de evaluacion no cumple el contrato.",
            "Proporciona ahora con una zona horaria y desfase UTC validos.",
            detalles={"tipo_error": type(error).__name__},
        ) from error
    if not tiene_desfase:
        raise ErrorExcepcionInvalida(
            "El instante de evaluacion no cumple el contrato.",
            "Proporciona ahora con una zona horaria y desfase UTC validos.",
            detalles={"campo": "ahora"},
        )


def evaluar_cierre(
    ejecucion: EjecucionPuertas,
    incumplimientos: Sequence[str],
    excepciones: Sequence[ExcepcionFallo],
    ahora: datetime,
) -> tuple[ValorEstadoCierre, tuple[str, ...]]:
    """Compute the final closure state and its uncovered blockers.

    Args:
        ejecucion: Aggregate quality-gate execution result.
        incumplimientos: Additional stable blocker identifiers, such as metrics.
        excepciones: Reviewed exceptions that may cover exact controls.
        ahora: Timezone-aware instant used to validate exception expiry.

    Returns:
        Final closure state and uncovered blocker identifiers.

    Raises:
        ErrorExcepcionInvalida: If the instant is naive or an exception has expired.
    """
    _validar_instante(ahora)
    for excepcion in excepciones:
        if not excepcion.vigente(ahora):
            raise ErrorExcepcionInvalida(
                "La excepcion ya no esta vigente.",
                "Renueva la aprobacion o corrige el bloqueo.",
                detalles={"control": excepcion.control_afectado},
            )

    if ejecucion.estado is ValorEstadoPuertas.CONFIGURACION_INVALIDA:
        # Una configuracion invalida no es riesgo aceptable: impide saber que se valido.
        return ValorEstadoCierre.BLOQUEADO, ("configuracion",)

    controles: list[str] = list(incumplimientos)
    if ejecucion.estado is ValorEstadoPuertas.EJECUTOR_NO_DISPONIBLE:
        controles.append("ejecutor")
    elif ejecucion.estado is ValorEstadoPuertas.SIN_CONFIGURAR:
        controles.append("puertas")
    elif ejecucion.estado is ValorEstadoPuertas.ERROR_EJECUCION:
        controles.extend(ejecucion.fallidas or ("ejecucion",))
    elif ejecucion.estado is ValorEstadoPuertas.FALLIDO:
        if not ejecucion.fallidas:
            return ValorEstadoCierre.BLOQUEADO, _sin_duplicados([*controles, "ejecucion"])
        controles.extend(ejecucion.fallidas)
    elif ejecucion.estado is ValorEstadoPuertas.APROBADO:
        if not ejecucion.ejecutadas:
            return ValorEstadoCierre.BLOQUEADO, _sin_duplicados([*controles, "puertas"])
        if ejecucion.fallidas or ejecucion.omitidas:
            return ValorEstadoCierre.BLOQUEADO, _sin_duplicados([*controles, "ejecucion"])

    controles_unicos = _sin_duplicados(controles)
    cubiertos = {excepcion.control_afectado for excepcion in excepciones}
    pendientes = tuple(control for control in controles_unicos if control not in cubiertos)
    if pendientes:
        return ValorEstadoCierre.BLOQUEADO, pendientes
    if controles_unicos:
        return ValorEstadoCierre.APROBADO_CON_EXCEPCIONES, ()
    if ejecucion.estado is ValorEstadoPuertas.APROBADO and ejecucion.ejecutadas:
        return ValorEstadoCierre.APROBADO, ()
    return ValorEstadoCierre.BLOQUEADO, ("puertas",)
