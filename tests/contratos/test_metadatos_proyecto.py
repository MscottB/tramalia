from pathlib import Path
from typing import Any
import tomllib


RAIZ = Path(__file__).resolve().parents[2]


def cargar_proyecto() -> dict[str, Any]:
    with (RAIZ / "pyproject.toml").open("rb") as archivo:
        return tomllib.load(archivo)


def test_python_minimo_y_clasificadores_beta() -> None:
    proyecto = cargar_proyecto()["project"]
    assert proyecto["requires-python"] == ">=3.11"
    clasificadores = set(proyecto["classifiers"])
    assert "Programming Language :: Python :: 3.10" not in clasificadores
    for version in ("3.11", "3.12", "3.13", "3.14"):
        assert f"Programming Language :: Python :: {version}" in clasificadores


def test_grupo_desarrollo_contiene_herramientas_obligatorias() -> None:
    grupos = cargar_proyecto()["dependency-groups"]
    nombres = {dependencia.split(">=")[0] for dependencia in grupos["desarrollo"]}
    assert {
        "pytest",
        "pytest-cov",
        "pytest-timeout",
        "pytest-repeat",
        "ruff",
        "mypy",
        "build",
        "twine",
    } <= nombres


def test_motor_de_construccion_esta_fijado() -> None:
    assert cargar_proyecto()["build-system"]["requires"] == ["hatchling==1.31.0"]


def test_marcadores_de_pruebas_estan_registrados() -> None:
    configuracion_pytest = cargar_proyecto()["tool"]["pytest"]["ini_options"]
    marcadores = "\n".join(configuracion_pytest["markers"])
    for marcador in (
        "unidad",
        "contrato",
        "integracion",
        "interfaz",
        "opcional",
        "publicacion",
    ):
        assert f"{marcador}:" in marcadores
