"""v0.21: tools.json para agentes y habilidades agregadas por URL."""

import json

from tramalia.core.detect import enabled_features
from tramalia.core.doctor import diagnose, write_snapshot
from tramalia.core.habilidades import agregar_habilidad, catalogo_habilidades
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


def test_snapshot_escribe_estado_para_agentes(tmp_path):
    _inicializar(tmp_path)
    salida = write_snapshot(diagnose(tmp_path), tmp_path)
    assert salida is not None and salida.name == "tools.json"
    datos = json.loads(salida.read_text(encoding="utf-8"))
    assert datos["tools"] and all("installed" in herramienta for herramienta in datos["tools"])
    ausentes = [herramienta for herramienta in datos["tools"] if not herramienta["installed"]]
    assert all(herramienta["alternative"] for herramienta in ausentes)


def test_snapshot_no_escribe_sin_init(tmp_path):
    assert write_snapshot(diagnose(tmp_path), tmp_path) is None


def test_agents_md_ordena_consultar_tools_json(tmp_path):
    _inicializar(tmp_path)
    texto = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "tools.json" in texto


def test_agregar_habilidad_por_url_deriva_nombre(tmp_path):
    _inicializar(tmp_path)
    correcto, nombre = agregar_habilidad(tmp_path, "https://github.com/acme/mi-skill.git")
    assert correcto and nombre == "mi-skill"
    catalogo = {habilidad.nombre: habilidad for habilidad in catalogo_habilidades(tmp_path)}
    assert catalogo["mi-skill"].habilitada is True
    assert catalogo["mi-skill"].fuente.startswith("git+https://")


def test_agregar_habilidad_con_alias(tmp_path):
    _inicializar(tmp_path)
    correcto, nombre = agregar_habilidad(
        tmp_path, "https://github.com/acme/x", nombre="alias-corto"
    )
    assert correcto and nombre == "alias-corto"


def test_agregar_habilidad_rechaza_duplicada_y_url_mala(tmp_path):
    _inicializar(tmp_path)
    assert agregar_habilidad(tmp_path, "https://github.com/acme/ponytail") == (
        False,
        "duplicada",
    )
    assert agregar_habilidad(tmp_path, "no-es-una-url") == (False, "url-invalida")
