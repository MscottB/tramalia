"""v0.17: instalador personalizado — por SO, por gestor, selección múltiple."""

from tramalia.core import installer
from tramalia.core.integraciones import REGISTRO


def _herramienta(clave):
    return next(herramienta for herramienta in REGISTRO if herramienta.clave == clave)


# ---------------------------------------------------------------- por SO
def test_mise_en_windows_winget_primero():
    opts = installer.options_for(_herramienta("mise"), os_name="windows")
    assert opts[0].method == "winget" and "jdx.mise" in opts[0].display
    # scoop existe pero como última alternativa (falló en pruebas reales)
    metodos = [o.method for o in opts]
    assert metodos.index("winget") < metodos.index("scoop")


def test_mise_en_linux_no_ejecuta_curl_pipe():
    opts = installer.options_for(_herramienta("mise"), os_name="linux")
    assert all(not o.auto for o in opts if "curl" in o.display)  # nunca automatizado


def test_uv_por_so():
    assert installer.options_for(_herramienta("uv"), os_name="windows")[0].method == "winget"
    assert installer.options_for(_herramienta("uv"), os_name="macos")[0].method == "brew"


# ---------------------------------------------------------------- del hint
def test_repomix_mise_y_npm():
    opts = installer.options_for(_herramienta("repomix"))
    metodos = [o.method for o in opts]
    assert metodos[0] == "mise"  # preferencia: mise
    npm = next(o for o in opts if o.method == "npm")
    assert npm.requires == "npm"  # verificador Node/npm
    assert npm.args == ("npm", "install", "-g", "repomix")


def test_semgrep_pipx_gana_opcion_uv():
    opts = installer.options_for(_herramienta("semgrep"))
    uv = next(o for o in opts if o.method == "uv")
    assert uv.args == ("uv", "tool", "install", "semgrep")


def test_markitdown_pip_deriva_uv_y_pip():
    opts = installer.options_for(_herramienta("markitdown"))
    metodos = [o.method for o in opts]
    assert "uv" in metodos and "pip" in metodos


def test_hint_url_es_manual():
    opts = installer.options_for(_herramienta("claude"))
    assert opts and not opts[0].auto  # URL: solo se muestra


# ---------------------------------------------------------------- best_auto
def test_best_auto_respeta_disponibilidad(monkeypatch):
    # sin ningún gestor presente → no hay opción automatizada
    monkeypatch.setattr(installer.shutil, "which", lambda _n: None)
    assert installer.best_auto(_herramienta("repomix")) is None


def test_best_auto_elige_el_primero_disponible(monkeypatch):
    # solo npm presente → repomix se instala vía npm (mise ausente)
    monkeypatch.setattr(installer.shutil, "which", lambda n: "C:/x/npm.cmd" if n == "npm" else None)
    best = installer.best_auto(_herramienta("repomix"))
    assert best is not None and best.method == "npm"


# ---------------------------------------------------------------- agrupación
def test_doctor_agrupado_orden_fijo():
    from tramalia.cli.render import group_statuses
    from tramalia.core.integraciones import EstadoHerramienta

    # semgrep=security, serena=context, engram=memory: cada feature en su dominio
    statuses = [
        EstadoHerramienta(_herramienta("claude"), False),
        EstadoHerramienta(_herramienta("mise"), True),
        EstadoHerramienta(_herramienta("engram"), False),
        EstadoHerramienta(_herramienta("serena"), False),
        EstadoHerramienta(_herramienta("semgrep"), False),
        EstadoHerramienta(_herramienta("node"), False),
    ]
    grupos = [cat for cat, _ in group_statuses(statuses)]
    assert grupos == ["bootstrap", "stack", "context", "memory", "security", "agent"]


def test_current_os_valores():
    assert installer.current_os() in ("windows", "macos", "linux")
