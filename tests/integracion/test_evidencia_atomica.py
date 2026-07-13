from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from tramalia.core.errores import ErrorPersistenciaEvidencia
from tramalia.core.evidencia import _serializar, crear_id_paquete, publicar_paquete

pytestmark = pytest.mark.integracion


def _temporales(base: Path) -> list[Path]:
    if not base.exists():
        return []
    return list(base.glob(".tmp-*"))


def test_paquete_valido_aparece_completo_y_sin_temporales(
    tmp_path: Path,
    metadatos_v1,
) -> None:
    paquete = publicar_paquete(
        tmp_path,
        metadatos_v1,
        {
            "traspaso.md": b"traspaso canonico\n",
            "diagnosticos/resultado.txt": b"ok\n",
        },
    )

    assert paquete.id_paquete == metadatos_v1.id_paquete
    assert (paquete.ruta / "metadatos.json").is_file()
    assert (paquete.ruta / "traspaso.md").read_bytes() == b"traspaso canonico\n"
    assert (paquete.ruta / "diagnosticos" / "resultado.txt").read_bytes() == b"ok\n"
    assert (paquete.ruta / "metadatos.json").read_bytes() == _serializar(metadatos_v1)
    assert {
        ruta.relative_to(paquete.ruta).as_posix()
        for ruta in paquete.ruta.rglob("*")
        if ruta.is_file()
    } == {"metadatos.json", "traspaso.md", "diagnosticos/resultado.txt"}
    assert _temporales(paquete.ruta.parent) == []


def test_unico_replace_publica_staging_ya_completo(
    tmp_path: Path,
    metadatos_v1,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replace_real = os.replace
    destinos: list[Path] = []

    def observar_replace(origen: str | Path, destino: str | Path) -> None:
        staging = Path(origen)
        final = Path(destino)
        assert staging.name.startswith(".tmp-")
        assert not final.exists()
        assert {ruta.name for ruta in staging.iterdir()} == {
            "metadatos.json",
            "salida.txt",
            "traspaso.md",
        }
        destinos.append(final)
        replace_real(staging, final)

    monkeypatch.setattr("tramalia.core.evidencia.os.replace", observar_replace)

    paquete = publicar_paquete(
        tmp_path,
        metadatos_v1,
        {"traspaso.md": b"ok", "salida.txt": b"ok"},
    )

    assert destinos == [paquete.ruta]


def test_fallo_de_rename_no_deja_paquete_final_ni_temporal(
    tmp_path: Path,
    metadatos_v1,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fallar_rename(origen: object, destino: object) -> None:
        raise OSError("inyectado")

    monkeypatch.setattr("tramalia.core.evidencia.os.replace", fallar_rename)

    with pytest.raises(ErrorPersistenciaEvidencia):
        publicar_paquete(tmp_path, metadatos_v1, {"traspaso.md": b"ok"})

    base = tmp_path / ".tramalia" / "evidencia"
    assert _temporales(base) == []
    assert not (base / metadatos_v1.id_paquete).exists()


def test_fallo_intermedio_de_escritura_limpia_staging(
    tmp_path: Path,
    metadatos_v1,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tramalia.core import evidencia

    escribir_real = evidencia._escribir_archivo
    llamadas = 0

    def fallar_segunda_escritura(ruta: Path, contenido: bytes) -> None:
        nonlocal llamadas
        llamadas += 1
        if llamadas == 2:
            raise OSError("disco lleno")
        escribir_real(ruta, contenido)

    monkeypatch.setattr(evidencia, "_escribir_archivo", fallar_segunda_escritura)

    with pytest.raises(ErrorPersistenciaEvidencia):
        publicar_paquete(
            tmp_path,
            metadatos_v1,
            {"traspaso.md": b"ok", "salida.txt": b"parcial"},
        )

    base = tmp_path / ".tramalia" / "evidencia"
    assert _temporales(base) == []
    assert not (base / metadatos_v1.id_paquete).exists()


def test_fallo_de_fsync_limpia_solo_su_staging(
    tmp_path: Path,
    metadatos_v1,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llamadas = 0

    def fallar_fsync(descriptor: int) -> None:
        nonlocal llamadas
        llamadas += 1
        if llamadas == 2:
            raise OSError("fsync inyectado")

    monkeypatch.setattr("tramalia.core.evidencia.os.fsync", fallar_fsync)

    with pytest.raises(ErrorPersistenciaEvidencia):
        publicar_paquete(
            tmp_path,
            metadatos_v1,
            {"traspaso.md": b"ok", "salida.txt": b"ok"},
        )

    base = tmp_path / ".tramalia" / "evidencia"
    assert llamadas == 2
    assert _temporales(base) == []


def test_dos_publicaciones_simultaneas_del_mismo_instante_son_distintas(
    tmp_path: Path,
    metadatos_v1,
) -> None:
    instante = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)

    def publicar(indice: int):
        metadatos = replace(
            metadatos_v1,
            id_paquete=crear_id_paquete(instante),
            inicio_utc=instante,
            fin_utc=instante,
        )
        return publicar_paquete(
            tmp_path,
            metadatos,
            {"traspaso.md": f"paquete {indice}\n".encode()},
        )

    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        paquetes = list(ejecutor.map(publicar, range(2)))

    assert paquetes[0].id_paquete != paquetes[1].id_paquete
    assert all(paquete.ruta.is_dir() for paquete in paquetes)
    assert not list((tmp_path / ".tramalia" / "evidencia").glob(".tmp-*"))


def test_ruta_resuelta_permanece_bajo_evidencia(
    tmp_path: Path,
    metadatos_v1,
) -> None:
    paquete = publicar_paquete(tmp_path, metadatos_v1, {"traspaso.md": b"ok"})
    base = (tmp_path / ".tramalia" / "evidencia").resolve()

    assert paquete.ruta.resolve().is_relative_to(base)


def test_fallo_al_crear_directorio_base_es_error_de_dominio(
    tmp_path: Path,
    metadatos_v1,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    crear_directorio = Path.mkdir

    def fallar(ruta: Path, *argumentos: object, **opciones: object) -> None:
        if ruta.name == "evidencia":
            raise PermissionError("solo lectura")
        crear_directorio(ruta, *argumentos, **opciones)

    monkeypatch.setattr(Path, "mkdir", fallar)

    with pytest.raises(ErrorPersistenciaEvidencia) as capturada:
        publicar_paquete(tmp_path, metadatos_v1, {"traspaso.md": b"ok"})

    assert capturada.value.codigo == "persistencia_evidencia_fallida"


@pytest.mark.parametrize(
    "nombre",
    [
        "",
        ".",
        "../escape.txt",
        "sub/../../escape.txt",
        "sub/../escape.txt",
        "sub/./escape.txt",
        "sub//escape.txt",
        "/tmp/escape.txt",
        "//servidor/recurso/escape.txt",
        r"C:\escape.txt",
        "C:/escape.txt",
        "C:relativo.txt",
        r"\\servidor\recurso\escape.txt",
        r"sub\escape.txt",
        "nul\x00.txt",
        "CON.txt",
        "sub/CON.txt",
        "invalido?.txt",
        "puntofinal.",
        "espaciofinal ",
    ],
)
def test_rutas_internas_no_portables_se_rechazan_sin_escribir(
    tmp_path: Path,
    metadatos_v1,
    nombre: str,
) -> None:
    with pytest.raises(ErrorPersistenciaEvidencia):
        publicar_paquete(
            tmp_path,
            metadatos_v1,
            {"traspaso.md": b"ok", nombre: b"escape"},
        )

    assert not (tmp_path.parent / "escape.txt").exists()
    assert not (tmp_path / ".tramalia" / "evidencia").exists()


@pytest.mark.parametrize(
    ("archivos", "campo"),
    [
        ({"salida.txt": b"sin traspaso"}, "traspaso.md"),
        ({"TRASPASO.MD": b"nombre no canonico"}, "traspaso.md"),
        ({"traspaso.md": b"ok", "metadatos.json": b"falso"}, "metadatos.json"),
        ({"traspaso.md": b"ok", "METADATOS.JSON": b"falso"}, "metadatos.json"),
        ({"traspaso.md": b"ok", "metadatos.json/hija": b"falso"}, "ruta"),
        ({"traspaso.md": "no-bytes"}, "contenido"),
        ({"traspaso.md": b"ok", "salida": b"x", "salida/hija.txt": b"y"}, "ruta"),
        ({"traspaso.md": b"ok", "A.txt": b"x", "a.txt": b"y"}, "ruta"),
    ],
)
def test_mapa_de_archivos_invalido_no_deja_residuos(
    tmp_path: Path,
    metadatos_v1,
    archivos: dict[str, object],
    campo: str,
) -> None:
    with pytest.raises(ErrorPersistenciaEvidencia) as capturada:
        publicar_paquete(tmp_path, metadatos_v1, archivos)  # type: ignore[arg-type]

    assert capturada.value.detalles.get("campo") == campo
    assert not (tmp_path / ".tramalia" / "evidencia").exists()


def test_publicacion_duplicada_no_sobrescribe_el_primer_paquete(
    tmp_path: Path,
    metadatos_v1,
) -> None:
    primero = publicar_paquete(tmp_path, metadatos_v1, {"traspaso.md": b"primero"})

    with pytest.raises(ErrorPersistenciaEvidencia):
        publicar_paquete(tmp_path, metadatos_v1, {"traspaso.md": b"segundo"})

    assert (primero.ruta / "traspaso.md").read_bytes() == b"primero"
    assert _temporales(primero.ruta.parent) == []


@pytest.mark.parametrize("tipo_destino", ["directorio", "archivo"])
def test_destino_preexistente_nunca_se_reemplaza(
    tmp_path: Path,
    metadatos_v1,
    tipo_destino: str,
) -> None:
    base = tmp_path / ".tramalia" / "evidencia"
    base.mkdir(parents=True)
    final = base / metadatos_v1.id_paquete
    if tipo_destino == "directorio":
        final.mkdir()
        (final / "centinela.txt").write_bytes(b"ajeno")
    else:
        final.write_bytes(b"ajeno")

    with pytest.raises(ErrorPersistenciaEvidencia):
        publicar_paquete(tmp_path, metadatos_v1, {"traspaso.md": b"nuevo"})

    centinela = final / "centinela.txt" if final.is_dir() else final
    assert centinela.read_bytes() == b"ajeno"


def test_dos_publicaciones_con_mismo_id_tienen_un_solo_ganador(
    tmp_path: Path,
    metadatos_v1,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    barrera = threading.Barrier(2)
    replace_real = os.replace

    def replace_sincronizado(origen: str | Path, destino: str | Path) -> None:
        barrera.wait(timeout=5)
        replace_real(origen, destino)

    monkeypatch.setattr("tramalia.core.evidencia.os.replace", replace_sincronizado)

    def intentar(contenido: bytes):
        try:
            return publicar_paquete(
                tmp_path,
                metadatos_v1,
                {"traspaso.md": contenido},
            )
        except ErrorPersistenciaEvidencia as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        resultados = list(ejecutor.map(intentar, (b"uno", b"dos")))

    paquetes = [resultado for resultado in resultados if not isinstance(resultado, Exception)]
    errores = [resultado for resultado in resultados if isinstance(resultado, Exception)]
    assert len(paquetes) == len(errores) == 1
    assert (paquetes[0].ruta / "traspaso.md").read_bytes() in {b"uno", b"dos"}
    assert _temporales(paquetes[0].ruta.parent) == []


def test_colision_de_uuid_no_borra_staging_ajeno(
    tmp_path: Path,
    metadatos_v1,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = tmp_path / ".tramalia" / "evidencia"
    base.mkdir(parents=True)
    staging_ajeno = base / f".tmp-{'0' * 32}"
    staging_ajeno.mkdir()
    centinela = staging_ajeno / "centinela.txt"
    centinela.write_bytes(b"ajeno")
    monkeypatch.setattr("tramalia.core.evidencia.uuid.uuid4", lambda: UUID(int=0))

    with pytest.raises(ErrorPersistenciaEvidencia):
        publicar_paquete(tmp_path, metadatos_v1, {"traspaso.md": b"nuevo"})

    assert centinela.read_bytes() == b"ajeno"


def test_metadata_invalida_falla_antes_de_crear_directorios(
    tmp_path: Path,
    metadatos_v1,
) -> None:
    metadatos_invalidos = replace(metadatos_v1, id_paquete="../escape")

    with pytest.raises(ErrorPersistenciaEvidencia):
        publicar_paquete(tmp_path, metadatos_invalidos, {"traspaso.md": b"ok"})

    assert not (tmp_path / ".tramalia" / "evidencia").exists()


@pytest.mark.parametrize(
    "cambios",
    [
        {"id_tarea": "../escape"},
        {"vinculo_traspaso": "otro.md"},
    ],
)
def test_identidad_y_traspaso_invalidos_fallan_antes_de_escribir(
    tmp_path: Path,
    metadatos_v1,
    cambios: dict[str, object],
) -> None:
    with pytest.raises(ErrorPersistenciaEvidencia):
        publicar_paquete(
            tmp_path,
            replace(metadatos_v1, **cambios),
            {"traspaso.md": b"ok"},
        )

    assert not (tmp_path / ".tramalia" / "evidencia").exists()


def test_base_de_evidencia_no_puede_ser_symlink_externo(
    tmp_path: Path,
    metadatos_v1,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    externo = tmp_path / "externo"
    externo.mkdir()
    tramalia = tmp_path / "proyecto" / ".tramalia"
    tramalia.mkdir(parents=True)
    base = tramalia / "evidencia"
    try:
        base.symlink_to(externo, target_is_directory=True)
    except OSError:
        resolver_real = Path.resolve

        def simular_enlace(ruta: Path, *args: object, **kwargs: object) -> Path:
            if ruta == base:
                return externo
            return resolver_real(ruta, *args, **kwargs)

        monkeypatch.setattr(Path, "resolve", simular_enlace)

    with pytest.raises(ErrorPersistenciaEvidencia):
        publicar_paquete(tmp_path / "proyecto", metadatos_v1, {"traspaso.md": b"ok"})

    assert list(externo.iterdir()) == []


def test_directorio_tramalia_no_puede_ser_symlink_externo(
    tmp_path: Path,
    metadatos_v1,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    externo = tmp_path / "externo"
    externo.mkdir()
    enlace = proyecto / ".tramalia"
    try:
        enlace.symlink_to(externo, target_is_directory=True)
    except OSError:
        resolver_real = Path.resolve
        base = enlace / "evidencia"

        def simular_enlace(ruta: Path, *args: object, **kwargs: object) -> Path:
            if ruta == base:
                return externo / "evidencia"
            return resolver_real(ruta, *args, **kwargs)

        monkeypatch.setattr(Path, "resolve", simular_enlace)

    with pytest.raises(ErrorPersistenciaEvidencia):
        publicar_paquete(proyecto, metadatos_v1, {"traspaso.md": b"ok"})

    assert list(externo.rglob("*")) == []


def test_fallo_no_expone_ruta_fuera_del_proyecto(
    tmp_path: Path,
    metadatos_v1,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tramalia.core import evidencia

    def fallar(ruta: Path, contenido: bytes) -> None:
        raise OSError("TOKEN_SUPER_SECRETO")

    monkeypatch.setattr(evidencia, "_escribir_archivo", fallar)

    with pytest.raises(ErrorPersistenciaEvidencia) as capturada:
        publicar_paquete(
            tmp_path,
            metadatos_v1,
            {"traspaso.md": b"ok"},
        )

    representacion = str(capturada.value.como_dict())
    assert "TOKEN_SUPER_SECRETO" not in representacion
    assert _temporales(tmp_path / ".tramalia" / "evidencia") == []
