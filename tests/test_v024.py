"""v0.24: backend de contexto seleccionable, codegraph vía npm, fix antigravity/agy."""

import asyncio
import json

import pytest

from tramalia import __version__
from tramalia.core import installer, project
from tramalia.core.context_backend import BACKENDS, DEFAULT, UTILITIES
from tramalia.core.detect import enabled_features
from tramalia.core.scaffold import scaffold
from tramalia.core.tools import REGISTRY


def _tool(key):
    return next(t for t in REGISTRY if t.key == key)


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


# ---------------------------------------------------------------- registro
def test_codegraph_automatizable_via_npm():
    opts = installer.options_for(_tool("codegraph"))
    npm = next((o for o in opts if o.method == "npm"), None)
    assert npm is not None and npm.auto and npm.requires == "npm"
    assert "@colbymchenry/codegraph" in npm.args[-1]


def test_antigravity_cmd_es_agy_no_antigravity():
    tool = _tool("antigravity")
    assert tool.cmd == "agy"  # el binario real en PATH
    assert tool.key == "antigravity"  # la key no cambia (no rompe otros usos)


def test_antigravity_winget_en_windows_script_manual_en_resto():
    # v0.27: en Windows hay paquete winget oficial (Google.AntigravityCLI) → automatizable;
    # en mac/linux solo el script curl|sh, que nunca se automatiza.
    win = installer.options_for(_tool("antigravity"), os_name="windows")
    assert win[0].method == "winget" and win[0].auto
    for os_name in ("macos", "linux"):
        opts = installer.options_for(_tool("antigravity"), os_name=os_name)
        assert opts and not any(o.auto for o in opts)


def test_ningun_script_pipe_es_automatizado():
    # regla dura intacta: un `curl … | sh` / `irm … | iex` jamás corre automatizado
    for key in ("antigravity", "hermes"):
        for os_name in ("windows", "macos", "linux"):
            for o in installer.options_for(_tool(key), os_name=os_name):
                if any(m in o.display for m in ("|", "curl", "iex")):
                    assert not o.auto


# ---------------------------------------------------------------- context_backend (core)
def test_default_backend_es_serena():
    assert DEFAULT == "serena"
    assert set(BACKENDS) == {"serena", "codegraph", "codebase-memory-mcp", "graphify"}
    # repomix/markitdown son utilidades, no compiten por el backend
    assert set(UTILITIES) == {"repomix", "markitdown"}
    for meta in {**BACKENDS, **UTILITIES}.values():
        assert meta["scope"] and meta["ideal"]  # explicación siempre presente


def test_project_context_backend_default_sin_config(tmp_path):
    assert project.context_backend(tmp_path) == "serena"


def test_project_context_backend_lee_config(tmp_path):
    _init(tmp_path)
    project.set_context_backend(tmp_path, "codegraph")
    assert project.context_backend(tmp_path) == "codegraph"


def test_set_context_backend_rechaza_invalido(tmp_path):
    _init(tmp_path)
    assert project.set_context_backend(tmp_path, "no-existe") is False
    assert project.context_backend(tmp_path) == "serena"  # no lo tocó


def test_set_context_backend_sin_proyecto_inicializado(tmp_path):
    assert project.set_context_backend(tmp_path, "serena") is False


def test_set_context_backend_persiste_en_config_json(tmp_path):
    _init(tmp_path)
    project.set_context_backend(tmp_path, "graphify")
    data = json.loads((tmp_path / ".tramalia" / "config.json").read_text(encoding="utf-8"))
    assert data["context"]["backend"] == "graphify"


# ---------------------------------------------------------------- tools.json
def test_tools_json_incluye_context_backend(tmp_path):
    from tramalia.core.doctor import diagnose, write_snapshot

    _init(tmp_path)
    project.set_context_backend(tmp_path, "codebase-memory-mcp")
    out = write_snapshot(diagnose(tmp_path), tmp_path)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["context_backend"] == "codebase-memory-mcp"


# ---------------------------------------------------------------- AGENTS.md
def test_agents_md_declara_backend_activo(tmp_path):
    _init(tmp_path)
    texto = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "context.backend" in texto
    assert "no alternes" in texto.lower()


# ---------------------------------------------------------------- CLI
def test_cli_context_set_y_list(tmp_path, monkeypatch, capsys):
    import sys

    from tramalia.__main__ import main

    monkeypatch.chdir(tmp_path)
    _init(tmp_path)

    monkeypatch.setattr(sys, "argv", ["tramalia", "--plain", "context", "set", "graphify"])
    assert main() in (0, None)
    assert project.context_backend(tmp_path) == "graphify"

    monkeypatch.setattr(sys, "argv", ["tramalia", "--plain", "context", "list"])
    main()
    out = capsys.readouterr().out
    assert "graphify" in out and "serena" in out


def test_cli_context_set_invalido_exit_1(tmp_path, monkeypatch):
    import sys

    from tramalia.__main__ import main

    monkeypatch.chdir(tmp_path)
    _init(tmp_path)
    monkeypatch.setattr(sys, "argv", ["tramalia", "--plain", "context", "set", "loquesea"])
    assert main() == 1


# ---------------------------------------------------------------- TUI
def test_tui_backend_screen_fija_config(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    monkeypatch.chdir(tmp_path)
    _init(tmp_path)
    from tramalia.tui import build_app

    app = build_app()()

    async def run():
        async with app.run_test() as pilot:
            await pilot.pause()
            app.action_context_backend()  # tecla b
            await pilot.pause()
            app._on_backend_chosen("codegraph")
            await pilot.pause()
            assert project.context_backend(tmp_path) == "codegraph"

    asyncio.run(run())


def test_tui_backend_screen_cancelar_no_cambia_nada(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    monkeypatch.chdir(tmp_path)
    _init(tmp_path)
    from tramalia.tui import build_app

    app = build_app()()

    async def run():
        async with app.run_test() as pilot:
            await pilot.pause()
            app._on_backend_chosen(None)  # cancelar
            await pilot.pause()
            assert project.context_backend(tmp_path) == "serena"

    asyncio.run(run())
