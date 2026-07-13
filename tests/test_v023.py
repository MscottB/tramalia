"""v0.23: versión en el UI + prerequisitos de runtime visibles y facilitados."""

from tramalia.core import installer
from tramalia.core.integraciones import REGISTRO


def _herramienta(clave):
    return next(herramienta for herramienta in REGISTRO if herramienta.clave == clave)


# ---------------------------------------------------------------- versión en UI
def test_header_muestra_version(capsys):
    from tramalia import __version__
    from tramalia.cli import render

    render.set_plain(True)
    render.header("demo", ["python"], True)
    out = capsys.readouterr().out
    assert f"Tramalia v{__version__}" in out
    render.set_plain(False)


def test_tui_title_incluye_version():
    import pytest

    pytest.importorskip("textual")
    from tramalia import __version__
    from tramalia.tui import build_app

    assert build_app().TITLE == f"Tramalia v{__version__}"


# ---------------------------------------------------------------- runtime bloqueante
def test_go_es_automatizable():
    win = installer.options_for(_herramienta("go"), os_name="windows")
    assert any(o.method == "winget" and o.auto for o in win)


def test_engram_bloqueado_por_go_si_falta(monkeypatch):
    # sin go ni ningún gestor auto → engram queda bloqueado por el runtime Go
    monkeypatch.setattr(installer.shutil, "which", lambda _n: None)
    rt = installer.blocking_runtime(_herramienta("engram"), os_name="windows")
    assert rt == "go"


def test_engram_no_bloqueado_si_go_presente(monkeypatch):
    monkeypatch.setattr(installer.shutil, "which", lambda n: "C:/x/go.exe" if n == "go" else None)
    assert installer.blocking_runtime(_herramienta("engram"), os_name="windows") is None


def test_runtime_install_option_para_go():
    opt = installer.runtime_install_option("go", os_name="windows")
    assert opt is not None and "GoLang.Go" in opt.display


# ---------------------------------------------------------------- plan_for
def test_plan_for_ofrece_el_runtime_que_desbloquea(monkeypatch):
    # solo winget presente (para instalar Go); go/npm ausentes
    monkeypatch.setattr(
        installer.shutil, "which", lambda n: "C:/w/winget.exe" if n == "winget" else None
    )
    monkeypatch.setattr(installer, "current_os", lambda: "windows")
    auto, manual, offers = installer.plan_for([_herramienta("engram")])
    # engram no es auto (falta go), aparece en manual con su runtime
    assert any(rt == "go" for _c, _d, rt in manual)
    # y se ofrece instalar Go, listando que habilita engram
    assert offers and offers[0][0] == "Go" and "engram" in offers[0][2]
