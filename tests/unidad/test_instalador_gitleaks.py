from __future__ import annotations

import gzip
import hashlib
import io
import os
import stat
import struct
import tarfile
import tomllib
import zipfile
from pathlib import Path

import pytest

from scripts import instalar_gitleaks as instalador
from scripts.instalar_gitleaks import (
    ArtefactoGitleaks,
    ErrorInstalacionGitleaks,
    instalar,
    resolver_artefacto,
)
from tramalia.core import versiones_herramientas
from tramalia.core.versiones_herramientas import (
    VERSION_ACTIONLINT,
    VERSION_ACTIONLINT_PY,
    VERSION_GITLEAKS,
    VERSION_SEMGREP,
)


def _crear_zip(miembros: list[tuple[str, bytes, int]]) -> bytes:
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as archivo:
        for nombre, contenido, modo in miembros:
            informacion = zipfile.ZipInfo(nombre)
            informacion.create_system = 3
            informacion.external_attr = modo << 16
            archivo.writestr(informacion, contenido)
    return salida.getvalue()


def _crear_tar(
    miembros: list[tuple[str, bytes, bytes, int, str]],
) -> bytes:
    salida = io.BytesIO()
    with tarfile.open(fileobj=salida, mode="w:gz") as archivo:
        for nombre, contenido, tipo, modo, enlace in miembros:
            informacion = tarfile.TarInfo(nombre)
            informacion.type = tipo
            informacion.mode = modo
            informacion.linkname = enlace
            informacion.size = len(contenido) if tipo in (tarfile.REGTYPE, tarfile.AREGTYPE) else 0
            archivo.addfile(informacion, io.BytesIO(contenido) if informacion.isreg() else None)
    return salida.getvalue()


def _inyectar_archivo(
    monkeypatch: pytest.MonkeyPatch,
    datos: bytes,
    nombre: str,
) -> None:
    artefacto = ArtefactoGitleaks(nombre=nombre, sha256=hashlib.sha256(datos).hexdigest())
    monkeypatch.setattr(
        instalador,
        "resolver_artefacto",
        lambda _sistema, _arquitectura: artefacto,
    )
    monkeypatch.setattr(instalador, "_descargar", lambda _url: datos)


def _ajustar_tamanos_zip(datos: bytes, tamanos: list[int]) -> bytes:
    ajustados = bytearray(datos)
    posicion = 0
    for tamano in tamanos:
        posicion = ajustados.find(b"PK\x01\x02", posicion)
        assert posicion >= 0
        struct.pack_into("<I", ajustados, posicion + 24, tamano)
        posicion += 46
    return bytes(ajustados)


def _crear_zip_con_limite(caso: str) -> bytes:
    if caso == "miembro":
        datos = _crear_zip([("grande.bin", b"", stat.S_IFREG | 0o644)])
        return _ajustar_tamanos_zip(datos, [instalador.MAXIMO_BYTES_MIEMBRO + 1])
    if caso == "total":
        datos = _crear_zip(
            [
                ("uno.bin", b"", stat.S_IFREG | 0o644),
                ("dos.bin", b"", stat.S_IFREG | 0o644),
            ]
        )
        mitad_excedida = instalador.MAXIMO_BYTES_EXTRAIDOS // 2 + 1
        return _ajustar_tamanos_zip(datos, [mitad_excedida, mitad_excedida])
    return _crear_zip(
        [
            (f"miembro-{indice}.txt", b"", stat.S_IFREG | 0o644)
            for indice in range(instalador.MAXIMO_MIEMBROS_ARCHIVO + 1)
        ]
    )


def _crear_tar_declarado(tamanos: list[int]) -> bytes:
    salida = io.BytesIO()
    ceros = b"\0" * (1024 * 1024)
    with gzip.GzipFile(fileobj=salida, mode="wb", mtime=0) as comprimido:
        for indice, tamano in enumerate(tamanos):
            informacion = tarfile.TarInfo(f"miembro-{indice}.bin")
            informacion.mode = 0o644
            informacion.size = tamano
            comprimido.write(informacion.tobuf(format=tarfile.GNU_FORMAT))
            restante = tamano
            while restante:
                bloque = ceros[: min(restante, len(ceros))]
                comprimido.write(bloque)
                restante -= len(bloque)
            relleno = (-tamano) % tarfile.BLOCKSIZE
            if relleno:
                comprimido.write(b"\0" * relleno)
        comprimido.write(b"\0" * (tarfile.BLOCKSIZE * 2))
    return salida.getvalue()


def _crear_tar_con_limite(caso: str) -> bytes:
    if caso == "miembro":
        return _crear_tar_declarado([instalador.MAXIMO_BYTES_MIEMBRO + 1])
    if caso == "total":
        mitad_excedida = instalador.MAXIMO_BYTES_EXTRAIDOS // 2 + 1
        return _crear_tar_declarado([mitad_excedida, mitad_excedida])
    return _crear_tar(
        [
            (f"miembro-{indice}.txt", b"", tarfile.REGTYPE, 0o644, "")
            for indice in range(instalador.MAXIMO_MIEMBROS_ARCHIVO + 1)
        ]
    )


def _afirmar_sin_publicacion(destino: Path, nombre: str) -> None:
    assert not (destino / nombre).exists()
    assert not list(destino.glob(".gitleaks-*.tmp"))


def test_versiones_de_herramientas_quedan_fijadas() -> None:
    assert VERSION_ACTIONLINT == "1.7.12"
    assert VERSION_ACTIONLINT_PY == "1.7.12.24"
    assert VERSION_GITLEAKS == "8.30.1"
    assert VERSION_SEMGREP == "1.169.0"


def test_grupo_seguridad_no_contamina_dependencias_del_paquete() -> None:
    raiz = Path(__file__).parents[2]
    configuracion = tomllib.loads((raiz / "pyproject.toml").read_text(encoding="utf-8"))

    assert configuracion["dependency-groups"]["seguridad"] == [
        "actionlint-py==1.7.12.24",
        "semgrep==1.169.0",
    ]
    assert all(
        not dependencia.startswith(("actionlint-py", "semgrep"))
        for dependencia in configuracion["project"]["dependencies"]
    )


def test_resuelve_windows_x64_con_digest_oficial() -> None:
    artefacto = resolver_artefacto("windows", "x86_64")
    assert artefacto.nombre == "gitleaks_8.30.1_windows_x64.zip"
    assert artefacto.sha256 == "d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e"


@pytest.mark.parametrize(
    ("sistema", "arquitectura", "nombre", "digest"),
    [
        (
            "darwin",
            "arm64",
            "gitleaks_8.30.1_darwin_arm64.tar.gz",
            "b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5",
        ),
        (
            "darwin",
            "x86_64",
            "gitleaks_8.30.1_darwin_x64.tar.gz",
            "dfe101a4db2255fc85120ac7f3d25e4342c3c20cf749f2c20a18081af1952709",
        ),
        (
            "linux",
            "arm64",
            "gitleaks_8.30.1_linux_arm64.tar.gz",
            "e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080",
        ),
        (
            "linux",
            "x86_64",
            "gitleaks_8.30.1_linux_x64.tar.gz",
            "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb",
        ),
        (
            "windows",
            "arm64",
            "gitleaks_8.30.1_windows_arm64.zip",
            "b95f5e4f5c425cedca7ee203d9afd29597e692c4924a12ed42f970537c72cc0f",
        ),
        (
            "windows",
            "x86_64",
            "gitleaks_8.30.1_windows_x64.zip",
            "d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e",
        ),
    ],
)
def test_resuelve_las_seis_combinaciones_auditadas(
    sistema: str,
    arquitectura: str,
    nombre: str,
    digest: str,
) -> None:
    artefacto = resolver_artefacto(sistema, arquitectura)

    assert artefacto.nombre == nombre
    assert artefacto.sha256 == digest


def test_rechaza_plataforma_no_auditada() -> None:
    with pytest.raises(ValueError, match="plataforma no soportada"):
        resolver_artefacto("plan9", "x86_64")


def test_digest_incorrecto_no_publica_binario(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(instalador, "_descargar", lambda *_argumentos: b"contenido alterado")

    with pytest.raises(ErrorInstalacionGitleaks, match="SHA-256"):
        instalar(tmp_path, sistema="windows", arquitectura="x86_64")

    _afirmar_sin_publicacion(tmp_path, "gitleaks.exe")


@pytest.mark.parametrize("ruta", ["../gitleaks.exe", "/gitleaks.exe", "C:\\gitleaks.exe"])
def test_rechaza_ruta_fuera_del_destino(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    ruta: str,
) -> None:
    datos = _crear_zip([(ruta, b"binario", stat.S_IFREG | 0o755)])
    _inyectar_archivo(monkeypatch, datos, "gitleaks_8.30.1_windows_x64.zip")

    with pytest.raises(ErrorInstalacionGitleaks, match="ruta"):
        instalar(tmp_path, sistema="windows", arquitectura="x86_64")

    _afirmar_sin_publicacion(tmp_path, "gitleaks.exe")


def test_rechaza_zip_con_mas_de_un_ejecutable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    datos = _crear_zip(
        [
            ("gitleaks.exe", b"gitleaks", stat.S_IFREG | 0o755),
            ("auxiliar.exe", b"auxiliar", stat.S_IFREG | 0o755),
        ]
    )
    _inyectar_archivo(monkeypatch, datos, "gitleaks_8.30.1_windows_x64.zip")

    with pytest.raises(ErrorInstalacionGitleaks, match="un solo ejecutable"):
        instalar(tmp_path, sistema="windows", arquitectura="x86_64")

    _afirmar_sin_publicacion(tmp_path, "gitleaks.exe")


@pytest.mark.parametrize("tipo", [tarfile.SYMTYPE, tarfile.LNKTYPE])
def test_rechaza_symlink_y_hardlink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tipo: bytes,
) -> None:
    datos = _crear_tar(
        [
            ("gitleaks", b"binario", tarfile.REGTYPE, 0o755, ""),
            ("enlace", b"", tipo, 0o777, "gitleaks"),
        ]
    )
    _inyectar_archivo(monkeypatch, datos, "gitleaks_8.30.1_linux_x64.tar.gz")

    with pytest.raises(ErrorInstalacionGitleaks, match="archivo regular"):
        instalar(tmp_path, sistema="linux", arquitectura="x86_64")

    _afirmar_sin_publicacion(tmp_path, "gitleaks")


def test_rechaza_dispositivo_tar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    datos = _crear_tar(
        [
            ("gitleaks", b"binario", tarfile.REGTYPE, 0o755, ""),
            ("dispositivo", b"", tarfile.CHRTYPE, 0o600, ""),
        ]
    )
    _inyectar_archivo(monkeypatch, datos, "gitleaks_8.30.1_linux_x64.tar.gz")

    with pytest.raises(ErrorInstalacionGitleaks, match="archivo regular"):
        instalar(tmp_path, sistema="linux", arquitectura="x86_64")

    _afirmar_sin_publicacion(tmp_path, "gitleaks")


def test_aplica_permisos_posix_al_temporal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    datos = _crear_tar([("gitleaks", b"nuevo", tarfile.REGTYPE, 0o755, "")])
    _inyectar_archivo(monkeypatch, datos, "gitleaks_8.30.1_linux_x64.tar.gz")
    permisos: list[tuple[Path, int]] = []

    def registrar_permisos(ruta: str | bytes | os.PathLike[str], modo: int) -> None:
        permisos.append((Path(ruta), modo))

    monkeypatch.setattr(instalador.os, "chmod", registrar_permisos)

    publicado = instalar(tmp_path, sistema="linux", arquitectura="x86_64")

    assert publicado.read_bytes() == b"nuevo"
    assert len(permisos) == 1
    ruta_temporal, modo = permisos[0]
    assert ruta_temporal.parent == tmp_path
    assert ruta_temporal != publicado
    assert modo == 0o755


def test_tar_inspecciona_cabeceras_incrementalmente_y_reabre_para_copiar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    datos = _crear_tar(
        [
            ("gitleaks", b"binario", tarfile.REGTYPE, 0o755, ""),
            ("LICENSE", b"licencia", tarfile.REGTYPE, 0o644, ""),
        ]
    )
    _inyectar_archivo(monkeypatch, datos, "gitleaks_8.30.1_linux_x64.tar.gz")
    abrir_real = tarfile.open
    modos: list[str | None] = []

    def abrir_incremental(*argumentos, **opciones):
        modos.append(opciones.get("mode"))
        return abrir_real(*argumentos, **opciones)

    def prohibir_getmembers(_archivo):
        pytest.fail("la inspección TAR no debe materializar todos los miembros")

    monkeypatch.setattr(instalador.tarfile, "open", abrir_incremental)
    monkeypatch.setattr(instalador.tarfile.TarFile, "getmembers", prohibir_getmembers)

    publicado = instalar(tmp_path, sistema="linux", arquitectura="x86_64")

    assert publicado.read_bytes() == b"binario"
    assert modos == ["r|gz", "r|gz"]


def test_sustituye_version_anterior_con_replace_atomico(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    datos = _crear_zip([("gitleaks.exe", b"nuevo", stat.S_IFREG | 0o755)])
    _inyectar_archivo(monkeypatch, datos, "gitleaks_8.30.1_windows_x64.zip")
    anterior = tmp_path / "gitleaks.exe"
    anterior.write_bytes(b"anterior")
    reemplazar_real = os.replace
    publicaciones: list[tuple[Path, Path]] = []

    def reemplazar(origen: str | bytes | os.PathLike[str], destino: str | bytes | os.PathLike[str]):
        publicaciones.append((Path(origen), Path(destino)))
        return reemplazar_real(origen, destino)

    monkeypatch.setattr(instalador.os, "replace", reemplazar)

    publicado = instalar(tmp_path, sistema="windows", arquitectura="x86_64")

    assert publicado == anterior.resolve()
    assert anterior.read_bytes() == b"nuevo"
    assert len(publicaciones) == 1
    temporal, destino = publicaciones[0]
    assert temporal.parent == tmp_path
    assert destino == anterior
    assert not temporal.exists()


def test_escribe_por_descriptor_privado_sin_reabrir_temporal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    datos = _crear_zip([("gitleaks.exe", b"nuevo", stat.S_IFREG | 0o755)])
    _inyectar_archivo(monkeypatch, datos, "gitleaks_8.30.1_windows_x64.zip")
    abrir_real = Path.open

    def abrir_controlado(ruta: Path, *argumentos, **opciones):
        if ruta.name.startswith(".gitleaks-"):
            pytest.fail("el temporal privado no debe reabrirse por nombre")
        return abrir_real(ruta, *argumentos, **opciones)

    monkeypatch.setattr(Path, "open", abrir_controlado)

    publicado = instalar(tmp_path, sistema="windows", arquitectura="x86_64")

    assert publicado.read_bytes() == b"nuevo"


@pytest.mark.parametrize("formato", ["zip", "tar"])
@pytest.mark.parametrize(
    ("caso", "mensaje"),
    [
        ("miembro", "128 MiB"),
        ("total", "160 MiB"),
        ("cantidad", "64 miembros"),
    ],
)
def test_limites_de_archivo_fallan_antes_de_publicar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    formato: str,
    caso: str,
    mensaje: str,
) -> None:
    if formato == "zip":
        datos = _crear_zip_con_limite(caso)
        nombre = "gitleaks_8.30.1_windows_x64.zip"
        sistema = "windows"
        ejecutable = "gitleaks.exe"
    else:
        datos = _crear_tar_con_limite(caso)
        nombre = "gitleaks_8.30.1_linux_x64.tar.gz"
        sistema = "linux"
        ejecutable = "gitleaks"
    _inyectar_archivo(monkeypatch, datos, nombre)

    with pytest.raises(ErrorInstalacionGitleaks, match=mensaje):
        instalar(tmp_path, sistema=sistema, arquitectura="x86_64")

    _afirmar_sin_publicacion(tmp_path, ejecutable)


def test_recuenta_bytes_reales_de_cabecera_mentirosa(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    datos = _crear_zip(
        [
            ("documento.txt", b"x", stat.S_IFREG | 0o644),
            ("gitleaks.exe", b"binario", stat.S_IFREG | 0o755),
        ]
    )
    _inyectar_archivo(monkeypatch, datos, "gitleaks_8.30.1_windows_x64.zip")
    abrir_real = zipfile.ZipFile.open

    def abrir_con_contenido_extra(
        archivo: zipfile.ZipFile,
        miembro,
        *argumentos,
        **opciones,
    ):
        nombre = miembro.filename if isinstance(miembro, zipfile.ZipInfo) else str(miembro)
        if nombre == "documento.txt":
            return io.BytesIO(b"contenido real mayor")
        return abrir_real(archivo, miembro, *argumentos, **opciones)

    monkeypatch.setattr(instalador, "MAXIMO_BYTES_MIEMBRO", 8)
    monkeypatch.setattr(instalador.zipfile.ZipFile, "open", abrir_con_contenido_extra)

    with pytest.raises(ErrorInstalacionGitleaks, match="128 MiB"):
        instalar(tmp_path, sistema="windows", arquitectura="x86_64")

    _afirmar_sin_publicacion(tmp_path, "gitleaks.exe")


def test_descarga_usa_timeout_y_rechaza_content_length_excesivo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llamadas: list[tuple[str, int]] = []

    class Respuesta:
        headers = {"Content-Length": str(instalador.MAXIMO_BYTES_DESCARGA + 1)}

        def __enter__(self):
            return self

        def __exit__(self, *_argumentos):
            return False

        def read(self, _tamano: int = -1) -> bytes:
            pytest.fail("no debe leer una respuesta cuyo tamaño declarado excede el máximo")

    def abrir(url: str, timeout: int):
        llamadas.append((url, timeout))
        return Respuesta()

    monkeypatch.setattr(instalador.urllib.request, "urlopen", abrir)

    with pytest.raises(ErrorInstalacionGitleaks, match="32 MiB"):
        instalador._descargar("https://ejemplo.invalid/gitleaks.zip")

    assert llamadas == [("https://ejemplo.invalid/gitleaks.zip", 30)]


def test_descarga_sin_content_length_recuenta_hasta_el_limite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Respuesta:
        headers: dict[str, str] = {}

        def __init__(self) -> None:
            self.bloques = iter([b"1234", b"5678", b"9"])

        def __enter__(self):
            return self

        def __exit__(self, *_argumentos):
            return False

        def read(self, _tamano: int = -1) -> bytes:
            return next(self.bloques, b"")

    monkeypatch.setattr(instalador, "MAXIMO_BYTES_DESCARGA", 8)
    monkeypatch.setattr(
        instalador.urllib.request,
        "urlopen",
        lambda _url, timeout: Respuesta(),
    )

    with pytest.raises(ErrorInstalacionGitleaks, match="32 MiB"):
        instalador._descargar("https://ejemplo.invalid/gitleaks.zip")


def test_destino_que_es_archivo_falla_antes_de_descargar_y_cli_no_filtra_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    destino = tmp_path / "ocupado"
    destino.write_text("no es un directorio", encoding="utf-8")
    descargas: list[str] = []

    def descargar(url: str) -> bytes:
        descargas.append(url)
        return b"no debe descargarse"

    monkeypatch.setattr(instalador, "_descargar", descargar)

    assert instalador.main(["--destino", str(destino)]) == 1

    captura = capsys.readouterr()
    assert captura.out == ""
    assert "destino" in captura.err
    assert "Traceback" not in captura.err
    assert descargas == []


def test_error_de_filesystem_al_crear_destino_se_normaliza(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destino = (tmp_path / "sin-permiso").resolve()
    crear_real = Path.mkdir

    def crear_controlado(ruta: Path, *argumentos, **opciones):
        if ruta == destino:
            raise PermissionError("acceso denegado")
        return crear_real(ruta, *argumentos, **opciones)

    monkeypatch.setattr(Path, "mkdir", crear_controlado)
    monkeypatch.setattr(
        instalador,
        "_descargar",
        lambda _url: pytest.fail("no debe descargar si el destino no puede crearse"),
    )

    with pytest.raises(ErrorInstalacionGitleaks, match="destino"):
        instalar(destino, sistema="windows", arquitectura="x86_64")


def test_main_imprime_solo_ruta_absoluta(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    publicado = (tmp_path / "gitleaks.exe").resolve()
    monkeypatch.setattr(instalador, "instalar", lambda _destino: publicado)

    assert instalador.main(["--destino", str(tmp_path)]) == 0

    captura = capsys.readouterr()
    assert captura.out == f"{publicado}\n"
    assert captura.err == ""


def test_docstrings_publicas_estan_en_ingles_google() -> None:
    assert versiones_herramientas.__doc__.startswith("Pin")
    assert instalador.__doc__.startswith("Install")
    assert ArtefactoGitleaks.__doc__.startswith("Describe")
    assert ErrorInstalacionGitleaks.__doc__.startswith("Report")

    for funcion in (resolver_artefacto, instalar, instalador.main):
        documento = funcion.__doc__ or ""
        assert "Args:" in documento
        assert "Returns:" in documento
    assert "Raises:" in (resolver_artefacto.__doc__ or "")
    assert "Raises:" in (instalar.__doc__ or "")
