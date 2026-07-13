from tramalia.core import governance
from tramalia.core.detect import enabled_features
from tramalia.core.scaffold import scaffold


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


def test_close_standalone_without_mise(tmp_path, monkeypatch):
    _init(tmp_path)
    monkeypatch.setattr(governance.proc, "which", lambda c: None)  # forzar sin mise
    res = governance.close(tmp_path, "TASK-1")
    assert res.evidence_dir.exists()
    assert (res.evidence_dir / "gates-status.md").exists()
    assert res.handoff_path.exists()
    assert res.gates_ran is False
    assert res.blocked is False  # sin gates ejecutados no bloquea; queda documentado
