"""Render Tramalia domain results for terminal users."""

from __future__ import annotations

from pathlib import Path

from tramalia.core.doctor import Report
from tramalia.core.errores import ErrorTramalia
from tramalia.core.modelos import (
    EstadoIntegracion,
    ResultadoCierre,
    ValorEstadoIntegracion,
    ValorResultadoPuerta,
)

_PLANO = False

try:  # La presentación enriquecida es opcional y nunca bloquea la CLI.
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    _consola: Console | None = Console()
    _TIENE_RICH = True
except Exception:  # pragma: no cover - alternativa stdlib
    _consola = None
    _TIENE_RICH = False


def fijar_plano(valor: bool) -> None:
    """Enable or disable plain terminal rendering.

    Args:
        valor: Whether Rich formatting must be disabled.
    """
    global _PLANO
    _PLANO = valor


def _usar_rich() -> bool:
    return _TIENE_RICH and not _PLANO


def cabecera(proyecto: str, tecnologias: list[str], inicializado: bool) -> None:
    """Render the project summary header.

    Args:
        proyecto: Project display name.
        tecnologias: Detected technology labels.
        inicializado: Whether Tramalia governance is ready.
    """
    from tramalia import __version__

    estado = "inicializado" if inicializado else "no inicializado"
    texto_tecnologias = " · ".join(tecnologias) if tecnologias else "—"
    if _usar_rich():
        assert _consola is not None
        _consola.print(
            Panel(
                f"proyecto [bold]{proyecto}[/bold]   stack [bold]{texto_tecnologias}[/bold]   "
                f"estado [{'green' if inicializado else 'yellow'}]{estado}[/]",
                title=f"Tramalia v{__version__}",
                border_style="cyan",
                box=box.ROUNDED,
            )
        )
    else:
        print("=" * 60)
        print(
            f"Tramalia v{__version__} · proyecto {proyecto} · stack {texto_tecnologias} · {estado}"
        )
        print("=" * 60)


# Las capacidades se subdividen por dominio para presentar el diagnóstico.
_GRUPO_CAPACIDAD = {
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
ORDEN_GRUPOS = (
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


def grupo_de(herramienta) -> str:
    """Return the stable presentation group for a tool.

    Args:
        herramienta: Tool descriptor reported by the doctor service.

    Returns:
        Stable group key used by translations and terminal sections.
    """
    if herramienta.categoria == "feature":
        return _GRUPO_CAPACIDAD.get(herramienta.capacidad, "convention")
    return herramienta.categoria


def agrupar_estados(estados) -> list[tuple[str, list]]:
    """Group doctor statuses by domain in a stable order.

    Args:
        estados: Tool statuses returned by the doctor service.

    Returns:
        Ordered pairs containing each non-empty group and its statuses.
    """
    grupos: list[tuple[str, list]] = []
    for grupo in ORDEN_GRUPOS:
        filas = [estado for estado in estados if grupo_de(estado.herramienta) == grupo]
        if filas:
            grupos.append((grupo, filas))
    return grupos


def _sugerencia_para(herramienta) -> str:
    """Selecciona la mejor sugerencia disponible para el sistema actual."""
    from tramalia.core import installer

    mejor = installer.best_auto(herramienta)
    if mejor:
        return mejor.display
    opciones = installer.options_for(herramienta)
    return opciones[0].display if opciones else herramienta.sugerencia_instalacion


def _nota_entorno(herramienta, plano: bool = False) -> str:
    """Explica el entorno ausente que bloquea una instalación automática."""
    from tramalia.core import installer

    entorno = installer.blocking_runtime(herramienta)
    if not entorno:
        return ""
    nombre = installer._RUNTIME_NAME.get(entorno, entorno)
    if plano:
        return f"  · requiere {nombre}"
    return f"  [magenta]· requiere {nombre}[/magenta]"


def renderizar_doctor(informe: Report) -> int:
    """Render a grouped doctor report and return its stable exit code.

    Args:
        informe: Diagnostic report to present.

    Returns:
        Zero when no blocking dependency is missing, otherwise one.
    """
    texto_tecnologias = " · ".join(informe.stack) if informe.stack else "—"
    from tramalia.i18n import t

    def fila(estado_herramienta):
        if estado_herramienta.presente:
            return t("tui.status.ok"), (estado_herramienta.version or "—")
        estado = (
            t("tui.status.optional")
            if estado_herramienta.herramienta.categoria in ("feature", "agent")
            else t("tui.status.missing")
        )
        return estado, _sugerencia_para(estado_herramienta.herramienta)

    if _usar_rich():
        assert _consola is not None
        tabla = Table(box=box.SIMPLE_HEAVY, expand=False)
        tabla.add_column(t("tui.col.tool"), style="bold")
        tabla.add_column(t("tui.col.purpose"), overflow="fold", max_width=32)
        tabla.add_column(t("tui.col.state"))
        tabla.add_column(t("tui.col.detail"), overflow="fold")
        for categoria, filas in agrupar_estados(informe.statuses):
            tabla.add_row(f"[bold cyan]· {t('doctor.group.' + categoria)}[/]", "", "", "")
            for estado_herramienta in filas:
                estado, detalle = fila(estado_herramienta)
                if not estado_herramienta.presente:
                    detalle += _nota_entorno(estado_herramienta.herramienta)
                tabla.add_row(
                    f"  {estado_herramienta.herramienta.comando}",
                    estado_herramienta.herramienta.rol,
                    estado,
                    detalle,
                )
        _consola.print(f"\n[dim]{t('doctor.stack')}[/dim] {texto_tecnologias}")
        _consola.print(tabla)
    else:
        print(f"\n{t('doctor.stack')} {texto_tecnologias}")
        for categoria, filas in agrupar_estados(informe.statuses):
            print(f"\n-- {t('doctor.group.' + categoria)} " + "-" * 40)
            for estado_herramienta in filas:
                _, detalle = fila(estado_herramienta)
                estado = (
                    "instalada"
                    if estado_herramienta.presente
                    else "no-inst(opc)"
                    if estado_herramienta.herramienta.categoria in ("feature", "agent")
                    else "NO INSTALADA"
                )
                if not estado_herramienta.presente:
                    detalle += _nota_entorno(estado_herramienta.herramienta, plano=True)
                print(
                    f"{estado_herramienta.herramienta.comando:<13}"
                    f"{estado:<14}{estado_herramienta.herramienta.rol} — {detalle}"
                )

    if not getattr(informe, "uv_bin_on_path", True):
        advertir(t("doctor.path.uv.missing"))

    if informe.needs_node:
        advertir(f"Node no está instalado y lo requieren: {', '.join(informe.node_tools)}.")
        informar("instálalo con `mise use node@22` (o nvm) para usar sync / ux / context completo.")

    bloqueantes = informe.missing_blocking
    opcionales = informe.missing_optional
    if bloqueantes:
        nombres = ", ".join(estado.herramienta.comando for estado in bloqueantes)
        advertir(f"faltan herramientas requeridas: {nombres}")
        informar("instálalas con los comandos de arriba y vuelve a correr `tramalia doctor`.")
        informar("una vez que tengas mise, el resto se instala con `mise install`.")
        return 1
    if opcionales:
        nombres = ", ".join(estado.herramienta.comando for estado in opcionales)
        informar(f"opcionales ausentes (se activan al usar su gate): {nombres}")
    exito("todo lo requerido está presente.")
    return 0


def exito(mensaje: str) -> None:
    """Render a successful terminal message."""
    if _usar_rich():
        assert _consola is not None
        _consola.print(f"[green]✓[/green] {mensaje}")
    else:
        print(f"[ok] {mensaje}")


def advertir(mensaje: str) -> None:
    """Render a warning terminal message."""
    if _usar_rich():
        assert _consola is not None
        _consola.print(f"[yellow]▲[/yellow] {mensaje}")
    else:
        print(f"[!] {mensaje}")


def informar(mensaje: str) -> None:
    """Render an informational terminal message."""
    if _usar_rich():
        assert _consola is not None
        _consola.print(f"[cyan]i[/cyan] {mensaje}")
    else:
        print(f"[i] {mensaje}")


def error(mensaje: str) -> None:
    """Render an error terminal message."""
    if _usar_rich():
        assert _consola is not None
        _consola.print(f"[red]✗[/red] {mensaje}")
    else:
        print(f"[x] {mensaje}")


def renderizar_error(error_dominio: ErrorTramalia) -> None:
    """Render a stable domain error without exposing an implementation traceback.

    Args:
        error_dominio: Recoverable domain error raised by a shared operation.
    """
    error(f"[{error_dominio.codigo}] {error_dominio.mensaje}")
    informar(error_dominio.sugerencia)
    if error_dominio.ruta is not None:
        informar(f"ruta: {error_dominio.ruta}")


def renderizar_exportacion_engram(estado: EstadoIntegracion) -> None:
    """Muestra el resultado opcional de Engram sin alterar la operacion primaria.

    Args:
        estado: Resultado tipado producido por la capa de integraciones.
    """
    if estado.estado in {
        ValorEstadoIntegracion.COMPLETO,
        ValorEstadoIntegracion.DEGRADADO,
    }:
        exito("exportado a Engram (memoria persistente N2).")
    elif estado.estado is ValorEstadoIntegracion.NO_DISPONIBLE:
        advertir("Engram no está instalado; se omite el export a memoria persistente.")
    elif estado.motivo == "proceso_salida_no_cero":
        advertir("Engram rechazó el export; el paquete publicado sigue siendo válido.")
    else:
        advertir("no se pudo exportar a Engram; el paquete publicado sigue siendo válido.")


def resultado_cierre(resultado: ResultadoCierre) -> None:
    """Render an already-calculated closure result without changing its policy.

    Args:
        resultado: Immutable closure result returned by the shared operation.
    """
    raiz = Path.cwd()
    if resultado.ejecucion.resultados:
        for puerta in resultado.ejecucion.resultados:
            if puerta.estado is ValorResultadoPuerta.APROBADO:
                mostrar = exito
            elif puerta.estado is ValorResultadoPuerta.OMITIDO:
                mostrar = advertir
            else:
                mostrar = error
            mostrar(f"puerta {puerta.nombre}: {puerta.estado.value}")
    else:
        advertir(f"puertas: {resultado.ejecucion.estado.value}")

    if resultado.ruta_paquete is not None:
        ruta_paquete = resultado.ruta_paquete.relative_to(raiz)
        exito(f"evidencia: {ruta_paquete}  (estado: {resultado.estado.value})")
        informar(f"metadatos: {ruta_paquete / 'metadatos.json'}")
    if resultado.ruta_traspaso is not None:
        exito(f"traspaso: {resultado.ruta_traspaso.relative_to(raiz)}")

    if resultado.aprobado:
        exito(f"cierre completado: {resultado.id_tarea} ({resultado.estado.value})")
    else:
        error(f"cierre bloqueado: {', '.join(resultado.bloqueos) or 'sin causa declarada'}")
