"""La convención generada por init debe estar completa: docs/ai 00-11, specs,
current-task y las 13 skills numeradas."""

import json

from tramalia.core.detect import enabled_features
from tramalia.core.scaffold import build_mcp_json, scaffold


def _init(tmp_path, **extra):
    answers = {
        "project_name": "demo", "stacks": ["node"],
        "features": enabled_features(["node"]),
        "primary_agent": "codex", "reviewer_agent": "claude",
    }
    answers.update(extra)
    return scaffold(tmp_path, answers)


def test_docs_ai_completo_00_a_13(tmp_path):
    _init(tmp_path)
    nombres = sorted(p.name for p in (tmp_path / "docs" / "ai").iterdir())
    numeros = sorted(n.split("-")[0] for n in nombres)
    assert numeros == [f"{i:02d}" for i in range(14)], f"docs/ai incompleto: {nombres}"


def test_specs_generada_e_integrada(tmp_path):
    _init(tmp_path)
    specs = tmp_path / "specs"
    for f in ("constitution.md", "specification.md", "plan.md", "tasks.md", "checklist.md"):
        assert (specs / f).exists(), f
    # integración con Tramalia: tasks referencia close; checklist exige evidence
    assert "tramalia close" in (specs / "tasks.md").read_text(encoding="utf-8")
    assert "tramalia close" in (specs / "checklist.md").read_text(encoding="utf-8")


def test_current_task_existe(tmp_path):
    _init(tmp_path)
    assert (tmp_path / ".tramalia" / "current-task.md").exists()


def test_dieciseis_skills_numeradas(tmp_path):
    _init(tmp_path)
    base = tmp_path / ".tramalia" / "skills"
    skills = sorted(d.name for d in base.iterdir() if d.is_dir())
    assert len(skills) == 16
    assert skills[0].startswith("01-") and skills[-1].startswith("16-")
    for d in skills:
        assert (base / d / "SKILL.md").exists(), d


def test_agents_md_referencia_skills_y_02(tmp_path):
    _init(tmp_path)
    texto = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "02-reglas-codigo" in texto
    assert "16 skills" in texto
    assert "tramalia close" in texto


def test_ponytail_declarado_en_skills_toml(tmp_path):
    _init(tmp_path)
    texto = (tmp_path / ".tramalia" / "skills.toml").read_text(encoding="utf-8")
    assert '[[skill]]' in texto and 'name   = "ponytail"' in texto


def test_init_con_ponytail_agrega_mcp(tmp_path):
    data = json.loads(build_mcp_json({"stacks": [], "features": (), "with_ponytail": True}))
    assert "ponytail" in data["mcpServers"]
    assert data["mcpServers"]["ponytail"]["command"] == "node"


def test_init_sin_ponytail_no_lo_agrega(tmp_path):
    data = json.loads(build_mcp_json({"stacks": [], "features": ()}))
    assert "ponytail" not in data["mcpServers"]
