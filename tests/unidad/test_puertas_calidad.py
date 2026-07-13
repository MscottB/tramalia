from __future__ import annotations

import hashlib
import subprocess
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tramalia.core import puertas_calidad
from tramalia.core.detect import enabled_features
from tramalia.core.errores import ErrorConfiguracionPuertas
from tramalia.core.modelos import ValorEstadoPuertas, ValorResultadoPuerta
from tramalia.core.scaffold import build_mise_toml


def _escribir_mise(tmp_path: Path, contenido: str) -> None:
    (tmp_path / "mise.toml").write_text(contenido, encoding="utf-8")


def test_toml_invalido_no_se_convierte_en_lista_vacia(tmp_path: Path) -> None:
    _escribir_mise(tmp_path, "[tasks")

    with pytest.raises(ErrorConfiguracionPuertas) as capturada:
        puertas_calidad.cargar_puertas(tmp_path)

    assert capturada.value.codigo == "configuracion_puertas_invalida"
    assert capturada.value.detalles["tipo_error"] == "TOMLDecodeError"


@pytest.mark.parametrize("tipo_error", [OSError, UnicodeError])
def test_error_de_lectura_se_convierte_en_error_de_dominio(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tipo_error: type[Exception],
) -> None:
    ruta = tmp_path / "mise.toml"
    ruta.touch()

    def fallar_lectura(self: Path, *args: object, **kwargs: object) -> str:
        if self == ruta:
            raise tipo_error("detalle sensible")
        raise AssertionError(f"lectura inesperada: {self}")

    monkeypatch.setattr(Path, "read_text", fallar_lectura)

    with pytest.raises(ErrorConfiguracionPuertas) as capturada:
        puertas_calidad.cargar_puertas(tmp_path)

    assert capturada.value.codigo == "configuracion_puertas_invalida"
    assert capturada.value.detalles["tipo_error"] == tipo_error.__name__


def test_tasks_debe_ser_una_tabla(tmp_path: Path) -> None:
    _escribir_mise(tmp_path, 'tasks = "test"')

    with pytest.raises(ErrorConfiguracionPuertas):
        puertas_calidad.cargar_puertas(tmp_path)


@pytest.mark.parametrize(
    "declaracion",
    [
        'test = "pytest"',
        "test = true",
        "test = 3",
        "[tasks.test]",
        '[tasks.test]\nrun = ""',
        '[tasks.test]\nrun = "   "',
        "[tasks.test]\nrun = []",
        '[tasks.test]\nrun = ["pytest", ""]',
        '[tasks.test]\nrun = ["pytest", "   "]',
        '[tasks.test]\nrun = ["pytest", true]',
        "[tasks.test]\nrun = true",
        "[tasks.test]\nrun = 7",
    ],
)
def test_declaracion_y_run_invalidos_se_rechazan(tmp_path: Path, declaracion: str) -> None:
    _escribir_mise(tmp_path, f"[tasks]\n{declaracion}\n")

    with pytest.raises(ErrorConfiguracionPuertas) as capturada:
        puertas_calidad.cargar_puertas(tmp_path)

    assert capturada.value.detalles["puerta"] == "test"


@pytest.mark.parametrize(
    "run",
    ['"pytest -q"', '["pytest", "-q"]'],
)
def test_run_valido_carga_la_puerta(tmp_path: Path, run: str) -> None:
    _escribir_mise(tmp_path, f"[tasks.test]\nrun = {run}\n")

    puertas = puertas_calidad.cargar_puertas(tmp_path)

    assert tuple(puerta.nombre for puerta in puertas) == ("test",)


def test_mise_ausente_y_sin_puertas_son_estados_bloqueantes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _escribir_mise(tmp_path, "[tasks.test]\nrun = 'pytest'")
    cargadas = puertas_calidad.cargar_puertas(tmp_path)
    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: None)

    sin_ejecutor = puertas_calidad.ejecutar_puertas(tmp_path, cargadas)
    sin_configurar = puertas_calidad.ejecutar_puertas(tmp_path, ())

    assert sin_ejecutor.estado is ValorEstadoPuertas.EJECUTOR_NO_DISPONIBLE
    assert sin_ejecutor.omitidas == ("test",)
    assert sin_configurar.estado is ValorEstadoPuertas.SIN_CONFIGURAR


def test_archivo_mise_ausente_no_inventa_puertas(tmp_path: Path) -> None:
    assert puertas_calidad.cargar_puertas(tmp_path) == ()


def test_carga_excluye_agregado_gates_y_conserva_build(tmp_path: Path) -> None:
    _escribir_mise(
        tmp_path,
        "[tasks.gates]\ndepends = ['build']\n[tasks.build]\nrun = 'python -m build'\n",
    )

    assert tuple(puerta.nombre for puerta in puertas_calidad.cargar_puertas(tmp_path)) == ("build",)


def test_catalogo_publico_incluye_bundle_y_notebooks(
    tmp_path: Path,
) -> None:
    nombres = (
        "ux",
        "notebooks",
        "bundle",
        "database",
        "security",
        "format",
        "lint",
        "test",
        "build",
    )
    _escribir_mise(
        tmp_path,
        "".join(f"[tasks.{nombre}]\nrun = 'echo {nombre}'\n" for nombre in nombres),
    )

    assert tuple(puerta.nombre for puerta in puertas_calidad.cargar_puertas(tmp_path)) == tuple(
        reversed(nombres)
    )


def test_ejecucion_de_notebooks_sigue_siendo_opt_in() -> None:
    base = {
        "stacks": ["python", "notebooks"],
        "features": enabled_features(["python", "notebooks"]),
    }

    assert "jupyter execute" not in build_mise_toml(base)
    activada = {**base, "with_notebook_exec": True}
    assert "jupyter execute notebooks/*.ipynb" in build_mise_toml(activada)


def test_lint_y_format_nunca_comparten_salida(tmp_path: Path) -> None:
    _escribir_mise(
        tmp_path,
        "[tasks.lint]\nrun = 'ruff check'\n[tasks.format]\nrun = 'ruff format --check'\n",
    )

    archivos = [puerta.archivo_salida for puerta in puertas_calidad.cargar_puertas(tmp_path)]

    assert archivos == ["lint-salida.txt", "format-salida.txt"]


@pytest.mark.parametrize(
    ("codigo", "estado_resultado", "estado_ejecucion"),
    [
        (0, ValorResultadoPuerta.APROBADO, ValorEstadoPuertas.APROBADO),
        (1, ValorResultadoPuerta.FALLIDO, ValorEstadoPuertas.FALLIDO),
    ],
)
def test_codigo_de_retorno_distingue_verde_y_rojo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    codigo: int,
    estado_resultado: ValorResultadoPuerta,
    estado_ejecucion: ValorEstadoPuertas,
) -> None:
    _escribir_mise(tmp_path, "[tasks.test]\nrun = 'pytest'")
    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: "mise")
    monkeypatch.setattr(
        puertas_calidad.proc,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess([], codigo, "salida", ""),
    )

    ejecucion = puertas_calidad.ejecutar_puertas(tmp_path, puertas_calidad.cargar_puertas(tmp_path))

    assert ejecucion.estado is estado_ejecucion
    assert ejecucion.resultados[0].estado is estado_resultado


def test_error_de_ejecucion_no_aborta_la_puerta_posterior(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _escribir_mise(
        tmp_path,
        "[tasks.test]\nrun = 'pytest'\n[tasks.lint]\nrun = 'ruff check'",
    )
    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: "mise")
    respuestas: Iterator[subprocess.CompletedProcess[str] | BaseException] = iter(
        [
            subprocess.TimeoutExpired(["mise"], 900),
            subprocess.CompletedProcess([], 0, "lint verde", ""),
        ]
    )

    def ejecutar(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        respuesta = next(respuestas)
        if isinstance(respuesta, BaseException):
            raise respuesta
        return respuesta

    monkeypatch.setattr(puertas_calidad.proc, "run", ejecutar)

    ejecucion = puertas_calidad.ejecutar_puertas(tmp_path, puertas_calidad.cargar_puertas(tmp_path))

    assert ejecucion.estado is ValorEstadoPuertas.ERROR_EJECUCION
    assert ejecucion.fallidas == ("test",)
    assert tuple(resultado.nombre for resultado in ejecucion.resultados) == (
        "test",
        "lint",
    )
    assert ejecucion.resultados[1].estado is ValorResultadoPuerta.APROBADO


def test_conserva_stdout_stderr_hash_tiempos_duracion_y_comando(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _escribir_mise(tmp_path, "[tasks.test]\nrun = 'pytest'")
    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: "mise")
    llamadas: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def ejecutar(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        llamadas.append((args, kwargs))
        return subprocess.CompletedProcess([], 0, "uno\n", "dos\n")

    monkeypatch.setattr(puertas_calidad.proc, "run", ejecutar)
    antes = datetime.now(UTC)

    ejecucion = puertas_calidad.ejecutar_puertas(tmp_path, puertas_calidad.cargar_puertas(tmp_path))

    despues = datetime.now(UTC)
    resultado = ejecucion.resultados[0]
    assert resultado.salida == "uno\ndos\n"
    assert resultado.hash_salida == hashlib.sha256(b"uno\ndos\n").hexdigest()
    assert resultado.comando == ("mise", "run", "test")
    assert resultado.inicio_utc.tzinfo is UTC
    assert resultado.fin_utc.tzinfo is UTC
    assert antes <= resultado.inicio_utc <= resultado.fin_utc <= despues
    assert resultado.duracion_segundos >= 0
    assert llamadas == [
        (
            (["mise", "run", "test"],),
            {
                "cwd": tmp_path,
                "capture_output": True,
                "text": True,
                "timeout": 900,
            },
        )
    ]


@pytest.mark.parametrize("interrupcion", [KeyboardInterrupt, SystemExit])
def test_no_captura_interrupciones_del_proceso(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    interrupcion: type[BaseException],
) -> None:
    _escribir_mise(tmp_path, "[tasks.test]\nrun = 'pytest'")
    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: "mise")

    def interrumpir(*args: object, **kwargs: object) -> None:
        raise interrupcion()

    monkeypatch.setattr(puertas_calidad.proc, "run", interrumpir)

    with pytest.raises(interrupcion):
        puertas_calidad.ejecutar_puertas(tmp_path, puertas_calidad.cargar_puertas(tmp_path))
