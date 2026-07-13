"""Create and serialize formal evidence-pack identities and metadata."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import secrets
import shutil
import subprocess
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath

from tramalia.core.errores import (
    ErrorIdentificadorInseguro,
    ErrorPersistenciaEvidencia,
)
from tramalia.core.modelos import (
    EntradaBitacora,
    EstadoGit,
    MetadatosPaqueteEvidencia,
    PaqueteEvidencia,
    ValorEstadoBitacora,
    ValorEstadoCierre,
    ValorEstadoPuertas,
    ValorResultadoPuerta,
)

_ID_SEGURO = re.compile(r"^[A-Za-z0-9._-]{1,64}$", re.ASCII)
_ID_PAQUETE = re.compile(r"^\d{8}T\d{6}\.\d{6}Z-[0-9a-f]{8}$", re.ASCII)
_HASH_SHA256 = re.compile(r"^[0-9a-f]{64}$", re.ASCII)
_ARCHIVO_SALIDA_SEGURO = re.compile(r"^[A-Za-z0-9._-]{1,128}$", re.ASCII)
_SEGMENTO_ARCHIVO_SEGURO = re.compile(r"^[A-Za-z0-9._-]{1,128}$", re.ASCII)
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


def _archivo_salida_es_seguro(valor: object) -> bool:
    if not isinstance(valor, str):
        return False
    nombre_base_windows = valor.split(".", 1)[0].upper()
    return bool(
        _ARCHIVO_SALIDA_SEGURO.fullmatch(valor)
        and ".." not in valor
        and not valor.endswith(".")
        and nombre_base_windows not in _RESERVADOS_WINDOWS
    )


def _numero_finito_no_negativo(valor: object) -> bool:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return False
    try:
        return math.isfinite(valor) and valor >= 0
    except (OverflowError, TypeError, ValueError):
        return False


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
    if not _numero_finito_no_negativo(duracion):
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
    if not _archivo_salida_es_seguro(archivo_salida):
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


def _error_archivo(campo: str, tipo_error: str | None = None) -> ErrorPersistenciaEvidencia:
    detalles = {"campo": campo}
    if tipo_error is not None:
        detalles["tipo_error"] = tipo_error
    return ErrorPersistenciaEvidencia(
        "El mapa de archivos del paquete no es seguro o completo.",
        "Usa rutas relativas portables y contenidos binarios validos.",
        detalles=detalles,
    )


def _partes_ruta_interna(nombre: object) -> tuple[str, ...]:
    if not isinstance(nombre, str) or not nombre or "\x00" in nombre:
        raise _error_archivo("ruta")
    # Una barra inversa puede cambiar de significado al mover el pack entre sistemas.
    if "\\" in nombre or "//" in nombre or nombre.endswith("/"):
        raise _error_archivo("ruta")

    ruta_posix = PurePosixPath(nombre)
    ruta_windows = PureWindowsPath(nombre)
    partes = tuple(nombre.split("/"))
    if (
        ruta_posix.is_absolute()
        or ruta_windows.is_absolute()
        or bool(ruta_windows.drive)
        or not partes
        or any(parte in {"", ".", ".."} for parte in partes)
    ):
        raise _error_archivo("ruta")

    for parte in partes:
        base_windows = parte.split(".", 1)[0].upper()
        if (
            not _SEGMENTO_ARCHIVO_SEGURO.fullmatch(parte)
            or parte.endswith(".")
            or base_windows in _RESERVADOS_WINDOWS
        ):
            raise _error_archivo("ruta")
    return partes


def _preparar_archivos(
    archivos: Mapping[str, bytes],
    metadata_serializada: bytes,
) -> tuple[tuple[str, bytes], ...]:
    if not isinstance(archivos, Mapping):
        raise _error_archivo("archivos", type(archivos).__name__)

    preparados: dict[tuple[str, ...], bytes] = {}
    rutas_portables: dict[tuple[str, ...], tuple[str, ...]] = {}
    try:
        elementos = tuple(archivos.items())
    except Exception as error:
        raise _error_archivo("archivos", type(error).__name__) from error

    for nombre, contenido in elementos:
        partes = _partes_ruta_interna(nombre)
        ruta_portable = tuple(parte.casefold() for parte in partes)
        if ruta_portable == ("metadatos.json",):
            raise _error_archivo("metadatos.json")
        if not isinstance(contenido, bytes):
            raise _error_archivo("contenido", type(contenido).__name__)
        if ruta_portable in rutas_portables:
            raise _error_archivo("ruta")
        preparados[partes] = contenido
        rutas_portables[ruta_portable] = partes

    traspaso = ("traspaso.md",)
    if traspaso not in preparados:
        raise _error_archivo("traspaso.md")

    metadata = ("metadatos.json",)
    preparados[metadata] = metadata_serializada
    rutas_portables[metadata] = metadata
    rutas = tuple(rutas_portables)
    for indice, ruta in enumerate(rutas):
        for otra in rutas[indice + 1 :]:
            limite = min(len(ruta), len(otra))
            if ruta[:limite] == otra[:limite]:
                raise _error_archivo("ruta")

    return tuple(
        ("/".join(partes), contenido)
        for partes, contenido in sorted(
            preparados.items(),
            key=lambda elemento: tuple(parte.casefold() for parte in elemento[0]),
        )
    )


def _bajo_base(ruta: Path, base: Path) -> bool:
    try:
        return ruta.resolve(strict=False).is_relative_to(base.resolve(strict=True))
    except (OSError, RuntimeError, ValueError):
        return False


def _escribir_archivo(ruta: Path, contenido: bytes) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("xb") as archivo:
        archivo.write(contenido)
        archivo.flush()
        os.fsync(archivo.fileno())


def publicar_paquete(
    raiz: Path,
    metadatos: MetadatosPaqueteEvidencia,
    archivos: Mapping[str, bytes],
) -> PaqueteEvidencia:
    """Publish one complete evidence pack through an atomic directory rename.

    Args:
        raiz: Governed project root that owns ``.tramalia/evidencia``.
        metadatos: Formal v1 metadata for the new immutable package.
        archivos: Relative portable paths and their exact byte contents.

    Returns:
        The immutable reference to the newly published package.

    Raises:
        ErrorPersistenciaEvidencia: If validation, containment, writing, or the
            final atomic rename fails.
    """
    temporal: Path | None = None
    temporal_creado = False
    final: Path | None = None
    try:
        if metadatos.vinculo_traspaso != "traspaso.md":
            raise ErrorPersistenciaEvidencia(
                "La metadata no referencia el traspaso canonico.",
                "Usa vinculo_traspaso igual a traspaso.md.",
                detalles={"campo": "vinculo_traspaso"},
            )
        metadata_serializada = _serializar(metadatos)
        contenido = _preparar_archivos(archivos, metadata_serializada)

        raiz_resuelta = raiz.resolve(strict=False)
        directorio_tramalia = raiz_resuelta / ".tramalia"
        if (directorio_tramalia.exists() or directorio_tramalia.is_symlink()) and (
            directorio_tramalia.resolve(strict=True) != directorio_tramalia
        ):
            raise ErrorPersistenciaEvidencia(
                "El directorio de gobierno no pertenece fisicamente al proyecto.",
                "Retira enlaces simbolicos de .tramalia antes de publicar.",
                directorio_tramalia,
            )

        base = directorio_tramalia / "evidencia"
        if (base.exists() or base.is_symlink()) and base.resolve(strict=True) != base:
            raise ErrorPersistenciaEvidencia(
                "El directorio de evidencia no pertenece fisicamente al proyecto.",
                "Retira enlaces simbolicos de .tramalia/evidencia antes de publicar.",
                base,
            )
        base.mkdir(parents=True, exist_ok=True)
        # Revalidar despues de mkdir reduce la ventana de sustitucion de la base.
        if base.resolve(strict=True) != base:
            raise ErrorPersistenciaEvidencia(
                "El directorio de evidencia no pertenece fisicamente al proyecto.",
                "Retira enlaces simbolicos de .tramalia/evidencia antes de publicar.",
                base,
            )

        final = base / metadatos.id_paquete
        temporal = base / f".tmp-{uuid.uuid4().hex}"
        if (
            not _bajo_base(final, base)
            or not _bajo_base(temporal, base)
            or final.exists()
            or final.is_symlink()
        ):
            raise ErrorPersistenciaEvidencia(
                "La ruta final del paquete no es nueva o segura.",
                "Reintenta con un ID de paquete nuevo.",
                final,
            )

        temporal.mkdir(mode=0o700)
        temporal_creado = True
        for nombre, datos in contenido:
            destino = temporal.joinpath(*nombre.split("/"))
            if not _bajo_base(destino, temporal):
                raise _error_archivo("ruta")
            _escribir_archivo(destino, datos)

        # Leer el JSON desde staging comprueba bytes y persistencia antes del rename.
        json.loads((temporal / "metadatos.json").read_text(encoding="utf-8"))
        os.replace(temporal, final)
        temporal = None
        temporal_creado = False
        return PaqueteEvidencia(metadatos.id_paquete, final, metadatos)
    except ErrorPersistenciaEvidencia:
        if temporal is not None and temporal_creado:
            shutil.rmtree(temporal, ignore_errors=True)
        raise
    except Exception as error:
        if temporal is not None and temporal_creado:
            shutil.rmtree(temporal, ignore_errors=True)
        raise ErrorPersistenciaEvidencia(
            "No se pudo publicar el paquete atomico.",
            "Revisa permisos y soporte de renombrado atomico en el sistema de archivos.",
            final,
            detalles={"tipo_error": type(error).__name__},
        ) from error


_CLAVES_METADATOS_V1 = frozenset(
    {
        "version_esquema",
        "id_paquete",
        "id_tarea",
        "operacion",
        "inicio_utc",
        "fin_utc",
        "entorno",
        "git",
        "comandos",
        "puertas",
        "estado_cierre",
        "agente",
        "modelo",
        "metricas",
        "umbrales",
        "errores_validacion",
        "excepciones",
        "vinculo_traspaso",
    }
)


def _exigir_objeto(valor: object, nombre: str) -> Mapping[str, object]:
    if not isinstance(valor, Mapping) or any(not isinstance(clave, str) for clave in valor):
        raise ValueError(f"{nombre} debe ser un objeto")
    return valor


def _exigir_lista_textos(valor: object, nombre: str) -> list[str]:
    if not isinstance(valor, list) or any(not isinstance(elemento, str) for elemento in valor):
        raise ValueError(f"{nombre} debe ser una lista de textos")
    return valor


def _validar_json_finito(valor: object, nombre: str) -> None:
    if isinstance(valor, float) and not math.isfinite(valor):
        raise ValueError(f"{nombre} debe contener valores finitos")
    if isinstance(valor, Mapping):
        for indice, (clave, elemento) in enumerate(valor.items()):
            if not isinstance(clave, str):
                raise ValueError(f"{nombre} contiene una clave no textual")
            # Las claves son datos no confiables y nunca forman parte del error visible.
            _validar_json_finito(elemento, f"{nombre}.valor[{indice}]")
    elif isinstance(valor, list):
        for indice, elemento in enumerate(valor):
            _validar_json_finito(elemento, f"{nombre}[{indice}]")
    elif not isinstance(valor, (str, int, float, bool, type(None))):
        raise ValueError(f"{nombre} contiene un valor no JSON")


def _instante_desde_json(valor: object, nombre: str) -> datetime:
    if not isinstance(valor, str):
        raise ValueError(f"{nombre} debe ser un timestamp UTC")
    try:
        instante = datetime.fromisoformat(valor)
        desfase = instante.utcoffset()
    except (TypeError, ValueError) as error:
        raise ValueError(f"{nombre} debe ser un timestamp UTC") from error
    if desfase is None or desfase.total_seconds() != 0:
        raise ValueError(f"{nombre} debe ser un timestamp UTC")
    return instante.astimezone(UTC)


def _validar_metadatos_bitacora(
    datos_crudos: object,
    id_directorio: str,
) -> Mapping[str, object]:
    datos = _exigir_objeto(datos_crudos, "metadatos.json")
    _validar_json_finito(datos, "metadatos")
    faltantes = sorted(_CLAVES_METADATOS_V1 - set(datos))
    if faltantes:
        raise ValueError(f"faltan claves formales: {', '.join(faltantes)}")
    if type(datos["version_esquema"]) is not int or datos["version_esquema"] != 1:
        raise ValueError("version_esquema no soportada")

    id_paquete = datos["id_paquete"]
    if not isinstance(id_paquete, str) or not _ID_PAQUETE.fullmatch(id_paquete):
        raise ValueError("id_paquete no cumple el formato formal")
    if id_paquete != id_directorio:
        raise ValueError("id_paquete no coincide con el directorio")
    id_tarea = datos["id_tarea"]
    try:
        validar_id_tarea(id_tarea)  # type: ignore[arg-type]
    except ErrorIdentificadorInseguro as error:
        raise ValueError("id_tarea no es seguro") from error

    operacion = datos["operacion"]
    if not isinstance(operacion, str) or operacion not in {
        "cierre",
        "evidencia",
        "traspaso",
    }:
        raise ValueError("operacion no soportada")
    inicio = _instante_desde_json(datos["inicio_utc"], "inicio_utc")
    fin = _instante_desde_json(datos["fin_utc"], "fin_utc")
    if fin < inicio:
        raise ValueError("fin_utc precede a inicio_utc")

    estado_cierre = datos["estado_cierre"]
    if not isinstance(estado_cierre, str):
        raise ValueError("estado_cierre invalido")
    try:
        ValorEstadoCierre(estado_cierre)
    except (TypeError, ValueError) as error:
        raise ValueError("estado_cierre invalido") from error

    entorno = _exigir_objeto(datos["entorno"], "entorno")
    claves_entorno = {"tramalia", "python", "sistema_operativo", "cadena_herramientas"}
    if not claves_entorno <= set(entorno):
        raise ValueError("estructura entorno incompleta")
    for nombre in ("tramalia", "python", "sistema_operativo"):
        valor_entorno = entorno[nombre]
        if not isinstance(valor_entorno, str) or not valor_entorno.strip():
            raise ValueError(f"entorno.{nombre} debe ser texto no vacio")
    herramientas = _exigir_objeto(
        entorno["cadena_herramientas"],
        "entorno.cadena_herramientas",
    )
    if any(valor is not None and not isinstance(valor, str) for valor in herramientas.values()):
        raise ValueError("entorno.cadena_herramientas invalida")

    git = _exigir_objeto(datos["git"], "git")
    claves_git = {
        "commit",
        "rama",
        "limpio",
        "base_comparacion",
        "rastreados",
        "preparados",
        "no_rastreados",
        "renombrados",
        "eliminados",
    }
    if not claves_git <= set(git):
        raise ValueError("estructura git incompleta")
    for nombre in ("commit", "rama", "base_comparacion"):
        if git[nombre] is not None and not isinstance(git[nombre], str):
            raise ValueError(f"git.{nombre} debe ser texto o nulo")
    if git["limpio"] is not None and not isinstance(git["limpio"], bool):
        raise ValueError("git.limpio debe ser booleano o nulo")
    for nombre in ("rastreados", "preparados", "no_rastreados", "renombrados", "eliminados"):
        _exigir_lista_textos(git[nombre], f"git.{nombre}")

    puertas = _exigir_objeto(datos["puertas"], "puertas")
    claves_puertas = {
        "estado",
        "descubiertas",
        "ejecutadas",
        "omitidas",
        "fallidas",
        "errores_validacion",
    }
    if not claves_puertas <= set(puertas):
        raise ValueError("estructura puertas incompleta")
    estado_puertas = puertas["estado"]
    if not isinstance(estado_puertas, str):
        raise ValueError("puertas.estado invalido")
    try:
        ValorEstadoPuertas(estado_puertas)
    except (TypeError, ValueError) as error:
        raise ValueError("puertas.estado invalido") from error
    for nombre in ("descubiertas", "ejecutadas", "omitidas", "fallidas", "errores_validacion"):
        _exigir_lista_textos(puertas[nombre], f"puertas.{nombre}")

    for nombre in ("metricas", "umbrales"):
        _exigir_objeto(datos[nombre], nombre)
    _exigir_lista_textos(datos["errores_validacion"], "errores_validacion")

    comandos = datos["comandos"]
    if not isinstance(comandos, list):
        raise ValueError("comandos debe ser una lista")
    claves_comando = {
        "nombre",
        "comando",
        "estado",
        "inicio_utc",
        "fin_utc",
        "duracion_segundos",
        "codigo_salida",
        "hash_salida",
        "archivo_salida",
    }
    for indice, comando_crudo in enumerate(comandos):
        comando = _exigir_objeto(comando_crudo, f"comandos[{indice}]")
        if not claves_comando <= set(comando):
            raise ValueError(f"comandos[{indice}] incompleto")
        if not isinstance(comando["nombre"], str) or not comando["nombre"].strip():
            raise ValueError(f"comandos[{indice}].nombre invalido")
        argumentos = _exigir_lista_textos(comando["comando"], f"comandos[{indice}].comando")
        if not argumentos or any(not argumento for argumento in argumentos):
            raise ValueError(f"comandos[{indice}].comando no puede estar vacio")
        estado_comando = comando["estado"]
        if not isinstance(estado_comando, str):
            raise ValueError(f"comandos[{indice}].estado invalido")
        try:
            ValorResultadoPuerta(estado_comando)
        except (TypeError, ValueError) as error:
            raise ValueError(f"comandos[{indice}].estado invalido") from error
        inicio_comando = _instante_desde_json(
            comando["inicio_utc"],
            f"comandos[{indice}].inicio_utc",
        )
        fin_comando = _instante_desde_json(
            comando["fin_utc"],
            f"comandos[{indice}].fin_utc",
        )
        if inicio_comando < inicio or fin_comando > fin or fin_comando < inicio_comando:
            raise ValueError(f"comandos[{indice}] queda fuera del intervalo")
        duracion = comando["duracion_segundos"]
        if not _numero_finito_no_negativo(duracion):
            raise ValueError(f"comandos[{indice}].duracion_segundos invalida")
        codigo = comando["codigo_salida"]
        if codigo is not None and (isinstance(codigo, bool) or not isinstance(codigo, int)):
            raise ValueError(f"comandos[{indice}].codigo_salida invalido")
        hash_salida = comando["hash_salida"]
        if not isinstance(hash_salida, str) or not _HASH_SHA256.fullmatch(hash_salida):
            raise ValueError(f"comandos[{indice}].hash_salida invalido")
        if not _archivo_salida_es_seguro(comando["archivo_salida"]):
            raise ValueError(f"comandos[{indice}].archivo_salida invalido")

    excepciones = datos["excepciones"]
    if not isinstance(excepciones, list):
        raise ValueError("excepciones debe ser una lista")
    claves_excepcion = {
        "razon",
        "riesgo_aceptado",
        "control_afectado",
        "referencia",
        "revisor",
        "expira_en",
        "condicion_remediacion",
    }
    for indice, excepcion_cruda in enumerate(excepciones):
        excepcion = _exigir_objeto(excepcion_cruda, f"excepciones[{indice}]")
        if not claves_excepcion <= set(excepcion):
            raise ValueError(f"excepciones[{indice}] incompleta")
        for nombre in ("razon", "riesgo_aceptado", "control_afectado", "referencia", "revisor"):
            valor_excepcion = excepcion[nombre]
            if not isinstance(valor_excepcion, str) or not valor_excepcion.strip():
                raise ValueError(f"excepciones[{indice}].{nombre} invalido")
        expiracion = excepcion["expira_en"]
        condicion = excepcion["condicion_remediacion"]
        if expiracion is not None:
            _instante_desde_json(expiracion, f"excepciones[{indice}].expira_en")
        if condicion is not None and not isinstance(condicion, str):
            raise ValueError(f"excepciones[{indice}].condicion_remediacion invalida")
        if expiracion is None and not (isinstance(condicion, str) and condicion.strip()):
            raise ValueError(f"excepciones[{indice}] no tiene vigencia ni remediacion")

    if datos["vinculo_traspaso"] != "traspaso.md":
        raise ValueError("vinculo_traspaso no es canonico")
    for nombre in ("agente", "modelo"):
        if datos[nombre] is not None and not isinstance(datos[nombre], str):
            raise ValueError(f"{nombre} debe ser texto o nulo")
    return datos


def _misma_identidad(ruta: Path, esperada: os.stat_result) -> bool:
    try:
        return os.path.samestat(ruta.stat(follow_symlinks=False), esperada)
    except (OSError, ValueError):
        return False


def _validar_descriptor_confinado(
    descriptor: int,
    ruta: Path,
    base_resuelta: Path,
) -> None:
    identidad_abierta = os.fstat(descriptor)
    if (
        ruta.is_symlink()
        or ruta.resolve(strict=True).parent != base_resuelta
        or not _misma_identidad(ruta, identidad_abierta)
    ):
        raise ValueError("un archivo queda fuera del paquete")


def _leer_bytes_confinados(ruta: Path, base_resuelta: Path) -> bytes:
    with ruta.open("rb") as archivo:
        _validar_descriptor_confinado(archivo.fileno(), ruta, base_resuelta)
        return archivo.read()


def _resumen_confinado(ruta: Path, base_resuelta: Path) -> str:
    resumen = hashlib.sha256()
    with ruta.open("rb") as archivo:
        _validar_descriptor_confinado(archivo.fileno(), ruta, base_resuelta)
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def _validar_archivos_paquete(
    ruta: Path,
    ruta_resuelta: Path,
    datos: Mapping[str, object],
) -> None:
    traspaso = ruta / "traspaso.md"
    if not traspaso.is_file():
        raise ValueError("falta traspaso.md canonico")
    _leer_bytes_confinados(traspaso, ruta_resuelta)

    comandos = datos["comandos"]
    if not isinstance(comandos, list):
        raise ValueError("comandos debe ser una lista")
    for indice, comando_crudo in enumerate(comandos):
        comando = _exigir_objeto(comando_crudo, f"comandos[{indice}]")
        nombre = comando["archivo_salida"]
        if not isinstance(nombre, str):
            raise ValueError(f"archivo de salida {indice} invalido")
        salida = ruta / nombre
        if not salida.is_file():
            raise ValueError(f"archivo de salida {indice} ausente o inseguro")
        if _resumen_confinado(salida, ruta_resuelta) != comando["hash_salida"]:
            raise ValueError(f"archivo de salida {indice} no coincide con su hash")


def _objeto_sin_claves_duplicadas(pares: list[tuple[str, object]]) -> dict[str, object]:
    resultado: dict[str, object] = {}
    for clave, valor in pares:
        if clave in resultado:
            raise ValueError("metadatos.json contiene claves duplicadas")
        resultado[clave] = valor
    return resultado


def _entrada_invalida(ruta: Path, error: str) -> EntradaBitacora:
    return EntradaBitacora(
        id_paquete=ruta.name,
        ruta=ruta,
        estado=ValorEstadoBitacora.INVALIDA,
        id_tarea=None,
        resultado=None,
        agente=None,
        modelo=None,
        cerrado_utc=None,
        error=error,
    )


def leer_bitacora(raiz: Path) -> list[EntradaBitacora]:
    """Read formal v1 packages without inferring state from legacy Markdown.

    Args:
        raiz: Project root whose immutable evidence packages will be inspected.

    Returns:
        Valid and explicitly invalid entries, ordered by package ID descending.
    """
    try:
        raiz_resuelta = raiz.resolve(strict=False)
        base = raiz_resuelta / ".tramalia" / "evidencia"
        if not base.is_dir() or base.is_symlink() or base.resolve(strict=True) != base:
            return []
        rutas = sorted(
            (
                ruta
                for ruta in base.iterdir()
                if not ruta.name.startswith(".tmp-") and (ruta.is_dir() or ruta.is_symlink())
            ),
            key=lambda ruta: ruta.name,
            reverse=True,
        )
    except (OSError, RuntimeError, ValueError):
        return []

    entradas: list[EntradaBitacora] = []
    for ruta in rutas:
        try:
            ruta_resuelta = ruta.resolve(strict=True)
            ruta_fuera_de_base = ruta_resuelta.parent != base
        except (OSError, RuntimeError, ValueError):
            ruta_resuelta = ruta
            ruta_fuera_de_base = True
        if ruta.is_symlink() or ruta_fuera_de_base:
            entradas.append(_entrada_invalida(ruta, "el directorio del paquete es un symlink"))
            continue
        try:
            ruta_metadatos = ruta / "metadatos.json"
            texto = _leer_bytes_confinados(ruta_metadatos, ruta_resuelta).decode("utf-8")
            datos_crudos = json.loads(texto, object_pairs_hook=_objeto_sin_claves_duplicadas)
            datos = _validar_metadatos_bitacora(datos_crudos, ruta.name)
            _validar_archivos_paquete(ruta, ruta_resuelta, datos)
            agente = datos["agente"] if isinstance(datos["agente"], str) else None
            modelo = datos["modelo"] if isinstance(datos["modelo"], str) else None
            entradas.append(
                EntradaBitacora(
                    id_paquete=ruta.name,
                    ruta=ruta,
                    estado=ValorEstadoBitacora.VALIDA,
                    id_tarea=str(datos["id_tarea"]),
                    resultado=ValorEstadoCierre(str(datos["estado_cierre"])),
                    agente=agente,
                    modelo=modelo,
                    cerrado_utc=_instante_desde_json(datos["fin_utc"], "fin_utc"),
                    error=None,
                )
            )
        except json.JSONDecodeError:
            entradas.append(_entrada_invalida(ruta, "metadatos.json no es JSON valido"))
        except ValueError as error:
            entradas.append(_entrada_invalida(ruta, str(error)))
        except (OSError, UnicodeError) as error:
            entradas.append(_entrada_invalida(ruta, f"lectura fallida: {type(error).__name__}"))
        except Exception as error:
            entradas.append(_entrada_invalida(ruta, f"validacion fallida: {type(error).__name__}"))
    return entradas
