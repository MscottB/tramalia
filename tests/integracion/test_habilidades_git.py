import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

from tramalia.core import habilidades
from tramalia.core.errores import ErrorEntradaInsegura
from tramalia.core.procesos import ResultadoProceso

pytestmark = pytest.mark.integracion


def _ejecutar_git(raiz: Path, *argumentos: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(raiz), *argumentos],
        capture_output=True,
        text=True,
        check=False,
    )


_PREFIJO_HTTPS_PRUEBA = "https://git.tramalia.test/"


def _fuente_remoto(remoto: Path) -> str:
    return f"git+{_PREFIJO_HTTPS_PRUEBA}{remoto.name}.git"


@pytest.fixture(autouse=True)
def _mapear_https_local(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ejecutar_real = habilidades._ejecutar_git

    def ejecutar(argumentos, **opciones):
        mapeados = []
        for argumento in argumentos:
            if isinstance(argumento, str) and argumento.startswith(_PREFIJO_HTTPS_PRUEBA):
                nombre = argumento.removeprefix(_PREFIJO_HTTPS_PRUEBA).removesuffix(".git")
                mapeados.append(str(tmp_path / nombre))
            else:
                mapeados.append(argumento)
        return ejecutar_real(mapeados, **opciones)

    monkeypatch.setattr(habilidades, "_ejecutar_git", ejecutar)


def _remoto(tmp_path: Path, nombre: str = "remoto") -> Path:
    remoto = tmp_path / nombre
    remoto.mkdir()
    if _ejecutar_git(remoto, "init", "-b", "main").returncode != 0:
        assert _ejecutar_git(remoto, "init").returncode == 0
        assert _ejecutar_git(remoto, "checkout", "-b", "main").returncode == 0
    (remoto / "SKILL.md").write_text("v1\n", encoding="utf-8")
    assert _ejecutar_git(remoto, "add", "SKILL.md").returncode == 0
    assert (
        _ejecutar_git(
            remoto,
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=Test",
            "commit",
            "-m",
            "v1",
        ).returncode
        == 0
    )
    return remoto


def _proyecto(tmp_path: Path, remoto: Path, *, modo: str = "team") -> Path:
    raiz = tmp_path / "proyecto"
    (raiz / ".tramalia").mkdir(parents=True)
    (raiz / ".tramalia" / "config.json").write_text(json.dumps({"mode": modo}), encoding="utf-8")
    (raiz / ".tramalia" / "habilidades.toml").write_text(
        f'[[habilidad]]\nnombre = "demo"\nfuente = "{_fuente_remoto(remoto)}"\n'
        'referencia = "main"\n',
        encoding="utf-8",
    )
    return raiz


def _proyecto_dos_habilidades(tmp_path: Path, primera: Path, segunda: Path) -> Path:
    raiz = tmp_path / "proyecto"
    directorio = raiz / ".tramalia"
    directorio.mkdir(parents=True)
    (directorio / "config.json").write_text(json.dumps({"mode": "team"}), encoding="utf-8")
    (directorio / "habilidades.toml").write_text(
        f'[[habilidad]]\nnombre = "primera"\nfuente = "{_fuente_remoto(primera)}"\n'
        'referencia = "main"\n\n'
        f'[[habilidad]]\nnombre = "segunda"\nfuente = "{_fuente_remoto(segunda)}"\n'
        'referencia = "main"\n',
        encoding="utf-8",
    )
    return raiz


def _confirmar_version(remoto: Path, version: str) -> None:
    (remoto / "SKILL.md").write_text(f"{version}\n", encoding="utf-8")
    assert _ejecutar_git(remoto, "add", "SKILL.md").returncode == 0
    assert (
        _ejecutar_git(
            remoto,
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=Test",
            "commit",
            "-m",
            version,
        ).returncode
        == 0
    )


def _eliminar_checkout(ruta: Path) -> None:
    def habilitar_escritura(funcion, objetivo, _informacion) -> None:
        os.chmod(objetivo, stat.S_IWRITE)
        funcion(objetivo)

    shutil.rmtree(ruta, onerror=habilitar_escritura)


def test_resolver_sha_normaliza_prefijo_git_sin_cambiar_fuente_canonica(
    tmp_path: Path, monkeypatch
) -> None:
    llamadas: list[tuple[str, ...]] = []

    def ejecutar(argumentos, **_opciones):
        llamadas.append(tuple(argumentos))
        return ResultadoProceso(
            tuple(argumentos),
            0,
            f"{'a' * 40}\trefs/heads/main\n",
            "",
            False,
            False,
        )

    monkeypatch.setattr(habilidades, "_ejecutar_git", ejecutar)
    sha, resultado = habilidades._resolver_sha(
        "git+https://example.com/equipo/habilidad.git", "main", tmp_path
    )

    assert resultado.exitoso
    assert sha == "a" * 40
    assert llamadas == [
        (
            "git",
            "ls-remote",
            "--exit-code",
            "https://example.com/equipo/habilidad.git",
            "main",
        )
    ]


@pytest.mark.skipif(not habilidades.git_disponible(), reason="requiere git")
def test_modo_equipo_rehidrata_sha_fijado_sin_seguir_main(tmp_path: Path) -> None:
    remoto = _remoto(tmp_path)
    raiz = _proyecto(tmp_path, remoto)

    inicial = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    sha_fijado = inicial.resoluciones[0].sha_resuelto
    assert inicial.estado.estado == "completo"
    assert sha_fijado is not None and len(sha_fijado) == 40

    (remoto / "SKILL.md").write_text("v2\n", encoding="utf-8")
    assert _ejecutar_git(remoto, "add", "SKILL.md").returncode == 0
    assert (
        _ejecutar_git(
            remoto,
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=Test",
            "commit",
            "-m",
            "v2",
        ).returncode
        == 0
    )
    destino = raiz / ".tramalia" / "habilidades" / "demo"
    sha_nuevo = _ejecutar_git(remoto, "rev-parse", "HEAD").stdout.strip()
    assert sha_nuevo != sha_fijado
    assert _ejecutar_git(destino, "fetch", "origin", sha_nuevo).returncode == 0
    assert _ejecutar_git(destino, "checkout", "--detach", sha_nuevo).returncode == 0
    assert _ejecutar_git(destino, "rev-parse", "HEAD").stdout.strip() == sha_nuevo

    rehidratado = habilidades.sincronizar_habilidades(raiz)
    assert rehidratado.resoluciones[0].sha_resuelto == sha_fijado
    assert _ejecutar_git(destino, "rev-parse", "HEAD").stdout.strip() == sha_fijado


@pytest.mark.skipif(not habilidades.git_disponible(), reason="requiere git")
def test_modo_equipo_recrea_checkout_ausente_desde_sha_fijado(tmp_path: Path) -> None:
    remoto = _remoto(tmp_path)
    raiz = _proyecto(tmp_path, remoto)
    inicial = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    sha_fijado = inicial.resoluciones[0].sha_resuelto
    ruta_bloqueo = raiz / ".tramalia" / "habilidades.lock.json"
    bloqueo_original = ruta_bloqueo.read_bytes()
    destino = raiz / ".tramalia" / "habilidades" / "demo"

    (remoto / "SKILL.md").write_text("v2\n", encoding="utf-8")
    assert _ejecutar_git(remoto, "add", "SKILL.md").returncode == 0
    assert (
        _ejecutar_git(
            remoto,
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=Test",
            "commit",
            "-m",
            "v2",
        ).returncode
        == 0
    )
    sha_nuevo = _ejecutar_git(remoto, "rev-parse", "HEAD").stdout.strip()
    assert sha_nuevo != sha_fijado

    # Simula un clon fresco del proyecto: se conserva el lock, no el checkout externo.
    _eliminar_checkout(destino)
    rehidratado = habilidades.sincronizar_habilidades(raiz)

    assert rehidratado.estado.estado == "completo"
    assert rehidratado.resoluciones[0].sha_resuelto == sha_fijado
    assert _ejecutar_git(destino, "rev-parse", "HEAD").stdout.strip() == sha_fijado
    assert ruta_bloqueo.read_bytes() == bloqueo_original


@pytest.mark.skipif(not habilidades.git_disponible(), reason="requiere git")
def test_actualizacion_explicita_mueve_el_bloqueo(tmp_path: Path) -> None:
    remoto = _remoto(tmp_path)
    raiz = _proyecto(tmp_path, remoto)
    anterior = (
        habilidades.sincronizar_habilidades(raiz, actualizar=True).resoluciones[0].sha_resuelto
    )
    (remoto / "SKILL.md").write_text("v2\n", encoding="utf-8")
    _ejecutar_git(remoto, "add", "SKILL.md")
    _ejecutar_git(
        remoto,
        "-c",
        "user.email=test@example.com",
        "-c",
        "user.name=Test",
        "commit",
        "-m",
        "v2",
    )

    actualizado = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    nuevo = actualizado.resoluciones[0].sha_resuelto
    bloqueo = json.loads((raiz / ".tramalia" / "habilidades.lock.json").read_text(encoding="utf-8"))
    assert nuevo != anterior
    assert bloqueo["habilidades"]["demo"] == {
        "fuente": _fuente_remoto(remoto),
        "referencia": "main",
        "sha_resuelto": nuevo,
    }


@pytest.mark.skipif(not habilidades.git_disponible(), reason="requiere git")
def test_fallo_segunda_publicacion_revierte_habilidades_y_lock_byte_a_byte(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    primera = _remoto(tmp_path, "remoto-primera")
    segunda = _remoto(tmp_path, "remoto-segunda")
    raiz = _proyecto_dos_habilidades(tmp_path, primera, segunda)
    inicial = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    assert inicial.estado.estado == "completo"
    destinos = {
        nombre: raiz / ".tramalia" / "habilidades" / nombre for nombre in ("primera", "segunda")
    }
    shas_anteriores = {
        nombre: _ejecutar_git(destino, "rev-parse", "HEAD").stdout.strip()
        for nombre, destino in destinos.items()
    }
    contenidos_anteriores = {
        nombre: (destino / "SKILL.md").read_bytes() for nombre, destino in destinos.items()
    }
    ruta_bloqueo = raiz / ".tramalia" / "habilidades.lock.json"
    bloqueo_anterior = ruta_bloqueo.read_bytes()
    _confirmar_version(primera, "v2")
    _confirmar_version(segunda, "v2")

    reemplazar_real = Path.replace
    publicaciones = 0

    def reemplazar(origen: Path, destino: Path) -> Path:
        nonlocal publicaciones
        origen = Path(origen)
        destino = Path(destino)
        if ".cuarentena-habilidades" in origen.parts and destino.parent.name == "habilidades":
            publicaciones += 1
            if publicaciones == 2:
                raise OSError("fallo Windows simulado al publicar segunda habilidad")
        return reemplazar_real(origen, destino)

    monkeypatch.setattr(Path, "replace", reemplazar)

    resultado = habilidades.sincronizar_habilidades(raiz, actualizar=True)

    assert resultado.estado.estado == "fallido"
    assert publicaciones == 2
    for nombre, destino in destinos.items():
        assert _ejecutar_git(destino, "rev-parse", "HEAD").stdout.strip() == shas_anteriores[nombre]
        assert (destino / "SKILL.md").read_bytes() == contenidos_anteriores[nombre]
    assert ruta_bloqueo.read_bytes() == bloqueo_anterior
    assert not (raiz / ".tramalia" / ".cuarentena-habilidades").exists()
    assert not list((raiz / ".tramalia" / "habilidades").glob("*.respaldo-*"))


@pytest.mark.skipif(not habilidades.git_disponible(), reason="requiere git")
def test_interrupcion_despues_de_staging_no_hace_visible_contenido_no_validado(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    remoto = _remoto(tmp_path)
    raiz = _proyecto(tmp_path, remoto)
    inspeccionadas: list[Path] = []

    def interrumpir(ruta: Path):
        inspeccionadas.append(ruta)
        assert ".cuarentena-habilidades" in ruta.parts
        assert (ruta / "SKILL.md").is_file()
        raise ErrorEntradaInsegura(
            "Arbol no validado.",
            "Corrige el contenido de la habilidad.",
        )

    monkeypatch.setattr(habilidades, "validar_arbol_habilidad", interrumpir, raising=False)

    resultado = habilidades.sincronizar_habilidades(raiz, actualizar=True)

    assert resultado.estado.estado == "fallido"
    assert len(inspeccionadas) == 1
    assert not (raiz / ".tramalia" / "habilidades" / "demo").exists()
    assert not (raiz / ".tramalia" / ".cuarentena-habilidades").exists()


def test_clonacion_no_cero_es_fallida_y_no_escribe_bloqueo(tmp_path: Path, monkeypatch) -> None:
    raiz = _proyecto(tmp_path, tmp_path / "ausente", modo="local-first")
    monkeypatch.setattr(
        habilidades,
        "_ejecutar_git",
        lambda *_a, **_k: ResultadoProceso(("git", "clone"), 128, "", "fatal: clone", False, False),
    )
    resultado = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    assert resultado.estado.estado == "fallido"
    assert resultado.resoluciones[0].estado.motivo == "git_salida_no_cero"
    assert not (raiz / ".tramalia" / "habilidades.lock.json").exists()


def test_pull_no_cero_no_declara_actualizada(tmp_path: Path, monkeypatch) -> None:
    raiz = _proyecto(tmp_path, tmp_path / "remoto", modo="local-first")
    destino = raiz / ".tramalia" / "habilidades" / "demo" / ".git"
    destino.mkdir(parents=True)
    monkeypatch.setattr(
        habilidades,
        "_ejecutar_git",
        lambda *_a, **_k: ResultadoProceso(
            ("git", "pull"), 1, "", "non-fast-forward", False, False
        ),
    )
    resultado = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    assert resultado.estado.estado == "fallido"
    assert resultado.resoluciones[0].accion == "fallida"


def test_tiempo_agotado_git_es_fallido_explicito(tmp_path: Path, monkeypatch) -> None:
    raiz = _proyecto(tmp_path, tmp_path / "remoto")
    monkeypatch.setattr(
        habilidades,
        "_ejecutar_git",
        lambda *_a, **_k: ResultadoProceso(("git", "ls-remote"), 124, "", "", True, False),
    )
    resultado = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    assert resultado.estado.estado == "fallido"
    assert resultado.resoluciones[0].estado.motivo == "git_tiempo_agotado"


@pytest.mark.parametrize(
    ("codigo_salida", "salida", "motivo"),
    [
        (2, "", "referencia_no_resuelta"),
        (7, "", "git_salida_no_cero"),
        (0, "referencia sin sha\n", "sha_no_verificado"),
    ],
)
def test_clasificacion_ls_remote_respeta_orden_y_sha_verificable(
    tmp_path: Path,
    monkeypatch,
    codigo_salida: int,
    salida: str,
    motivo: str,
) -> None:
    raiz = _proyecto(tmp_path, tmp_path / "remoto")
    monkeypatch.setattr(
        habilidades,
        "_ejecutar_git",
        lambda *_a, **_k: ResultadoProceso(
            ("git", "ls-remote", "--exit-code"),
            codigo_salida,
            salida,
            "fallo simulado",
            False,
            False,
        ),
    )

    resultado = habilidades.sincronizar_habilidades(raiz, actualizar=True)

    assert resultado.estado.estado == "fallido"
    assert resultado.resoluciones[0].estado.motivo == motivo


def test_latest_se_rechaza_sin_invocar_git(tmp_path: Path, monkeypatch) -> None:
    raiz = _proyecto(tmp_path, tmp_path / "remoto")
    manifiesto = raiz / ".tramalia" / "habilidades.toml"
    manifiesto.write_text(
        manifiesto.read_text(encoding="utf-8").replace("main", "latest"),
        encoding="utf-8",
    )
    llamadas: list[tuple[str, ...]] = []

    def ejecutar(argumentos, **_opciones):
        llamadas.append(tuple(argumentos))
        return ResultadoProceso(tuple(argumentos), 0, "", "", False, False)

    monkeypatch.setattr(habilidades, "_ejecutar_git", ejecutar)

    resultado = habilidades.sincronizar_habilidades(raiz, actualizar=True)

    assert resultado.estado.estado == "fallido"
    assert resultado.resoluciones[0].estado.motivo == "referencia_no_resuelta"
    assert llamadas == []


@pytest.mark.skipif(not habilidades.git_disponible(), reason="requiere git")
def test_fallo_de_actualizacion_conserva_bloqueo_anterior_byte_a_byte(
    tmp_path: Path,
) -> None:
    remoto = _remoto(tmp_path)
    raiz = _proyecto(tmp_path, remoto)
    inicial = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    assert inicial.estado.estado == "completo"
    ruta_bloqueo = raiz / ".tramalia" / "habilidades.lock.json"
    bloqueo_anterior = ruta_bloqueo.read_bytes()
    manifiesto = raiz / ".tramalia" / "habilidades.toml"
    manifiesto.write_text(
        manifiesto.read_text(encoding="utf-8").replace("main", "no-existe"),
        encoding="utf-8",
    )

    resultado = habilidades.sincronizar_habilidades(raiz, actualizar=True)

    assert resultado.estado.estado == "fallido"
    assert ruta_bloqueo.read_bytes() == bloqueo_anterior


@pytest.mark.skipif(not habilidades.git_disponible(), reason="requiere git")
def test_sync_team_no_mueve_lock_si_manifiesto_cambia_referencia(
    tmp_path: Path, monkeypatch
) -> None:
    remoto = _remoto(tmp_path)
    raiz = _proyecto(tmp_path, remoto)
    inicial = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    assert inicial.estado.estado == "completo"
    assert _ejecutar_git(remoto, "branch", "otra").returncode == 0
    ruta_bloqueo = raiz / ".tramalia" / "habilidades.lock.json"
    bloqueo_anterior = ruta_bloqueo.read_bytes()
    manifiesto = raiz / ".tramalia" / "habilidades.toml"
    manifiesto.write_text(
        manifiesto.read_text(encoding="utf-8").replace("main", "otra"),
        encoding="utf-8",
    )
    ejecutar_real = habilidades._ejecutar_git
    llamadas: list[tuple[str, ...]] = []

    def ejecutar(argumentos, **opciones):
        llamadas.append(tuple(argumentos))
        return ejecutar_real(argumentos, **opciones)

    monkeypatch.setattr(habilidades, "_ejecutar_git", ejecutar)

    resultado = habilidades.sincronizar_habilidades(raiz)

    assert resultado.estado.estado == "fallido"
    assert resultado.resoluciones[0].estado.motivo == "bloqueo_desalineado"
    assert llamadas == []
    assert ruta_bloqueo.read_bytes() == bloqueo_anterior


def test_preflight_team_detecta_segundo_bloqueo_desalineado_sin_invocar_git(
    tmp_path: Path, monkeypatch
) -> None:
    raiz = tmp_path / "proyecto"
    directorio_tramalia = raiz / ".tramalia"
    directorio_tramalia.mkdir(parents=True)
    (directorio_tramalia / "config.json").write_text(json.dumps({"mode": "team"}), encoding="utf-8")
    fuente_primera = "git+https://example.com/equipo/primera.git"
    fuente_segunda = "git+https://example.com/equipo/segunda.git"
    (directorio_tramalia / "habilidades.toml").write_text(
        f'[[habilidad]]\nnombre = "primera"\nfuente = "{fuente_primera}"\n'
        'referencia = "main"\n\n'
        f'[[habilidad]]\nnombre = "segunda"\nfuente = "{fuente_segunda}"\n'
        'referencia = "otra"\n',
        encoding="utf-8",
    )
    ruta_bloqueo = directorio_tramalia / "habilidades.lock.json"
    ruta_bloqueo.write_text(
        json.dumps(
            {
                "version_esquema": 1,
                "habilidades": {
                    "primera": {
                        "fuente": fuente_primera,
                        "referencia": "main",
                        "sha_resuelto": "a" * 40,
                    },
                    "segunda": {
                        "fuente": fuente_segunda,
                        "referencia": "main",
                        "sha_resuelto": "b" * 40,
                    },
                },
            },
            indent=3,
        )
        + "\n",
        encoding="utf-8",
    )
    bloqueo_anterior = ruta_bloqueo.read_bytes()
    llamadas: list[tuple[str, ...]] = []

    def ejecutar(argumentos, **_opciones):
        llamadas.append(tuple(argumentos))
        return ResultadoProceso(tuple(argumentos), 1, "", "Git no debe ejecutarse")

    monkeypatch.setattr(habilidades, "git_disponible", lambda: True)
    monkeypatch.setattr(habilidades, "_ejecutar_git", ejecutar)

    resultado = habilidades.sincronizar_habilidades(raiz)

    assert resultado.estado.estado == "fallido"
    assert any(
        resolucion.nombre == "segunda" and resolucion.estado.motivo == "bloqueo_desalineado"
        for resolucion in resultado.resoluciones
    )
    assert llamadas == []
    assert ruta_bloqueo.read_bytes() == bloqueo_anterior


@pytest.mark.skipif(not habilidades.git_disponible(), reason="requiere git")
def test_consulta_remota_fallida_conserva_sha_local(tmp_path: Path, monkeypatch) -> None:
    remoto = _remoto(tmp_path)
    raiz = _proyecto(tmp_path, remoto)
    sincronizacion = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    sha_local = sincronizacion.resoluciones[0].sha_resuelto
    ejecutar_real = habilidades._ejecutar_git

    def ejecutar(argumentos, **opciones):
        if tuple(argumentos[:2]) == ("git", "ls-remote"):
            return ResultadoProceso(tuple(argumentos), 128, "", "remoto inaccesible", False, False)
        return ejecutar_real(argumentos, **opciones)

    monkeypatch.setattr(habilidades, "_ejecutar_git", ejecutar)

    resolucion = habilidades.consultar_habilidades(raiz, consultar_remoto=True)[0]

    assert sha_local is not None
    assert resolucion.sha_resuelto == sha_local
    assert resolucion.accion == "fallida"
    assert resolucion.estado.estado == "fallido"
    assert resolucion.estado.motivo == "git_salida_no_cero"


def test_consulta_local_sin_git_es_no_disponible_y_no_invoca_proceso(
    tmp_path: Path, monkeypatch
) -> None:
    raiz = _proyecto(tmp_path, tmp_path / "remoto")
    (raiz / ".tramalia" / "habilidades" / "demo").mkdir(parents=True)
    llamadas: list[tuple[str, ...]] = []

    def ejecutar(argumentos, **_opciones):
        llamadas.append(tuple(argumentos))
        return ResultadoProceso(tuple(argumentos), 127, "", "git ausente")

    monkeypatch.setattr(habilidades, "git_disponible", lambda: False)
    monkeypatch.setattr(habilidades, "_ejecutar_git", ejecutar)

    resolucion = habilidades.consultar_habilidades(raiz, consultar_remoto=True)[0]

    assert resolucion.accion == "sin_cambios"
    assert resolucion.estado.estado == "no_disponible"
    assert resolucion.estado.motivo == "git_no_instalado"
    assert "Instala Git" in resolucion.estado.remediacion
    assert llamadas == []


def test_consulta_local_checkout_corrupto_es_fallida(tmp_path: Path, monkeypatch) -> None:
    raiz = _proyecto(tmp_path, tmp_path / "remoto")
    (raiz / ".tramalia" / "habilidades" / "demo" / ".git").mkdir(parents=True)
    monkeypatch.setattr(habilidades, "git_disponible", lambda: True)
    monkeypatch.setattr(
        habilidades,
        "_ejecutar_git",
        lambda argumentos, **_opciones: ResultadoProceso(
            tuple(argumentos), 128, "", "checkout corrupto"
        ),
    )

    resolucion = habilidades.consultar_habilidades(raiz)[0]

    assert resolucion.sha_resuelto is None
    assert resolucion.accion == "fallida"
    assert resolucion.estado.estado == "fallido"
    assert resolucion.estado.motivo == "git_salida_no_cero"


@pytest.mark.skipif(not habilidades.git_disponible(), reason="requiere git")
def test_modo_equipo_no_usa_pull_ni_resuelve_referencia_con_lock(
    tmp_path: Path, monkeypatch
) -> None:
    remoto = _remoto(tmp_path)
    raiz = _proyecto(tmp_path, remoto)
    inicial = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    assert inicial.estado.estado == "completo"
    ejecutar_real = habilidades._ejecutar_git
    llamadas: list[tuple[str, ...]] = []

    def ejecutar(argumentos, **opciones):
        llamadas.append(tuple(argumentos))
        return ejecutar_real(argumentos, **opciones)

    monkeypatch.setattr(habilidades, "_ejecutar_git", ejecutar)

    resultado = habilidades.sincronizar_habilidades(raiz)

    assert resultado.estado.estado == "completo"
    assert all("pull" not in llamada for llamada in llamadas)
    assert all("ls-remote" not in llamada for llamada in llamadas)
    assert any("--detach" in llamada for llamada in llamadas)


@pytest.mark.skipif(not habilidades.git_disponible(), reason="requiere git")
def test_bloqueo_se_publica_mediante_replace_de_temporal_hermano(
    tmp_path: Path, monkeypatch
) -> None:
    remoto = _remoto(tmp_path)
    raiz = _proyecto(tmp_path, remoto)
    reemplazar_real = Path.replace
    publicaciones: list[tuple[Path, Path]] = []

    def reemplazar(origen: Path, destino: Path) -> Path:
        destino = Path(destino)
        if destino.name == "habilidades.lock.json":
            publicaciones.append((origen, destino))
        return reemplazar_real(origen, destino)

    monkeypatch.setattr(Path, "replace", reemplazar)

    resultado = habilidades.sincronizar_habilidades(raiz, actualizar=True)

    assert resultado.estado.estado == "completo"
    assert len(publicaciones) == 1
    temporal, destino = publicaciones[0]
    assert temporal.parent == destino.parent
    assert ".tmp-" in temporal.name
    assert not temporal.exists()


@pytest.mark.skipif(not habilidades.git_disponible(), reason="requiere git")
def test_referencia_invalida_no_mueve_bloqueo(tmp_path: Path) -> None:
    remoto = _remoto(tmp_path)
    raiz = _proyecto(tmp_path, remoto)
    manifiesto = raiz / ".tramalia" / "habilidades.toml"
    manifiesto.write_text(
        manifiesto.read_text(encoding="utf-8").replace("main", "no-existe"),
        encoding="utf-8",
    )
    resultado = habilidades.sincronizar_habilidades(raiz, actualizar=True)
    assert resultado.estado.estado == "fallido"
    assert resultado.resoluciones[0].estado.motivo == "referencia_no_resuelta"
    assert not (raiz / ".tramalia" / "habilidades.lock.json").exists()
