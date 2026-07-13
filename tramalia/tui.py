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
    from rich.text import Text
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.screen import ModalScreen
    from textual.widgets import (
        Button,
        DataTable,
        Footer,
        Header,
        Input,
        OptionList,
        RichLog,
        SelectionList,
        Static,
        TabbedContent,
        TabPane,
    )
    from textual.widgets.option_list import Option
    from textual.widgets.selection_list import Selection

    from tramalia.core import configuracion, habilidades, installer
    from tramalia.core import doctor as doctor_core
    from tramalia.core.detect import detect_stack, enabled_features
    from tramalia.core.errores import ErrorProyectoNoGobernado, ErrorTramalia
    from tramalia.core.evidencia import leer_bitacora
    from tramalia.core.modelos import (
        EntradaBitacora,
        ResultadoCierre,
        ValorEstadoBitacora,
        ValorResultadoPuerta,
    )
    from tramalia.core.operaciones import cerrar_proyecto
    from tramalia.core.proveedor_contexto import PROVEEDORES, proveedor_disponible
    from tramalia.core.proyecto import exigir_proyecto_gobernado, inspeccionar_estado_proyecto
    from tramalia.core.puertas_calidad import cargar_puertas
    from tramalia.core.scaffold import scaffold

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

        BINDINGS = [("escape", "dismiss_empty", "cerrar")]

        def __init__(self, plans, manuals):
            super().__init__()
            self._plans = plans  # [(label, InstallOption, enables)] automatizables
            self._manuals = manuals  # [(label, comando_str)] solo manual

        def action_dismiss_empty(self) -> None:
            self.dismiss([])

        def compose(self) -> ComposeResult:
            with Vertical(id="inst-box"):
                yield Static(f"[b]{t('tui.install.title')}[/b]")
                if self._plans:
                    yield SelectionList(
                        *[
                            Selection(f"{label} — {opt.display}", idx, True)
                            for idx, (label, opt, _en) in enumerate(self._plans)
                        ]
                    )
                if self._manuals:
                    lineas = "\n".join(f"  • {label} — {cmd}" for label, cmd in self._manuals)
                    yield Static(
                        f"[dim]{t('tui.install.manual.header')}\n{lineas}[/dim]", id="inst-manual"
                    )
                with Horizontal(id="inst-botones"):
                    yield Button(t("tui.install.button"), id="inst-ok", variant="primary")
                    yield Button(t("tui.install.cancel"), id="inst-cancel")

        def on_button_pressed(self, event) -> None:
            if event.button.id == "inst-ok" and self._plans:
                seleccion = self.query_one(SelectionList).selected
                self.dismiss([self._plans[i] for i in seleccion])
            else:
                self.dismiss([])

    class ContextBackendScreen(ModalScreen):
        """Selección ÚNICA del backend de contexto activo (tecla b), con el
        alcance y el caso de uso ideal de cada opción para decidir con info."""

        CSS = """
        ContextBackendScreen { align: center middle; }
        #ctx-box { width: 100; max-height: 85%; border: round $primary;
                   background: $surface; padding: 1 2; }
        #ctx-box OptionList { height: auto; max-height: 20; }
        #ctx-botones { height: 3; align-horizontal: right; }
        """

        BINDINGS = [("escape", "cancel", "cerrar")]

        def __init__(self, current: str):
            super().__init__()
            self._current = current

        def action_cancel(self) -> None:
            self.dismiss(None)

        def compose(self) -> ComposeResult:
            with Vertical(id="ctx-box"):
                yield Static(f"[b]{t('tui.ctxbackend.title')}[/b]")
                yield Static(t("tui.ctxbackend.currentline", name=self._current))
                opciones = OptionList()
                for key, meta in PROVEEDORES.items():
                    inst = proveedor_disponible(key)
                    estado = "✓" if inst else "○"
                    estado_txt = (
                        t("tui.ctxbackend.installed") if inst else t("tui.ctxbackend.notinstalled")
                    )
                    actual = (
                        f"  [reverse] {t('tui.ctxbackend.current')} [/reverse]"
                        if key == self._current
                        else ""
                    )
                    texto = (
                        f"{estado} [b]{meta['etiqueta']}[/b]{actual}\n"
                        f"   {meta['alcance']}\n"
                        f"   {t('tui.ctxbackend.ideal')}: {meta['ideal']}\n"
                        f"   [dim]{estado_txt}[/dim]"
                    )
                    opciones.add_option(Option(texto, id=key))
                yield opciones
                with Horizontal(id="ctx-botones"):
                    yield Button(t("tui.install.cancel"), id="ctx-cancel")

        def on_option_list_option_selected(self, event) -> None:
            self.dismiss(event.option.id)

        def on_button_pressed(self, event) -> None:
            self.dismiss(None)

    _LOG_MARKS = {
        "aprobado": "✓ aprobado",
        "aprobado_con_excepciones": "⚠ aprobado_con_excepciones",
        "bloqueado": "✗ bloqueado",
        "invalida": "✗ invalida",
    }

    def _estado_entrada(entrada: EntradaBitacora) -> str:
        if entrada.estado is ValorEstadoBitacora.INVALIDA:
            return entrada.estado.value
        return entrada.resultado.value if entrada.resultado is not None else entrada.estado.value

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
            ("b", "context_backend", t("tui.binding.contextbackend")),
            ("u", "check_updates", t("tui.binding.checkupdates")),
            ("escape", "close_panels", t("tui.binding.closepanels")),
        ]
        CSS = """
        #estado, #gates-linea, #lastclose { padding: 0 1; }
        #detalle-log { padding: 0 1; height: 1fr; overflow-y: auto; }
        #cierre-form Input { margin: 0 1; }
        #btn-close, #btn-init, #btn-init-resumen { margin: 1 1; }
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
                    # botón de inicializar aquí mismo cuando el repo no está gobernado
                    yield Button(
                        t("tui.close.init.button"), id="btn-init-resumen", variant="warning"
                    )
                    yield Static(id="gates-linea")
                    yield Static(id="lastclose")
                    yield Static(id="pathaviso")
                    yield Static(id="ctxbackend")
                    # tabla | log del instalador lado a lado (el log aparece al usar `i`)
                    with Horizontal(id="resumen-cuerpo"):
                        yield DataTable(id="tabla-doctor", cursor_type="row")
                        yield RichLog(id="instalador", wrap=True, markup=True)
                with TabPane(t("tui.tab.skills"), id="skills"):
                    yield Static(t("tui.skills.hint"), id="skills-hint")
                    yield Input(placeholder=t("tui.skills.url.placeholder"), id="skill-url")
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
                        yield Input(
                            placeholder=t("tui.close.reviewer.placeholder"), id="in-reviewer"
                        )
                        yield Input(placeholder=t("tui.close.model.placeholder"), id="in-model")
                        yield Button(t("tui.close.button"), id="btn-close", variant="primary")
                        yield RichLog(id="salida", wrap=True, markup=True)
            yield Footer()

        def on_mount(self) -> None:
            self._skill_updates: dict[str, bool] = {}
            self._entradas_bitacora: dict[str, EntradaBitacora] = {}
            self.action_refresh()

        # ------------------------------------------------------------ refresh
        def action_refresh(self) -> None:
            root = Path.cwd()
            inicializado = inspeccionar_estado_proyecto(root).listo
            stack = detect_stack(root)
            report = doctor_core.diagnose(root)

            estado = t("tui.state.initialized") if inicializado else t("tui.state.uninitialized")
            self.query_one("#estado", Static).update(
                t("tui.header", path=str(root), stack=", ".join(stack) or "—", estado=estado)
            )
            # el botón de init vive aquí (Resumen): visible solo si falta inicializar
            self.query_one("#btn-init-resumen", Button).display = not inicializado

            # Las puertas visibles son exactamente las que acepta el cargador formal.
            try:
                gates = tuple(puerta.nombre for puerta in cargar_puertas(root))
                texto_puertas = (
                    t("tui.gates.line", gates=" · ".join(gates)) if gates else t("tui.gates.none")
                )
            except ErrorTramalia as error:
                texto_puertas = f"[red]{error.mensaje}[/red]"
            self.query_one("#gates-linea", Static).update(texto_puertas)

            entries = leer_bitacora(root)
            last = ""
            if entries:
                e = entries[0]
                estado_entrada = _estado_entrada(e)
                last = t(
                    "tui.lastclose",
                    id=e.id_paquete,
                    mark=_LOG_MARKS.get(estado_entrada, f"○ {estado_entrada}"),
                )
            self.query_one("#lastclose", Static).update(last)

            # aviso de PATH de uv (si sus binarios no están en el PATH)
            self.query_one("#pathaviso", Static).update(
                "" if report.uv_bin_on_path else f"[yellow]▲ {t('doctor.path.uv.missing')}[/yellow]"
            )

            # backend de contexto activo (config.json → context.backend)
            if inicializado:
                self.query_one("#ctxbackend", Static).update(
                    t("tui.ctxbackend.line", name=configuracion.proveedor_contexto(root))
                )
            else:
                self.query_one("#ctxbackend", Static).update("")

            self._report = report  # lo usa el instalador (tecla i)
            from tramalia.cli.render import group_statuses

            tabla = self.query_one("#tabla-doctor", DataTable)
            tabla.clear(columns=True)
            tabla.add_columns(
                t("tui.col.tool"), t("tui.col.purpose"), t("tui.col.state"), t("tui.col.detail")
            )
            for cat, rows in group_statuses(report.statuses):
                tabla.add_row(f"[bold cyan]· {t('doctor.group.' + cat)}[/]", "", "", "")
                for estado in rows:
                    if estado.presente:
                        mark, detalle = t("tui.status.ok"), (estado.version or "—")
                    else:
                        best = installer.best_auto(estado.herramienta)
                        hint = (
                            best.display
                            if best
                            else (
                                installer.options_for(estado.herramienta)[0].display
                                if installer.options_for(estado.herramienta)
                                else estado.herramienta.sugerencia_instalacion
                            )
                        )
                        mark = (
                            t("tui.status.optional")
                            if estado.herramienta.categoria in ("feature", "agent")
                            else t("tui.status.missing")
                        )
                        detalle = hint
                    tabla.add_row(
                        f"  {estado.herramienta.comando}",
                        estado.herramienta.rol,
                        mark,
                        detalle,
                    )

            self._refresh_skills(root, inicializado)
            self._refresh_audit(root, inicializado, entries)
            self._refresh_close(root, inicializado)

        def _refresh_skills(self, root, initialized) -> None:
            tabla = self.query_one("#tabla-skills", DataTable)
            tabla.clear(columns=True)
            tabla.add_columns(
                t("tui.skills.col.name"), t("tui.col.state"), t("tui.skills.col.info")
            )
            if not initialized:
                self.query_one("#skills-hint", Static).update(t("tui.skills.uninit"))
                return
            hint = t("tui.skills.hint")
            rastreadas = habilidades.habilidades_externas_rastreadas(root)
            if rastreadas:
                hint += (
                    "\n[yellow]"
                    + t("skills.tracked.warn", names=", ".join(rastreadas))
                    + "[/yellow]"
                )
            self.query_one("#skills-hint", Static).update(hint)
            tabla.add_row(f"[bold cyan]· {t('skills.group.own')}[/]", "", "")
            for habilidad in habilidades.habilidades_propias(root):
                tabla.add_row(
                    f"  {habilidad['nombre']}",
                    t("skills.state.installed"),
                    habilidad["descripcion"],
                )
            tabla.add_row(f"[bold cyan]· {t('skills.group.external')}[/]", "", "")
            updates = getattr(self, "_skill_updates", {})
            for habilidad in habilidades.catalogo_habilidades(root):
                estado = (
                    t("skills.state.installed")
                    if habilidad.instalada
                    else t("skills.state.declared")
                    if habilidad.habilitada
                    else t("skills.state.available")
                )
                referencia = habilidades.referencia_instalada(root, habilidad.nombre)
                if referencia:
                    info = f"@{referencia}"
                    if updates.get(habilidad.nombre):
                        info += f"  [yellow]⬆ {t('skills.update.available')}[/yellow]"
                else:
                    info = habilidad.fuente
                tabla.add_row(f"  {habilidad.nombre}", estado, info)

        def _refresh_audit(self, root, initialized, entries) -> None:
            aviso = self.query_one("#aviso-audit", Static)
            tabla = self.query_one("#tabla-log", DataTable)
            tabla.clear(columns=True)
            self._entradas_bitacora = {entrada.id_paquete: entrada for entrada in entries}
            if not initialized:
                aviso.update(t("tui.audit.uninit"))
                return
            if not entries:
                aviso.update(t("tui.audit.empty"))
                return
            aviso.update("")
            tabla.add_columns(t("tui.col.close"), t("tui.col.status"), t("tui.col.agent"))
            for e in entries:
                modelo = f" ({e.modelo})" if e.modelo else ""
                tabla.add_row(
                    e.id_paquete,
                    _estado_entrada(e),
                    (e.agente or "—") + modelo,
                )

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
            primary, reviewer = configuracion.agentes_predeterminados(root)
            in_task = self.query_one("#in-task", Input)
            if not in_task.value:
                in_task.value = configuracion.id_tarea_actual(root) or ""
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
            desc = configuracion.descripcion_tarea(root, task_id.strip())
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
            ok, resultado = habilidades.agregar_habilidad(root, event.value)
            log = self._skills_log()
            if ok:
                log.write(t("skills.add.ok", name=resultado))
                event.input.value = ""
                self._refresh_skills(root, inspeccionar_estado_proyecto(root).listo)
            else:
                log.write(t(f"skills.add.{resultado}"))

        def on_data_table_row_selected(self, event) -> None:
            if event.data_table.id == "tabla-skills":
                self._toggle_skill(event)
                return
            if event.data_table.id != "tabla-log":
                return
            row = event.data_table.get_row(event.row_key)
            id_paquete = str(row[0])
            entrada = self._entradas_bitacora.get(id_paquete)
            detalle = self.query_one("#detalle-log", Static)
            if entrada is None:
                detalle.update(t("tui.audit.nometa"))
                return
            if entrada.estado is ValorEstadoBitacora.INVALIDA:
                detalle.update(entrada.error or entrada.estado.value)
                return
            meta = entrada.ruta / "metadatos.json"
            try:
                data = json.loads(meta.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                detalle.update(t("tui.audit.nometa"))
                return
            detalle.update(json.dumps(data, indent=2, ensure_ascii=False))

        # ------------------------------------------------------------ skills
        def _skills_log(self) -> RichLog:
            log = self.query_one("#skills-log", RichLog)
            log.display = True
            return log

        def _toggle_skill(self, event) -> None:
            """Enter sobre una skill externa, en UN paso:
            - no instalada  → la declara, fija su SHA y la materializa.
            - instalada     → actualiza explícitamente esa sola habilidad."""
            root = Path.cwd()
            name = str(event.data_table.get_row(event.row_key)[0]).strip()
            externa = next(
                (
                    habilidad
                    for habilidad in habilidades.catalogo_habilidades(root)
                    if habilidad.nombre == name
                ),
                None,
            )
            if externa is None:  # encabezado o skill propia: nada que hacer
                return
            log = self._skills_log()
            if externa.instalada:
                # ya instalada → actualización explícita de esa sola habilidad.
                log.write(t("skills.update.one", name=name))
                self.run_worker(
                    lambda: self._sync_one_skill(name, actualizar=True),
                    thread=True,
                    exclusive=True,
                )
                return
            if not externa.habilitada:
                habilidades.fijar_habilitada(root, name, True)
            log.write(t("skills.install.one", name=name))  # y clonar en el acto
            self.run_worker(
                lambda: self._sync_one_skill(name, actualizar=True),
                thread=True,
                exclusive=True,
            )

        def _sync_one_skill(self, name, actualizar=False) -> None:
            resultado = habilidades.sincronizar_habilidades(
                Path.cwd(), solo=name, actualizar=actualizar
            )
            self.call_from_thread(self._after_one_skill, name, resultado)

        def _after_one_skill(self, name, resultado) -> None:
            log = self._skills_log()
            resolucion = next((r for r in resultado.resoluciones if r.nombre == name), None)
            accion = resolucion.accion if resolucion else None
            if accion == "clonada":
                log.write(t("skills.install.ok", name=name))
            elif accion in ("actualizada", "rehidratada", "sin_cambios"):
                log.write(t("skills.update.ok", name=name))
            elif resultado.estado.motivo == "git_no_instalado":
                log.write(t("skills.install.nogit"))
            else:
                log.write(t("skills.install.fail", name=name))
            self._skill_updates.pop(name, None)  # ya no está desactualizada
            root = Path.cwd()
            self._refresh_skills(root, inspeccionar_estado_proyecto(root).listo)

        def action_check_updates(self) -> None:
            """Tecla u: comprueba en los remotos qué skills externas tienen
            una versión más nueva (git ls-remote), y lo marca en la tabla."""
            root = Path.cwd()
            if not inspeccionar_estado_proyecto(root).listo:
                self.notify(t("tui.close.uninit"), severity="warning", markup=False)
                return
            self.query_one(TabbedContent).active = "skills"
            self._skills_log().write(t("skills.update.checking"))
            self.run_worker(self._check_updates_worker, thread=True, exclusive=True)

        def _check_updates_worker(self) -> None:
            estados = habilidades.consultar_habilidades(Path.cwd(), consultar_remoto=True)
            self.call_from_thread(self._after_check_updates, estados)

        def _after_check_updates(self, estados) -> None:
            fallidas = [
                estado
                for estado in estados
                if not estado.estado.exitoso and estado.estado.motivo != "habilidad_no_instalada"
            ]
            self._skill_updates = {
                estado.nombre: estado.estado.motivo == "actualizacion_disponible"
                for estado in estados
                if estado.sha_resuelto and estado.estado.exitoso
            }
            log = self._skills_log()
            for estado in fallidas:
                log.write(
                    t(
                        "skills.outdated.fail",
                        name=estado.nombre,
                        reason=estado.estado.motivo,
                        remediation=estado.estado.remediacion,
                    )
                )
            n = sum(1 for v in self._skill_updates.values() if v)
            if n or not fallidas:
                log.write(t("skills.update.found", n=n))
            root = Path.cwd()
            self._refresh_skills(root, inspeccionar_estado_proyecto(root).listo)

        def action_skills_sync(self) -> None:
            self.query_one(TabbedContent).active = "skills"
            log = self._skills_log()
            log.write(t("tui.skills.sync.running"))
            self.run_worker(self._skills_sync_worker, thread=True, exclusive=True)

        def _skills_sync_worker(self) -> None:
            resultado = habilidades.sincronizar_habilidades(Path.cwd())
            self.call_from_thread(self._after_skills_sync, resultado)

        def _after_skills_sync(self, resultado) -> None:
            log = self._skills_log()
            if not resultado.resoluciones:
                log.write(t("tui.skills.sync.none"))
            total = len(resultado.resoluciones)
            for numero, resolucion in enumerate(resultado.resoluciones, 1):
                log.write(f"[{numero}/{total}] {resolucion.accion:>12}  {resolucion.nombre}")
            if resultado.resoluciones:
                ok = sum(1 for r in resultado.resoluciones if r.estado.exitoso)
                log.write(t("tui.skills.sync.summary", ok=ok, total=total))
            root = Path.cwd()
            self._refresh_skills(root, inspeccionar_estado_proyecto(root).listo)

        def on_button_pressed(self, event) -> None:
            if event.button.id in ("btn-init", "btn-init-resumen"):
                self._run_init(event.button)
            elif event.button.id == "btn-close":
                self._start_close(event.button)

        # ------------------------------------------------------------ init
        def _run_init(self, button) -> None:
            button.disabled = True
            root = Path.cwd()
            stack = detect_stack(root)
            from tramalia.core.integraciones import detectar_agentes_predeterminados

            primary, reviewer = detectar_agentes_predeterminados()
            scaffold(
                root,
                {
                    "project_name": root.name,
                    "stacks": stack,
                    "features": enabled_features(stack),
                    "primary_agent": primary,
                    "reviewer_agent": reviewer,
                },
            )
            configuracion.fijar_version_andamiaje(root, _tramalia_version)
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
            faltantes = [estado.herramienta for estado in report.statuses if not estado.presente]
            auto, manual, runtime_offers = installer.plan_for(faltantes)
            # plans: 3-tuplas (label, opción, [cmds que desbloquea al instalarse])
            plans: list[tuple[str, installer.InstallOption, list[str]]] = [
                (cmd, opt, []) for cmd, opt in auto
            ]
            # ofrecer instalar el runtime (Node/Go) que desbloquea otras herramientas;
            # `enables` deja que el worker las instale encadenadas en la misma corrida
            for name, opt, enables in runtime_offers:
                plans.append(
                    (
                        t("tui.install.runtime", rt=name, tools=", ".join(enables)),
                        opt,
                        list(enables),
                    )
                )
            # manuales: anotar "requiere X" si un runtime falta
            manuals = []
            for cmd, display, rt in manual:
                label = (
                    cmd
                    if not rt
                    else t("tui.install.needs", tool=cmd, rt=installer._RUNTIME_NAME.get(rt, rt))
                )
                manuals.append((label, display))
            # acción de PATH: si uv está pero su bin no está en el PATH
            if not report.uv_bin_on_path and installer.shutil.which("uv"):
                plans.append((t("tui.install.pathfix"), installer.pathfix_option(), []))
            if not plans and not manuals:
                self._log_install().write(t("tui.install.none"))
                return
            self.push_screen(InstallScreen(plans, manuals), self._run_installs)

        def _run_installs(self, seleccion) -> None:
            if not seleccion:
                return
            import threading

            self._cancel = threading.Event()
            self.run_worker(lambda: self._install_worker(seleccion), thread=True, exclusive=True)

        def action_cancel_install(self) -> None:
            """Tecla c: termina la instalación en curso y sigue con la próxima."""
            ev = getattr(self, "_cancel", None)
            if ev is not None:
                ev.set()

        def _install_worker(self, seleccion) -> None:
            from tramalia.core.integraciones import REGISTRO

            cola = list(seleccion)  # crece si un runtime desbloquea otras (engram tras Go)
            i = 0
            while i < len(cola):
                label, opt, enables = cola[i]
                i += 1
                self._cancel.clear()  # cancelar aplica a UNA herramienta, no a todas
                self.call_from_thread(
                    self._log_write,
                    t(
                        "tui.install.installing",
                        n=i,
                        total=len(cola),
                        tool=label,
                        method=opt.method,
                        cmd=opt.display,
                    ),
                )
                code, out = installer.run_install_streaming(
                    opt,
                    on_line=lambda ln: self.call_from_thread(self._log_write, f"[dim]{ln}[/dim]"),
                    cancel=self._cancel,
                )
                if code == 0:
                    self.call_from_thread(self._log_write, t("tui.install.ok", tool=label))
                    # el runtime recién instalado ya deja su binario en disco:
                    # refrescar el PATH del proceso y encadenar lo que desbloquea.
                    installer.refresh_runtime_path()
                    for cmd in enables:
                        herramienta = next(
                            (x for x in REGISTRO if x.comando == cmd),
                            None,
                        )
                        best = installer.best_auto(herramienta) if herramienta else None
                        if best:
                            cola.append((cmd, best, []))
                            self.call_from_thread(
                                self._log_write, t("tui.install.chained", tool=cmd)
                            )
                elif code == 130:
                    self.call_from_thread(self._log_write, t("tui.install.cancelled", tool=label))
                elif code == 124:
                    self.call_from_thread(self._log_write, t("tui.install.timeout", tool=label))
                else:
                    self.call_from_thread(
                        self._log_write, t("tui.install.fail", tool=label, code=code)
                    )
                    if installer.needs_admin(out):
                        self.call_from_thread(self._log_write, t("tui.install.admin", tool=label))
            self.call_from_thread(self._after_installs)

        # ------------------------------------------------------------ docs
        def action_open_docs(self) -> None:
            """Tecla d: abre la documentación de lo seleccionado.

            En Resumen: la doc oficial de la herramienta. En Skills: el repo de
            origen de la skill externa, o la guía de skills para las propias.
            Usa una notificación (toast) — NO el panel del instalador.
            """
            import webbrowser

            if self.query_one(TabbedContent).active == "skills":
                url = self._skill_docs_url()
            else:
                from tramalia.core.integraciones import REGISTRO, url_documentacion

                tabla = self.query_one("#tabla-doctor", DataTable)
                try:
                    fila = tabla.get_row_at(tabla.cursor_row)
                except Exception:
                    return
                cmd = str(fila[0]).strip()
                herramienta = next((x for x in REGISTRO if x.comando == cmd), None)
                url = url_documentacion(herramienta) if herramienta else ""
            if url:
                webbrowser.open(url)
                self.notify(t("tui.docs.opened", url=url), markup=False)
            else:
                self.notify(t("tui.docs.none"), severity="warning", markup=False)

        def _skill_docs_url(self) -> str:
            """URL de docs de la skill bajo el cursor: repo de origen (externa) o
            la guía de skills del sitio (propia NN-*)."""
            root = Path.cwd()
            tabla = self.query_one("#tabla-skills", DataTable)
            try:
                fila = tabla.get_row_at(tabla.cursor_row)
            except Exception:
                return ""
            name = str(fila[0]).strip()
            externa = next(
                (
                    habilidad
                    for habilidad in habilidades.catalogo_habilidades(root)
                    if habilidad.nombre == name
                ),
                None,
            )
            if externa and externa.fuente:
                return externa.fuente.removeprefix("git+").removesuffix(".git")
            if len(name) >= 2 and name[:2].isdigit():
                return "https://mscottb.github.io/tramalia/skills-guia/"
            return ""

        def action_close_panels(self) -> None:
            """Tecla Escape: oculta los paneles de log (instalador/skills) si
            quedaron abiertos — la salida de una instalación/sync ya cumplió
            su propósito y hay que poder cerrarla."""
            for panel_id in ("#instalador", "#skills-log"):
                panel = self.query_one(panel_id, RichLog)
                panel.display = False

        # ------------------------------------------------------------ backend
        def action_context_backend(self) -> None:
            """Tecla b: elegir el backend de contexto activo del proyecto."""
            root = Path.cwd()
            try:
                exigir_proyecto_gobernado(root)
            except ErrorProyectoNoGobernado:
                self.notify(t("tui.close.uninit"), severity="warning", markup=False)
                return
            actual = configuracion.proveedor_contexto(root)
            self.push_screen(ContextBackendScreen(actual), self._on_backend_chosen)

        def _on_backend_chosen(self, chosen: str | None) -> None:
            if not chosen:
                return
            root = Path.cwd()
            try:
                exigir_proyecto_gobernado(root)
            except ErrorProyectoNoGobernado:
                self.notify(t("tui.close.uninit"), severity="warning", markup=False)
                return
            if configuracion.fijar_proveedor_contexto(root, chosen):
                # el backend es una PREFERENCIA de proyecto: se fija aunque no esté
                # instalado, pero se avisa y se dice cómo obtenerlo (tecla i / doctor).
                if proveedor_disponible(chosen):
                    self.notify(t("tui.ctxbackend.ok", name=chosen), markup=False)
                else:
                    self.notify(
                        t("tui.ctxbackend.oknotinstalled", name=chosen),
                        severity="warning",
                        markup=False,
                    )
                self.action_refresh()
            else:
                self.notify(t("tui.ctxbackend.fail"), severity="error", markup=False)

        def _log_write(self, msg: str) -> None:
            self._log_install().write(msg)

        def _after_installs(self) -> None:
            self._log_install().write(t("tui.install.done"))
            self.action_refresh()

        # ------------------------------------------------------------ close
        def _start_close(self, button) -> None:
            root = Path.cwd()
            salida = self.query_one("#salida", RichLog)
            try:
                estado_proyecto = exigir_proyecto_gobernado(root)
            except ErrorProyectoNoGobernado:
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
            self.run_worker(
                lambda: self._run_close(estado_proyecto.raiz, task, agent, reviewer, model),
                thread=True,
                exclusive=True,
            )

        def _run_close(
            self,
            raiz: Path,
            task: str,
            agent: str,
            reviewer: str,
            model: str,
        ) -> None:
            try:
                result = cerrar_proyecto(
                    raiz,
                    task,
                    agente=agent,
                    revisor=reviewer,
                    modelo=model,
                )
            except Exception as exc:
                self.call_from_thread(self._show_close_error, str(exc))
                return
            self.call_from_thread(self._show_close_result, result)

        def _show_close_error(self, message: str) -> None:
            self.query_one("#salida", RichLog).write(t("tui.close.error", msg=message))
            self.query_one("#btn-close", Button).disabled = False

        def _show_close_result(self, result: ResultadoCierre) -> None:
            salida = self.query_one("#salida", RichLog)
            for puerta in result.ejecucion.resultados:
                salida.write(
                    t("tui.close.gate.ok", name=puerta.nombre)
                    if puerta.estado is ValorResultadoPuerta.APROBADO
                    else t("tui.close.gate.fail", name=puerta.nombre)
                )
            salida.write(t("tui.close.status", status=result.estado.value))
            if result.ruta_paquete is not None:
                salida.write(t("tui.close.evidence", dir=str(result.ruta_paquete)))
            for bloqueo in result.bloqueos:
                salida.write(Text(f"- {bloqueo}", style="red"))
            if not result.aprobado:
                salida.write(t("tui.close.blocked"))
            else:
                salida.write(t("tui.close.done"))
            self.query_one("#btn-close", Button).disabled = False
            self.action_refresh()

    return TramaliaApp


def run() -> None:
    build_app()().run()
