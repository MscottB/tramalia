"""Load and execute quality gates without fail-open fallbacks."""

from __future__ import annotations

import hashlib
import tomllib
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

from tramalia.core import procesos
from tramalia.core.errores import ErrorConfiguracionPuertas
from tramalia.core.modelos import (
    EjecucionPuertas,
    PuertaCalidad,
    ResultadoPuerta,
    ValorEstadoPuertas,
    ValorResultadoPuerta,
)

_ORDEN_PUERTAS = (
    "build",
    "test",
    "lint",
    "format",
    "security",
    "database",
    "bundle",
    "notebooks",
    "ux",
)


def _error_configuracion(
    ruta: Path,
    *,
    puerta: str | None = None,
    tipo_error: str | None = None,
) -> ErrorConfiguracionPuertas:
    detalles = {}
    if puerta is not None:
        detalles["puerta"] = puerta
    if tipo_error is not None:
        detalles["tipo_error"] = tipo_error
    return ErrorConfiguracionPuertas(
        "mise.toml no cumple el contrato de puertas.",
        "Define tasks como tabla y cada puerta conocida como tabla con run no vacio.",
        ruta,
        detalles or None,
    )


def _run_valido(valor: object) -> bool:
    if isinstance(valor, str):
        return bool(valor.strip())
    if not isinstance(valor, list) or not valor:
        return False
    return all(isinstance(elemento, str) and bool(elemento.strip()) for elemento in valor)


def cargar_puertas(raiz: Path) -> tuple[PuertaCalidad, ...]:
    """Load applicable quality gates from ``mise.toml``.

    Args:
        raiz: Project root that may contain ``mise.toml``.

    Returns:
        Known gates in their stable execution order.

    Raises:
        ErrorConfiguracionPuertas: If the file cannot be read or its gate schema is invalid.
    """
    ruta = raiz / "mise.toml"
    try:
        contenido = ruta.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ()
    except (OSError, UnicodeError) as error:
        raise _error_configuracion(ruta, tipo_error=type(error).__name__) from error

    try:
        datos = tomllib.loads(contenido)
    except tomllib.TOMLDecodeError as error:
        raise _error_configuracion(ruta, tipo_error=type(error).__name__) from error

    tareas = datos.get("tasks", {})
    if not isinstance(tareas, dict):
        raise _error_configuracion(ruta)

    puertas: list[PuertaCalidad] = []
    for nombre in _ORDEN_PUERTAS:
        if nombre not in tareas:
            continue
        declaracion = tareas[nombre]
        if not isinstance(declaracion, dict) or not _run_valido(declaracion.get("run")):
            raise _error_configuracion(ruta, puerta=nombre)
        puertas.append(
            PuertaCalidad(
                nombre=nombre,
                comando=("mise", "run", nombre),
                archivo_salida=f"{nombre}-salida.txt",
            )
        )
    return tuple(puertas)


def ejecutar_puertas(
    raiz: Path,
    puertas: Sequence[PuertaCalidad],
    *,
    verificar_configuracion: Callable[[], None] | None = None,
) -> EjecucionPuertas:
    """Execute quality gates and preserve each raw combined output.

    Args:
        raiz: Project root used as the process working directory.
        puertas: Gates to attempt in the supplied order.
        verificar_configuracion: Guardia fail-closed ejecutada antes y despues
            de cada proceso para impedir que una puerta cambie las siguientes.

    Returns:
        A typed aggregate with every attempted gate result.
    """
    nombres = tuple(puerta.nombre for puerta in puertas)
    if not puertas:
        return EjecucionPuertas(estado=ValorEstadoPuertas.SIN_CONFIGURAR)
    if procesos.encontrar("mise") is None:
        return EjecucionPuertas(
            estado=ValorEstadoPuertas.EJECUTOR_NO_DISPONIBLE,
            descubiertas=nombres,
            omitidas=nombres,
        )

    resultados: list[ResultadoPuerta] = []
    hubo_error = False
    for puerta in puertas:
        if verificar_configuracion is not None:
            verificar_configuracion()
        inicio_utc = datetime.now(UTC)
        marca_inicio = monotonic()
        try:
            proceso = procesos.ejecutar(
                puerta.comando,
                raiz=raiz,
                limite_segundos=900,
            )
            salida = proceso.salida + proceso.error
            if proceso.exitoso:
                estado = ValorResultadoPuerta.APROBADO
            else:
                estado = ValorResultadoPuerta.FALLIDO
            codigo_salida = proceso.codigo_salida
        except Exception as error:
            salida = f"{type(error).__name__}: {error}"
            estado = ValorResultadoPuerta.ERROR_EJECUCION
            codigo_salida = None
            hubo_error = True
        finally:
            if verificar_configuracion is not None:
                verificar_configuracion()
        fin_utc = datetime.now(UTC)
        duracion_segundos = monotonic() - marca_inicio
        resultados.append(
            ResultadoPuerta(
                nombre=puerta.nombre,
                comando=puerta.comando,
                estado=estado,
                codigo_salida=codigo_salida,
                salida=salida,
                inicio_utc=inicio_utc,
                fin_utc=fin_utc,
                duracion_segundos=duracion_segundos,
                hash_salida=hashlib.sha256(salida.encode("utf-8")).hexdigest(),
                archivo_salida=puerta.archivo_salida,
            )
        )

    fallidas = tuple(
        resultado.nombre
        for resultado in resultados
        if resultado.estado is not ValorResultadoPuerta.APROBADO
    )
    if hubo_error:
        estado_final = ValorEstadoPuertas.ERROR_EJECUCION
    elif fallidas:
        estado_final = ValorEstadoPuertas.FALLIDO
    else:
        estado_final = ValorEstadoPuertas.APROBADO
    return EjecucionPuertas(
        estado=estado_final,
        descubiertas=nombres,
        ejecutadas=nombres,
        fallidas=fallidas,
        resultados=tuple(resultados),
    )
