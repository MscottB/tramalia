"""v0.19: administración de skills — catálogo (incl. comentadas), toggle, TUI/CLI."""

from tramalia.core.detect import enabled_features
from tramalia.core.scaffold import scaffold
from tramalia.core.skills import catalog, own_skills, set_enabled


def _init(tmp_path):
    scaffold(tmp_path, {
        "project_name": "demo", "stacks": ["python"],
        "features": enabled_features(["python"]),
        "primary_agent": "codex", "reviewer_agent": "claude",
    })
    return tmp_path


# ---------------------------------------------------------------- catálogo
def test_catalog_ve_activas_y_comentadas(tmp_path):
    _init(tmp_path)
    items = {s["name"]: s for s in catalog(tmp_path)}
    assert items["ponytail"]["enabled"] is True          # activa por defecto
    assert items["gstack"]["enabled"] is False           # comentada = disponible
    assert items["anthropic-skills"]["enabled"] is False
    assert all("source" in s and s["source"] for s in items.values())


def test_catalog_marca_instaladas(tmp_path):
    _init(tmp_path)
    (tmp_path / ".tramalia" / "skills" / "gstack").mkdir()
    items = {s["name"]: s for s in catalog(tmp_path)}
    assert items["gstack"]["installed"] is True
    assert items["superpowers"]["installed"] is False


# ---------------------------------------------------------------- toggle
def test_enable_descomenta_y_disable_comenta(tmp_path):
    _init(tmp_path)
    assert set_enabled(tmp_path, "gstack", True)
    items = {s["name"]: s for s in catalog(tmp_path)}
    assert items["gstack"]["enabled"] is True
    # y ahora tomllib también la ve (read_skills / sync la usarían)
    from tramalia.core.skills import read_skills
    assert any(s.get("name") == "gstack" for s in read_skills(tmp_path))
    assert set_enabled(tmp_path, "gstack", False)
    assert {s["name"]: s for s in catalog(tmp_path)}["gstack"]["enabled"] is False


def test_toggle_es_idempotente(tmp_path):
    _init(tmp_path)
    antes = (tmp_path / ".tramalia" / "skills.toml").read_text(encoding="utf-8")
    assert set_enabled(tmp_path, "ponytail", True)       # ya estaba activa
    despues = (tmp_path / ".tramalia" / "skills.toml").read_text(encoding="utf-8")
    assert antes == despues                              # no tocó nada


def test_toggle_nombre_desconocido_no_toca_nada(tmp_path):
    _init(tmp_path)
    antes = (tmp_path / ".tramalia" / "skills.toml").read_text(encoding="utf-8")
    assert set_enabled(tmp_path, "no-existe", True) is False
    assert (tmp_path / ".tramalia" / "skills.toml").read_text(encoding="utf-8") == antes


def test_toggle_conserva_el_resto_del_archivo(tmp_path):
    _init(tmp_path)
    set_enabled(tmp_path, "superpowers", True)
    texto = (tmp_path / ".tramalia" / "skills.toml").read_text(encoding="utf-8")
    # los comentarios descriptivos y las demás skills siguen intactos
    assert "Ponytail:" in texto and "gstack" in texto
    assert 'name   = "superpowers"' in texto             # descomentada limpia


# ---------------------------------------------------------------- propias
def test_own_skills_lee_las_16_con_descripcion(tmp_path):
    _init(tmp_path)
    propias = own_skills(tmp_path)
    assert len(propias) == 16
    assert propias[0]["name"].startswith("01-")
    assert all(s["description"] for s in propias)        # frontmatter leído


def test_own_skills_ignora_clones_externos(tmp_path):
    _init(tmp_path)
    (tmp_path / ".tramalia" / "skills" / "gstack").mkdir()   # clon externo sin NN-
    assert len(own_skills(tmp_path)) == 16
