import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FLUJO_VALIDACION = RAIZ / ".github" / "workflows" / "validacion.yml"
URL_IMAGEN_VALIDACION = (
    "https://github.com/MscottB/tramalia/actions/workflows/validacion.yml/badge.svg"
)
URL_DESTINO_VALIDACION = "https://github.com/MscottB/tramalia/actions/workflows/validacion.yml"
BADGE_ESPERADO_ES = f"[![Validación]({URL_IMAGEN_VALIDACION})]({URL_DESTINO_VALIDACION})"
BADGE_ESPERADO_EN = f"[![Validation]({URL_IMAGEN_VALIDACION})]({URL_DESTINO_VALIDACION})"
BADGES_ESPERADOS = {
    "README.md": BADGE_ESPERADO_ES,
    "README.en.md": BADGE_ESPERADO_EN,
}
PATRON_SEPARADOR_CABECERA = re.compile(r"(?m)^---[ \t]*\r?$")
PATRON_BADGE = re.compile(
    r"^\[!\[(?P<alternativo>[^\]]+)\]\((?P<imagen>[^)]+)\)\]"
    r"\((?P<destino>[^)]+)\)$"
)
TERMINO_PRUEBAS = r"(?<![A-Za-z])(?:tests?|pruebas?)(?![A-Za-z])"
PATRON_CONTEO_FIJO = re.compile(
    rf"(?:{TERMINO_PRUEBAS}[^0-9\r\n]{{0,30}}\d+"
    rf"|\d+[^0-9\r\n]{{0,30}}{TERMINO_PRUEBAS})",
    re.IGNORECASE,
)


def _leer_cabecera(nombre: str) -> str:
    contenido = (RAIZ / nombre).read_text(encoding="utf-8")
    partes = PATRON_SEPARADOR_CABECERA.split(contenido, maxsplit=1)
    assert len(partes) == 2, f"{nombre} no contiene el separador de cabecera"
    return partes[0]


def test_flujo_validacion_existe() -> None:
    assert FLUJO_VALIDACION.is_file()


def test_readmes_muestran_exactamente_un_badge_esperado() -> None:
    for nombre, badge_esperado in BADGES_ESPERADOS.items():
        lineas = _leer_cabecera(nombre).splitlines()
        assert lineas.count(badge_esperado) == 1, (
            f"{nombre} debe contener exactamente una vez {badge_esperado!r}"
        )


def test_readmes_comparten_urls_de_validacion() -> None:
    urls_por_readme = {}
    for nombre in BADGES_ESPERADOS:
        coincidencias = [
            coincidencia
            for linea in _leer_cabecera(nombre).splitlines()
            if (coincidencia := PATRON_BADGE.fullmatch(linea))
            and coincidencia.group("imagen") == URL_IMAGEN_VALIDACION
        ]
        assert len(coincidencias) == 1, f"{nombre} debe tener un badge con la imagen de validacion"
        urls_por_readme[nombre] = (
            coincidencias[0].group("imagen"),
            coincidencias[0].group("destino"),
        )

    assert set(urls_por_readme.values()) == {(URL_IMAGEN_VALIDACION, URL_DESTINO_VALIDACION)}


def test_cabeceras_no_fijan_un_conteo_de_pruebas() -> None:
    for nombre in BADGES_ESPERADOS:
        coincidencia = PATRON_CONTEO_FIJO.search(_leer_cabecera(nombre))
        assert coincidencia is None, (
            f"{nombre} fija un conteo de pruebas: {coincidencia.group(0)!r}"
        )


def test_patron_reconoce_formatos_de_conteo_fijo() -> None:
    for ejemplo in (
        "tests-258%20passing",
        "258 tests passing",
        "tests: 258",
        "pruebas-258%20aprobadas",
        "258 pruebas aprobadas",
        "pruebas: 258",
    ):
        assert PATRON_CONTEO_FIJO.search(ejemplo), ejemplo
