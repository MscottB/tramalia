"""Dashboard TUI opcional (Textual) — `tramalia ui`.

Misma regla que la fachada MCP: NO implementa lógica nueva; solo lee e invoca el
core existente (doctor, log, close, init, mise). Textos vía tramalia.i18n
(es/en; agrega idiomas con un JSON, sin tocar código).
"""

from __future__ import annotations

import json
from pathlib import Path

from tramalia.i18n import t


def build_app():
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.widgets import (Button, DataTable, Footer, Header, Input,
                                 RichLog, Static, TabbedContent, TabPane)

    from tramalia.core import doctor as doctor_core
    from tramalia.core import governance, project
    from tramalia.core.detect import detect_stack
    from tramalia.core.scaffold import scaffold
    from tramalia.core.detect import enabled_features

    _LOG_MARKS = {
        "passed": t("log.passed"),
        "passed_with_exceptions": t("log.exceptions"),
        "blocked": t("log.blocked"),
        "no_gates": t("log.nogates"),
        None: "○ —",
    }

    class TramaliaApp(App):
        TITLE = "Tramalia"
        SUB_TITLE = t("tui.subtitle")
        # la command palette de Textual está en inglés: fuera, por coherencia i18n
        ENABLE_COMMAND_PALETTE = False
        BINDINGS = [
            ("q", "quit", t("tui.binding.quit")),
            ("r", "refresh", t("tui.binding.refresh")),
            ("i", "install_missing", t("tui.binding.install")),
        ]
        CSS = """
        #estado, #gates-linea, #lastclose { padding: 0 1; }
        #detalle-log { padding: 0 1; height: 1fr; overflow-y: auto; }
        #cierre-form Input { margin: 0 1; }
        #btn-close, #btn-init { margin: 1 1; }
        #taskinfo { padding: 0 1; color: $text-muted; max-height: 10; overflow-y: auto; }
        #salida { height: 1fr; margin: 0 1; border: round $primary; }
        #aviso-uninit, #aviso-audit { padding: 1 1; }
        DataTable { height: 1fr; }
        """

        def compose(self) -> ComposeResult:
            yield Header()
            with TabbedContent(initial="resumen"):
                with TabPane(t("tui.tab.summary"), id="resumen"):
                    yield Static(id="estado")
                    yield Static(id="gates-linea")
                    yield Static(id="lastclose")
                    yield DataTable(id="tabla-doctor", cursor_type="row")
                with TabPane(t("tui.tab.audit"), id="auditoria"):
                    yield Static(id="aviso-audit")
                    with Horizontal():
                        yield DataTable(id="tabla-log", cursor_type="row")
                        yield Static(t("tui.audit.select"), id="detalle-log")
                with TabPane(t("tui.tab.close"), id="cierre"):
                    yield Static(id="aviso-uninit")
                    yield Button(t("tui.close.init.button"), id="btn-init", variant="warning")
                    with Vertical(id="cierre-form"):
                        yield Input(placeholder=t("tui.close.task.placeholder"), id="in-task")
                        yield Static(id="taskinfo")
                        yield Input(placeholder=t("tui.close.agent.placeholder"), id="in-agent")
                        yield Input(placeholder=t("tui.close.reviewer.placeholder"), id="in-reviewer")
                        yield Input(placeholder=t("tui.close.model.placeholder"), id="in-model")
                        yield Button(t("tui.close.button"), id="btn-close", variant="primary")
                        yield RichLog(id="salida", wrap=True, markup=True)
            yield Footer()

        def on_mount(self) -> None:
            self.action_refresh()

        # ------------------------------------------------------------ refresh
        def action_refresh(self) -> None:
            root = Path.cwd()
            initialized = project.is_initialized(root)
            stack = detect_stack(root)
            report = doctor_core.diagnose(root)

            estado = (t("tui.state.initialized") if initialized
                      else t("tui.state.uninitialized"))
            self.query_one("#estado", Static).update(
                t("tui.header", path=str(root), stack=", ".join(stack) or "—",
                  estado=estado))

            # gates REALES del proyecto (mise.toml), no features internas
            gates = governance.gate_tasks(root)
            self.query_one("#gates-linea", Static).update(
                t("tui.gates.line", gates=" · ".join(gates)) if gates
                else t("tui.gates.none"))

            entries = governance.read_log(root)
            last = ""
            if entries:
                e = entries[0]
                last = t("tui.lastclose", id=e["id"],
                         mark=_LOG_MARKS.get(e.get("status"), "○ —"))
            self.query_one("#lastclose", Static).update(last)

            tabla = self.query_one("#tabla-doctor", DataTable)
            tabla.clear(columns=True)
            tabla.add_columns(t("tui.col.tool"), t("tui.col.purpose"),
                              t("tui.col.state"), t("tui.col.detail"))
            for s in report.statuses:
                if s.present:
                    mark, detalle = t("tui.status.ok"), (s.version or "—")
                elif s.tool.category in ("feature", "agent"):
                    mark, detalle = t("tui.status.optional"), s.tool.install_hint
                else:
                    mark, detalle = t("tui.status.missing"), s.tool.install_hint
                tabla.add_row(s.tool.cmd, s.tool.role, mark, detalle)

            self._refresh_audit(root, initialized, entries)
            self._refresh_close(root, initialized)

        def _refresh_audit(self, root, initialized, entries) -> None:
            aviso = self.query_one("#aviso-audit", Static)
            tabla = self.query_one("#tabla-log", DataTable)
            tabla.clear(columns=True)
            if not initialized:
                aviso.update(t("tui.audit.uninit"))
                return
            if not entries:
                aviso.update(t("tui.audit.empty"))
                return
            aviso.update("")
            tabla.add_columns(t("tui.col.close"), t("tui.col.status"), t("tui.col.agent"))
            for e in entries:
                modelo = f" ({e['model']})" if e.get("model") else ""
                tabla.add_row(e["id"], str(e.get("status") or "—"),
                              (e.get("agent") or "—") + modelo)

        def _refresh_close(self, root, initialized) -> None:
            aviso = self.query_one("#aviso-uninit", Static)
            btn_init = self.query_one("#btn-init", Button)
            form = self.query_one("#cierre-form", Vertical)
            if not initialized:
                aviso.update(t("tui.close.uninit"))
                btn_init.display = True
                form.display = False
                return
            aviso.update("")
            btn_init.display = False
            form.display = True
            # prellenado con los defaults REALES del proyecto (no ejemplos)
            primary, reviewer = project.default_agents(root)
            in_task = self.query_one("#in-task", Input)
            if not in_task.value:
                in_task.value = project.current_task_id(root) or ""
            in_agent = self.query_one("#in-agent", Input)
            if not in_agent.value:
                in_agent.value = primary
            in_rev = self.query_one("#in-reviewer", Input)
            if not in_rev.value:
                in_rev.value = reviewer
            self._show_task_info(root, in_task.value)

        def _show_task_info(self, root, task_id: str) -> None:
            info = self.query_one("#taskinfo", Static)
            if not task_id.strip():
                info.update("")
                return
            desc = project.task_description(root, task_id.strip())
            if desc:
                info.update(f"[dim]{t('tui.close.taskinfo.header')}[/dim]\n{desc}")
            else:
                info.update(f"[yellow]{t('tui.close.taskinfo.none')}[/yellow]")

        # ------------------------------------------------------------ eventos
        def on_input_changed(self, event) -> None:
            if event.input.id == "in-task":
                self._show_task_info(Path.cwd(), event.value)

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
                detalle.update(t("tui.audit.nometa"))

        def on_button_pressed(self, event) -> None:
            if event.button.id == "btn-init":
                self._run_init(event.button)
            elif event.button.id == "btn-close":
                self._start_close(event.button)

        # ------------------------------------------------------------ init
        def _run_init(self, button) -> None:
            button.disabled = True
            root = Path.cwd()
            stack = detect_stack(root)
            scaffold(root, {
                "project_name": root.name, "stacks": stack,
                "features": enabled_features(stack),
                "primary_agent": "codex", "reviewer_agent": "claude",
            })
            button.disabled = False
            self.notify(t("tui.init.done"), markup=False)
            self.action_refresh()

        # ------------------------------------------------------------ install
        def action_install_missing(self) -> None:
            from tramalia.core import proc
            salida = self.query_one("#salida", RichLog)
            self.query_one(TabbedContent).active = "cierre"
            if proc.which("mise") is None:
                salida.write(t("tui.install.nomise"))
                return
            salida.write(t("tui.install.running"))
            self.run_worker(self._mise_install, thread=True, exclusive=True)

        def _mise_install(self) -> None:
            from tramalia.core import proc
            try:
                cp = proc.run(["mise", "install"], capture_output=True, text=True,
                              timeout=900)
                out = (cp.stdout or "") + (cp.stderr or "")
            except Exception as exc:
                out = str(exc)
            self.call_from_thread(self._after_install, out)

        def _after_install(self, out: str) -> None:
            salida = self.query_one("#salida", RichLog)
            for line in out.strip().splitlines()[-15:]:
                salida.write(line)
            salida.write(t("tui.install.done"))
            self.action_refresh()

        # ------------------------------------------------------------ close
        def _start_close(self, button) -> None:
            root = Path.cwd()
            salida = self.query_one("#salida", RichLog)
            if not project.is_initialized(root):
                salida.write(t("tui.close.uninit"))
                return
            task = self.query_one("#in-task", Input).value.strip()
            if not task:
                salida.write(t("tui.close.needtask"))
                return
            agent = self.query_one("#in-agent", Input).value.strip()
            reviewer = self.query_one("#in-reviewer", Input).value.strip()
            model = self.query_one("#in-model", Input).value.strip()
            salida.write(t("tui.close.running", task=task))
            button.disabled = True
            self.run_worker(lambda: self._run_close(task, agent, reviewer, model),
                            thread=True, exclusive=True)

        def _run_close(self, task, agent, reviewer, model) -> None:
            from tramalia.core import governance as gov
            try:
                result = gov.close(Path.cwd(), task, agent, reviewer, model=model)
            except Exception as exc:
                self.call_from_thread(self._show_close_error, str(exc))
                return
            self.call_from_thread(self._show_close_result, result)

        def _show_close_error(self, message: str) -> None:
            self.query_one("#salida", RichLog).write(t("tui.close.error", msg=message))
            self.query_one("#btn-close", Button).disabled = False

        def _show_close_result(self, result) -> None:
            salida = self.query_one("#salida", RichLog)
            if not result.gates_ran:
                salida.write(t("tui.close.nogates"))
            for name, code, _ in result.gates:
                salida.write(t("tui.close.gate.ok", name=name) if code == 0
                             else t("tui.close.gate.fail", name=name))
            salida.write(t("tui.close.status", status=result.status))
            salida.write(t("tui.close.evidence", dir=str(result.evidence_dir)))
            if result.blocked:
                salida.write(t("tui.close.blocked"))
            elif result.status == "no_gates":
                salida.write(t("tui.close.done.nogates"))
            else:
                salida.write(t("tui.close.done"))
            self.query_one("#btn-close", Button).disabled = False
            self.action_refresh()

    return TramaliaApp


def run() -> None:
    build_app()().run()
