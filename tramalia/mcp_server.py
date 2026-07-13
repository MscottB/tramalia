"""Expose Tramalia operations through the optional MCP stdio transport."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from tramalia.core.errores import (
    ErrorArgumentosMCPConflictivos,
    ErrorExcepcionInvalida,
    ErrorTramalia,
)
from tramalia.core.modelos import ExcepcionFallo, ResultadoCierre
from tramalia.core.operaciones import cerrar_proyecto, crear_evidencia, registrar_traspaso


def _valor_publico(valor: object) -> object:
    """Convert a domain value into transport-safe public data."""
    if is_dataclass(valor) and not isinstance(valor, type):
        return {campo.name: _valor_publico(getattr(valor, campo.name)) for campo in fields(valor)}
    if isinstance(valor, Enum):
        return _valor_publico(valor.value)
    if isinstance(valor, Path):
        try:
            return valor.relative_to(Path.cwd()).as_posix()
        except ValueError:
            return str(valor)
    if isinstance(valor, datetime):
        return valor.isoformat()
    if isinstance(valor, Mapping):
        return {str(clave): _valor_publico(dato) for clave, dato in valor.items()}
    if isinstance(valor, (tuple, list)):
        return [_valor_publico(dato) for dato in valor]
    return valor


def _respuesta(operacion: Callable[[], object]) -> dict[str, object]:
    """Run one domain operation and preserve its typed success or failure."""
    try:
        return {"ok": True, "resultado": _valor_publico(operacion())}
    except ErrorTramalia as error_dominio:
        return {"ok": False, "error": _valor_publico(error_dominio.como_dict())}


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
        ruta = Path.cwd() / relativa
        return ruta.read_text(encoding="utf-8") if ruta.exists() else ausente

    @servidor.tool(name="project_status")
    def estado_proyecto_mcp() -> str:
        """Return the detected stack, applicable gates, and initialization state."""
        raiz = Path.cwd()
        tecnologias = detect.detect_stack(raiz)
        capacidades = detect.enabled_features(tecnologias)
        inicializado = inspeccionar_estado_proyecto(raiz).listo
        return (
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
        return "\n".join(lineas)

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
        return "generado: " + ", ".join(ruta.name for ruta in resultado.archivos)

    return servidor


def ejecutar() -> None:
    """Run the MCP server over stdio."""
    construir_servidor().run()


if __name__ == "__main__":
    ejecutar()
