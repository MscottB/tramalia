"""Install an audited Gitleaks release without executing downloaded content."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import http.client
import io
import lzma
import os
import platform
import stat
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
import zlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import IO

from tramalia.core.versiones_herramientas import VERSION_GITLEAKS

MAXIMO_BYTES_DESCARGA = 32 * 1024 * 1024
MAXIMO_MIEMBROS_ARCHIVO = 64
MAXIMO_BYTES_MIEMBRO = 128 * 1024 * 1024
MAXIMO_BYTES_EXTRAIDOS = 160 * 1024 * 1024
# Un registro TAR estándar ocupa 10 KiB e incluye sus dos bloques de fin.
MAXIMO_BYTES_RELLENO_FINAL_TAR = 10 * 1024

_TAMANO_BLOQUE = 1024 * 1024
_TAMANO_BLOQUE_TAR = tarfile.BLOCKSIZE
_BLOQUE_NULO_TAR = b"\0" * _TAMANO_BLOQUE_TAR
_URL_PUBLICACION = (
    "https://github.com/gitleaks/gitleaks/releases/download/"
    f"v{VERSION_GITLEAKS}"
)

_ERRORES_ARCHIVO_ESPERABLES: tuple[type[BaseException], ...] = (
    EOFError,
    lzma.LZMAError,
    NotImplementedError,
    RuntimeError,
    tarfile.TarError,
    zipfile.BadZipFile,
    zipfile.LargeZipFile,
    zlib.error,
)

try:
    from compression import zstd as _compresion_zstd
except ImportError:  # Python 3.11-3.13 no incluye compression.zstd.
    pass
else:
    _ERRORES_ARCHIVO_ESPERABLES += (_compresion_zstd.ZstdError,)


class ErrorInstalacionGitleaks(RuntimeError):
    """Report a failure to validate or atomically publish Gitleaks."""


@dataclass(frozen=True, slots=True)
class ArtefactoGitleaks:
    """Describe an official Gitleaks asset with its audited digest."""

    nombre: str
    sha256: str

    @property
    def url(self) -> str:
        """Build the immutable URL for the official asset.

        Returns:
            The pinned GitHub release URL.
        """
        return f"{_URL_PUBLICACION}/{self.nombre}"


_ARTEFACTOS_AUDITADOS = {
    ("darwin", "arm64"): ArtefactoGitleaks(
        f"gitleaks_{VERSION_GITLEAKS}_darwin_arm64.tar.gz",
        "b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5",
    ),
    ("darwin", "x86_64"): ArtefactoGitleaks(
        f"gitleaks_{VERSION_GITLEAKS}_darwin_x64.tar.gz",
        "dfe101a4db2255fc85120ac7f3d25e4342c3c20cf749f2c20a18081af1952709",
    ),
    ("linux", "arm64"): ArtefactoGitleaks(
        f"gitleaks_{VERSION_GITLEAKS}_linux_arm64.tar.gz",
        "e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080",
    ),
    ("linux", "x86_64"): ArtefactoGitleaks(
        f"gitleaks_{VERSION_GITLEAKS}_linux_x64.tar.gz",
        "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb",
    ),
    ("windows", "arm64"): ArtefactoGitleaks(
        f"gitleaks_{VERSION_GITLEAKS}_windows_arm64.zip",
        "b95f5e4f5c425cedca7ee203d9afd29597e692c4924a12ed42f970537c72cc0f",
    ),
    ("windows", "x86_64"): ArtefactoGitleaks(
        f"gitleaks_{VERSION_GITLEAKS}_windows_x64.zip",
        "d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e",
    ),
}

_ALIAS_SISTEMAS = {
    "darwin": "darwin",
    "linux": "linux",
    "macos": "darwin",
    "win32": "windows",
    "windows": "windows",
}
_ALIAS_ARQUITECTURAS = {
    "aarch64": "arm64",
    "amd64": "x86_64",
    "arm64": "arm64",
    "x64": "x86_64",
    "x86_64": "x86_64",
}


@dataclass(frozen=True, slots=True)
class _MiembroArchivo:
    nombre: str
    tamano: int
    modo: int
    regular: bool
    referencia: object


def _normalizar_sistema(sistema: str) -> str:
    return _ALIAS_SISTEMAS.get(sistema.strip().lower(), sistema.strip().lower())


def _normalizar_arquitectura(arquitectura: str) -> str:
    valor = arquitectura.strip().lower()
    return _ALIAS_ARQUITECTURAS.get(valor, valor)


def resolver_artefacto(
    sistema: str | None = None,
    arquitectura: str | None = None,
) -> ArtefactoGitleaks:
    """Resolve an audited asset for one supported platform.

    Args:
        sistema: Operating system name, or the current system when omitted.
        arquitectura: Machine architecture, or the current machine when omitted.

    Returns:
        The pinned official asset and its SHA-256 digest.

    Raises:
        ValueError: If the platform pair has not been audited.
    """
    sistema_original = sistema or platform.system()
    arquitectura_original = arquitectura or platform.machine()
    clave = (
        _normalizar_sistema(sistema_original),
        _normalizar_arquitectura(arquitectura_original),
    )
    try:
        return _ARTEFACTOS_AUDITADOS[clave]
    except KeyError as error:
        raise ValueError(
            "plataforma no soportada: "
            f"{sistema_original}/{arquitectura_original}"
        ) from error


def _descargar(url: str) -> bytes:
    """Download one asset with declared and observed size limits.

    Args:
        url: Immutable official asset URL.

    Returns:
        The downloaded bytes.

    Raises:
        ErrorInstalacionGitleaks: If the transfer fails or exceeds 32 MiB.
    """
    try:
        with urllib.request.urlopen(url, timeout=30) as respuesta:  # noqa: S310
            longitud = respuesta.headers.get("Content-Length")
            if longitud is not None:
                try:
                    tamano_declarado = int(longitud)
                except ValueError:
                    tamano_declarado = 0
                if tamano_declarado > MAXIMO_BYTES_DESCARGA:
                    raise ErrorInstalacionGitleaks(
                        "la descarga supera el límite de 32 MiB"
                    )

            bloques: list[bytes] = []
            total = 0
            while True:
                bloque = respuesta.read(_TAMANO_BLOQUE)
                if not bloque:
                    break
                total += len(bloque)
                if total > MAXIMO_BYTES_DESCARGA:
                    raise ErrorInstalacionGitleaks(
                        "la descarga supera el límite de 32 MiB"
                    )
                bloques.append(bloque)
            return b"".join(bloques)
    except ErrorInstalacionGitleaks:
        raise
    except (
        http.client.IncompleteRead,
        http.client.HTTPException,
        OSError,
        urllib.error.URLError,
    ) as error:
        raise ErrorInstalacionGitleaks(f"falló la descarga de Gitleaks: {error}") from error


def _validar_ruta_miembro(nombre: str) -> str:
    normalizado = nombre.replace("\\", "/")
    ruta_windows = PureWindowsPath(nombre)
    if (
        not normalizado
        or "\0" in normalizado
        or normalizado.startswith("/")
        or ruta_windows.is_absolute()
        or bool(ruta_windows.drive)
        or ".." in normalizado.split("/")
    ):
        raise ErrorInstalacionGitleaks(
            f"ruta de miembro no permitida: {nombre!r}"
        )
    return PurePosixPath(normalizado).as_posix()


def _validar_limite_incremental(
    miembro: _MiembroArchivo,
    cantidad: int,
    total_anterior: int,
) -> int:
    if cantidad > MAXIMO_MIEMBROS_ARCHIVO:
        raise ErrorInstalacionGitleaks(
            "el archivo supera el límite de 64 miembros"
        )
    if miembro.tamano < 0:
        raise ErrorInstalacionGitleaks("un miembro declara un tamaño inválido")
    if miembro.tamano > MAXIMO_BYTES_MIEMBRO:
        raise ErrorInstalacionGitleaks(
            "un miembro supera el límite de 128 MiB"
        )
    total = total_anterior + miembro.tamano
    if total > MAXIMO_BYTES_EXTRAIDOS:
        raise ErrorInstalacionGitleaks(
            "el contenido extraído supera el límite de 160 MiB"
        )
    return total


def _validar_limites(miembros: list[_MiembroArchivo]) -> None:
    total = 0
    for cantidad, miembro in enumerate(miembros, start=1):
        total = _validar_limite_incremental(miembro, cantidad, total)


def _leer_numero_octal_tar(campo: bytes, etiqueta: str) -> int:
    if campo and campo[0] & 0x80:
        raise ErrorInstalacionGitleaks(
            f"la cabecera TAR usa una codificación binaria no permitida en {etiqueta}"
        )
    valor = campo.strip(b"\0 ")
    if not valor:
        return 0
    if any(digito not in b"01234567" for digito in valor):
        raise ErrorInstalacionGitleaks(
            f"la cabecera TAR contiene un valor octal inválido en {etiqueta}"
        )
    return int(valor, 8)


def _validar_checksum_tar(cabecera: bytes) -> None:
    almacenado = _leer_numero_octal_tar(cabecera[148:156], "checksum")
    normalizada = cabecera[:148] + (b" " * 8) + cabecera[156:]
    sin_signo = sum(normalizada)
    con_signo = sum(valor if valor < 128 else valor - 256 for valor in normalizada)
    if almacenado not in (sin_signo, con_signo):
        raise ErrorInstalacionGitleaks("la cabecera TAR tiene un checksum inválido")


def _decodificar_texto_tar(campo: bytes) -> str:
    return campo.split(b"\0", 1)[0].decode("utf-8", errors="surrogateescape")


def _miembro_desde_cabecera_tar(
    cabecera: bytes,
) -> tuple[_MiembroArchivo, bytes]:
    _validar_checksum_tar(cabecera)
    nombre = _decodificar_texto_tar(cabecera[0:100])
    if cabecera[257:263] == b"ustar\0":
        prefijo = _decodificar_texto_tar(cabecera[345:500])
        if prefijo:
            nombre = f"{prefijo}/{nombre}" if nombre else prefijo
    tipo = cabecera[156:157]
    miembro = _MiembroArchivo(
        nombre=nombre,
        tamano=_leer_numero_octal_tar(cabecera[124:136], "tamaño"),
        modo=_leer_numero_octal_tar(cabecera[100:108], "modo"),
        regular=tipo in (tarfile.REGTYPE, tarfile.AREGTYPE),
        referencia=None,
    )
    return miembro, tipo


def _leer_hasta_bloque_tar(flujo: gzip.GzipFile) -> bytes:
    partes: list[bytes] = []
    restante = _TAMANO_BLOQUE_TAR
    while restante:
        parte = flujo.read1(restante)
        if not parte:
            break
        partes.append(parte)
        restante -= len(parte)
    return b"".join(partes)


def _consumir_exacto_tar(
    flujo: gzip.GzipFile,
    cantidad: int,
    *,
    exigir_nulos: bool,
    contexto: str,
) -> None:
    restante = cantidad
    while restante:
        bloque = flujo.read1(min(restante, _TAMANO_BLOQUE))
        if not bloque:
            raise ErrorInstalacionGitleaks(f"TAR truncado al leer {contexto}")
        if exigir_nulos and any(bloque):
            raise ErrorInstalacionGitleaks("el padding TAR contiene bytes no nulos")
        restante -= len(bloque)


def _validar_fin_tar(flujo: gzip.GzipFile) -> None:
    segundo = _leer_hasta_bloque_tar(flujo)
    if len(segundo) != _TAMANO_BLOQUE_TAR:
        raise ErrorInstalacionGitleaks("fin TAR truncado: falta el segundo bloque nulo")
    if segundo != _BLOQUE_NULO_TAR:
        raise ErrorInstalacionGitleaks("fin TAR inválido: se requieren dos bloques nulos")
    bytes_relleno_final = 2 * _TAMANO_BLOQUE_TAR
    while bytes_relleno_final < MAXIMO_BYTES_RELLENO_FINAL_TAR:
        adicional = _leer_hasta_bloque_tar(flujo)
        if not adicional:
            return
        if len(adicional) != _TAMANO_BLOQUE_TAR:
            raise ErrorInstalacionGitleaks("TAR truncado después de su marca de fin")
        if adicional != _BLOQUE_NULO_TAR:
            raise ErrorInstalacionGitleaks("el TAR contiene datos después de su marca de fin")
        bytes_relleno_final += len(adicional)
    if flujo.read1(1):
        raise ErrorInstalacionGitleaks(
            "el relleno final TAR supera el límite de 10 KiB"
        )


def _prevalidar_tar_crudo(datos: bytes) -> list[_MiembroArchivo]:
    miembros: list[_MiembroArchivo] = []
    total_declarado = 0
    cantidad_cabeceras = 0
    with gzip.GzipFile(fileobj=io.BytesIO(datos), mode="rb") as flujo:
        while True:
            cabecera = _leer_hasta_bloque_tar(flujo)
            if len(cabecera) != _TAMANO_BLOQUE_TAR:
                raise ErrorInstalacionGitleaks("TAR truncado o sin marca de fin")
            if cabecera == _BLOQUE_NULO_TAR:
                _validar_fin_tar(flujo)
                return miembros

            miembro, tipo = _miembro_desde_cabecera_tar(cabecera)
            cantidad_cabeceras += 1
            total_declarado = _validar_limite_incremental(
                miembro,
                cantidad_cabeceras,
                total_declarado,
            )
            if tipo not in (tarfile.REGTYPE, tarfile.AREGTYPE):
                raise ErrorInstalacionGitleaks(
                    f"el miembro TAR {miembro.nombre!r} no es un archivo regular"
                )
            _validar_ruta_miembro(miembro.nombre)
            miembros.append(miembro)

            _consumir_exacto_tar(
                flujo,
                miembro.tamano,
                exigir_nulos=False,
                contexto=f"el payload de {miembro.nombre!r}",
            )
            tamano_padding = (-miembro.tamano) % _TAMANO_BLOQUE_TAR
            _consumir_exacto_tar(
                flujo,
                tamano_padding,
                exigir_nulos=True,
                contexto=f"el padding de {miembro.nombre!r}",
            )


def _seleccionar_ejecutable(
    miembros: list[_MiembroArchivo],
    nombre_esperado: str,
) -> _MiembroArchivo:
    candidatos: list[tuple[_MiembroArchivo, str]] = []
    for miembro in miembros:
        nombre = _validar_ruta_miembro(miembro.nombre)
        if not miembro.regular:
            raise ErrorInstalacionGitleaks(
                f"el miembro {miembro.nombre!r} no es un archivo regular"
            )
        es_candidato = nombre == nombre_esperado
        if nombre_esperado.endswith(".exe"):
            es_candidato = es_candidato or nombre.lower().endswith(".exe")
        else:
            es_candidato = es_candidato or bool(miembro.modo & 0o111)
        if es_candidato:
            candidatos.append((miembro, nombre))

    if len(candidatos) != 1:
        raise ErrorInstalacionGitleaks(
            "el archivo debe contener un solo ejecutable"
        )
    elegido, nombre = candidatos[0]
    if nombre != nombre_esperado:
        raise ErrorInstalacionGitleaks(
            f"el ejecutable debe llamarse exactamente {nombre_esperado!r}"
        )
    return elegido


def _copiar_flujo(
    miembro: _MiembroArchivo,
    origen: IO[bytes],
    salida: IO[bytes] | None,
    total_anterior: int,
) -> int:
    total_miembro = 0
    total_extraido = total_anterior
    while True:
        bloque = origen.read(_TAMANO_BLOQUE)
        if not bloque:
            break
        total_miembro += len(bloque)
        total_extraido += len(bloque)
        if total_miembro > MAXIMO_BYTES_MIEMBRO:
            raise ErrorInstalacionGitleaks(
                "un miembro supera el límite de 128 MiB"
            )
        if total_extraido > MAXIMO_BYTES_EXTRAIDOS:
            raise ErrorInstalacionGitleaks(
                "el contenido extraído supera el límite de 160 MiB"
            )
        if salida is not None:
            salida.write(bloque)
    if total_miembro != miembro.tamano:
        raise ErrorInstalacionGitleaks(
            f"el tamaño real de {miembro.nombre!r} no coincide con su cabecera"
        )
    return total_extraido


def _copiar_y_recontar(
    miembros: list[_MiembroArchivo],
    elegido: _MiembroArchivo,
    abrir_miembro: Callable[[_MiembroArchivo], IO[bytes]],
    salida: IO[bytes],
) -> None:
    total_extraido = 0
    for miembro in miembros:
        with abrir_miembro(miembro) as origen:
            total_extraido = _copiar_flujo(
                miembro,
                origen,
                salida if miembro is elegido else None,
                total_extraido,
            )


def _publicar_temporal(
    destino: Path,
    nombre_ejecutable: str,
    sistema: str,
    escribir: Callable[[IO[bytes]], None],
) -> Path:
    descriptor, nombre_temporal = tempfile.mkstemp(
        dir=destino,
        prefix=".gitleaks-",
        suffix=".tmp",
    )
    descriptor_pendiente: int | None = descriptor
    temporal = Path(nombre_temporal)
    publicado = destino / nombre_ejecutable
    try:
        archivo_temporal = os.fdopen(descriptor, "wb")
        descriptor_pendiente = None
        with archivo_temporal as salida:
            escribir(salida)
            salida.flush()
            os.fsync(salida.fileno())
        if sistema != "windows":
            os.chmod(temporal, 0o755)
        os.replace(temporal, publicado)
    finally:
        if descriptor_pendiente is not None:
            os.close(descriptor_pendiente)
        temporal.unlink(missing_ok=True)
    return publicado.resolve()


def _publicar_desde_miembros(
    miembros: list[_MiembroArchivo],
    abrir_miembro: Callable[[_MiembroArchivo], IO[bytes]],
    destino: Path,
    nombre_ejecutable: str,
    sistema: str,
) -> Path:
    _validar_limites(miembros)
    elegido = _seleccionar_ejecutable(miembros, nombre_ejecutable)

    def escribir(salida: IO[bytes]) -> None:
        _copiar_y_recontar(miembros, elegido, abrir_miembro, salida)

    return _publicar_temporal(
        destino,
        nombre_ejecutable,
        sistema,
        escribir,
    )


def _publicar_zip(
    datos: bytes,
    destino: Path,
    nombre_ejecutable: str,
    sistema: str,
) -> Path:
    with zipfile.ZipFile(io.BytesIO(datos), mode="r") as archivo:
        miembros = []
        for informacion in archivo.infolist():
            modo = (informacion.external_attr >> 16) & 0xFFFF
            tipo = stat.S_IFMT(modo)
            miembros.append(
                _MiembroArchivo(
                    nombre=informacion.filename,
                    tamano=informacion.file_size,
                    modo=modo,
                    regular=not informacion.is_dir() and tipo in (0, stat.S_IFREG),
                    referencia=informacion,
                )
            )

        def abrir_miembro(miembro: _MiembroArchivo) -> IO[bytes]:
            assert isinstance(miembro.referencia, zipfile.ZipInfo)
            return archivo.open(miembro.referencia, mode="r")

        return _publicar_desde_miembros(
            miembros,
            abrir_miembro,
            destino,
            nombre_ejecutable,
            sistema,
        )


def _publicar_tar(
    datos: bytes,
    destino: Path,
    nombre_ejecutable: str,
    sistema: str,
) -> Path:
    miembros = _prevalidar_tar_crudo(datos)
    elegido = _seleccionar_ejecutable(miembros, nombre_ejecutable)
    indice_elegido = next(
        indice for indice, miembro in enumerate(miembros) if miembro is elegido
    )

    def escribir(salida: IO[bytes]) -> None:
        total_extraido = 0
        cantidad_copiada = 0
        with tarfile.open(fileobj=io.BytesIO(datos), mode="r|gz") as archivo:
            for indice, informacion in enumerate(archivo):
                if indice >= len(miembros):
                    raise ErrorInstalacionGitleaks(
                        "las cabeceras TAR cambiaron entre validación y copia"
                    )
                esperado = miembros[indice]
                observado = _MiembroArchivo(
                    nombre=informacion.name,
                    tamano=informacion.size,
                    modo=informacion.mode,
                    regular=informacion.isreg(),
                    referencia=informacion,
                )
                if (
                    observado.nombre,
                    observado.tamano,
                    observado.modo,
                    observado.regular,
                ) != (
                    esperado.nombre,
                    esperado.tamano,
                    esperado.modo,
                    esperado.regular,
                ):
                    raise ErrorInstalacionGitleaks(
                        "las cabeceras TAR cambiaron entre validación y copia"
                    )
                flujo = archivo.extractfile(informacion)
                if flujo is None:
                    raise ErrorInstalacionGitleaks(
                        f"no se pudo leer el miembro {observado.nombre!r}"
                    )
                with flujo:
                    total_extraido = _copiar_flujo(
                        observado,
                        flujo,
                        salida if indice == indice_elegido else None,
                        total_extraido,
                    )
                cantidad_copiada += 1
        if cantidad_copiada != len(miembros):
            raise ErrorInstalacionGitleaks(
                "las cabeceras TAR cambiaron entre validación y copia"
            )

    return _publicar_temporal(
        destino,
        nombre_ejecutable,
        sistema,
        escribir,
    )


def _preparar_destino(destino: str | os.PathLike[str]) -> Path:
    try:
        ruta_destino = Path(destino).expanduser().resolve()
        ruta_destino.mkdir(parents=True, exist_ok=True)
        if not ruta_destino.is_dir():
            raise ErrorInstalacionGitleaks(
                f"el destino no es un directorio: {ruta_destino}"
            )
        return ruta_destino
    except ErrorInstalacionGitleaks:
        raise
    except (OSError, RuntimeError) as error:
        raise ErrorInstalacionGitleaks(
            f"no se pudo preparar el destino {destino!s}: {error}"
        ) from error


def instalar(
    destino: str | os.PathLike[str],
    *,
    sistema: str | None = None,
    arquitectura: str | None = None,
) -> Path:
    """Download, validate, and atomically publish the audited binary.

    Args:
        destino: Directory where the executable will be published.
        sistema: Operating system override used by tests and cross-installers.
        arquitectura: Machine architecture override.

    Returns:
        The absolute path of the published executable.

    Raises:
        ErrorInstalacionGitleaks: If validation, extraction, or publication fails.
        ValueError: If the platform pair has not been audited.
    """
    sistema_resuelto = _normalizar_sistema(sistema or platform.system())
    arquitectura_resuelta = _normalizar_arquitectura(
        arquitectura or platform.machine()
    )
    artefacto = resolver_artefacto(sistema_resuelto, arquitectura_resuelta)
    ruta_destino = _preparar_destino(destino)
    datos = _descargar(artefacto.url)
    digest = hashlib.sha256(datos).hexdigest()
    if digest != artefacto.sha256:
        raise ErrorInstalacionGitleaks(
            "la descarga no coincide con el SHA-256 oficial"
        )

    nombre_ejecutable = "gitleaks.exe" if sistema_resuelto == "windows" else "gitleaks"

    try:
        if artefacto.nombre.endswith(".zip"):
            return _publicar_zip(
                datos,
                ruta_destino,
                nombre_ejecutable,
                sistema_resuelto,
            )
        if artefacto.nombre.endswith(".tar.gz"):
            return _publicar_tar(
                datos,
                ruta_destino,
                nombre_ejecutable,
                sistema_resuelto,
            )
        raise ErrorInstalacionGitleaks(
            f"formato de activo no soportado: {artefacto.nombre}"
        )
    except ErrorInstalacionGitleaks:
        raise
    except OSError as error:
        raise ErrorInstalacionGitleaks(
            f"no se pudo publicar Gitleaks: {error}"
        ) from error
    except _ERRORES_ARCHIVO_ESPERABLES as error:
        raise ErrorInstalacionGitleaks(
            f"el archivo descargado no es válido: {error}"
        ) from error


def main(argumentos: list[str] | None = None) -> int:
    """Run the installer and emit only the published path on stdout.

    Args:
        argumentos: Optional command-line arguments for programmatic callers.

    Returns:
        Zero on success and one when installation fails.
    """
    analizador = argparse.ArgumentParser(description=__doc__)
    analizador.add_argument(
        "--destino",
        type=Path,
        required=True,
        help="directorio donde publicar el ejecutable",
    )
    opciones = analizador.parse_args(argumentos)
    try:
        publicado = instalar(opciones.destino)
    except (ErrorInstalacionGitleaks, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(publicado)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
