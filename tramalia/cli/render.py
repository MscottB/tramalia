"""Render con Rich si está disponible; si no, texto plano (terminal básica).

Así la CLI corre sin instalar nada y se ve bonita automáticamente cuando
instalas el extra `pretty` (rich + questionary).
"""

from __future__ import annotations

from tramalia.core.doctor import Report

_PLAIN = False

try:  # modo bonito opcional
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    _console: "Console | None" = Console()
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
    estado = "inicializado" if initialized else "no inicializado"
    stack_txt = " · ".join(stack) if stack else "—"
    if _rich():
        _console.print(Panel(
            f"proyecto [bold]{project}[/bold]   stack [bold]{stack_txt}[/bold]   "
            f"estado [{'green' if initialized else 'yellow'}]{estado}[/]",
            title="Tramalia", border_style="cyan", box=box.ROUNDED,
        ))
    else:
        print("=" * 60)
        print(f"Tramalia · proyecto {project} · stack {stack_txt} · {estado}")
        print("=" * 60)


GROUP_ORDER = ("bootstrap", "stack", "feature", "agent")


def group_statuses(statuses) -> list[tuple[str, list]]:
    """Agrupa los statuses del doctor por categoría, en orden fijo."""
    groups: list[tuple[str, list]] = []
    for cat in GROUP_ORDER:
        rows = [s for s in statuses if s.tool.category == cat]
        if rows:
            groups.append((cat, rows))
    return groups


def _hint_for(tool) -> str:
    """La mejor sugerencia de instalación para ESTE sistema (no un hint fijo)."""
    from tramalia.core import installer
    best = installer.best_auto(tool)
    if best:
        return best.display
    opts = installer.options_for(tool)
    return opts[0].display if opts else tool.install_hint


def doctor(report: Report) -> int:
    """Imprime el diagnóstico agrupado. Exit 0 si nada bloqueante falta."""
    stack_txt = " · ".join(report.stack) if report.stack else "—"
    from tramalia.i18n import t

    def fila(s):
        if s.present:
            return t("tui.status.ok"), (s.version or "—")
        estado = (t("tui.status.optional") if s.tool.category in ("feature", "agent")
                  else t("tui.status.missing"))
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
                if s.tool.runtime == "node" and not s.present:
                    detalle += "  [magenta]· Node[/magenta]"
                table.add_row(f"  {s.tool.cmd}", s.tool.role, estado, detalle)
        _console.print(f"\n[dim]{t('doctor.stack')}[/dim] {stack_txt}")
        _console.print(table)
    else:
        print(f"\n{t('doctor.stack')} {stack_txt}")
        for cat, rows in group_statuses(report.statuses):
            print(f"\n-- {t('doctor.group.' + cat)} " + "-" * 40)
            for s in rows:
                _, detalle = fila(s)
                estado = ("ok" if s.present else
                          "opcional" if s.tool.category in ("feature", "agent")
                          else "FALTA")
                if s.tool.runtime == "node" and not s.present:
                    detalle += "  · Node"
                print(f"{s.tool.cmd:<13}{estado:<10}{s.tool.role} — {detalle}")

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
