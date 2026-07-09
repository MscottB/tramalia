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
    from textual.screen import ModalScreen
    from textual.widgets import (Button, DataTable, Footer, Header, Input,
                                 RichLog, SelectionList, Static, TabbedContent,
                                 TabPane)
    from textual.widgets.selection_list import Selection

    from tramalia.core import doctor as doctor_core
    from tramalia.core import governance, installer, project
    from tramalia.core import skills as skills_core
    from tramalia.core.detect import detect_stack
    from tramalia.core.scaffold import scaffold
    from tramalia.core.detect import enabled_features

    class InstallScreen(ModalScreen):
        """Selección múltiple de qué instalar. Muestra TODAS las faltantes:
        las automatizables como opciones marcables, y las que solo tienen vía
        manual como lista visible (con su comando), para que ninguna se omita.
        """

        CSS = """
        InstallScreen { align: center middle; }
        #inst-box { width: 96; max-height: 85%; border: round $primary;
                    background: $surface; padding: 1 2; }
        #inst-manual { color: $text-muted; padding: 1 0 0 0; }
        #inst-botones { height: 3; align-horizontal: right; }
        #inst-botones Button { margin-left: 2; }
        """

        def __init__(self, plans, manuals):
            super().__init__()
            self._plans = plans      # [(label, InstallOption)] automatizables
            self._manuals = manuals  # [(label, comando_str)] solo manual

        def compose(self) -> ComposeResult:
            with Vertical(id="inst-box"):
                yield Static(f"[b]{t('tui.install.title')}[/b]")
                if self._plans:
                    yield SelectionList(*[
                        Selection(f"{label} — {opt.display}", idx, True)
                        for idx, (label, opt) in enumerate(self._plans)
                    ])
                if self._manuals:
                    lineas = "\n".join(f"  • {label} — {cmd}" for label, cmd in self._manuals)
                    yield Static(f"[dim]{t('tui.install.manual.header')}\n{lineas}[/dim]",
                                 id="inst-manual")
                with Horizontal(id="inst-botones"):
                    yield Button(t("tui.install.button"), id="inst-ok", variant="primary")
                    yield Button(t("tui.install.cancel"), id="inst-cancel")

        def on_button_pressed(self, event) -> None:
            if event.button.id == "inst-ok" and self._plans:
                seleccion = self.query_one(SelectionList).selected
                self.dismiss([self._plans[i] for i in seleccion])
            else:
                self.dismiss([])

    _LOG_MARKS = {
        "passed": t("log.passed"),
        "passed_with_exceptions": t("log.exceptions"),
        "blocked": t("log.blocked"),
        "no_gates": t("log.nogates"),
        None: "○ —",
    }

    from tramalia import __version__ as _tramalia_version

    class TramaliaApp(App):
        TITLE = f"Tramalia v{_tramalia_version}"
        SUB_TITLE = t("tui.subtitle")
        # la command palette de Textual está en inglés: fuera, por coherencia i18n
        ENABLE_COMMAND_PALETTE = False
        BINDINGS = [
            ("q", "quit", t("tui.binding.quit")),
            ("r", "refresh", t("tui.binding.refresh")),
            ("i", "install_missing", t("tui.binding.install")),
            ("s", "skills_sync", t("tui.binding.skills")),
            ("d", "open_docs", t("tui.binding.docs")),
            ("c", "cancel_install", t("tui.binding.cancel")),
            ("escape", "close_panels", t("tui.binding.closepanels")),
        ]
        CSS = """
        #estado, #gates-linea, #lastclose { padding: 0 1; }
        #detalle-log { padding: 0 1; height: 1fr; overflow-y: auto; }
        #cierre-form Input { margin: 0 1; }
        #btn-close, #btn-init { margin: 1 1; }
        #taskinfo { padding: 0 1; color: $text-muted; max-height: 10; overflow-y: auto; }
        #salida { height: 1fr; margin: 0 1; border: round $primary; }
        #resumen-cuerpo { height: 1fr; }
        #instalador { width: 45%; margin: 0 1; border: round $secondary; display: none; }
        #skills-hint { padding: 0 1; color: $text-muted; }
        #skills-log { height: 8; margin: 0 1; border: round $secondary; display: none; }
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
                    yield Static(id="pathaviso")
                    # tabla | log del instalador lado a lado (el log aparece al usar `i`)
                    with Horizontal(id="resumen-cuerpo"):
                        yield DataTable(id="tabla-doctor", cursor_type="row")
                        yield RichLog(id="instalador", wrap=True, markup=True)
                with TabPane(t("tui.tab.skills"), id="skills"):
                    yield Static(t("tui.skills.hint"), id="skills-hint")
                    yield Input(placeholder=t("tui.skills.url.placeholder"),
                                id="skill-url")
                    yield DataTable(id="tabla-skills", cursor_type="row")
                    yield RichLog(id="skills-log", wrap=True, markup=True)
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

            # aviso de PATH de uv (si sus binarios no están en el PATH)
            self.query_one("#pathaviso", Static).update(
                "" if report.uv_bin_on_path
                else f"[yellow]▲ {t('doctor.path.uv.missing')}[/yellow]")

            self._report = report  # lo usa el instalador (tecla i)
            from tramalia.cli.render import group_statuses
            tabla = self.query_one("#tabla-doctor", DataTable)
            tabla.clear(columns=True)
            tabla.add_columns(t("tui.col.tool"), t("tui.col.purpose"),
                              t("tui.col.state"), t("tui.col.detail"))
            for cat, rows in group_statuses(report.statuses):
                tabla.add_row(f"[bold cyan]· {t('doctor.group.' + cat)}[/]", "", "", "")
                for s in rows:
                    if s.present:
                        mark, detalle = t("tui.status.ok"), (s.version or "—")
                    else:
                        best = installer.best_auto(s.tool)
                        hint = best.display if best else (
                            installer.options_for(s.tool)[0].display
                            if installer.options_for(s.tool) else s.tool.install_hint)
                        mark = (t("tui.status.optional")
                                if s.tool.category in ("feature", "agent")
                                else t("tui.status.missing"))
                        detalle = hint
                    tabla.add_row(f"  {s.tool.cmd}", s.tool.role, mark, detalle)

            self._refresh_skills(root, initialized)
            self._refresh_audit(root, initialized, entries)
            self._refresh_close(root, initialized)

        def _refresh_skills(self, root, initialized) -> None:
            tabla = self.query_one("#tabla-skills", DataTable)
            tabla.clear(columns=True)
            tabla.add_columns(t("tui.skills.col.name"), t("tui.col.state"),
                              t("tui.skills.col.info"))
            if not initialized:
                self.query_one("#skills-hint", Static).update(t("tui.skills.uninit"))
                return
            self.query_one("#skills-hint", Static).update(t("tui.skills.hint"))
            tabla.add_row(f"[bold cyan]· {t('skills.group.own')}[/]", "", "")
            for s in skills_core.own_skills(root):
                tabla.add_row(f"  {s['name']}", t("skills.state.installed"),
                              s["description"])
            tabla.add_row(f"[bold cyan]· {t('skills.group.external')}[/]", "", "")
            for s in skills_core.catalog(root):
                estado = (t("skills.state.installed") if s["installed"]
                          else t("skills.state.declared") if s["enabled"]
                          else t("skills.state.available"))
                tabla.add_row(f"  {s['name']}", estado, s["source"])

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

        def on_input_submitted(self, event) -> None:
            """Enter en el input de URL: agrega la skill al manifiesto."""
            if event.input.id != "skill-url" or not event.value.strip():
                return
            root = Path.cwd()
            ok, resultado = skills_core.add_skill(root, event.value)
            log = self._skills_log()
            if ok:
                log.write(t("skills.add.ok", name=resultado))
                event.input.value = ""
                self._refresh_skills(root, project.is_initialized(root))
            else:
                log.write(t(f"skills.add.{resultado}"))

        def on_data_table_row_selected(self, event) -> None:
            if event.data_table.id == "tabla-skills":
                self._toggle_skill(event)
                return
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

        # ------------------------------------------------------------ skills
        def _skills_log(self) -> RichLog:
            log = self.query_one("#skills-log", RichLog)
            log.display = True
            return log

        def _toggle_skill(self, event) -> None:
            """Enter sobre una skill externa: activa/desactiva su bloque del TOML."""
            root = Path.cwd()
            name = str(event.data_table.get_row(event.row_key)[0]).strip()
            externa = next((s for s in skills_core.catalog(root)
                            if s["name"] == name), None)
            if externa is None:  # encabezado o skill propia: nada que alternar
                return
            log = self._skills_log()
            nuevo = not externa["enabled"]
            if skills_core.set_enabled(root, name, nuevo):
                log.write(t("skills.toggle.on" if nuevo else "skills.toggle.off",
                            name=name))
            else:
                log.write(t("skills.toggle.fail", name=name))
            self._refresh_skills(root, project.is_initialized(root))

        def action_skills_sync(self) -> None:
            self.query_one(TabbedContent).active = "skills"
            log = self._skills_log()
            log.write(t("tui.skills.sync.running"))
            self.run_worker(self._skills_sync_worker, thread=True, exclusive=True)

        def _skills_sync_worker(self) -> None:
            results = skills_core.sync_skills(Path.cwd())
            self.call_from_thread(self._after_skills_sync, results)

        def _after_skills_sync(self, results) -> None:
            log = self._skills_log()
            if not results:
                log.write(t("tui.skills.sync.none"))
            for name, act in results:
                log.write(f"{act:>12}  {name}")
            self._refresh_skills(Path.cwd(), project.is_initialized(Path.cwd()))

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
        def _log_install(self) -> RichLog:
            log = self.query_one("#instalador", RichLog)
            log.display = True
            return log

        def action_install_missing(self) -> None:
            """Tecla i: selección múltiple de faltantes. Muestra TODAS las que
            faltan — automatizables como marcables, manuales como lista visible —
            más la acción de configurar el PATH de uv si hace falta."""
            self.query_one(TabbedContent).active = "resumen"
            report = getattr(self, "_report")
            faltantes = [s.tool for s in report.statuses if not s.present]
            auto, manual, runtime_offers = installer.plan_for(faltantes)
            plans = list(auto)
            # ofrecer instalar el runtime (Node/Go) que desbloquea otras herramientas
            for name, opt, enables in runtime_offers:
                plans.append((t("tui.install.runtime", rt=name,
                                tools=", ".join(enables)), opt))
            # manuales: anotar "requiere X" si un runtime falta
            manuals = []
            for cmd, display, rt in manual:
                label = (cmd if not rt else
                         t("tui.install.needs", tool=cmd,
                           rt=installer._RUNTIME_NAME.get(rt, rt)))
                manuals.append((label, display))
            # acción de PATH: si uv está pero su bin no está en el PATH
            if not report.uv_bin_on_path and installer.shutil.which("uv"):
                plans.append((t("tui.install.pathfix"), installer.pathfix_option()))
            if not plans and not manuals:
                self._log_install().write(t("tui.install.none"))
                return
            self.push_screen(InstallScreen(plans, manuals), self._run_installs)

        def _run_installs(self, seleccion) -> None:
            if not seleccion:
                return
            import threading
            self._cancel = threading.Event()
            self.run_worker(lambda: self._install_worker(seleccion),
                            thread=True, exclusive=True)

        def action_cancel_install(self) -> None:
            """Tecla c: termina la instalación en curso y sigue con la próxima."""
            ev = getattr(self, "_cancel", None)
            if ev is not None:
                ev.set()

        def _install_worker(self, seleccion) -> None:
            for label, opt in seleccion:
                self._cancel.clear()  # cancelar aplica a UNA herramienta, no a todas
                self.call_from_thread(
                    self._log_write,
                    t("tui.install.installing", tool=label,
                      method=opt.method, cmd=opt.display))
                code, out = installer.run_install_streaming(
                    opt, on_line=lambda ln: self.call_from_thread(
                        self._log_write, f"[dim]{ln}[/dim]"),
                    cancel=self._cancel)
                if code == 0:
                    self.call_from_thread(
                        self._log_write, t("tui.install.ok", tool=label))
                elif code == 130:
                    self.call_from_thread(
                        self._log_write, t("tui.install.cancelled", tool=label))
                elif code == 124:
                    self.call_from_thread(
                        self._log_write, t("tui.install.timeout", tool=label))
                else:
                    self.call_from_thread(
                        self._log_write, t("tui.install.fail", tool=label, code=code))
                    if installer.needs_admin(out):
                        self.call_from_thread(
                            self._log_write, t("tui.install.admin", tool=label))
            self.call_from_thread(self._after_installs)

        # ------------------------------------------------------------ docs
        def action_open_docs(self) -> None:
            """Tecla d: abre la documentación de la herramienta seleccionada.

            Usa una notificación (toast, se cierra sola) — NO el panel del
            instalador, que solo debe aparecer durante una instalación real.
            """
            import webbrowser
            from tramalia.core.tools import REGISTRY, docs_url
            tabla = self.query_one("#tabla-doctor", DataTable)
            try:
                fila = tabla.get_row_at(tabla.cursor_row)
            except Exception:
                return
            cmd = str(fila[0]).strip()
            tool = next((x for x in REGISTRY if x.cmd == cmd), None)
            url = docs_url(tool) if tool else ""
            if url:
                webbrowser.open(url)
                self.notify(t("tui.docs.opened", url=url), markup=False)
            else:
                self.notify(t("tui.docs.none"), severity="warning", markup=False)

        def action_close_panels(self) -> None:
            """Tecla Escape: oculta los paneles de log (instalador/skills) si
            quedaron abiertos — la salida de una instalación/sync ya cumplió
            su propósito y hay que poder cerrarla."""
            for panel_id in ("#instalador", "#skills-log"):
                panel = self.query_one(panel_id, RichLog)
                panel.display = False

        def _log_write(self, msg: str) -> None:
            self._log_install().write(msg)

        def _after_installs(self) -> None:
            self._log_install().write(t("tui.install.done"))
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
