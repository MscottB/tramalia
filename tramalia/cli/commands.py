"""Implementación de cada comando. La mayoría hace *shell-out* transparente a la
herramienta real (regla de diseño: el façade muestra el comando, pasa la salida
tal cual y nunca esconde errores). doctor/detect son lógica propia.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from tramalia.cli import menu, render
from tramalia.core import doctor as doctor_core
from tramalia.core import proc
from tramalia.core.detect import detect_stack, enabled_features


def _is_initialized(root: Path) -> bool:
    return (root / "AGENTS.md").exists() or (root / ".tramalia").exists()


def _run(cmd: list[str]) -> int:
    """Ejecuta un comando externo mostrando exactamente su salida."""
    render.info(f"→ {' '.join(cmd)}")
    try:
        return proc.run(cmd).returncode
    except FileNotFoundError:
        render.err(f"no se encontró '{cmd[0]}'. Corre `tramalia doctor` para instalarlo.")
        return 127


# --------------------------------------------------------------------------- #

def cmd_doctor(args) -> int:
    report = doctor_core.diagnose(Path.cwd())
    code = render.doctor(report)
    if getattr(args, "fix", False) and report.missing_blocking:
        if doctor_core.fix(report):
            render.info("`mise install` ejecutado; re-evaluando…")
            return render.doctor(doctor_core.diagnose(Path.cwd()))
        render.warn("no se pudo auto-instalar (instala primero mise — ver enlace arriba).")
    return code


def cmd_detect(args) -> int:
    root = Path.cwd()
    stack = detect_stack(root)
    feats = enabled_features(stack)
    render.header(root.name, stack, _is_initialized(root))
    render.info(f"gates aplicables: {', '.join(feats)}")
    return 0


def cmd_init(args) -> int:
    from tramalia.core import scaffold
    root = Path.cwd()
    stack = detect_stack(root)
    answers = {
        "project_name": root.name,
        "stacks": stack,
        "features": enabled_features(stack),
        "primary_agent": "codex",
        "reviewer_agent": "claude",
        "with_headroom": getattr(args, "with_headroom", False),
    }
    render.header(root.name, stack, _is_initialized(root))
    results = scaffold.scaffold(root, answers)
    for rel, state in results:
        (render.ok if state == "creado" else render.info)(f"{state:>6}  {rel}")
    creados = sum(1 for _, s in results if s == "creado")
    render.ok(f"init listo: {creados} creados, {len(results) - creados} ya existían.")
    render.info("revisa AGENTS.md y mise.toml; instala lo que falte con `tramalia doctor`.")
    return 0


def cmd_gates(args) -> int:
    if shutil.which("mise") is None:
        render.err("falta 'mise'. Corre `tramalia doctor` para los pasos de instalación.")
        return 127
    return _run(["mise", "run", "gates"])


def cmd_context(args) -> int:
    from tramalia.core import context
    results = context.build_context(Path.cwd())
    for rel in results:
        render.ok(f"generado  .tramalia/context/{rel}")
    if shutil.which("repomix") is None:
        render.info("repomix ausente: project-map se generó con el árbol stdlib.")
        render.info("para snapshot completo: `mise use npm:repomix`.")
    return 0


def _engram_save(title: str, body: str) -> None:
    """Export opt-in a Engram (memoria persistente N2). Nunca automático."""
    if shutil.which("engram") is None:
        render.warn("engram no está instalado; se omite el export a memoria persistente.")
        return
    if _run(["engram", "save", title, body]) == 0:
        render.ok("exportado a Engram (memoria persistente N2).")


def cmd_evidence(args) -> int:
    from tramalia.core import evidence
    task = getattr(args, "task", None) or "TASK-000"
    target = evidence.build_evidence(Path.cwd(), task)
    render.ok(f"evidence pack creado: {target.relative_to(Path.cwd())}")
    render.info("completa summary.md, risks.md y next-steps.md antes de cerrar.")
    if getattr(args, "engram", False):
        _engram_save(f"evidence {task}", f"Evidence pack de {task} en {target}.")
    return 0


def cmd_handoff(args) -> int:
    from tramalia.core import handoff
    task = getattr(args, "task", None) or "TASK-000"
    agent = getattr(args, "agent", None) or ""
    reviewer = getattr(args, "reviewer", None) or ""
    path = handoff.new_handoff(Path.cwd(), task, agent, reviewer)
    render.ok(f"handoff agregado a {path.relative_to(Path.cwd())}")
    if getattr(args, "engram", False):
        _engram_save(f"handoff {task}",
                     f"Handoff de {task}; ejecutor {agent or '?'}, revisor {reviewer or '?'}.")
    return 0


def cmd_close(args) -> int:
    from tramalia.core import governance
    task = getattr(args, "task", None) or "TASK-000"
    res = governance.close(
        Path.cwd(), task,
        getattr(args, "agent", None) or "",
        getattr(args, "reviewer", None) or "",
        allow_fail=getattr(args, "allow_fail", False),
    )
    if not res.gates_ran:
        render.warn("gates no ejecutados (mise ausente); registrado como excepción en el pack.")
    else:
        for name, code, _ in res.gates:
            (render.ok if code == 0 else render.err)(
                f"gate {name}: {'ok' if code == 0 else 'FALLA'}")
    render.ok(f"evidence: {res.evidence_dir.relative_to(Path.cwd())}  (estado: {res.status})")
    render.ok(f"handoff: {res.handoff_path.relative_to(Path.cwd())}")
    render.info(f"metadata: {(res.evidence_dir / 'metadata.json').relative_to(Path.cwd())}")
    if getattr(args, "engram", False):
        _engram_save(f"close {task}",
                     f"Cierre de {task}; estado {res.status}; fallidos: {', '.join(res.failed) or 'ninguno'}.")
    if res.blocked:
        render.err(f"cierre BLOQUEADO por gates fallidos: {', '.join(res.failed)}.")
        render.info("usa --allow-fail solo con una excepción documentada en risks.md.")
        return 1
    render.ok(f"tarea {task} cerrada con evidencia verificable.")
    return 0


_LOG_MARKS = {
    "passed": "✓ passed",
    "passed_with_exceptions": "⚠ con excepciones (forzado)",
    "blocked": "✗ bloqueado",
    "no_gates": "○ sin gates",
    None: "○ —",
}


def cmd_log(args) -> int:
    from tramalia.core import governance
    entries = governance.read_log(Path.cwd())
    if not entries:
        render.info("sin cierres registrados todavía. Usa `tramalia close`.")
        return 0
    render.info(f"pista de auditoría — {len(entries)} cierres (más reciente primero):")
    for e in entries:
        mark = _LOG_MARKS.get(e.get("status"), "○ —")
        extra = f"  ·  {e['agent']}" if e.get("agent") else ""
        render.ok(f"{e['id']}  ·  {mark}{extra}")
    return 0


def cmd_sync(args) -> int:
    if shutil.which("rulesync") is None:
        render.err("falta 'rulesync'. Instálalo con: mise use npm:rulesync")
        return 127
    if not (Path.cwd() / "AGENTS.md").exists():
        render.err("no hay AGENTS.md. Ejecuta `tramalia init` primero.")
        return 1
    # CLAUDE.md/Codex no se incluyen: ya leen AGENTS.md nativamente.
    # Targets válidos en rulesync v9: copilot, cursor, cline, antigravity-cli, zed, junie, warp, …
    targets = getattr(args, "to", None) or "copilot,cursor,cline"
    render.info(f"convirtiendo AGENTS.md → {targets} (rulesync)")
    return _run(["rulesync", "convert", "--from", "agentsmd",
                 "--to", targets, "--features", "rules"])


def cmd_skills(args) -> int:
    from tramalia.core import skills
    root = Path.cwd()
    action = getattr(args, "action", None) or "sync"

    if action == "list":
        items = skills.read_skills(root)
        if not items:
            render.info("no hay skills declaradas en .tramalia/skills.toml")
        for s in items:
            render.ok(f"{s.get('name', '?')}  ←  {s.get('source', '')}")
        return 0

    results = skills.sync_skills(root)
    if not results:
        render.info("no hay skills declaradas en .tramalia/skills.toml (todas comentadas).")
        return 0
    for name, act in results:
        ok = act in ("clonada", "actualizada")
        (render.ok if ok else render.warn)(f"{act:>12}  {name}")
    return 0


def cmd_update(args) -> int:
    render.info("update = mise upgrade + copier update + skills sync")
    code = 0
    if shutil.which("mise"):
        code |= _run(["mise", "upgrade"])
    else:
        render.warn("mise ausente; omitiendo `mise upgrade`.")
    return code


def cmd_mcp(args) -> int:
    try:
        import mcp  # noqa: F401
    except ImportError:
        render.err('falta el SDK MCP. Instálalo con: pip install "tramalia-cli[mcp]"')
        return 127
    from tramalia import mcp_server
    render.info("levantando Tramalia MCP (stdio)… Ctrl+C para detener.")
    mcp_server.run()
    return 0


def cmd_menu(args) -> int:
    root = Path.cwd()
    stack = detect_stack(root)
    render.header(root.name, stack, _is_initialized(root))
    choice = menu.choose()
    if choice == "quit":
        return 0
    return dispatch(choice, args)


_HANDLERS = {
    "doctor": cmd_doctor,
    "detect": cmd_detect,
    "init": cmd_init,
    "gates": cmd_gates,
    "context": cmd_context,
    "evidence": cmd_evidence,
    "handoff": cmd_handoff,
    "close": cmd_close,
    "log": cmd_log,
    "sync": cmd_sync,
    "skills": cmd_skills,
    "update": cmd_update,
    "mcp": cmd_mcp,
    "menu": cmd_menu,
}


def dispatch(command: str, args) -> int:
    handler = _HANDLERS.get(command)
    if handler is None:
        render.err(f"comando desconocido: {command}")
        return 2
    return handler(args)
