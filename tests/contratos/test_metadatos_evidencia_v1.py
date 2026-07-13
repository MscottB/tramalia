from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from tramalia.core import evidencia
from tramalia.core.errores import ErrorPersistenciaEvidencia
from tramalia.core.evidencia import _serializar, capturar_estado_git
from tramalia.core.modelos import (
    EjecucionPuertas,
    ExcepcionFallo,
    ResultadoPuerta,
    ValorEstadoCierre,
    ValorEstadoPuertas,
    ValorResultadoPuerta,
)


def test_gitignore_usa_directorio_de_evidencia_espanol() -> None:
    raiz = Path(__file__).resolve().parents[2]
    contenido = (raiz / ".gitignore").read_text(encoding="utf-8")

    assert ".tramalia/evidencia/" in contenido
    assert ".tramalia/evidence/" not in contenido


def _ejecutar_git(raiz: Path, *argumentos: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *argumentos],
        cwd=raiz,
        check=True,
        text=True,
        capture_output=True,
    )


def _crear_repo_git(raiz: Path) -> None:
    _ejecutar_git(raiz, "init", "-b", "main")
    _ejecutar_git(raiz, "config", "user.email", "test@example.com")
    _ejecutar_git(raiz, "config", "user.name", "Test")


def test_git_distingue_rastreados_preparados_no_rastreados_y_cambios(
    tmp_path: Path,
) -> None:
    _crear_repo_git(tmp_path)
    nombres = (
        "rastreado con espacio.txt",
        "renombrar á.txt",
        "eliminar.txt",
        "eliminar-preparado.txt",
    )
    for nombre in nombres:
        (tmp_path / nombre).write_text(nombre, encoding="utf-8")
    _ejecutar_git(tmp_path, "add", ".")
    _ejecutar_git(tmp_path, "commit", "-m", "base")

    (tmp_path / "rastreado con espacio.txt").write_text("cambio", encoding="utf-8")
    _ejecutar_git(tmp_path, "mv", "renombrar á.txt", "renombrado á.txt")
    (tmp_path / "eliminar.txt").unlink()
    (tmp_path / "eliminar-preparado.txt").unlink()
    _ejecutar_git(tmp_path, "add", "eliminar-preparado.txt")
    (tmp_path / "preparado.txt").write_text("preparado", encoding="utf-8")
    _ejecutar_git(tmp_path, "add", "preparado.txt")
    (tmp_path / "no-rastreado á.txt").write_text("nuevo", encoding="utf-8")

    estado = capturar_estado_git(tmp_path)

    assert estado.commit
    assert estado.rama == "main"
    assert estado.limpio is False
    assert estado.base_comparacion == estado.commit
    assert "rastreado con espacio.txt" in estado.rastreados
    assert "eliminar.txt" in estado.rastreados
    assert "preparado.txt" in estado.preparados
    assert "eliminar-preparado.txt" in estado.preparados
    assert "no-rastreado á.txt" in estado.no_rastreados
    assert "renombrar á.txt -> renombrado á.txt" in estado.renombrados
    assert {"eliminar.txt", "eliminar-preparado.txt"} <= set(estado.eliminados)


def test_git_limpio_y_fuera_de_git_son_estados_distintos(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _crear_repo_git(repo)
    (repo / "base.txt").write_text("base", encoding="utf-8")
    _ejecutar_git(repo, "add", ".")
    _ejecutar_git(repo, "commit", "-m", "base")

    limpio = capturar_estado_git(repo)
    ausente = capturar_estado_git(tmp_path / "sin-repo")

    assert limpio.limpio is True
    assert limpio.commit and limpio.rama == "main"
    assert limpio.rastreados == limpio.preparados == limpio.no_rastreados == ()
    assert ausente.commit is ausente.rama is ausente.limpio is None
    assert ausente.rastreados == ausente.preparados == ausente.no_rastreados == ()


def test_fallo_de_git_no_escapa_como_excepcion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fallar(*args: object, **kwargs: object) -> None:
        raise OSError("git no disponible")

    monkeypatch.setattr(evidencia.subprocess, "run", fallar)

    estado = capturar_estado_git(tmp_path)

    assert estado.commit is estado.rama is estado.limpio is None
    assert estado.rastreados == estado.preparados == estado.no_rastreados == ()


def _metadatos_con_comando(metadatos_v1):
    ahora = metadatos_v1.inicio_utc
    resultado = ResultadoPuerta(
        nombre="test",
        comando=("mise", "run", "test"),
        estado=ValorResultadoPuerta.APROBADO,
        codigo_salida=0,
        salida="SECRETO-RAW-NO-METADATA",
        inicio_utc=ahora,
        fin_utc=ahora + timedelta(seconds=1),
        duracion_segundos=1.0,
        hash_salida="a" * 64,
        archivo_salida="test-salida.txt",
    )
    ejecucion = EjecucionPuertas(
        estado=ValorEstadoPuertas.APROBADO,
        descubiertas=("test",),
        ejecutadas=("test",),
        resultados=(resultado,),
    )
    excepciones = (
        ExcepcionFallo(
            razon="riesgo revisado",
            riesgo_aceptado="impacto acotado",
            control_afectado="test",
            referencia="ISSUE-8",
            revisor="ana",
            expira_en=ahora + timedelta(days=1),
        ),
        ExcepcionFallo(
            razon="remediacion acordada",
            riesgo_aceptado="impacto acotado",
            control_afectado="metrica:accuracy",
            referencia="ISSUE-9",
            revisor="ana",
            condicion_remediacion="corregir antes del release",
        ),
    )
    return replace(
        metadatos_v1,
        fin_utc=ahora + timedelta(seconds=1),
        ejecucion=ejecucion,
        estado_cierre=ValorEstadoCierre.APROBADO,
        excepciones=excepciones,
    )


def test_metadatos_serializados_tienen_claves_formales(metadatos_v1) -> None:
    metadatos = _metadatos_con_comando(metadatos_v1)

    serializado = _serializar(metadatos)
    datos = json.loads(serializado)

    assert datos["version_esquema"] == 1
    assert {
        "id_paquete",
        "id_tarea",
        "operacion",
        "inicio_utc",
        "fin_utc",
        "entorno",
        "git",
        "comandos",
        "puertas",
        "estado_cierre",
        "agente",
        "modelo",
        "metricas",
        "umbrales",
        "errores_validacion",
        "excepciones",
        "vinculo_traspaso",
    } <= datos.keys()
    comando = datos["comandos"][0]
    assert {
        "nombre",
        "comando",
        "estado",
        "inicio_utc",
        "fin_utc",
        "duracion_segundos",
        "codigo_salida",
        "hash_salida",
        "archivo_salida",
    } <= comando.keys()
    assert "salida" not in comando
    assert b"SECRETO-RAW-NO-METADATA" not in serializado
    assert datos["puertas"]["ejecutadas"] == ["test"]
    assert datos["excepciones"][0]["expira_en"].endswith("Z")
    assert datos["excepciones"][1]["expira_en"] is None
    assert datos["excepciones"][1]["condicion_remediacion"]


def test_serializacion_es_determinista_utf8_y_termina_en_newline(metadatos_v1) -> None:
    metadatos = replace(
        _metadatos_con_comando(metadatos_v1),
        metricas={"descripcion": "métrica válida"},
    )

    primero = _serializar(metadatos)
    segundo = _serializar(metadatos)

    assert primero == segundo
    assert primero.endswith(b"\n")
    assert "métrica válida".encode() in primero
    json.loads(primero.decode("utf-8"))


@pytest.mark.parametrize(
    "mutacion",
    [
        {"version_esquema": 2},
        {"inicio_utc": datetime(2026, 7, 12)},
        {"fin_utc": datetime(2026, 7, 12)},
        {"metricas": {"accuracy": float("nan")}},
        {"metricas": {"accuracy": float("inf")}},
    ],
)
def test_metadata_invalida_falla_con_error_de_dominio(
    metadatos_v1,
    mutacion: dict[str, object],
) -> None:
    with pytest.raises(ErrorPersistenciaEvidencia):
        _serializar(replace(metadatos_v1, **mutacion))


def test_objeto_no_json_no_invoca_repr(metadatos_v1) -> None:
    class ObjetoPeligroso:
        def __repr__(self) -> str:
            raise AssertionError("repr no debe ejecutarse")

    with pytest.raises(ErrorPersistenciaEvidencia) as capturada:
        _serializar(replace(metadatos_v1, metricas={"accuracy": ObjetoPeligroso()}))

    json.dumps(capturada.value.como_dict())
    assert "repr no debe ejecutarse" not in json.dumps(capturada.value.como_dict())


def test_timestamps_se_normalizan_a_utc(metadatos_v1) -> None:
    from datetime import timezone

    zona = timezone(-timedelta(hours=3))
    inicio = datetime(2026, 7, 12, 17, 0, tzinfo=zona)
    fin = inicio + timedelta(seconds=2)

    datos = json.loads(_serializar(replace(metadatos_v1, inicio_utc=inicio, fin_utc=fin)))

    assert datos["inicio_utc"] == "2026-07-12T20:00:00Z"
    assert datos["fin_utc"] == "2026-07-12T20:00:02Z"


def test_ids_y_orden_temporal_invalidos_no_forman_metadata(metadatos_v1) -> None:
    with pytest.raises(ErrorPersistenciaEvidencia):
        _serializar(replace(metadatos_v1, id_paquete="../escape"))
    with pytest.raises(ErrorPersistenciaEvidencia):
        _serializar(
            replace(
                metadatos_v1,
                fin_utc=metadatos_v1.inicio_utc - timedelta(seconds=1),
            )
        )


@pytest.mark.parametrize(
    "cambios_resultado",
    [
        {"comando": ()},
        {"comando": ("mise", "")},
        {"duracion_segundos": -1.0},
        {"duracion_segundos": float("nan")},
        {"codigo_salida": True},
        {"hash_salida": "no-es-sha256"},
        {"archivo_salida": "../escape.txt"},
        {"inicio_utc": datetime(2026, 7, 12)},
    ],
)
def test_comando_invalido_no_entra_al_esquema(
    metadatos_v1,
    cambios_resultado: dict[str, object],
) -> None:
    metadatos = _metadatos_con_comando(metadatos_v1)
    resultado = replace(metadatos.ejecucion.resultados[0], **cambios_resultado)
    ejecucion = replace(metadatos.ejecucion, resultados=(resultado,))

    with pytest.raises(ErrorPersistenciaEvidencia):
        _serializar(replace(metadatos, ejecucion=ejecucion))
