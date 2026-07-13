from tramalia.core import integraciones, procesos
from tramalia.core.integraciones import (
    AdaptadorCapacidad,
    ejecutar_integracion,
)
from tramalia.core.procesos import ResultadoProceso, ejecutar


def _resultado(codigo: int) -> ResultadoProceso:
    return ResultadoProceso(
        comando=("adaptador",),
        codigo_salida=codigo,
        salida="salida",
        error="error" if codigo else "",
        agotado_tiempo=codigo == 124,
        cancelado=codigo == 130,
    )


def test_proceso_con_salida_no_cero_no_se_convierte_en_exito() -> None:
    resultado = ejecutar(
        ["python", "-c", "import sys; print('fallo'); sys.exit(7)"],
        limite_segundos=5,
    )
    assert resultado.codigo_salida == 7
    assert resultado.salida.strip() == "fallo"
    assert not resultado.exitoso


def test_proceso_agotado_conserva_estado_124() -> None:
    resultado = ejecutar(
        ["python", "-c", "import time; time.sleep(2)"],
        limite_segundos=0.05,
    )
    assert resultado.codigo_salida == 124
    assert resultado.agotado_tiempo
    assert not resultado.cancelado


def test_alternativa_exitosa_es_degradada() -> None:
    llamados: list[str] = []
    adaptadores = (
        AdaptadorCapacidad("preferido", frozenset({"memoria"}), lambda: False),
        AdaptadorCapacidad("local", frozenset({"memoria"}), lambda: True),
    )

    intento = ejecutar_integracion(
        capacidad="memoria",
        solicitado="preferido",
        adaptadores=adaptadores,
        operacion=lambda nombre: llamados.append(nombre) or _resultado(0),
        impacto_degradado="sin sincronización remota",
        remediacion="instala preferido",
    )

    assert llamados == ["local"]
    assert intento.estado.estado == "degradado"
    assert intento.estado.solicitado == "preferido"
    assert intento.estado.utilizado == "local"


def test_intento_fallido_no_se_oculta_con_otra_alternativa() -> None:
    llamados: list[str] = []
    adaptadores = (
        AdaptadorCapacidad("preferido", frozenset({"memoria"}), lambda: True),
        AdaptadorCapacidad("local", frozenset({"memoria"}), lambda: True),
    )

    intento = ejecutar_integracion(
        capacidad="memoria",
        solicitado="preferido",
        adaptadores=adaptadores,
        operacion=lambda nombre: llamados.append(nombre) or _resultado(9),
        impacto_degradado="sin sincronización remota",
        remediacion="revisa el adaptador preferido",
    )

    assert llamados == ["preferido"]
    assert intento.estado.estado == "fallido"
    assert intento.estado.motivo == "proceso_salida_no_cero"
    assert intento.proceso is not None and intento.proceso.codigo_salida == 9


def test_capacidad_opcional_sin_adaptador_es_no_disponible() -> None:
    intento = ejecutar_integracion(
        capacidad="memoria",
        solicitado=None,
        adaptadores=(),
        operacion=lambda _nombre: _resultado(0),
        impacto_degradado="sin memoria persistente",
        remediacion="instala un adaptador de memoria",
    )
    assert intento.estado.estado == "no_disponible"
    assert intento.estado.motivo == "capacidad_opcional_no_solicitada"
    assert intento.proceso is None


def test_exportacion_engram_exitosa_conserva_el_proceso_tipado(monkeypatch) -> None:
    comandos: list[tuple[str, ...]] = []
    monkeypatch.setattr(procesos, "encontrar", lambda _comando: "engram")
    monkeypatch.setattr(
        procesos,
        "ejecutar",
        lambda comando: comandos.append(tuple(comando)) or _resultado(0),
    )

    intento = integraciones.exportar_memoria_engram(
        "evidence TASK-1",
        "Paquete formal de TASK-1: paquete-1.",
    )

    assert comandos == [
        (
            "engram",
            "save",
            "evidence TASK-1",
            "Paquete formal de TASK-1: paquete-1.",
        )
    ]
    assert intento.estado.estado == "completo"
    assert intento.estado.utilizado == "engram"
    assert intento.proceso is not None and intento.proceso.exitoso


def test_exportacion_engram_ausente_no_inicia_un_proceso(monkeypatch) -> None:
    monkeypatch.setattr(procesos, "encontrar", lambda _comando: None)

    def ejecutar_prohibido(_comando: object) -> ResultadoProceso:
        raise AssertionError("no se debe ejecutar Engram cuando esta ausente")

    monkeypatch.setattr(procesos, "ejecutar", ejecutar_prohibido)

    intento = integraciones.exportar_memoria_engram("close TASK-2", "cierre durable")

    assert intento.estado.estado == "no_disponible"
    assert intento.estado.motivo == "adaptador_no_instalado"
    assert intento.proceso is None


def test_exportacion_engram_fallida_no_se_convierte_en_exito(monkeypatch) -> None:
    monkeypatch.setattr(procesos, "encontrar", lambda _comando: "engram")
    monkeypatch.setattr(procesos, "ejecutar", lambda _comando: _resultado(9))

    intento = integraciones.exportar_memoria_engram("handoff TASK-3", "traspaso durable")

    assert intento.estado.estado == "fallido"
    assert intento.estado.motivo == "proceso_salida_no_cero"
    assert intento.proceso is not None and intento.proceso.codigo_salida == 9


def test_exportacion_engram_atrapa_excepcion_del_adaptador(monkeypatch) -> None:
    monkeypatch.setattr(procesos, "encontrar", lambda _comando: "engram")

    def fallar(_comando: object) -> ResultadoProceso:
        raise OSError("servicio de memoria no disponible")

    monkeypatch.setattr(procesos, "ejecutar", fallar)

    intento = integraciones.exportar_memoria_engram("close TASK-4", "cierre durable")

    assert intento.estado.estado == "fallido"
    assert intento.estado.motivo == "excepcion_inesperada"
    assert intento.proceso is None
