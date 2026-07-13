from __future__ import annotations

import ast
import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

import tramalia.mcp_server as servidor_mcp
from tramalia.__main__ import construir_parser, main
from tramalia.cli import comandos
from tramalia.cli.comandos import construir_excepciones
from tramalia.core import operaciones
from tramalia.core.errores import ErrorExcepcionInvalida, ErrorIdentificadorInseguro
from tramalia.core.modelos import (
    EjecucionPuertas,
    ResultadoCierre,
    ValorEstadoCierre,
    ValorEstadoPuertas,
)
from tramalia.core.operaciones import cerrar_proyecto, crear_evidencia, registrar_traspaso
from tramalia.core.procesos import ResultadoProceso


def test_cli_evidencia_delega_en_crear_evidencia(tmp_path, monkeypatch, capsys) -> None:
    llamadas: list[tuple[Path, str]] = []

    class Paquete:
        id_paquete = "paquete-1"
        ruta = tmp_path / ".tramalia" / "evidencia" / "paquete-1"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "tramalia.cli.comandos.crear_evidencia",
        lambda raiz, id_tarea, **_opciones: llamadas.append((raiz, id_tarea)) or Paquete(),
    )
    assert main(["--plain", "evidence", "TASK-1"]) == 0
    assert llamadas == [(tmp_path, "TASK-1")]
    assert "paquete-1" in capsys.readouterr().out


def test_cli_traspaso_delega_y_crea_paquete_nuevo(tmp_path, monkeypatch, capsys) -> None:
    class Paquete:
        id_paquete = "traspaso-1"
        ruta = tmp_path / ".tramalia" / "evidencia" / "traspaso-1"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("tramalia.cli.comandos.registrar_traspaso", lambda *_a, **_k: Paquete())
    assert main(["--plain", "handoff", "TASK-2"]) == 0
    assert "traspaso-1" in capsys.readouterr().out


def test_cli_error_de_dominio_conserva_codigo(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    def fallar(*_argumentos, **_opciones):
        raise ErrorIdentificadorInseguro(
            mensaje="ID inseguro",
            sugerencia="usa letras ASCII",
            ruta=None,
            detalles={"id_tarea": "../x"},
        )

    monkeypatch.setattr("tramalia.cli.comandos.crear_evidencia", fallar)
    assert main(["--plain", "evidence", "../x"]) == 2
    salida = capsys.readouterr().out
    assert "id_tarea_inseguro" in salida
    assert "usa letras ASCII" in salida


def test_cli_cierre_bloqueado_devuelve_uno_sin_recalcular(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    resultado = ResultadoCierre(
        estado=ValorEstadoCierre.BLOQUEADO,
        id_tarea="TASK-3",
        id_paquete="paquete-3",
        ruta_paquete=tmp_path / "paquete-3",
        ruta_traspaso=None,
        ejecucion=EjecucionPuertas(estado=ValorEstadoPuertas.SIN_CONFIGURAR),
        excepciones=(),
        bloqueos=("sin_configurar",),
    )
    monkeypatch.setattr(
        "tramalia.cli.comandos.cerrar_proyecto",
        lambda *_argumentos, **_opciones: resultado,
    )
    assert main(["--plain", "close", "TASK-3"]) == 1


def test_alias_allow_fail_sin_campos_es_rechazado_antes_de_operar(tmp_path, monkeypatch) -> None:
    llamado = False

    def cerrar(*_argumentos, **_opciones):
        nonlocal llamado
        llamado = True

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("tramalia.cli.comandos.cerrar_proyecto", cerrar)
    assert main(["--plain", "close", "TASK-4", "--allow-fail"]) == 2
    assert not llamado


def test_firmas_publicas_compartidas() -> None:
    assert str(inspect.signature(cerrar_proyecto)) == (
        "(raiz: 'Path', id_tarea: 'str', *, agente: 'str' = '', revisor: 'str' = '', "
        "modelo: 'str' = '', excepciones: 'Sequence[ExcepcionFallo]' = ()) -> "
        "'ResultadoCierre'"
    )


def test_cli_y_mcp_comparten_el_constructor_de_excepciones_del_nucleo() -> None:
    assert comandos.construir_excepciones_fallo is operaciones.construir_excepciones_fallo
    assert servidor_mcp.construir_excepciones_fallo is operaciones.construir_excepciones_fallo
    assert str(inspect.signature(crear_evidencia)) == (
        "(raiz: 'Path', id_tarea: 'str', *, agente: 'str' = '', revisor: 'str' = '', "
        "modelo: 'str' = '') -> 'PaqueteEvidencia'"
    )
    assert str(inspect.signature(registrar_traspaso)) == (
        "(raiz: 'Path', id_tarea: 'str', *, agente: 'str' = '', revisor: 'str' = '') "
        "-> 'PaqueteEvidencia'"
    )


def test_parser_expone_un_solo_juego_de_campos_de_excepcion() -> None:
    argumentos = construir_parser().parse_args(
        [
            "close",
            "TASK-1",
            "--allow-fail",
            "--razon-excepcion",
            "falso positivo",
            "--riesgo-aceptado",
            "riesgo acotado",
            "--control-afectado",
            "test",
            "--referencia-excepcion",
            "ISSUE-1",
            "--revisor-excepcion",
            "ana",
            "--expira-en",
            "2026-08-01T00:00:00+00:00",
            "--condicion-remediacion",
            "corregir antes del release",
        ]
    )

    assert argumentos.razon_excepcion == "falso positivo"
    assert argumentos.riesgo_aceptado == "riesgo acotado"
    assert argumentos.control_afectado == "test"
    assert argumentos.referencia_excepcion == "ISSUE-1"
    assert argumentos.revisor_excepcion == "ana"
    assert argumentos.expira_en == "2026-08-01T00:00:00+00:00"
    assert argumentos.condicion_remediacion == "corregir antes del release"


def test_alias_allow_fail_sin_campos_no_construye_excepcion_vacia() -> None:
    with pytest.raises(ErrorExcepcionInvalida):
        construir_excepciones(SimpleNamespace(allow_fail=True), "ana")


def test_alias_allow_fail_con_campos_construye_excepcion_completa() -> None:
    argumentos = SimpleNamespace(
        allow_fail=True,
        razon_excepcion="falso positivo",
        riesgo_aceptado="riesgo acotado",
        control_afectado="test",
        referencia_excepcion="ISSUE-1",
        revisor_excepcion="ana",
        expira_en="2026-08-01T00:00:00+00:00",
        condicion_remediacion="",
    )

    excepciones = construir_excepciones(argumentos, "revisor por defecto")

    assert len(excepciones) == 1
    assert excepciones[0].control_afectado == "test"
    assert excepciones[0].revisor == "ana"
    assert excepciones[0].expira_en is not None


def test_campos_explicitos_construyen_excepcion_sin_requerir_alias() -> None:
    argumentos = SimpleNamespace(
        allow_fail=False,
        razon_excepcion="falso positivo",
        riesgo_aceptado="riesgo acotado",
        control_afectado="test",
        referencia_excepcion="ISSUE-2",
        revisor_excepcion="ana",
        expira_en="",
        condicion_remediacion="corregir antes del release",
    )

    excepciones = construir_excepciones(argumentos, "revisor por defecto")

    assert len(excepciones) == 1
    assert excepciones[0].referencia == "ISSUE-2"
    assert excepciones[0].condicion_remediacion == "corregir antes del release"


def test_cli_ejecutable_ausente_no_duplica_el_error_interno(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    errores: list[str] = []
    monkeypatch.setattr(
        comandos.procesos,
        "ejecutar",
        lambda _comando: ResultadoProceso(
            ("ausente",),
            127,
            "",
            "[WinError 2] El sistema no puede encontrar el archivo",
        ),
    )
    monkeypatch.setattr(comandos.renderizado, "error", errores.append)

    codigo = comandos._ejecutar(["ausente"])

    captura = capsys.readouterr()
    assert codigo == 127
    assert captura.err == ""
    assert errores == ["no se encontró 'ausente'. Corre `tramalia doctor` para instalarlo."]


@pytest.mark.parametrize(
    ("nombre_comando", "nombre_operacion"),
    [
        ("comando_evidencia", "crear_evidencia"),
        ("comando_traspaso", "registrar_traspaso"),
    ],
)
def test_cli_evidencia_y_traspaso_delegan_una_sola_vez(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    nombre_comando: str,
    nombre_operacion: str,
) -> None:
    llamadas: list[tuple[Path, str, dict[str, object]]] = []
    paquete = SimpleNamespace(
        id_paquete="paquete-1",
        ruta=tmp_path / ".tramalia" / "evidencia" / "paquete-1",
    )

    def operar(raiz: Path, id_tarea: str, **opciones: object) -> object:
        llamadas.append((raiz, id_tarea, opciones))
        return paquete

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(comandos, "_resolver", lambda _argumentos: ("TASK-1", "codex", "ana"))
    monkeypatch.setattr(comandos, nombre_operacion, operar)

    codigo = getattr(comandos, nombre_comando)(SimpleNamespace(engram=False))

    assert codigo == 0
    assert llamadas == [(tmp_path, "TASK-1", {"agente": "codex", "revisor": "ana"})]


@pytest.mark.parametrize(
    ("estado", "codigo_esperado"),
    [
        (ValorEstadoCierre.APROBADO, 0),
        (ValorEstadoCierre.BLOQUEADO, 1),
    ],
)
def test_cli_cierre_usa_el_resultado_sin_recalcular(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    estado: ValorEstadoCierre,
    codigo_esperado: int,
) -> None:
    llamadas: list[dict[str, object]] = []
    resultado = ResultadoCierre(
        estado=estado,
        id_tarea="TASK-2",
        id_paquete="paquete-2",
        ruta_paquete=None,
        ruta_traspaso=None,
        ejecucion=EjecucionPuertas(estado=ValorEstadoPuertas.SIN_CONFIGURAR),
        bloqueos=("test",) if estado is ValorEstadoCierre.BLOQUEADO else (),
    )

    def cerrar(*argumentos: object, **opciones: object) -> ResultadoCierre:
        llamadas.append({"argumentos": argumentos, **opciones})
        return resultado

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(comandos, "_resolver", lambda _argumentos: ("TASK-2", "codex", "ana"))
    monkeypatch.setattr(comandos, "cerrar_proyecto", cerrar)
    argumentos = SimpleNamespace(allow_fail=False, model="gpt-5", engram=False)

    assert comandos.comando_cerrar(argumentos) == codigo_esperado
    assert len(llamadas) == 1
    assert llamadas[0]["modelo"] == "gpt-5"
    assert llamadas[0]["excepciones"] == ()


def test_cli_allow_fail_incompleto_falla_antes_de_operar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llamado = False

    def cerrar(*argumentos: object, **opciones: object) -> None:
        nonlocal llamado
        llamado = True

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(comandos, "_resolver", lambda _argumentos: ("TASK-3", "codex", "ana"))
    monkeypatch.setattr(comandos, "cerrar_proyecto", cerrar)

    assert (
        comandos.despachar(
            "close",
            SimpleNamespace(allow_fail=True, engram=False),
        )
        == 2
    )
    assert llamado is False


def test_superficies_importan_las_operaciones_compartidas() -> None:
    esperados = {
        Path("tramalia/cli/comandos.py"): {
            "cerrar_proyecto",
            "crear_evidencia",
            "registrar_traspaso",
        },
        Path("tramalia/mcp_server.py"): {
            "cerrar_proyecto",
            "crear_evidencia",
            "registrar_traspaso",
        },
        Path("tramalia/tui.py"): {"cerrar_proyecto"},
    }
    for ruta, nombres in esperados.items():
        arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
        importados = {
            alias.name
            for nodo in ast.walk(arbol)
            if isinstance(nodo, ast.ImportFrom) and nodo.module == "tramalia.core.operaciones"
            for alias in nodo.names
        }
        assert nombres <= importados, ruta


def test_no_quedan_imports_del_nucleo_historico() -> None:
    modulos = {"governance", "evidence", "handoff"}
    for base in (Path("tramalia"), Path("tests")):
        for ruta in base.rglob("*.py"):
            arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
            for nodo in ast.walk(arbol):
                if isinstance(nodo, ast.Import):
                    assert not any(
                        alias.name in {f"tramalia.core.{nombre}" for nombre in modulos}
                        for alias in nodo.names
                    ), ruta
                if isinstance(nodo, ast.ImportFrom):
                    assert nodo.module not in {f"tramalia.core.{nombre}" for nombre in modulos}, (
                        ruta
                    )
                    if nodo.module == "tramalia.core":
                        assert not ({alias.name for alias in nodo.names} & modulos), ruta
