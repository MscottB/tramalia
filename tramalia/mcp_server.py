"""Tramalia MCP — fachada (nivel 1).

NO implementa memoria ni lógica nueva: expone como herramientas MCP nativas las
mismas funciones del CLI/core, para que cualquier agente compatible las invoque
sin hacer shell-out ni aprender el formato de los archivos.

Se levanta con `tramalia mcp` (stdio). Requiere el extra: pip install "tramalia-cli[mcp]".
"""

from __future__ import annotations

from pathlib import Path

from tramalia.core.operaciones import (
    cerrar_proyecto as ejecutar_cierre,
)
from tramalia.core.operaciones import (
    construir_excepciones_fallo,
    crear_evidencia,
    registrar_traspaso,
)


def build_server():
    from mcp.server.fastmcp import FastMCP

    from tramalia.core import contexto, detect
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
        for estado in report.statuses:
            mark = (
                "OK"
                if estado.presente
                else "opcional"
                if estado.herramienta.categoria == "feature"
                else "FALTA"
            )
            lines.append(
                f"  [{mark}] {estado.herramienta.comando} "
                f"({estado.herramienta.categoria}) — "
                f"{estado.version or estado.herramienta.sugerencia_instalacion}"
            )
        return "\n".join(lines)

    @server.tool(name="record_handoff")
    def registrar_traspaso_mcp(
        task: str,
        agent: str = "",
        reviewer: str = "",
    ) -> dict[str, object]:
        """Publica un traspaso canonico dentro de un paquete de evidencia v1."""
        root = Path.cwd()
        paquete = registrar_traspaso(root, task, agente=agent, revisor=reviewer)
        return {
            "operacion": "traspaso",
            "id_paquete": paquete.id_paquete,
            "ruta_paquete": paquete.ruta.relative_to(root).as_posix(),
        }

    @server.tool(name="build_evidence")
    def construir_evidencia_mcp(
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
        excepciones = construir_excepciones_fallo(
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
        resultado = contexto.construir_contexto(root)
        return "generado: " + ", ".join(ruta.name for ruta in resultado.archivos)

    return server


def run() -> None:
    build_server().run()


if __name__ == "__main__":
    run()
