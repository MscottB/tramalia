"""v0.31: identidad instalada y actualización disponible de habilidades externas."""

import json
import shutil
import subprocess
import types

import pytest

from tramalia.core import habilidades
from tramalia.core.procesos import ResultadoProceso


def _ejecutar_git(raiz, *argumentos):
    return subprocess.run(
        ["git", "-C", str(raiz), *argumentos],
        capture_output=True,
        text=True,
        check=False,
    )


def _confirmar(raiz, mensaje):
    _ejecutar_git(
        raiz,
        "-c",
        "user.email=t@t.co",
        "-c",
        "user.name=t",
        "commit",
        "-m",
        mensaje,
    )


def _crear_remoto(tmp_path):
    remoto = tmp_path / "habilidad-remota"
    remoto.mkdir()
    resultado = _ejecutar_git(remoto, "init", "-b", "main")
    if resultado.returncode != 0:
        _ejecutar_git(remoto, "init")
        _ejecutar_git(remoto, "checkout", "-b", "main")
    (remoto / "SKILL.md").write_text("v1", encoding="utf-8")
    _ejecutar_git(remoto, "add", "-A")
    _confirmar(remoto, "v1")
    return remoto


def _proyecto_con_habilidad(tmp_path, remoto):
    proyecto = tmp_path / "proyecto"
    (proyecto / ".tramalia").mkdir(parents=True)
    (proyecto / ".tramalia" / "habilidades.toml").write_text(
        f'[[habilidad]]\nnombre = "mihabilidad"\nfuente = "{remoto.as_uri()}"\n'
        'referencia = "main"\n',
        encoding="utf-8",
    )
    return proyecto


def _esta_git_disponible():
    return shutil.which("git") is not None


pytestmark = pytest.mark.skipif(not _esta_git_disponible(), reason="requiere git")


def test_sincronizar_solo_inexistente_no_hace_nada(tmp_path):
    remoto = _crear_remoto(tmp_path)
    proyecto = _proyecto_con_habilidad(tmp_path, remoto)
    resultado = habilidades.sincronizar_habilidades(proyecto, solo="no-existe")
    assert resultado.resoluciones == ()


def test_sincronizar_solo_clona_esa_habilidad(tmp_path):
    remoto = _crear_remoto(tmp_path)
    proyecto = _proyecto_con_habilidad(tmp_path, remoto)
    resultado = habilidades.sincronizar_habilidades(proyecto, solo="mihabilidad")
    assert resultado.resoluciones[0].accion == "clonada"
    assert (proyecto / ".tramalia" / "habilidades" / "mihabilidad" / "SKILL.md").exists()


def test_referencia_instalada_tras_clonar(tmp_path):
    remoto = _crear_remoto(tmp_path)
    proyecto = _proyecto_con_habilidad(tmp_path, remoto)
    habilidades.sincronizar_habilidades(proyecto)
    referencia = habilidades.referencia_instalada(proyecto, "mihabilidad")
    assert referencia and len(referencia) == 7


def test_referencia_instalada_none_si_no_esta(tmp_path):
    remoto = _crear_remoto(tmp_path)
    proyecto = _proyecto_con_habilidad(tmp_path, remoto)
    assert habilidades.referencia_instalada(proyecto, "mihabilidad") is None


def test_consulta_al_dia_y_luego_actualizable(tmp_path):
    remoto = _crear_remoto(tmp_path)
    proyecto = _proyecto_con_habilidad(tmp_path, remoto)
    habilidades.sincronizar_habilidades(proyecto)

    estado = habilidades.consultar_habilidades(proyecto, consultar_remoto=True)[0]
    assert estado.sha_resuelto
    assert estado.estado.motivo == "sha_instalado_verificado"

    (remoto / "SKILL.md").write_text("v2", encoding="utf-8")
    _ejecutar_git(remoto, "add", "-A")
    _confirmar(remoto, "v2")
    actualizado = habilidades.consultar_habilidades(proyecto, consultar_remoto=True)[0]
    assert actualizado.estado.motivo == "actualizacion_disponible"


def test_consulta_sin_remoto_es_local(tmp_path):
    remoto = _crear_remoto(tmp_path)
    proyecto = _proyecto_con_habilidad(tmp_path, remoto)
    habilidades.sincronizar_habilidades(proyecto)
    estado = habilidades.consultar_habilidades(proyecto)[0]
    assert estado.sha_resuelto is not None
    assert estado.estado.motivo == "sha_instalado_verificado"


def test_cli_habilidades_desactualizadas(tmp_path, monkeypatch):
    remoto = _crear_remoto(tmp_path)
    proyecto = _proyecto_con_habilidad(tmp_path, remoto)
    habilidades.sincronizar_habilidades(proyecto)
    monkeypatch.chdir(proyecto)
    from tramalia.cli import comandos

    argumentos = types.SimpleNamespace(action="outdated", name=None)
    assert comandos.comando_habilidades(argumentos) == 0


def test_cli_habilidades_desactualizadas_renderiza_fallo_remoto_y_devuelve_uno(
    tmp_path, monkeypatch
):
    remoto = _crear_remoto(tmp_path)
    proyecto = _proyecto_con_habilidad(tmp_path, remoto)
    habilidades.sincronizar_habilidades(proyecto)
    monkeypatch.chdir(proyecto)
    monkeypatch.setattr(
        habilidades,
        "_resolver_sha",
        lambda *_argumentos: (
            None,
            ResultadoProceso(("git", "ls-remote"), 128, "", "remoto inaccesible", False, False),
        ),
    )
    from tramalia.cli import comandos

    errores: list[str] = []
    monkeypatch.setattr(comandos.renderizado, "error", errores.append)
    argumentos = types.SimpleNamespace(action="outdated", name=None)

    codigo = comandos.comando_habilidades(argumentos)

    assert codigo == 1
    assert any("mihabilidad" in error and "git_salida_no_cero" in error for error in errores)


def test_tui_habilidades_muestra_fallo_remoto_sin_informar_cero_actualizaciones(
    tmp_path, monkeypatch
):
    pytest.importorskip("textual")
    remoto = _crear_remoto(tmp_path)
    proyecto = _proyecto_con_habilidad(tmp_path, remoto)
    habilidades.sincronizar_habilidades(proyecto)
    monkeypatch.chdir(proyecto)
    monkeypatch.setattr(
        habilidades,
        "_resolver_sha",
        lambda *_argumentos: (
            None,
            ResultadoProceso(("git", "ls-remote"), 128, "", "remoto inaccesible", False, False),
        ),
    )
    resolucion = habilidades.consultar_habilidades(proyecto, consultar_remoto=True)[0]
    from tramalia.i18n import t
    from tramalia.tui import build_app

    mensajes: list[str] = []

    class RegistroMensajes:
        def write(self, mensaje: str) -> None:
            mensajes.append(mensaje)

    aplicacion = build_app()()
    aplicacion._skill_updates = {}
    clase_aplicacion = type(aplicacion)
    monkeypatch.setattr(clase_aplicacion, "_skills_log", lambda _self: RegistroMensajes())
    monkeypatch.setattr(clase_aplicacion, "_refresh_skills", lambda *_argumentos: None)

    aplicacion._after_check_updates((resolucion,))

    assert any("mihabilidad" in mensaje and "git_salida_no_cero" in mensaje for mensaje in mensajes)
    assert t("skills.update.found", n=0) not in mensajes


def test_cli_habilidades_desactualizadas_renderiza_git_ausente_y_devuelve_uno(
    tmp_path, monkeypatch
):
    remoto = _crear_remoto(tmp_path)
    proyecto = _proyecto_con_habilidad(tmp_path, remoto)
    (proyecto / ".tramalia" / "habilidades" / "mihabilidad").mkdir(parents=True)
    monkeypatch.chdir(proyecto)
    monkeypatch.setattr(habilidades, "git_disponible", lambda: False)
    monkeypatch.setattr(
        habilidades,
        "_ejecutar_git",
        lambda argumentos, **_opciones: ResultadoProceso(tuple(argumentos), 127, "", "git ausente"),
    )
    from tramalia.cli import comandos

    errores: list[str] = []
    monkeypatch.setattr(comandos.renderizado, "error", errores.append)
    argumentos = types.SimpleNamespace(action="outdated", name=None)

    codigo = comandos.comando_habilidades(argumentos)

    assert codigo == 1
    assert any(
        "mihabilidad" in error and "git_no_instalado" in error and "Instala Git" in error
        for error in errores
    )


def test_tui_habilidades_muestra_git_ausente_con_remediacion(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    remoto = _crear_remoto(tmp_path)
    proyecto = _proyecto_con_habilidad(tmp_path, remoto)
    (proyecto / ".tramalia" / "habilidades" / "mihabilidad").mkdir(parents=True)
    monkeypatch.chdir(proyecto)
    monkeypatch.setattr(habilidades, "git_disponible", lambda: False)
    monkeypatch.setattr(
        habilidades,
        "_ejecutar_git",
        lambda argumentos, **_opciones: ResultadoProceso(tuple(argumentos), 127, "", "git ausente"),
    )
    resolucion = habilidades.consultar_habilidades(proyecto, consultar_remoto=True)[0]
    from tramalia.i18n import t
    from tramalia.tui import build_app

    mensajes: list[str] = []

    class RegistroMensajes:
        def write(self, mensaje: str) -> None:
            mensajes.append(mensaje)

    aplicacion = build_app()()
    aplicacion._skill_updates = {}
    clase_aplicacion = type(aplicacion)
    monkeypatch.setattr(clase_aplicacion, "_skills_log", lambda _self: RegistroMensajes())
    monkeypatch.setattr(clase_aplicacion, "_refresh_skills", lambda *_argumentos: None)

    aplicacion._after_check_updates((resolucion,))

    assert any(
        "mihabilidad" in mensaje and "git_no_instalado" in mensaje and "Instala Git" in mensaje
        for mensaje in mensajes
    )
    assert t("skills.update.found", n=0) not in mensajes


def test_tui_enter_habilidad_team_ausente_autoriza_fijar_y_materializar(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    remoto = _crear_remoto(tmp_path)
    proyecto = _proyecto_con_habilidad(tmp_path, remoto)
    (proyecto / ".tramalia" / "config.json").write_text(
        json.dumps({"mode": "team"}), encoding="utf-8"
    )
    (proyecto / ".tramalia" / "habilidades.lock.json").write_text(
        json.dumps(
            {
                "version_esquema": 1,
                "habilidades": {
                    "existente": {
                        "fuente": "git+https://example.com/existente.git",
                        "referencia": "main",
                        "sha_resuelto": "a" * 40,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(proyecto)
    from tramalia.tui import build_app

    class RegistroMensajes:
        def write(self, _mensaje: str) -> None:
            return None

    evento = types.SimpleNamespace(
        data_table=types.SimpleNamespace(get_row=lambda _clave: ["mihabilidad"]),
        row_key="mihabilidad",
    )
    llamadas: list[tuple[str, bool]] = []
    aplicacion = build_app()()
    clase_aplicacion = type(aplicacion)

    def sincronizar_una(_self, nombre, actualizar=False):
        llamadas.append((nombre, actualizar))

    def ejecutar_trabajo(_self, trabajo, **_opciones):
        trabajo()

    monkeypatch.setattr(clase_aplicacion, "_skills_log", lambda _self: RegistroMensajes())
    monkeypatch.setattr(clase_aplicacion, "_sync_one_skill", sincronizar_una)
    monkeypatch.setattr(clase_aplicacion, "run_worker", ejecutar_trabajo)

    aplicacion._toggle_skill(evento)

    assert llamadas == [("mihabilidad", True)]


def test_cli_habilidades_sincroniza_una(tmp_path, monkeypatch):
    remoto = _crear_remoto(tmp_path)
    proyecto = _proyecto_con_habilidad(tmp_path, remoto)
    monkeypatch.chdir(proyecto)
    from tramalia.cli import comandos

    argumentos = types.SimpleNamespace(action="sync", name="mihabilidad")
    assert comandos.comando_habilidades(argumentos) == 0
    assert (proyecto / ".tramalia" / "habilidades" / "mihabilidad").exists()
