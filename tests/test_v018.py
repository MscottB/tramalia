"""v0.18: docs/ai enriquecido y stack-aware + skills 14-16 + catálogo externo."""

from tramalia.core.detect import enabled_features
from tramalia.core.scaffold import scaffold


def _init(tmp_path, stacks):
    scaffold(
        tmp_path,
        {
            "project_name": "demo",
            "stacks": stacks,
            "features": enabled_features(stacks),
            "primary_agent": "codex",
            "reviewer_agent": "claude",
        },
    )
    return tmp_path / "docs" / "ai"


# ---------------------------------------------------------------- stack-aware
def test_reglas_codigo_incluyen_stack_detectado(tmp_path):
    ai = _init(tmp_path, ["angular", "dotnet"])
    texto = (ai / "02-reglas-codigo.md").read_text(encoding="utf-8")
    assert "Angular" in texto and ".NET" in texto
    assert "{{" not in texto  # sin placeholders sin renderizar


def test_reglas_bd_con_dialecto_del_motor(tmp_path):
    ai = _init(tmp_path, ["dotnet", "postgres", "sqlserver"])
    texto = (ai / "03-reglas-base-datos.md").read_text(encoding="utf-8")
    assert "SQL Server (tsql)" in texto and "PostgreSQL" in texto
    assert "rollback" in texto  # lo innegociable de migraciones


def test_stack_sin_frontend_lo_dice_en_ux(tmp_path):
    ai = _init(tmp_path, ["python"])
    texto = (ai / "11-reglas-ux-ui.md").read_text(encoding="utf-8")
    assert "sin frontend" in texto


def test_stack_python_no_arrastra_reglas_ajenas(tmp_path):
    ai = _init(tmp_path, ["python"])
    texto = (ai / "02-reglas-codigo.md").read_text(encoding="utf-8")
    assert "Python" in texto and "Angular" not in texto


# ---------------------------------------------------------------- nuevos docs/ai
def test_deploy_release_existe_con_checklist(tmp_path):
    ai = _init(tmp_path, ["python"])
    texto = (ai / "12-deploy-release.md").read_text(encoding="utf-8")
    assert "rollback" in texto and "feature flag" in texto
    assert "tramalia close" in texto  # anclado al gobierno


def test_analitica_datos_referencia_metricas(tmp_path):
    ai = _init(tmp_path, ["python"])
    texto = (ai / "13-analitica-datos.md").read_text(encoding="utf-8")
    assert "metrics.json" in texto and "thresholds.json" in texto
    assert "nbstripout" in texto


# ---------------------------------------------------------------- skills 14-16
def test_skills_nuevas_ancladas_a_gobierno(tmp_path):
    _init(tmp_path, ["python"])
    base = tmp_path / ".tramalia" / "skills"
    for skill, ancla in [
        ("14-deploy-gate", "12-deploy-release"),
        ("15-analytics-governance", "metrics.json"),
        ("16-threat-modeling", "STRIDE"),
    ]:
        texto = (base / skill / "SKILL.md").read_text(encoding="utf-8")
        assert ancla in texto, skill
        assert "tramalia close" in texto, skill  # regla de oro: ancladas al cierre


# ---------------------------------------------------------------- catálogo
def test_catalogo_externo_ampliado(tmp_path):
    _init(tmp_path, ["python"])
    texto = (tmp_path / ".tramalia" / "skills.toml").read_text(encoding="utf-8")
    for fuente in ("gstack", "impeccable", "anthropic-skills", "vercel-agent-skills"):
        assert fuente in texto, fuente
