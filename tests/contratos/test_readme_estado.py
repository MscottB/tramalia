from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def test_readmes_muestran_validacion_real_y_no_un_conteo_estatico() -> None:
    for nombre in ("README.md", "README.en.md"):
        contenido = (RAIZ / nombre).read_text(encoding="utf-8")
        assert "tests-250%20passing" not in contenido
        assert "actions/workflows/validacion.yml/badge.svg" in contenido
        assert "actions/workflows/validacion.yml" in contenido
