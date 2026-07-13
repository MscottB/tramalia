"""v0.16: analítica avanzada — métricas/umbrales en el cierre + gate de notebooks."""

import json

from tramalia.core import governance
from tramalia.core.detect import enabled_features
from tramalia.core.governance import _check_thresholds, close
from tramalia.core.scaffold import build_mise_toml


# ---------------------------------------------------------------- umbrales (unit)
def test_check_thresholds_min_y_max():
    metrics = {"metrics": {"accuracy": 0.88, "drift": 0.09}}
    thr = {"accuracy": {"min": 0.90}, "drift": {"max": 0.05}}
    v = _check_thresholds(metrics, thr)
    assert any("accuracy" in x for x in v) and any("drift" in x for x in v)


def test_check_thresholds_ok():
    metrics = {"metrics": {"accuracy": 0.95}}
    assert _check_thresholds(metrics, {"accuracy": {"min": 0.90}}) == []


def test_check_thresholds_metrica_ausente_es_incumplimiento():
    v = _check_thresholds({"metrics": {}}, {"accuracy": {"min": 0.9}})
    assert v and "ausente" in v[0]


# ---------------------------------------------------------------- close integra
def _prep(tmp_path):
    (tmp_path / ".tramalia").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "ai").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "ai" / "07-handoff-agentes.md").write_text("# handoff\n", encoding="utf-8")


def test_close_embebe_metricas_en_evidencia(tmp_path):
    _prep(tmp_path)
    (tmp_path / ".tramalia" / "metrics.json").write_text(
        json.dumps({"dataset": {"name": "d", "hash": "abc"}, "metrics": {"accuracy": 0.93}}),
        encoding="utf-8",
    )
    res = close(tmp_path, task="TASK-1", agent="codex", reviewer="claude")
    # sin mise: no_gates, pero las métricas quedan como evidencia cruda + en metadata
    assert (res.evidence_dir / "metrics.json").is_file()
    assert res.metadata["metrics"]["metrics"]["accuracy"] == 0.93


def test_close_umbral_incumplido_bloquea(tmp_path):
    _prep(tmp_path)
    (tmp_path / ".tramalia" / "metrics.json").write_text(
        json.dumps({"metrics": {"accuracy": 0.80}}), encoding="utf-8"
    )
    (tmp_path / ".tramalia" / "thresholds.json").write_text(
        json.dumps({"accuracy": {"min": 0.90}}), encoding="utf-8"
    )
    res = close(tmp_path, task="TASK-1", agent="codex", reviewer="claude")
    assert res.status == "blocked" and res.blocked is True
    assert res.metadata["metric_thresholds"]["passed"] is False
    assert (res.evidence_dir / "metrics-thresholds.txt").read_text(encoding="utf-8").find(
        "INCUMPLIMIENTOS"
    ) >= 0


def test_close_umbral_cumplido_no_bloquea(tmp_path):
    _prep(tmp_path)
    (tmp_path / ".tramalia" / "metrics.json").write_text(
        json.dumps({"metrics": {"accuracy": 0.95}}), encoding="utf-8"
    )
    (tmp_path / ".tramalia" / "thresholds.json").write_text(
        json.dumps({"accuracy": {"min": 0.90}}), encoding="utf-8"
    )
    res = close(tmp_path, task="TASK-1", agent="codex", reviewer="claude")
    assert res.blocked is False
    assert res.metadata["metric_thresholds"]["passed"] is True


def test_close_umbral_incumplido_con_allow_fail_es_excepcion(tmp_path):
    _prep(tmp_path)
    (tmp_path / ".tramalia" / "metrics.json").write_text(
        json.dumps({"metrics": {"accuracy": 0.80}}), encoding="utf-8"
    )
    (tmp_path / ".tramalia" / "thresholds.json").write_text(
        json.dumps({"accuracy": {"min": 0.90}}), encoding="utf-8"
    )
    res = close(tmp_path, task="TASK-1", allow_fail=True)
    assert res.status == "passed_with_exceptions" and res.blocked is False


def test_close_sin_metricas_es_igual_que_antes(tmp_path, monkeypatch):
    _prep(tmp_path)
    # hermético: simular que mise NO está (independiente de la máquina)
    monkeypatch.setattr(governance.proc, "which", lambda _cmd: None)
    res = close(tmp_path, task="TASK-1")
    assert res.status == "no_gates"  # sin mise ni métricas: comportamiento previo
    assert "metrics" not in (res.metadata or {})


# ---------------------------------------------------------------- gate notebooks
def test_gate_notebooks_es_opt_in():
    base = {
        "stacks": ["python", "notebooks"],
        "features": enabled_features(["python", "notebooks"]),
    }
    assert "jupyter execute" not in build_mise_toml(base)  # off por defecto
    on = dict(base, with_notebook_exec=True)
    assert "jupyter execute notebooks/*.ipynb" in build_mise_toml(on)


def test_notebooks_en_gate_order():
    assert "notebooks" in governance._GATE_ORDER
