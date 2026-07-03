"""Subagentes con ruteo de modelo por rol + registro del modelo en la auditoría."""

import re

from tramalia.__main__ import build_parser
from tramalia.core import governance
from tramalia.core.detect import enabled_features
from tramalia.core.scaffold import scaffold

_AGENTES_ESPERADOS = {
    "planificador": "opus",
    "ejecutor": "inherit",
    "revisor": "opus",
    "documentador": "haiku",
    "resolutor-profundo": "fable",
}


def _init(tmp_path):
    scaffold(tmp_path, {
        "project_name": "demo", "stacks": ["node"],
        "features": enabled_features(["node"]),
        "primary_agent": "codex", "reviewer_agent": "claude",
    })


def _frontmatter_model(texto: str) -> str:
    m = re.search(r"^model:\s*(\S+)", texto, flags=re.M)
    return m.group(1) if m else ""


def test_cinco_subagentes_con_su_modelo(tmp_path):
    _init(tmp_path)
    base = tmp_path / ".claude" / "agents"
    for nombre, modelo in _AGENTES_ESPERADOS.items():
        archivo = base / f"{nombre}.md"
        assert archivo.exists(), nombre
        assert _frontmatter_model(archivo.read_text(encoding="utf-8")) == modelo, nombre


def test_subagentes_anclados_a_tramalia(tmp_path):
    _init(tmp_path)
    base = tmp_path / ".claude" / "agents"
    assert "tramalia close" in (base / "ejecutor.md").read_text(encoding="utf-8")
    assert "evidence pack" in (base / "revisor.md").read_text(encoding="utf-8")


def test_close_registra_modelo_en_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(governance.proc, "which", lambda c: None)
    res = governance.close(tmp_path, "TASK-1", agent="codex", model="opus")
    assert res.metadata["model"] == "opus"


def test_log_incluye_modelo(tmp_path, monkeypatch):
    monkeypatch.setattr(governance, "run_gates", lambda root: ([("build", 0, "ok")], True))
    governance.close(tmp_path, "TASK-2", agent="codex", model="haiku")
    entries = governance.read_log(tmp_path)
    assert entries[0]["model"] == "haiku"


def test_parser_acepta_model_y_features():
    p = build_parser()
    args = p.parse_args(["close", "--task", "T-1", "--model", "opus"])
    assert args.model == "opus"
    args = p.parse_args(["sync", "--features", "rules"])
    assert args.features == "rules"
