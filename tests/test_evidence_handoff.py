from tramalia.core.evidence import build_evidence
from tramalia.core.handoff import new_handoff

_EXPECTED = [
    "summary.md",
    "files-changed.md",
    "commands.md",
    "risks.md",
    "rollback.md",
    "next-steps.md",
    "ux-output.txt",
    "security-output.txt",
]


def test_evidence_pack_has_all_files(tmp_path):
    target = build_evidence(tmp_path, "TASK-9")
    assert target.exists()
    for name in _EXPECTED:
        assert (target / name).exists(), name


def test_handoff_appends_entries(tmp_path):
    path = new_handoff(tmp_path, "TASK-1", "codex", "claude")
    new_handoff(tmp_path, "TASK-2", "claude", "codex")
    text = path.read_text(encoding="utf-8")
    assert "TASK-1" in text and "TASK-2" in text
    assert text.count("Agente ejecutor") == 2
