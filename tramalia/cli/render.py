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


_NEED = {"bootstrap": "base", "stack": "stack"}


def _need_label(tool) -> str:
    from tramalia.i18n import t
    if tool.category == "feature":
        return f"gate:{tool.feature}"
    if tool.category == "agent":
        return t("doctor.need.agent")
    if tool.category == "bootstrap":
        return t("doctor.need.base")
    if tool.category == "stack":
        return t("doctor.need.stack")
    return _NEED.get(tool.category, tool.category)


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


def doctor(report: Report) -> int:
    """Imprime el diagnóstico. Devuelve el exit code (0 si nada bloqueante falta)."""
    stack_txt = " · ".join(report.stack) if report.stack else "—"
    from tramalia.i18n import t
    if _rich():
        table = Table(box=box.SIMPLE_HEAVY, expand=False)
        table.add_column(t("tui.col.tool"), style="bold")
        table.add_column(t("tui.col.purpose"), overflow="fold", max_width=32)
        table.add_column("tipo", style="dim")
        table.add_column(t("tui.col.state"))
        table.add_column(t("tui.col.detail"), overflow="fold")
        for s in report.statuses:
            if s.present:
                estado = t("tui.status.ok")
                detalle = s.version or "—"
            elif s.tool.category in ("feature", "agent"):
                estado = t("tui.status.optional")
                detalle = s.tool.install_hint
            else:
                estado = t("tui.status.missing")
                detalle = s.tool.install_hint
            if s.tool.runtime == "node":
                detalle += "  [magenta]· Node[/magenta]"
            table.add_row(s.tool.cmd, s.tool.role, _need_label(s.tool), estado, detalle)
        _console.print(f"\n[dim]{t('doctor.stack')}[/dim] {stack_txt}")
        _console.print(table)
    else:
        print(f"\n{t('doctor.stack')} {stack_txt}")
        print(f"{'tool':<13}{'tipo':<15}{'estado':<10}para qué / detalle")
        print("-" * 78)
        for s in report.statuses:
            if s.present:
                estado, detalle = "ok", (s.version or "—")
            elif s.tool.category in ("feature", "agent"):
                estado, detalle = "opcional", s.tool.install_hint
            else:
                estado, detalle = "FALTA", s.tool.install_hint
            if s.tool.runtime == "node":
                detalle += "  · Node"
            print(f"{s.tool.cmd:<13}{_need_label(s.tool):<15}{estado:<10}{s.tool.role} — {detalle}")

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
