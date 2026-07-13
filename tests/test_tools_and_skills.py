from tramalia.core.integraciones import herramientas_relevantes
from tramalia.core.skills import read_skills, sync_skills


def test_bootstrap_tools_always_present():
    keys = {herramienta.clave for herramienta in herramientas_relevantes([], ())}
    assert {"mise", "git", "uv"} <= keys


def test_stack_and_feature_filtering():
    keys = {herramienta.clave for herramienta in herramientas_relevantes(["node"], ("security",))}
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
