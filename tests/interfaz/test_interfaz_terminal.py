import asyncio
from pathlib import Path

import pytest

pytest.importorskip("textual")

from textual.widgets import Input, Switch, TabbedContent

from tramalia.core.modelos import (
    EjecucionPuertas,
    EntradaBitacora,
    EstadoIntegracion,
    EstadoProyecto,
    ExcepcionFallo,
    ResultadoCierre,
    ValorEstadoBitacora,
    ValorEstadoCierre,
    ValorEstadoIntegracion,
    ValorEstadoProyecto,
    ValorEstadoPuertas,
)
from tramalia.core.tablero import InstantaneaTablero
from tramalia.interfaz_terminal import construir_aplicacion


def resultado_cierre_falso(id_tarea: str) -> ResultadoCierre:
    return ResultadoCierre(
        estado=ValorEstadoCierre.BLOQUEADO,
        id_tarea=id_tarea,
        id_paquete=None,
        ruta_paquete=None,
        ruta_traspaso=None,
        ejecucion=EjecucionPuertas(ValorEstadoPuertas.SIN_CONFIGURAR),
        excepciones=(),
        bloqueos=("puertas_sin_configurar",),
    )


class ServicioFalso:
    def __init__(self, instantanea: InstantaneaTablero) -> None:
        self.instantanea = instantanea
        self.llamadas_cierre: list[tuple[str, tuple[ExcepcionFallo, ...]]] = []

    def obtener_instantanea(self) -> InstantaneaTablero:
        return self.instantanea

    def cerrar(
        self,
        id_tarea: str,
        *,
        agente: str = "",
        revisor: str = "",
        modelo: str = "",
        excepciones: tuple[ExcepcionFallo, ...] = (),
    ) -> ResultadoCierre:
        self.llamadas_cierre.append((id_tarea, excepciones))
        return resultado_cierre_falso(id_tarea)


def _instantanea(
    tmp_path: Path,
    *,
    motivo: str = "proceso_agotado",
) -> InstantaneaTablero:
    entrada = EntradaBitacora(
        id_paquete="paquete-roto",
        ruta=tmp_path / "paquete-roto",
        estado=ValorEstadoBitacora.INVALIDA,
        id_tarea=None,
        resultado=None,
        agente=None,
        modelo=None,
        cerrado_utc=None,
        error="archivo metadatos.json corrupto",
    )
    integracion = EstadoIntegracion(
        ValorEstadoIntegracion.FALLIDO,
        "instalacion",
        "mise",
        "mise",
        motivo,
        "herramienta no instalada",
        "reintenta o instala manualmente",
    )
    return InstantaneaTablero(
        tmp_path,
        EstadoProyecto(ValorEstadoProyecto.LISTO, tmp_path),
        ("python",),
        ("test",),
        (),
        (),
        (entrada,),
        (integracion,),
        "TASK-1",
        "codex",
        "claude",
        "serena",
    )


def _rellenar(app, selector: str, valor: str) -> None:
    app.query_one(selector, Input).value = valor


def _activar_cierre(app) -> None:
    app.query_one(TabbedContent).active = "cierre"


async def _pulsar_cerrar(app, piloto) -> None:
    boton = app.query_one("#cerrar")
    boton.focus(scroll_visible=True)
    await piloto.pause()
    await piloto.press("enter")
    await piloto.pause()


async def _activar_excepcion(app, piloto) -> None:
    interruptor = app.query_one("#permitir-excepcion", Switch)
    interruptor.scroll_visible(
        animate=False,
        force=True,
        immediate=True,
    )
    await piloto.pause()
    assert await piloto.click(interruptor)
    await piloto.pause()
    assert interruptor.value is True


@pytest.mark.interfaz
@pytest.mark.opcional
def test_interfaz_muestra_metadatos_invalidos_y_tiempo_agotado(
    tmp_path: Path,
) -> None:
    async def escenario() -> None:
        app = construir_aplicacion(ServicioFalso(_instantanea(tmp_path)))
        async with app.run_test() as piloto:
            await piloto.pause()
            await app.workers.wait_for_complete()
            assert "archivo metadatos.json corrupto" in app.query_one("#detalle-log").render().plain
            assert "tiempo agotado" in app.query_one("#estado-integraciones").render().plain.lower()

    asyncio.run(escenario())


@pytest.mark.interfaz
@pytest.mark.opcional
def test_interfaz_distingue_cancelacion_de_degradacion(tmp_path: Path) -> None:
    cancelada = _instantanea(tmp_path, motivo="proceso_cancelado")
    degradada = EstadoIntegracion(
        ValorEstadoIntegracion.DEGRADADO,
        "memoria",
        "engram",
        "archivo_local",
        "alternativa_completada",
        "sin memoria compartida",
        "instala engram",
    )
    cancelada = InstantaneaTablero(
        cancelada.raiz,
        cancelada.proyecto,
        cancelada.tecnologias,
        cancelada.puertas,
        cancelada.herramientas,
        cancelada.habilidades,
        cancelada.bitacora,
        (cancelada.integraciones[0], degradada),
        cancelada.id_tarea,
        cancelada.agente,
        cancelada.revisor,
        cancelada.proveedor_contexto,
    )

    async def escenario() -> None:
        app = construir_aplicacion(ServicioFalso(cancelada))
        async with app.run_test() as piloto:
            await piloto.pause()
            await app.workers.wait_for_complete()
            texto = app.query_one("#estado-integraciones").render().plain.lower()
            assert "cancelada" in texto
            assert "degradada" in texto
            assert "sin memoria compartida" in texto

    asyncio.run(escenario())


@pytest.mark.interfaz
@pytest.mark.opcional
def test_interfaz_formulario_excepcion_es_tipado_y_cierre_seguro(
    tmp_path: Path,
) -> None:
    async def escenario() -> None:
        servicio = ServicioFalso(_instantanea(tmp_path))
        app = construir_aplicacion(servicio)
        async with app.run_test() as piloto:
            await piloto.pause()
            await app.workers.wait_for_complete()
            _activar_cierre(app)
            await piloto.pause()
            await _activar_excepcion(app, piloto)
            _rellenar(app, "#razon-excepcion", "falso positivo")
            await _pulsar_cerrar(app, piloto)
            await piloto.pause()
            assert servicio.llamadas_cierre == []
            error = app.query_one("#error-cierre").render().plain.lower()
            for texto in ("riesgo", "control", "referencia", "revisor", "remediacion"):
                assert texto in error

            _rellenar(app, "#riesgo-aceptado", "riesgo acotado")
            _rellenar(app, "#control-afectado", "pruebas")
            _rellenar(app, "#referencia-excepcion", "ISSUE-7")
            _rellenar(app, "#revisor-excepcion", "ana")
            _rellenar(app, "#condicion-remediacion", "corregir antes del release")
            await _pulsar_cerrar(app, piloto)
            await app.workers.wait_for_complete()

        assert len(servicio.llamadas_cierre) == 1
        id_tarea, excepciones = servicio.llamadas_cierre[0]
        assert id_tarea == "TASK-1"
        assert len(excepciones) == 1
        excepcion = excepciones[0]
        assert excepcion.razon == "falso positivo"
        assert excepcion.riesgo_aceptado == "riesgo acotado"
        assert excepcion.control_afectado == "pruebas"
        assert excepcion.referencia == "ISSUE-7"
        assert excepcion.revisor == "ana"
        assert excepcion.condicion_remediacion == "corregir antes del release"

    asyncio.run(escenario())


@pytest.mark.interfaz
@pytest.mark.opcional
def test_interfaz_fecha_excepcion_invalida_no_inicia_cierre(tmp_path: Path) -> None:
    async def escenario() -> None:
        servicio = ServicioFalso(_instantanea(tmp_path))
        app = construir_aplicacion(servicio)
        async with app.run_test() as piloto:
            await piloto.pause()
            await app.workers.wait_for_complete()
            _activar_cierre(app)
            await piloto.pause()
            await _activar_excepcion(app, piloto)
            _rellenar(app, "#razon-excepcion", "falso positivo")
            _rellenar(app, "#riesgo-aceptado", "riesgo acotado")
            _rellenar(app, "#control-afectado", "pruebas")
            _rellenar(app, "#referencia-excepcion", "ISSUE-7")
            _rellenar(app, "#revisor-excepcion", "ana")
            _rellenar(app, "#condicion-remediacion", "corregir antes del release")
            _rellenar(app, "#expira-en", "fecha-no-iso")
            await _pulsar_cerrar(app, piloto)
            await piloto.pause()
            assert servicio.llamadas_cierre == []
            assert "iso 8601" in app.query_one("#error-cierre").render().plain.lower()

    asyncio.run(escenario())
