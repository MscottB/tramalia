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
