import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import pytest

pytest.importorskip("mcp")

import tramalia.mcp_server as servidor_mcp
from tramalia.core.modelos import (
    EjecucionPuertas,
    ResultadoCierre,
    ValorEstadoCierre,
    ValorEstadoPuertas,
)
from tramalia.mcp_server import construir_servidor

pytestmark = [pytest.mark.integracion, pytest.mark.opcional]

_ESPERADAS = {
    "project_status",
    "get_agent_rules",
    "get_failed_attempts",
    "get_current_task",
    "doctor",
    "record_handoff",
    "build_evidence",
    "cerrar_proyecto",
    "build_context",
}


@dataclass(frozen=True)
class PaqueteFalso:
    id_paquete: str
    ruta: Path


class ValorPrueba(Enum):
    UNO = 1


def _invocar(nombre: str, argumentos: dict[str, object]) -> dict[str, object]:
    contenido, estructurado = asyncio.run(construir_servidor().call_tool(nombre, argumentos))
    assert json.loads(contenido[0].text) == estructurado
    assert isinstance(estructurado, dict)
    return estructurado


def test_serializacion_mcp_convierte_enumeraciones_recursivamente() -> None:
    valor = {"estado": ValorPrueba.UNO, "historial": (ValorPrueba.UNO,)}

    assert servidor_mcp._valor_publico(valor) == {
        "estado": 1,
        "historial": [1],
    }


def test_servidor_registra_herramientas_esperadas() -> None:
    herramientas = asyncio.run(construir_servidor().list_tools())
    assert _ESPERADAS <= {herramienta.name for herramienta in herramientas}


def test_estado_mcp_usa_inspeccion_tipificada(tmp_path, monkeypatch) -> None:
    (tmp_path / "AGENTS.md").write_text("reglas aisladas", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    contenido, _estructurado = asyncio.run(construir_servidor().call_tool("project_status", {}))

    assert any("inicializado: False" in bloque.text for bloque in contenido)


@pytest.mark.parametrize(
    ("nombre", "argumentos"),
    [
        ("record_handoff", {"task": "TASK-1"}),
        ("build_evidence", {"task": "TASK-1"}),
        ("cerrar_proyecto", {"task": "TASK-1"}),
    ],
)
def test_mutaciones_mcp_devuelven_error_tipado_sin_proyecto(
    tmp_path,
    monkeypatch,
    nombre: str,
    argumentos: dict[str, object],
) -> None:
    monkeypatch.chdir(tmp_path)

    respuesta = _invocar(nombre, argumentos)

    assert respuesta["ok"] is False
    assert respuesta["error"]["codigo"] == "proyecto_no_gobernado"  # type: ignore[index]


def test_excepcion_mcp_parcial_no_se_ignora(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    respuesta = _invocar(
        "cerrar_proyecto",
        {"task": "TASK-1", "razon_excepcion": "falso positivo"},
    )

    assert respuesta["ok"] is False
    assert respuesta["error"]["codigo"] == "excepcion_invalida"  # type: ignore[index]


def test_aliases_mcp_contradictorios_fallan_sin_mutar(tmp_path, monkeypatch) -> None:
    llamadas: list[str] = []
    monkeypatch.setattr(
        servidor_mcp,
        "cerrar_proyecto",
        lambda _raiz, id_tarea, **_opciones: llamadas.append(id_tarea),
    )
    monkeypatch.chdir(tmp_path)

    respuesta = _invocar(
        "cerrar_proyecto",
        {"id_tarea": "TASK-ES", "task": "TASK-EN"},
    )

    assert respuesta["ok"] is False
    assert respuesta["error"]["codigo"] == "argumentos_mcp_conflictivos"  # type: ignore[index]
    assert llamadas == []


def test_cierre_mcp_delega_campos_y_devuelve_esquema(tmp_path, monkeypatch) -> None:
    llamadas = []
    resultado = ResultadoCierre(
        estado=ValorEstadoCierre.APROBADO_CON_EXCEPCIONES,
        id_tarea="TASK-7",
        id_paquete="paquete-7",
        ruta_paquete=None,
        ruta_traspaso=None,
        ejecucion=EjecucionPuertas(
            estado=ValorEstadoPuertas.APROBADO,
            ejecutadas=("test",),
        ),
        bloqueos=(),
    )

    def cerrar(raiz, id_tarea, **opciones):
        llamadas.append((raiz, id_tarea, opciones))
        return resultado

    monkeypatch.setattr(servidor_mcp, "cerrar_proyecto", cerrar)
    monkeypatch.chdir(tmp_path)
    argumentos = {
        "task": "TASK-7",
        "agent": "codex",
        "reviewer": "ana",
        "model": "gpt-5",
        "razon_excepcion": "falso positivo",
        "riesgo_aceptado": "riesgo acotado",
        "control_afectado": "test",
        "referencia_excepcion": "ISSUE-7",
        "revisor_excepcion": "ana",
        "expira_en": "2026-08-01T00:00:00+00:00",
        "condicion_remediacion": "corregir antes del release",
    }

    respuesta = _invocar("cerrar_proyecto", argumentos)

    assert len(llamadas) == 1
    raiz, id_tarea, opciones = llamadas[0]
    assert raiz == tmp_path and id_tarea == "TASK-7"
    assert opciones["agente"] == "codex"
    assert opciones["revisor"] == "ana"
    assert opciones["modelo"] == "gpt-5"
    excepcion = opciones["excepciones"][0]
    assert excepcion.razon == "falso positivo"
    assert excepcion.riesgo_aceptado == "riesgo acotado"
    assert excepcion.control_afectado == "test"
    assert excepcion.referencia == "ISSUE-7"
    assert excepcion.revisor == "ana"
    assert excepcion.expira_en is not None
    assert excepcion.condicion_remediacion == "corregir antes del release"
    assert respuesta["ok"] is True
    assert respuesta["resultado"]["estado"] == "aprobado_con_excepciones"  # type: ignore[index]
    assert respuesta["resultado"]["id_paquete"] == "paquete-7"  # type: ignore[index]


@pytest.mark.parametrize(
    ("herramienta", "atributo", "argumentos", "opciones_esperadas"),
    [
        (
            "record_handoff",
            "registrar_traspaso",
            {"task": "TASK-8", "agent": "codex", "reviewer": "ana"},
            {"agente": "codex", "revisor": "ana"},
        ),
        (
            "build_evidence",
            "crear_evidencia",
            {
                "task": "TASK-8",
                "agent": "codex",
                "reviewer": "ana",
                "model": "gpt-5",
            },
            {"agente": "codex", "revisor": "ana", "modelo": "gpt-5"},
        ),
    ],
)
def test_herramientas_mcp_standalone_delegan_una_vez(
    tmp_path,
    monkeypatch,
    herramienta: str,
    atributo: str,
    argumentos: dict[str, object],
    opciones_esperadas: dict[str, str],
) -> None:
    llamadas = []
    paquete = PaqueteFalso(
        id_paquete="paquete-8",
        ruta=tmp_path / ".tramalia" / "evidencia" / "paquete-8",
    )

    def operar(raiz, id_tarea, **opciones):
        llamadas.append((raiz, id_tarea, opciones))
        return paquete

    monkeypatch.setattr(servidor_mcp, atributo, operar)
    monkeypatch.chdir(tmp_path)

    respuesta = _invocar(herramienta, argumentos)

    assert llamadas == [(tmp_path, "TASK-8", opciones_esperadas)]
    assert respuesta["ok"] is True
    assert respuesta["resultado"]["id_paquete"] == "paquete-8"  # type: ignore[index]
    assert respuesta["resultado"]["ruta"] == ".tramalia/evidencia/paquete-8"  # type: ignore[index]
