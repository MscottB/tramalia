"""v0.14: modo adopt — integrar el gobierno en repos con agente existente."""

import json

from tramalia.core.scaffold import scaffold, _inject_block, _merge_mcp, _GOBIERNO_MARKER


def _answers(**extra):
    base = {"project_name": "demo", "stacks": ["python"], "features": [],
            "primary_agent": "codex", "reviewer_agent": "claude"}
    base.update(extra)
    return base


# ---------------------------------------------------------------- inject block
def test_inject_agrega_bloque_y_conserva_contenido():
    original = "# Mi proyecto\n\nReglas propias del equipo.\n"
    out = _inject_block(original, "tramalia:gobierno", "## Gobierno\ncerrar con close")
    assert "Reglas propias del equipo." in out          # no pisa lo del usuario
    assert "<!-- tramalia:gobierno inicio -->" in out
    assert "<!-- tramalia:gobierno fin -->" in out


def test_inject_es_idempotente():
    original = "# X\n\ncontenido\n"
    once = _inject_block(original, "m", "cuerpo v1")
    twice = _inject_block(once, "m", "cuerpo v1")
    assert once == twice                                 # re-ejecutar no duplica
    assert once.count("<!-- m inicio -->") == 1


def test_inject_reemplaza_bloque_al_cambiar():
    once = _inject_block("base\n", "m", "cuerpo v1")
    updated = _inject_block(once, "m", "cuerpo v2")
    assert "cuerpo v2" in updated and "cuerpo v1" not in updated
    assert updated.count("<!-- m inicio -->") == 1


# ---------------------------------------------------------------- merge mcp
def test_merge_mcp_respeta_servidores_del_usuario():
    existing = json.dumps({"mcpServers": {"mio": {"command": "x"}}})
    merged, ok = _merge_mcp(existing, {"serena": {"command": "uvx"}, "mio": {"command": "NO"}})
    assert ok
    data = json.loads(merged)
    assert data["mcpServers"]["mio"]["command"] == "x"   # no lo pisa
    assert "serena" in data["mcpServers"]                # agrega el nuevo


def test_merge_mcp_json_malformado_no_se_toca():
    bad = "{ esto no es json"
    merged, ok = _merge_mcp(bad, {"serena": {}})
    assert ok is False and merged == bad


# ---------------------------------------------------------------- scaffold adopt
def test_adopt_integra_agents_md_existente(tmp_path):
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# Reglas del equipo\n\nNo tocar la carpeta legacy/.\n", encoding="utf-8")
    results = dict(scaffold(tmp_path, _answers(adopt=True)))
    assert results["AGENTS.md"] == "adaptado"
    texto = agents.read_text(encoding="utf-8")
    assert "No tocar la carpeta legacy/." in texto        # conserva lo del usuario
    assert _GOBIERNO_MARKER in texto and "tramalia close" in texto


def test_sin_adopt_no_toca_agents_md_existente(tmp_path):
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# Reglas del equipo\n", encoding="utf-8")
    results = dict(scaffold(tmp_path, _answers()))
    assert results["AGENTS.md"] == "existe"
    assert _GOBIERNO_MARKER not in agents.read_text(encoding="utf-8")


def test_adopt_fusiona_mcp_json_existente(tmp_path):
    mcp = tmp_path / ".mcp.json"
    mcp.write_text(json.dumps({"mcpServers": {"custom": {"command": "z"}}}), encoding="utf-8")
    results = dict(scaffold(tmp_path, _answers(adopt=True)))
    assert results[".mcp.json"] == "adaptado"
    data = json.loads(mcp.read_text(encoding="utf-8"))
    assert "custom" in data["mcpServers"] and "serena" in data["mcpServers"]


def test_adopt_reejecutado_no_duplica(tmp_path):
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# Reglas\n", encoding="utf-8")
    scaffold(tmp_path, _answers(adopt=True))
    scaffold(tmp_path, _answers(adopt=True))             # segunda pasada
    texto = agents.read_text(encoding="utf-8")
    assert texto.count("<!-- tramalia:gobierno inicio -->") == 1
