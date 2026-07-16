"""Contrato estructural para la configuracion Semgrep local."""

from __future__ import annotations

import tomllib
from collections.abc import Iterator, Mapping
from pathlib import Path
from urllib.parse import urlparse

from ruamel.yaml import YAML

RAIZ = Path(__file__).resolve().parents[2]
RUTA_CONFIGURACION = RAIZ / "configuracion" / "semgrep" / "seguridad-python.yml"
RUTA_EMPAQUETADA = (
    RAIZ
    / "tramalia"
    / "templates"
    / "project"
    / ".tramalia"
    / "configuracion"
    / "semgrep"
    / "seguridad-python.yml"
)

IDS_REQUERIDOS = {
    "tramalia.python.eval-exec",
    "tramalia.python.subprocess-shell",
    "tramalia.python.sistema-shell",
    "tramalia.python.proceso-sin-timeout",
    "tramalia.python.pickle-inseguro",
    "tramalia.python.yaml-inseguro",
    "tramalia.python.mktemp-inseguro",
    "tramalia.python.tls-sin-verificar",
    "tramalia.python.red-sin-timeout",
    "tramalia.python.extraccion-insegura",
    "tramalia.python.mcp-stdout-directo",
}
METADATOS_REQUERIDOS = {
    "categoria",
    "cwe",
    "tecnologia",
    "control_tramalia",
    "referencia",
}
EXCLUSIONES_PROCESOS = [
    "tests/contratos/test_metadatos_evidencia_v1.py",
    "tests/integracion/test_habilidades_git.py",
    "tests/test_v029.py",
    "tests/test_v031.py",
]
RAZON_EXCLUSION = "tests invocan procesos falsos o efimeros"
CLAVES_CARGA_REMOTA = {
    "config",
    "configs",
    "extends",
    "registry",
    "remote",
    "remote-config",
    "remote_config",
}
DOMINIOS_REFERENCIA_OFICIAL = {
    "cwe.mitre.org",
    "docs.python.org",
    "owasp.org",
    "semgrep.dev",
}


def _cargar_configuracion() -> dict[str, object]:
    yaml = YAML(typ="safe")
    configuracion = yaml.load(RUTA_CONFIGURACION.read_text(encoding="utf-8"))
    assert isinstance(configuracion, dict)
    return configuracion


def _recorrer_pares(valor: object) -> Iterator[tuple[str, object]]:
    if isinstance(valor, Mapping):
        for clave, contenido in valor.items():
            yield str(clave), contenido
            yield from _recorrer_pares(contenido)
    elif isinstance(valor, list):
        for elemento in valor:
            yield from _recorrer_pares(elemento)


def test_configuracion_es_local_y_parseable_con_ruamel() -> None:
    configuracion = _cargar_configuracion()

    assert set(configuracion) == {"rules"}
    assert isinstance(configuracion["rules"], list)
    for clave, valor in _recorrer_pares(configuracion):
        assert clave not in CLAVES_CARGA_REMOTA
        if clave == "metrics":
            assert valor != "on"


def test_reglas_tienen_ids_y_metadatos_exactos() -> None:
    reglas = _cargar_configuracion()["rules"]
    assert isinstance(reglas, list)
    assert {regla["id"] for regla in reglas} == IDS_REQUERIDOS

    for regla in reglas:
        assert regla["severity"] == "ERROR"
        assert regla["languages"] == ["python"]
        mensaje = regla["message"]
        assert isinstance(mensaje, str) and mensaje.strip()
        assert mensaje.split(maxsplit=1)[0] in {"Define", "Evita", "Mantén", "Usa", "Valida"}

        metadatos = regla["metadata"]
        assert METADATOS_REQUERIDOS <= set(metadatos)
        assert all(metadatos[clave] for clave in METADATOS_REQUERIDOS)
        referencia = urlparse(metadatos["referencia"])
        assert referencia.scheme == "https"
        assert referencia.hostname in DOMINIOS_REFERENCIA_OFICIAL


def test_exclusiones_solo_pertenecen_a_proceso_sin_timeout() -> None:
    reglas = _cargar_configuracion()["rules"]
    assert isinstance(reglas, list)

    for regla in reglas:
        metadatos = regla["metadata"]
        if regla["id"] == "tramalia.python.proceso-sin-timeout":
            assert regla["paths"] == {"exclude": EXCLUSIONES_PROCESOS}
            assert metadatos["razon_exclusion"] == RAZON_EXCLUSION
        else:
            assert "paths" not in regla
            assert "razon_exclusion" not in metadatos


def test_copia_empaquetada_es_identica_byte_por_byte() -> None:
    assert RUTA_CONFIGURACION.read_bytes() == RUTA_EMPAQUETADA.read_bytes()


def test_ruamel_yaml_esta_fijado_directamente_en_seguridad() -> None:
    pyproject = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["dependency-groups"]["seguridad"].count("ruamel-yaml==0.19.1") == 1
