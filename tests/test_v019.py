"""v0.19: administración de skills — catálogo (incl. comentadas), toggle, TUI/CLI."""

from tramalia.core.detect import enabled_features
from tramalia.core.habilidades import (
    catalogo_habilidades,
    fijar_habilitada,
    habilidades_propias,
)
from tramalia.core.scaffold import scaffold


def _inicializar(tmp_path):
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


# ---------------------------------------------------------------- catálogo
def test_catalog_ve_activas_y_comentadas(tmp_path):
    _inicializar(tmp_path)
    catalogo = {habilidad.nombre: habilidad for habilidad in catalogo_habilidades(tmp_path)}
    assert catalogo["ponytail"].habilitada is True
    assert catalogo["gstack"].habilitada is False
    assert catalogo["anthropic-skills"].habilitada is False
    assert all(habilidad.fuente for habilidad in catalogo.values())


def test_catalog_marca_instaladas(tmp_path):
    _inicializar(tmp_path)
    (tmp_path / ".tramalia" / "habilidades" / "gstack").mkdir()
    catalogo = {habilidad.nombre: habilidad for habilidad in catalogo_habilidades(tmp_path)}
    assert catalogo["gstack"].instalada is True
    assert catalogo["superpowers"].instalada is False


# ---------------------------------------------------------------- toggle
def test_enable_descomenta_y_disable_comenta(tmp_path):
    _inicializar(tmp_path)
    assert fijar_habilitada(tmp_path, "gstack", True)
    catalogo = {habilidad.nombre: habilidad for habilidad in catalogo_habilidades(tmp_path)}
    assert catalogo["gstack"].habilitada is True
    from tramalia.core.habilidades import leer_habilidades

    assert any(habilidad.nombre == "gstack" for habilidad in leer_habilidades(tmp_path))
    assert fijar_habilitada(tmp_path, "gstack", False)
    catalogo = {habilidad.nombre: habilidad for habilidad in catalogo_habilidades(tmp_path)}
    assert catalogo["gstack"].habilitada is False


def test_toggle_es_idempotente(tmp_path):
    _inicializar(tmp_path)
    ruta = tmp_path / ".tramalia" / "habilidades.toml"
    antes = ruta.read_text(encoding="utf-8")
    assert fijar_habilitada(tmp_path, "ponytail", True)
    despues = ruta.read_text(encoding="utf-8")
    assert antes == despues  # no tocó nada


def test_toggle_nombre_desconocido_no_toca_nada(tmp_path):
    _inicializar(tmp_path)
    ruta = tmp_path / ".tramalia" / "habilidades.toml"
    antes = ruta.read_text(encoding="utf-8")
    assert fijar_habilitada(tmp_path, "no-existe", True) is False
    assert ruta.read_text(encoding="utf-8") == antes


def test_toggle_conserva_el_resto_del_archivo(tmp_path):
    _inicializar(tmp_path)
    fijar_habilitada(tmp_path, "superpowers", True)
    texto = (tmp_path / ".tramalia" / "habilidades.toml").read_text(encoding="utf-8")
    # los comentarios descriptivos y las demás skills siguen intactos
    assert "Ponytail:" in texto and "gstack" in texto
    assert 'nombre = "superpowers"' in texto


# ---------------------------------------------------------------- propias
def test_own_skills_lee_las_16_con_descripcion(tmp_path):
    _inicializar(tmp_path)
    propias = habilidades_propias(tmp_path)
    assert len(propias) == 16
    assert propias[0]["nombre"].startswith("01-")
    assert all(habilidad["descripcion"] for habilidad in propias)


def test_own_skills_ignora_clones_externos(tmp_path):
    _inicializar(tmp_path)
    (tmp_path / ".tramalia" / "habilidades" / "gstack").mkdir()
    assert len(habilidades_propias(tmp_path)) == 16
