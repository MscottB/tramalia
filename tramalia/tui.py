"""Dashboard TUI opcional (Textual) — `tramalia ui`.

Misma regla que la fachada MCP: NO implementa lógica nueva; solo lee e invoca el
core existente (doctor, log, close). Extra opcional: pip install "tramalia-cli[tui]".
"""

from __future__ import annotations

import json
from pathlib import Path


def build_app():
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical, VerticalScroll
    from textual.widgets import (Button, DataTable, Footer, Header, Input,
                                 RichLog, Static, TabbedContent, TabPane)

    from tramalia.core import doctor as doctor_core
    from tramalia.core import governance
    from tramalia.core.detect import detect_stack

    class TramaliaApp(App):
        TITLE = "Tramalia"
        SUB_TITLE = "gobierno y evidencia repo-first"
        BINDINGS = [("q", "quit", "Salir"), ("r", "refresh", "Refrescar")]
        CSS = """
        #estado { padding: 0 1; color: $text-muted; }
        #detalle-log { padding: 0 1; height: 1fr; overflow-y: auto; }
        #cierre-form Input { margin: 0 1; }
        #btn-close { margin: 1 1; }
        #salida { height: 1fr; margin: 0 1; border: round $primary; }
        DataTable { height: 1fr; }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            with TabbedContent(initial="resumen"):
                with TabPane("Resumen", id="resumen"):
                    yield Static(id="estado")
                    yield DataTable(id="tabla-doctor", cursor_type="row")
                with TabPane("Auditoría", id="auditoria"):
                    with Horizontal():
                        yield DataTable(id="tabla-log", cursor_type="row")
                        yield Static("selecciona un cierre →", id="detalle-log")
                with TabPane("Cierre", id="cierre"):
                    with Vertical(id="cierre-form"):
                        yield Input(placeholder="ID de tarea (TASK-001)", id="in-task")
                        yield Input(placeholder="agente ejecutor (codex)", id="in-agent")
                        yield Input(placeholder="agente revisor (claude)", id="in-reviewer")
                        yield Button("▶ Ejecutar close", id="btn-close", variant="primary")
                        yield RichLog(id="salida", wrap=True, markup=True)
            yield Footer()

        def on_mount(self) -> None:
            self.action_refresh()

        def action_refresh(self) -> None:
            root = Path.cwd()
            stack = detect_stack(root)
            report = doctor_core.diagnose(root)
            self.query_one("#estado", Static).update(
                f"proyecto [b]{root.name}[/b] · stack {', '.join(stack) or '—'} · "
                f"gates: {', '.join(report.features)}"
            )
            tabla = self.query_one("#tabla-doctor", DataTable)
            tabla.clear(columns=True)
            tabla.add_columns("herramienta", "estado", "detalle / cómo obtenerla")
            for s in report.statuses:
                if s.present:
                    mark = "[green]✓ ok[/green]"
                elif s.tool.category == "feature":
                    mark = "[yellow]○ opcional[/yellow]"
                else:
                    mark = "[red]✗ falta[/red]"
                tabla.add_row(s.tool.cmd, mark, s.version or s.tool.install_hint)

            tlog = self.query_one("#tabla-log", DataTable)
            tlog.clear(columns=True)
            tlog.add_columns("cierre", "estado", "agente")
            for e in governance.read_log(root):
                tlog.add_row(e["id"], str(e.get("status") or "—"), e.get("agent") or "—")

        def on_data_table_row_selected(self, event) -> None:
            if event.data_table.id != "tabla-log":
                return
            row = event.data_table.get_row(event.row_key)
            meta = Path.cwd() / ".tramalia" / "evidence" / str(row[0]) / "metadata.json"
            detalle = self.query_one("#detalle-log", Static)
            if meta.exists():
                data = json.loads(meta.read_text(encoding="utf-8"))
                detalle.update(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                detalle.update("(cierre sin metadata.json — pack antiguo)")

        def on_button_pressed(self, event) -> None:
            if event.button.id != "btn-close":
                return
            task = self.query_one("#in-task", Input).value.strip() or "TASK-000"
            agent = self.query_one("#in-agent", Input).value.strip()
            reviewer = self.query_one("#in-reviewer", Input).value.strip()
            salida = self.query_one("#salida", RichLog)
            salida.write(f"cerrando [b]{task}[/b]…")
            event.button.disabled = True
            self.run_worker(lambda: self._run_close(task, agent, reviewer),
                            thread=True, exclusive=True)

        def _run_close(self, task: str, agent: str, reviewer: str) -> None:
            try:
                result = governance.close(Path.cwd(), task, agent, reviewer)
            except Exception as exc:  # nunca dejar la UI colgada
                self.call_from_thread(self._show_close_error, str(exc))
                return
            self.call_from_thread(self._show_close_result, result)

        def _show_close_error(self, message: str) -> None:
            self.query_one("#salida", RichLog).write(f"[red]error:[/red] {message}")
            self.query_one("#btn-close", Button).disabled = False

        def _show_close_result(self, result) -> None:
            salida = self.query_one("#salida", RichLog)
            if not result.gates_ran:
                salida.write("[yellow]▲ gates no ejecutados (mise ausente) — excepción documentada[/yellow]")
            for name, code, _ in result.gates:
                mark = "[green]ok[/green]" if code == 0 else "[red]FALLA[/red]"
                salida.write(f"gate {name}: {mark}")
            salida.write(f"estado: [b]{result.status}[/b]")
            salida.write(f"evidence: {result.evidence_dir}")
            if result.blocked:
                salida.write("[red]✗ cierre BLOQUEADO por gates fallidos[/red]")
            else:
                salida.write("[green]✓ tarea cerrada con evidencia verificable[/green]")
            self.query_one("#btn-close", Button).disabled = False
            self.action_refresh()

    return TramaliaApp


def run() -> None:
    build_app()().run()
