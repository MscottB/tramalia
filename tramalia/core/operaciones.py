"""Orquesta las operaciones mutantes compartidas por CLI, MCP y TUI.

Este modulo es la unica entrada publica para crear paquetes de evidencia, registrar
traspasos o cerrar una tarea. La separacion evita que cada interfaz interprete de
nuevo las puertas o transforme un fallo en una aprobacion por accidente.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import stat
import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

from tramalia import __version__
from tramalia.core.errores import (
    ErrorConfiguracionMetricas,
    ErrorExcepcionInvalida,
    ErrorPersistenciaEvidencia,
)
from tramalia.core.evidencia import (
    capturar_estado_git,
    crear_id_paquete,
    publicar_paquete,
    validar_id_tarea,
)
from tramalia.core.modelos import (
    EjecucionPuertas,
    ExcepcionFallo,
    MetadatosPaqueteEvidencia,
    PaqueteEvidencia,
    ResultadoCierre,
    ValorEstadoCierre,
    ValorEstadoPuertas,
)
from tramalia.core.politica_cierre import evaluar_cierre, evaluar_metricas
from tramalia.core.proyecto import exigir_proyecto_gobernado
from tramalia.core.puertas_calidad import cargar_puertas, ejecutar_puertas
from tramalia.core.traspaso import construir_traspaso, proyectar_traspaso

_TAMANO_MAXIMO_JSON = 2 * 1024 * 1024
_PROFUNDIDAD_MAXIMA_JSON = 64
_ATRIBUTO_REPARSE_WINDOWS = 0x0400


@dataclass(frozen=True, slots=True)
class _DocumentoJSON:
    """Conserva datos validados y la identidad de contenido usada por la politica."""

    datos: Mapping[str, object]
    presente: bool
    huella_sha256: str | None


def _rechazar_constante_json(valor: str) -> None:
    """Impide aceptar NaN e infinitos, admitidos por defecto por ``json``."""
    raise ValueError(f"constante JSON no finita: {valor}")


def _objeto_sin_claves_duplicadas(pares: list[tuple[str, object]]) -> dict[str, object]:
    """Construye un objeto JSON sin ocultar una clave anterior duplicada."""
    resultado: dict[str, object] = {}
    for clave, valor in pares:
        if clave in resultado:
            raise ValueError("objeto JSON con claves duplicadas")
        resultado[clave] = valor
    return resultado


def _es_enlace_o_reparse(estado: os.stat_result) -> bool:
    """Detecta enlaces POSIX y puntos de reanalisis de Windows."""
    return stat.S_ISLNK(estado.st_mode) or bool(
        getattr(estado, "st_file_attributes", 0) & _ATRIBUTO_REPARSE_WINDOWS
    )


def _error_lectura_json(
    ruta: Path,
    mensaje: str,
    sugerencia: str,
    *,
    tipo_error: str | None = None,
) -> ErrorConfiguracionMetricas:
    detalles = {"tipo_error": tipo_error} if tipo_error is not None else None
    return ErrorConfiguracionMetricas(mensaje, sugerencia, ruta, detalles=detalles)


def _leer_bytes_json_confinados(raiz: Path, ruta: Path) -> bytes | None:
    """Lee un archivo regular anclado a ``.tramalia`` y con tamano acotado."""
    directorio = raiz / ".tramalia"
    try:
        estado_directorio = directorio.stat(follow_symlinks=False)
        if (
            not stat.S_ISDIR(estado_directorio.st_mode)
            or _es_enlace_o_reparse(estado_directorio)
            or directorio.resolve(strict=True) != directorio
        ):
            raise OSError("directorio de configuracion no local")
    except (OSError, RuntimeError, ValueError) as error:
        raise _error_lectura_json(
            ruta,
            "El directorio de configuracion no pertenece fisicamente al proyecto.",
            "Retira enlaces o puntos de reanalisis de .tramalia.",
            tipo_error=type(error).__name__,
        ) from error

    if not os.path.lexists(ruta):
        return None
    descriptor: int | None = None
    try:
        estado_esperado = ruta.stat(follow_symlinks=False)
        if not stat.S_ISREG(estado_esperado.st_mode) or _es_enlace_o_reparse(estado_esperado):
            raise OSError("archivo de configuracion no regular")
        if ruta.resolve(strict=True).parent != directorio:
            raise OSError("archivo fuera de .tramalia")
        if estado_esperado.st_size > _TAMANO_MAXIMO_JSON:
            raise ValueError("archivo JSON demasiado grande")

        banderas = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        banderas |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(ruta, banderas)
        if not os.path.samestat(os.fstat(descriptor), estado_esperado):
            raise OSError("el archivo cambio antes de abrirse")

        fragmentos: list[bytes] = []
        total = 0
        while True:
            fragmento = os.read(descriptor, min(64 * 1024, _TAMANO_MAXIMO_JSON + 1 - total))
            if not fragmento:
                break
            fragmentos.append(fragmento)
            total += len(fragmento)
            if total > _TAMANO_MAXIMO_JSON:
                raise ValueError("archivo JSON demasiado grande")

        if (
            not os.path.samestat(ruta.stat(follow_symlinks=False), estado_esperado)
            or not os.path.samestat(
                directorio.stat(follow_symlinks=False),
                estado_directorio,
            )
            or directorio.resolve(strict=True) != directorio
        ):
            raise OSError("la configuracion cambio durante la lectura")
        return b"".join(fragmentos)
    except (OSError, RuntimeError, ValueError) as error:
        raise _error_lectura_json(
            ruta,
            "El archivo de metricas no es local, regular o estable.",
            "Usa un archivo JSON regular dentro de .tramalia y menor a 2 MiB.",
            tipo_error=type(error).__name__,
        ) from error
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _texto_unicode_valido(texto: str) -> bool:
    return not any(0xD800 <= ord(caracter) <= 0xDFFF for caracter in texto)


def _validar_valor_json(valor: object, profundidad: int = 0) -> None:
    """Rechaza profundidad excesiva, Unicode invalido y numeros no finitos."""
    if profundidad > _PROFUNDIDAD_MAXIMA_JSON:
        raise ValueError("JSON demasiado profundo")
    if valor is None or isinstance(valor, bool | int):
        return
    if isinstance(valor, float):
        if not math.isfinite(valor):
            raise ValueError("numero JSON no finito")
        return
    if isinstance(valor, str):
        if not _texto_unicode_valido(valor):
            raise ValueError("texto JSON con surrogate aislado")
        return
    if isinstance(valor, list):
        for elemento in valor:
            _validar_valor_json(elemento, profundidad + 1)
        return
    if isinstance(valor, dict):
        for clave, elemento in valor.items():
            if not _texto_unicode_valido(clave):
                raise ValueError("clave JSON con surrogate aislado")
            _validar_valor_json(elemento, profundidad + 1)
        return
    raise ValueError("tipo JSON no soportado")


def _leer_json(raiz: Path, nombre: str) -> _DocumentoJSON:
    """Lee una configuracion JSON estricta y conserva si el archivo existia.

    Args:
        raiz: Raiz gobernada y resuelta del proyecto.
        nombre: Nombre fijo del archivo dentro de ``.tramalia``.

    Returns:
        Los datos, su presencia y la huella exacta de los bytes leidos.

    Raises:
        ErrorConfiguracionMetricas: Si no se puede leer, no es JSON formal o su
            raiz no es un objeto.
    """
    ruta = raiz / ".tramalia" / nombre
    contenido_bytes = _leer_bytes_json_confinados(raiz, ruta)
    if contenido_bytes is None:
        return _DocumentoJSON({}, False, None)

    try:
        contenido = contenido_bytes.decode("utf-8")
        datos = json.loads(
            contenido,
            parse_constant=_rechazar_constante_json,
            object_pairs_hook=_objeto_sin_claves_duplicadas,
        )
        _validar_valor_json(datos)
    except (json.JSONDecodeError, OverflowError, RecursionError, UnicodeError, ValueError) as error:
        raise ErrorConfiguracionMetricas(
            "La configuracion de metricas no es JSON formal valido.",
            "Corrige UTF-8, profundidad y valores; usa exclusivamente numeros finitos.",
            ruta,
            detalles={"tipo_error": type(error).__name__},
        ) from error
    if not isinstance(datos, dict):
        raise ErrorConfiguracionMetricas(
            "La configuracion de metricas debe ser un objeto JSON.",
            "Usa pares nombre/valor para metricas y umbrales.",
            ruta,
            detalles={"tipo_raiz": type(datos).__name__},
        )
    return _DocumentoJSON(
        datos,
        True,
        hashlib.sha256(contenido_bytes).hexdigest(),
    )


def _validar_excepciones(
    excepciones: Sequence[ExcepcionFallo],
    ahora: datetime,
) -> tuple[ExcepcionFallo, ...]:
    """Revalida el limite publico antes de entregar excepciones a la politica."""
    validadas: list[ExcepcionFallo] = []
    for indice, excepcion in enumerate(excepciones):
        if not isinstance(excepcion, ExcepcionFallo):
            raise ErrorExcepcionInvalida(
                "La coleccion contiene una excepcion de tipo invalido.",
                "Proporciona exclusivamente instancias de ExcepcionFallo.",
                detalles={"indice": indice, "tipo": type(excepcion).__name__},
            )
        campos_texto = (
            excepcion.razon,
            excepcion.riesgo_aceptado,
            excepcion.control_afectado,
            excepcion.referencia,
            excepcion.revisor,
        )
        if any(not isinstance(valor, str) for valor in campos_texto) or (
            excepcion.condicion_remediacion is not None
            and not isinstance(excepcion.condicion_remediacion, str)
        ):
            raise ErrorExcepcionInvalida(
                "La excepcion contiene campos que no son texto.",
                "Usa texto para razon, riesgo, control, referencia, revisor y remediacion.",
                detalles={"indice": indice},
            )
        # Reconstruir activa de nuevo todas las invariantes del modelo incluso si un
        # consumidor altero una instancia congelada mediante tecnicas no soportadas.
        validada = ExcepcionFallo(
            razon=excepcion.razon,
            riesgo_aceptado=excepcion.riesgo_aceptado,
            control_afectado=excepcion.control_afectado,
            referencia=excepcion.referencia,
            revisor=excepcion.revisor,
            expira_en=excepcion.expira_en,
            condicion_remediacion=excepcion.condicion_remediacion,
        )
        if not validada.vigente(ahora):
            raise ErrorExcepcionInvalida(
                "La excepcion ya no esta vigente.",
                "Renueva la aprobacion o corrige el bloqueo.",
                detalles={"control": validada.control_afectado},
            )
        validadas.append(validada)
    return tuple(validadas)


def _construir_metadatos(
    raiz: Path,
    id_paquete: str,
    id_tarea: str,
    operacion: str,
    inicio: datetime,
    fin: datetime,
    ejecucion: EjecucionPuertas,
    estado: ValorEstadoCierre,
    agente: str,
    modelo: str,
    metricas: Mapping[str, object],
    umbrales: Mapping[str, object],
    bloqueos: Sequence[str],
    excepciones: Sequence[ExcepcionFallo],
) -> MetadatosPaqueteEvidencia:
    """Construye el unico esquema de metadatos aceptado por el publicador."""
    return MetadatosPaqueteEvidencia(
        version_esquema=1,
        id_paquete=id_paquete,
        id_tarea=id_tarea,
        operacion=operacion,
        inicio_utc=inicio,
        fin_utc=fin,
        version_tramalia=__version__,
        version_python=platform.python_version(),
        sistema_operativo=platform.platform(),
        cadena_herramientas={"mise": None},
        git=capturar_estado_git(raiz),
        ejecucion=ejecucion,
        estado_cierre=estado,
        agente=agente or None,
        modelo=modelo or None,
        metricas=metricas,
        umbrales=umbrales,
        errores_validacion=tuple(bloqueos),
        excepciones=tuple(excepciones),
        vinculo_traspaso="traspaso.md",
    )


def _json_formal(datos: Mapping[str, object]) -> bytes:
    """Serializa un artefacto legible con las mismas reglas JSON del esquema v1."""
    try:
        contenido = json.dumps(
            dict(datos),
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        return (contenido + "\n").encode("utf-8")
    except (OverflowError, TypeError, UnicodeError, ValueError) as error:
        raise ErrorPersistenciaEvidencia(
            "Las metricas no se pueden serializar como JSON formal.",
            "Usa claves de texto y valores JSON finitos.",
            detalles={"tipo_error": type(error).__name__},
        ) from error


def _diagnostico_umbrales(incumplimientos: Sequence[str]) -> bytes:
    """Representa la evaluacion ya calculada sin ejecutar una segunda politica."""
    if incumplimientos:
        cuerpo = "INCUMPLIMIENTOS:\n" + "\n".join(
            f"- {incumplimiento}" for incumplimiento in incumplimientos
        )
    else:
        cuerpo = "todos los umbrales cumplen"
    return (f"# Evaluacion de umbrales de metricas\n\n{cuerpo}\n").encode()


def _publicar(
    raiz: Path,
    metadatos: MetadatosPaqueteEvidencia,
    resultado: ResultadoCierre,
    agente: str,
    revisor: str,
    *,
    metricas_presentes: bool = False,
    umbrales_presentes: bool = False,
    incumplimientos_metricas: Sequence[str] = (),
) -> PaqueteEvidencia:
    """Publica artefactos exactos y luego intenta actualizar la proyeccion global."""
    archivos = {
        comando.archivo_salida: comando.salida.encode("utf-8")
        for comando in metadatos.ejecucion.resultados
    }
    archivos["traspaso.md"] = construir_traspaso(resultado, agente, revisor)
    if metricas_presentes:
        archivos["metricas.json"] = _json_formal(metadatos.metricas)
    if umbrales_presentes:
        archivos["umbrales-metricas.txt"] = _diagnostico_umbrales(incumplimientos_metricas)

    paquete = publicar_paquete(raiz, metadatos, archivos)
    # La proyeccion es una ayuda de navegacion. Su implementacion garantiza que un
    # fallo aqui no altera ni invalida el paquete canonico ya publicado. Este limite
    # tambien evita que un defecto inesperado o adaptador externo oculte la identidad
    # durable y provoque un reintento que publique un segundo cierre.
    try:
        proyectar_traspaso(raiz, paquete)
    except Exception:
        warnings.warn(
            "El paquete se publico, pero no se pudo actualizar su proyeccion documental.",
            RuntimeWarning,
            stacklevel=2,
        )
    return paquete


def cerrar_proyecto(
    raiz: Path,
    id_tarea: str,
    *,
    agente: str = "",
    revisor: str = "",
    modelo: str = "",
    excepciones: Sequence[ExcepcionFallo] = (),
) -> ResultadoCierre:
    """Ejecuta puertas, evalua la politica y publica un cierre atomico.

    Args:
        raiz: Raiz del proyecto gobernado.
        id_tarea: Identificador portable de la tarea que se cierra.
        agente: Agente ejecutor registrado para auditoria.
        revisor: Responsable reflejado en el traspaso canonico.
        modelo: Modelo usado por el agente ejecutor.
        excepciones: Excepciones completas que cubren controles exactos.

    Returns:
        El resultado definitivo con las rutas del paquete publicado.

    Raises:
        ErrorTramalia: Si el proyecto, la configuracion, una excepcion o la
            persistencia incumplen su contrato.
    """
    estado_proyecto = exigir_proyecto_gobernado(raiz)
    raiz = estado_proyecto.raiz
    validar_id_tarea(id_tarea)
    inicio = datetime.now(UTC)
    excepciones_validadas = _validar_excepciones(excepciones, inicio)

    # Toda configuracion se valida antes de lanzar procesos. Asi un JSON o TOML
    # corrupto no ejecuta una validacion parcial ni deja una interpretacion ambigua.
    puertas = cargar_puertas(raiz)
    metricas_iniciales = _leer_json(raiz, "metrics.json")
    umbrales_iniciales = _leer_json(raiz, "thresholds.json")
    # La primera evaluacion valida el esquema completo antes de ejecutar procesos;
    # sus bloqueos aun no son definitivos porque una puerta puede generar metricas.
    if umbrales_iniciales.datos:
        evaluar_metricas(metricas_iniciales.datos, umbrales_iniciales.datos)

    ejecucion = ejecutar_puertas(raiz, puertas)
    metricas_efectivas = _leer_json(raiz, "metrics.json")
    umbrales_efectivos = _leer_json(raiz, "thresholds.json")
    if (
        umbrales_efectivos.presente != umbrales_iniciales.presente
        or umbrales_efectivos.huella_sha256 != umbrales_iniciales.huella_sha256
    ):
        raise ErrorConfiguracionMetricas(
            "Los umbrales cambiaron durante la ejecucion de puertas.",
            "Repite el cierre con una configuracion de umbrales estable.",
            raiz / ".tramalia" / "thresholds.json",
        )
    incumplimientos_metricas = (
        evaluar_metricas(metricas_efectivas.datos, umbrales_efectivos.datos)
        if umbrales_efectivos.datos
        else ()
    )
    ahora = datetime.now(UTC)
    estado, bloqueos = evaluar_cierre(
        ejecucion,
        incumplimientos_metricas,
        excepciones_validadas,
        ahora,
    )
    id_paquete = crear_id_paquete(ahora)
    provisional = ResultadoCierre(
        estado=estado,
        id_tarea=id_tarea,
        id_paquete=id_paquete,
        ruta_paquete=None,
        ruta_traspaso=None,
        ejecucion=ejecucion,
        excepciones=excepciones_validadas,
        bloqueos=bloqueos,
    )
    metadatos = _construir_metadatos(
        raiz,
        id_paquete,
        id_tarea,
        "cierre",
        inicio,
        ahora,
        ejecucion,
        estado,
        agente,
        modelo,
        metricas_efectivas.datos,
        umbrales_efectivos.datos,
        bloqueos,
        excepciones_validadas,
    )
    paquete = _publicar(
        raiz,
        metadatos,
        provisional,
        agente,
        revisor,
        metricas_presentes=metricas_efectivas.presente,
        umbrales_presentes=umbrales_efectivos.presente,
        incumplimientos_metricas=incumplimientos_metricas,
    )
    return replace(
        provisional,
        ruta_paquete=paquete.ruta,
        ruta_traspaso=paquete.ruta / "traspaso.md",
    )


def _publicar_operacion_independiente(
    raiz: Path,
    id_tarea: str,
    operacion: str,
    bloqueo: str,
    agente: str,
    revisor: str,
    modelo: str,
) -> PaqueteEvidencia:
    """Crea un pack standalone que no afirma haber aprobado un cierre."""
    estado_proyecto = exigir_proyecto_gobernado(raiz)
    raiz = estado_proyecto.raiz
    validar_id_tarea(id_tarea)
    ahora = datetime.now(UTC)
    ejecucion = EjecucionPuertas(estado=ValorEstadoPuertas.SIN_CONFIGURAR)
    id_paquete = crear_id_paquete(ahora)
    resultado = ResultadoCierre(
        estado=ValorEstadoCierre.BLOQUEADO,
        id_tarea=id_tarea,
        id_paquete=id_paquete,
        ruta_paquete=None,
        ruta_traspaso=None,
        ejecucion=ejecucion,
        excepciones=(),
        bloqueos=(bloqueo,),
    )
    metadatos = _construir_metadatos(
        raiz,
        id_paquete,
        id_tarea,
        operacion,
        ahora,
        ahora,
        ejecucion,
        resultado.estado,
        agente,
        modelo,
        {},
        {},
        resultado.bloqueos,
        (),
    )
    return _publicar(raiz, metadatos, resultado, agente, revisor)


def crear_evidencia(
    raiz: Path,
    id_tarea: str,
    *,
    agente: str = "",
    revisor: str = "",
    modelo: str = "",
) -> PaqueteEvidencia:
    """Publica evidencia formal standalone sin afirmar un cierre aprobado.

    Args:
        raiz: Raiz del proyecto gobernado.
        id_tarea: Identificador portable de la tarea.
        agente: Agente ejecutor registrado.
        revisor: Responsable reflejado en el traspaso.
        modelo: Modelo del agente registrado.

    Returns:
        Un paquete v1 nuevo e inmutable con estado ``bloqueado``.
    """
    return _publicar_operacion_independiente(
        raiz,
        id_tarea,
        "evidencia",
        "operacion_evidencia",
        agente,
        revisor,
        modelo,
    )


def registrar_traspaso(
    raiz: Path,
    id_tarea: str,
    *,
    agente: str = "",
    revisor: str = "",
) -> PaqueteEvidencia:
    """Publica un traspaso canonico standalone dentro de un paquete formal.

    Args:
        raiz: Raiz del proyecto gobernado.
        id_tarea: Identificador portable de la tarea.
        agente: Agente que entrega el trabajo.
        revisor: Responsable que recibe o revisa el trabajo.

    Returns:
        Un paquete v1 nuevo e inmutable con estado ``bloqueado``.
    """
    return _publicar_operacion_independiente(
        raiz,
        id_tarea,
        "traspaso",
        "operacion_traspaso",
        agente,
        revisor,
        "",
    )
