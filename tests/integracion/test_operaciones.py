from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tramalia.core import operaciones, puertas_calidad
from tramalia.core.errores import (
    ErrorConfiguracionMetricas,
    ErrorConfiguracionPuertas,
    ErrorExcepcionInvalida,
    ErrorIdentificadorInseguro,
    ErrorPersistenciaEvidencia,
    ErrorProyectoNoGobernado,
)
from tramalia.core.evidencia import leer_bitacora
from tramalia.core.modelos import ExcepcionFallo, ValorEstadoCierre


def _simular_mise(
    monkeypatch: pytest.MonkeyPatch,
    *,
    codigo: int,
    salida: str,
    error: str = "",
) -> None:
    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: "mise")
    monkeypatch.setattr(
        puertas_calidad.proc,
        "run",
        lambda *argumentos, **opciones: subprocess.CompletedProcess(
            argumentos, codigo, salida, error
        ),
    )


def _leer_metadatos(ruta_paquete: Path) -> dict[str, object]:
    return json.loads((ruta_paquete / "metadatos.json").read_text(encoding="utf-8"))


def test_sin_mise_bloquea_y_no_aprueba(
    proyecto_listo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: None)

    resultado = operaciones.cerrar_proyecto(proyecto_listo, "TASK-1")

    assert resultado.estado is ValorEstadoCierre.BLOQUEADO
    assert resultado.aprobado is False
    assert resultado.bloqueos == ("ejecutor",)
    assert resultado.ruta_paquete is not None
    assert _leer_metadatos(resultado.ruta_paquete)["estado_cierre"] == "bloqueado"


def test_toml_invalido_es_error_tipado_y_no_escribe(proyecto_listo: Path) -> None:
    (proyecto_listo / "mise.toml").write_text("[tasks", encoding="utf-8")

    with pytest.raises(ErrorConfiguracionPuertas):
        operaciones.cerrar_proyecto(proyecto_listo, "TASK-2")

    assert not (proyecto_listo / ".tramalia" / "evidencia").exists()


@pytest.mark.parametrize("contenido", ["{", "NaN", '{"coverage": NaN}', "[]"])
def test_metricas_o_umbrales_corruptos_no_escriben(
    proyecto_listo: Path,
    contenido: str,
) -> None:
    (proyecto_listo / ".tramalia" / "thresholds.json").write_text(
        contenido,
        encoding="utf-8",
    )

    with pytest.raises(ErrorConfiguracionMetricas):
        operaciones.cerrar_proyecto(proyecto_listo, "TASK-2B")

    assert not (proyecto_listo / ".tramalia" / "evidencia").exists()


def test_esquema_de_umbrales_invalido_no_ejecuta_ni_escribe(
    proyecto_listo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (proyecto_listo / ".tramalia" / "thresholds.json").write_text(
        json.dumps({"coverage": {"minimum": 80}}),
        encoding="utf-8",
    )
    ejecutado = False

    def ejecutar(*argumentos: object, **opciones: object) -> object:
        nonlocal ejecutado
        ejecutado = True
        raise AssertionError("las puertas no deben ejecutarse con configuracion invalida")

    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: "mise")
    monkeypatch.setattr(puertas_calidad.proc, "run", ejecutar)

    with pytest.raises(ErrorConfiguracionMetricas):
        operaciones.cerrar_proyecto(proyecto_listo, "TASK-2C")

    assert ejecutado is False
    assert not (proyecto_listo / ".tramalia" / "evidencia").exists()


@pytest.mark.parametrize(
    "contenido",
    [
        r'{"metrics": {"coverage": "\ud800"}}',
        '{"metrics": {"coverage": 1e400}}',
        '{"x":' * 66 + "0" + "}" * 66,
    ],
)
def test_json_no_finito_unicode_invalido_o_profundo_falla_antes_de_puertas(
    proyecto_listo: Path,
    monkeypatch: pytest.MonkeyPatch,
    contenido: str,
) -> None:
    (proyecto_listo / ".tramalia" / "metrics.json").write_text(
        contenido,
        encoding="utf-8",
    )
    ejecutado = False

    def ejecutar(*argumentos: object, **opciones: object) -> object:
        nonlocal ejecutado
        ejecutado = True
        raise AssertionError("el JSON invalido debe fallar antes de las puertas")

    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: "mise")
    monkeypatch.setattr(puertas_calidad.proc, "run", ejecutar)

    with pytest.raises(ErrorConfiguracionMetricas):
        operaciones.cerrar_proyecto(proyecto_listo, "TASK-JSON")

    assert ejecutado is False
    assert not (proyecto_listo / ".tramalia" / "evidencia").exists()


def test_archivo_json_enlazado_fuera_del_proyecto_es_rechazado(
    proyecto_listo: Path,
) -> None:
    externo = proyecto_listo.parent / "metricas-externas.json"
    externo.write_text('{"metrics": {"coverage": 100}}', encoding="utf-8")
    enlace = proyecto_listo / ".tramalia" / "metrics.json"
    try:
        enlace.symlink_to(externo)
    except OSError as error:
        pytest.skip(f"el sistema no permite crear el enlace de prueba: {error}")

    with pytest.raises(ErrorConfiguracionMetricas):
        operaciones.cerrar_proyecto(proyecto_listo, "TASK-ENLACE")

    assert not (proyecto_listo / ".tramalia" / "evidencia").exists()


def test_id_inseguro_no_escribe(proyecto_listo: Path) -> None:
    with pytest.raises(ErrorIdentificadorInseguro):
        operaciones.cerrar_proyecto(proyecto_listo, "../TASK")

    assert not (proyecto_listo / ".tramalia" / "evidencia").exists()


@pytest.mark.parametrize(
    "nombre_operacion",
    ["cerrar_proyecto", "crear_evidencia", "registrar_traspaso"],
)
def test_operaciones_mutantes_rechazan_proyecto_parcial_antes_de_escribir(
    tmp_path: Path,
    nombre_operacion: str,
) -> None:
    (tmp_path / ".tramalia").mkdir()
    operacion = getattr(operaciones, nombre_operacion)

    with pytest.raises(ErrorProyectoNoGobernado):
        operacion(tmp_path, "TASK-PARCIAL")

    assert list((tmp_path / ".tramalia").iterdir()) == []


def test_puerta_roja_con_excepcion_completa_publica_resultado_honesto(
    proyecto_listo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _simular_mise(monkeypatch, codigo=1, salida="LOG CRUDO", error=" DEL TEST")
    excepcion = ExcepcionFallo(
        razon="falso positivo revisado",
        riesgo_aceptado="impacto acotado",
        control_afectado="test",
        referencia="ISSUE-2",
        revisor="ana",
        condicion_remediacion="corregir antes del release",
    )

    resultado = operaciones.cerrar_proyecto(
        proyecto_listo,
        "TASK-3",
        agente="codex",
        revisor="ana",
        modelo="gpt-5",
        excepciones=(excepcion,),
    )

    assert resultado.estado is ValorEstadoCierre.APROBADO_CON_EXCEPCIONES
    assert resultado.ruta_paquete is not None
    metadatos = _leer_metadatos(resultado.ruta_paquete)
    traspaso = (resultado.ruta_paquete / "traspaso.md").read_text(encoding="utf-8")
    salida = (resultado.ruta_paquete / "test-salida.txt").read_bytes()
    assert metadatos["estado_cierre"] == "aprobado_con_excepciones"
    assert metadatos["agente"] == "codex"
    assert metadatos["modelo"] == "gpt-5"
    assert "aprobado_con_excepciones" in traspaso
    assert "test (ISSUE-2)" in traspaso
    assert salida == b"LOG CRUDO DEL TEST"
    comando = metadatos["comandos"][0]
    assert comando["archivo_salida"] == "test-salida.txt"
    assert comando["hash_salida"] == hashlib.sha256(salida).hexdigest()
    assert not (resultado.ruta_paquete / "test-salida.comprimida.md").exists()
    entrada = leer_bitacora(proyecto_listo)[0]
    assert entrada.agente == "codex"
    assert entrada.modelo == "gpt-5"
    assert entrada.resultado is ValorEstadoCierre.APROBADO_CON_EXCEPCIONES


def test_error_al_ejecutar_puerta_bloquea_y_se_registra(
    proyecto_listo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: "mise")

    def fallar(*argumentos: object, **opciones: object) -> object:
        raise TimeoutError("tiempo agotado")

    monkeypatch.setattr(puertas_calidad.proc, "run", fallar)

    resultado = operaciones.cerrar_proyecto(proyecto_listo, "TASK-ERROR")

    assert resultado.estado is ValorEstadoCierre.BLOQUEADO
    assert resultado.bloqueos == ("test",)
    assert resultado.ruta_paquete is not None
    assert (
        (resultado.ruta_paquete / "test-salida.txt")
        .read_text(encoding="utf-8")
        .startswith("TimeoutError:")
    )


def test_mise_sin_puertas_configuradas_bloquea(
    proyecto_listo: Path,
) -> None:
    (proyecto_listo / "mise.toml").write_text(
        "[tasks.auxiliar]\nrun = 'echo ok'\n",
        encoding="utf-8",
    )

    resultado = operaciones.cerrar_proyecto(proyecto_listo, "TASK-SIN-PUERTAS")

    assert resultado.estado is ValorEstadoCierre.BLOQUEADO
    assert resultado.bloqueos == ("puertas",)


def test_umbral_incumplido_bloquea_y_publica_diagnostico(
    proyecto_listo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metricas = {"dataset": {"name": "d"}, "metrics": {"coverage": 70}}
    umbrales = {"coverage": {"min": 80}}
    (proyecto_listo / ".tramalia" / "metrics.json").write_text(
        json.dumps(metricas),
        encoding="utf-8",
    )
    (proyecto_listo / ".tramalia" / "thresholds.json").write_text(
        json.dumps(umbrales),
        encoding="utf-8",
    )
    _simular_mise(monkeypatch, codigo=0, salida="ok")

    resultado = operaciones.cerrar_proyecto(proyecto_listo, "TASK-3B")

    assert resultado.estado is ValorEstadoCierre.BLOQUEADO
    assert resultado.bloqueos == ("metrica:coverage",)
    assert resultado.ruta_paquete is not None
    metadatos = _leer_metadatos(resultado.ruta_paquete)
    assert metadatos["metricas"] == metricas
    assert metadatos["umbrales"] == umbrales
    assert (
        json.loads((resultado.ruta_paquete / "metricas.json").read_text(encoding="utf-8"))
        == metricas
    )
    diagnostico = (resultado.ruta_paquete / "umbrales-metricas.txt").read_text(encoding="utf-8")
    assert "INCUMPLIMIENTOS" in diagnostico
    assert "metrica:coverage" in diagnostico


def test_umbral_cumplido_no_bloquea_y_conserva_artefactos(
    proyecto_listo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (proyecto_listo / ".tramalia" / "metrics.json").write_text(
        json.dumps({"metrics": {"coverage": 95}}),
        encoding="utf-8",
    )
    (proyecto_listo / ".tramalia" / "thresholds.json").write_text(
        json.dumps({"coverage": {"min": 80}}),
        encoding="utf-8",
    )
    _simular_mise(monkeypatch, codigo=0, salida="ok")

    resultado = operaciones.cerrar_proyecto(proyecto_listo, "TASK-3C")

    assert resultado.estado is ValorEstadoCierre.APROBADO
    assert resultado.aprobado is True
    assert resultado.ruta_paquete is not None
    assert (resultado.ruta_paquete / "metricas.json").is_file()
    assert "todos los umbrales cumplen" in (
        resultado.ruta_paquete / "umbrales-metricas.txt"
    ).read_text(encoding="utf-8")


def test_metricas_regeneradas_por_puerta_son_las_que_deciden_el_cierre(
    proyecto_listo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ruta_metricas = proyecto_listo / ".tramalia" / "metrics.json"
    ruta_metricas.write_text(
        json.dumps({"metrics": {"coverage": 95}}),
        encoding="utf-8",
    )
    (proyecto_listo / ".tramalia" / "thresholds.json").write_text(
        json.dumps({"coverage": {"min": 80}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: "mise")

    def regenerar(*argumentos: object, **opciones: object) -> subprocess.CompletedProcess[str]:
        ruta_metricas.write_text(
            json.dumps({"metrics": {"coverage": 50}}),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess([], 0, "ok", "")

    monkeypatch.setattr(puertas_calidad.proc, "run", regenerar)

    resultado = operaciones.cerrar_proyecto(proyecto_listo, "TASK-METRICAS-EFECTIVAS")

    assert resultado.estado is ValorEstadoCierre.BLOQUEADO
    assert resultado.bloqueos == ("metrica:coverage",)
    assert resultado.ruta_paquete is not None
    assert _leer_metadatos(resultado.ruta_paquete)["metricas"] == {"metrics": {"coverage": 50}}


def test_umbrales_no_pueden_cambiar_durante_las_puertas(
    proyecto_listo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ruta_umbrales = proyecto_listo / ".tramalia" / "thresholds.json"
    (proyecto_listo / ".tramalia" / "metrics.json").write_text(
        json.dumps({"metrics": {"coverage": 50}}),
        encoding="utf-8",
    )
    ruta_umbrales.write_text(
        json.dumps({"coverage": {"min": 80}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: "mise")

    def relajar(*argumentos: object, **opciones: object) -> subprocess.CompletedProcess[str]:
        ruta_umbrales.write_text(
            json.dumps({"coverage": {"min": 40}}),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess([], 0, "ok", "")

    monkeypatch.setattr(puertas_calidad.proc, "run", relajar)

    with pytest.raises(ErrorConfiguracionMetricas):
        operaciones.cerrar_proyecto(proyecto_listo, "TASK-UMBRAL-MUTABLE")

    assert not (proyecto_listo / ".tramalia" / "evidencia").exists()


def test_fallo_de_persistencia_no_devuelve_resultado_aprobado(
    proyecto_listo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _simular_mise(monkeypatch, codigo=0, salida="ok")

    def fallar_replace(*argumentos: object) -> None:
        raise OSError("disco")

    monkeypatch.setattr("tramalia.core.evidencia.os.replace", fallar_replace)

    with pytest.raises(ErrorPersistenciaEvidencia):
        operaciones.cerrar_proyecto(proyecto_listo, "TASK-4")


def test_fallo_inesperado_de_proyeccion_no_oculta_paquete_publicado(
    proyecto_listo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _simular_mise(monkeypatch, codigo=0, salida="ok")

    def fallar_proyeccion(*argumentos: object, **opciones: object) -> Path:
        raise RuntimeError("adaptador defectuoso")

    monkeypatch.setattr(operaciones, "proyectar_traspaso", fallar_proyeccion)

    with pytest.warns(RuntimeWarning, match="paquete se publico"):
        resultado = operaciones.cerrar_proyecto(proyecto_listo, "TASK-PROYECCION")

    assert resultado.estado is ValorEstadoCierre.APROBADO
    assert resultado.ruta_paquete is not None
    assert (resultado.ruta_paquete / "metadatos.json").is_file()
    assert len(list((proyecto_listo / ".tramalia" / "evidencia").iterdir())) == 1


@pytest.mark.parametrize(
    ("nombre", "operacion_esperada", "bloqueo_esperado"),
    [
        ("crear_evidencia", "evidencia", "operacion_evidencia"),
        ("registrar_traspaso", "traspaso", "operacion_traspaso"),
    ],
)
def test_operaciones_independientes_publican_pack_bloqueado_y_proyeccion(
    proyecto_listo: Path,
    nombre: str,
    operacion_esperada: str,
    bloqueo_esperado: str,
) -> None:
    operacion = getattr(operaciones, nombre)

    paquete = operacion(
        proyecto_listo,
        "TASK-5",
        agente="codex",
        revisor="ana",
    )

    metadatos = _leer_metadatos(paquete.ruta)
    assert metadatos["operacion"] == operacion_esperada
    assert metadatos["estado_cierre"] == "bloqueado"
    assert metadatos["errores_validacion"] == [bloqueo_esperado]
    assert (paquete.ruta / "traspaso.md").is_file()
    proyeccion = proyecto_listo / "docs" / "ai" / "07-traspaso-agentes.md"
    assert paquete.id_paquete in proyeccion.read_text(encoding="utf-8")


def test_excepcion_expirada_no_publica(
    proyecto_listo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ejecutado = False

    def ejecutar(*argumentos: object, **opciones: object) -> object:
        nonlocal ejecutado
        ejecutado = True
        raise AssertionError("una excepcion expirada debe fallar antes de las puertas")

    monkeypatch.setattr(puertas_calidad.proc, "which", lambda _: "mise")
    monkeypatch.setattr(puertas_calidad.proc, "run", ejecutar)
    excepcion = ExcepcionFallo(
        "razon",
        "riesgo",
        "test",
        "ISSUE-9",
        "ana",
        expira_en=datetime(2020, 1, 1, tzinfo=UTC),
    )

    with pytest.raises(ErrorExcepcionInvalida):
        operaciones.cerrar_proyecto(
            proyecto_listo,
            "TASK-6",
            excepciones=(excepcion,),
        )

    assert ejecutado is False
    assert not (proyecto_listo / ".tramalia" / "evidencia").exists()
