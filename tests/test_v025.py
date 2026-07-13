"""v0.25: tope de modelos por subagente, portable y opt-in."""

import json
import re

from tramalia.core import model_cap, project
from tramalia.core.detect import enabled_features
from tramalia.core.scaffold import scaffold


def _init(tmp_path):
    scaffold(
        tmp_path,
        {
            "project_name": "demo",
            "stacks": ["python"],
            "features": enabled_features(["python"]),
            "primary_agent": "codex",
            "reviewer_agent": "claude",
        },
    )
    return tmp_path


def _model_of(root, role):
    text = (root / ".claude" / "agents" / f"{role}.md").read_text(encoding="utf-8")
    return re.search(r"(?m)^model:\s*(.+)$", text).group(1).strip()


# ---------------------------------------------------------------- cap_model
def test_cap_baja_lo_superior_y_conserva_lo_inferior():
    # tope sonnet: opus/fable → sonnet; haiku se conserva; inherit intacto
    assert model_cap.cap_model("opus", "sonnet") == "sonnet"
    assert model_cap.cap_model("fable", "sonnet") == "sonnet"
    assert model_cap.cap_model("haiku", "sonnet") == "haiku"
    assert model_cap.cap_model("inherit", "sonnet") == "inherit"
    assert model_cap.cap_model("sonnet", "sonnet") == "sonnet"


def test_cap_none_no_cambia_nada():
    for m in ("opus", "fable", "haiku", "inherit"):
        assert model_cap.cap_model(m, "none") == m


def test_resolved_models_tope_sonnet():
    r = model_cap.resolved_models("sonnet")
    assert r == {
        "planificador": "sonnet",
        "ejecutor": "inherit",
        "revisor": "sonnet",
        "documentador": "haiku",
        "resolutor-profundo": "sonnet",
    }


# ---------------------------------------------------------------- apply / config
def test_apply_reescribe_solo_la_linea_model(tmp_path):
    _init(tmp_path)
    antes = (tmp_path / ".claude" / "agents" / "planificador.md").read_text(encoding="utf-8")
    model_cap.apply_to_agents(tmp_path, "sonnet")
    despues = (tmp_path / ".claude" / "agents" / "planificador.md").read_text(encoding="utf-8")
    assert _model_of(tmp_path, "planificador") == "sonnet"
    assert _model_of(tmp_path, "documentador") == "haiku"  # ya estaba debajo
    # el cuerpo del agente no se toca (solo cambió la línea model:)
    assert antes.replace("model: opus", "") == despues.replace("model: sonnet", "")


def test_cap_none_restaura_defaults(tmp_path):
    _init(tmp_path)
    model_cap.apply_to_agents(tmp_path, "haiku")
    assert _model_of(tmp_path, "planificador") == "haiku"
    model_cap.apply_to_agents(tmp_path, "none")
    assert _model_of(tmp_path, "planificador") == "opus"  # vuelve al default de rol
    assert _model_of(tmp_path, "resolutor-profundo") == "fable"


def test_project_cap_persiste_en_config(tmp_path):
    _init(tmp_path)
    assert project.agents_model_cap(tmp_path) == "none"
    assert project.set_agents_model_cap(tmp_path, "opus")
    assert project.agents_model_cap(tmp_path) == "opus"
    data = json.loads((tmp_path / ".tramalia" / "config.json").read_text(encoding="utf-8"))
    assert data["agents"]["model_cap"] == "opus"


def test_set_cap_rechaza_invalido_y_sin_config(tmp_path):
    _init(tmp_path)
    assert project.set_agents_model_cap(tmp_path, "gpt5") is False
    assert project.set_agents_model_cap(tmp_path, "opus")  # válido
    # sin config.json:
    assert project.set_agents_model_cap(tmp_path / "otro", "opus") is False


# ---------------------------------------------------------------- equivalencias
def test_equivalencias_por_capacidad_no_por_modelo():
    lines = model_cap.equivalence_lines("sonnet")
    joined = "\n".join(lines)
    assert "Codex" in joined and "Antigravity" in joined
    assert "estándar" in joined  # nivel de capacidad, no "gpt-5"
    assert model_cap.equivalence_lines("none") == []


# ---------------------------------------------------------------- tools.json
def test_tools_json_incluye_model_cap(tmp_path):
    from tramalia.core.doctor import diagnose, write_snapshot

    _init(tmp_path)
    project.set_agents_model_cap(tmp_path, "sonnet")
    out = write_snapshot(diagnose(tmp_path), tmp_path)
    assert json.loads(out.read_text(encoding="utf-8"))["model_cap"] == "sonnet"


# ---------------------------------------------------------------- AGENTS.md + init
def test_agents_md_declara_regla_portable(tmp_path):
    _init(tmp_path)
    texto = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "model_cap" in texto and "sin ruteo por rol" in texto
    assert "son **tuyos**" in texto  # aclara que los 5 archivos son editables


def test_init_con_model_cap_aplica(tmp_path, monkeypatch):
    import sys

    from tramalia.__main__ import main

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["tramalia", "--plain", "init", "--model-cap", "sonnet"])
    assert main() in (0, None)
    assert _model_of(tmp_path, "revisor") == "sonnet"
    assert project.agents_model_cap(tmp_path) == "sonnet"


# ---------------------------------------------------------------- CLI
def test_cli_agents_cap_invalido_exit_1(tmp_path, monkeypatch):
    import sys

    from tramalia.__main__ import main

    monkeypatch.chdir(tmp_path)
    _init(tmp_path)
    monkeypatch.setattr(sys, "argv", ["tramalia", "--plain", "agents", "cap", "turbo"])
    assert main() == 1
