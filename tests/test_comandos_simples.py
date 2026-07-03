"""Comandos simples: task posicional + defaults desde config.json y current-task.md."""

import json

from tramalia.__main__ import build_parser
from tramalia.core.project import current_task_id, default_agents, resolve_close_args


def _proyecto(tmp_path, task_id=None):
    d = tmp_path / ".tramalia"
    d.mkdir()
    (d / "config.json").write_text(json.dumps(
        {"agents": {"primary": "codex", "reviewer": "claude"}}), encoding="utf-8")
    if task_id:
        (d / "current-task.md").write_text(f"# Tarea\n\n- ID: {task_id}\n", encoding="utf-8")


def test_parser_acepta_task_posicional():
    args = build_parser().parse_args(["close", "TASK-9"])
    assert args.task_pos == "TASK-9"
    args = build_parser().parse_args(["handoff", "TASK-9"])
    assert args.task_pos == "TASK-9"


def test_flag_task_sigue_funcionando():
    args = build_parser().parse_args(["close", "--task", "TASK-9"])
    assert args.task == "TASK-9" and args.task_pos is None


def test_current_task_placeholder_no_cuenta(tmp_path):
    (tmp_path / ".tramalia").mkdir()
    (tmp_path / ".tramalia" / "current-task.md").write_text(
        "- ID: [TASK-XXX — debe existir en specs/tasks.md]\n", encoding="utf-8")
    assert current_task_id(tmp_path) is None


def test_current_task_con_id_real(tmp_path):
    _proyecto(tmp_path, "TASK-042")
    assert current_task_id(tmp_path) == "TASK-042"


def test_defaults_de_config(tmp_path):
    _proyecto(tmp_path)
    assert default_agents(tmp_path) == ("codex", "claude")


def test_resolucion_completa_sin_flags(tmp_path):
    _proyecto(tmp_path, "TASK-042")
    # `tramalia close` a secas: tarea de current-task, agentes de config
    assert resolve_close_args(tmp_path, None, None, None, None) == \
        ("TASK-042", "codex", "claude")


def test_posicional_gana_y_flags_hacen_override(tmp_path):
    _proyecto(tmp_path, "TASK-042")
    task, agent, _ = resolve_close_args(tmp_path, "TASK-7", "TASK-8", "gemini", None)
    assert task == "TASK-7" and agent == "gemini"


def test_sin_nada_cae_a_task_000_sin_colgarse(tmp_path):
    # sin config, sin current-task, sin prompt (ask=None): scripts nunca se cuelgan
    assert resolve_close_args(tmp_path, None, None, None, None) == ("TASK-000", "", "")
