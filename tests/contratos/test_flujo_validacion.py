from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FLUJO_VALIDACION = RAIZ / ".github" / "workflows" / "validacion.yml"


def test_validacion_ejecuta_matriz_calidad_y_paquete() -> None:
    contenido = FLUJO_VALIDACION.read_text(encoding="utf-8")
    for version in ("3.11", "3.12", "3.13", "3.14"):
        assert f'"{version}"' in contenido
    for trabajo in ("nucleo:", "calidad:", "paquete:"):
        assert trabajo in contenido
    assert "uv run --no-sync pytest -q" in contenido
    assert "uv run --no-sync ruff check ." in contenido
    assert "uv run --no-sync ruff format --check ." in contenido
    assert "uv run --no-sync twine check dist/*.whl dist/*.tar.gz" in contenido
    assert "SOURCE_DATE_EPOCH" in contenido
    assert "dist/segunda" in contenido


def test_acciones_estan_fijadas_por_sha() -> None:
    contenido = FLUJO_VALIDACION.read_text(encoding="utf-8")
    assert "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0" in contenido
    assert "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1" in contenido
    assert "astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990" in contenido
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in contenido
    assert 'version: "0.11.28"' in contenido


def test_no_queda_publicacion_que_reconstruya_fuera_de_validacion() -> None:
    assert not (RAIZ / ".github" / "workflows" / "publish.yml").exists()
