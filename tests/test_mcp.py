import asyncio
import json
from types import SimpleNamespace

import pytest

pytest.importorskip("mcp")

from mcp.server.fastmcp.exceptions import ToolError

import tramalia.mcp_server as servidor_mcp
from tramalia.core.errores import ErrorExcepcionInvalida, ErrorProyectoNoGobernado
from tramalia.core.modelos import (
    EjecucionPuertas,
    ResultadoCierre,
    ValorEstadoCierre,
    ValorEstadoPuertas,
)
from tramalia.mcp_server import build_server

_EXPECTED = {
    "project_status",
    "get_agent_rules",
    "get_failed_attempts",
    "get_current_task",
    "doctor",
    "record_handoff",
    "build_evidence",
    "cerrar_proyecto",
    "build_context",
}


def test_server_registers_expected_tools():
    server = build_server()
    tools = asyncio.run(server.list_tools())
    names = {t.name for t in tools}
    assert _EXPECTED <= names


def test_estado_mcp_usa_inspeccion_tipificada(tmp_path, monkeypatch):
    (tmp_path / "AGENTS.md").write_text("reglas aisladas", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    contenido, _ = asyncio.run(build_server().call_tool("project_status", {}))

    assert any("inicializado: False" in bloque.text for bloque in contenido)


@pytest.mark.parametrize(
    ("nombre", "argumentos"),
    [
        ("record_handoff", {"task": "TASK-1"}),
        ("build_evidence", {"task": "TASK-1"}),
        ("cerrar_proyecto", {"task": "TASK-1"}),
        ("build_context", {}),
    ],
)
def test_mutaciones_mcp_exigen_proyecto_gobernado(
    tmp_path,
    monkeypatch,
    nombre,
    argumentos,
):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ToolError) as capturada:
        asyncio.run(build_server().call_tool(nombre, argumentos))

    assert isinstance(capturada.value.__cause__, ErrorProyectoNoGobernado)


def test_excepcion_mcp_parcial_no_se_ignora(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ToolError) as capturada:
        asyncio.run(
            build_server().call_tool(
                "cerrar_proyecto",
                {"task": "TASK-1", "razon_excepcion": "falso positivo"},
            )
        )

    assert isinstance(capturada.value.__cause__, ErrorExcepcionInvalida)


def test_cierre_mcp_delega_los_siete_campos_y_devuelve_esquema(
    tmp_path,
    monkeypatch,
):
    llamadas = []
    resultado = ResultadoCierre(
        estado=ValorEstadoCierre.APROBADO_CON_EXCEPCIONES,
        id_tarea="TASK-7",
        id_paquete="paquete-7",
        ruta_paquete=None,
        ruta_traspaso=None,
        ejecucion=EjecucionPuertas(
            estado=ValorEstadoPuertas.APROBADO,
            ejecutadas=("test",),
        ),
        bloqueos=(),
    )

    def cerrar(raiz, id_tarea, **opciones):
        llamadas.append((raiz, id_tarea, opciones))
        return resultado

    monkeypatch.setattr(servidor_mcp, "ejecutar_cierre", cerrar)
    monkeypatch.chdir(tmp_path)
    argumentos = {
        "task": "TASK-7",
        "agent": "codex",
        "reviewer": "ana",
        "model": "gpt-5",
        "razon_excepcion": "falso positivo",
        "riesgo_aceptado": "riesgo acotado",
        "control_afectado": "test",
        "referencia_excepcion": "ISSUE-7",
        "revisor_excepcion": "ana",
        "expira_en": "2026-08-01T00:00:00+00:00",
        "condicion_remediacion": "corregir antes del release",
    }

    contenido, estructurado = asyncio.run(build_server().call_tool("cerrar_proyecto", argumentos))

    assert len(llamadas) == 1
    raiz, id_tarea, opciones = llamadas[0]
    assert raiz == tmp_path and id_tarea == "TASK-7"
    assert opciones["agente"] == "codex"
    assert opciones["revisor"] == "ana"
    assert opciones["modelo"] == "gpt-5"
    excepcion = opciones["excepciones"][0]
    assert excepcion.razon == "falso positivo"
    assert excepcion.riesgo_aceptado == "riesgo acotado"
    assert excepcion.control_afectado == "test"
    assert excepcion.referencia == "ISSUE-7"
    assert excepcion.revisor == "ana"
    assert excepcion.expira_en is not None
    assert excepcion.condicion_remediacion == "corregir antes del release"
    assert estructurado == {
        "estado": "aprobado_con_excepciones",
        "id_paquete": "paquete-7",
        "bloqueos": [],
        "aprobado": True,
    }
    assert json.loads(contenido[0].text) == estructurado


@pytest.mark.parametrize(
    ("herramienta", "atributo", "argumentos", "opciones_esperadas"),
    [
        (
            "record_handoff",
            "registrar_traspaso",
            {"task": "TASK-8", "agent": "codex", "reviewer": "ana"},
            {"agente": "codex", "revisor": "ana"},
        ),
        (
            "build_evidence",
            "crear_evidencia",
            {
                "task": "TASK-8",
                "agent": "codex",
                "reviewer": "ana",
                "model": "gpt-5",
            },
            {"agente": "codex", "revisor": "ana", "modelo": "gpt-5"},
        ),
    ],
)
def test_herramientas_mcp_standalone_delegan_y_devuelven_paquete(
    tmp_path,
    monkeypatch,
    herramienta,
    atributo,
    argumentos,
    opciones_esperadas,
):
    llamadas = []
    paquete = SimpleNamespace(
        id_paquete="paquete-8",
        ruta=tmp_path / ".tramalia" / "evidencia" / "paquete-8",
    )

    def operar(raiz, id_tarea, **opciones):
        llamadas.append((raiz, id_tarea, opciones))
        return paquete

    monkeypatch.setattr(servidor_mcp, atributo, operar)
    monkeypatch.chdir(tmp_path)

    contenido, estructurado = asyncio.run(build_server().call_tool(herramienta, argumentos))

    assert llamadas == [(tmp_path, "TASK-8", opciones_esperadas)]
    assert estructurado["id_paquete"] == "paquete-8"
    assert estructurado["ruta_paquete"] == ".tramalia/evidencia/paquete-8"
    assert json.loads(contenido[0].text) == estructurado
