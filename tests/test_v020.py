"""v0.20: instalador robusto — streaming/cancelar, detección uv, docs, registro."""

import sys
import threading
from pathlib import Path

from tramalia.core import installer, integraciones
from tramalia.core.installer import InstallOption, needs_admin, run_install_streaming
from tramalia.core.integraciones import REGISTRO, url_documentacion


def _herramienta(clave):
    return next(herramienta for herramienta in REGISTRO if herramienta.clave == clave)


# ---------------------------------------------------------------- detección uv
def test_probe_ve_instaladas_por_uv_fuera_del_path(tmp_path, monkeypatch):
    # uv deja binarios en ~/.local/bin SIN tocar el PATH (ni reiniciando)
    (tmp_path / ".local" / "bin").mkdir(parents=True)
    (tmp_path / ".local" / "bin" / "headroom.exe").write_bytes(b"")
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    monkeypatch.setattr(integraciones.shutil, "which", lambda _n: None)
    estado = integraciones.sondear(_herramienta("headroom"))
    assert estado.presente is True and "uv" in (estado.version or "")


def test_serena_efimera_ok_con_uv(monkeypatch):
    monkeypatch.setattr(
        integraciones.shutil, "which", lambda n: "C:/x/uv.exe" if n == "uv" else None
    )
    estado = integraciones.sondear(_herramienta("serena"))
    assert estado.presente is True and "uvx" in (estado.version or "")


# ---------------------------------------------------------------- registro
def test_gemini_fuera_openclaw_hermes_dentro():
    keys = {herramienta.clave for herramienta in REGISTRO}
    assert "gemini" not in keys
    assert {"openclaw", "hermes"} <= keys


def test_opencode_automatizable_via_npm():
    opts = installer.options_for(_herramienta("opencode"))
    assert any(o.method == "npm" for o in opts)


def test_docs_url_conocida_y_fallback():
    assert url_documentacion(_herramienta("mise")).startswith("https://mise")
    assert url_documentacion(_herramienta("markitdown")).startswith("https://github.com/microsoft")


# ---------------------------------------------------------------- admin
def test_needs_admin_detecta_marcas():
    assert needs_admin("Error 0x80070005: acceso denegado")
    assert needs_admin("requires elevation")
    assert not needs_admin("todo bien")


# ---------------------------------------------------------------- streaming
def test_streaming_emite_lineas_en_vivo():
    lineas = []
    opt = InstallOption("pip", (sys.executable, "-c", "print('uno'); print('dos')"), "demo")
    code, out = run_install_streaming(opt, on_line=lineas.append, timeout=60)
    assert code == 0
    assert "uno" in lineas and "dos" in lineas  # línea a línea, no al final


def test_streaming_cancelar_no_bloquea(tmp_path):
    cancel = threading.Event()
    script = "import time,sys\nprint('arranca', flush=True)\ntime.sleep(60)\n"
    f = tmp_path / "lento.py"
    f.write_text(script, encoding="utf-8")
    opt = InstallOption("pip", (sys.executable, str(f)), "lento")

    def on_line(_ln):
        cancel.set()  # cancela apenas aparece la primera línea

    code, _out = run_install_streaming(opt, on_line=on_line, cancel=cancel, timeout=60)
    assert code == 130  # cancelada, no colgada 60s


def test_streaming_timeout_termina_el_proceso(tmp_path):
    script = "import time\nprint('x', flush=True)\ntime.sleep(60)\n"
    f = tmp_path / "pegado.py"
    f.write_text(script, encoding="utf-8")
    opt = InstallOption("pip", (sys.executable, str(f)), "pegado")
    code, _ = run_install_streaming(opt, on_line=lambda _l: None, timeout=2)
    assert code == 124
