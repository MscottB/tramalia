"""v0.20: instalador robusto — streaming/cancelar, detección uv, docs, registro."""

import sys
import threading
from pathlib import Path

from tramalia.core import installer, tools
from tramalia.core.installer import InstallOption, needs_admin, run_install_streaming
from tramalia.core.tools import REGISTRY, docs_url


def _tool(key):
    return next(t for t in REGISTRY if t.key == key)


# ---------------------------------------------------------------- detección uv
def test_probe_ve_instaladas_por_uv_fuera_del_path(tmp_path, monkeypatch):
    # uv deja binarios en ~/.local/bin SIN tocar el PATH (ni reiniciando)
    (tmp_path / ".local" / "bin").mkdir(parents=True)
    (tmp_path / ".local" / "bin" / "headroom.exe").write_bytes(b"")
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    monkeypatch.setattr(tools.shutil, "which", lambda _n: None)
    st = tools.probe(_tool("headroom"))
    assert st.present is True and "uv" in (st.version or "")


def test_serena_efimera_ok_con_uv(monkeypatch):
    monkeypatch.setattr(tools.shutil, "which",
                        lambda n: "C:/x/uv.exe" if n == "uv" else None)
    st = tools.probe(_tool("serena"))
    assert st.present is True and "uvx" in (st.version or "")


# ---------------------------------------------------------------- registro
def test_gemini_fuera_openclaw_hermes_dentro():
    keys = {t.key for t in REGISTRY}
    assert "gemini" not in keys
    assert {"openclaw", "hermes"} <= keys


def test_opencode_automatizable_via_npm():
    opts = installer.options_for(_tool("opencode"))
    assert any(o.method == "npm" for o in opts)


def test_docs_url_conocida_y_fallback():
    assert docs_url(_tool("mise")).startswith("https://mise")
    assert docs_url(_tool("markitdown")).startswith("https://github.com/microsoft")


# ---------------------------------------------------------------- admin
def test_needs_admin_detecta_marcas():
    assert needs_admin("Error 0x80070005: acceso denegado")
    assert needs_admin("requires elevation")
    assert not needs_admin("todo bien")


# ---------------------------------------------------------------- streaming
def test_streaming_emite_lineas_en_vivo():
    lineas = []
    opt = InstallOption("pip", (sys.executable, "-c", "print('uno'); print('dos')"),
                        "demo")
    code, out = run_install_streaming(opt, on_line=lineas.append, timeout=60)
    assert code == 0
    assert "uno" in lineas and "dos" in lineas   # línea a línea, no al final


def test_streaming_cancelar_no_bloquea(tmp_path):
    cancel = threading.Event()
    script = ("import time,sys\n"
              "print('arranca', flush=True)\n"
              "time.sleep(60)\n")
    f = tmp_path / "lento.py"
    f.write_text(script, encoding="utf-8")
    opt = InstallOption("pip", (sys.executable, str(f)), "lento")

    def on_line(_ln):
        cancel.set()      # cancela apenas aparece la primera línea

    code, _out = run_install_streaming(opt, on_line=on_line, cancel=cancel, timeout=60)
    assert code == 130    # cancelada, no colgada 60s


def test_streaming_timeout_termina_el_proceso(tmp_path):
    script = "import time\nprint('x', flush=True)\ntime.sleep(60)\n"
    f = tmp_path / "pegado.py"
    f.write_text(script, encoding="utf-8")
    opt = InstallOption("pip", (sys.executable, str(f)), "pegado")
    code, _ = run_install_streaming(opt, on_line=lambda _l: None, timeout=2)
    assert code == 124
