import asyncio
import json
import re
from pathlib import Path

import pytest

from tramalia.core.errores import ErrorTramalia
from tramalia.core.modelos import ExcepcionFallo
from tramalia.core.scaffold import ResultadoMergeMCP, _merge_mcp, build_mcp_json, scaffold
from tramalia.core.versiones_herramientas import FUENTE_SERENA, SHA_SERENA, VERSION_SERENA
from tramalia.mcp_server import _respuesta, _valor_publico, construir_servidor

pytestmark = pytest.mark.integracion


def _respuestas(**adicionales: object) -> dict[str, object]:
    respuestas: dict[str, object] = {
        "project_name": "demo",
        "stacks": ["python"],
        "features": [],
        "primary_agent": "codex",
        "reviewer_agent": "claude",
    }
    respuestas.update(adicionales)
    return respuestas


def test_merge_mcp_conflicto_homonimo_conserva_bytes() -> None:
    original = '{\n  "mcpServers": {"serena": {"command": "otro", "args": ["mcp"]}}\n}\n'

    resultado = _merge_mcp(
        original,
        {"serena": {"command": "uvx", "args": ["--from", FUENTE_SERENA]}},
    )

    assert isinstance(resultado, ResultadoMergeMCP)
    assert resultado.estado == "conflicto"
    assert resultado.texto == original


@pytest.mark.parametrize(
    "original",
    ("{json-invalido", "[]", '{"mcpServers": []}'),
)
def test_merge_mcp_json_invalido_conserva_bytes(original: str) -> None:
    resultado = _merge_mcp(original, {"serena": {"command": "uvx", "args": []}})

    assert resultado.estado == "json_invalido"
    assert resultado.texto == original


@pytest.mark.parametrize(
    "original",
    (
        '{"mcpServers":{"propio":{"command":"propio","args":[]}},"mcpServers":{}}',
        '{"mcpServers":{"propio":{"command":"primero","command":"segundo","args":[]}}}',
    ),
    ids=("raiz", "anidado"),
)
def test_merge_mcp_rechaza_claves_duplicadas_en_cualquier_profundidad(original: str) -> None:
    resultado = _merge_mcp(original, {"serena": {"command": "uvx", "args": []}})

    assert resultado.estado == "json_invalido"
    assert resultado.texto == original


@pytest.mark.parametrize(
    "literal",
    ("NaN", "Infinity", "-Infinity", "1e999"),
    ids=("nan", "infinito", "infinito-negativo", "desbordado"),
)
def test_merge_mcp_rechaza_numeros_no_finitos_y_conserva_bytes(literal: str) -> None:
    original = '{"mcpServers":{},"valor":' + literal + "}"

    resultado = _merge_mcp(original, {})

    assert resultado.estado == "json_invalido"
    assert resultado.texto == original


def test_merge_mcp_acepta_numero_finito_y_conserva_json_legitimo() -> None:
    original = '{"mcpServers":{},"valor":1.25}'

    resultado = _merge_mcp(original, {})

    assert resultado.estado == "sin_cambios"
    assert resultado.texto == original


def test_merge_mcp_identico_conserva_bytes_y_declara_sin_cambios() -> None:
    servidor = {"command": "uvx", "args": ["--from", FUENTE_SERENA]}
    original = json.dumps({"mcpServers": {"serena": servidor}}, separators=(",", ":"))

    resultado = _merge_mcp(original, {"serena": servidor})

    assert resultado.estado == "sin_cambios"
    assert resultado.texto == original


def test_merge_mcp_fusiona_sin_perder_servidor_usuario() -> None:
    original = json.dumps({"mcpServers": {"propio": {"command": "propio", "args": []}}})

    resultado = _merge_mcp(
        original,
        {"serena": {"command": "uvx", "args": ["--from", FUENTE_SERENA]}},
    )

    assert resultado.estado == "fusionado"
    datos = json.loads(resultado.texto)
    assert datos["mcpServers"]["propio"] == {"command": "propio", "args": []}
    assert "serena" in datos["mcpServers"]


def test_scaffold_adopt_conflicto_mcp_conserva_bytes_y_estado_publico(
    tmp_path: Path,
) -> None:
    ruta = tmp_path / ".mcp.json"
    original = '{"mcpServers":{"serena":{"command":"otro","args":[]}}}\n'
    ruta.write_text(original, encoding="utf-8")

    resultados = dict(scaffold(tmp_path, _respuestas(adopt=True)))

    assert resultados[".mcp.json"] == "existe"
    assert ruta.read_text(encoding="utf-8") == original


def test_serena_usa_version_y_sha_completos_exactos() -> None:
    assert VERSION_SERENA == "1.6.0"
    assert SHA_SERENA == "93b9544ea9def8e93cb6a90f8ea67befe3c8fee4"
    assert FUENTE_SERENA == (
        "git+https://github.com/oraios/serena.git@93b9544ea9def8e93cb6a90f8ea67befe3c8fee4"
    )
    contenido = build_mcp_json({"stacks": [], "features": ()})
    datos = json.loads(contenido)
    argumentos = datos["mcpServers"]["serena"]["args"]
    assert FUENTE_SERENA in argumentos
    for argumento in argumentos:
        if isinstance(argumento, str) and argumento.startswith("git+https://"):
            assert re.search(r"@[0-9a-f]{40}$", argumento)


def test_valor_publico_sanea_hojas_sin_aplanar_estructura() -> None:
    valor = {
        "salida": "\x1b[31mrojo\x1b[0m",
        "anidado": ["authorization=valor-real", {"linea": "x" * 20_000}],
    }

    resultado = _valor_publico(valor)

    assert isinstance(resultado, dict)
    assert isinstance(resultado["anidado"], list)
    serializado = json.dumps(resultado, ensure_ascii=False).encode("utf-8")
    assert b"valor-real" not in serializado
    assert b"\x1b" not in serializado
    assert len(serializado) <= 132 * 1024


def test_valor_publico_oculta_path_fuera_del_proyecto(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raiz = tmp_path / "proyecto"
    raiz.mkdir()
    externa = tmp_path / "secreto.txt"
    externa.write_text("secreto", encoding="utf-8")
    monkeypatch.chdir(raiz)

    assert _valor_publico(externa) == "[RUTA_FUERA_DEL_PROYECTO]"


def test_valor_publico_limita_resultado_serializado() -> None:
    resultado = _valor_publico({"salida": ("x" * 1_000 + "\n") * 200})

    assert len(json.dumps(resultado, ensure_ascii=False).encode("utf-8")) <= 132 * 1024


def test_valor_publico_limita_estructura_con_muchas_hojas_numericas() -> None:
    resultado = _valor_publico(list(range(50_000)))

    assert len(json.dumps(resultado, ensure_ascii=False).encode("utf-8")) <= 132 * 1024


def _excepcion_control(texto: str) -> ExcepcionFallo:
    return ExcepcionFallo(
        razon=texto,
        riesgo_aceptado=texto,
        control_afectado=texto,
        referencia=texto,
        revisor=texto,
        condicion_remediacion=texto,
    )


def test_valor_publico_limita_bytes_json_reales_de_clases_de_datos() -> None:
    excepcion = _excepcion_control("x" * 70)

    resultado = _valor_publico([excepcion] * 300)
    serializado = json.dumps(resultado, ensure_ascii=False).encode("utf-8")

    assert isinstance(resultado, list)
    assert all(isinstance(elemento, dict) for elemento in resultado)
    assert resultado[-1] == {"truncado": True}
    assert len(serializado) <= 135_168


def test_valor_publico_preserva_estructura_normal_de_clase_de_datos() -> None:
    resultado = _valor_publico([_excepcion_control("control")])

    assert isinstance(resultado, list)
    assert len(resultado) == 1
    assert isinstance(resultado[0], dict)
    assert resultado[0]["razon"] == "control"
    assert resultado[0]["condicion_remediacion"] == "control"


def test_respuesta_error_confina_rutas_anidadas_y_preserva_contrato_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raiz = tmp_path / "proyecto"
    raiz.mkdir()
    monkeypatch.chdir(raiz)
    externa = tmp_path / "archivo-externo.txt"
    relativa = Path("docs/control.md")
    error = ErrorTramalia(
        "fallo controlado",
        "reintenta",
        detalles={
            "contexto": {
                "archivo_externo": externa,
                "archivo_relativo": relativa,
            }
        },
    )

    def fallar() -> object:
        raise error

    respuesta = _respuesta(fallar)
    detalles_mcp = respuesta["error"]["detalles"]["contexto"]
    detalles_cli = error.como_dict()["detalles"]["contexto"]

    assert (
        detalles_mcp["archivo_externo"] == "[RUTA_FUERA_DEL_PROYECTO]",
        detalles_mcp["archivo_relativo"] == relativa.as_posix(),
        isinstance(detalles_cli["archivo_externo"], str),
        isinstance(detalles_cli["archivo_relativo"], str),
    ) == (True, True, True, True)
    json.dumps(error.como_dict(), ensure_ascii=False, allow_nan=False)


def _crear_symlink_o_saltar(enlace: Path, destino: Path) -> None:
    try:
        enlace.symlink_to(destino)
    except OSError as error_symlink:
        pytest.skip(f"El entorno no permite symlinks: {error_symlink}")


def test_herramienta_lectura_no_sigue_agents_symlink_fuera_del_proyecto(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raiz = tmp_path / "proyecto"
    raiz.mkdir()
    secreto = tmp_path / "secreto.txt"
    contenido_secreto = "token=secreto-no-filtrar"
    secreto.write_text(contenido_secreto, encoding="utf-8")
    _crear_symlink_o_saltar(raiz / "AGENTS.md", secreto)
    monkeypatch.chdir(raiz)

    contenido, _estructurado = asyncio.run(construir_servidor().call_tool("get_agent_rules", {}))
    serializado = "\n".join(bloque.text for bloque in contenido)

    assert contenido_secreto not in serializado
    assert str(secreto) not in serializado
    assert "LECTURA_RECHAZADA" in serializado
