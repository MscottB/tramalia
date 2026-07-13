from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from tramalia.core.errores import (
    ErrorConfiguracionMetricas,
    ErrorConfiguracionPuertas,
    ErrorExcepcionInvalida,
    ErrorIdentificadorInseguro,
    ErrorPersistenciaEvidencia,
    ErrorProyectoNoGobernado,
    ErrorTramalia,
)
from tramalia.core.modelos import (
    EjecucionPuertas,
    EntradaBitacora,
    EstadoGit,
    EstadoIntegracion,
    EstadoProyecto,
    ExcepcionFallo,
    MetadatosPaqueteEvidencia,
    PaqueteEvidencia,
    PuertaCalidad,
    ResultadoCierre,
    ResultadoPuerta,
    ValorEstadoBitacora,
    ValorEstadoCierre,
    ValorEstadoIntegracion,
    ValorEstadoProyecto,
    ValorEstadoPuertas,
    ValorResultadoPuerta,
)


def test_error_sanea_secretos_recursivos() -> None:
    class ErrorPrueba(ErrorTramalia):
        codigo = "fallo"

    error = ErrorPrueba(
        mensaje="fallo humano",
        sugerencia="reintenta",
        ruta=Path("mise.toml"),
        detalles={
            "token": "abc",
            "git": {"branch": "main", "password": "x"},
            "intentos": [
                {"Authorization": "Bearer x", "resultado": "fallido"},
                ({"api_key": "123"},),
            ],
        },
    )

    assert error.como_dict() == {
        "codigo": "fallo",
        "mensaje": "fallo humano",
        "sugerencia": "reintenta",
        "ruta": "mise.toml",
        "detalles": {
            "token": "[REDACTADO]",
            "git": {"branch": "main", "password": "[REDACTADO]"},
            "intentos": [
                {"Authorization": "[REDACTADO]", "resultado": "fallido"},
                [{"api_key": "[REDACTADO]"}],
            ],
        },
    }


@pytest.mark.parametrize(
    ("tipo_error", "codigo"),
    [
        (ErrorProyectoNoGobernado, "proyecto_no_gobernado"),
        (ErrorConfiguracionPuertas, "configuracion_puertas_invalida"),
        (ErrorConfiguracionMetricas, "configuracion_metricas_invalida"),
        (ErrorIdentificadorInseguro, "id_tarea_inseguro"),
        (ErrorExcepcionInvalida, "excepcion_invalida"),
        (ErrorPersistenciaEvidencia, "persistencia_evidencia_fallida"),
    ],
)
def test_errores_publican_codigos_estables(tipo_error: type[ErrorTramalia], codigo: str) -> None:
    error = tipo_error("fallo", "corrige la entrada")

    assert error.como_dict() == {
        "codigo": codigo,
        "mensaje": "fallo",
        "sugerencia": "corrige la entrada",
        "ruta": None,
        "detalles": {},
    }
    assert str(error) == "fallo"


def test_excepcion_exige_todos_los_datos_y_remediacion() -> None:
    with pytest.raises(ErrorExcepcionInvalida) as capturada:
        ExcepcionFallo("", "riesgo", "test", "ISSUE-1", "ana")

    assert capturada.value.codigo == "excepcion_invalida"
    assert capturada.value.detalles == {"campos": ["razon", "expira_en_o_condicion_remediacion"]}

    excepcion = ExcepcionFallo(
        razon="runner en mantenimiento",
        riesgo_aceptado="la regresion puede detectarse tarde",
        control_afectado="ejecutor",
        referencia="ISSUE-123",
        revisor="ana",
        expira_en=datetime(2026, 7, 13, tzinfo=UTC),
    )
    assert excepcion.vigente(datetime(2026, 7, 12, tzinfo=UTC)) is True


def test_excepcion_rechaza_expiracion_sin_zona_horaria() -> None:
    with pytest.raises(ErrorExcepcionInvalida) as capturada:
        ExcepcionFallo(
            razon="runner en mantenimiento",
            riesgo_aceptado="demora",
            control_afectado="ejecutor",
            referencia="ISSUE-123",
            revisor="ana",
            expira_en=datetime(2026, 7, 13),
        )

    assert "expira_en_con_zona_horaria" in capturada.value.detalles["campos"]


def test_excepcion_compara_expiracion_en_zonas_horarias() -> None:
    expira_en = datetime(2026, 7, 13, 12, tzinfo=UTC)
    excepcion = ExcepcionFallo(
        razon="runner en mantenimiento",
        riesgo_aceptado="demora",
        control_afectado="ejecutor",
        referencia="ISSUE-123",
        revisor="ana",
        expira_en=expira_en,
    )
    zona_chile = timezone(timedelta(hours=-4))

    assert excepcion.vigente(datetime(2026, 7, 13, 8, tzinfo=zona_chile)) is True
    assert excepcion.vigente(expira_en + timedelta(microseconds=1)) is False


@pytest.mark.parametrize(
    ("tipo_enum", "valor", "miembro"),
    [
        (ValorEstadoProyecto, "listo", ValorEstadoProyecto.LISTO),
        (ValorEstadoPuertas, "aprobado", ValorEstadoPuertas.APROBADO),
        (ValorResultadoPuerta, "omitido", ValorResultadoPuerta.OMITIDO),
        (ValorEstadoCierre, "bloqueado", ValorEstadoCierre.BLOQUEADO),
        (ValorEstadoIntegracion, "degradado", ValorEstadoIntegracion.DEGRADADO),
        (ValorEstadoBitacora, "invalida", ValorEstadoBitacora.INVALIDA),
    ],
)
def test_enums_coercionan_valores_de_texto(tipo_enum: type, valor: str, miembro: object) -> None:
    assert tipo_enum(valor) is miembro
    assert str(miembro) == valor


def test_estado_integracion_coerciona_y_exige_fallback_efectivo() -> None:
    with pytest.raises(ValueError, match="utilizado"):
        EstadoIntegracion(
            "degradado", "memoria", "engram", None, "fallback", "sin memoria", "instalar"
        )

    estado = EstadoIntegracion(
        "degradado", "memoria", "engram", "archivo", "fallback", "local", "instalar"
    )

    assert estado.estado is ValorEstadoIntegracion.DEGRADADO
    assert estado.exitoso is True


@pytest.mark.parametrize(
    ("estado", "esperado"),
    [
        (ValorEstadoIntegracion.COMPLETO, True),
        (ValorEstadoIntegracion.DEGRADADO, True),
        (ValorEstadoIntegracion.NO_DISPONIBLE, False),
        (ValorEstadoIntegracion.FALLIDO, False),
    ],
)
def test_estado_integracion_define_exito(estado: ValorEstadoIntegracion, esperado: bool) -> None:
    utilizado = "archivo" if estado is ValorEstadoIntegracion.DEGRADADO else None
    integracion = EstadoIntegracion(
        estado, "memoria", "engram", utilizado, "motivo", "impacto", "remediacion"
    )

    assert integracion.exitoso is esperado


@pytest.mark.parametrize(
    ("estado", "esperado"),
    [
        (ValorEstadoCierre.APROBADO, True),
        (ValorEstadoCierre.APROBADO_CON_EXCEPCIONES, True),
        (ValorEstadoCierre.BLOQUEADO, False),
    ],
)
def test_resultado_cierre_define_aprobacion(estado: ValorEstadoCierre, esperado: bool) -> None:
    ejecucion = EjecucionPuertas(ValorEstadoPuertas.APROBADO)
    resultado = ResultadoCierre(estado, "TASK-1", None, None, None, ejecucion)

    assert resultado.aprobado is esperado


def test_modelos_son_inmutables_y_sin_diccionario_mutable() -> None:
    estado = EstadoProyecto(ValorEstadoProyecto.LISTO, Path("."))

    assert estado.listo is True
    assert not hasattr(estado, "__dict__")
    with pytest.raises(FrozenInstanceError):
        estado.estado = ValorEstadoProyecto.AUSENTE


def test_modelos_publican_los_campos_contractuales() -> None:
    contratos = {
        EstadoProyecto: ("estado", "raiz", "problemas", "comando_reparacion"),
        PuertaCalidad: ("nombre", "comando", "archivo_salida"),
        ResultadoPuerta: (
            "nombre",
            "comando",
            "estado",
            "codigo_salida",
            "salida",
            "inicio_utc",
            "fin_utc",
            "duracion_segundos",
            "hash_salida",
            "archivo_salida",
        ),
        EjecucionPuertas: (
            "estado",
            "descubiertas",
            "ejecutadas",
            "omitidas",
            "fallidas",
            "resultados",
            "errores_validacion",
        ),
        ExcepcionFallo: (
            "razon",
            "riesgo_aceptado",
            "control_afectado",
            "referencia",
            "revisor",
            "expira_en",
            "condicion_remediacion",
        ),
        EstadoGit: (
            "commit",
            "rama",
            "limpio",
            "base_comparacion",
            "rastreados",
            "preparados",
            "no_rastreados",
            "renombrados",
            "eliminados",
        ),
        MetadatosPaqueteEvidencia: (
            "version_esquema",
            "id_paquete",
            "id_tarea",
            "operacion",
            "inicio_utc",
            "fin_utc",
            "version_tramalia",
            "version_python",
            "sistema_operativo",
            "cadena_herramientas",
            "git",
            "ejecucion",
            "estado_cierre",
            "agente",
            "modelo",
            "metricas",
            "umbrales",
            "errores_validacion",
            "excepciones",
            "vinculo_traspaso",
        ),
        PaqueteEvidencia: ("id_paquete", "ruta", "metadatos"),
        ResultadoCierre: (
            "estado",
            "id_tarea",
            "id_paquete",
            "ruta_paquete",
            "ruta_traspaso",
            "ejecucion",
            "excepciones",
            "bloqueos",
        ),
        EntradaBitacora: (
            "id_paquete",
            "ruta",
            "estado",
            "id_tarea",
            "resultado",
            "agente",
            "modelo",
            "cerrado_utc",
            "error",
        ),
        EstadoIntegracion: (
            "estado",
            "capacidad",
            "solicitado",
            "utilizado",
            "motivo",
            "impacto",
            "remediacion",
        ),
    }

    for tipo_modelo, nombres_esperados in contratos.items():
        assert tuple(campo.name for campo in fields(tipo_modelo)) == nombres_esperados
