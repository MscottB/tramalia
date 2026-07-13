import asyncio

import pytest

pytest.importorskip("mcp")

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
