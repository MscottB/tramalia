"""Validate untrusted skill and MCP inputs at local trust boundaries."""

from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from tramalia.core import procesos
from tramalia.core.errores import ErrorEntradaInsegura

_PATRON_NOMBRE_HABILIDAD = re.compile(r"[a-z0-9](?:[a-z0-9._-]{0,62}[a-z0-9])?")
_DISPOSITIVOS_WINDOWS = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{indice}" for indice in range(1, 10)),
    *(f"LPT{indice}" for indice in range(1, 10)),
}
_MAXIMO_ARCHIVOS_HABILIDAD = 2_000
_MAXIMO_BYTES_ARCHIVO = 4 * 1024 * 1024
_MAXIMO_BYTES_ARBOL = 64 * 1024 * 1024
_PATRON_OSC = re.compile(r"\x1b\].*?(?:\x07|\x1b\\|$)", re.DOTALL)
_PATRON_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_PATRON_ASIGNACION = re.compile(r"(?i)(?<![\w.-])(?P<clave>[\"']?(?>[\w.-]+)[\"']?)\s*[:=]\s*")
_NOMBRES_SECRETOS = ("token", "secret", "password", "contrasena", "api_key", "authorization")


@dataclass(frozen=True, slots=True)
class ResumenArbolHabilidad:
    """Summarize the bounded regular files in one validated skill tree.

    Attributes:
        archivos: Number of regular files excluding repository metadata.
        bytes_totales: Total logical size of those files in bytes.
    """

    archivos: int
    bytes_totales: int


def validar_nombre_habilidad(nombre: str) -> str:
    """Validate a skill name for safe use as one directory component.

    Args:
        nombre: Candidate skill name.

    Returns:
        The unchanged validated name.

    Raises:
        ErrorEntradaInsegura: If the name is not a safe portable component.
    """
    if (
        _PATRON_NOMBRE_HABILIDAD.fullmatch(nombre) is None
        or nombre.upper() in _DISPOSITIVOS_WINDOWS
    ):
        raise ErrorEntradaInsegura(
            "El nombre de habilidad no es un componente de ruta seguro.",
            "Usa entre 1 y 64 caracteres minusculos, numeros, punto, guion o guion bajo.",
        )
    return nombre


def validar_fuente_git(fuente: str) -> str:
    """Validate and normalize an HTTPS Git source.

    Args:
        fuente: Candidate Git source using HTTPS or git+HTTPS.

    Returns:
        The canonical source prefixed with ``git+``.

    Raises:
        ErrorEntradaInsegura: If the source does not use HTTPS.
    """
    valor = fuente.strip()
    url = valor.removeprefix("git+")
    partes = urlsplit(url)
    if partes.scheme != "https" or not partes.netloc or valor not in {url, f"git+{url}"}:
        raise ErrorEntradaInsegura(
            "La fuente Git debe usar HTTPS.",
            "Declara una URL https:// o git+https:// valida.",
        )
    return f"git+{url}"


def resolver_ruta_confinada(
    raiz: Path,
    relativa: Path,
    *,
    permitir_ausente: bool = False,
) -> Path:
    """Resolve a relative path while confining it to a trusted root.

    Args:
        raiz: Trusted filesystem root.
        relativa: Untrusted relative path below the root.
        permitir_ausente: Whether the resolved target may be absent.

    Returns:
        The resolved path confined below the resolved root.

    Raises:
        ErrorEntradaInsegura: If the path escapes, is absolute, or is absent
            when absence is not allowed.
    """
    if relativa.is_absolute():
        raise ErrorEntradaInsegura(
            "La ruta absoluta no esta permitida.",
            "Usa una ruta relativa dentro del proyecto.",
        )
    try:
        raiz_resuelta = raiz.resolve(strict=True)
        candidata = (raiz_resuelta / relativa).resolve(strict=False)
    except OSError as error_ruta:
        raise ErrorEntradaInsegura(
            "La ruta no se pudo resolver de forma segura.",
            "Verifica que la raiz exista y no contenga enlaces invalidos.",
        ) from error_ruta
    if not candidata.is_relative_to(raiz_resuelta):
        raise ErrorEntradaInsegura(
            "La ruta queda fuera de la raiz permitida.",
            "Usa una ruta relativa confinada al proyecto.",
        )
    if not permitir_ausente and not candidata.exists():
        raise ErrorEntradaInsegura(
            "La ruta confinada no existe.",
            "Crea el archivo dentro del proyecto o usa una ruta existente.",
        )
    return candidata


def _es_reparse_point(informacion: object) -> bool:
    atributo = getattr(informacion, "st_file_attributes", 0)
    mascara = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(atributo & mascara)


def _error_arbol(mensaje: str, ruta: Path) -> ErrorEntradaInsegura:
    return ErrorEntradaInsegura(
        mensaje,
        "Retira la entrada insegura o reduce el arbol antes de sincronizar.",
        ruta=ruta,
    )


def _validar_modos_git(ruta: Path) -> None:
    if not (ruta / ".git").exists():
        return
    resultado = procesos.ejecutar(
        ["git", "-C", str(ruta), "ls-tree", "-r", "HEAD"],
        raiz=ruta,
        limite_segundos=20,
    )
    if not resultado.exitoso:
        raise _error_arbol("No se pudieron validar los modos Git del arbol.", ruta)
    for linea in resultado.salida.splitlines():
        modo = linea.split(maxsplit=1)[0] if linea else ""
        if modo in {"120000", "160000"}:
            raise _error_arbol(f"El arbol contiene una entrada Git modo {modo}.", ruta)


def validar_arbol_habilidad(ruta: Path) -> ResumenArbolHabilidad:
    """Validate a skill tree without following links or reparse points.

    Args:
        ruta: Checked-out skill directory to inspect.

    Returns:
        File count and logical byte total excluding the root ``.git`` entry.

    Raises:
        ErrorEntradaInsegura: If the tree contains unsafe entry types,
            forbidden metadata, or exceeds an exact resource limit.
    """
    try:
        informacion_raiz = ruta.lstat()
    except OSError as error_raiz:
        raise _error_arbol("El arbol de habilidad no se puede inspeccionar.", ruta) from error_raiz
    if stat.S_ISLNK(informacion_raiz.st_mode):
        raise _error_arbol("El arbol de habilidad no puede ser un enlace.", ruta)
    if _es_reparse_point(informacion_raiz):
        raise _error_arbol("El arbol de habilidad no puede ser un reparse point.", ruta)
    if not stat.S_ISDIR(informacion_raiz.st_mode):
        raise _error_arbol("La habilidad debe ser un directorio.", ruta)
    _validar_modos_git(ruta)

    archivos = 0
    bytes_totales = 0
    pendientes = [ruta]
    while pendientes:
        directorio = pendientes.pop()
        try:
            entradas = sorted(os.scandir(directorio), key=lambda entrada: entrada.name)
        except OSError as error_directorio:
            raise _error_arbol(
                "El arbol de habilidad no se puede recorrer por completo.",
                directorio,
            ) from error_directorio
        for entrada in entradas:
            candidata = Path(entrada.path)
            try:
                informacion = candidata.lstat()
            except OSError as error_entrada:
                raise _error_arbol(
                    "Una entrada del arbol no se puede inspeccionar.",
                    candidata,
                ) from error_entrada
            if stat.S_ISLNK(informacion.st_mode):
                raise _error_arbol("El arbol de habilidad contiene un enlace.", candidata)
            if _es_reparse_point(informacion):
                raise _error_arbol(
                    "El arbol de habilidad contiene un reparse point.",
                    candidata,
                )
            if directorio == ruta and entrada.name == ".git":
                continue
            if entrada.name == ".gitmodules":
                raise _error_arbol("El arbol de habilidad contiene .gitmodules.", candidata)
            if stat.S_ISDIR(informacion.st_mode):
                pendientes.append(candidata)
                continue
            if not stat.S_ISREG(informacion.st_mode):
                raise _error_arbol("El arbol contiene una entrada especial insegura.", candidata)
            archivos += 1
            if archivos > _MAXIMO_ARCHIVOS_HABILIDAD:
                raise _error_arbol("El arbol supera el limite de 2.000 archivos.", ruta)
            if informacion.st_size > _MAXIMO_BYTES_ARCHIVO:
                raise _error_arbol("Un archivo supera el limite de 4 MiB.", candidata)
            bytes_totales += informacion.st_size
            if bytes_totales > _MAXIMO_BYTES_ARBOL:
                raise _error_arbol("El arbol supera el limite total de 64 MiB.", ruta)
    return ResumenArbolHabilidad(archivos=archivos, bytes_totales=bytes_totales)


def _texto_seguro_basico(valor: object) -> str:
    if isinstance(valor, str):
        return valor
    if isinstance(valor, (bytes, bytearray)):
        return bytes(valor).decode("utf-8", errors="replace")
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if isinstance(valor, (int, float)):
        return str(valor)
    tipo = type(valor)
    return f"<objeto_no_serializable:{tipo.__module__}.{tipo.__qualname__}>"


def _prefijo_utf8(texto: str, maximo_bytes: int) -> tuple[str, int]:
    codificado = texto.encode("utf-8")
    if len(codificado) <= maximo_bytes:
        return texto, 0
    prefijo = codificado[:maximo_bytes].decode("utf-8", errors="ignore")
    retenidos = len(prefijo.encode("utf-8"))
    return prefijo, len(codificado) - retenidos


def _redactar_asignacion(linea: str) -> str:
    posicion = 0
    while coincidencia := _PATRON_ASIGNACION.search(linea, posicion):
        clave = coincidencia.group("clave").strip("\"'").casefold()
        if any(nombre in clave for nombre in _NOMBRES_SECRETOS):
            return linea[: coincidencia.end()] + "[REDACTADO]"
        posicion = coincidencia.end()
    return linea


def _anadir_marca_truncado(
    texto: str,
    *,
    maximo_bytes: int,
    bytes_omitidos_iniciales: int,
) -> str:
    codificado = texto.encode("utf-8")
    if bytes_omitidos_iniciales == 0 and len(codificado) <= maximo_bytes:
        return texto
    omitidos = bytes_omitidos_iniciales + max(0, len(codificado) - maximo_bytes)
    for _intento in range(10):
        marca = f"\n[TRUNCADO: {omitidos} bytes omitidos]"
        bytes_marca = len(marca.encode("utf-8"))
        if bytes_marca >= maximo_bytes:
            return _prefijo_utf8(marca, maximo_bytes)[0]
        prefijo, omitidos_total = _prefijo_utf8(texto, maximo_bytes - bytes_marca)
        nuevo_total = bytes_omitidos_iniciales + omitidos_total
        if nuevo_total == omitidos:
            return prefijo + marca
        omitidos = nuevo_total
    marca = f"\n[TRUNCADO: {omitidos} bytes omitidos]"
    prefijo = _prefijo_utf8(texto, maximo_bytes - len(marca.encode("utf-8")))[0]
    return prefijo + marca


def _sanear_texto(
    valor: object,
    *,
    maximo_bytes: int,
    maximo_linea: int,
    bytes_omitidos_adicionales: int = 0,
) -> str:
    texto = _texto_seguro_basico(valor)
    texto = _PATRON_OSC.sub("", texto)
    texto = _PATRON_ANSI.sub("", texto)
    texto = "".join(
        caracter for caracter in texto if caracter in {"\n", "\t"} or ord(caracter) >= 32
    )
    lineas: list[str] = []
    omitidos_lineas = bytes_omitidos_adicionales
    for linea in texto.split("\n"):
        linea = _redactar_asignacion(linea)
        prefijo, omitidos = _prefijo_utf8(linea, maximo_linea)
        lineas.append(prefijo)
        omitidos_lineas += omitidos
    return _anadir_marca_truncado(
        "\n".join(lineas),
        maximo_bytes=maximo_bytes,
        bytes_omitidos_iniciales=omitidos_lineas,
    )


def leer_texto_confinado(
    raiz: Path,
    relativa: Path,
    *,
    maximo_bytes: int = 131_072,
) -> str:
    """Read bounded UTF-8 text from a path confined to a trusted root.

    Args:
        raiz: Trusted filesystem root.
        relativa: Untrusted relative file path.
        maximo_bytes: Maximum UTF-8 bytes returned, including truncation notice.

    Returns:
        Sanitized text whose encoded size does not exceed the limit.

    Raises:
        ErrorEntradaInsegura: If the path escapes, is not a regular file, or
            cannot be read safely.
        ValueError: If the byte limit is not positive.
    """
    if maximo_bytes <= 0:
        raise ValueError("el limite de bytes debe ser positivo")
    ruta = resolver_ruta_confinada(raiz, relativa)
    try:
        with ruta.open("rb") as archivo:
            informacion_inicial = os.fstat(archivo.fileno())
            if not stat.S_ISREG(informacion_inicial.st_mode):
                raise ErrorEntradaInsegura(
                    "La ruta confinada no es un archivo regular.",
                    "Usa un archivo de texto regular dentro del proyecto.",
                    ruta=relativa,
                )
            contenido = archivo.read(maximo_bytes + 1)
            informacion_final = os.fstat(archivo.fileno())
    except ErrorEntradaInsegura:
        raise
    except OSError as error_lectura:
        raise ErrorEntradaInsegura(
            "El archivo confinado no se pudo leer.",
            "Verifica que sea un archivo regular accesible dentro del proyecto.",
            ruta=relativa,
        ) from error_lectura
    prefijo = contenido[:maximo_bytes]
    tamano_observado = max(
        informacion_inicial.st_size,
        informacion_final.st_size,
        len(contenido),
    )
    omitidos = max(0, tamano_observado - len(prefijo))
    texto = prefijo.decode("utf-8", errors="replace")
    return _sanear_texto(
        texto,
        maximo_bytes=maximo_bytes,
        maximo_linea=8_192,
        bytes_omitidos_adicionales=omitidos,
    )


def sanear_texto_externo(
    valor: object,
    *,
    maximo_bytes: int = 131_072,
    maximo_linea: int = 8_192,
) -> str:
    """Sanitize untrusted text for bounded local transport output.

    Args:
        valor: External value or known scalar to sanitize.
        maximo_bytes: Maximum UTF-8 bytes returned, including truncation notice.
        maximo_linea: Maximum UTF-8 bytes retained from each logical line.

    Returns:
        Redacted, control-free, valid UTF-8 text within both limits.

    Raises:
        ValueError: If either limit is not positive.
    """
    if maximo_bytes <= 0 or maximo_linea <= 0:
        raise ValueError("los limites de saneamiento deben ser positivos")
    return _sanear_texto(
        valor,
        maximo_bytes=maximo_bytes,
        maximo_linea=maximo_linea,
    )
