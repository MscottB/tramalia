"""Spec Kit en doctor y construccion opcional de la TUI."""

import pytest

from tramalia.core.detect import enabled_features
from tramalia.core.tools import REGISTRY, relevant_tools


def test_speckit_en_registro_como_opcional():
    sk = next((t for t in REGISTRY if t.key == "speckit"), None)
    assert sk is not None
    assert sk.cmd == "specify"
    assert sk.category == "feature" and sk.feature == "specs"


def test_specs_feature_siempre_habilitada():
    assert "specs" in enabled_features([])
    keys = {t.key for t in relevant_tools([], enabled_features([]))}
    assert "speckit" in keys


def test_graphify_en_registro_como_alternativa_de_contexto():
    gf = next((t for t in REGISTRY if t.key == "graphify"), None)
    assert gf is not None
    assert gf.category == "feature" and gf.feature == "context"
    assert gf.managed_by_mise is False


def test_tui_construye():
    pytest.importorskip("textual")
    from tramalia.tui import build_app

    app_cls = build_app()
    app = app_cls()  # instanciar no levanta la UI
    assert app.TITLE.startswith("Tramalia v")  # muestra la versión en el UI
