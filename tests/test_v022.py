"""v0.22: subgrupos por dominio, estado instalada/no, PATH de uv, selector completo."""

from tramalia.cli.render import group_of, group_statuses
from tramalia.core import installer
from tramalia.core.tools import REGISTRY, Status


def _tool(key):
    return next(t for t in REGISTRY if t.key == key)


# ---------------------------------------------------------------- subgrupos
def test_features_se_reparten_por_dominio():
    assert group_of(_tool("serena")) == "context"
    assert group_of(_tool("engram")) == "memory"
    assert group_of(_tool("semgrep")) == "security"
    assert group_of(_tool("sqlfluff")) == "database"
    assert group_of(_tool("databricks")) == "analytics"
    assert group_of(_tool("rulesync")) == "convention"   # feature=sync
    assert group_of(_tool("claude")) == "agent"
    assert group_of(_tool("mise")) == "bootstrap"


def test_grupos_respetan_orden():
    st = [Status(_tool("databricks"), False), Status(_tool("engram"), False),
          Status(_tool("mise"), True), Status(_tool("serena"), False)]
    grupos = [g for g, _ in group_statuses(st)]
    assert grupos == ["bootstrap", "context", "memory", "analytics"]


# ---------------------------------------------------------------- engram/codegraph
def test_engram_instalable_en_mac_visible_en_windows():
    mac = installer.options_for(_tool("engram"), os_name="macos")
    assert any(o.method == "brew" and o.auto for o in mac)
    win = installer.options_for(_tool("engram"), os_name="windows")
    assert win and all(not o.auto for o in win)           # visible pero manual


def test_codegraph_siempre_visible_como_manual():
    for os_name in ("windows", "macos", "linux"):
        opts = installer.options_for(_tool("codegraph"), os_name=os_name)
        assert opts and "codegraph" in opts[0].display


# ---------------------------------------------------------------- PATH de uv
def test_uv_bin_on_path(monkeypatch, tmp_path):
    monkeypatch.setattr(installer, "uv_bin_dir", lambda: tmp_path / ".local" / "bin")
    monkeypatch.setenv("PATH", str(tmp_path / ".local" / "bin"))
    assert installer.uv_bin_on_path() is True
    monkeypatch.setenv("PATH", "/otra/cosa")
    assert installer.uv_bin_on_path() is False


def test_pathfix_option_es_update_shell():
    opt = installer.pathfix_option()
    assert opt.args == ("uv", "tool", "update-shell")


# ---------------------------------------------------------------- selector completo
def test_selector_incluye_todas_las_faltantes():
    """Cada faltante cae en automatizable (best_auto) o manual (options_for) —
    ninguna se omite (el bug: solo aparecían las automatizables)."""
    for key in ("engram", "codegraph", "hermes", "openclaw"):
        tool = _tool(key)
        best = installer.best_auto(tool)
        opts = installer.options_for(tool)
        # o tiene vía automatizable, o al menos una opción manual visible
        assert best is not None or (opts and not opts[0].auto)
