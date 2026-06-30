from tramalia.core.detect import detect_stack, enabled_features


def test_detects_node_angular_postgres(tmp_path):
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "angular.json").write_text("{}", encoding="utf-8")
    (tmp_path / "schema.sql").write_text("select 1;", encoding="utf-8")
    stack = detect_stack(tmp_path)
    assert {"node", "angular", "postgres"} <= set(stack)


def test_features_include_ux_and_db(tmp_path):
    (tmp_path / "angular.json").write_text("{}", encoding="utf-8")
    (tmp_path / "schema.sql").write_text("select 1;", encoding="utf-8")
    feats = enabled_features(detect_stack(tmp_path))
    assert "ux" in feats and "database" in feats


def test_python_only_has_db_not_ux(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    feats = enabled_features(detect_stack(tmp_path))
    assert "database" in feats
    assert "ux" not in feats
