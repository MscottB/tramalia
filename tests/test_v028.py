"""v0.28 (R2): backend de contexto — detección correcta, ESC, backend no instalado.

- backend_installed usa la misma sonda que doctor (sondear): Serena (efímera vía
  uvx) NO debe salir como ausente — era el bug del ✓/○.
- ESC cierra el panel de backend (antes solo el botón Cancelar).
- Elegir un backend no instalado lo fija igual (es preferencia) con aviso.
"""

import asyncio
import json

import pytest

from tramalia import __version__
from tramalia.core import project
from tramalia.core.context_backend import backend_installed
from tramalia.core.detect import enabled_features
from tramalia.core.scaffold import scaffold


def _init(tmp_path):
    scaffold(
        tmp_path,
        {
            "project_name": "demo",
            "stacks": ["python"],
            "features": enabled_features(["python"]),
            "primary_agent": "codex",
            "reviewer_agent": "claude",
        },
    )
    project.set_scaffolded_version(tmp_path, __version__)
    return tmp_path


# ---------------------------------------------------------------- detección
def test_serena_efimera_cuenta_como_instalada(monkeypatch):
    import tramalia.core.integraciones as integraciones_mod

    # serena no está como binario, pero uv sí → corre vía uvx → instalada
    monkeypatch.setattr(integraciones_mod.shutil, "which", lambda c: "uv" if c == "uv" else None)
    monkeypatch.setattr(integraciones_mod, "_instalada_por_uv", lambda c: False)
    monkeypatch.setattr(integraciones_mod, "_instalada_por_go", lambda c: False)
    assert backend_installed("serena") is True


def test_serena_sin_uv_no_esta(monkeypatch):
    import tramalia.core.integraciones as integraciones_mod

    monkeypatch.setattr(integraciones_mod.shutil, "which", lambda c: None)
    monkeypatch.setattr(integraciones_mod, "_instalada_por_uv", lambda c: False)
    monkeypatch.setattr(integraciones_mod, "_instalada_por_go", lambda c: False)
    assert backend_installed("serena") is False


def test_backend_desconocido_no_revienta():
    assert backend_installed("no-existe") is False


# ---------------------------------------------------------------- TUI: ESC
def test_esc_cierra_panel_backend(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    from textual.screen import ModalScreen

    monkeypatch.chdir(tmp_path)
    _init(tmp_path)
    from tramalia.tui import build_app

    app = build_app()()

    async def run():
        async with app.run_test() as pilot:
            await pilot.pause()
            app.action_context_backend()  # tecla b: abre el modal
            await pilot.pause()
            assert isinstance(app.screen, ModalScreen)
            await pilot.press("escape")  # debe cerrarlo (antes no)
            await pilot.pause()
            assert not isinstance(app.screen, ModalScreen)
            assert project.context_backend(tmp_path) == "serena"  # cancelar no cambia

    asyncio.run(run())


# ---------------------------------------------------------------- backend no instalado
def test_elegir_backend_no_instalado_lo_fija_igual(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    monkeypatch.chdir(tmp_path)
    _init(tmp_path)
    # simulamos que codegraph NO está instalado
    import tramalia.core.context_backend as cb

    monkeypatch.setattr(cb, "backend_installed", lambda k: k != "codegraph")
    from tramalia.tui import build_app

    app = build_app()()

    async def run():
        async with app.run_test() as pilot:
            await pilot.pause()
            app._on_backend_chosen("codegraph")  # no instalado → se fija con aviso
            await pilot.pause()
            # es una preferencia de proyecto: se persiste aunque no esté instalado
            assert project.context_backend(tmp_path) == "codegraph"
            data = json.loads((tmp_path / ".tramalia" / "config.json").read_text(encoding="utf-8"))
            assert data["context"]["backend"] == "codegraph"

    asyncio.run(run())
