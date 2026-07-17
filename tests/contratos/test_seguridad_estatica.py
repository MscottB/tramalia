"""Contrato estructural para las configuraciones Semgrep y Gitleaks."""

from __future__ import annotations

import re
import tomllib
from collections.abc import Iterator, Mapping
from pathlib import Path
from urllib.parse import urlparse

import pytest
from ruamel.yaml import YAML

RAIZ = Path(__file__).resolve().parents[2]
RUTA_CONFIGURACION = RAIZ / "configuracion" / "semgrep" / "seguridad-python.yml"
RUTA_CONFIGURACION_GITLEAKS = RAIZ / ".gitleaks.toml"
RUTA_EXCEPCIONES_GITLEAKS = RAIZ / "docs" / "seguridad" / "excepciones-gitleaks.md"
RUTA_IGNORE_GITLEAKS = RAIZ / ".gitleaksignore"
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
DESCRIPCION_ALLOWLIST_GITLEAKS = (
    "Directorios generados y dependencias; el código fuente no se excluye"
)
PATRON_ALLOWLIST_GITLEAKS = (
    r"(^|/)(\.git|\.venv|node_modules|site|\.artefactos|dist|build|\.pytest_cache|"
    r"\.mypy_cache|\.ruff_cache|__pycache__)(/|$)"
)
PATRONES_PROHIBIDOS_GITLEAKS = (
    r"(^|/)\.env($|/)",
    r"private.*key",
    r"token",
    r"(^|/)tramalia(/|$)",
    r"(^|/)scripts(/|$)",
    r"(^|/)tests(/|$)",
    r"(^|/)docs(/|$)",
    r"(^|/)\.github(/|$)",
)
RUTAS_CON_COMANDOS_GITLEAKS = (
    RAIZ / ".github" / "workflows",
    RAIZ / "tramalia",
    RAIZ / "scripts",
    RAIZ / "docs" / "seguridad",
)
SUFIJOS_TEXTO_GITLEAKS = {
    ".cjs",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
PATRON_COMANDO_GITLEAKS_DIR = re.compile(
    r"[^\s\"'`]*gitleaks(?:\.exe)?[\"']?\s+dir\b[^\r\n]*",
    re.IGNORECASE,
)
PATRON_LIMITE_GITLEAKS_DIR = re.compile(
    r"(?<!\S)--max-target-megabytes(?!\S)\s+([0-9]+)(?=$|\s|[\"'`;,\)\]}])"
)
PATRON_FINGERPRINT_GITLEAKS = re.compile(
    r"(?P<commit>[0-9a-fA-F]{40}):(?P<ruta>.+):(?P<regla>[^:]+):"
    r"(?P<linea>[1-9][0-9]*)"
)


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


def _validar_configuracion_gitleaks(configuracion: dict[str, object]) -> None:
    assert set(configuracion) == {"extend", "allowlists"}
    assert configuracion["extend"] == {"useDefault": True}
    assert configuracion["allowlists"] == [
        {
            "description": DESCRIPCION_ALLOWLIST_GITLEAKS,
            "paths": [PATRON_ALLOWLIST_GITLEAKS],
        }
    ]


def _archivos_con_comandos_gitleaks() -> Iterator[Path]:
    for ruta in RUTAS_CON_COMANDOS_GITLEAKS:
        if ruta.is_file():
            yield ruta
        elif ruta.is_dir():
            yield from (
                archivo
                for archivo in ruta.rglob("*")
                if archivo.is_file() and archivo.suffix in SUFIJOS_TEXTO_GITLEAKS
            )


def _filas_excepciones_gitleaks(contenido: str) -> dict[str, list[str]]:
    filas: dict[str, list[str]] = {}
    for linea in contenido.splitlines():
        celdas = [celda.strip() for celda in linea.strip().strip("|").split("|")]
        if len(celdas) == 5 and celdas[0] not in {"Fingerprint", "---"}:
            filas[celdas[0].strip("`")] = celdas
    return filas


def _extraer_comandos_gitleaks_dir(archivo: Path) -> Iterator[str]:
    contenido = archivo.read_text(encoding="utf-8", errors="ignore")
    for linea in contenido.splitlines():
        linea_activa = linea.lstrip()
        if linea_activa.startswith(("#", "//", "<!--")):
            continue
        if archivo.suffix == ".md" and not re.match(
            r"^(?:&\s+)?[^\s\"'`]*gitleaks(?:\.exe)?[\"']?\s+dir\b",
            linea_activa,
            re.IGNORECASE,
        ):
            continue
        linea_activa = linea.split("#", maxsplit=1)[0]
        linea_activa = re.split(r"\s//", linea_activa, maxsplit=1)[0]
        linea_activa = linea_activa.split("<!--", maxsplit=1)[0]
        yield from (
            coincidencia.group(0)
            for coincidencia in PATRON_COMANDO_GITLEAKS_DIR.finditer(linea_activa)
        )


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
    ids = [regla["id"] for regla in reglas]
    assert len(reglas) == len(IDS_REQUERIDOS)
    assert len(ids) == len(set(ids))
    assert set(ids) == IDS_REQUERIDOS

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


def test_ids_duplicados_se_rechazan(monkeypatch: pytest.MonkeyPatch) -> None:
    configuracion = _cargar_configuracion()
    reglas = configuracion["rules"]
    assert isinstance(reglas, list)
    configuracion_duplicada = {"rules": [*reglas, reglas[0]]}
    monkeypatch.setitem(globals(), "_cargar_configuracion", lambda: configuracion_duplicada)

    with pytest.raises(AssertionError):
        test_reglas_tienen_ids_y_metadatos_exactos()


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


def test_gitleaks_extiende_reglas_y_solo_excluye_directorios_generados() -> None:
    configuracion = tomllib.loads(RUTA_CONFIGURACION_GITLEAKS.read_text(encoding="utf-8"))

    _validar_configuracion_gitleaks(configuracion)


@pytest.mark.parametrize("patron_prohibido", PATRONES_PROHIBIDOS_GITLEAKS)
def test_gitleaks_rechaza_allowlists_de_secretos_o_codigo_fuente(
    patron_prohibido: str,
) -> None:
    configuracion_insegura = {
        "extend": {"useDefault": True},
        "allowlists": [
            {
                "description": DESCRIPCION_ALLOWLIST_GITLEAKS,
                "paths": [PATRON_ALLOWLIST_GITLEAKS, patron_prohibido],
            }
        ],
    }

    with pytest.raises(AssertionError):
        _validar_configuracion_gitleaks(configuracion_insegura)


def test_excepciones_gitleaks_son_individuales_y_documentadas() -> None:
    contenido = RUTA_EXCEPCIONES_GITLEAKS.read_text(encoding="utf-8")
    assert "`gitleaks git`" in contenido
    assert "commits" in contenido
    assert "`gitleaks dir .`" in contenido
    assert "árbol de trabajo" in contenido
    assert "sin confirmar" in contenido
    assert "ninguno sustituye al otro" in contenido

    if not RUTA_IGNORE_GITLEAKS.exists():
        assert "No hay excepciones activas" in contenido
        return

    fingerprints = [
        linea.strip()
        for linea in RUTA_IGNORE_GITLEAKS.read_text(encoding="utf-8").splitlines()
        if linea.strip() and not linea.lstrip().startswith("#")
    ]
    filas = _filas_excepciones_gitleaks(contenido)
    assert set(filas) == set(fingerprints)

    for fingerprint in fingerprints:
        coincidencia = PATRON_FINGERPRINT_GITLEAKS.fullmatch(fingerprint)
        assert coincidencia is not None
        ruta = coincidencia.group("ruta")
        regla = coincidencia.group("regla")
        assert ruta.strip()
        assert regla.strip()
        _, ruta_documentada, regla_documentada, razon, revision = filas[fingerprint]
        assert ruta_documentada.strip("`") == ruta
        assert regla_documentada.strip("`") == regla
        assert razon.strip("` ")
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", revision)


def test_todos_los_comandos_dir_limitan_archivos_a_diez_megabytes() -> None:
    comandos = [
        comando
        for archivo in _archivos_con_comandos_gitleaks()
        for comando in _extraer_comandos_gitleaks_dir(archivo)
    ]

    assert comandos
    for comando in comandos:
        valores = PATRON_LIMITE_GITLEAKS_DIR.findall(comando)
        assert valores == ["10"]


def _usar_archivo_comandos_temporal(
    monkeypatch: pytest.MonkeyPatch, ruta: Path, contenido: str
) -> None:
    ruta.write_text(contenido, encoding="utf-8")
    monkeypatch.setitem(globals(), "_archivos_con_comandos_gitleaks", lambda: iter((ruta,)))


@pytest.mark.parametrize(
    "contenido",
    (
        "gitleaks dir . --redact --max-target-megabytes 100 --exit-code 1",
        "gitleaks dir . --redact --max-target-megabytes 1024 --exit-code 1",
        "gitleaks dir . --redact # --max-target-megabytes 10",
        "\n".join(
            (
                "gitleaks dir . --redact --max-target-megabytes 10",
                "gitleaks dir .",
            )
        ),
    ),
)
def test_comandos_dir_con_limite_invalido_se_rechazan(
    contenido: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _usar_archivo_comandos_temporal(monkeypatch, tmp_path / "comandos.md", contenido)

    with pytest.raises(AssertionError):
        test_todos_los_comandos_dir_limitan_archivos_a_diez_megabytes()


def test_lineas_que_solo_son_comentarios_no_cuentan_como_comandos(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    contenido = "\n".join(
        (
            "gitleaks dir . --redact --max-target-megabytes 10",
            "# gitleaks dir . --redact",
            "// gitleaks dir . --exit-code 1",
        )
    )
    _usar_archivo_comandos_temporal(monkeypatch, tmp_path / "comentarios.md", contenido)

    test_todos_los_comandos_dir_limitan_archivos_a_diez_megabytes()


@pytest.mark.parametrize(
    ("fingerprint", "ruta", "regla"),
    (
        ("abc:ruta.py:generic-api-key:1", "ruta.py", "generic-api-key"),
        (f"{'a' * 40}::generic-api-key:1", "", "generic-api-key"),
        (f"{'a' * 40}:ruta.py::1", "ruta.py", ""),
        (f"{'a' * 40}:ruta.py:generic-api-key:0", "ruta.py", "generic-api-key"),
    ),
)
def test_fingerprints_invalidos_se_rechazan(
    fingerprint: str,
    ruta: str,
    regla: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    ruta_ignore = tmp_path / ".gitleaksignore"
    ruta_ignore.write_text(f"{fingerprint}\n", encoding="utf-8")
    ruta_documento = tmp_path / "excepciones-gitleaks.md"
    contenido = RUTA_EXCEPCIONES_GITLEAKS.read_text(encoding="utf-8").replace(
        "No hay excepciones activas.",
        f"| `{fingerprint}` | `{ruta}` | `{regla}` | falso positivo | 2026-07-17 |",
    )
    ruta_documento.write_text(contenido, encoding="utf-8")
    monkeypatch.setitem(globals(), "RUTA_IGNORE_GITLEAKS", ruta_ignore)
    monkeypatch.setitem(globals(), "RUTA_EXCEPCIONES_GITLEAKS", ruta_documento)

    with pytest.raises(AssertionError):
        test_excepciones_gitleaks_son_individuales_y_documentadas()


def test_fingerprint_completo_y_documentado_se_admite(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fingerprint = f"{'a' * 40}:docs/ejemplo.md:generic-api-key:1"
    ruta_ignore = tmp_path / ".gitleaksignore"
    ruta_ignore.write_text(f"{fingerprint}\n", encoding="utf-8")
    ruta_documento = tmp_path / "excepciones-gitleaks.md"
    contenido = RUTA_EXCEPCIONES_GITLEAKS.read_text(encoding="utf-8").replace(
        "No hay excepciones activas.",
        f"| `{fingerprint}` | `docs/ejemplo.md` | `generic-api-key` | "
        "falso positivo | 2026-07-17 |",
    )
    ruta_documento.write_text(contenido, encoding="utf-8")
    monkeypatch.setitem(globals(), "RUTA_IGNORE_GITLEAKS", ruta_ignore)
    monkeypatch.setitem(globals(), "RUTA_EXCEPCIONES_GITLEAKS", ruta_documento)

    test_excepciones_gitleaks_son_individuales_y_documentadas()


def test_docstring_describe_semgrep_y_gitleaks() -> None:
    assert __doc__ == "Contrato estructural para las configuraciones Semgrep y Gitleaks."
