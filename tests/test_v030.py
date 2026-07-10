"""v0.30 (R4): ciclo de vida — upgrade no-destructivo, marcador de versión, botón init en Resumen.

- tramalia upgrade agrega lo nuevo que falte SIN pisar lo existente + registra versión.
- .tramalia/version marca con qué versión se generó/actualizó el repo.
- el botón de init vive en la pestaña Resumen (donde dice "sin inicializar").
"""

import asyncio
import types

import pytest

from tramalia import __version__
from tramalia.cli import commands
from tramalia.core import project
from tramalia.core.detect import enabled_features
from tramalia.core.scaffold import scaffold


def _init(tmp_path):
    scaffold(tmp_path, {
        "project_name": "demo", "stacks": ["python"],
        "features": enabled_features(["python"]),
        "primary_agent": "codex", "reviewer_agent": "claude",
    })
    return tmp_path


# ---------------------------------------------------------------- marcador de versión
def test_version_marker_round_trip(tmp_path):
    assert project.scaffolded_version(tmp_path) is None
    project.set_scaffolded_version(tmp_path, "0.30.0")
    assert project.scaffolded_version(tmp_path) == "0.30.0"


# ---------------------------------------------------------------- upgrade
def test_upgrade_sin_inicializar_falla(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert commands.cmd_upgrade(types.SimpleNamespace()) == 1


def test_upgrade_recrea_lo_que_falta_y_no_pisa(tmp_path, monkeypatch):
    _init(tmp_path)
    # el usuario editó un archivo y borró otro
    arq = tmp_path / "docs" / "ai" / "01-arquitectura.md"
    arq.write_text("MI CONTENIDO EDITADO", encoding="utf-8")
    borrado = tmp_path / "docs" / "ai" / "04-reglas-seguridad.md"
    borrado.unlink()
    assert not borrado.exists()

    monkeypatch.chdir(tmp_path)
    assert commands.cmd_upgrade(types.SimpleNamespace()) == 0

    assert borrado.exists()                                   # lo que faltaba: recreado
    assert arq.read_text(encoding="utf-8") == "MI CONTENIDO EDITADO"  # lo editado: intacto
    assert project.scaffolded_version(tmp_path) == __version__       # versión registrada


def test_upgrade_registra_gitignore(tmp_path, monkeypatch):
    # repo inicializado a mano SIN el bloque de .gitignore (simula repo viejo)
    _init(tmp_path)
    (tmp_path / ".gitignore").unlink(missing_ok=True)
    monkeypatch.chdir(tmp_path)
    commands.cmd_upgrade(types.SimpleNamespace())
    txt = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".tramalia/skills/*/" in txt                       # upgrade dejó el bloque


def test_suggest_fanout_no_revienta(tmp_path):
    commands._suggest_fanout(tmp_path)   # solo imprime; nunca debe lanzar


# ---------------------------------------------------------------- TUI: botón init en Resumen
def test_boton_init_en_resumen(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    from textual.widgets import Button
    monkeypatch.chdir(tmp_path)   # repo VACÍO: sin inicializar
    from tramalia.tui import build_app
    app = build_app()()

    async def run():
        async with app.run_test() as pilot:
            await pilot.pause()
            btn = app.query_one("#btn-init-resumen", Button)
            assert btn.display is True                 # visible cuando falta init
            app._run_init(btn)                         # inicializa desde Resumen
            await pilot.pause()
            assert project.is_initialized(tmp_path)
            assert project.scaffolded_version(tmp_path) == __version__
            assert app.query_one("#btn-init-resumen", Button).display is False  # se oculta

    asyncio.run(run())
