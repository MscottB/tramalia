"""v0.31: identidad instalada y actualización disponible de habilidades externas."""

import shutil
import subprocess
import types

import pytest

from tramalia.core import habilidades


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
    from tramalia.cli import commands

    argumentos = types.SimpleNamespace(action="outdated", name=None)
    assert commands.cmd_skills(argumentos) == 0


def test_cli_habilidades_sincroniza_una(tmp_path, monkeypatch):
    remoto = _crear_remoto(tmp_path)
    proyecto = _proyecto_con_habilidad(tmp_path, remoto)
    monkeypatch.chdir(proyecto)
    from tramalia.cli import commands

    argumentos = types.SimpleNamespace(action="sync", name="mihabilidad")
    assert commands.cmd_skills(argumentos) == 0
    assert (proyecto / ".tramalia" / "habilidades" / "mihabilidad").exists()
