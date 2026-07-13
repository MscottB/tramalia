"""v0.32 (R5b/F1): init detecta agentes instalados en vez de codex/claude fijos.

Antes, `tramalia init` grababa siempre primary="codex", reviewer="claude" en
config.json sin importar qué había instalado — el tab Cierre precargaba esos
nombres sin relación con la máquina real. Ahora se detecta con tools.probe().
"""

import json
import types

from tramalia.core import tools
from tramalia.core.detect import enabled_features
from tramalia.core.scaffold import scaffold


def _tool(key):
    return next(t for t in tools.REGISTRY if t.key == key)


# ---------------------------------------------------------------- detect_default_agents
def test_dos_agentes_detectados_uno_ejecuta_otro_revisa(monkeypatch):
    def fake_probe(tool, timeout=8.0):
        return tools.Status(tool, present=tool.key in ("claude", "codex"))

    monkeypatch.setattr(tools, "probe", fake_probe)
    primary, reviewer = tools.detect_default_agents()
    assert primary == "claude"  # primero en el orden de preferencia
    assert reviewer == "codex"
    assert primary != reviewer  # cross-review real


def test_un_solo_agente_se_usa_para_ambos(monkeypatch):
    def fake_probe(tool, timeout=8.0):
        return tools.Status(tool, present=tool.key == "opencode")

    monkeypatch.setattr(tools, "probe", fake_probe)
    primary, reviewer = tools.detect_default_agents()
    assert primary == reviewer == "opencode"


def test_ningun_agente_cae_a_ejemplo_editable(monkeypatch):
    monkeypatch.setattr(tools, "probe", lambda tool, timeout=8.0: tools.Status(tool, present=False))
    assert tools.detect_default_agents() == ("codex", "claude")


def test_antigravity_ide_y_2_excluidos_de_deteccion(monkeypatch):
    # apps de escritorio: no pueden ejecutar `close` por shell, no deben elegirse
    def fake_probe(tool, timeout=8.0):
        return tools.Status(tool, present=tool.key in ("antigravity-ide", "antigravity-2"))

    monkeypatch.setattr(tools, "probe", fake_probe)
    assert tools.detect_default_agents() == ("codex", "claude")  # fallback, no las apps


# ---------------------------------------------------------------- init usa la detección
def test_init_config_json_usa_agentes_detectados(tmp_path, monkeypatch):
    # cmd_init hace `from tramalia.core.tools import detect_default_agents` en
    # el cuerpo de la función: parchar el atributo del módulo alcanza.
    monkeypatch.setattr(tools, "detect_default_agents", lambda: ("opencode", "opencode"))
    monkeypatch.chdir(tmp_path)
    from tramalia.cli import commands

    commands.cmd_init(types.SimpleNamespace())
    data = json.loads((tmp_path / ".tramalia" / "config.json").read_text(encoding="utf-8"))
    assert data["agents"]["primary"] == "opencode"
    assert data["agents"]["reviewer"] == "opencode"


def test_upgrade_no_pisa_config_existente(tmp_path, monkeypatch):
    # upgrade nunca toca un config.json ya existente (idempotencia del scaffold)
    scaffold(
        tmp_path,
        {
            "project_name": "demo",
            "stacks": ["python"],
            "features": enabled_features(["python"]),
            "primary_agent": "claude",
            "reviewer_agent": "codex",
        },
    )
    cfg = tmp_path / ".tramalia" / "config.json"
    original = cfg.read_text(encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    from tramalia.cli import commands

    commands.cmd_upgrade(types.SimpleNamespace())
    assert cfg.read_text(encoding="utf-8") == original
