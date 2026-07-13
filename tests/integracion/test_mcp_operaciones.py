import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("mcp")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def _invocar(
    nombre: str,
    argumentos: dict[str, object],
    raiz: Path,
) -> dict[str, object]:
    raiz_codigo = Path(__file__).parents[2]
    parametros = StdioServerParameters(
        command=sys.executable,
        args=["-m", "tramalia.mcp_server"],
        env={**os.environ, "PYTHONPATH": str(raiz_codigo)},
        cwd=str(raiz),
    )
    async with stdio_client(parametros) as (lector, escritor):
        async with ClientSession(lector, escritor) as sesion:
            await sesion.initialize()
            resultado = await sesion.call_tool(nombre, argumentos)
    return json.loads(resultado.content[0].text)


@pytest.mark.integracion
@pytest.mark.opcional
def test_herramienta_mcp_evidencia_sin_inicializar_devuelve_error_tipado(
    tmp_path: Path,
) -> None:
    respuesta = asyncio.run(_invocar("build_evidence", {"task": "TASK-1"}, tmp_path))
    assert respuesta["ok"] is False
    assert respuesta["error"]["codigo"] == "proyecto_no_gobernado"  # type: ignore[index]


@pytest.mark.integracion
@pytest.mark.opcional
def test_herramienta_mcp_real_crea_evidencia_via_operacion(
    proyecto_listo: Path,
) -> None:
    respuesta = asyncio.run(_invocar("build_evidence", {"task": "TASK-2"}, proyecto_listo))
    assert respuesta["ok"] is True
    ruta = proyecto_listo / str(respuesta["resultado"]["ruta"])  # type: ignore[index]
    assert ruta.is_dir()
    assert len(list((proyecto_listo / ".tramalia" / "evidencia").iterdir())) == 1
    assert json.loads((ruta / "metadatos.json").read_text(encoding="utf-8"))["id_tarea"] == "TASK-2"


@pytest.mark.integracion
@pytest.mark.opcional
def test_herramienta_mcp_cierre_con_excepcion_incompleta_devuelve_error_tipado(
    proyecto_listo: Path,
) -> None:
    respuesta = asyncio.run(
        _invocar(
            "cerrar_proyecto",
            {"id_tarea": "TASK-3", "razon_excepcion": "riesgo temporal"},
            proyecto_listo,
        )
    )
    assert respuesta["ok"] is False
    assert respuesta["error"]["codigo"] == "excepcion_invalida"  # type: ignore[index]
    assert not (proyecto_listo / ".tramalia" / "evidencia").exists()
