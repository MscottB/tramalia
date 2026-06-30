from tramalia.core.context import build_context


def test_context_generates_derived_files(tmp_path):
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    results = build_context(tmp_path)
    assert "tech-stack.md" in results
    assert "project-map.md" in results
    ctx = tmp_path / ".tramalia" / "context"
    assert (ctx / "tech-stack.md").exists()
    assert (ctx / "project-map.md").exists()
