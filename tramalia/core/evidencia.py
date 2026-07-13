"""Create and serialize formal evidence-pack identities and metadata."""

from __future__ import annotations

import json
import math
import re
import secrets
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from tramalia.core.errores import (
    ErrorIdentificadorInseguro,
    ErrorPersistenciaEvidencia,
)
from tramalia.core.modelos import (
    EstadoGit,
    MetadatosPaqueteEvidencia,
)

_ID_SEGURO = re.compile(r"^[A-Za-z0-9._-]{1,64}$", re.ASCII)
_ID_PAQUETE = re.compile(r"^\d{8}T\d{6}\.\d{6}Z-[0-9a-f]{8}$", re.ASCII)
_HASH_SHA256 = re.compile(r"^[0-9a-f]{64}$", re.ASCII)
_ARCHIVO_SALIDA_SEGURO = re.compile(r"^[A-Za-z0-9._-]{1,128}$", re.ASCII)
_RESERVADOS_WINDOWS = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{indice}" for indice in range(1, 10)),
    *(f"LPT{indice}" for indice in range(1, 10)),
}


def validar_id_tarea(id_tarea: str) -> str:
    """Validate a task identifier before any filesystem write.

    Args:
        id_tarea: Candidate task identifier.

    Returns:
        The unchanged portable identifier.

    Raises:
        ErrorIdentificadorInseguro: If the value is unsafe on any target OS.
    """
    if not isinstance(id_tarea, str):
        raise ErrorIdentificadorInseguro(
            "El ID de tarea debe ser texto.",
            "Usa 1-64 letras ASCII, numeros, punto, guion o guion bajo.",
            detalles={"tipo": type(id_tarea).__name__},
        )
    nombre_base_windows = id_tarea.split(".", 1)[0].upper()
    if (
        not _ID_SEGURO.fullmatch(id_tarea)
        or ".." in id_tarea
        or id_tarea.endswith(".")
        or nombre_base_windows in _RESERVADOS_WINDOWS
    ):
        raise ErrorIdentificadorInseguro(
            "El ID de tarea no es seguro.",
            "Usa 1-64 letras ASCII, numeros, punto, guion o guion bajo.",
            detalles={"id_tarea": id_tarea},
        )
    return id_tarea


def _normalizar_instante_utc(instante: datetime, campo: str) -> datetime:
    try:
        tiene_desfase = instante.tzinfo is not None and instante.utcoffset() is not None
    except Exception as error:
        raise ErrorPersistenciaEvidencia(
            "Un instante de evidencia no cumple el contrato UTC.",
            "Proporciona timestamps con zona horaria y desfase UTC validos.",
            detalles={"campo": campo, "tipo_error": type(error).__name__},
        ) from error
    if not tiene_desfase:
        raise ErrorPersistenciaEvidencia(
            "Un instante de evidencia no cumple el contrato UTC.",
            "Proporciona timestamps con zona horaria y desfase UTC validos.",
            detalles={"campo": campo},
        )
    return instante.astimezone(UTC)


def _instante_iso_utc(instante: datetime, campo: str) -> str:
    return _normalizar_instante_utc(instante, campo).isoformat().replace("+00:00", "Z")


def crear_id_paquete(ahora: datetime | None = None) -> str:
    """Create a collision-resistant UTC evidence-pack identifier.

    Args:
        ahora: Optional timezone-aware instant. Current UTC time is used by default.

    Returns:
        A timestamp identifier with microseconds and eight random hex digits.

    Raises:
        ErrorPersistenciaEvidencia: If ``ahora`` has no valid UTC offset.
    """
    instante = _normalizar_instante_utc(ahora or datetime.now(UTC), "ahora")
    return f"{instante.strftime('%Y%m%dT%H%M%S.%fZ')}-{secrets.token_hex(4)}"


def _consultar_git(raiz: Path, *argumentos: str) -> str | None:
    try:
        proceso = subprocess.run(
            ["git", *argumentos],
            cwd=raiz,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proceso.stdout if proceso.returncode == 0 else None


def _valor_git(raiz: Path, *argumentos: str) -> str | None:
    salida = _consultar_git(raiz, *argumentos)
    if salida is None:
        return None
    valor = salida.strip()
    return valor or None


def _rutas_nulas(salida: str | None) -> tuple[str, ...]:
    if salida is None:
        return ()
    return tuple(sorted(set(ruta for ruta in salida.split("\0") if ruta)))


def _analizar_estado_nulo(salida: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    elementos = salida.split("\0")
    renombrados: set[str] = set()
    eliminados: set[str] = set()
    indice = 0
    while indice < len(elementos):
        entrada = elementos[indice]
        if not entrada:
            indice += 1
            continue
        estado = entrada[:2]
        destino = entrada[3:]
        if "R" in estado or "C" in estado:
            origen = elementos[indice + 1] if indice + 1 < len(elementos) else ""
            if origen:
                renombrados.add(f"{origen} -> {destino}")
            indice += 2
        else:
            indice += 1
        if "D" in estado and destino:
            eliminados.add(destino)
    return tuple(sorted(renombrados)), tuple(sorted(eliminados))


def capturar_estado_git(raiz: Path) -> EstadoGit:
    """Capture tracked, staged, untracked, renamed, and deleted Git paths.

    Args:
        raiz: Repository root to inspect without changing it.

    Returns:
        A deterministic Git inventory. Unknown scalar state is represented by ``None``.
    """
    if _valor_git(raiz, "rev-parse", "--is-inside-work-tree") != "true":
        return EstadoGit(None, None, None, None)

    commit = _valor_git(raiz, "rev-parse", "--verify", "HEAD")
    rama = _valor_git(raiz, "symbolic-ref", "--quiet", "--short", "HEAD")
    estado_crudo = _consultar_git(
        raiz,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
    )
    if estado_crudo is None:
        return EstadoGit(commit, rama, None, None)

    rastreados = _rutas_nulas(_consultar_git(raiz, "diff", "--name-only", "-z", "--"))
    preparados = _rutas_nulas(_consultar_git(raiz, "diff", "--cached", "--name-only", "-z", "--"))
    no_rastreados = _rutas_nulas(
        _consultar_git(raiz, "ls-files", "--others", "--exclude-standard", "-z")
    )
    renombrados, eliminados = _analizar_estado_nulo(estado_crudo)
    base_comparacion = _valor_git(raiz, "merge-base", "HEAD", "main") if commit else None
    return EstadoGit(
        commit=commit,
        rama=rama,
        limpio=not bool(estado_crudo) if commit else None,
        base_comparacion=base_comparacion,
        rastreados=rastreados,
        preparados=preparados,
        no_rastreados=no_rastreados,
        renombrados=renombrados,
        eliminados=eliminados,
    )


def _rechazar_campo_comando(nombre: object, campo: str) -> None:
    """Raise a safe domain error for one invalid command-result field."""
    raise ErrorPersistenciaEvidencia(
        "Un resultado de comando no cumple el esquema formal.",
        "Corrige el campo indicado antes de publicar la evidencia.",
        detalles={"campo": campo, "comando": nombre if isinstance(nombre, str) else None},
    )


def _validar_resultado_comando(resultado: object) -> None:
    """Validate persisted command fields without exposing their raw output."""
    nombre = getattr(resultado, "nombre", None)
    if not isinstance(nombre, str) or not nombre.strip():
        _rechazar_campo_comando(nombre, "nombre")

    comando = getattr(resultado, "comando", None)
    if (
        not isinstance(comando, tuple)
        or not comando
        or any(not isinstance(argumento, str) or not argumento for argumento in comando)
    ):
        _rechazar_campo_comando(nombre, "comando")

    duracion = getattr(resultado, "duracion_segundos", None)
    if (
        isinstance(duracion, bool)
        or not isinstance(duracion, (int, float))
        or not math.isfinite(duracion)
        or duracion < 0
    ):
        _rechazar_campo_comando(nombre, "duracion_segundos")

    codigo_salida = getattr(resultado, "codigo_salida", None)
    if codigo_salida is not None and (
        isinstance(codigo_salida, bool) or not isinstance(codigo_salida, int)
    ):
        _rechazar_campo_comando(nombre, "codigo_salida")

    hash_salida = getattr(resultado, "hash_salida", None)
    if not isinstance(hash_salida, str) or not _HASH_SHA256.fullmatch(hash_salida):
        _rechazar_campo_comando(nombre, "hash_salida")

    archivo_salida = getattr(resultado, "archivo_salida", None)
    nombre_base_windows = (
        archivo_salida.split(".", 1)[0].upper() if isinstance(archivo_salida, str) else ""
    )
    if (
        not isinstance(archivo_salida, str)
        or not _ARCHIVO_SALIDA_SEGURO.fullmatch(archivo_salida)
        or ".." in archivo_salida
        or archivo_salida.endswith(".")
        or nombre_base_windows in _RESERVADOS_WINDOWS
    ):
        _rechazar_campo_comando(nombre, "archivo_salida")


def _serializar(metadatos: MetadatosPaqueteEvidencia) -> bytes:
    if metadatos.version_esquema != 1:
        raise ErrorPersistenciaEvidencia(
            "La metadata no usa el esquema formal v1.",
            "Genera nuevamente el paquete con version_esquema igual a 1.",
            detalles={"version_esquema": metadatos.version_esquema},
        )
    validar_id_tarea(metadatos.id_tarea)
    if not _ID_PAQUETE.fullmatch(metadatos.id_paquete):
        raise ErrorPersistenciaEvidencia(
            "El ID del paquete no cumple el formato formal.",
            "Genera el ID mediante crear_id_paquete().",
            detalles={"tipo": "id_paquete_invalido"},
        )

    inicio = _normalizar_instante_utc(metadatos.inicio_utc, "inicio_utc")
    fin = _normalizar_instante_utc(metadatos.fin_utc, "fin_utc")
    if fin < inicio:
        raise ErrorPersistenciaEvidencia(
            "El fin de la operacion precede a su inicio.",
            "Corrige las marcas de tiempo antes de publicar evidencia.",
            detalles={"campo": "fin_utc"},
        )

    comandos: list[dict[str, object]] = []
    for resultado in metadatos.ejecucion.resultados:
        _validar_resultado_comando(resultado)
        inicio_resultado = _normalizar_instante_utc(
            resultado.inicio_utc,
            f"comando:{resultado.nombre}:inicio_utc",
        )
        fin_resultado = _normalizar_instante_utc(
            resultado.fin_utc,
            f"comando:{resultado.nombre}:fin_utc",
        )
        if fin_resultado < inicio_resultado:
            raise ErrorPersistenciaEvidencia(
                "El fin de un comando precede a su inicio.",
                "Corrige las marcas de tiempo del resultado.",
                detalles={"comando": resultado.nombre},
            )
        if inicio_resultado < inicio or fin_resultado > fin:
            raise ErrorPersistenciaEvidencia(
                "Un comando queda fuera del intervalo de la operacion.",
                "Alinea sus marcas de tiempo con el inicio y fin del paquete.",
                detalles={"comando": resultado.nombre},
            )
        comandos.append(
            {
                "nombre": resultado.nombre,
                "comando": list(resultado.comando),
                "estado": resultado.estado.value,
                "inicio_utc": _instante_iso_utc(inicio_resultado, "inicio_comando"),
                "fin_utc": _instante_iso_utc(fin_resultado, "fin_comando"),
                "duracion_segundos": resultado.duracion_segundos,
                "codigo_salida": resultado.codigo_salida,
                "hash_salida": resultado.hash_salida,
                "archivo_salida": resultado.archivo_salida,
            }
        )

    excepciones: list[dict[str, object]] = []
    for excepcion in metadatos.excepciones:
        excepciones.append(
            {
                "razon": excepcion.razon,
                "riesgo_aceptado": excepcion.riesgo_aceptado,
                "control_afectado": excepcion.control_afectado,
                "referencia": excepcion.referencia,
                "revisor": excepcion.revisor,
                "expira_en": (
                    _instante_iso_utc(excepcion.expira_en, "excepcion:expira_en")
                    if excepcion.expira_en is not None
                    else None
                ),
                "condicion_remediacion": excepcion.condicion_remediacion,
            }
        )

    datos: dict[str, object] = {
        "version_esquema": metadatos.version_esquema,
        "id_paquete": metadatos.id_paquete,
        "id_tarea": metadatos.id_tarea,
        "operacion": metadatos.operacion,
        "inicio_utc": _instante_iso_utc(inicio, "inicio_utc"),
        "fin_utc": _instante_iso_utc(fin, "fin_utc"),
        "entorno": {
            "tramalia": metadatos.version_tramalia,
            "python": metadatos.version_python,
            "sistema_operativo": metadatos.sistema_operativo,
            "cadena_herramientas": dict(metadatos.cadena_herramientas),
        },
        "git": {
            "commit": metadatos.git.commit,
            "rama": metadatos.git.rama,
            "limpio": metadatos.git.limpio,
            "base_comparacion": metadatos.git.base_comparacion,
            "rastreados": list(metadatos.git.rastreados),
            "preparados": list(metadatos.git.preparados),
            "no_rastreados": list(metadatos.git.no_rastreados),
            "renombrados": list(metadatos.git.renombrados),
            "eliminados": list(metadatos.git.eliminados),
        },
        "comandos": comandos,
        "puertas": {
            "estado": metadatos.ejecucion.estado.value,
            "descubiertas": list(metadatos.ejecucion.descubiertas),
            "ejecutadas": list(metadatos.ejecucion.ejecutadas),
            "omitidas": list(metadatos.ejecucion.omitidas),
            "fallidas": list(metadatos.ejecucion.fallidas),
            "errores_validacion": list(metadatos.ejecucion.errores_validacion),
        },
        "estado_cierre": metadatos.estado_cierre.value,
        "agente": metadatos.agente,
        "modelo": metadatos.modelo,
        "metricas": dict(metadatos.metricas),
        "umbrales": dict(metadatos.umbrales),
        "errores_validacion": list(metadatos.errores_validacion),
        "excepciones": excepciones,
        "vinculo_traspaso": metadatos.vinculo_traspaso,
    }
    try:
        texto = json.dumps(
            datos,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        return (texto + "\n").encode("utf-8")
    except (OverflowError, TypeError, UnicodeError, ValueError) as error:
        raise ErrorPersistenciaEvidencia(
            "La metadata contiene un valor que no es JSON formal.",
            "Corrige metricas, umbrales o inventario antes de publicar.",
            detalles={"tipo_error": type(error).__name__},
        ) from error
