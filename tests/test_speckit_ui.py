"""Spec Kit en doctor y construccion opcional de la TUI."""

import pytest

from tramalia.core.detect import enabled_features
from tramalia.core.integraciones import REGISTRO, herramientas_relevantes


def test_speckit_en_registro_como_opcional():
    sk = next((herramienta for herramienta in REGISTRO if herramienta.clave == "speckit"), None)
    assert sk is not None
    assert sk.comando == "specify"
    assert sk.categoria == "feature" and sk.capacidad == "specs"


def test_specs_feature_siempre_habilitada():
    assert "specs" in enabled_features([])
    keys = {herramienta.clave for herramienta in herramientas_relevantes([], enabled_features([]))}
    assert "speckit" in keys


def test_graphify_en_registro_como_alternativa_de_contexto():
    gf = next((herramienta for herramienta in REGISTRO if herramienta.clave == "graphify"), None)
    assert gf is not None
    assert gf.categoria == "feature" and gf.capacidad == "context"
    assert gf.administrada_por_mise is False


def test_tui_construye():
    pytest.importorskip("textual")
    from tramalia.tui import build_app

    app_cls = build_app()
    app = app_cls()  # instanciar no levanta la UI
    assert app.TITLE.startswith("Tramalia v")  # muestra la versión en el UI
