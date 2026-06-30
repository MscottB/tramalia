import json
import tomllib

from tramalia.core.detect import enabled_features
from tramalia.core.scaffold import scaffold


def _answers(stack):
    return {
        "project_name": "demo",
        "stacks": stack,
        "features": enabled_features(stack),
        "primary_agent": "codex",
        "reviewer_agent": "claude",
    }


def test_scaffold_creates_and_is_idempotent(tmp_path):
    ans = _answers(["node", "angular", "postgres"])
    first = scaffold(tmp_path, ans)
    assert any(rel == "AGENTS.md" and st == "creado" for rel, st in first)
    assert (tmp_path / "AGENTS.md").exists()
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / "docs" / "ai" / "11-reglas-ux-ui.md").exists()

    # TOML/JSON generados deben ser válidos
    tomllib.loads((tmp_path / "mise.toml").read_text(encoding="utf-8"))
    json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))
    json.loads((tmp_path / ".tramalia" / "config.json").read_text(encoding="utf-8"))

    # segunda corrida: nada se recrea
    second = scaffold(tmp_path, ans)
    assert all(st == "existe" for _, st in second)


def test_mise_tasks_match_stack(tmp_path):
    scaffold(tmp_path, _answers(["node", "angular", "postgres"]))
    data = tomllib.loads((tmp_path / "mise.toml").read_text(encoding="utf-8"))
    tasks = data["tasks"]
    assert "ux" in tasks          # frontend detectado
    assert "database" in tasks    # postgres detectado
    assert set(tasks["gates"]["depends"]) >= {
        "build", "test", "lint", "security", "database", "ux"
    }


def test_existing_file_is_preserved(tmp_path):
    (tmp_path / "AGENTS.md").write_text("CONTENIDO PREVIO", encoding="utf-8")
    scaffold(tmp_path, _answers(["python"]))
    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == "CONTENIDO PREVIO"
