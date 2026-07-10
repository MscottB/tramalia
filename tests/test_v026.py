"""v0.26: estilo arquitectónico declarado (no inferido), CRUD/Transaction Script
por defecto — sin tocar scaffold.py: es contenido de plantilla, no lógica."""

from pathlib import Path

from tramalia.core.detect import enabled_features
from tramalia.core.scaffold import scaffold

DOCS = Path(__file__).resolve().parents[1] / "docs"


def _init(tmp_path, stacks=("python",)):
    scaffold(tmp_path, {
        "project_name": "demo", "stacks": list(stacks),
        "features": enabled_features(list(stacks)),
        "primary_agent": "codex", "reviewer_agent": "claude",
    })
    return tmp_path


# ---------------------------------------------------------------- 01-arquitectura
def test_01_arquitectura_pide_declarar_estilo(tmp_path):
    root = _init(tmp_path)
    texto = (root / "docs" / "ai" / "01-arquitectura.md").read_text(encoding="utf-8")
    assert "Estilo arquitectónico de este proyecto" in texto
    for estilo in ("CRUD", "Transaction Script", "Domain-Driven Design", "Data-Oriented"):
        assert estilo in texto, estilo


def test_01_arquitectura_default_es_simple_no_ddd(tmp_path):
    root = _init(tmp_path)
    texto = (root / "docs" / "ai" / "01-arquitectura.md").read_text(encoding="utf-8")
    assert "el más simple que resuelva la tarea" in texto
    assert "no asumas DDD/Hexagonal por defecto" in texto.lower() or \
           "no asumas ddd/hexagonal por defecto" in texto.lower()


def test_reglas_dependencia_condicionada_al_estilo(tmp_path):
    root = _init(tmp_path)
    texto = (root / "docs" / "ai" / "01-arquitectura.md").read_text(encoding="utf-8")
    # la regla de dependencia (hexagonal/DDD-flavored) ya no aplica a todo proyecto
    idx = texto.index("Reglas de dependencia")
    bloque = texto[idx:idx + 300]
    assert "solo si el estilo declarado es" in bloque.lower()


def test_dos_stacks_distintos_no_cambian_el_estilo_sugerido(tmp_path, tmp_path_factory):
    """El estilo NO se infiere del stack (es decisión de negocio) — dos proyectos
    con stacks distintos deben recibir exactamente el mismo texto de la sección."""
    a = _init(tmp_path_factory.mktemp("a"), stacks=("python",))
    b = _init(tmp_path_factory.mktemp("b"), stacks=("angular", "dotnet", "postgres"))
    ta = (a / "docs" / "ai" / "01-arquitectura.md").read_text(encoding="utf-8")
    tb = (b / "docs" / "ai" / "01-arquitectura.md").read_text(encoding="utf-8")
    assert ta == tb   # archivo estático: idéntico sin importar el stack detectado


# ---------------------------------------------------------------- AGENTS.md guardrail
def test_agents_md_guardrail_anti_sobreingenieria(tmp_path):
    root = _init(tmp_path)
    texto = (root / "AGENTS.md").read_text(encoding="utf-8")
    assert "01-arquitectura.md" in texto
    assert "no metas capas de dominio" in texto.lower()


# ---------------------------------------------------------------- idempotencia (--adopt)
def test_adopt_no_reescribe_01_arquitectura_existente(tmp_path):
    """--adopt solo intercepta AGENTS.md/CLAUDE.md/.mcp.json — 01-arquitectura.md
    de un proyecto ya inicializado (con contenido propio) queda intacto."""
    ai = tmp_path / "docs" / "ai"
    ai.mkdir(parents=True)
    propio = "# 01 — Arquitectura\n\nTexto propio del equipo, sin la sección nueva.\n"
    (ai / "01-arquitectura.md").write_text(propio, encoding="utf-8")
    scaffold(tmp_path, {
        "project_name": "demo", "stacks": ["python"],
        "features": enabled_features(["python"]),
        "primary_agent": "codex", "reviewer_agent": "claude", "adopt": True,
    })
    assert (ai / "01-arquitectura.md").read_text(encoding="utf-8") == propio


# ---------------------------------------------------------------- docs del sitio
def test_pagina_patrones_arquitectura_existe_es_en():
    assert (DOCS / "patrones-arquitectura.md").is_file()
    assert (DOCS / "patrones-arquitectura.en.md").is_file()
    es = (DOCS / "patrones-arquitectura.md").read_text(encoding="utf-8")
    en = (DOCS / "patrones-arquitectura.en.md").read_text(encoding="utf-8")
    for term in ("CRUD", "Transaction Script", "Domain-Driven Design", "Data-Oriented"):
        assert term in es and term in en


def test_patrones_arquitectura_aclara_que_no_se_infiere_del_stack():
    es = (DOCS / "patrones-arquitectura.md").read_text(encoding="utf-8")
    assert "no infiere el estilo por el stack" in es.lower()


def test_glosario_incluye_terminos_nuevos():
    es = (DOCS / "glosario.md").read_text(encoding="utf-8")
    en = (DOCS / "glosario.en.md").read_text(encoding="utf-8")
    for term in ("CRUD", "DDD", "Hexagonal", "Transaction Script", "Data-Oriented"):
        assert term in es, term
        assert term in en, term
    assert "Lenguaje ubicuo" in es and "Ubiquitous language" in en


def test_nav_incluye_patrones_arquitectura():
    mkdocs = (Path(__file__).resolve().parents[1] / "mkdocs.yml").read_text(encoding="utf-8")
    assert "patrones-arquitectura.md" in mkdocs
    assert "Patrones de arquitectura: Architecture patterns" in mkdocs
