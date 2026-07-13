"""Headroom como interop opcional de compresión: nunca toca el núcleo ni la evidencia."""

import json

from tramalia.core.detect import enabled_features
from tramalia.core.doctor import diagnose
from tramalia.core.scaffold import build_mcp_json, scaffold


def _init(tmp_path):
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    scaffold(
        tmp_path,
        {
            "project_name": "d",
            "stacks": ["node"],
            "features": enabled_features(["node"]),
            "primary_agent": "codex",
            "reviewer_agent": "claude",
        },
    )


def test_doctor_clasifica_headroom_como_opcional(tmp_path, monkeypatch):
    import tramalia.core.integraciones as integraciones_mod

    real_which = integraciones_mod.shutil.which
    monkeypatch.setattr(
        integraciones_mod.shutil, "which", lambda c: None if c == "headroom" else real_which(c)
    )
    # hermético: headroom no debe verse "presente" por estar en ~/.local/bin o ~/go/bin
    # del equipo que corre los tests (las sondas de filesystem no dependen de `which`).
    monkeypatch.setattr(integraciones_mod, "_instalada_por_uv", lambda c: False)
    monkeypatch.setattr(integraciones_mod, "_instalada_por_go", lambda c: False)
    rep = diagnose(tmp_path)
    assert "headroom" in {estado.herramienta.clave for estado in rep.missing_optional}
    assert "headroom" not in {estado.herramienta.clave for estado in rep.missing_blocking}


def test_init_no_agrega_headroom_por_defecto(tmp_path):
    data = json.loads(build_mcp_json({"stacks": [], "features": ()}))
    assert "headroom" not in data["mcpServers"]


def test_init_con_headroom_agrega_mcp(tmp_path):
    data = json.loads(build_mcp_json({"stacks": [], "features": (), "with_headroom": True}))
    assert "headroom" in data["mcpServers"]
