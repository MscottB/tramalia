"""Spec Kit en doctor, handoff enlazado a evidence, y TUI opcional."""

import pytest

from tramalia.core import governance
from tramalia.core.detect import enabled_features
from tramalia.core.handoff import new_handoff
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


def test_handoff_acepta_referencia_a_evidence(tmp_path):
    path = new_handoff(
        tmp_path, "TASK-5", "codex", "claude", evidence_ref=".tramalia/evidence/x-TASK-5"
    )
    assert ".tramalia/evidence/x-TASK-5" in path.read_text(encoding="utf-8")


def test_close_enlaza_evidence_en_handoff(tmp_path, monkeypatch):
    monkeypatch.setattr(governance.proc, "which", lambda c: None)
    res = governance.close(tmp_path, "TASK-9")
    texto = res.handoff_path.read_text(encoding="utf-8")
    assert res.metadata["evidence_dir"] in texto


def test_tui_construye():
    pytest.importorskip("textual")
    from tramalia.tui import build_app

    app_cls = build_app()
    app = app_cls()  # instanciar no levanta la UI
    assert app.TITLE.startswith("Tramalia v")  # muestra la versión en el UI
