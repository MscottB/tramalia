import asyncio

import pytest

pytest.importorskip("mcp")

from mcp.server.fastmcp.exceptions import ToolError

from tramalia.core import context, evidence, handoff
from tramalia.core.errores import ErrorProyectoNoGobernado
from tramalia.mcp_server import build_server

_EXPECTED = {
    "project_status",
    "get_agent_rules",
    "get_failed_attempts",
    "get_current_task",
    "doctor",
    "record_handoff",
    "build_evidence",
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
    ("nombre", "argumentos", "modulo", "atributo"),
    [
        ("record_handoff", {"task": "TASK-1"}, "handoff", "new_handoff"),
        ("build_evidence", {"task": "TASK-1"}, "evidence", "build_evidence"),
        ("build_context", {}, "context", "build_context"),
    ],
)
def test_mutaciones_mcp_exigen_proyecto_gobernado(
    tmp_path,
    monkeypatch,
    nombre,
    argumentos,
    modulo,
    atributo,
):
    modulos = {"context": context, "evidence": evidence, "handoff": handoff}
    llamadas = []

    def mutacion_prohibida(*args, **kwargs):
        llamadas.append((*args, kwargs))
        return tmp_path / "mutado"

    monkeypatch.setattr(modulos[modulo], atributo, mutacion_prohibida)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ToolError) as capturada:
        asyncio.run(build_server().call_tool(nombre, argumentos))

    assert isinstance(capturada.value.__cause__, ErrorProyectoNoGobernado)
    assert llamadas == []
