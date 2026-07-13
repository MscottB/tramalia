import json

from tramalia.core.detect import enabled_features
from tramalia.core.integraciones import REGISTRO
from tramalia.core.scaffold import build_mcp_json


def test_engram_is_optional_memory_tool():
    eng = next((herramienta for herramienta in REGISTRO if herramienta.clave == "engram"), None)
    assert eng is not None
    assert eng.categoria == "feature"
    assert eng.capacidad == "memory"
    assert eng.administrada_por_mise is False


def test_memory_feature_always_enabled():
    # doctor debe poder surface Engram en cualquier proyecto
    assert "memory" in enabled_features([])


def test_mcp_json_always_has_serena_and_is_valid():
    data = json.loads(build_mcp_json({"stacks": [], "features": ()}))
    assert "serena" in data["mcpServers"]
    assert "Engram" in data["_note"] or "engram" in data["_note"]
