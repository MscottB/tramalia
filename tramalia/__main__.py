"""Expose Tramalia's stable public commands through an argparse entry point."""

from __future__ import annotations

import argparse
import sys
from typing import Protocol, runtime_checkable

from tramalia import __version__


@runtime_checkable
class _FlujoReconfigurable(Protocol):
    def reconfigure(self, *, encoding: str) -> None:
        """Update the text encoding exposed by a console stream."""


def construir_parser() -> argparse.ArgumentParser:
    """Build the backwards-compatible public CLI parser.

    Returns:
        Parser containing Tramalia's established English commands and arguments.
    """
    p = argparse.ArgumentParser(
        prog="tramalia",
        description="Capa fina que orquesta herramientas externas para desarrollo con agentes IA.",
    )
    p.add_argument("--version", action="version", version=f"tramalia {__version__}")
    p.add_argument("--plain", action="store_true", help="salida sin colores (terminal básica)")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("menu", help="menú interactivo")
    d = sub.add_parser("doctor", help="diagnostica las herramientas requeridas")
    d.add_argument("--fix", action="store_true", help="intenta instalar lo que falte vía mise")
    sub.add_parser("detect", help="detecta el stack del proyecto")
    ini = sub.add_parser("init", help="inicializa la estructura (copier)")
    ini.add_argument(
        "--with-headroom",
        action="store_true",
        help="agrega Headroom (compresión) al .mcp.json (opt-in explícito)",
    )
    ini.add_argument(
        "--with-ponytail",
        action="store_true",
        help="agrega el MCP de Ponytail al .mcp.json (requiere `tramalia skills` + Node)",
    )
    ini.add_argument(
        "--adopt",
        action="store_true",
        help="integra el gobierno en un AGENTS.md/.mcp.json existentes (merge no destructivo)",
    )
    ini.add_argument(
        "--with-notebook-exec",
        action="store_true",
        help="agrega un gate que EJECUTA los notebooks (jupyter execute); opt-in, requiere datos/entorno",
    )
    ini.add_argument(
        "--model-cap",
        default=None,
        choices=["fable", "opus", "sonnet", "haiku", "none"],
        help="tope de modelos para los subagentes (default: none = sin tope)",
    )
    sub.add_parser(
        "upgrade", help="actualiza un repo ya inicializado (agrega lo nuevo, no pisa lo existente)"
    )
    ag = sub.add_parser("agents", help="subagentes: list | cap <fable|opus|sonnet|haiku|none>")
    ag.add_argument("action", nargs="?", choices=["list", "cap"], default="list")
    ag.add_argument(
        "name",
        nargs="?",
        default=None,
        help="tope de modelos (para `cap`): fable|opus|sonnet|haiku|none",
    )
    sub.add_parser("gates", help="ejecuta quality gates (mise run gates)")
    ctx = sub.add_parser(
        "context", help="contexto/token-saver: build (default) | list | set <backend>"
    )
    ctx.add_argument("action", nargs="?", choices=["build", "list", "set"], default="build")
    ctx.add_argument(
        "name", nargs="?", default=None, help="nombre del backend (para `set`; ver `context list`)"
    )
    ev = sub.add_parser("evidence", help="genera el evidence pack (ej: tramalia evidence TASK-001)")
    ev.add_argument(
        "task_pos",
        nargs="?",
        metavar="TAREA",
        default=None,
        help="ID de la tarea; si se omite, se usa .tramalia/current-task.md",
    )
    ev.add_argument("--task", default=None, help="ID de la tarea (alternativa al posicional)")
    ev.add_argument(
        "--engram", action="store_true", help="exporta a Engram (memoria persistente N2, opt-in)"
    )
    ho = sub.add_parser(
        "handoff", help="crea un handoff multiagente (ej: tramalia handoff TASK-001)"
    )
    ho.add_argument(
        "task_pos",
        nargs="?",
        metavar="TAREA",
        default=None,
        help="ID de la tarea; si se omite, se usa .tramalia/current-task.md",
    )
    ho.add_argument("--task", default=None, help="ID de la tarea (alternativa al posicional)")
    ho.add_argument(
        "--agent",
        default=None,
        help="quién ejecutó la tarea — solo registro (def: config agents.primary)",
    )
    ho.add_argument(
        "--reviewer",
        default=None,
        help="quién revisa — solo registro (def: config agents.reviewer)",
    )
    ho.add_argument(
        "--engram", action="store_true", help="exporta a Engram (memoria persistente N2, opt-in)"
    )
    cl = sub.add_parser(
        "close", help="ritual de cierre: gates → evidence → handoff (ej: tramalia close TASK-001)"
    )
    cl.add_argument(
        "task_pos",
        nargs="?",
        metavar="TAREA",
        default=None,
        help="ID de la tarea; si se omite, se usa .tramalia/current-task.md",
    )
    cl.add_argument("--task", default=None, help="ID de la tarea (alternativa al posicional)")
    cl.add_argument(
        "--agent",
        default=None,
        help="quién ejecutó la tarea — solo registro de auditoría, Tramalia no lo invoca (def: config agents.primary)",
    )
    cl.add_argument(
        "--reviewer",
        default=None,
        help="quién revisa el cierre — solo registro (def: config agents.reviewer)",
    )
    cl.add_argument(
        "--allow-fail",
        action="store_true",
        help="alias deprecado: exige una excepción razonada completa",
    )
    cl.add_argument("--razon-excepcion", default="", help="motivo concreto de la excepción")
    cl.add_argument("--riesgo-aceptado", default="", help="riesgo aceptado por el revisor")
    cl.add_argument("--control-afectado", default="", help="puerta o control cubierto")
    cl.add_argument(
        "--referencia-excepcion",
        default="",
        help="issue, decisión o documento que respalda la excepción",
    )
    cl.add_argument(
        "--revisor-excepcion",
        default="",
        help="responsable que acepta explícitamente el riesgo",
    )
    cl.add_argument(
        "--expira-en",
        default="",
        help="fecha ISO 8601 de expiración, con zona horaria",
    )
    cl.add_argument(
        "--condicion-remediacion",
        default="",
        help="condición verificable que cierra la excepción",
    )
    cl.add_argument(
        "--model",
        default=None,
        help="modelo usado por el agente ejecutor (queda en metadatos.json)",
    )
    cl.add_argument("--engram", action="store_true", help="exporta el cierre a Engram (N2)")
    sub.add_parser("log", help="pista de auditoría: cierres registrados (evidence packs)")
    sy = sub.add_parser("sync", help="propaga reglas y subagentes a otros agentes (rulesync)")
    sy.add_argument(
        "--to", default=None, help="targets separados por coma (def: copilot,cursor,cline)"
    )
    sy.add_argument(
        "--features", default=None, help="features de rulesync a propagar (def: rules,subagents)"
    )
    sk = sub.add_parser(
        "skills",
        help=(
            "administra skills (.tramalia/habilidades.toml): sync rehidrata "
            "SHA fijados y update mueve locks explícitamente"
        ),
    )
    sk.add_argument(
        "action",
        nargs="?",
        choices=["sync", "update", "list", "outdated", "enable", "disable", "add"],
        default="sync",
    )
    sk.add_argument(
        "name",
        nargs="?",
        default=None,
        help=(
            "nombre (sync/update/enable/disable) o URL git (add). "
            "En sync/update, limita la operación a esa skill"
        ),
    )
    sk.add_argument(
        "alias", nargs="?", default=None, help="nombre opcional para `add` (default: del URL)"
    )
    sub.add_parser(
        "update",
        help="actualiza mise y rehidrata skills sin mover sus locks Team",
    )
    sub.add_parser("mcp", help="levanta el Tramalia MCP (fachada nivel 1, stdio)")
    sub.add_parser("ui", help="abre el dashboard TUI (requiere extra [tui])")
    return p


def main(argv: list[str] | None = None) -> int:
    """Run Tramalia's command-line surface.

    Args:
        argv: Optional argument list without the executable name.

    Returns:
        Stable process exit code for the selected command.
    """
    # En Windows la consola puede no ser UTF-8; lo forzamos para acentos y símbolos.
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, _FlujoReconfigurable):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                # Algunos flujos embebidos anuncian reconfigure, pero no permiten usarlo.
                pass

    argumentos_crudos = list(argv if argv is not None else sys.argv[1:])
    # --plain se acepta en cualquier posición; se extrae antes de parsear
    plano = "--plain" in argumentos_crudos
    argumentos_crudos = [valor for valor in argumentos_crudos if valor != "--plain"]
    argumentos = construir_parser().parse_args(argumentos_crudos)

    from tramalia.cli import renderizado

    if plano:
        renderizado.fijar_plano(True)

    from tramalia.cli import comandos

    return comandos.despachar(argumentos.command or "menu", argumentos)


if __name__ == "__main__":
    raise SystemExit(main())
