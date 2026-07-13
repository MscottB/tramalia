from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from tramalia.core.evidencia import crear_id_paquete, leer_bitacora, publicar_paquete
from tramalia.core.modelos import (
    EjecucionPuertas,
    ExcepcionFallo,
    ResultadoCierre,
    ResultadoPuerta,
    ValorEstadoBitacora,
    ValorEstadoCierre,
    ValorEstadoPuertas,
    ValorResultadoPuerta,
)
from tramalia.core.traspaso import construir_traspaso, proyectar_traspaso


def _raiz_paquete(paquete_v1) -> Path:
    return paquete_v1.ruta.parents[2]


def _leer_datos(paquete_v1) -> dict[str, object]:
    return json.loads((paquete_v1.ruta / "metadatos.json").read_text(encoding="utf-8"))


def _crear_entrada_manual(
    raiz: Path,
    id_paquete: str,
    datos: object,
    *,
    traspaso: bytes | None = b"traspaso\n",
) -> Path:
    ruta = raiz / ".tramalia" / "evidencia" / id_paquete
    ruta.mkdir(parents=True)
    (ruta / "metadatos.json").write_text(
        json.dumps(datos, ensure_ascii=False),
        encoding="utf-8",
    )
    if traspaso is not None:
        (ruta / "traspaso.md").write_bytes(traspaso)
    return ruta


def _resultado_con_excepcion(metadatos_v1) -> ResultadoCierre:
    excepcion = ExcepcionFallo(
        razon="falso positivo revisado",
        riesgo_aceptado="impacto acotado",
        control_afectado="test",
        referencia="ISSUE-7",
        revisor="ana",
        condicion_remediacion="corregir antes del release",
    )
    return ResultadoCierre(
        estado=ValorEstadoCierre.APROBADO_CON_EXCEPCIONES,
        id_tarea=metadatos_v1.id_tarea,
        id_paquete=metadatos_v1.id_paquete,
        ruta_paquete=None,
        ruta_traspaso=None,
        ejecucion=metadatos_v1.ejecucion,
        excepciones=(excepcion,),
        bloqueos=("test",),
    )


def test_construir_traspaso_refleja_resultado_sin_recalcular(metadatos_v1) -> None:
    resultado = _resultado_con_excepcion(metadatos_v1)

    contenido = construir_traspaso(resultado, "codex", "ana")
    texto = contenido.decode("utf-8")

    assert texto.startswith("# Traspaso canonico\n")
    assert f"id_paquete: {resultado.id_paquete}" in texto
    assert f"id_tarea: {resultado.id_tarea}" in texto
    assert "resultado: aprobado_con_excepciones" in texto
    assert "agente: codex" in texto and "revisor: ana" in texto
    assert "bloqueos: test" in texto
    assert "excepciones: test (ISSUE-7)" in texto
    assert contenido.endswith(b"\n")


def test_metadatos_y_traspaso_coinciden(paquete_v1) -> None:
    datos = _leer_datos(paquete_v1)
    texto = (paquete_v1.ruta / "traspaso.md").read_text(encoding="utf-8")

    assert datos["id_paquete"] in texto
    assert datos["id_tarea"] in texto
    assert datos["estado_cierre"] in texto


def test_bitacora_valida_conserva_modelo_agente_resultado_y_fecha(paquete_v1) -> None:
    entrada = leer_bitacora(_raiz_paquete(paquete_v1))[0]

    assert entrada.estado is ValorEstadoBitacora.VALIDA
    assert entrada.id_paquete == paquete_v1.id_paquete
    assert entrada.id_tarea == paquete_v1.metadatos.id_tarea
    assert entrada.agente == paquete_v1.metadatos.agente
    assert entrada.modelo == paquete_v1.metadatos.modelo
    assert entrada.resultado is paquete_v1.metadatos.estado_cierre
    assert entrada.cerrado_utc == paquete_v1.metadatos.fin_utc


def test_enlace_proyectado_resuelve_al_traspaso_canonico(
    tmp_path: Path,
    paquete_v1,
) -> None:
    ruta = proyectar_traspaso(tmp_path, paquete_v1)
    texto = ruta.read_text(encoding="utf-8")
    coincidencia = re.search(r"\]\(([^)]+)\)", texto)

    assert coincidencia is not None
    assert not Path(coincidencia.group(1)).is_absolute()
    assert (ruta.parent / coincidencia.group(1)).resolve() == (
        paquete_v1.ruta / "traspaso.md"
    ).resolve()
    assert paquete_v1.id_paquete in texto
    assert not list(ruta.parent.glob(".*.tmp-*"))


def test_fallo_de_proyeccion_conserva_canonico_y_proyeccion_anterior(
    tmp_path: Path,
    paquete_v1,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destino = tmp_path / "docs" / "ai" / "07-traspaso-agentes.md"
    destino.parent.mkdir(parents=True)
    destino.write_bytes(b"proyeccion anterior\n")
    canonico_antes = (paquete_v1.ruta / "traspaso.md").read_bytes()

    def fallar_replace(origen: object, destino: object) -> None:
        raise OSError("bloqueado")

    monkeypatch.setattr("tramalia.core.traspaso.os.replace", fallar_replace)

    ruta = proyectar_traspaso(tmp_path, paquete_v1)

    assert ruta == destino
    assert destino.read_bytes() == b"proyeccion anterior\n"
    assert (paquete_v1.ruta / "traspaso.md").read_bytes() == canonico_antes
    assert not list(destino.parent.glob(".*.tmp-*"))


def test_fallo_al_crear_directorio_de_proyeccion_es_no_fatal(
    tmp_path: Path,
    paquete_v1,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    crear_directorio = Path.mkdir

    def fallar(ruta: Path, *argumentos: object, **opciones: object) -> None:
        if ruta.name == "ai":
            raise PermissionError("documentacion de solo lectura")
        crear_directorio(ruta, *argumentos, **opciones)

    canonico_antes = (paquete_v1.ruta / "traspaso.md").read_bytes()
    monkeypatch.setattr(Path, "mkdir", fallar)

    ruta = proyectar_traspaso(tmp_path, paquete_v1)

    assert ruta == tmp_path / "docs" / "ai" / "07-traspaso-agentes.md"
    assert (paquete_v1.ruta / "traspaso.md").read_bytes() == canonico_antes


def test_metadatos_corruptos_son_invalidos_sin_fallback_markdown(tmp_path: Path) -> None:
    id_paquete = crear_id_paquete(datetime(2026, 7, 13, tzinfo=UTC))
    ruta = tmp_path / ".tramalia" / "evidencia" / id_paquete
    ruta.mkdir(parents=True)
    (ruta / "metadatos.json").write_text("{SECRETO_NO_FILTRAR", encoding="utf-8")
    (ruta / "estado-puertas.md").write_text("aprobado", encoding="utf-8")

    entrada = leer_bitacora(tmp_path)[0]

    assert entrada.estado is ValorEstadoBitacora.INVALIDA
    assert entrada.resultado is None
    assert "SECRETO_NO_FILTRAR" not in (entrada.error or "")


def test_metadatos_v1_truncados_no_se_marcan_validos(tmp_path: Path) -> None:
    id_paquete = crear_id_paquete(datetime(2026, 7, 13, 0, 0, 1, tzinfo=UTC))
    _crear_entrada_manual(
        tmp_path,
        id_paquete,
        {
            "version_esquema": 1,
            "id_paquete": id_paquete,
            "id_tarea": "TASK-1",
            "estado_cierre": "bloqueado",
            "fin_utc": "2026-07-12T20:30:00Z",
        },
    )

    entrada = leer_bitacora(tmp_path)[0]

    assert entrada.estado is ValorEstadoBitacora.INVALIDA
    assert "faltan claves" in (entrada.error or "")


def test_id_paquete_debe_coincidir_con_directorio(paquete_v1) -> None:
    ruta_metadatos = paquete_v1.ruta / "metadatos.json"
    datos = _leer_datos(paquete_v1)
    datos["id_paquete"] = crear_id_paquete(datetime(2026, 7, 13, 0, 0, 2, tzinfo=UTC))
    ruta_metadatos.write_text(json.dumps(datos), encoding="utf-8")

    entrada = leer_bitacora(_raiz_paquete(paquete_v1))[0]

    assert entrada.estado is ValorEstadoBitacora.INVALIDA
    assert "no coincide" in (entrada.error or "")


@pytest.mark.parametrize(
    ("mutar", "fragmento"),
    [
        (lambda datos: datos["puertas"].__setitem__("estado", None), "puertas.estado"),
        (
            lambda datos: datos["entorno"].__setitem__("cadena_herramientas", None),
            "cadena_herramientas",
        ),
        (lambda datos: datos["git"].__setitem__("rastreados", None), "git.rastreados"),
        (lambda datos: datos.__setitem__("estado_cierre", "inventado"), "estado_cierre"),
        (lambda datos: datos.__setitem__("metricas", {"x": float("nan")}), "finito"),
        (lambda datos: datos.__setitem__("vinculo_traspaso", "otro.md"), "canonico"),
    ],
)
def test_metadatos_semanticamente_corruptos_son_invalidos(
    tmp_path: Path,
    metadatos_v1,
    mutar,
    fragmento: str,
) -> None:
    datos = json.loads(
        publicar_paquete(
            tmp_path,
            metadatos_v1,
            {"traspaso.md": b"base\n"},
        )
        .ruta.joinpath("metadatos.json")
        .read_text(encoding="utf-8")
    )
    mutar(datos)
    ruta = tmp_path / ".tramalia" / "evidencia" / metadatos_v1.id_paquete
    ruta.joinpath("metadatos.json").write_text(
        json.dumps(datos, allow_nan=True),
        encoding="utf-8",
    )

    entrada = leer_bitacora(tmp_path)[0]

    assert entrada.estado is ValorEstadoBitacora.INVALIDA
    assert fragmento in (entrada.error or "")


def _metadatos_con_salida(metadatos_v1, contenido: bytes):
    inicio = metadatos_v1.inicio_utc
    fin = inicio + timedelta(seconds=1)
    resultado = ResultadoPuerta(
        nombre="test",
        comando=("mise", "run", "test"),
        estado=ValorResultadoPuerta.APROBADO,
        codigo_salida=0,
        salida=contenido.decode(),
        inicio_utc=inicio,
        fin_utc=fin,
        duracion_segundos=1.0,
        hash_salida=hashlib.sha256(contenido).hexdigest(),
        archivo_salida="test-salida.txt",
    )
    ejecucion = EjecucionPuertas(
        estado=ValorEstadoPuertas.APROBADO,
        descubiertas=("test",),
        ejecutadas=("test",),
        resultados=(resultado,),
    )
    return replace(
        metadatos_v1,
        fin_utc=fin,
        ejecucion=ejecucion,
        estado_cierre=ValorEstadoCierre.APROBADO,
        errores_validacion=(),
    )


@pytest.mark.parametrize("alteracion", ["ausente", "hash_distinto"])
def test_bitacora_verifica_archivos_de_salida(
    tmp_path: Path,
    metadatos_v1,
    alteracion: str,
) -> None:
    contenido = b"salida exacta\n"
    metadatos = _metadatos_con_salida(metadatos_v1, contenido)
    paquete = publicar_paquete(
        tmp_path,
        metadatos,
        {"traspaso.md": b"traspaso\n", "test-salida.txt": contenido},
    )
    salida = paquete.ruta / "test-salida.txt"
    if alteracion == "ausente":
        salida.unlink()
    else:
        salida.write_bytes(b"contenido alterado")

    entrada = leer_bitacora(tmp_path)[0]

    assert entrada.estado is ValorEstadoBitacora.INVALIDA
    assert "archivo de salida" in (entrada.error or "")


@pytest.mark.parametrize(
    ("campo", "valor", "fragmento"),
    [
        ("duracion_segundos", 10**400, "duracion_segundos"),
        ("hash_salida", "x", "hash_salida"),
        ("archivo_salida", "..", "archivo_salida"),
        ("codigo_salida", True, "codigo_salida"),
        ("comando", [], "no puede estar vacio"),
        ("inicio_utc", "2026-07-13T12:00:00", "timestamp UTC"),
        ("estado", "inventado", "estado invalido"),
    ],
)
def test_comandos_semanticamente_corruptos_son_invalidos(
    tmp_path: Path,
    metadatos_v1,
    campo: str,
    valor: object,
    fragmento: str,
) -> None:
    contenido = b"salida exacta\n"
    metadatos = _metadatos_con_salida(metadatos_v1, contenido)
    paquete = publicar_paquete(
        tmp_path,
        metadatos,
        {"traspaso.md": b"traspaso\n", "test-salida.txt": contenido},
    )
    datos = _leer_datos(paquete)
    datos["comandos"][0][campo] = valor
    (paquete.ruta / "metadatos.json").write_text(
        json.dumps(datos),
        encoding="utf-8",
    )

    entrada = leer_bitacora(tmp_path)[0]

    assert entrada.estado is ValorEstadoBitacora.INVALIDA
    assert fragmento in (entrada.error or "")


def test_bitacora_ignora_staging_y_una_entrada_corrupta_no_oculta_las_validas(
    paquete_v1,
) -> None:
    raiz = _raiz_paquete(paquete_v1)
    base = paquete_v1.ruta.parent
    staging = base / ".tmp-ajeno"
    staging.mkdir()
    (staging / "metadatos.json").write_text("{}", encoding="utf-8")
    id_corrupto = crear_id_paquete(datetime(2026, 7, 13, 0, 0, 3, tzinfo=UTC))
    _crear_entrada_manual(raiz, id_corrupto, {})

    entradas = leer_bitacora(raiz)

    assert all(not entrada.id_paquete.startswith(".tmp-") for entrada in entradas)
    assert {entrada.estado for entrada in entradas} == {
        ValorEstadoBitacora.VALIDA,
        ValorEstadoBitacora.INVALIDA,
    }


def test_plantilla_y_documentos_usan_nombres_formales(raiz_proyecto: Path) -> None:
    plantilla = raiz_proyecto / "tramalia" / "templates" / "project" / "docs" / "ai"
    nombre_anterior = "07-" + "handoff-agentes.md"
    assert (plantilla / "07-traspaso-agentes.md").is_file()
    assert not (plantilla / nombre_anterior).exists()

    rutas = [
        raiz_proyecto / "tramalia" / "mcp_server.py",
        raiz_proyecto / "tramalia" / "templates" / "project" / "specs" / "tasks.md",
        raiz_proyecto
        / "tramalia"
        / "templates"
        / "project"
        / "docs"
        / "ai"
        / "13-analitica-datos.md",
        raiz_proyecto / "docs" / "flujo-completo.md",
        raiz_proyecto / "docs" / "flujo-completo.en.md",
        raiz_proyecto / "docs" / "comandos.md",
        raiz_proyecto / "docs" / "comandos.en.md",
    ]
    vocabulario_anterior = (
        "07-" + "handoff-agentes",
        ".tramalia/" + "evidence",
        "metadata" + ".json",
    )
    for ruta in rutas:
        texto = ruta.read_text(encoding="utf-8")
        assert not any(termino in texto for termino in vocabulario_anterior), ruta


def test_proyeccion_no_escribe_fuera_si_docs_es_symlink(
    tmp_path: Path,
    paquete_v1,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    externo = tmp_path / "externo"
    externo.mkdir()
    docs = tmp_path / "docs"
    try:
        docs.symlink_to(externo, target_is_directory=True)
    except OSError:
        resolver_real = Path.resolve

        def simular_enlace(ruta: Path, *args: object, **kwargs: object) -> Path:
            if ruta == docs or docs in ruta.parents:
                return externo / ruta.relative_to(docs)
            return resolver_real(ruta, *args, **kwargs)

        monkeypatch.setattr(Path, "resolve", simular_enlace)

    destino = proyectar_traspaso(tmp_path, paquete_v1)

    assert destino == tmp_path / "docs" / "ai" / "07-traspaso-agentes.md"
    assert list(externo.rglob("*")) == []


def test_proyeccion_revalida_padre_despues_de_escribir_temporal(
    tmp_path: Path,
    paquete_v1,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    padre = tmp_path / "docs" / "ai"
    externo = tmp_path / "externo"
    externo.mkdir()
    resolver_real = Path.resolve
    fsync_real = os.fsync
    desviado = False
    replace_invocado = False

    def marcar_desvio(descriptor: int) -> None:
        nonlocal desviado
        fsync_real(descriptor)
        desviado = True

    def resolver(ruta: Path, *args: object, **kwargs: object) -> Path:
        if desviado and (ruta == padre or padre in ruta.parents):
            relativo = Path() if ruta == padre else ruta.relative_to(padre)
            return externo / relativo
        return resolver_real(ruta, *args, **kwargs)

    def observar_replace(origen: object, destino: object) -> None:
        nonlocal replace_invocado
        replace_invocado = True

    monkeypatch.setattr("tramalia.core.traspaso.os.fsync", marcar_desvio)
    monkeypatch.setattr(Path, "resolve", resolver)
    monkeypatch.setattr("tramalia.core.traspaso.os.replace", observar_replace)

    proyectar_traspaso(tmp_path, paquete_v1)

    assert replace_invocado is False
    assert list(externo.rglob("*")) == []
    assert not list(padre.glob(".*.tmp-*"))


def test_bitacora_revalida_metadata_despues_de_abrirla(
    tmp_path: Path,
    paquete_v1,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metadata = paquete_v1.ruta / "metadatos.json"
    abrir_real = Path.open
    resolver_real = Path.resolve
    abierta = False

    def abrir(ruta: Path, *args: object, **kwargs: object):
        nonlocal abierta
        archivo = abrir_real(ruta, *args, **kwargs)
        if ruta == metadata:
            abierta = True
        return archivo

    def resolver(ruta: Path, *args: object, **kwargs: object) -> Path:
        if abierta and ruta == metadata:
            return tmp_path / "fuera" / "metadatos.json"
        return resolver_real(ruta, *args, **kwargs)

    monkeypatch.setattr(Path, "open", abrir)
    monkeypatch.setattr(Path, "resolve", resolver)

    entrada = leer_bitacora(_raiz_paquete(paquete_v1))[0]

    assert entrada.estado is ValorEstadoBitacora.INVALIDA
    assert "fuera del paquete" in (entrada.error or "")


def test_error_de_bitacora_no_incluye_clave_controlada_por_metadata(paquete_v1) -> None:
    datos = _leer_datos(paquete_v1)
    clave_secreta = "TOKEN_RUTA_SUPER_SECRETA"
    datos["metricas"] = {clave_secreta: float("nan")}
    (paquete_v1.ruta / "metadatos.json").write_text(
        json.dumps(datos, allow_nan=True),
        encoding="utf-8",
    )

    entrada = leer_bitacora(_raiz_paquete(paquete_v1))[0]

    assert entrada.estado is ValorEstadoBitacora.INVALIDA
    assert clave_secreta not in (entrada.error or "")
