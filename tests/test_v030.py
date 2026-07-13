"""v0.30 (R4): ciclo de vida — upgrade no-destructivo, marcador de versión, botón init en Resumen.

- tramalia upgrade agrega lo nuevo que falte SIN pisar lo existente + registra versión.
- .tramalia/version marca con qué versión se generó/actualizó el repo.
- el botón de init vive en la pestaña Resumen (donde dice "sin inicializar").
"""

import asyncio
import types

import pytest

from tramalia import __version__
from tramalia.cli import comandos
from tramalia.core import configuracion
from tramalia.core.detect import enabled_features
from tramalia.core.proyecto import inspeccionar_estado_proyecto
from tramalia.core.scaffold import scaffold


def _init(tmp_path):
    scaffold(
        tmp_path,
        {
            "project_name": "demo",
            "stacks": ["python"],
            "features": enabled_features(["python"]),
            "primary_agent": "codex",
            "reviewer_agent": "claude",
        },
    )
    return tmp_path


# ---------------------------------------------------------------- marcador de versión
def test_version_marker_round_trip(tmp_path):
    assert configuracion.version_andamiaje(tmp_path) is None
    configuracion.fijar_version_andamiaje(tmp_path, "0.30.0")
    assert configuracion.version_andamiaje(tmp_path) == "0.30.0"


# ---------------------------------------------------------------- upgrade
def test_upgrade_sin_inicializar_falla(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert comandos.comando_actualizar_proyecto(types.SimpleNamespace()) == 1


def test_upgrade_recrea_lo_que_falta_y_no_pisa(tmp_path, monkeypatch):
    _init(tmp_path)
    agentes = tmp_path / "AGENTS.md"
    agentes_antes = agentes.read_bytes()
    # el usuario editó un archivo y borró otro
    arq = tmp_path / "docs" / "ai" / "01-arquitectura.md"
    arq.write_text("MI CONTENIDO EDITADO", encoding="utf-8")
    borrado = tmp_path / "docs" / "ai" / "04-reglas-seguridad.md"
    borrado.unlink()
    assert not borrado.exists()

    monkeypatch.chdir(tmp_path)
    assert comandos.comando_actualizar_proyecto(types.SimpleNamespace()) == 0

    assert borrado.exists()  # lo que faltaba: recreado
    assert agentes.read_bytes() == agentes_antes  # faltar versión no adopta AGENTS.md
    assert arq.read_text(encoding="utf-8") == "MI CONTENIDO EDITADO"  # lo editado: intacto
    assert configuracion.version_andamiaje(tmp_path) == __version__  # versión registrada


def test_upgrade_registra_gitignore(tmp_path, monkeypatch):
    # repo inicializado a mano SIN el bloque de .gitignore (simula repo viejo)
    _init(tmp_path)
    (tmp_path / ".gitignore").unlink(missing_ok=True)
    monkeypatch.chdir(tmp_path)
    comandos.comando_actualizar_proyecto(types.SimpleNamespace())
    txt = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".tramalia/habilidades/*/" in txt  # upgrade dejó el bloque


def test_upgrade_cli_migra_heredado_sin_pisar_contenido(tmp_path, monkeypatch):
    _init(tmp_path)
    agentes = tmp_path / "AGENTS.md"
    agentes.write_text(
        "# Reglas del equipo\n\nNo tocar legacy/.\nCierre: tramalia close.\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(comandos, "_sugerir_propagacion", lambda raiz: None)

    assert comandos.comando_actualizar_proyecto(types.SimpleNamespace()) == 0

    texto = agentes.read_text(encoding="utf-8")
    inicio = "<!-- tramalia:gobierno inicio -->"
    fin = "<!-- tramalia:gobierno fin -->"
    assert "No tocar legacy/." in texto
    assert texto.count(inicio) == texto.count(fin) == 1
    assert inspeccionar_estado_proyecto(tmp_path).listo


def test_sugerir_propagacion_no_revienta(tmp_path):
    comandos._sugerir_propagacion(tmp_path)  # solo imprime; nunca debe lanzar


# ---------------------------------------------------------------- TUI: botón init en Resumen
@pytest.mark.interfaz
@pytest.mark.opcional
def test_boton_inicializar_en_resumen(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    from textual.widgets import Button

    monkeypatch.chdir(tmp_path)  # repo VACÍO: sin inicializar
    from tramalia.interfaz_terminal import construir_aplicacion

    app = construir_aplicacion()

    async def run():
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.workers.wait_for_complete()
            btn = app.query_one("#btn-init-resumen", Button)
            assert btn.display is True  # visible cuando falta init
            await pilot.click(btn)
            await app.workers.wait_for_complete()
            await pilot.pause()
            await app.workers.wait_for_complete()
            assert inspeccionar_estado_proyecto(tmp_path).listo
            assert configuracion.version_andamiaje(tmp_path) == __version__
            assert app.query_one("#btn-init-resumen", Button).display is False  # se oculta

    asyncio.run(run())


@pytest.mark.interfaz
@pytest.mark.opcional
def test_interfaz_trata_proyecto_parcial_como_no_inicializado(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    from textual.widgets import Button

    from tramalia.interfaz_terminal import construir_aplicacion

    (tmp_path / ".tramalia").mkdir()
    monkeypatch.chdir(tmp_path)
    aplicacion = construir_aplicacion()

    async def verificar():
        async with aplicacion.run_test() as piloto:
            await piloto.pause()
            await aplicacion.workers.wait_for_complete()
            assert aplicacion.query_one("#btn-init-resumen", Button).display is True
            assert aplicacion.query_one("#cierre-form").display is False
            assert list((tmp_path / ".tramalia").iterdir()) == []

    asyncio.run(verificar())


@pytest.mark.interfaz
@pytest.mark.opcional
def test_interfaz_cierre_revalida_raiz_del_servicio_en_worker(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    from textual.widgets import Button, Input, TabbedContent

    from tramalia.core.tablero import ServicioTablero
    from tramalia.interfaz_terminal import construir_aplicacion

    raiz_original = tmp_path / "original"
    raiz_alterna = tmp_path / "alterna"
    raiz_original.mkdir()
    raiz_alterna.mkdir()
    _init(raiz_original)
    _init(raiz_alterna)
    configuracion.fijar_version_andamiaje(raiz_original, __version__)
    configuracion.fijar_version_andamiaje(raiz_alterna, __version__)

    monkeypatch.chdir(raiz_original)
    aplicacion = construir_aplicacion(ServicioTablero(raiz_original))

    async def verificar():
        async with aplicacion.run_test() as piloto:
            await piloto.pause()
            await aplicacion.workers.wait_for_complete()
            aplicacion.query_one(TabbedContent).active = "cierre"
            aplicacion.query_one("#in-task", Input).value = "TASK-1"
            (raiz_original / "AGENTS.md").unlink()
            monkeypatch.chdir(raiz_alterna)
            boton = aplicacion.query_one("#cerrar", Button)
            boton.scroll_visible(animate=False, force=True, immediate=True)
            boton.focus()
            await piloto.pause()
            await piloto.press("enter")
            await aplicacion.workers.wait_for_complete()

            assert not (raiz_original / ".tramalia" / "evidencia").exists()
            assert not (raiz_alterna / ".tramalia" / "evidencia").exists()

    asyncio.run(verificar())


@pytest.mark.interfaz
@pytest.mark.opcional
def test_interfaz_cierre_positivo_delega_y_renderiza_resultado_tipado(tmp_path, monkeypatch):
    pytest.importorskip("textual")
    from textual.widgets import Button, Input, RichLog, TabbedContent

    from tramalia.core.modelos import (
        EjecucionPuertas,
        ResultadoCierre,
        ValorEstadoCierre,
        ValorEstadoPuertas,
    )
    from tramalia.core.tablero import ServicioTablero
    from tramalia.interfaz_terminal import construir_aplicacion

    llamadas = []
    resultado = ResultadoCierre(
        estado=ValorEstadoCierre.APROBADO,
        id_tarea="TASK-TUI",
        id_paquete="paquete-tui",
        ruta_paquete=tmp_path / ".tramalia" / "evidencia" / "paquete-tui",
        ruta_traspaso=tmp_path / ".tramalia" / "evidencia" / "paquete-tui" / "traspaso.md",
        ejecucion=EjecucionPuertas(
            estado=ValorEstadoPuertas.APROBADO,
            ejecutadas=("test",),
        ),
    )

    def cerrar(raiz, id_tarea, **opciones):
        llamadas.append((raiz, id_tarea, opciones))
        return resultado

    _init(tmp_path)
    configuracion.fijar_version_andamiaje(tmp_path, __version__)
    monkeypatch.chdir(tmp_path)
    aplicacion = construir_aplicacion(ServicioTablero(tmp_path, operacion_cerrar=cerrar))

    async def verificar():
        async with aplicacion.run_test() as piloto:
            # RichLog difiere el render mientras su pestana no tiene tamano.
            await aplicacion.workers.wait_for_complete()
            aplicacion.query_one(TabbedContent).active = "cierre"
            await piloto.pause()
            aplicacion.query_one("#in-task", Input).value = "TASK-TUI"
            aplicacion.query_one("#in-agent", Input).value = "codex"
            aplicacion.query_one("#in-reviewer", Input).value = "ana"
            aplicacion.query_one("#in-model", Input).value = "gpt-5"
            boton = aplicacion.query_one("#cerrar", Button)
            boton.scroll_visible(animate=False, force=True, immediate=True)
            boton.focus()
            await piloto.pause()
            await piloto.press("enter")
            await aplicacion.workers.wait_for_complete()

            assert llamadas == [
                (
                    tmp_path,
                    "TASK-TUI",
                    {
                        "agente": "codex",
                        "revisor": "ana",
                        "modelo": "gpt-5",
                        "excepciones": (),
                    },
                )
            ]
            salida = aplicacion.query_one("#salida", RichLog)
            texto = "\n".join(linea.text for linea in salida.lines)
            assert "aprobado" in texto
            assert "paquete-tui" in texto

    asyncio.run(verificar())
