"""Tramalia MCP — fachada (nivel 1).

NO implementa memoria ni lógica nueva: expone como herramientas MCP nativas las
mismas funciones del CLI/core, para que cualquier agente compatible las invoque
sin hacer shell-out ni aprender el formato de los archivos.

Se levanta con `tramalia mcp` (stdio). Requiere el extra: pip install "tramalia-cli[mcp]".
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from tramalia.core.errores import ErrorExcepcionInvalida
from tramalia.core.modelos import ExcepcionFallo
from tramalia.core.operaciones import (
    cerrar_proyecto as ejecutar_cierre,
)
from tramalia.core.operaciones import (
    crear_evidencia,
    registrar_traspaso,
)


def _construir_excepciones_mcp(
    *,
    permitir_fallo: bool,
    razon: str,
    riesgo_aceptado: str,
    control_afectado: str,
    referencia: str,
    revisor_excepcion: str,
    revisor_predeterminado: str,
    expira_en: str,
    condicion_remediacion: str,
) -> tuple[ExcepcionFallo, ...]:
    """Convierte los argumentos MCP en una excepcion completa y auditable."""
    campos = (
        razon,
        riesgo_aceptado,
        control_afectado,
        referencia,
        revisor_excepcion,
        expira_en,
        condicion_remediacion,
    )
    if not permitir_fallo and not any(campo.strip() for campo in campos):
        return ()

    expiracion = None
    if expira_en.strip():
        try:
            expiracion = datetime.fromisoformat(expira_en.strip())
        except ValueError as error:
            raise ErrorExcepcionInvalida(
                "La expiracion de la excepcion no usa un formato ISO 8601 valido.",
                "Usa una fecha con zona horaria, por ejemplo 2026-08-01T00:00:00+00:00.",
                detalles={"campos": ["expira_en"]},
            ) from error

    # El modelo valida que todos los campos obligatorios esten presentes, que la
    # fecha incluya zona horaria y que exista expiracion o condicion de remediacion.
    return (
        ExcepcionFallo(
            razon=razon,
            riesgo_aceptado=riesgo_aceptado,
            control_afectado=control_afectado,
            referencia=referencia,
            revisor=revisor_excepcion.strip() or revisor_predeterminado,
            expira_en=expiracion,
            condicion_remediacion=condicion_remediacion or None,
        ),
    )


def build_server():
    from mcp.server.fastmcp import FastMCP

    from tramalia.core import context as context_core
    from tramalia.core import detect
    from tramalia.core import doctor as doctor_core
    from tramalia.core.proyecto import exigir_proyecto_gobernado, inspeccionar_estado_proyecto

    server = FastMCP("tramalia")

    def _read(rel: str, missing: str) -> str:
        f = Path.cwd() / rel
        return f.read_text(encoding="utf-8") if f.exists() else missing

    @server.tool()
    def project_status() -> str:
        """Estado del proyecto: stack detectado, gates aplicables e inicialización."""
        root = Path.cwd()
        stack = detect.detect_stack(root)
        feats = detect.enabled_features(stack)
        initialized = inspeccionar_estado_proyecto(root).listo
        return (
            f"stack: {', '.join(stack) or '—'}\n"
            f"gates aplicables: {', '.join(feats)}\n"
            f"inicializado: {initialized}"
        )

    @server.tool()
    def get_agent_rules() -> str:
        """Reglas del proyecto para agentes (contenido de AGENTS.md)."""
        return _read("AGENTS.md", "(sin AGENTS.md; ejecuta `tramalia init`)")

    @server.tool()
    def get_failed_attempts() -> str:
        """Intentos fallidos previos. Léelos ANTES de proponer una solución."""
        return _read("docs/ai/06-intentos-fallidos.md", "(sin registro de intentos fallidos)")

    @server.tool()
    def get_current_task() -> str:
        """Tarea en curso (.tramalia/current-task.md)."""
        return _read(".tramalia/current-task.md", "(sin tarea en curso)")

    @server.tool()
    def doctor() -> str:
        """Diagnóstico de herramientas requeridas/opcionales para este proyecto."""
        report = doctor_core.diagnose(Path.cwd())
        lines = [f"stack: {', '.join(report.stack) or '—'}"]
        for s in report.statuses:
            mark = "OK" if s.present else ("opcional" if s.tool.category == "feature" else "FALTA")
            lines.append(
                f"  [{mark}] {s.tool.cmd} ({s.tool.category}) — {s.version or s.tool.install_hint}"
            )
        return "\n".join(lines)

    @server.tool()
    def record_handoff(task: str, agent: str = "", reviewer: str = "") -> dict[str, object]:
        """Publica un traspaso canonico dentro de un paquete de evidencia v1."""
        root = Path.cwd()
        paquete = registrar_traspaso(root, task, agente=agent, revisor=reviewer)
        return {
            "operacion": "traspaso",
            "id_paquete": paquete.id_paquete,
            "ruta_paquete": paquete.ruta.relative_to(root).as_posix(),
        }

    @server.tool()
    def build_evidence(
        task: str = "TASK-000",
        agent: str = "",
        reviewer: str = "",
        model: str = "",
    ) -> dict[str, object]:
        """Publica evidencia standalone sin afirmar que el cierre fue aprobado."""
        root = Path.cwd()
        paquete = crear_evidencia(
            root,
            task,
            agente=agent,
            revisor=reviewer,
            modelo=model,
        )
        return {
            "operacion": "evidencia",
            "id_paquete": paquete.id_paquete,
            "ruta_paquete": paquete.ruta.relative_to(root).as_posix(),
        }

    @server.tool()
    def cerrar_proyecto(
        task: str,
        agent: str = "",
        reviewer: str = "",
        model: str = "",
        allow_fail: bool = False,
        razon_excepcion: str = "",
        riesgo_aceptado: str = "",
        control_afectado: str = "",
        referencia_excepcion: str = "",
        revisor_excepcion: str = "",
        expira_en: str = "",
        condicion_remediacion: str = "",
    ) -> dict[str, object]:
        """Cierra una tarea con puertas y excepciones completas, si corresponden."""
        root = Path.cwd()
        excepciones = _construir_excepciones_mcp(
            permitir_fallo=allow_fail,
            razon=razon_excepcion,
            riesgo_aceptado=riesgo_aceptado,
            control_afectado=control_afectado,
            referencia=referencia_excepcion,
            revisor_excepcion=revisor_excepcion,
            revisor_predeterminado=reviewer,
            expira_en=expira_en,
            condicion_remediacion=condicion_remediacion,
        )
        resultado = ejecutar_cierre(
            root,
            task,
            agente=agent,
            revisor=reviewer,
            modelo=model,
            excepciones=excepciones,
        )
        return {
            "estado": resultado.estado.value,
            "id_paquete": resultado.id_paquete,
            "bloqueos": list(resultado.bloqueos),
            "aprobado": resultado.aprobado,
        }

    @server.tool()
    def build_context() -> str:
        """Regenera la memoria derivada (tech-stack, project-map) para ahorrar tokens."""
        root = Path.cwd()
        exigir_proyecto_gobernado(root)
        results = context_core.build_context(root)
        return "generado: " + ", ".join(results)

    return server


def run() -> None:
    build_server().run()


if __name__ == "__main__":
    run()
