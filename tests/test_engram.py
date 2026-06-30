import json

from tramalia.core.detect import enabled_features
from tramalia.core.scaffold import build_mcp_json
from tramalia.core.tools import REGISTRY


def test_engram_is_optional_memory_tool():
    eng = next((t for t in REGISTRY if t.key == "engram"), None)
    assert eng is not None
    assert eng.category == "feature"
    assert eng.feature == "memory"
    assert eng.managed_by_mise is False


def test_memory_feature_always_enabled():
    # doctor debe poder surface Engram en cualquier proyecto
    assert "memory" in enabled_features([])


def test_mcp_json_always_has_serena_and_is_valid():
    data = json.loads(build_mcp_json({"stacks": [], "features": ()}))
    assert "serena" in data["mcpServers"]
    assert "Engram" in data["_note"] or "engram" in data["_note"]
