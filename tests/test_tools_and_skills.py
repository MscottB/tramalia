from tramalia.core.tools import relevant_tools
from tramalia.core.skills import read_skills, sync_skills


def test_bootstrap_tools_always_present():
    keys = {t.key for t in relevant_tools([], ())}
    assert {"mise", "git", "uv"} <= keys


def test_stack_and_feature_filtering():
    keys = {t.key for t in relevant_tools(["node"], ("security",))}
    assert "node" in keys
    assert {"semgrep", "gitleaks"} <= keys
    assert "sqlfluff" not in keys  # feature "database" no habilitado


def test_read_skills_empty(tmp_path):
    assert read_skills(tmp_path) == []


def test_read_skills_parses(tmp_path):
    (tmp_path / ".tramalia").mkdir()
    (tmp_path / ".tramalia" / "skills.toml").write_text(
        '[[skill]]\nname = "ponytail"\nsource = "git+https://example.com/x"\nref = "main"\n',
        encoding="utf-8",
    )
    items = read_skills(tmp_path)
    assert items and items[0]["name"] == "ponytail"


def test_sync_no_skills_returns_empty(tmp_path):
    assert sync_skills(tmp_path) == []
