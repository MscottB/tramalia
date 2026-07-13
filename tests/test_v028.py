"""v0.28 (R2): backend de contexto — detección correcta, ESC, backend no instalado.

- proveedor_disponible usa la misma sonda que doctor (sondear): Serena (efímera vía
  uvx) NO debe salir como ausente — era el bug del ✓/○.
- ESC cierra el panel de backend (antes solo el botón Cancelar).
- Elegir un backend no instalado lo fija igual (es preferencia) con aviso.
"""

import asyncio
import json

import pytest

from tramalia import __version__
from tramalia.core import configuracion
from tramalia.core.detect import enabled_features
from tramalia.core.proveedor_contexto import proveedor_disponible
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
    configuracion.fijar_version_andamiaje(tmp_path, __version__)
    return tmp_path


# ---------------------------------------------------------------- detección
def test_serena_efimera_cuenta_como_instalada(monkeypatch):
    import tramalia.core.integraciones as integraciones_mod

    # serena no está como binario, pero uv sí → corre vía uvx → instalada
    monkeypatch.setattr(integraciones_mod.shutil, "which", lambda c: "uv" if c == "uv" else None)
    monkeypatch.setattr(integraciones_mod, "_instalada_por_uv", lambda c: False)
    monkeypatch.setattr(integraciones_mod, "_instalada_por_go", lambda c: False)
    assert proveedor_disponible("serena") is True


def test_serena_sin_uv_no_esta(monkeypatch):
    import tramalia.core.integraciones as integraciones_mod

    monkeypatch.setattr(integraciones_mod.shutil, "which", lambda c: None)
    monkeypatch.setattr(integraciones_mod, "_instalada_por_uv", lambda c: False)
    monkeypatch.setattr(integraciones_mod, "_instalada_por_go", lambda c: False)
    assert proveedor_disponible("serena") is False


def test_backend_desconocido_no_revienta():
    assert proveedor_disponible("no-existe") is False


# ---------------------------------------------------------------- TUI: ESC
@pytest.mark.interfaz
@pytest.mark.opcional
def test_escape_cierra_panel_proveedor(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    from textual.screen import ModalScreen

    monkeypatch.chdir(tmp_path)
    _init(tmp_path)
    from tramalia.interfaz_terminal import construir_aplicacion

    app = construir_aplicacion()

    async def run():
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            await pilot.press("b")
            await pilot.pause()
            assert isinstance(app.screen, ModalScreen)
            await pilot.press("escape")  # debe cerrarlo (antes no)
            await pilot.pause()
            assert not isinstance(app.screen, ModalScreen)
            assert configuracion.proveedor_contexto(tmp_path) == "serena"

    asyncio.run(run())


# ---------------------------------------------------------------- backend no instalado
@pytest.mark.interfaz
@pytest.mark.opcional
def test_elegir_proveedor_no_instalado_lo_fija_igual(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    from textual.widgets import OptionList

    monkeypatch.chdir(tmp_path)
    _init(tmp_path)
    # simulamos que codegraph NO está instalado
    import tramalia.core.tablero as modulo_tablero

    monkeypatch.setattr(modulo_tablero, "proveedor_disponible", lambda clave: clave != "codegraph")
    from tramalia.interfaz_terminal import construir_aplicacion

    app = construir_aplicacion()

    async def run():
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            await pilot.press("b")
            await pilot.pause()
            opciones = app.screen.query_one(OptionList)
            opciones.highlighted = 1
            opciones.focus()
            await pilot.press("enter")
            await app.workers.wait_for_complete()
            # es una preferencia de proyecto: se persiste aunque no esté instalado
            assert configuracion.proveedor_contexto(tmp_path) == "codegraph"
            data = json.loads((tmp_path / ".tramalia" / "config.json").read_text(encoding="utf-8"))
            assert data["context"]["backend"] == "codegraph"

    asyncio.run(run())
