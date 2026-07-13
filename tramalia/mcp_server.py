"""Tramalia MCP — fachada (nivel 1).

NO implementa memoria ni lógica nueva: expone como herramientas MCP nativas las
mismas funciones del CLI/core, para que cualquier agente compatible las invoque
sin hacer shell-out ni aprender el formato de los archivos.

Se levanta con `tramalia mcp` (stdio). Requiere el extra: pip install "tramalia-cli[mcp]".
"""

from __future__ import annotations

from pathlib import Path


def build_server():
    from mcp.server.fastmcp import FastMCP

    from tramalia.core import context as context_core
    from tramalia.core import detect
    from tramalia.core import doctor as doctor_core
    from tramalia.core import evidence as evidence_core
    from tramalia.core import handoff as handoff_core
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
    def record_handoff(task: str, agent: str = "", reviewer: str = "") -> str:
        """Agrega un handoff estructurado a docs/ai/07-handoff-agentes.md."""
        root = Path.cwd()
        exigir_proyecto_gobernado(root)
        path = handoff_core.new_handoff(root, task, agent, reviewer)
        return f"handoff agregado a {path}"

    @server.tool()
    def build_evidence(task: str = "TASK-000") -> str:
        """Crea el evidence pack de cierre de una tarea."""
        root = Path.cwd()
        exigir_proyecto_gobernado(root)
        target = evidence_core.build_evidence(root, task)
        return f"evidence pack creado en {target}"

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
