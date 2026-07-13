from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from tramalia.core.errores import ErrorProyectoNoGobernado
from tramalia.core.modelos import EstadoProyecto, ValorEstadoProyecto
from tramalia.core.proyecto import (
    exigir_proyecto_actualizable,
    exigir_proyecto_gobernado,
    inspeccionar_estado_proyecto,
)

_INICIO_GOBIERNO = "<!-- tramalia:gobierno inicio -->"
_FIN_GOBIERNO = "<!-- tramalia:gobierno fin -->"


def _escribir_listo(raiz: Path) -> None:
    (raiz / ".tramalia").mkdir()
    (raiz / ".tramalia" / "config.json").write_text(
        json.dumps({"projectName": "demo"}),
        encoding="utf-8",
    )
    (raiz / ".tramalia" / "version").write_text("0.33.0\n", encoding="utf-8")
    (raiz / "AGENTS.md").write_text(
        f"{_INICIO_GOBIERNO}\ntramalia close\n{_FIN_GOBIERNO}\n",
        encoding="utf-8",
    )
    (raiz / "mise.toml").write_text(
        '[tasks.test]\nrun = "pytest"\n',
        encoding="utf-8",
    )


def _escribir_heredado(raiz: Path) -> None:
    _escribir_listo(raiz)
    (raiz / "AGENTS.md").write_text("Cierre: tramalia close\n", encoding="utf-8")


def test_distingue_ausente_heredado_parcial_y_listo(tmp_path: Path) -> None:
    assert inspeccionar_estado_proyecto(tmp_path).estado is ValorEstadoProyecto.AUSENTE

    (tmp_path / ".tramalia").mkdir()
    assert inspeccionar_estado_proyecto(tmp_path).estado is ValorEstadoProyecto.PARCIAL

    (tmp_path / ".tramalia" / "config.json").write_text(
        json.dumps({"projectName": "demo"}),
        encoding="utf-8",
    )
    (tmp_path / "AGENTS.md").write_text("tramalia close", encoding="utf-8")
    (tmp_path / "mise.toml").write_text("[tasks.test]\nrun='pytest'", encoding="utf-8")
    assert inspeccionar_estado_proyecto(tmp_path).estado is ValorEstadoProyecto.HEREDADO

    (tmp_path / ".tramalia" / "version").write_text("0.33.0", encoding="utf-8")
    assert inspeccionar_estado_proyecto(tmp_path).estado is ValorEstadoProyecto.HEREDADO

    (tmp_path / "AGENTS.md").write_text(
        f"{_INICIO_GOBIERNO}\ntramalia close\n{_FIN_GOBIERNO}\n",
        encoding="utf-8",
    )
    assert inspeccionar_estado_proyecto(tmp_path).estado is ValorEstadoProyecto.LISTO


def test_inspeccion_ausente_no_muta_el_repositorio(tmp_path: Path) -> None:
    estado = inspeccionar_estado_proyecto(tmp_path)

    assert estado.estado is ValorEstadoProyecto.AUSENTE
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("marcador", ["agentes", "directorio"])
def test_marcador_aislado_no_habilita_mutaciones(tmp_path: Path, marcador: str) -> None:
    if marcador == "agentes":
        (tmp_path / "AGENTS.md").write_text("reglas", encoding="utf-8")
    else:
        (tmp_path / ".tramalia").mkdir()

    with pytest.raises(ErrorProyectoNoGobernado) as capturada:
        exigir_proyecto_gobernado(tmp_path)

    assert capturada.value.codigo == "proyecto_no_gobernado"


def test_configuracion_json_invalida_es_parcial(tmp_path: Path) -> None:
    _escribir_listo(tmp_path)
    (tmp_path / ".tramalia" / "config.json").write_text("{", encoding="utf-8")

    estado = inspeccionar_estado_proyecto(tmp_path)

    assert estado.estado is ValorEstadoProyecto.PARCIAL
    assert "config.json invalido" in estado.problemas


@pytest.mark.parametrize("contenido", ["[]", '"demo"', "null", "1"])
def test_configuracion_no_objeto_es_parcial(tmp_path: Path, contenido: str) -> None:
    _escribir_listo(tmp_path)
    (tmp_path / ".tramalia" / "config.json").write_text(contenido, encoding="utf-8")

    estado = inspeccionar_estado_proyecto(tmp_path)

    assert estado.estado is ValorEstadoProyecto.PARCIAL
    assert "config.json invalido" in estado.problemas


@pytest.mark.parametrize("nombre", [None, "", " \t\n"])
def test_configuracion_sin_project_name_valido_es_parcial(
    tmp_path: Path,
    nombre: str | None,
) -> None:
    _escribir_listo(tmp_path)
    (tmp_path / ".tramalia" / "config.json").write_text(
        json.dumps({"projectName": nombre}),
        encoding="utf-8",
    )

    estado = inspeccionar_estado_proyecto(tmp_path)

    assert estado.estado is ValorEstadoProyecto.PARCIAL
    assert "config.json sin projectName valido" in estado.problemas


def test_archivo_agentes_sin_contrato_de_cierre_es_parcial(tmp_path: Path) -> None:
    _escribir_listo(tmp_path)
    (tmp_path / "AGENTS.md").write_text("reglas locales", encoding="utf-8")

    estado = inspeccionar_estado_proyecto(tmp_path)

    assert estado.estado is ValorEstadoProyecto.PARCIAL
    assert "AGENTS.md sin contrato tramalia close" in estado.problemas


@pytest.mark.parametrize(
    "contenido",
    [
        f"{_INICIO_GOBIERNO}\ntramalia close\n",
        f"tramalia close\n{_FIN_GOBIERNO}\n",
        f"{_FIN_GOBIERNO}\ntramalia close\n{_INICIO_GOBIERNO}\n",
        "tramalia:gobierno\ntramalia close\n",
        f"{_INICIO_GOBIERNO}\n{_FIN_GOBIERNO}\ntramalia close\n",
        f"tramalia close\n{_INICIO_GOBIERNO}\ntexto\n{_FIN_GOBIERNO}\n",
        (
            f"{_INICIO_GOBIERNO}\ntramalia close\n{_FIN_GOBIERNO}\n"
            f"{_INICIO_GOBIERNO}\ntramalia close\n{_FIN_GOBIERNO}\n"
        ),
        (
            f"{_INICIO_GOBIERNO}\n{_INICIO_GOBIERNO}\ntramalia close\n"
            f"{_FIN_GOBIERNO}\n{_FIN_GOBIERNO}\n"
        ),
    ],
    ids=[
        "inicio_sin_fin",
        "fin_sin_inicio",
        "desordenados",
        "mencion_no_canonica",
        "cierre_fuera_del_bloque",
        "mencion_previa_sin_cierre_en_bloque",
        "duplicados",
        "anidados",
    ],
)
def test_marcadores_de_gobierno_corruptos_no_estan_listos(
    tmp_path: Path,
    contenido: str,
) -> None:
    _escribir_listo(tmp_path)
    (tmp_path / "AGENTS.md").write_text(contenido, encoding="utf-8")

    assert inspeccionar_estado_proyecto(tmp_path).estado is ValorEstadoProyecto.PARCIAL


def test_mencion_previa_no_invalida_un_bloque_gobernado_correcto(tmp_path: Path) -> None:
    _escribir_listo(tmp_path)
    (tmp_path / "AGENTS.md").write_text(
        "Referencia historica a tramalia close.\n"
        f"{_INICIO_GOBIERNO}\n"
        "Cierre obligatorio: tramalia close --task TASK-1\n"
        f"{_FIN_GOBIERNO}\n",
        encoding="utf-8",
    )

    assert inspeccionar_estado_proyecto(tmp_path).estado is ValorEstadoProyecto.LISTO


def test_mise_invalido_se_delega_al_cargador_de_puertas(tmp_path: Path) -> None:
    _escribir_listo(tmp_path)
    (tmp_path / "mise.toml").write_text("[tasks", encoding="utf-8")

    assert inspeccionar_estado_proyecto(tmp_path).estado is ValorEstadoProyecto.LISTO


@pytest.mark.parametrize(
    "error",
    [
        OSError("lectura bloqueada"),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "byte invalido"),
    ],
    ids=["error_lectura", "utf8_invalido"],
)
def test_version_ilegible_es_parcial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error: OSError | UnicodeError,
) -> None:
    _escribir_listo(tmp_path)
    version = tmp_path / ".tramalia" / "version"
    lectura_original = Path.read_text

    def leer_texto(ruta: Path, *args: object, **kwargs: object) -> str:
        if ruta == version:
            raise error
        return lectura_original(ruta, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", leer_texto)

    estado = inspeccionar_estado_proyecto(tmp_path)

    assert estado.estado is ValorEstadoProyecto.PARCIAL
    assert ".tramalia/version invalido" in estado.problemas


def test_ruta_version_directorio_es_parcial(tmp_path: Path) -> None:
    _escribir_listo(tmp_path)
    version = tmp_path / ".tramalia" / "version"
    version.unlink()
    version.mkdir()

    estado = inspeccionar_estado_proyecto(tmp_path)

    assert estado.estado is ValorEstadoProyecto.PARCIAL
    assert ".tramalia/version invalido" in estado.problemas


def test_version_vacia_es_parcial(tmp_path: Path) -> None:
    _escribir_listo(tmp_path)
    (tmp_path / ".tramalia" / "version").write_text(" \n", encoding="utf-8")

    estado = inspeccionar_estado_proyecto(tmp_path)

    assert estado.estado is ValorEstadoProyecto.PARCIAL
    assert ".tramalia/version vacio" in estado.problemas


def test_upgrade_acepta_heredado_y_rechaza_ausente(tmp_path: Path) -> None:
    _escribir_heredado(tmp_path)
    (tmp_path / ".tramalia" / "version").unlink()

    assert exigir_proyecto_actualizable(tmp_path).estado is ValorEstadoProyecto.HEREDADO
    with pytest.raises(ErrorProyectoNoGobernado):
        exigir_proyecto_actualizable(tmp_path / "ausente")


def test_guardia_ordinaria_rechaza_heredado(tmp_path: Path) -> None:
    _escribir_heredado(tmp_path)

    with pytest.raises(ErrorProyectoNoGobernado):
        exigir_proyecto_gobernado(tmp_path)


@pytest.mark.parametrize(
    "guardia",
    [exigir_proyecto_gobernado, exigir_proyecto_actualizable],
    ids=["mutacion", "upgrade"],
)
def test_errores_de_guardia_son_serializables(
    tmp_path: Path,
    guardia: Callable[[Path], EstadoProyecto],
) -> None:
    (tmp_path / ".tramalia").mkdir()

    with pytest.raises(ErrorProyectoNoGobernado) as capturada:
        guardia(tmp_path)

    datos = capturada.value.como_dict()
    assert json.loads(json.dumps(datos, ensure_ascii=False, allow_nan=False)) == datos
    assert datos["codigo"] == "proyecto_no_gobernado"
    assert datos["detalles"]["estado"] == "parcial"
