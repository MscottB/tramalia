"""Render con Rich si está disponible; si no, texto plano (terminal básica).

Así la CLI corre sin instalar nada y se ve bonita automáticamente cuando
instalas el extra `pretty` (rich + questionary).
"""

from __future__ import annotations

from tramalia.core.doctor import Report

_PLAIN = False

try:  # modo bonito opcional
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    _console: Console | None = Console()
    _HAS_RICH = True
except Exception:  # pragma: no cover - fallback stdlib
    _console = None
    _HAS_RICH = False


def set_plain(value: bool) -> None:
    global _PLAIN
    _PLAIN = value


def _rich() -> bool:
    return _HAS_RICH and not _PLAIN


def header(project: str, stack: list[str], initialized: bool) -> None:
    from tramalia import __version__

    estado = "inicializado" if initialized else "no inicializado"
    stack_txt = " · ".join(stack) if stack else "—"
    if _rich():
        _console.print(
            Panel(
                f"proyecto [bold]{project}[/bold]   stack [bold]{stack_txt}[/bold]   "
                f"estado [{'green' if initialized else 'yellow'}]{estado}[/]",
                title=f"Tramalia v{__version__}",
                border_style="cyan",
                box=box.ROUNDED,
            )
        )
    else:
        print("=" * 60)
        print(f"Tramalia v{__version__} · proyecto {project} · stack {stack_txt} · {estado}")
        print("=" * 60)


# los "feature" se subdividen por dominio para saber qué es contexto/memoria/etc.
_FEATURE_GROUP = {
    "context": "context",
    "memory": "memory",
    "security": "security",
    "database": "database",
    "ux": "ux",
    "databricks": "analytics",
    "init": "convention",
    "sync": "convention",
    "specs": "convention",
}
GROUP_ORDER = (
    "bootstrap",
    "stack",
    "context",
    "memory",
    "security",
    "database",
    "ux",
    "analytics",
    "convention",
    "agent",
)


def group_of(tool) -> str:
    if tool.category == "feature":
        return _FEATURE_GROUP.get(tool.feature, "convention")
    return tool.category


def group_statuses(statuses) -> list[tuple[str, list]]:
    """Agrupa los statuses del doctor por dominio, en orden fijo."""
    groups: list[tuple[str, list]] = []
    for g in GROUP_ORDER:
        rows = [s for s in statuses if group_of(s.tool) == g]
        if rows:
            groups.append((g, rows))
    return groups


def _hint_for(tool) -> str:
    """La mejor sugerencia de instalación para ESTE sistema (no un hint fijo)."""
    from tramalia.core import installer

    best = installer.best_auto(tool)
    if best:
        return best.display
    opts = installer.options_for(tool)
    return opts[0].display if opts else tool.install_hint


def _runtime_note(tool, plain: bool = False) -> str:
    """Si automatizar la tool requiere un runtime ausente (Node/Go), avisarlo."""
    from tramalia.core import installer

    rt = installer.blocking_runtime(tool)
    if not rt:
        return ""
    name = installer._RUNTIME_NAME.get(rt, rt)
    if plain:
        return f"  · requiere {name}"
    return f"  [magenta]· requiere {name}[/magenta]"


def doctor(report: Report) -> int:
    """Imprime el diagnóstico agrupado. Exit 0 si nada bloqueante falta."""
    stack_txt = " · ".join(report.stack) if report.stack else "—"
    from tramalia.i18n import t

    def fila(s):
        if s.present:
            return t("tui.status.ok"), (s.version or "—")
        estado = (
            t("tui.status.optional")
            if s.tool.category in ("feature", "agent")
            else t("tui.status.missing")
        )
        return estado, _hint_for(s.tool)

    if _rich():
        table = Table(box=box.SIMPLE_HEAVY, expand=False)
        table.add_column(t("tui.col.tool"), style="bold")
        table.add_column(t("tui.col.purpose"), overflow="fold", max_width=32)
        table.add_column(t("tui.col.state"))
        table.add_column(t("tui.col.detail"), overflow="fold")
        for cat, rows in group_statuses(report.statuses):
            table.add_row(f"[bold cyan]· {t('doctor.group.' + cat)}[/]", "", "", "")
            for s in rows:
                estado, detalle = fila(s)
                if not s.present:
                    detalle += _runtime_note(s.tool)
                table.add_row(f"  {s.tool.cmd}", s.tool.role, estado, detalle)
        _console.print(f"\n[dim]{t('doctor.stack')}[/dim] {stack_txt}")
        _console.print(table)
    else:
        print(f"\n{t('doctor.stack')} {stack_txt}")
        for cat, rows in group_statuses(report.statuses):
            print(f"\n-- {t('doctor.group.' + cat)} " + "-" * 40)
            for s in rows:
                _, detalle = fila(s)
                estado = (
                    "instalada"
                    if s.present
                    else "no-inst(opc)"
                    if s.tool.category in ("feature", "agent")
                    else "NO INSTALADA"
                )
                if not s.present:
                    detalle += _runtime_note(s.tool, plain=True)
                print(f"{s.tool.cmd:<13}{estado:<14}{s.tool.role} — {detalle}")

    if not getattr(report, "uv_bin_on_path", True):
        _warn(t("doctor.path.uv.missing"))

    if report.needs_node:
        _warn(f"Node no está instalado y lo requieren: {', '.join(report.node_tools)}.")
        _info("instálalo con `mise use node@22` (o nvm) para usar sync / ux / context completo.")

    blocking = report.missing_blocking
    optional = report.missing_optional
    if blocking:
        names = ", ".join(s.tool.cmd for s in blocking)
        _warn(f"faltan herramientas requeridas: {names}")
        _info("instálalas con los comandos de arriba y vuelve a correr `tramalia doctor`.")
        _info("una vez que tengas mise, el resto se instala con `mise install`.")
        return 1
    if optional:
        names = ", ".join(s.tool.cmd for s in optional)
        _info(f"opcionales ausentes (se activan al usar su gate): {names}")
    _ok("todo lo requerido está presente.")
    return 0


def _ok(msg: str) -> None:
    _console.print(f"[green]✓[/green] {msg}") if _rich() else print(f"[ok] {msg}")


def _warn(msg: str) -> None:
    _console.print(f"[yellow]▲[/yellow] {msg}") if _rich() else print(f"[!] {msg}")


def _info(msg: str) -> None:
    _console.print(f"[cyan]i[/cyan] {msg}") if _rich() else print(f"[i] {msg}")


def _err(msg: str) -> None:
    _console.print(f"[red]✗[/red] {msg}") if _rich() else print(f"[x] {msg}")


# alias públicos
ok, warn, info, err = _ok, _warn, _info, _err
