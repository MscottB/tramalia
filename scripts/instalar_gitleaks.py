"""Install an audited Gitleaks release without executing downloaded content."""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import platform
import stat
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import IO

from tramalia.core.versiones_herramientas import VERSION_GITLEAKS

MAXIMO_BYTES_DESCARGA = 32 * 1024 * 1024
MAXIMO_MIEMBROS_ARCHIVO = 64
MAXIMO_BYTES_MIEMBRO = 128 * 1024 * 1024
MAXIMO_BYTES_EXTRAIDOS = 160 * 1024 * 1024

_TAMANO_BLOQUE = 1024 * 1024
_URL_PUBLICACION = (
    "https://github.com/gitleaks/gitleaks/releases/download/"
    f"v{VERSION_GITLEAKS}"
)


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
    except (OSError, urllib.error.URLError) as error:
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
    miembros: list[_MiembroArchivo] = []
    total_declarado = 0
    with tarfile.open(fileobj=io.BytesIO(datos), mode="r|gz") as archivo:
        for cantidad, informacion in enumerate(archivo, start=1):
            miembro = _MiembroArchivo(
                nombre=informacion.name,
                tamano=informacion.size,
                modo=informacion.mode,
                regular=informacion.isreg(),
                referencia=None,
            )
            total_declarado = _validar_limite_incremental(
                miembro,
                cantidad,
                total_declarado,
            )
            _validar_ruta_miembro(miembro.nombre)
            if not miembro.regular:
                raise ErrorInstalacionGitleaks(
                    f"el miembro {miembro.nombre!r} no es un archivo regular"
                )
            miembros.append(miembro)

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
    except OSError as error:
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
    except (EOFError, tarfile.TarError, zipfile.BadZipFile) as error:
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
