"""v0.12: i18n, guard de init, tareas por horizonte, agentes CLI y analítica."""

import argparse
import json

from tramalia import i18n
from tramalia.core import governance
from tramalia.core.detect import detect_stack, enabled_features
from tramalia.core.doctor import diagnose
from tramalia.core.project import is_initialized, task_description
from tramalia.core.scaffold import scaffold
from tramalia.core.tools import REGISTRY, relevant_tools


# ---------------------------------------------------------------- i18n
def test_catalogos_es_en_mismas_claves():
    es = json.loads((i18n._DIR / "es.json").read_text(encoding="utf-8"))
    en = json.loads((i18n._DIR / "en.json").read_text(encoding="utf-8"))
    assert set(es) == set(en), set(es) ^ set(en)


def test_t_traduce_y_cae_a_clave(monkeypatch):
    i18n.set_lang("en")
    assert i18n.t("menu.quit") == "quit"
    i18n.set_lang("es")
    assert i18n.t("menu.quit") == "salir"
    assert i18n.t("clave.inexistente") == "clave.inexistente"
    i18n.set_lang("es")  # dejar es para el resto de la suite


def test_env_manda_sobre_locale(monkeypatch):
    monkeypatch.setenv("TRAMALIA_LANG", "en")
    assert i18n.detect_lang() == "en"
    monkeypatch.setenv("TRAMALIA_LANG", "es")
    assert i18n.detect_lang() == "es"


# ---------------------------------------------------------------- guard init
def test_close_bloqueado_sin_init(tmp_path, monkeypatch):
    from tramalia.cli import commands
    monkeypatch.chdir(tmp_path)
    args = argparse.Namespace(task_pos="TASK-1", task=None, agent=None,
                              reviewer=None, model=None, allow_fail=False,
                              engram=False)
    assert commands.cmd_close(args) == 1
    assert not (tmp_path / ".tramalia" / "evidence").exists()


def test_is_initialized(tmp_path):
    assert is_initialized(tmp_path) is False
    (tmp_path / ".tramalia").mkdir()
    assert is_initialized(tmp_path) is True


# ---------------------------------------------------------------- tareas
def _init(tmp_path, stacks):
    scaffold(tmp_path, {
        "project_name": "demo", "stacks": stacks,
        "features": enabled_features(stacks),
        "primary_agent": "codex", "reviewer_agent": "claude",
    })


def test_tasks_template_con_horizonte(tmp_path):
    _init(tmp_path, ["python"])
    texto = (tmp_path / "specs" / "tasks.md").read_text(encoding="utf-8")
    assert "Horizonte:" in texto and "Estado:" in texto
    assert "Re-planificar es editar este archivo" in texto


def test_task_description_extrae_seccion(tmp_path):
    (tmp_path / "specs").mkdir()
    (tmp_path / "specs" / "tasks.md").write_text(
        "# Tasks\n\n## TASK-001 — Login\n- Alcance: pantalla\n\n## TASK-002 — Otro\n- x\n",
        encoding="utf-8")
    desc = task_description(tmp_path, "TASK-001")
    assert desc and "Login" in desc and "TASK-002" not in desc
    assert task_description(tmp_path, "TASK-999") is None


# ---------------------------------------------------------------- agentes CLI
def test_agentes_cli_detectables_y_no_bloqueantes(tmp_path):
    agentes = {t.key for t in REGISTRY if t.category == "agent"}
    assert {"claude", "codex", "antigravity", "gemini", "opencode"} <= agentes
    keys = {t.key for t in relevant_tools([], ())}
    assert "claude" in keys  # siempre visibles
    rep = diagnose(tmp_path)
    assert all(s.tool.category != "agent" for s in rep.missing_blocking)


# ---------------------------------------------------------------- analítica
def test_detecta_databricks_y_notebooks(tmp_path):
    (tmp_path / "databricks.yml").write_text("bundle:\n", encoding="utf-8")
    (tmp_path / "analisis.ipynb").write_text("{}", encoding="utf-8")
    stack = detect_stack(tmp_path)
    assert "databricks" in stack and "notebooks" in stack
    assert "databricks" in enabled_features(stack)


def test_mise_toml_analitica(tmp_path):
    _init(tmp_path, ["python", "databricks", "notebooks"])
    mise = (tmp_path / "mise.toml").read_text(encoding="utf-8")
    assert "databricks bundle validate" in mise
    assert "--dialect databricks" in mise
    assert "nbstripout --verify" in mise
    assert "bundle" in governance._GATE_ORDER
