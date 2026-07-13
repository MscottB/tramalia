"""v0.21: tools.json para agentes + skills add por URL."""

import json

from tramalia.core.detect import enabled_features
from tramalia.core.doctor import diagnose, write_snapshot
from tramalia.core.scaffold import scaffold
from tramalia.core.skills import add_skill, catalog


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


# ---------------------------------------------------------------- tools.json
def test_snapshot_escribe_estado_para_agentes(tmp_path):
    _init(tmp_path)
    out = write_snapshot(diagnose(tmp_path), tmp_path)
    assert out is not None and out.name == "tools.json"
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["tools"] and all("installed" in t for t in data["tools"])
    # las ausentes traen la alternativa (para que el agente no llame a ciegas)
    ausentes = [t for t in data["tools"] if not t["installed"]]
    assert all(t["alternative"] for t in ausentes)


def test_snapshot_no_escribe_sin_init(tmp_path):
    assert write_snapshot(diagnose(tmp_path), tmp_path) is None


def test_agents_md_ordena_consultar_tools_json(tmp_path):
    _init(tmp_path)
    texto = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "tools.json" in texto


# ---------------------------------------------------------------- skills add
def test_add_skill_por_url_deriva_nombre(tmp_path):
    _init(tmp_path)
    ok, nombre = add_skill(tmp_path, "https://github.com/acme/mi-skill.git")
    assert ok and nombre == "mi-skill"
    items = {s["name"]: s for s in catalog(tmp_path)}
    assert items["mi-skill"]["enabled"] is True
    assert items["mi-skill"]["source"].startswith("git+https://")


def test_add_skill_con_alias(tmp_path):
    _init(tmp_path)
    ok, nombre = add_skill(tmp_path, "https://github.com/acme/x", name="alias-corto")
    assert ok and nombre == "alias-corto"


def test_add_skill_rechaza_duplicada_y_url_mala(tmp_path):
    _init(tmp_path)
    assert add_skill(tmp_path, "https://github.com/acme/ponytail") == (False, "duplicada")
    assert add_skill(tmp_path, "no-es-una-url") == (False, "url-invalida")
