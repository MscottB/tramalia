"""metadata.json: auditoría estructurada de cada cierre, con estado honesto."""

import json

from tramalia.core import governance


def test_close_genera_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(governance.proc, "which", lambda c: None)  # sin mise
    res = governance.close(tmp_path, "TASK-7", agent="codex", reviewer="claude")
    meta_file = res.evidence_dir / "metadata.json"
    assert meta_file.exists()
    m = json.loads(meta_file.read_text(encoding="utf-8"))
    assert m["task"] == "TASK-7"
    assert m["agent"] == "codex"
    assert m["reviewer"] == "claude"
    assert m["gates_ran"] is False
    assert "closed_at" in m and "started_at" in m


def test_estado_sin_gates(tmp_path, monkeypatch):
    monkeypatch.setattr(governance.proc, "which", lambda c: None)
    res = governance.close(tmp_path, "TASK-1")
    assert res.status == "no_gates"
    assert res.blocked is False


def test_estado_bloqueado(tmp_path, monkeypatch):
    monkeypatch.setattr(governance, "run_gates", lambda root: ([("build", 1, "falló")], True))
    res = governance.close(tmp_path, "TASK-2")
    assert res.status == "blocked"
    assert res.blocked is True


def test_estado_forzado_no_se_maquilla_como_passed(tmp_path, monkeypatch):
    monkeypatch.setattr(governance, "run_gates", lambda root: ([("build", 1, "falló")], True))
    res = governance.close(tmp_path, "TASK-3", allow_fail=True)
    assert res.status == "passed_with_exceptions"  # honesto: no es "passed" a secas
    assert res.blocked is False  # forzado, no bloquea


def test_log_lee_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(governance, "run_gates", lambda root: ([("build", 0, "ok")], True))
    governance.close(tmp_path, "TASK-9", agent="codex")
    entries = governance.read_log(tmp_path)
    assert entries[0]["status"] == "passed"
    assert entries[0]["agent"] == "codex"
