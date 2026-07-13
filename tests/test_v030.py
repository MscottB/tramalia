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
from tramalia.core.proyecto import inspeccionar_estado_proyecto
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
    agentes = tmp_path / "AGENTS.md"
    agentes_antes = agentes.read_bytes()
    # el usuario editó un archivo y borró otro
    arq = tmp_path / "docs" / "ai" / "01-arquitectura.md"
    arq.write_text("MI CONTENIDO EDITADO", encoding="utf-8")
    borrado = tmp_path / "docs" / "ai" / "04-reglas-seguridad.md"
    borrado.unlink()
    assert not borrado.exists()

    monkeypatch.chdir(tmp_path)
    assert commands.cmd_upgrade(types.SimpleNamespace()) == 0

    assert borrado.exists()  # lo que faltaba: recreado
    assert agentes.read_bytes() == agentes_antes  # faltar versión no adopta AGENTS.md
    assert arq.read_text(encoding="utf-8") == "MI CONTENIDO EDITADO"  # lo editado: intacto
    assert project.scaffolded_version(tmp_path) == __version__  # versión registrada


def test_upgrade_registra_gitignore(tmp_path, monkeypatch):
    # repo inicializado a mano SIN el bloque de .gitignore (simula repo viejo)
    _init(tmp_path)
    (tmp_path / ".gitignore").unlink(missing_ok=True)
    monkeypatch.chdir(tmp_path)
    commands.cmd_upgrade(types.SimpleNamespace())
    txt = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".tramalia/skills/*/" in txt  # upgrade dejó el bloque


def test_upgrade_cli_migra_heredado_sin_pisar_contenido(tmp_path, monkeypatch):
    _init(tmp_path)
    agentes = tmp_path / "AGENTS.md"
    agentes.write_text(
        "# Reglas del equipo\n\nNo tocar legacy/.\nCierre: tramalia close.\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(commands, "_suggest_fanout", lambda raiz: None)

    assert commands.cmd_upgrade(types.SimpleNamespace()) == 0

    texto = agentes.read_text(encoding="utf-8")
    inicio = "<!-- tramalia:gobierno inicio -->"
    fin = "<!-- tramalia:gobierno fin -->"
    assert "No tocar legacy/." in texto
    assert texto.count(inicio) == texto.count(fin) == 1
    assert inspeccionar_estado_proyecto(tmp_path).listo


def test_suggest_fanout_no_revienta(tmp_path):
    commands._suggest_fanout(tmp_path)  # solo imprime; nunca debe lanzar


# ---------------------------------------------------------------- TUI: botón init en Resumen
def test_boton_init_en_resumen(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    from textual.widgets import Button

    monkeypatch.chdir(tmp_path)  # repo VACÍO: sin inicializar
    from tramalia.tui import build_app

    app = build_app()()

    async def run():
        async with app.run_test() as pilot:
            await pilot.pause()
            btn = app.query_one("#btn-init-resumen", Button)
            assert btn.display is True  # visible cuando falta init
            app._run_init(btn)  # inicializa desde Resumen
            await pilot.pause()
            assert inspeccionar_estado_proyecto(tmp_path).listo
            assert project.scaffolded_version(tmp_path) == __version__
            assert app.query_one("#btn-init-resumen", Button).display is False  # se oculta

    asyncio.run(run())


def test_tui_trata_proyecto_parcial_como_no_inicializado(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    from textual.widgets import Button, Input

    from tramalia.core import governance
    from tramalia.tui import build_app

    llamadas = []

    def cierre_prohibido(*args, **kwargs):
        llamadas.append((*args, kwargs))
        raise AssertionError("el cierre no debe ejecutarse")

    (tmp_path / ".tramalia").mkdir()
    monkeypatch.setattr(governance, "close", cierre_prohibido)
    monkeypatch.chdir(tmp_path)
    aplicacion = build_app()()

    async def verificar():
        async with aplicacion.run_test() as piloto:
            await piloto.pause()
            assert aplicacion.query_one("#btn-init-resumen", Button).display is True
            aplicacion.query_one("#in-task", Input).value = "TASK-1"
            aplicacion._start_close(aplicacion.query_one("#btn-close", Button))
            await piloto.pause()
            assert llamadas == []

    asyncio.run(verificar())


def test_tui_cierre_revalida_raiz_capturada_en_worker(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    from textual.widgets import Button, Input

    from tramalia.core import governance
    from tramalia.tui import build_app

    raiz_original = tmp_path / "original"
    raiz_alterna = tmp_path / "alterna"
    raiz_original.mkdir()
    raiz_alterna.mkdir()
    _init(raiz_original)
    _init(raiz_alterna)
    project.set_scaffolded_version(raiz_original, __version__)
    project.set_scaffolded_version(raiz_alterna, __version__)

    cierres = []
    trabajos = []

    def cierre_prohibido(raiz, *args, **kwargs):
        cierres.append(raiz)
        raise AssertionError("el cierre no debe ejecutarse")

    def capturar_worker(trabajo, **kwargs):
        trabajos.append(trabajo)
        return None

    monkeypatch.setattr(governance, "close", cierre_prohibido)
    monkeypatch.chdir(raiz_original)
    aplicacion = build_app()()

    async def verificar():
        async with aplicacion.run_test() as piloto:
            await piloto.pause()
            monkeypatch.setattr(aplicacion, "run_worker", capturar_worker)
            aplicacion.query_one("#in-task", Input).value = "TASK-1"
            aplicacion._start_close(aplicacion.query_one("#btn-close", Button))
            assert len(trabajos) == 1

            (raiz_original / "AGENTS.md").unlink()
            monkeypatch.chdir(raiz_alterna)
            await asyncio.to_thread(trabajos[0])
            await piloto.pause()

            assert cierres == []

    asyncio.run(verificar())
