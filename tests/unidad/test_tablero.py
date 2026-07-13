from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from tramalia.core.modelos import (
    EjecucionPuertas,
    EstadoProyecto,
    ResultadoCierre,
    ValorEstadoCierre,
    ValorEstadoProyecto,
    ValorEstadoPuertas,
)
from tramalia.core.tablero import InstantaneaTablero, ServicioTablero


def test_instantanea_es_inmutable(tmp_path: Path) -> None:
    instantanea = InstantaneaTablero.vacia(
        tmp_path,
        EstadoProyecto(ValorEstadoProyecto.AUSENTE, tmp_path),
    )
    with pytest.raises(FrozenInstanceError):
        instantanea.id_tarea = "TASK-1"  # type: ignore[misc]


def test_servicio_cerrar_delega_sin_recalcular(tmp_path: Path) -> None:
    esperado = ResultadoCierre(
        estado=ValorEstadoCierre.BLOQUEADO,
        id_tarea="TASK-1",
        id_paquete=None,
        ruta_paquete=None,
        ruta_traspaso=None,
        ejecucion=EjecucionPuertas(estado=ValorEstadoPuertas.SIN_CONFIGURAR),
        excepciones=(),
        bloqueos=("sin_configurar",),
    )
    llamadas: list[tuple[Path, str]] = []
    servicio = ServicioTablero(
        tmp_path,
        operacion_cerrar=lambda raiz, id_tarea, **_opciones: (
            llamadas.append((raiz, id_tarea)) or esperado
        ),
    )
    assert servicio.cerrar("TASK-1") is esperado
    assert llamadas == [(tmp_path, "TASK-1")]


def test_servicio_reutiliza_diagnostico_y_conserva_estado_uv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tramalia.core import tablero
    from tramalia.core.doctor import Report

    monkeypatch.setattr(
        tablero.doctor,
        "diagnose",
        lambda _raiz: Report(["python"], (), [], uv_bin_on_path=False),
    )
    monkeypatch.setattr(
        tablero,
        "detect_stack",
        lambda _raiz: pytest.fail("no debe repetir la deteccion del diagnostico"),
    )
    monkeypatch.setattr(tablero, "cargar_puertas", lambda _raiz: ())
    monkeypatch.setattr(tablero, "consultar_habilidades", lambda _raiz: ())
    monkeypatch.setattr(tablero, "leer_bitacora", lambda _raiz: [])
    monkeypatch.setattr(tablero, "agentes_predeterminados", lambda _raiz: ("", ""))
    monkeypatch.setattr(tablero, "id_tarea_actual", lambda _raiz: None)
    monkeypatch.setattr(tablero, "proveedor_contexto", lambda _raiz: "serena")

    instantanea = ServicioTablero(tmp_path).obtener_instantanea()

    assert instantanea.tecnologias == ("python",)
    assert instantanea.uv_en_ruta is False
