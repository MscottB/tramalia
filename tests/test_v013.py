"""v0.13: criterio de herramientas (local primero), markitdown y desempates."""

from pathlib import Path

from tramalia.core.scaffold import scaffold
from tramalia.core.tools import REGISTRY

RAIZ = Path(__file__).resolve().parents[1]
DOCS = RAIZ / "docs"


# ---------------------------------------------------------------- registry
def test_markitdown_en_registry_como_contexto():
    tool = next(t for t in REGISTRY if t.key == "markitdown")
    assert tool.category == "feature"
    assert tool.feature == "context"
    assert "markitdown[all]" in tool.install_hint


def test_notebooklm_no_esta_en_registry():
    # corre vía npx y es cloud: se documenta, no se detecta (doctor honesto).
    assert not any("notebooklm" in t.key for t in REGISTRY)


# ---------------------------------------------------------------- plantilla
def test_agents_md_tiene_criterio_local_primero(tmp_path):
    scaffold(
        tmp_path,
        {
            "project_name": "demo",
            "stacks": ["python"],
            "features": [],
            "primary_agent": "codex",
            "reviewer_agent": "claude",
        },
    )
    texto = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "local primero" in texto
    assert "prosigue con" in texto  # degradación normal si falta la herramienta
    assert "una sola" in texto  # una única memoria activa


# ---------------------------------------------------------------- docs
def test_criterio_documentado_en_ambos_idiomas():
    for nombre, marca in [
        ("interop-contexto.md", "El criterio"),
        ("interop-contexto.en.md", "The criterion"),
        ("interop-memoria.md", "El criterio"),
        ("interop-memoria.en.md", "The criterion"),
    ]:
        texto = (DOCS / nombre).read_text(encoding="utf-8")
        assert marca in texto, nombre


def test_eficiencia_ponytail_antes_que_caveman():
    texto = (DOCS / "interop-memoria.md").read_text(encoding="utf-8")
    assert texto.index("Ponytail") < texto.index("caveman")
    assert "`lite`" in texto  # nivel recomendado
