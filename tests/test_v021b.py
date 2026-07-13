"""v0.21.1: fix — tecla `d` (docs) no debe dejar un panel bloqueado abierto."""

import asyncio

import pytest


def _proyecto(tmp_path):
    from tramalia.core.detect import enabled_features
    from tramalia.core.scaffold import scaffold

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


def test_tecla_d_no_abre_el_panel_del_instalador(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("webbrowser.open", lambda url: True)  # no abrir navegador real
    _proyecto(tmp_path)

    from tramalia.tui import build_app

    app = build_app()()

    async def run():
        async with app.run_test() as pilot:
            await pilot.pause()
            panel = app.query_one("#instalador")
            assert panel.display is False  # estado inicial: oculto
            app.action_open_docs()  # tecla `d` sobre la fila actual
            await pilot.pause()
            # el bug reportado: `d` ponía display=True y nunca se podía cerrar
            assert panel.display is False

    asyncio.run(run())


def test_escape_cierra_paneles_abiertos(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    monkeypatch.chdir(tmp_path)
    _proyecto(tmp_path)

    from tramalia.tui import build_app

    app = build_app()()

    async def run():
        async with app.run_test() as pilot:
            await pilot.pause()
            instalador = app.query_one("#instalador")
            skills_log = app.query_one("#skills-log")
            instalador.display = True  # simula una instalación en curso
            skills_log.display = True  # simula un sync en curso
            app.action_close_panels()  # tecla Escape
            assert instalador.display is False
            assert skills_log.display is False

    asyncio.run(run())
