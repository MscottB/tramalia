"""v0.22: subgrupos por dominio, estado instalada/no, PATH de uv, selector completo."""

from tramalia.cli.renderizado import agrupar_estados, grupo_de
from tramalia.core import installer
from tramalia.core.integraciones import REGISTRO, EstadoHerramienta


def _herramienta(clave):
    return next(herramienta for herramienta in REGISTRO if herramienta.clave == clave)


# ---------------------------------------------------------------- subgrupos
def test_features_se_reparten_por_dominio():
    assert grupo_de(_herramienta("serena")) == "context"
    assert grupo_de(_herramienta("engram")) == "memory"
    assert grupo_de(_herramienta("semgrep")) == "security"
    assert grupo_de(_herramienta("sqlfluff")) == "database"
    assert grupo_de(_herramienta("databricks")) == "analytics"
    assert grupo_de(_herramienta("rulesync")) == "convention"  # capacidad=sync
    assert grupo_de(_herramienta("claude")) == "agent"
    assert grupo_de(_herramienta("mise")) == "bootstrap"


def test_grupos_respetan_orden():
    st = [
        EstadoHerramienta(_herramienta("databricks"), False),
        EstadoHerramienta(_herramienta("engram"), False),
        EstadoHerramienta(_herramienta("mise"), True),
        EstadoHerramienta(_herramienta("serena"), False),
    ]
    grupos = [g for g, _ in agrupar_estados(st)]
    assert grupos == ["bootstrap", "context", "memory", "analytics"]


# ---------------------------------------------------------------- engram/codegraph
def test_engram_instalable_en_mac_y_en_windows_con_go():
    mac = installer.options_for(_herramienta("engram"), os_name="macos")
    assert any(o.method == "brew" and o.auto for o in mac)
    # Windows: automatizable vía `go install` (si Go está) + binario manual de respaldo
    win = installer.options_for(_herramienta("engram"), os_name="windows")
    go = next(o for o in win if o.method == "go")
    assert go.auto and go.requires == "go" and "engram" in go.args[2]
    assert any(not o.auto for o in win)  # respaldo manual visible


def test_probe_detecta_engram_instalado_por_go(tmp_path, monkeypatch):
    import pathlib

    from tramalia.core import integraciones

    (tmp_path / "go" / "bin").mkdir(parents=True)
    (tmp_path / "go" / "bin" / "engram.exe").write_bytes(b"")
    monkeypatch.delenv("GOPATH", raising=False)
    monkeypatch.setattr(pathlib.Path, "home", staticmethod(lambda: tmp_path))
    monkeypatch.setattr(integraciones.shutil, "which", lambda _n: None)
    estado = integraciones.sondear(_herramienta("engram"))
    assert estado.presente is True and "go" in (estado.version or "")


def test_codegraph_siempre_visible_como_manual():
    for os_name in ("windows", "macos", "linux"):
        opts = installer.options_for(_herramienta("codegraph"), os_name=os_name)
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
        herramienta = _herramienta(key)
        best = installer.best_auto(herramienta)
        opts = installer.options_for(herramienta)
        # o tiene vía automatizable, o al menos una opción manual visible
        assert best is not None or any(not o.auto for o in opts), key
