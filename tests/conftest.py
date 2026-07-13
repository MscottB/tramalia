from pathlib import Path

import pytest


@pytest.fixture
def raiz_proyecto() -> Path:
    """Return the repository root used by contract and release tests."""
    return Path(__file__).resolve().parents[1]
