"""Register external tools and detect their availability.

Categories:
  - bootstrap: tools that Tramalia and mise cannot install by themselves.
  - stack: tools selected from the detected project technologies.
  - feature: tools selected from the enabled quality gates and capabilities.

Tramalia diagnoses and delegates installation instead of reimplementing package
managers.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from tramalia.core import procesos
from tramalia.core.modelos import EstadoIntegracion, ValorEstadoIntegracion
from tramalia.core.procesos import ResultadoProceso


@dataclass(frozen=True, slots=True)
class AdaptadorCapacidad:
    """Declare which capability an optional adapter can provide."""

    nombre: str
    capacidades: frozenset[str]
    disponible: Callable[[], bool]


@dataclass(frozen=True, slots=True)
class ResultadoIntentoIntegracion:
    """Pair an integration state with the external process that produced it."""

    estado: EstadoIntegracion
    proceso: ResultadoProceso | None


def ejecutar_integracion(
    *,
    capacidad: str,
    solicitado: str | None,
    adaptadores: Sequence[AdaptadorCapacidad],
    operacion: Callable[[str], ResultadoProceso],
    impacto_degradado: str,
    remediacion: str,
) -> ResultadoIntentoIntegracion:
    """Execute one adapter selected by capability without hiding failed attempts.

    A missing preferred adapter may fall back to the first available adapter that
    declares the same capability. Once any adapter is executed, a non-zero exit,
    timeout or cancellation is final and no second adapter is attempted.
    """
    candidatos = [a for a in adaptadores if capacidad in a.capacidades]
    if solicitado is None:
        return ResultadoIntentoIntegracion(
            EstadoIntegracion(
                ValorEstadoIntegracion.NO_DISPONIBLE,
                capacidad,
                None,
                None,
                "capacidad_opcional_no_solicitada",
                impacto_degradado,
                remediacion,
            ),
            None,
        )

    preferidos = [a for a in candidatos if a.nombre == solicitado]
    restantes = [a for a in candidatos if a.nombre != solicitado]
    elegido = next((a for a in (*preferidos, *restantes) if a.disponible()), None)
    if elegido is None:
        return ResultadoIntentoIntegracion(
            EstadoIntegracion(
                ValorEstadoIntegracion.NO_DISPONIBLE,
                capacidad,
                solicitado,
                None,
                "adaptador_no_instalado",
                impacto_degradado,
                remediacion,
            ),
            None,
        )

    proceso = operacion(elegido.nombre)
    if not proceso.exitoso:
        motivo = (
            "proceso_agotado"
            if proceso.agotado_tiempo
            else "proceso_cancelado"
            if proceso.cancelado
            else "proceso_salida_no_cero"
        )
        return ResultadoIntentoIntegracion(
            EstadoIntegracion(
                ValorEstadoIntegracion.FALLIDO,
                capacidad,
                solicitado,
                elegido.nombre,
                motivo,
                impacto_degradado,
                remediacion,
            ),
            proceso,
        )

    degradado = elegido.nombre != solicitado
    return ResultadoIntentoIntegracion(
        EstadoIntegracion(
            ValorEstadoIntegracion.DEGRADADO if degradado else ValorEstadoIntegracion.COMPLETO,
            capacidad,
            solicitado,
            elegido.nombre,
            "alternativa_completada" if degradado else "adaptador_completado",
            impacto_degradado if degradado else "sin impacto",
            remediacion if degradado else "ninguna",
        ),
        proceso,
    )


def exportar_memoria_engram(titulo: str, cuerpo: str) -> ResultadoIntentoIntegracion:
    """Exporta una copia opcional a Engram con un resultado tipado y no lanzable.

    Esta capacidad no publica ni modifica el paquete de evidencia. Su consumidor
    debe invocarla solo despues de recibir el resultado durable de la operacion
    primaria; asi un fallo externo nunca provoca repetir esa publicacion.

    Args:
        titulo: Titulo estable con que Engram identifica la memoria.
        cuerpo: Resumen del paquete durable ya publicado.

    Returns:
        Estado completo, no disponible o fallido junto al proceso ejecutado. Las
        excepciones inesperadas del adaptador se convierten en un fallo visible.
    """
    adaptador = AdaptadorCapacidad(
        nombre="engram",
        capacidades=frozenset({"memoria"}),
        disponible=lambda: procesos.encontrar("engram") is not None,
    )
    try:
        return ejecutar_integracion(
            capacidad="memoria",
            solicitado="engram",
            adaptadores=(adaptador,),
            operacion=lambda _nombre: procesos.ejecutar(["engram", "save", titulo, cuerpo]),
            impacto_degradado="el paquete durable conserva su validez sin la copia de memoria",
            remediacion="instala o revisa Engram y exporta la memoria manualmente",
        )
    except Exception:
        # Engram es un efecto opcional pospublicacion. Normalizar cualquier defecto
        # del adaptador evita que un paquete valido parezca fallido y sea repetido.
        return ResultadoIntentoIntegracion(
            EstadoIntegracion(
                estado=ValorEstadoIntegracion.FALLIDO,
                capacidad="memoria",
                solicitado="engram",
                utilizado=None,
                motivo="excepcion_inesperada",
                impacto="el paquete durable conserva su validez sin la copia de memoria",
                remediacion="revisa Engram y exporta la memoria manualmente",
            ),
            None,
        )


@dataclass(frozen=True)
class Herramienta:
    """Describe an external tool and how Tramalia can discover it."""

    clave: str
    comando: str
    rol: str
    categoria: str  # "bootstrap" | "stack" | "feature"
    argumentos_version: tuple[str, ...] = ("--version",)
    administrada_por_mise: bool = True
    sugerencia_instalacion: str = ""
    tecnologias: tuple[str, ...] = ()  # categoria "stack": tecnologias que la requieren
    capacidad: str = ""  # categoria "feature": puerta/capacidad que la activa
    entorno_ejecucion: str = ""  # entorno externo necesario: "node", "python", ...
    efimera: bool = False  # corre via uvx/npx: no requiere instalacion
    id_winget: str = ""  # app de escritorio detectable via `winget list`


REGISTRO: list[Herramienta] = [
    # --- bootstrap (mise no puede instalarse a sí mismo) ---
    Herramienta(
        "mise",
        "mise",
        "gestor de versiones + runner de gates",
        "bootstrap",
        administrada_por_mise=False,
        sugerencia_instalacion="https://mise.jdx.dev/getting-started.html",
    ),
    Herramienta(
        "git",
        "git",
        "control de versiones (memoria, ADR, handoff)",
        "bootstrap",
        administrada_por_mise=False,
        sugerencia_instalacion="https://git-scm.com/downloads",
    ),
    Herramienta(
        "uv",
        "uv",
        "instalador de tools Python (copier, specify, ...)",
        "bootstrap",
        administrada_por_mise=False,
        sugerencia_instalacion="https://docs.astral.sh/uv/getting-started/installation/",
    ),
    # --- por stack ---
    Herramienta(
        "node",
        "node",
        "runtime JS para frontend/build",
        "stack",
        tecnologias=("node", "angular", "react", "next", "nest", "vue", "svelte"),
    ),
    Herramienta("dotnet", "dotnet", "SDK .NET", "stack", tecnologias=("dotnet",)),
    Herramienta(
        "mvn",
        "mvn",
        "build Java (Maven)",
        "stack",
        tecnologias=("maven",),
        administrada_por_mise=False,
        sugerencia_instalacion="https://maven.apache.org/install.html",
    ),
    Herramienta(
        "gradle",
        "gradle",
        "build Java (Gradle)",
        "stack",
        tecnologias=("gradle",),
        administrada_por_mise=False,
        sugerencia_instalacion="https://gradle.org/install/",
    ),
    Herramienta(
        "go",
        "go",
        "toolchain Go (build/test)",
        "stack",
        tecnologias=("go",),
        administrada_por_mise=False,
        sugerencia_instalacion="https://go.dev/doc/install",
    ),
    Herramienta(
        "cargo",
        "cargo",
        "toolchain Rust (build/test)",
        "stack",
        tecnologias=("rust",),
        administrada_por_mise=False,
        sugerencia_instalacion="https://www.rust-lang.org/tools/install",
    ),
    # --- por feature/gate ---
    Herramienta(
        "copier",
        "copier",
        "scaffolding de la convención (tramalia init)",
        "feature",
        capacidad="init",
        administrada_por_mise=False,
        sugerencia_instalacion="uv tool install copier",
    ),
    Herramienta(
        "repomix",
        "repomix",
        "snapshot de contexto para IA",
        "feature",
        capacidad="context",
        entorno_ejecucion="node",
        sugerencia_instalacion="mise use npm:repomix",
    ),
    Herramienta(
        "serena",
        "serena",
        "navegación/edición semántica (MCP)",
        "feature",
        capacidad="context",
        administrada_por_mise=False,
        efimera=True,
        sugerencia_instalacion="uvx --from git+https://github.com/oraios/serena serena --help",
    ),
    Herramienta(
        "semgrep",
        "semgrep",
        "SAST (gate seguridad)",
        "feature",
        capacidad="security",
        sugerencia_instalacion="mise use pipx:semgrep",
    ),
    Herramienta(
        "gitleaks",
        "gitleaks",
        "secret scanning (gate seguridad)",
        "feature",
        capacidad="security",
        sugerencia_instalacion="mise use aqua:gitleaks",
    ),
    Herramienta(
        "sqlfluff",
        "sqlfluff",
        "lint SQL (gate base de datos)",
        "feature",
        capacidad="database",
        sugerencia_instalacion="mise use pipx:sqlfluff",
    ),
    Herramienta(
        "rulesync",
        "rulesync",
        "fan-out de reglas/skills por agente",
        "feature",
        capacidad="sync",
        entorno_ejecucion="node",
        sugerencia_instalacion="mise use npm:rulesync",
    ),
    Herramienta(
        "lhci",
        "lhci",
        "Lighthouse CI (gate UX/UI)",
        "feature",
        capacidad="ux",
        entorno_ejecucion="node",
        sugerencia_instalacion="mise use npm:@lhci/cli",
    ),
    Herramienta(
        "playwright",
        "playwright",
        "regresión visual + e2e (gate UX/UI)",
        "feature",
        capacidad="ux",
        entorno_ejecucion="node",
        sugerencia_instalacion="mise use npm:playwright",
    ),
    # memoria persistente opcional (nivel N2). Tramalia no la construye: la delega.
    Herramienta(
        "engram",
        "engram",
        "memoria persistente para agentes (N2, opcional)",
        "feature",
        capacidad="memory",
        administrada_por_mise=False,
        sugerencia_instalacion="brew install gentleman-programming/tap/engram",
    ),
    # compresión de contexto/outputs (token-saver opcional). NO reemplaza la evidencia.
    Herramienta(
        "headroom",
        "headroom",
        "compresión de contexto/outputs (token-saver, opcional)",
        "feature",
        capacidad="context",
        administrada_por_mise=False,
        sugerencia_instalacion='pip install "headroom-ai[all]"',
    ),
    # spec-driven development (opcional): complementa specs/ generada por init.
    Herramienta(
        "speckit",
        "specify",
        "spec-driven development (Spec Kit, opcional)",
        "feature",
        capacidad="specs",
        administrada_por_mise=False,
        sugerencia_instalacion="uv tool install specify-cli --from git+https://github.com/github/spec-kit.git",
    ),
    # grafo de código pre-indexado (contexto quirúrgico en una llamada, opcional).
    # binario vía npm (@colbymchenry/codegraph); el wiring a agentes es aparte:
    # `codegraph install --skip-config` (nunca automatizado por Tramalia).
    Herramienta(
        "codegraph",
        "codegraph",
        "grafo de código pre-indexado (contexto, opcional)",
        "feature",
        capacidad="context",
        administrada_por_mise=False,
        sugerencia_instalacion="npm i -g @colbymchenry/codegraph",
    ),
    # grafo de conocimiento desde código/docs/schemas (CLI+MCP+skill, opcional).
    Herramienta(
        "graphify",
        "graphify",
        "grafo de conocimiento del proyecto (contexto, opcional)",
        "feature",
        capacidad="context",
        administrada_por_mise=False,
        sugerencia_instalacion="uv tool install graphifyy",
    ),
    # ingesta de documentos: PDF/Office/imágenes → Markdown (contexto, opcional).
    Herramienta(
        "markitdown",
        "markitdown",
        "convierte PDF/Office/imágenes a Markdown (ingesta, contexto)",
        "feature",
        capacidad="context",
        administrada_por_mise=False,
        sugerencia_instalacion='pip install "markitdown[all]"',
    ),
    # analítica: Databricks Asset Bundles (gate bundle validate).
    Herramienta(
        "databricks",
        "databricks",
        "Databricks CLI (bundle validate, analítica)",
        "feature",
        capacidad="databricks",
        administrada_por_mise=False,
        sugerencia_instalacion="https://docs.databricks.com/dev-tools/cli/install",
    ),
    # --- agentes CLI y hosts (detección informativa: Tramalia NO los configura) ---
    # El rol dice explícitamente "CLI" para no confundir con las apps de escritorio.
    Herramienta(
        "claude",
        "claude",
        "Claude Code — CLI del agente (no la app de escritorio)",
        "agent",
        administrada_por_mise=False,
        sugerencia_instalacion="https://claude.com/claude-code",
    ),
    Herramienta(
        "codex",
        "codex",
        "OpenAI Codex — CLI del agente",
        "agent",
        administrada_por_mise=False,
        sugerencia_instalacion="npm i -g @openai/codex",
    ),
    # el binario real en PATH se llama "agy" (no "antigravity"); Antigravity CLI
    # reemplazó oficialmente a Gemini CLI (descontinuado 2026-06-18). En Windows
    # se automatiza vía winget (Google.AntigravityCLI); ver installer._SYSTEM.
    Herramienta(
        "antigravity",
        "agy",
        "Antigravity CLI — comando `agy` (agente; ex-Gemini CLI)",
        "agent",
        administrada_por_mise=False,
        sugerencia_instalacion="winget install -e --id Google.AntigravityCLI",
    ),
    # Antigravity IDE y 2.0 son apps de ESCRITORIO (hosts), no CLIs: se detectan
    # por `winget list` (winget_id), no por un comando en PATH.
    Herramienta(
        "antigravity-ide",
        "antigravity-ide",
        "Antigravity IDE — app de escritorio (fork de VS Code)",
        "agent",
        administrada_por_mise=False,
        id_winget="Google.AntigravityIDE",
        sugerencia_instalacion="winget install -e --id Google.AntigravityIDE",
    ),
    Herramienta(
        "antigravity-2",
        "antigravity-2.0",
        "Antigravity 2.0 — app de escritorio (plataforma de agentes)",
        "agent",
        administrada_por_mise=False,
        id_winget="Google.Antigravity",
        sugerencia_instalacion="winget install -e --id Google.Antigravity",
    ),
    Herramienta(
        "opencode",
        "opencode",
        "OpenCode — CLI del agente",
        "agent",
        administrada_por_mise=False,
        sugerencia_instalacion="npm i -g opencode-ai",
    ),
    # OpenClaw: CLI real por npm (requiere Node). El `onboard`/daemon es config
    # posterior del usuario, no la instalación del binario.
    Herramienta(
        "openclaw",
        "openclaw",
        "OpenClaw — CLI gateway multi-modelo",
        "agent",
        administrada_por_mise=False,
        entorno_ejecucion="node",
        sugerencia_instalacion="npm i -g openclaw",
    ),
    # Hermes Agent: CLI real, pero solo instalable vía script (`curl … | bash`),
    # que Tramalia NUNCA ejecuta automatizado — se muestra el comando exacto.
    Herramienta(
        "hermes",
        "hermes",
        "Hermes Agent — CLI (auto-mejora + gateway)",
        "agent",
        administrada_por_mise=False,
        sugerencia_instalacion="curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash",
    ),
]

# documentación oficial de cada herramienta (tecla `d` en la TUI / docs del sitio)
DOCUMENTACION: dict[str, str] = {
    "mise": "https://mise.jdx.dev",
    "git": "https://git-scm.com/doc",
    "uv": "https://docs.astral.sh/uv/",
    "node": "https://nodejs.org/docs",
    "dotnet": "https://learn.microsoft.com/dotnet/",
    "go": "https://go.dev/doc/",
    "cargo": "https://doc.rust-lang.org/cargo/",
    "mvn": "https://maven.apache.org/guides/",
    "gradle": "https://docs.gradle.org",
    "copier": "https://copier.readthedocs.io",
    "repomix": "https://repomix.com",
    "serena": "https://github.com/oraios/serena",
    "semgrep": "https://semgrep.dev/docs/",
    "gitleaks": "https://github.com/gitleaks/gitleaks",
    "sqlfluff": "https://docs.sqlfluff.com",
    "rulesync": "https://github.com/dyoshikawa/rulesync",
    "lhci": "https://github.com/GoogleChrome/lighthouse-ci",
    "playwright": "https://playwright.dev/docs/intro",
    "engram": "https://github.com/gentleman-programming/engram",
    "headroom": "https://github.com/headroom-ai/headroom",
    "speckit": "https://github.com/github/spec-kit",
    "codegraph": "https://github.com/colbymchenry/codegraph",
    "graphify": "https://github.com/irsbugs/graphifyy",
    "markitdown": "https://github.com/microsoft/markitdown",
    "databricks": "https://docs.databricks.com/dev-tools/cli/",
    "claude": "https://code.claude.com/docs",
    "codex": "https://developers.openai.com/codex",
    "antigravity": "https://antigravity.google/docs/cli-install",
    "antigravity-ide": "https://antigravity.google/docs",
    "antigravity-2": "https://antigravity.google/docs",
    "opencode": "https://opencode.ai/docs",
    "openclaw": "https://github.com/openclaw/openclaw",
    "hermes": "https://hermes-agent.nousresearch.com/docs/",
}


def url_documentacion(herramienta: Herramienta) -> str:
    """Return the official documentation URL for an external tool."""
    if herramienta.clave in DOCUMENTACION:
        return DOCUMENTACION[herramienta.clave]
    sugerencia = herramienta.sugerencia_instalacion
    return sugerencia if sugerencia.startswith("http") else ""


@dataclass
class EstadoHerramienta:
    """Describe whether an external tool is currently available."""

    herramienta: Herramienta
    presente: bool
    version: str | None = None


def _instalada_por_mise(comando: str, limite_segundos: float = 6.0) -> bool:
    """¿La instaló mise? Sus shims no están en el PATH hasta `mise activate` /
    reiniciar la terminal, así que `shutil.which` no las ve — `mise which` sí."""
    if shutil.which("mise") is None:
        return False
    try:
        completado = subprocess.run(
            ["mise", "which", comando],
            capture_output=True,
            text=True,
            timeout=limite_segundos,
        )
        return completado.returncode == 0 and bool((completado.stdout or "").strip())
    except Exception:
        return False


def _instalada_por_uv(comando: str) -> bool:
    """¿La instaló `uv tool install`? uv deja los ejecutables en ~/.local/bin,
    que en Windows NO entra al PATH (ni reiniciando) salvo `uv tool update-shell`
    — se revisa la carpeta directamente, sin depender del PATH."""
    from pathlib import Path

    base = Path.home() / ".local" / "bin"
    return any((base / f"{comando}{extension}").is_file() for extension in (".exe", ".cmd", ""))


def _instalada_por_go(comando: str) -> bool:
    """¿La instaló `go install`? Deja el binario en ~/go/bin (o $GOPATH/bin),
    que a menudo tampoco está en el PATH — se revisa la carpeta directamente."""
    import os
    from pathlib import Path

    gopath = os.environ.get("GOPATH")
    base = (Path(gopath) / "bin") if gopath else (Path.home() / "go" / "bin")
    return any((base / f"{comando}{extension}").is_file() for extension in (".exe", ""))


# `winget list` completo, cacheado UNA vez por proceso: las apps de escritorio
# (Antigravity IDE/2.0) no tienen comando en PATH, así que se detectan por su id.
_ESTADO_WINGET: dict = {"cargado": False, "texto": ""}


def _instalada_por_winget(id_winget: str, limite_segundos: float = 15.0) -> bool:
    if not id_winget:
        return False
    if not _ESTADO_WINGET["cargado"]:
        _ESTADO_WINGET["cargado"] = True
        if shutil.which("winget") is not None:
            try:
                completado = subprocess.run(
                    ["winget", "list", "--disable-interactivity"],
                    capture_output=True,
                    text=True,
                    timeout=limite_segundos,
                    encoding="utf-8",
                    errors="replace",
                )
                _ESTADO_WINGET["texto"] = completado.stdout or ""
            except Exception:
                _ESTADO_WINGET["texto"] = ""
    return id_winget.lower() in _ESTADO_WINGET["texto"].lower()


def sondear(
    herramienta: Herramienta,
    limite_segundos: float = 8.0,
) -> EstadoHerramienta:
    """Check whether an external tool is available and report its version."""
    from tramalia.i18n import t

    if shutil.which(herramienta.comando) is None:
        if herramienta.efimera and shutil.which("uv"):
            # corre vía uvx: no hay nada que instalar
            return EstadoHerramienta(herramienta, presente=True, version=t("doctor.ephemeral"))
        if herramienta.administrada_por_mise and _instalada_por_mise(herramienta.comando):
            return EstadoHerramienta(herramienta, presente=True, version=t("doctor.viamise"))
        if _instalada_por_uv(herramienta.comando):
            return EstadoHerramienta(herramienta, presente=True, version=t("doctor.viauv"))
        if _instalada_por_go(herramienta.comando):
            return EstadoHerramienta(herramienta, presente=True, version=t("doctor.viago"))
        if herramienta.id_winget and _instalada_por_winget(herramienta.id_winget):
            return EstadoHerramienta(herramienta, presente=True, version=t("doctor.viawinget"))
        return EstadoHerramienta(herramienta, presente=False)
    version = None
    try:
        completado = subprocess.run(
            [herramienta.comando, *herramienta.argumentos_version],
            capture_output=True,
            text=True,
            timeout=limite_segundos,
        )
        salida_cruda = (completado.stdout or completado.stderr or "").strip()
        if salida_cruda:
            version = salida_cruda.splitlines()[0].strip()
    except Exception:
        version = None
    return EstadoHerramienta(herramienta, presente=True, version=version)


# orden de preferencia para prellenar primary/reviewer en init: CLIs reales que
# pueden ejecutar `close` por shell. Excluye antigravity-ide/antigravity-2 (apps
# de escritorio sin shell propio) — no tiene sentido prellenarlas como ejecutor.
_ORDEN_DETECCION_AGENTES = ("claude", "codex", "opencode", "antigravity", "openclaw", "hermes")


def detectar_agentes_predeterminados() -> tuple[str, str]:
    """Select default primary and reviewer agents from installed command-line tools.

    Returns:
        A primary/reviewer pair. One installed agent fills both roles, while no
        installed agents falls back to the editable Codex/Claude example.
    """
    presentes = [
        clave
        for clave in _ORDEN_DETECCION_AGENTES
        if sondear(
            next(herramienta for herramienta in REGISTRO if herramienta.clave == clave)
        ).presente
    ]
    if len(presentes) >= 2:
        return presentes[0], presentes[1]
    if len(presentes) == 1:
        return presentes[0], presentes[0]
    return "codex", "claude"


def herramientas_relevantes(
    tecnologias: list[str],
    capacidades: tuple[str, ...],
) -> list[Herramienta]:
    """Return the tools that apply to the detected technologies and capabilities."""
    resultado: list[Herramienta] = []
    for herramienta in REGISTRO:
        if herramienta.categoria in ("bootstrap", "agent"):
            resultado.append(herramienta)
        elif herramienta.categoria == "stack" and any(
            tecnologia in tecnologias for tecnologia in herramienta.tecnologias
        ):
            resultado.append(herramienta)
        elif herramienta.categoria == "feature" and herramienta.capacidad in capacidades:
            resultado.append(herramienta)
    return resultado
