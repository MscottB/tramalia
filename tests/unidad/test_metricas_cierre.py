from __future__ import annotations

import json

import pytest

from tramalia.core.errores import ErrorConfiguracionMetricas
from tramalia.core.politica_cierre import evaluar_metricas


def test_minimo_y_maximo_generan_bloqueos_estables() -> None:
    metricas = {"metrics": {"accuracy": 0.88, "drift": 0.09}}
    umbrales = {"accuracy": {"min": 0.90}, "drift": {"max": 0.05}}

    assert evaluar_metricas(metricas, umbrales) == (
        "metrica:accuracy",
        "metrica:drift",
    )


def test_metricas_conformes_no_bloquean() -> None:
    metricas = {"metrics": {"accuracy": 0.95, "drift": 0.01}}
    umbrales = {
        "accuracy": {"min": 0.90, "max": 0.99},
        "drift": {"max": 0.05},
    }

    assert evaluar_metricas(metricas, umbrales) == ()


def test_metrica_ausente_bloquea() -> None:
    assert evaluar_metricas({"metrics": {}}, {"accuracy": {"min": 0.9}}) == ("metrica:accuracy",)


@pytest.mark.parametrize(
    "umbrales",
    [
        {1: {"min": 80}},
        {" ": {"min": 80}},
        {"coverage": []},
        {"coverage": {}},
        {"coverage": {"minimum": 80}},
        {"coverage": {"min": True}},
        {"coverage": {"min": "80"}},
        {"coverage": {"min": 90, "max": 80}},
        {"coverage": {"min": float("nan")}},
        {"coverage": {"min": float("inf")}},
        {"coverage": {"max": -float("inf")}},
        {"coverage": {"min": 10**400}},
    ],
)
def test_esquema_de_umbrales_invalido_es_error(umbrales: dict[object, object]) -> None:
    with pytest.raises(ErrorConfiguracionMetricas):
        evaluar_metricas({"metrics": {"coverage": 85}}, umbrales)


@pytest.mark.parametrize(
    "valor",
    [True, False, "0.95", None, float("nan"), float("inf"), -float("inf")],
)
def test_valor_medido_invalido_nunca_aprueba(valor: object) -> None:
    assert evaluar_metricas(
        {"metrics": {"accuracy": valor}},
        {"accuracy": {"min": 0.9}},
    ) == ("metrica:accuracy",)


def test_diagnostico_de_limites_invalidos_usa_orden_estable() -> None:
    with pytest.raises(ErrorConfiguracionMetricas) as capturada:
        evaluar_metricas(
            {"metrics": {"coverage": 85}},
            {"coverage": {"max": "noventa", "min": True}},
        )

    assert capturada.value.detalles["limite"] == "min"


def test_wrapper_de_metricas_invalido_equivale_a_metrica_ausente() -> None:
    assert evaluar_metricas(
        {"metrics": [0.95]},
        {"accuracy": {"min": 0.9}},
    ) == ("metrica:accuracy",)


def test_mapeo_plano_y_limites_inclusivos_son_validos() -> None:
    assert (
        evaluar_metricas(
            {"minimo": 0.9, "maximo": 1.0},
            {"minimo": {"min": 0.9}, "maximo": {"max": 1.0}},
        )
        == ()
    )


def test_sin_umbrales_no_inventa_bloqueos() -> None:
    assert evaluar_metricas({"metrics": {"accuracy": float("nan")}}, {}) == ()


def test_error_de_esquema_es_json_seguro_sin_representar_objetos() -> None:
    class ObjetoPeligroso:
        def __repr__(self) -> str:
            raise AssertionError("repr no debe ejecutarse")

    with pytest.raises(ErrorConfiguracionMetricas) as capturada:
        evaluar_metricas(
            {"metrics": {"accuracy": 0.9}},
            {"accuracy": ObjetoPeligroso()},
        )

    serializado = json.dumps(capturada.value.como_dict(), ensure_ascii=False)
    assert "configuracion_metricas_invalida" in serializado
    assert '"tipo_regla": "ObjetoPeligroso"' in serializado
    assert "repr no debe ejecutarse" not in serializado
