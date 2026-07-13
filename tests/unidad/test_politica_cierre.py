from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from tramalia.core.errores import ErrorExcepcionInvalida
from tramalia.core.modelos import (
    EjecucionPuertas,
    ExcepcionFallo,
    ValorEstadoCierre,
    ValorEstadoPuertas,
)
from tramalia.core.politica_cierre import evaluar_cierre, evaluar_metricas

AHORA = datetime(2026, 7, 12, tzinfo=UTC)


def _excepcion(
    control: str,
    *,
    expirada: bool = False,
    solo_remediacion: bool = False,
) -> ExcepcionFallo:
    if solo_remediacion:
        return ExcepcionFallo(
            razon="bloqueo conocido",
            riesgo_aceptado="impacto acotado",
            control_afectado=control,
            referencia="ISSUE-8",
            revisor="ana",
            condicion_remediacion="corregir antes del siguiente release",
        )
    desplazamiento = -timedelta(days=1) if expirada else timedelta(days=1)
    return ExcepcionFallo(
        razon="bloqueo conocido",
        riesgo_aceptado="impacto acotado",
        control_afectado=control,
        referencia="ISSUE-8",
        revisor="ana",
        expira_en=AHORA + desplazamiento,
    )


@pytest.mark.parametrize(
    ("estado", "control"),
    [
        (ValorEstadoPuertas.EJECUTOR_NO_DISPONIBLE, "ejecutor"),
        (ValorEstadoPuertas.SIN_CONFIGURAR, "puertas"),
        (ValorEstadoPuertas.ERROR_EJECUCION, "ejecucion"),
    ],
)
def test_bloqueo_solo_pasa_con_excepcion_vigente(
    estado: ValorEstadoPuertas,
    control: str,
) -> None:
    ejecucion = EjecucionPuertas(estado=estado)

    assert evaluar_cierre(ejecucion, (), (), AHORA) == (
        ValorEstadoCierre.BLOQUEADO,
        (control,),
    )
    assert evaluar_cierre(ejecucion, (), (_excepcion(control),), AHORA) == (
        ValorEstadoCierre.APROBADO_CON_EXCEPCIONES,
        (),
    )


def test_fallido_sin_puertas_identificadas_no_admite_excepcion() -> None:
    ejecucion = EjecucionPuertas(estado=ValorEstadoPuertas.FALLIDO)

    assert evaluar_cierre(ejecucion, (), (_excepcion("ejecucion"),), AHORA) == (
        ValorEstadoCierre.BLOQUEADO,
        ("ejecucion",),
    )


def test_configuracion_de_puertas_invalida_no_admite_excepcion() -> None:
    ejecucion = EjecucionPuertas(estado=ValorEstadoPuertas.CONFIGURACION_INVALIDA)

    assert evaluar_cierre(ejecucion, (), (_excepcion("configuracion"),), AHORA) == (
        ValorEstadoCierre.BLOQUEADO,
        ("configuracion",),
    )


def test_cada_bloqueo_necesita_su_excepcion() -> None:
    ejecucion = EjecucionPuertas(
        estado=ValorEstadoPuertas.FALLIDO,
        fallidas=("test", "lint"),
    )

    assert evaluar_cierre(ejecucion, (), (_excepcion("test"),), AHORA) == (
        ValorEstadoCierre.BLOQUEADO,
        ("lint",),
    )


def test_error_mixto_exige_excepcion_por_cada_puerta_fallida() -> None:
    ejecucion = EjecucionPuertas(
        estado=ValorEstadoPuertas.ERROR_EJECUCION,
        fallidas=("test", "lint"),
    )

    assert evaluar_cierre(ejecucion, (), (_excepcion("test"),), AHORA) == (
        ValorEstadoCierre.BLOQUEADO,
        ("lint",),
    )


def test_puerta_y_metrica_requieren_cobertura_independiente() -> None:
    ejecucion = EjecucionPuertas(
        estado=ValorEstadoPuertas.FALLIDO,
        fallidas=("test",),
    )

    assert evaluar_cierre(
        ejecucion,
        ("metrica:accuracy",),
        (_excepcion("test"),),
        AHORA,
    ) == (ValorEstadoCierre.BLOQUEADO, ("metrica:accuracy",))


def test_aprobado_requiere_al_menos_una_puerta_ejecutada() -> None:
    ejecucion = EjecucionPuertas(estado=ValorEstadoPuertas.APROBADO)

    assert evaluar_cierre(ejecucion, (), (), AHORA) == (
        ValorEstadoCierre.BLOQUEADO,
        ("puertas",),
    )
    assert evaluar_cierre(ejecucion, (), (_excepcion("puertas"),), AHORA) == (
        ValorEstadoCierre.BLOQUEADO,
        ("puertas",),
    )


def test_ejecucion_realmente_aprobada_no_inventa_excepciones() -> None:
    ejecucion = EjecucionPuertas(
        estado=ValorEstadoPuertas.APROBADO,
        descubiertas=("test",),
        ejecutadas=("test",),
    )

    assert evaluar_cierre(ejecucion, (), (), AHORA) == (
        ValorEstadoCierre.APROBADO,
        (),
    )


@pytest.mark.parametrize(
    "ejecucion",
    [
        EjecucionPuertas(
            estado=ValorEstadoPuertas.APROBADO,
            ejecutadas=("test",),
            fallidas=("test",),
        ),
        EjecucionPuertas(
            estado=ValorEstadoPuertas.APROBADO,
            ejecutadas=("test",),
            omitidas=("lint",),
        ),
    ],
)
def test_agregado_aprobado_inconsistente_permanece_bloqueado(
    ejecucion: EjecucionPuertas,
) -> None:
    estado, pendientes = evaluar_cierre(ejecucion, (), (), AHORA)

    assert estado is ValorEstadoCierre.BLOQUEADO
    assert pendientes


def test_excepcion_expirada_se_rechaza_antes_de_persistir() -> None:
    with pytest.raises(ErrorExcepcionInvalida, match="vigente"):
        evaluar_cierre(
            EjecucionPuertas(estado=ValorEstadoPuertas.SIN_CONFIGURAR),
            (),
            (_excepcion("puertas", expirada=True),),
            AHORA,
        )


def test_instante_ingenuo_se_rechaza_incluso_sin_excepciones() -> None:
    with pytest.raises(ErrorExcepcionInvalida):
        evaluar_cierre(
            EjecucionPuertas(estado=ValorEstadoPuertas.APROBADO, ejecutadas=("test",)),
            (),
            (),
            datetime(2026, 7, 12),
        )


def test_control_ajeno_no_cubre_el_bloqueo() -> None:
    ejecucion = EjecucionPuertas(estado=ValorEstadoPuertas.SIN_CONFIGURAR)

    assert evaluar_cierre(ejecucion, (), (_excepcion("test"),), AHORA) == (
        ValorEstadoCierre.BLOQUEADO,
        ("puertas",),
    )


def test_controles_duplicados_se_deduplican_preservando_orden() -> None:
    ejecucion = EjecucionPuertas(
        estado=ValorEstadoPuertas.FALLIDO,
        fallidas=("test", "test", "lint"),
    )

    assert evaluar_cierre(
        ejecucion,
        ("metrica:a", "metrica:a"),
        (),
        AHORA,
    ) == (
        ValorEstadoCierre.BLOQUEADO,
        ("metrica:a", "test", "lint"),
    )


def test_excepcion_con_remediacion_sin_expiracion_es_vigente() -> None:
    ejecucion = EjecucionPuertas(estado=ValorEstadoPuertas.SIN_CONFIGURAR)

    assert evaluar_cierre(
        ejecucion,
        (),
        (_excepcion("puertas", solo_remediacion=True),),
        AHORA,
    ) == (ValorEstadoCierre.APROBADO_CON_EXCEPCIONES, ())


def test_todos_los_controles_cubiertos_aprueban_con_excepciones() -> None:
    ejecucion = EjecucionPuertas(
        estado=ValorEstadoPuertas.FALLIDO,
        fallidas=("test",),
    )

    assert evaluar_cierre(
        ejecucion,
        ("metrica:accuracy",),
        (_excepcion("test"), _excepcion("metrica:accuracy")),
        AHORA,
    ) == (ValorEstadoCierre.APROBADO_CON_EXCEPCIONES, ())


def test_metricas_ausentes_o_fuera_de_umbral_bloquean() -> None:
    assert evaluar_metricas({"metrics": {}}, {"accuracy": {"min": 0.9}}) == ("metrica:accuracy",)
    assert evaluar_metricas(
        {"metrics": {"drift": 0.2}},
        {"drift": {"max": 0.1}},
    ) == ("metrica:drift",)
