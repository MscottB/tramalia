"""Instalación personalizada por SO y por gestor disponible.

Tramalia no reimplementa gestores de paquetes: detecta el sistema y qué
gestores hay (winget/brew/choco/scoop, mise, uv, npm) y arma para cada
herramienta una lista ordenada de opciones — la primera disponible se puede
ejecutar automatizada; el resto se muestra como alternativa manual.
Reglas: npm solo si Node está presente; nada de `curl | sh` automatizado.
"""

from __future__ import annotations

import platform
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from tramalia.core.integraciones import Herramienta
from tramalia.core.procesos import _resolver, ejecutar


def current_os() -> str:
    s = platform.system().lower()
    if "windows" in s:
        return "windows"
    if "darwin" in s:
        return "macos"
    return "linux"


@dataclass(frozen=True)
class InstallOption:
    method: str  # "mise" | "uv" | "npm" | "pip" | "winget" | "brew" | ...
    args: tuple[str, ...]  # comando ejecutable (vacío si es solo manual)
    display: str  # cómo mostrarlo al usuario
    requires: str = ""  # binario que debe existir para poder automatizarla
    auto: bool = True  # False = solo se muestra (p. ej. curl | sh, URLs)

    @property
    def available(self) -> bool:
        if not self.auto or not self.args:
            return False
        need = self.requires or self.method
        return shutil.which(need) is not None


def _winget(pkg_id: str) -> InstallOption:
    args = (
        "winget",
        "install",
        "-e",
        "--id",
        pkg_id,
        "--accept-source-agreements",
        "--accept-package-agreements",
    )
    return InstallOption("winget", args, f"winget install {pkg_id}", requires="winget")


def _brew(pkg: str) -> InstallOption:
    return InstallOption("brew", ("brew", "install", pkg), f"brew install {pkg}", requires="brew")


def _manual(display: str) -> InstallOption:
    return InstallOption("manual", (), display, auto=False)


def _go_install(pkg: str) -> InstallOption:
    # requiere Go; el binario queda en ~/go/bin (sondear lo detecta aunque no esté en PATH)
    return InstallOption("go", ("go", "install", pkg), f"go install {pkg}", requires="go")


# bootstrap y runtimes: opciones por SO, en orden de preferencia.
# En Windows, winget es la vía verificada para mise (scoop falló en pruebas
# reales; choco sin verificar) — por eso va primero y las otras como alternativa.
_SYSTEM: dict[str, dict[str, list[InstallOption]]] = {
    "mise": {
        "windows": [
            _winget("jdx.mise"),
            InstallOption(
                "choco", ("choco", "install", "mise", "-y"), "choco install mise", requires="choco"
            ),
            InstallOption(
                "scoop", ("scoop", "install", "mise"), "scoop install mise", requires="scoop"
            ),
        ],
        "macos": [_brew("mise"), _manual("curl https://mise.run | sh")],
        "linux": [_manual("curl https://mise.run | sh")],
    },
    "git": {
        "windows": [_winget("Git.Git")],
        "macos": [_brew("git")],
        "linux": [_manual("sudo apt install git (o el gestor de tu distro)")],
    },
    "uv": {
        "windows": [_winget("astral-sh.uv")],
        "macos": [_brew("uv"), _manual("curl -LsSf https://astral.sh/uv/install.sh | sh")],
        "linux": [_manual("curl -LsSf https://astral.sh/uv/install.sh | sh")],
    },
    "node": {
        "windows": [_winget("OpenJS.NodeJS.LTS")],
        "macos": [_brew("node")],
        "linux": [_manual("mise use node@22 (o el gestor de tu distro)")],
    },
    "go": {
        "windows": [_winget("GoLang.Go")],
        "macos": [_brew("go")],
        "linux": [_manual("ver https://go.dev/doc/install (o el gestor de tu distro)")],
    },
    # engram (memoria N2): brew en mac; `go install` multiplataforma (incl. Windows)
    # si Go está presente; binario de releases como último recurso manual.
    "engram": {
        "windows": [
            _go_install("github.com/Gentleman-Programming/engram/cmd/engram@latest"),
            _manual("binario de github.com/Gentleman-Programming/engram/releases"),
        ],
        "macos": [
            _brew("gentleman-programming/tap/engram"),
            _go_install("github.com/Gentleman-Programming/engram/cmd/engram@latest"),
        ],
        "linux": [
            _brew("gentleman-programming/tap/engram"),
            _go_install("github.com/Gentleman-Programming/engram/cmd/engram@latest"),
            _manual("binario de github.com/Gentleman-Programming/engram/releases"),
        ],
    },
    # codegraph: el binario SÍ se automatiza vía npm (_from_hint lo deriva del
    # install_hint del registro); aquí no hace falta _SYSTEM. El wiring a agentes
    # (`codegraph install --skip-config`) es un paso aparte, nunca automatizado.
    # Antigravity CLI (agy): en Windows hay paquete winget oficial (automatizable);
    # en mac/linux solo el script curl|sh, que NUNCA se ejecuta automatizado.
    "antigravity": {
        "windows": [
            _winget("Google.AntigravityCLI"),
            _manual("irm https://antigravity.google/cli/install.ps1 | iex"),
        ],
        "macos": [_manual("curl -fsSL https://antigravity.google/cli/install.sh | bash")],
        "linux": [_manual("curl -fsSL https://antigravity.google/cli/install.sh | bash")],
    },
    # Antigravity IDE y 2.0: apps de escritorio. winget en Windows; descarga en el resto.
    "antigravity-ide": {
        "windows": [_winget("Google.AntigravityIDE")],
        "macos": [_manual("descarga desde antigravity.google/download")],
        "linux": [_manual("descarga desde antigravity.google/download")],
    },
    "antigravity-2": {
        "windows": [_winget("Google.Antigravity")],
        "macos": [_manual("descarga desde antigravity.google/download")],
        "linux": [_manual("descarga desde antigravity.google/download")],
    },
}


def known_runtime_bin_dirs() -> list:
    """Dirs donde los instaladores dejan los runtimes (Go/Node) — que winget/etc
    agregan al PATH del USUARIO pero no al del proceso en marcha."""
    from pathlib import Path

    if current_os() == "windows":
        cand = [
            Path("C:/Program Files/Go/bin"),
            Path.home() / "go" / "bin",
            Path("C:/Program Files/nodejs"),
        ]
    else:
        cand = [Path("/usr/local/go/bin"), Path.home() / "go" / "bin"]
    return [d for d in cand if d.exists()]


def refresh_runtime_path() -> None:
    """Agrega al PATH del proceso los dirs de runtimes recién instalados, para
    que una instalación encadenada (p. ej. engram justo después de Go) los vea
    sin reiniciar la terminal. Idempotente."""
    import os

    parts = os.environ.get("PATH", "").split(os.pathsep)
    seen = {p.strip().lower().rstrip("\\/") for p in parts}
    add = [str(d) for d in known_runtime_bin_dirs() if str(d).lower().rstrip("\\/") not in seen]
    if add:
        os.environ["PATH"] = os.pathsep.join(add) + os.pathsep + os.environ.get("PATH", "")


def uv_bin_dir() -> Path:
    """Return the directory where uv installs user-level executables."""
    return Path.home() / ".local" / "bin"


def uv_bin_on_path() -> bool:
    """¿Está ~/.local/bin (donde uv deja los binarios) en el PATH del proceso?"""
    import os

    target = str(uv_bin_dir()).lower()
    entries = [
        p.strip().lower().rstrip("\\/") for p in os.environ.get("PATH", "").split(os.pathsep)
    ]
    return target.rstrip("\\/") in entries


def pathfix_option() -> InstallOption:
    """Acción para agregar los binarios de uv al PATH (uv tool update-shell)."""
    return InstallOption(
        "uv", ("uv", "tool", "update-shell"), "uv tool update-shell", requires="uv"
    )


def _from_hint(herramienta: Herramienta) -> list[InstallOption]:
    """Deriva opciones del install_hint del registro (mise use / uv / pip / npm)."""
    hint = (herramienta.sugerencia_instalacion or "").strip()
    opts: list[InstallOption] = []
    if hint.startswith("mise use "):
        spec = hint.removeprefix("mise use ").strip()
        opts.append(InstallOption("mise", ("mise", "use", spec), hint, requires="mise"))
        if spec.startswith("npm:"):
            pkg = spec.removeprefix("npm:")
            # npm solo si Node está: el verificador es el propio binario npm
            opts.append(
                InstallOption(
                    "npm", ("npm", "install", "-g", pkg), f"npm i -g {pkg}", requires="npm"
                )
            )
        elif spec.startswith("pipx:"):
            pkg = spec.removeprefix("pipx:")
            opts.append(
                InstallOption(
                    "uv", ("uv", "tool", "install", pkg), f"uv tool install {pkg}", requires="uv"
                )
            )
    elif hint.startswith("uv tool install"):
        opts.append(InstallOption("uv", tuple(hint.split()), hint, requires="uv"))
    elif hint.startswith("npm i -g ") or hint.startswith("npm install -g "):
        pkg = hint.split("-g", 1)[1].strip()
        opts.append(InstallOption("npm", ("npm", "install", "-g", pkg), hint, requires="npm"))
    elif hint.startswith("pip install"):
        pkg = hint.removeprefix("pip install").strip().strip('"').strip("'")
        opts.append(
            InstallOption(
                "uv", ("uv", "tool", "install", pkg), f'uv tool install "{pkg}"', requires="uv"
            )
        )
        opts.append(
            InstallOption(
                "pip", (sys.executable, "-m", "pip", "install", pkg), hint, requires=sys.executable
            )
        )
    return opts


def options_for(herramienta: Herramienta, os_name: str | None = None) -> list[InstallOption]:
    """Opciones de instalación ordenadas (mejor primero) para esta herramienta."""
    os_name = os_name or current_os()
    opts = list(_SYSTEM.get(herramienta.clave, {}).get(os_name, []))
    opts += _from_hint(herramienta)
    if not opts and herramienta.sugerencia_instalacion:
        opts.append(_manual(herramienta.sugerencia_instalacion))
    return opts


def best_auto(herramienta: Herramienta, os_name: str | None = None) -> InstallOption | None:
    """La primera opción ejecutable automatizada (su gestor está presente)."""
    for opt in options_for(herramienta, os_name):
        if opt.available:
            return opt
    return None


# runtimes que habilitan automatización (npm→Node, go→Go): nombre legible + su key
# en el registro/_SYSTEM para poder instalarlos y así desbloquear la herramienta.
_RUNTIME_NAME = {"npm": "Node.js", "go": "Go"}
_RUNTIME_KEY = {"npm": "node", "go": "go"}


def blocking_runtime(herramienta: Herramienta, os_name: str | None = None) -> str | None:
    """Si la mejor vía automatizable de `herramienta` NO está disponible SOLO porque
    falta un runtime (Node/Go), devuelve ese runtime (`npm`/`go`); None si ya es
    automatizable o si no depende de un runtime que se pueda instalar."""
    if best_auto(herramienta, os_name):
        return None
    for opt in options_for(herramienta, os_name):
        if opt.auto and opt.requires in _RUNTIME_NAME and shutil.which(opt.requires) is None:
            return opt.requires
    return None


def runtime_install_option(requires: str, os_name: str | None = None) -> InstallOption | None:
    """La mejor opción para instalar el runtime (`npm`→node, `go`→go)."""
    key = _RUNTIME_KEY.get(requires)
    if not key:
        return None
    opts = _SYSTEM.get(key, {}).get(os_name or current_os(), [])
    for o in opts:
        if o.available:
            return o
    return opts[0] if opts else None


def plan_for(tools, os_name: str | None = None):
    """Arma el plan de instalación para una lista de Herramientas faltantes.

    Devuelve (auto, manual, runtime_offers):
    - auto: [(label, InstallOption)] automatizables ya.
    - manual: [(label, comando, runtime_bloqueante|None)] visibles pero no auto.
    - runtime_offers: [(nombre_runtime, InstallOption, [tools que habilita])] —
      instalar ese runtime (Node/Go) vuelve automatizables a esas herramientas.
    """
    os_name = os_name or current_os()
    auto, manual = [], []
    blocked: dict[str, list[str]] = {}
    for herramienta in tools:
        best = best_auto(herramienta, os_name)
        if best:
            auto.append((herramienta.comando, best))
            continue
        rt = blocking_runtime(herramienta, os_name)
        opts = options_for(herramienta, os_name)
        cmd = opts[0].display if opts else herramienta.sugerencia_instalacion
        manual.append((herramienta.comando, cmd, rt))
        if rt:
            blocked.setdefault(rt, []).append(herramienta.comando)
    runtime_offers = []
    for rt, enables in blocked.items():
        opt = runtime_install_option(rt, os_name)
        if opt and opt.available:
            runtime_offers.append((_RUNTIME_NAME[rt], opt, enables))
    return auto, manual, runtime_offers


def run_install(opt: InstallOption, timeout: int = 900) -> tuple[int, str]:
    """Ejecuta una opción automatizada. Devuelve (exit_code, salida)."""
    if not opt.args:
        return 1, f"opción manual, no ejecutable: {opt.display}"
    try:
        resultado = ejecutar(opt.args, limite_segundos=timeout)
        return resultado.codigo_salida, resultado.salida + resultado.error
    except Exception as exc:
        return 1, str(exc)


# señales típicas de "requiere terminal como administrador" (winget/choco en Windows)
_ADMIN_MARKS = (
    "0x8a150049",
    "0x80070005",
    "access is denied",
    "acceso denegado",
    "administrator",
    "administrador",
    "elevation",
    "elevad",
)


def needs_admin(output: str) -> bool:
    low = (output or "").lower()
    return any(m in low for m in _ADMIN_MARKS)


def run_install_streaming(
    opt: InstallOption, on_line, cancel=None, timeout: int = 600
) -> tuple[int, str]:
    """Ejecuta una opción emitiendo la salida LÍNEA A LÍNEA (on_line(str)).

    - `cancel`: threading.Event — al activarse se termina el proceso (exit 130)
      para que una instalación pegada no bloquee al resto de la selección.
    - `timeout`: por herramienta; al expirar se termina el proceso (exit 124).
    Devuelve (exit_code, salida_completa).
    """
    import subprocess
    import threading
    import time

    if not opt.args:
        return 1, f"opción manual, no ejecutable: {opt.display}"
    try:
        p = subprocess.Popen(
            _resolver(opt.args),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as exc:
        return 1, str(exc)

    # watchdog: vigila cancelación y timeout aunque el proceso esté MUDO
    # (una instalación pegada sin imprimir nada era justo el caso reportado).
    why: dict = {"code": None}

    def _watch():
        fin = time.monotonic() + timeout
        while p.poll() is None:
            if cancel is not None and cancel.is_set():
                why["code"] = 130
                p.terminate()
                return
            if time.monotonic() > fin:
                why["code"] = 124
                p.terminate()
                return
            time.sleep(0.2)

    threading.Thread(target=_watch, daemon=True).start()
    lines: list[str] = []
    salida_proceso = p.stdout
    if salida_proceso is None:
        p.terminate()
        return 1, "el instalador no expuso stdout"
    try:
        for line in iter(salida_proceso.readline, ""):
            lines.append(line)
            on_line(line.rstrip())
        p.wait(timeout=30)
        return why["code"] if why["code"] is not None else p.returncode, "".join(lines)
    except Exception as exc:
        try:
            p.terminate()
        except Exception:
            pass
        return why["code"] or 1, "".join(lines) + f"\n{exc}"
