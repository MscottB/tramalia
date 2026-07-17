"""Expose Tramalia operations through the optional MCP stdio transport."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, cast

from tramalia.core.errores import (
    ErrorArgumentosMCPConflictivos,
    ErrorExcepcionInvalida,
    ErrorTramalia,
)
from tramalia.core.modelos import ExcepcionFallo, ResultadoCierre
from tramalia.core.operaciones import cerrar_proyecto, crear_evidencia, registrar_traspaso
from tramalia.core.seguridad_entradas import (
    leer_texto_confinado,
    resolver_ruta_confinada,
    sanear_texto_externo,
)

_PRESUPUESTO_HOJAS_MCP = 120 * 1024
_MAXIMO_BYTES_JSON_MCP = 135_168
_MAXIMO_NODOS_MCP = 2_048
_MAXIMA_PROFUNDIDAD_MCP = 64
_NOMBRES_SECRETOS = ("token", "secret", "password", "contrasena", "api_key", "authorization")
_MARCA_TRUNCADO_MAPEO = {"truncado": True}


def _consumir_texto(valor: object, presupuesto: list[int]) -> str:
    if presupuesto[0] <= 2:
        return ""
    limite = min(131_072, presupuesto[0] - 2)
    for _intento in range(10):
        texto = sanear_texto_externo(valor, maximo_bytes=max(1, limite))
        costo = len(json.dumps(texto, ensure_ascii=False).encode("utf-8"))
        if costo <= presupuesto[0]:
            presupuesto[0] -= costo
            return texto
        limite_nuevo = max(1, limite - (costo - presupuesto[0]))
        if limite_nuevo >= limite:
            break
        limite = limite_nuevo
    presupuesto[0] = 0
    return ""


def _clave_publica(clave: object, presupuesto: list[int]) -> str:
    return _consumir_texto(clave, presupuesto)


def _es_clave_secreta(clave: str) -> bool:
    normalizada = "".join(
        caracter for caracter in clave.casefold() if caracter not in {"-", "_", "."}
    )
    return any(nombre.replace("_", "") in normalizada for nombre in _NOMBRES_SECRETOS)


def _consumir_escalar(valor: bool | int | float | None, presupuesto: list[int]) -> object:
    try:
        costo = len(json.dumps(valor, ensure_ascii=False).encode("utf-8"))
    except (OverflowError, ValueError):
        return _consumir_texto("<escalar_no_serializable>", presupuesto)
    if costo <= presupuesto[0]:
        presupuesto[0] -= costo
        return valor
    return _consumir_texto("[TRUNCADO]", presupuesto)


def _valor_publico_recursivo(
    valor: object,
    presupuesto: list[int],
    nodos: list[int],
    vistos: set[int],
    profundidad: int,
) -> object:
    if nodos[0] <= 0 or profundidad >= _MAXIMA_PROFUNDIDAD_MCP:
        return _consumir_texto("[TRUNCADO]", presupuesto)
    nodos[0] -= 1

    es_dataclass = is_dataclass(valor) and not isinstance(valor, type)
    es_compuesto = es_dataclass or isinstance(valor, (Mapping, tuple, list))
    identidad = id(valor)
    if es_compuesto and identidad in vistos:
        return _consumir_texto("[REFERENCIA_CICLICA]", presupuesto)
    if es_compuesto:
        vistos.add(identidad)

    def convertir(dato: object) -> object:
        return _valor_publico_recursivo(
            dato,
            presupuesto,
            nodos,
            vistos,
            profundidad + 1,
        )

    try:
        if es_dataclass:
            resultado_dataclass: dict[str, object] = {}
            for campo in fields(cast(Any, valor)):
                if nodos[0] <= 0:
                    break
                resultado_dataclass[campo.name] = convertir(getattr(valor, campo.name))
            return resultado_dataclass
        if isinstance(valor, Enum):
            return convertir(valor.value)
        if isinstance(valor, Path):
            raiz = Path.cwd().resolve()
            try:
                candidata = (valor if valor.is_absolute() else raiz / valor).resolve(strict=False)
            except OSError:
                return _consumir_texto("[RUTA_FUERA_DEL_PROYECTO]", presupuesto)
            if not candidata.is_relative_to(raiz):
                return _consumir_texto("[RUTA_FUERA_DEL_PROYECTO]", presupuesto)
            return _consumir_texto(candidata.relative_to(raiz).as_posix(), presupuesto)
        if isinstance(valor, datetime):
            return _consumir_texto(valor.isoformat(), presupuesto)
        if isinstance(valor, Mapping):
            resultado: dict[str, object] = {}
            for clave, dato in valor.items():
                if nodos[0] <= 0:
                    break
                clave_publica = _clave_publica(clave, presupuesto)
                if _es_clave_secreta(clave_publica):
                    resultado[clave_publica] = _consumir_texto("[REDACTADO]", presupuesto)
                else:
                    resultado[clave_publica] = convertir(dato)
            return resultado
        if isinstance(valor, (tuple, list)):
            resultado_lista: list[object] = []
            for dato in valor:
                if nodos[0] <= 0:
                    break
                resultado_lista.append(convertir(dato))
            return resultado_lista
        if isinstance(valor, str | bytes | bytearray):
            return _consumir_texto(valor, presupuesto)
        if valor is None or type(valor) in {bool, int, float}:
            return _consumir_escalar(cast(bool | int | float | None, valor), presupuesto)
        return _consumir_texto(valor, presupuesto)
    finally:
        if es_compuesto:
            vistos.discard(identidad)


def _tamano_json(valor: object) -> int:
    return len(json.dumps(valor, ensure_ascii=False).encode("utf-8"))


def _acotar_resultado_json(valor: object, limite: int) -> object:
    if _tamano_json(valor) <= limite:
        return valor
    if isinstance(valor, list):
        resultado: list[object] = []
        marca = dict(_MARCA_TRUNCADO_MAPEO)
        for elemento in valor:
            candidato_lista = [*resultado, elemento, marca]
            if _tamano_json(candidato_lista) > limite:
                break
            resultado.append(elemento)
        return [*resultado, marca]
    if isinstance(valor, dict):
        resultado_mapeo: dict[str, object] = {}
        for clave, elemento in valor.items():
            candidato_mapeo = {
                **resultado_mapeo,
                clave: elemento,
                **_MARCA_TRUNCADO_MAPEO,
            }
            if _tamano_json(candidato_mapeo) > limite:
                break
            resultado_mapeo[clave] = elemento
        return {**resultado_mapeo, **_MARCA_TRUNCADO_MAPEO}
    return "[TRUNCADO]"


def _valor_publico(
    valor: object,
    _presupuesto: list[int] | None = None,
    _nodos: list[int] | None = None,
    _vistos: set[int] | None = None,
    _profundidad: int = 0,
) -> object:
    """Convert a domain value into transport-safe public data."""
    presupuesto = _presupuesto if _presupuesto is not None else [_PRESUPUESTO_HOJAS_MCP]
    nodos = _nodos if _nodos is not None else [_MAXIMO_NODOS_MCP]
    vistos = _vistos if _vistos is not None else set()
    resultado = _valor_publico_recursivo(
        valor,
        presupuesto,
        nodos,
        vistos,
        _profundidad,
    )
    if _presupuesto is not None:
        return resultado
    return _acotar_resultado_json(resultado, _MAXIMO_BYTES_JSON_MCP)


def _restaurar_rutas_error(
    original: object,
    normalizado: object,
    vistos: set[int] | None = None,
) -> object:
    if isinstance(original, Path):
        return original
    if vistos is None:
        vistos = set()
    if isinstance(original, Mapping) and isinstance(normalizado, Mapping):
        identidad = id(original)
        if identidad in vistos:
            return normalizado
        vistos.add(identidad)
        try:
            resultado = dict(normalizado)
            for clave, valor in original.items():
                if type(clave) is not str or clave not in resultado or _es_clave_secreta(clave):
                    continue
                resultado[clave] = _restaurar_rutas_error(
                    valor,
                    resultado[clave],
                    vistos,
                )
            return resultado
        finally:
            vistos.discard(identidad)
    if isinstance(original, (tuple, list)) and isinstance(normalizado, list):
        identidad = id(original)
        if identidad in vistos:
            return normalizado
        vistos.add(identidad)
        try:
            return [
                _restaurar_rutas_error(valor, publico, vistos)
                for valor, publico in zip(original, normalizado, strict=False)
            ]
        finally:
            vistos.discard(identidad)
    return normalizado


def _respuesta(operacion: Callable[[], object]) -> dict[str, object]:
    """Run one domain operation and preserve its typed success or failure."""
    try:
        return {"ok": True, "resultado": _valor_publico(operacion())}
    except ErrorTramalia as error_dominio:
        datos_error: dict[str, object] = dict(error_dominio.como_dict())
        datos_error["ruta"] = error_dominio.ruta
        datos_error["detalles"] = _restaurar_rutas_error(
            error_dominio._detalles_originales,
            error_dominio.detalles,
        )
        return {"ok": False, "error": _valor_publico(datos_error)}
    except Exception as error_inesperado:
        return {
            "ok": False,
            "error": {
                "codigo": "error_interno",
                "mensaje": sanear_texto_externo(error_inesperado),
            },
        }


def _resolver_alias(
    nombre_espanol: str,
    valor_espanol: str,
    nombre_heredado: str,
    valor_heredado: str,
) -> str:
    """Resolve one bilingual alias pair without accepting ambiguity."""
    if valor_espanol and valor_heredado and valor_espanol != valor_heredado:
        raise ErrorArgumentosMCPConflictivos(
            "Los argumentos MCP equivalentes tienen valores contradictorios.",
            "Envia solo el nombre nuevo o el heredado, o usa el mismo valor en ambos.",
            detalles={
                "campo_espanol": nombre_espanol,
                "campo_heredado": nombre_heredado,
            },
        )
    return valor_espanol or valor_heredado


def construir_servidor():
    """Build the optional FastMCP server with stable public tool names."""
    from mcp.server.fastmcp import FastMCP

    from tramalia.core import contexto, detect
    from tramalia.core import doctor as doctor_core
    from tramalia.core.proyecto import exigir_proyecto_gobernado, inspeccionar_estado_proyecto

    servidor = FastMCP("tramalia")

    def _leer(relativa: str, ausente: str) -> str:
        raiz = Path.cwd()
        try:
            ruta = resolver_ruta_confinada(raiz, Path(relativa), permitir_ausente=True)
            if not ruta.exists():
                return sanear_texto_externo(ausente)
            return leer_texto_confinado(raiz, Path(relativa))
        except ErrorTramalia:
            return "[LECTURA_RECHAZADA]"

    @servidor.tool(name="project_status")
    def estado_proyecto_mcp() -> str:
        """Return the detected stack, applicable gates, and initialization state."""
        raiz = Path.cwd()
        tecnologias = detect.detect_stack(raiz)
        capacidades = detect.enabled_features(tecnologias)
        inicializado = inspeccionar_estado_proyecto(raiz).listo
        return sanear_texto_externo(
            f"stack: {', '.join(tecnologias) or '—'}\n"
            f"gates aplicables: {', '.join(capacidades)}\n"
            f"inicializado: {inicializado}"
        )

    @servidor.tool(name="get_agent_rules")
    def obtener_reglas_agentes_mcp() -> str:
        """Return the repository agent rules."""
        return _leer("AGENTS.md", "(sin AGENTS.md; ejecuta `tramalia init`)")

    @servidor.tool(name="get_failed_attempts")
    def obtener_intentos_fallidos_mcp() -> str:
        """Return the recorded failed attempts that should inform new work."""
        return _leer(
            "docs/ai/06-intentos-fallidos.md",
            "(sin registro de intentos fallidos)",
        )

    @servidor.tool(name="get_current_task")
    def obtener_tarea_actual_mcp() -> str:
        """Return the current governed task description."""
        return _leer(".tramalia/current-task.md", "(sin tarea en curso)")

    @servidor.tool(name="doctor")
    def diagnosticar_mcp() -> str:
        """Return required and optional tool availability for the project."""
        reporte = doctor_core.diagnose(Path.cwd())
        lineas = [f"stack: {', '.join(reporte.stack) or '—'}"]
        for estado in reporte.statuses:
            marca = (
                "OK"
                if estado.presente
                else "opcional"
                if estado.herramienta.categoria == "feature"
                else "FALTA"
            )
            lineas.append(
                f"  [{marca}] {estado.herramienta.comando} "
                f"({estado.herramienta.categoria}) — "
                f"{estado.version or estado.herramienta.sugerencia_instalacion}"
            )
        return sanear_texto_externo("\n".join(lineas))

    @servidor.tool(name="record_handoff")
    def registrar_traspaso_mcp(
        task: str,
        agent: str = "",
        reviewer: str = "",
    ) -> dict[str, object]:
        """Create a canonical handoff pack and update its global projection."""
        return _respuesta(
            lambda: registrar_traspaso(Path.cwd(), task, agente=agent, revisor=reviewer)
        )

    @servidor.tool(name="build_evidence")
    def construir_evidencia_mcp(
        task: str = "TASK-000",
        agent: str = "",
        reviewer: str = "",
        model: str = "",
    ) -> dict[str, object]:
        """Create a formal evidence pack without claiming an approved close."""
        return _respuesta(
            lambda: crear_evidencia(
                Path.cwd(),
                task,
                agente=agent,
                revisor=reviewer,
                modelo=model,
            )
        )

    @servidor.tool(name="cerrar_proyecto")
    def cerrar_mcp(
        id_tarea: str = "",
        agente: str = "",
        revisor: str = "",
        modelo: str = "",
        razon_excepcion: str = "",
        riesgo_aceptado: str = "",
        control_afectado: str = "",
        referencia_excepcion: str = "",
        revisor_excepcion: str = "",
        expira_en: str = "",
        condicion_remediacion: str = "",
        task: str = "",
        agent: str = "",
        reviewer: str = "",
        model: str = "",
        allow_fail: bool = False,
    ) -> dict[str, object]:
        """Close a governed task with the same policy used by CLI and TUI."""

        def operacion() -> ResultadoCierre:
            tarea_efectiva = _resolver_alias("id_tarea", id_tarea, "task", task)
            agente_efectivo = _resolver_alias("agente", agente, "agent", agent)
            revisor_efectivo = _resolver_alias("revisor", revisor, "reviewer", reviewer)
            modelo_efectivo = _resolver_alias("modelo", modelo, "model", model)
            excepciones: tuple[ExcepcionFallo, ...] = ()
            campos = (
                razon_excepcion,
                riesgo_aceptado,
                control_afectado,
                referencia_excepcion,
                revisor_excepcion,
                expira_en,
                condicion_remediacion,
            )
            if allow_fail or any(campos):
                try:
                    expiracion = datetime.fromisoformat(expira_en) if expira_en else None
                except ValueError as error_fecha:
                    raise ErrorExcepcionInvalida(
                        "La expiracion MCP no es ISO 8601.",
                        "Usa una fecha con zona horaria o una condicion de remediacion.",
                        detalles={"expira_en": expira_en},
                    ) from error_fecha
                excepciones = (
                    ExcepcionFallo(
                        razon_excepcion,
                        riesgo_aceptado,
                        control_afectado,
                        referencia_excepcion,
                        revisor_excepcion or revisor_efectivo,
                        expiracion,
                        condicion_remediacion or None,
                    ),
                )
            return cerrar_proyecto(
                Path.cwd(),
                tarea_efectiva,
                agente=agente_efectivo,
                revisor=revisor_efectivo,
                modelo=modelo_efectivo,
                excepciones=excepciones,
            )

        return _respuesta(operacion)

    @servidor.tool(name="build_context")
    def construir_contexto_mcp() -> str:
        """Regenerate derived repository context files."""
        raiz = Path.cwd()
        exigir_proyecto_gobernado(raiz)
        resultado = contexto.construir_contexto(raiz)
        return sanear_texto_externo(
            "generado: " + ", ".join(ruta.name for ruta in resultado.archivos)
        )

    return servidor


def ejecutar() -> None:
    """Run the MCP server over stdio."""
    construir_servidor().run()


if __name__ == "__main__":
    ejecutar()
