from tramalia.core.handoff import new_handoff


def test_handoff_appends_entries(tmp_path):
    path = new_handoff(tmp_path, "TASK-1", "codex", "claude")
    new_handoff(tmp_path, "TASK-2", "claude", "codex")
    text = path.read_text(encoding="utf-8")
    assert "TASK-1" in text and "TASK-2" in text
    assert text.count("Agente ejecutor") == 2
