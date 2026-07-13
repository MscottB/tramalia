import json
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, date, datetime, time, timedelta, timezone, tzinfo
from enum import Enum, StrEnum
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


class PrioridadPrueba(Enum):
    ALTA = 2


class ZonaSinDesfase(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> str:
        return "sin-desfase"


CAMPOS_MODELOS: dict[type[object], tuple[str, ...]] = {
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


def test_error_como_dict_es_json_serializable_y_determinista() -> None:
    class ErrorPrueba(ErrorTramalia):
        codigo = "fallo_serializable"

    error = ErrorPrueba(
        mensaje="fallo con contexto",
        sugerencia="revisa los detalles",
        ruta=Path("configuracion.toml"),
        detalles={
            "ruta": Path("evidencia/salida.json"),
            "instante": datetime(2026, 7, 13, 15, 30, tzinfo=UTC),
            "etiquetas": {"beta", "alfa"},
            "intentos": frozenset({2, 1}),
            "contenido": b"tramalia",
            "credenciales": {"token": Path("no-debe-aparecer.txt")},
        },
    )

    esperado = {
        "codigo": "fallo_serializable",
        "mensaje": "fallo con contexto",
        "sugerencia": "revisa los detalles",
        "ruta": "configuracion.toml",
        "detalles": {
            "ruta": str(Path("evidencia/salida.json")),
            "instante": "2026-07-13T15:30:00+00:00",
            "etiquetas": ["alfa", "beta"],
            "intentos": [1, 2],
            "contenido": "base64:dHJhbWFsaWE=",
            "credenciales": {"token": "[REDACTADO]"},
        },
    }

    serializado = json.dumps(error.como_dict(), ensure_ascii=False, allow_nan=False, sort_keys=True)

    assert json.loads(serializado) == esperado
    assert serializado == json.dumps(
        error.como_dict(), ensure_ascii=False, allow_nan=False, sort_keys=True
    )


def test_error_normaliza_tipos_json_adicionales_y_objetos_desconocidos() -> None:
    error = ErrorTramalia(
        mensaje="fallo",
        sugerencia="revisa",
        detalles={
            "fecha": date(2026, 7, 13),
            "hora": time(15, 30, tzinfo=UTC),
            "contenido_mutable": bytearray(b"beta"),
            "prioridad": PrioridadPrueba.ALTA,
            "no_numero": float("nan"),
            "infinito": float("inf"),
            "menos_infinito": float("-inf"),
            "desconocido": object(),
        },
    )

    resultado = error.como_dict()
    json.dumps(resultado, ensure_ascii=False, allow_nan=False, sort_keys=True)

    assert resultado["detalles"] == {
        "fecha": "2026-07-13",
        "hora": "15:30:00+00:00",
        "contenido_mutable": "base64:YmV0YQ==",
        "prioridad": 2,
        "no_numero": "NaN",
        "infinito": "Infinity",
        "menos_infinito": "-Infinity",
        "desconocido": "<objeto_no_serializable:builtins.object>",
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


@pytest.mark.parametrize(
    "expira_en",
    [datetime(2026, 7, 13), datetime(2026, 7, 13, tzinfo=ZonaSinDesfase())],
)
def test_excepcion_rechaza_expiracion_sin_desfase_utc(expira_en: datetime) -> None:
    with pytest.raises(ErrorExcepcionInvalida) as capturada:
        ExcepcionFallo(
            razon="runner en mantenimiento",
            riesgo_aceptado="demora",
            control_afectado="ejecutor",
            referencia="ISSUE-123",
            revisor="ana",
            expira_en=expira_en,
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
    "ahora",
    [datetime(2026, 7, 12), datetime(2026, 7, 12, tzinfo=ZonaSinDesfase())],
)
def test_excepcion_vigente_rechaza_ahora_sin_desfase_utc(ahora: datetime) -> None:
    excepcion = ExcepcionFallo(
        razon="runner en mantenimiento",
        riesgo_aceptado="demora",
        control_afectado="ejecutor",
        referencia="ISSUE-123",
        revisor="ana",
        expira_en=datetime(2026, 7, 13, tzinfo=UTC),
    )

    with pytest.raises(ErrorExcepcionInvalida) as capturada:
        excepcion.vigente(ahora)

    assert capturada.value.codigo == "excepcion_invalida"
    assert capturada.value.detalles == {"campos": ["ahora_con_zona_horaria"]}


@pytest.mark.parametrize(
    ("tipo_enumeracion", "valor", "miembro"),
    [
        (ValorEstadoProyecto, "listo", ValorEstadoProyecto.LISTO),
        (ValorEstadoPuertas, "aprobado", ValorEstadoPuertas.APROBADO),
        (ValorResultadoPuerta, "omitido", ValorResultadoPuerta.OMITIDO),
        (ValorEstadoCierre, "bloqueado", ValorEstadoCierre.BLOQUEADO),
        (ValorEstadoIntegracion, "degradado", ValorEstadoIntegracion.DEGRADADO),
        (ValorEstadoBitacora, "invalida", ValorEstadoBitacora.INVALIDA),
    ],
)
def test_enumeraciones_coercionan_valores_de_texto(
    tipo_enumeracion: type[StrEnum], valor: str, miembro: StrEnum
) -> None:
    assert tipo_enumeracion(valor) is miembro
    assert str(miembro) == valor


@pytest.mark.parametrize("utilizado", [None, "", "   ", "\t"])
def test_estado_integracion_rechaza_fallback_sin_nombre_efectivo(
    utilizado: str | None,
) -> None:
    with pytest.raises(ValueError, match="utilizado"):
        EstadoIntegracion(
            "degradado", "memoria", "engram", utilizado, "fallback", "sin memoria", "instalar"
        )


def test_estado_integracion_coerciona_fallback_efectivo() -> None:
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


def test_estado_proyecto_es_inmutable_en_ejecucion() -> None:
    estado = EstadoProyecto(ValorEstadoProyecto.LISTO, Path("."))

    assert estado.listo is True
    with pytest.raises(FrozenInstanceError):
        estado.estado = ValorEstadoProyecto.AUSENTE


@pytest.mark.parametrize("tipo_modelo", CAMPOS_MODELOS)
def test_todos_los_modelos_son_frozen_y_slots(tipo_modelo: type[object]) -> None:
    parametros_dataclass = getattr(tipo_modelo, "__dataclass_params__")
    slots = getattr(tipo_modelo, "__slots__")

    assert parametros_dataclass.frozen is True
    assert "__slots__" in vars(tipo_modelo)
    assert "__dict__" not in slots


@pytest.mark.parametrize(("tipo_modelo", "nombres_esperados"), CAMPOS_MODELOS.items())
def test_modelos_publican_los_campos_contractuales(
    tipo_modelo: type[object], nombres_esperados: tuple[str, ...]
) -> None:
    assert tuple(campo.name for campo in fields(tipo_modelo)) == nombres_esperados
