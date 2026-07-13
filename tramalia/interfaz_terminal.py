"""Provide the optional Textual dashboard as a thin, injectable surface."""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from tramalia.core.errores import ErrorExcepcionInvalida, ErrorTramalia
from tramalia.core.habilidades import ResolucionHabilidad
from tramalia.core.modelos import (
    EntradaBitacora,
    ExcepcionFallo,
    ResultadoCierre,
    ValorEstadoBitacora,
    ValorEstadoIntegracion,
    ValorResultadoPuerta,
)
from tramalia.core.tablero import InstantaneaTablero, ProveedorTablero, ServicioTablero
from tramalia.i18n import t

if TYPE_CHECKING:
    from textual.app import App


def construir_aplicacion(servicio: ServicioTablero | None = None) -> App:
    """Build the Textual app around an injectable dashboard service.

    Args:
        servicio: Shared dashboard service. The current directory is used when
            no service is provided.

    Returns:
        A configured Textual application instance.
    """
    from rich.text import Text
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical, VerticalScroll
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
        Switch,
        TabbedContent,
        TabPane,
    )
    from textual.widgets.option_list import Option
    from textual.widgets.selection_list import Selection

    from tramalia import __version__ as version_tramalia
    from tramalia.core import installer
    from tramalia.core.integraciones import REGISTRO, url_documentacion

    class PantallaInstalacion(ModalScreen):
        """Let users select safe installation plans prepared in a worker."""

        CSS = """
        PantallaInstalacion { align: center middle; }
        #inst-box { width: 96; max-height: 85%; border: round $primary;
                    background: $surface; padding: 1 2; }
        #inst-manual { color: $text-muted; padding: 1 0 0 0; }
        #inst-botones { height: 3; align-horizontal: right; }
        #inst-botones Button { margin-left: 2; }
        """
        BINDINGS = [("escape", "cancelar", "cerrar")]

        def __init__(self, planes, manuales) -> None:
            super().__init__()
            self._planes = planes
            self._manuales = manuales

        def action_cancelar(self) -> None:
            self.dismiss([])

        def compose(self) -> ComposeResult:
            with Vertical(id="inst-box"):
                yield Static(f"[b]{t('tui.install.title')}[/b]")
                if self._planes:
                    yield SelectionList(
                        *[
                            Selection(f"{etiqueta} — {opcion.display}", indice, True)
                            for indice, (etiqueta, opcion, _habilita) in enumerate(self._planes)
                        ]
                    )
                if self._manuales:
                    lineas = "\n".join(
                        f"  • {etiqueta} — {comando}" for etiqueta, comando in self._manuales
                    )
                    yield Static(
                        f"[dim]{t('tui.install.manual.header')}\n{lineas}[/dim]",
                        id="inst-manual",
                    )
                with Horizontal(id="inst-botones"):
                    yield Button(t("tui.install.button"), id="inst-ok", variant="primary")
                    yield Button(t("tui.install.cancel"), id="inst-cancel")

        def on_button_pressed(self, evento: Button.Pressed) -> None:
            if evento.button.id == "inst-ok" and self._planes:
                seleccion = self.query_one(SelectionList).selected
                self.dismiss([self._planes[indice] for indice in seleccion])
                return
            self.dismiss([])

    class PantallaProveedor(ModalScreen):
        """Choose one already-probed context provider without blocking compose."""

        CSS = """
        PantallaProveedor { align: center middle; }
        #ctx-box { width: 100; max-height: 85%; border: round $primary;
                   background: $surface; padding: 1 2; }
        #ctx-box OptionList { height: auto; max-height: 20; }
        #ctx-botones { height: 3; align-horizontal: right; }
        """
        BINDINGS = [("escape", "cancelar", "cerrar")]

        def __init__(
            self,
            actual: str,
            proveedores: tuple[ProveedorTablero, ...],
        ) -> None:
            super().__init__()
            self._actual = actual
            self._proveedores = proveedores

        def action_cancelar(self) -> None:
            self.dismiss(None)

        def compose(self) -> ComposeResult:
            with Vertical(id="ctx-box"):
                yield Static(f"[b]{t('tui.ctxbackend.title')}[/b]")
                yield Static(t("tui.ctxbackend.currentline", name=self._actual))
                opciones = OptionList()
                for proveedor in self._proveedores:
                    estado = "✓" if proveedor.disponible else "○"
                    estado_texto = t(
                        "tui.ctxbackend.installed"
                        if proveedor.disponible
                        else "tui.ctxbackend.notinstalled"
                    )
                    actual = (
                        f"  [reverse] {t('tui.ctxbackend.current')} [/reverse]"
                        if proveedor.nombre == self._actual
                        else ""
                    )
                    texto = (
                        f"{estado} [b]{proveedor.etiqueta}[/b]{actual}\n"
                        f"   {proveedor.alcance}\n"
                        f"   {t('tui.ctxbackend.ideal')}: {proveedor.ideal}\n"
                        f"   [dim]{estado_texto}[/dim]"
                    )
                    opciones.add_option(Option(texto, id=proveedor.nombre))
                yield opciones
                with Horizontal(id="ctx-botones"):
                    yield Button(t("tui.install.cancel"), id="ctx-cancel")

        def on_option_list_option_selected(self, evento) -> None:
            self.dismiss(str(evento.option.id))

        def on_button_pressed(self, _evento: Button.Pressed) -> None:
            self.dismiss(None)

    marcas_bitacora = {
        "aprobado": "✓ aprobado",
        "aprobado_con_excepciones": "⚠ aprobado_con_excepciones",
        "bloqueado": "✗ bloqueado",
        "invalida": "✗ invalida",
    }

    def estado_entrada(entrada: EntradaBitacora) -> str:
        if entrada.estado is ValorEstadoBitacora.INVALIDA:
            return entrada.estado.value
        return entrada.resultado.value if entrada.resultado is not None else entrada.estado.value

    class AplicacionTramalia(App):
        """Render immutable snapshots and dispatch every blocking task to threads."""

        TITLE = f"Tramalia v{version_tramalia}"
        SUB_TITLE = t("tui.subtitle")
        ENABLE_COMMAND_PALETTE = False
        BINDINGS = [
            ("q", "quit", t("tui.binding.quit")),
            ("r", "actualizar", t("tui.binding.refresh")),
            ("i", "instalar_faltantes", t("tui.binding.install")),
            ("s", "sincronizar_habilidades", t("tui.binding.skills")),
            ("d", "abrir_documentacion", t("tui.binding.docs")),
            ("c", "cancelar_instalacion", t("tui.binding.cancel")),
            ("b", "proveedor_contexto", t("tui.binding.contextbackend")),
            ("u", "comprobar_actualizaciones", t("tui.binding.checkupdates")),
            ("escape", "cerrar_paneles", t("tui.binding.closepanels")),
        ]
        CSS = """
        #estado, #gates-linea, #lastclose, #estado-integraciones { padding: 0 1; }
        #detalle-log { padding: 0 1; height: 1fr; overflow-y: auto; }
        #cierre-form { height: 1fr; overflow-y: auto; }
        #cierre-form Input, #cierre-form Switch { margin: 0 1; }
        #cerrar, #btn-init, #btn-init-resumen { margin: 1 1; }
        #taskinfo, #error-cierre { padding: 0 1; color: $text-muted; max-height: 10;
                                  overflow-y: auto; }
        #error-cierre { color: $error; }
        #salida { height: 1fr; margin: 0 1; border: round $primary; }
        #resumen-cuerpo { height: 1fr; }
        #instalador { width: 45%; margin: 0 1; border: round $secondary; display: none; }
        #skills-hint { padding: 0 1; color: $text-muted; }
        #skills-log { height: 8; margin: 0 1; border: round $secondary; display: none; }
        #aviso-uninit, #aviso-audit { padding: 1 1; }
        DataTable { height: 1fr; }
        """

        def __init__(self, servicio_tablero: ServicioTablero) -> None:
            super().__init__()
            self._servicio_tablero = servicio_tablero
            self._instantanea: InstantaneaTablero | None = None
            self._detalles_bitacora: dict[str, str] = {}
            self._habilidades_por_nombre: dict[str, ResolucionHabilidad] = {}
            self._urls_documentacion: dict[str, str] = {}
            self._actualizaciones_habilidades: dict[str, bool] = {}
            self._cancelacion_instalacion = threading.Event()
            self._desmontada = False
            self._aplicando_instantanea = False

        def compose(self) -> ComposeResult:
            yield Header()
            with TabbedContent(initial="resumen"):
                with TabPane(t("tui.tab.summary"), id="resumen"):
                    yield Static(id="estado")
                    yield Button(
                        t("tui.close.init.button"),
                        id="btn-init-resumen",
                        variant="warning",
                    )
                    yield Static(id="gates-linea")
                    yield Static(id="lastclose")
                    yield Static(id="pathaviso")
                    yield Static(id="ctxbackend")
                    yield Static(id="estado-integraciones")
                    with Horizontal(id="resumen-cuerpo"):
                        yield DataTable(id="tabla-doctor", cursor_type="row")
                        yield RichLog(id="instalador", wrap=True, markup=True)
                with TabPane(t("tui.tab.skills"), id="skills"):
                    yield Static(t("tui.skills.hint"), id="skills-hint")
                    yield Input(
                        placeholder=t("tui.skills.url.placeholder"),
                        id="skill-url",
                    )
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
                    with VerticalScroll(id="cierre-form"):
                        yield Input(placeholder=t("tui.close.task.placeholder"), id="in-task")
                        yield Static(id="taskinfo")
                        yield Input(placeholder=t("tui.close.agent.placeholder"), id="in-agent")
                        yield Input(
                            placeholder=t("tui.close.reviewer.placeholder"),
                            id="in-reviewer",
                        )
                        yield Input(placeholder=t("tui.close.model.placeholder"), id="in-model")
                        yield Static(t("tui.excepcion.permitir"))
                        yield Switch(
                            False,
                            id="permitir-excepcion",
                            tooltip=t("tui.excepcion.permitir"),
                        )
                        yield Input(placeholder=t("tui.excepcion.razon"), id="razon-excepcion")
                        yield Input(placeholder=t("tui.excepcion.riesgo"), id="riesgo-aceptado")
                        yield Input(placeholder=t("tui.excepcion.control"), id="control-afectado")
                        yield Input(
                            placeholder=t("tui.excepcion.referencia"),
                            id="referencia-excepcion",
                        )
                        yield Input(
                            placeholder=t("tui.excepcion.revisor"),
                            id="revisor-excepcion",
                        )
                        yield Input(placeholder=t("tui.excepcion.expira"), id="expira-en")
                        yield Input(
                            placeholder=t("tui.excepcion.remediacion"),
                            id="condicion-remediacion",
                        )
                        yield Static(id="error-cierre")
                        yield Button(t("tui.close.button"), id="cerrar", variant="primary")
                        yield RichLog(id="salida", wrap=True, markup=True)
            yield Footer()

        def on_mount(self) -> None:
            self.action_actualizar()

        def on_unmount(self) -> None:
            # La señal cooperativa evita dejar un instalador vivo tras cerrar la app.
            self._desmontada = True
            self._cancelacion_instalacion.set()

        def _publicar_desde_hilo(self, funcion, *argumentos) -> None:
            if self._desmontada:
                return
            try:
                self.call_from_thread(funcion, *argumentos)
            except RuntimeError:
                # Textual puede haber desmontado el bucle entre la comprobación y el callback.
                return

        def action_actualizar(self) -> None:
            """Schedule one complete snapshot refresh in a worker thread."""
            self.query_one("#estado", Static).update(t("tui.estado.cargando"))
            self.run_worker(
                self._cargar_instantanea,
                thread=True,
                exclusive=True,
                group="instantanea",
            )

        def _cargar_instantanea(self) -> None:
            try:
                instantanea = self._servicio_tablero.obtener_instantanea()
            except ErrorTramalia as error_dominio:
                self._publicar_desde_hilo(self._mostrar_error, error_dominio)
                return
            self._publicar_desde_hilo(self._mostrar_instantanea, instantanea)

        def _mostrar_error(self, error_dominio: ErrorTramalia) -> None:
            self.query_one("#estado", Static).update(
                f"[red]{error_dominio.mensaje}[/red] {error_dominio.sugerencia}"
            )

        def _texto_integracion(self, integracion) -> str:
            argumentos = {
                "capacidad": integracion.capacidad,
                "impacto": integracion.impacto,
                "remediacion": integracion.remediacion,
            }
            if integracion.motivo in {"proceso_agotado", "git_tiempo_agotado"}:
                clave = "tui.integracion.tiempo_agotado"
            elif integracion.motivo == "proceso_cancelado":
                clave = "tui.integracion.cancelada"
            elif integracion.estado is ValorEstadoIntegracion.DEGRADADO:
                clave = "tui.integracion.degradada"
            else:
                clave = "tui.integracion.fallida"
            return t(clave, **argumentos)

        def _mostrar_instantanea(self, instantanea: InstantaneaTablero) -> None:
            """Render every table from one immutable snapshot only."""
            self._instantanea = instantanea
            listo = instantanea.proyecto.listo
            estado = t("tui.state.initialized") if listo else t("tui.state.uninitialized")
            self.query_one("#estado", Static).update(
                t(
                    "tui.header",
                    path=str(instantanea.raiz),
                    stack=", ".join(instantanea.tecnologias) or "—",
                    estado=estado,
                )
            )
            self.query_one("#btn-init-resumen", Button).display = not listo
            self.query_one("#gates-linea", Static).update(
                t("tui.gates.line", gates=" · ".join(instantanea.puertas))
                if instantanea.puertas
                else t("tui.gates.none")
            )
            ultimo = ""
            if instantanea.bitacora:
                entrada = instantanea.bitacora[0]
                valor = estado_entrada(entrada)
                ultimo = t(
                    "tui.lastclose",
                    id=entrada.id_paquete,
                    mark=marcas_bitacora.get(valor, f"○ {valor}"),
                )
            self.query_one("#lastclose", Static).update(ultimo)
            self.query_one("#pathaviso", Static).update(
                ""
                if instantanea.uv_en_ruta
                else f"[yellow]▲ {t('doctor.path.uv.missing')}[/yellow]"
            )
            self.query_one("#ctxbackend", Static).update(
                t("tui.ctxbackend.line", name=instantanea.proveedor_contexto) if listo else ""
            )
            self.query_one("#estado-integraciones", Static).update(
                "\n".join(self._texto_integracion(i) for i in instantanea.integraciones)
            )

            self._urls_documentacion = {}
            tabla_doctor = self.query_one("#tabla-doctor", DataTable)
            tabla_doctor.clear(columns=True)
            tabla_doctor.add_columns(
                t("tui.col.tool"),
                t("tui.col.purpose"),
                t("tui.col.state"),
                t("tui.col.detail"),
            )
            categoria_anterior = None
            for herramienta in instantanea.herramientas:
                if herramienta.categoria != categoria_anterior:
                    categoria_anterior = herramienta.categoria
                    tabla_doctor.add_row(
                        f"[bold cyan]· {t('doctor.group.' + herramienta.categoria)}[/]",
                        "",
                        "",
                        "",
                    )
                marca = (
                    t("tui.status.ok")
                    if herramienta.presente
                    else t("tui.status.optional")
                    if herramienta.categoria in {"feature", "agent"}
                    else t("tui.status.missing")
                )
                tabla_doctor.add_row(
                    f"  {herramienta.comando}",
                    herramienta.proposito,
                    marca,
                    herramienta.detalle,
                )
                if herramienta.herramienta is not None:
                    self._urls_documentacion[herramienta.comando] = url_documentacion(
                        herramienta.herramienta
                    )

            tabla_habilidades = self.query_one("#tabla-skills", DataTable)
            tabla_habilidades.clear(columns=True)
            tabla_habilidades.add_columns(
                t("tui.skills.col.name"),
                t("tui.col.state"),
                t("tui.skills.col.info"),
            )
            self._habilidades_por_nombre = {
                habilidad.nombre: habilidad for habilidad in instantanea.habilidades
            }
            aviso_habilidades = t("tui.skills.hint") if listo else t("tui.skills.uninit")
            if instantanea.habilidades_rastreadas:
                aviso_habilidades += (
                    "\n[yellow]"
                    + t(
                        "skills.tracked.warn",
                        names=", ".join(instantanea.habilidades_rastreadas),
                    )
                    + "[/yellow]"
                )
            self.query_one("#skills-hint", Static).update(aviso_habilidades)
            if listo:
                tabla_habilidades.add_row(f"[bold cyan]· {t('skills.group.own')}[/]", "", "")
                for habilidad_propia in instantanea.habilidades_propias:
                    tabla_habilidades.add_row(
                        f"  {habilidad_propia.nombre}",
                        t("skills.state.installed"),
                        habilidad_propia.descripcion,
                    )
                tabla_habilidades.add_row(f"[bold cyan]· {t('skills.group.external')}[/]", "", "")
                for resolucion_habilidad in instantanea.habilidades:
                    estado_habilidad = (
                        t("skills.state.installed")
                        if resolucion_habilidad.sha_resuelto
                        else t("skills.state.declared")
                    )
                    informacion = (
                        f"@{resolucion_habilidad.sha_resuelto[:7]}"
                        if resolucion_habilidad.sha_resuelto
                        else resolucion_habilidad.fuente
                    )
                    if self._actualizaciones_habilidades.get(resolucion_habilidad.nombre):
                        informacion += f"  [yellow]⬆ {t('skills.update.available')}[/yellow]"
                    tabla_habilidades.add_row(
                        f"  {resolucion_habilidad.nombre}",
                        estado_habilidad,
                        informacion,
                    )

            tabla_bitacora = self.query_one("#tabla-log", DataTable)
            tabla_bitacora.clear(columns=True)
            aviso_auditoria = self.query_one("#aviso-audit", Static)
            self._detalles_bitacora = {
                detalle.id_paquete: detalle.texto for detalle in instantanea.detalles_bitacora
            }
            if not listo:
                aviso_auditoria.update(t("tui.audit.uninit"))
            elif not instantanea.bitacora:
                aviso_auditoria.update(t("tui.audit.empty"))
            else:
                aviso_auditoria.update("")
                tabla_bitacora.add_columns(
                    t("tui.col.close"), t("tui.col.status"), t("tui.col.agent")
                )
                for entrada in instantanea.bitacora:
                    modelo = f" ({entrada.modelo})" if entrada.modelo else ""
                    tabla_bitacora.add_row(
                        entrada.id_paquete,
                        estado_entrada(entrada),
                        (entrada.agente or "—") + modelo,
                    )
                primera = instantanea.bitacora[0]
                detalle = self._detalles_bitacora.get(primera.id_paquete, "")
                if primera.estado is ValorEstadoBitacora.INVALIDA:
                    detalle = primera.error or detalle or t("tui.audit.nometa")
                self.query_one("#detalle-log", Static).update(detalle)

            aviso_cierre = self.query_one("#aviso-uninit", Static)
            boton_inicializar = self.query_one("#btn-init", Button)
            formulario = self.query_one("#cierre-form", VerticalScroll)
            if not listo:
                aviso_cierre.update(t("tui.close.uninit"))
                boton_inicializar.display = True
                formulario.display = False
            else:
                aviso_cierre.update("")
                boton_inicializar.display = False
                formulario.display = True
                self._aplicando_instantanea = True
                try:
                    tarea = self.query_one("#in-task", Input)
                    if not tarea.value:
                        tarea.value = instantanea.id_tarea or ""
                    agente = self.query_one("#in-agent", Input)
                    if not agente.value:
                        agente.value = instantanea.agente
                    revisor = self.query_one("#in-reviewer", Input)
                    if not revisor.value:
                        revisor.value = instantanea.revisor
                    self._mostrar_descripcion_tarea(instantanea.descripcion_tarea)
                finally:
                    self._aplicando_instantanea = False

        def _mostrar_descripcion_tarea(self, descripcion: str | None) -> None:
            panel = self.query_one("#taskinfo", Static)
            if descripcion:
                panel.update(f"[dim]{t('tui.close.taskinfo.header')}[/dim]\n{descripcion}")
            elif self.query_one("#in-task", Input).value.strip():
                panel.update(f"[yellow]{t('tui.close.taskinfo.none')}[/yellow]")
            else:
                panel.update("")

        def on_input_changed(self, evento: Input.Changed) -> None:
            if (
                evento.input.id != "in-task"
                or self._aplicando_instantanea
                or not hasattr(self._servicio_tablero, "describir_tarea")
            ):
                return
            id_tarea = evento.value.strip()
            self.run_worker(
                lambda: self._cargar_descripcion_tarea(id_tarea),
                thread=True,
                exclusive=True,
                group="descripcion-tarea",
            )

        def _cargar_descripcion_tarea(self, id_tarea: str) -> None:
            descripcion = self._servicio_tablero.describir_tarea(id_tarea)
            self._publicar_desde_hilo(self._mostrar_descripcion_tarea, descripcion)

        def on_data_table_row_selected(self, evento: DataTable.RowSelected) -> None:
            if evento.data_table.id == "tabla-log":
                fila = evento.data_table.get_row(evento.row_key)
                id_paquete = str(fila[0])
                self.query_one("#detalle-log", Static).update(
                    self._detalles_bitacora.get(id_paquete, t("tui.audit.nometa"))
                )
                return
            if evento.data_table.id != "tabla-skills":
                return
            nombre = str(evento.data_table.get_row(evento.row_key)[0]).strip()
            habilidad = self._habilidades_por_nombre.get(nombre)
            if habilidad is None:
                return
            self._registro_habilidades().write(t("skills.install.one", name=nombre))
            self.run_worker(
                lambda: self._trabajador_habilidad(
                    nombre,
                    habilitar=habilidad.sha_resuelto is None,
                    actualizar=True,
                ),
                thread=True,
                exclusive=True,
                group="habilidades",
            )

        def on_input_submitted(self, evento: Input.Submitted) -> None:
            if evento.input.id != "skill-url" or not evento.value.strip():
                return
            self.run_worker(
                lambda: self._trabajador_agregar_habilidad(evento.value.strip()),
                thread=True,
                exclusive=True,
                group="habilidades",
            )

        def _trabajador_agregar_habilidad(self, fuente: str) -> None:
            resultado = self._servicio_tablero.agregar_habilidad(fuente)
            self._publicar_desde_hilo(self._mostrar_habilidad_agregada, resultado)

        def _mostrar_habilidad_agregada(self, resultado: tuple[bool, str]) -> None:
            correcta, detalle = resultado
            self._registro_habilidades().write(
                t("skills.add.ok", name=detalle) if correcta else t(f"skills.add.{detalle}")
            )
            if correcta:
                self.query_one("#skill-url", Input).value = ""
                self.action_actualizar()

        def _registro_habilidades(self) -> RichLog:
            registro = self.query_one("#skills-log", RichLog)
            registro.display = True
            return registro

        def _trabajador_habilidad(
            self,
            nombre: str,
            *,
            habilitar: bool,
            actualizar: bool,
        ) -> None:
            resultado = self._servicio_tablero.habilitar_y_sincronizar(
                nombre,
                habilitar=habilitar,
                actualizar=actualizar,
            )
            self._publicar_desde_hilo(self._mostrar_resultado_habilidad, nombre, resultado)

        def _mostrar_resultado_habilidad(self, nombre, resultado) -> None:
            registro = self._registro_habilidades()
            resolucion = next(
                (item for item in resultado.resoluciones if item.nombre == nombre), None
            )
            if resolucion is not None and resolucion.estado.exitoso:
                registro.write(t("skills.update.ok", name=nombre))
            elif resultado.estado.motivo == "git_no_instalado":
                registro.write(t("skills.install.nogit"))
            else:
                registro.write(t("skills.install.fail", name=nombre))
            self._actualizaciones_habilidades.pop(nombre, None)
            self.action_actualizar()

        def action_sincronizar_habilidades(self) -> None:
            """Synchronize locked skills in a worker thread."""
            self.query_one(TabbedContent).active = "skills"
            self._registro_habilidades().write(t("tui.skills.sync.running"))
            self.run_worker(
                self._trabajador_sincronizacion,
                thread=True,
                exclusive=True,
                group="habilidades",
            )

        def _trabajador_sincronizacion(self) -> None:
            resultado = self._servicio_tablero.sincronizar_habilidades()
            self._publicar_desde_hilo(self._mostrar_sincronizacion, resultado)

        def _mostrar_sincronizacion(self, resultado) -> None:
            registro = self._registro_habilidades()
            if not resultado.resoluciones:
                registro.write(t("tui.skills.sync.none"))
            total = len(resultado.resoluciones)
            for numero, resolucion in enumerate(resultado.resoluciones, 1):
                registro.write(f"[{numero}/{total}] {resolucion.accion:>12}  {resolucion.nombre}")
            if total:
                correctas = sum(
                    1 for resolucion in resultado.resoluciones if resolucion.estado.exitoso
                )
                registro.write(t("tui.skills.sync.summary", ok=correctas, total=total))
            self.action_actualizar()

        def action_comprobar_actualizaciones(self) -> None:
            """Check remote skill references in a worker thread."""
            if self._instantanea is None or not self._instantanea.proyecto.listo:
                self.notify(t("tui.close.uninit"), severity="warning", markup=False)
                return
            self.query_one(TabbedContent).active = "skills"
            self._registro_habilidades().write(t("skills.update.checking"))
            self.run_worker(
                self._trabajador_actualizaciones,
                thread=True,
                exclusive=True,
                group="habilidades",
            )

        def _trabajador_actualizaciones(self) -> None:
            estados = self._servicio_tablero.consultar_actualizaciones()
            self._publicar_desde_hilo(self._mostrar_actualizaciones, estados)

        def _mostrar_actualizaciones(self, estados) -> None:
            fallidas = [
                estado
                for estado in estados
                if not estado.estado.exitoso and estado.estado.motivo != "habilidad_no_instalada"
            ]
            self._actualizaciones_habilidades = {
                estado.nombre: estado.estado.motivo == "actualizacion_disponible"
                for estado in estados
                if estado.sha_resuelto and estado.estado.exitoso
            }
            registro = self._registro_habilidades()
            for estado in fallidas:
                registro.write(
                    t(
                        "skills.outdated.fail",
                        name=estado.nombre,
                        reason=estado.estado.motivo,
                        remediation=estado.estado.remediacion,
                    )
                )
            cantidad = sum(self._actualizaciones_habilidades.values())
            if cantidad or not fallidas:
                registro.write(t("skills.update.found", n=cantidad))
            self.action_actualizar()

        def on_button_pressed(self, evento: Button.Pressed) -> None:
            if evento.button.id in {"btn-init", "btn-init-resumen"}:
                evento.button.disabled = True
                self.run_worker(
                    lambda: self._trabajador_inicializacion(evento.button.id or ""),
                    thread=True,
                    exclusive=True,
                    group="inicializacion",
                )
            elif evento.button.id == "cerrar":
                self._iniciar_cierre(evento.button)

        def _trabajador_inicializacion(self, id_boton: str) -> None:
            try:
                self._servicio_tablero.inicializar(version_tramalia)
            except ErrorTramalia as error_dominio:
                self._publicar_desde_hilo(self._terminar_inicializacion, id_boton, error_dominio)
                return
            self._publicar_desde_hilo(self._terminar_inicializacion, id_boton, None)

        def _terminar_inicializacion(
            self,
            id_boton: str,
            error_dominio: ErrorTramalia | None,
        ) -> None:
            boton = self.query_one(f"#{id_boton}", Button)
            boton.disabled = False
            if error_dominio is not None:
                self.notify(error_dominio.mensaje, severity="error", markup=False)
                return
            self.notify(t("tui.init.done"), markup=False)
            self.action_actualizar()

        def _construir_excepciones_formulario(self) -> tuple[ExcepcionFallo, ...]:
            if not self.query_one("#permitir-excepcion", Switch).value:
                return ()
            texto_expiracion = self.query_one("#expira-en", Input).value.strip()
            try:
                expiracion = datetime.fromisoformat(texto_expiracion) if texto_expiracion else None
            except ValueError as error_fecha:
                raise ErrorExcepcionInvalida(
                    "La expiracion no es ISO 8601.",
                    "Usa una fecha como 2026-08-01T00:00:00+00:00.",
                    detalles={"expira_en": texto_expiracion},
                ) from error_fecha
            return (
                ExcepcionFallo(
                    self.query_one("#razon-excepcion", Input).value.strip(),
                    self.query_one("#riesgo-aceptado", Input).value.strip(),
                    self.query_one("#control-afectado", Input).value.strip(),
                    self.query_one("#referencia-excepcion", Input).value.strip(),
                    self.query_one("#revisor-excepcion", Input).value.strip(),
                    expiracion,
                    self.query_one("#condicion-remediacion", Input).value.strip() or None,
                ),
            )

        def _iniciar_cierre(self, boton: Button) -> None:
            error = self.query_one("#error-cierre", Static)
            error.update("")
            if self._instantanea is None or not self._instantanea.proyecto.listo:
                error.update(t("tui.close.uninit"))
                return
            id_tarea = self.query_one("#in-task", Input).value.strip()
            if not id_tarea:
                error.update(t("tui.close.needtask"))
                return
            try:
                excepciones = self._construir_excepciones_formulario()
            except ErrorExcepcionInvalida as error_excepcion:
                error.update(f"{error_excepcion.mensaje} {error_excepcion.sugerencia}")
                return
            agente = self.query_one("#in-agent", Input).value.strip()
            revisor = self.query_one("#in-reviewer", Input).value.strip()
            modelo = self.query_one("#in-model", Input).value.strip()
            self.query_one("#salida", RichLog).write(t("tui.close.running", task=id_tarea))
            boton.disabled = True
            self.run_worker(
                lambda: self._trabajador_cierre(id_tarea, agente, revisor, modelo, excepciones),
                thread=True,
                exclusive=True,
                group="cierre",
            )

        def _trabajador_cierre(
            self,
            id_tarea: str,
            agente: str,
            revisor: str,
            modelo: str,
            excepciones: tuple[ExcepcionFallo, ...],
        ) -> None:
            try:
                resultado = self._servicio_tablero.cerrar(
                    id_tarea,
                    agente=agente,
                    revisor=revisor,
                    modelo=modelo,
                    excepciones=excepciones,
                )
            except ErrorTramalia as error_dominio:
                self._publicar_desde_hilo(self._mostrar_error_cierre, error_dominio.mensaje)
                return
            except Exception as error_inesperado:
                self._publicar_desde_hilo(self._mostrar_error_cierre, str(error_inesperado))
                return
            self._publicar_desde_hilo(self._mostrar_resultado_cierre, resultado)

        def _mostrar_error_cierre(self, mensaje: str) -> None:
            self.query_one("#salida", RichLog).write(t("tui.close.error", msg=mensaje))
            self.query_one("#cerrar", Button).disabled = False

        def _mostrar_resultado_cierre(self, resultado: ResultadoCierre) -> None:
            salida = self.query_one("#salida", RichLog)
            for puerta in resultado.ejecucion.resultados:
                salida.write(
                    t("tui.close.gate.ok", name=puerta.nombre)
                    if puerta.estado is ValorResultadoPuerta.APROBADO
                    else t("tui.close.gate.fail", name=puerta.nombre)
                )
            salida.write(t("tui.close.status", status=resultado.estado.value))
            if resultado.ruta_paquete is not None:
                salida.write(t("tui.close.evidence", dir=str(resultado.ruta_paquete)))
            for bloqueo in resultado.bloqueos:
                salida.write(Text(f"- {bloqueo}", style="red"))
            salida.write(t("tui.close.done") if resultado.aprobado else t("tui.close.blocked"))
            self.query_one("#cerrar", Button).disabled = False
            self.action_actualizar()

        def action_instalar_faltantes(self) -> None:
            """Prepare installation choices in a worker thread."""
            if self._instantanea is None:
                return
            self.query_one(TabbedContent).active = "resumen"
            self.run_worker(
                lambda: self._preparar_instalaciones(self._instantanea),
                thread=True,
                exclusive=True,
                group="preparar-instalacion",
            )

        def _preparar_instalaciones(self, instantanea: InstantaneaTablero) -> None:
            faltantes = [
                fila.herramienta
                for fila in instantanea.herramientas
                if not fila.presente and fila.herramienta is not None
            ]
            automaticas, manuales, entornos = installer.plan_for(faltantes)
            planes: list[tuple[str, installer.InstallOption, list[str]]] = [
                (comando, opcion, []) for comando, opcion in automaticas
            ]
            for nombre, opcion, habilita in entornos:
                planes.append(
                    (
                        t(
                            "tui.install.runtime",
                            rt=nombre,
                            tools=", ".join(habilita),
                        ),
                        opcion,
                        list(habilita),
                    )
                )
            filas_manuales: list[tuple[str, str]] = []
            for comando, mostrar, entorno in manuales:
                etiqueta = (
                    comando
                    if not entorno
                    else t(
                        "tui.install.needs",
                        tool=comando,
                        rt=installer._RUNTIME_NAME.get(entorno, entorno),
                    )
                )
                filas_manuales.append((etiqueta, mostrar))
            if not instantanea.uv_en_ruta and installer.shutil.which("uv"):
                planes.append((t("tui.install.pathfix"), installer.pathfix_option(), []))
            self._publicar_desde_hilo(self._mostrar_instalaciones, planes, filas_manuales)

        def _mostrar_instalaciones(self, planes, manuales) -> None:
            if not planes and not manuales:
                self._registro_instalacion().write(t("tui.install.none"))
                return
            self.push_screen(PantallaInstalacion(planes, manuales), self._iniciar_instalaciones)

        def _iniciar_instalaciones(self, seleccion) -> None:
            if not seleccion:
                return
            self._cancelacion_instalacion.clear()
            self.run_worker(
                lambda: self._trabajador_instalacion(seleccion),
                thread=True,
                exclusive=True,
                group="instalacion",
            )

        def action_cancelar_instalacion(self) -> None:
            """Signal cooperative cancellation for the current installer."""
            self._cancelacion_instalacion.set()

        def _trabajador_instalacion(self, seleccion) -> None:
            cola = list(seleccion)
            indice = 0
            while indice < len(cola) and not self._desmontada:
                etiqueta, opcion, habilita = cola[indice]
                indice += 1
                self._cancelacion_instalacion.clear()
                self._publicar_desde_hilo(
                    self._escribir_instalacion,
                    t(
                        "tui.install.installing",
                        n=indice,
                        total=len(cola),
                        tool=etiqueta,
                        method=opcion.method,
                        cmd=opcion.display,
                    ),
                )
                codigo, salida = installer.run_install_streaming(
                    opcion,
                    on_line=lambda linea: self._publicar_desde_hilo(
                        self._escribir_instalacion, f"[dim]{linea}[/dim]"
                    ),
                    cancel=self._cancelacion_instalacion,
                )
                if codigo == 0:
                    self._publicar_desde_hilo(
                        self._escribir_instalacion,
                        t("tui.install.ok", tool=etiqueta),
                    )
                    installer.refresh_runtime_path()
                    for comando in habilita:
                        herramienta = next(
                            (item for item in REGISTRO if item.comando == comando), None
                        )
                        opcion_nueva = installer.best_auto(herramienta) if herramienta else None
                        if opcion_nueva:
                            cola.append((comando, opcion_nueva, []))
                elif codigo == 130:
                    self._publicar_desde_hilo(
                        self._escribir_instalacion,
                        t("tui.install.cancelled", tool=etiqueta),
                    )
                elif codigo == 124:
                    self._publicar_desde_hilo(
                        self._escribir_instalacion,
                        t("tui.install.timeout", tool=etiqueta),
                    )
                else:
                    self._publicar_desde_hilo(
                        self._escribir_instalacion,
                        t("tui.install.fail", tool=etiqueta, code=codigo),
                    )
                    if installer.needs_admin(salida):
                        self._publicar_desde_hilo(
                            self._escribir_instalacion,
                            t("tui.install.admin", tool=etiqueta),
                        )
            self._publicar_desde_hilo(self._terminar_instalaciones)

        def _registro_instalacion(self) -> RichLog:
            registro = self.query_one("#instalador", RichLog)
            registro.display = True
            return registro

        def _escribir_instalacion(self, mensaje: str) -> None:
            self._registro_instalacion().write(mensaje)

        def _terminar_instalaciones(self) -> None:
            self._escribir_instalacion(t("tui.install.done"))
            self.action_actualizar()

        def action_abrir_documentacion(self) -> None:
            """Open the selected documentation URL outside the event loop."""
            if self.query_one(TabbedContent).active == "skills":
                tabla = self.query_one("#tabla-skills", DataTable)
                try:
                    nombre = str(tabla.get_row_at(tabla.cursor_row)[0]).strip()
                except Exception:
                    return
                habilidad = self._habilidades_por_nombre.get(nombre)
                url = (
                    habilidad.fuente.removeprefix("git+").removesuffix(".git")
                    if habilidad is not None and habilidad.fuente
                    else "https://mscottb.github.io/tramalia/skills-guia/"
                    if len(nombre) >= 2 and nombre[:2].isdigit()
                    else ""
                )
            else:
                tabla = self.query_one("#tabla-doctor", DataTable)
                try:
                    comando = str(tabla.get_row_at(tabla.cursor_row)[0]).strip()
                except Exception:
                    return
                url = self._urls_documentacion.get(comando, "")
            if not url:
                self.notify(t("tui.docs.none"), severity="warning", markup=False)
                return
            self.run_worker(
                lambda: self._abrir_url(url),
                thread=True,
                exclusive=False,
                group="documentacion",
            )

        def _abrir_url(self, url: str) -> None:
            import webbrowser

            webbrowser.open(url)
            self._publicar_desde_hilo(self._notificar_documentacion_abierta, url)

        def _notificar_documentacion_abierta(self, url: str) -> None:
            self.notify(t("tui.docs.opened", url=url), markup=False)

        def action_cerrar_paneles(self) -> None:
            """Hide transient installer and skill logs."""
            for selector in ("#instalador", "#skills-log"):
                self.query_one(selector, RichLog).display = False

        def action_proveedor_contexto(self) -> None:
            """Open the provider chooser using only the current snapshot."""
            if self._instantanea is None or not self._instantanea.proyecto.listo:
                self.notify(t("tui.close.uninit"), severity="warning", markup=False)
                return
            self.push_screen(
                PantallaProveedor(
                    self._instantanea.proveedor_contexto,
                    self._instantanea.proveedores,
                ),
                self._proveedor_elegido,
            )

        def _proveedor_elegido(self, nombre: str | None) -> None:
            if not nombre:
                return
            self.run_worker(
                lambda: self._trabajador_proveedor(nombre),
                thread=True,
                exclusive=True,
                group="proveedor",
            )

        def _trabajador_proveedor(self, nombre: str) -> None:
            resultado = self._servicio_tablero.fijar_proveedor(nombre)
            self._publicar_desde_hilo(self._mostrar_proveedor, nombre, resultado)

        def _mostrar_proveedor(
            self,
            nombre: str,
            resultado: tuple[bool, bool],
        ) -> None:
            guardado, disponible = resultado
            if not guardado:
                self.notify(t("tui.ctxbackend.fail"), severity="error", markup=False)
                return
            self.notify(
                t(
                    "tui.ctxbackend.ok" if disponible else "tui.ctxbackend.oknotinstalled",
                    name=nombre,
                ),
                severity="information" if disponible else "warning",
                markup=False,
            )
            self.action_actualizar()

    servicio_elegido = servicio if servicio is not None else ServicioTablero(Path.cwd())
    return AplicacionTramalia(servicio_elegido)


def ejecutar() -> None:
    """Run the optional Textual dashboard."""
    construir_aplicacion().run()
