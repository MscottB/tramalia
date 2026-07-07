"""Implementación de cada comando. La mayoría hace *shell-out* transparente a la
herramienta real (regla de diseño: el façade muestra el comando, pasa la salida
tal cual y nunca esconde errores). doctor/detect son lógica propia.
"""

from __future__ import annotations

import shutil
import sys
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
    # snapshot para los agentes: qué está instalado (AGENTS.md les dice leerlo)
    doctor_core.write_snapshot(report, Path.cwd())
    code = render.doctor(report)
    if not getattr(args, "fix", False):
        return code
    from tramalia.core import installer
    from tramalia.i18n import t
    faltantes = [s.tool for s in report.statuses if not s.present]
    plans = [(tool, best) for tool in faltantes
             if (best := installer.best_auto(tool))]
    manuales = [tool for tool in faltantes
                if all(tool is not p[0] for p in plans)]
    if manuales:
        render.info(t("doctor.fix.manual",
                      names=", ".join(m.cmd for m in manuales)))
    if not plans:
        return code
    render.info(t("doctor.fix.plan",
                  names=", ".join(f"{tl.cmd} ({opt.method})" for tl, opt in plans)))
    # selección múltiple si hay terminal + questionary; si no, todas las auto.
    elegidas = plans
    if sys.stdin.isatty() and sys.stdout.isatty():
        try:
            import questionary
            marcadas = questionary.checkbox(
                t("doctor.fix.pick"),
                choices=[questionary.Choice(f"{tl.cmd} — {opt.display}",
                                            value=i, checked=True)
                         for i, (tl, opt) in enumerate(plans)],
            ).ask()
            if marcadas is None:
                return code
            elegidas = [plans[i] for i in marcadas]
        except ImportError:
            pass
    for tool, opt in elegidas:
        render.info(f"{tool.cmd} ← {opt.display}")
        rc, out = installer.run_install(opt)
        if rc == 0:
            render.ok(tool.cmd)
        else:
            render.warn(f"{tool.cmd} exit {rc}")
            for line in out.strip().splitlines()[-5:]:
                render.info(f"  {line}")
    render.info("re-evaluando…")
    return render.doctor(doctor_core.diagnose(Path.cwd()))


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
    adopt = getattr(args, "adopt", False)
    answers = {
        "project_name": root.name,
        "stacks": stack,
        "features": enabled_features(stack),
        "primary_agent": "codex",
        "reviewer_agent": "claude",
        "with_headroom": getattr(args, "with_headroom", False),
        "with_ponytail": getattr(args, "with_ponytail", False),
        "with_notebook_exec": getattr(args, "with_notebook_exec", False),
        "adopt": adopt,
    }
    render.header(root.name, stack, _is_initialized(root))
    results = scaffold.scaffold(root, answers)
    for rel, state in results:
        (render.ok if state in ("creado", "adaptado") else render.info)(f"{state:>9}  {rel}")
    creados = sum(1 for _, s in results if s == "creado")
    adaptados = sum(1 for _, s in results if s == "adaptado")
    extra = f", {adaptados} adaptados" if adaptados else ""
    ya = len(results) - creados - adaptados
    render.ok(f"init listo: {creados} creados{extra}, {ya} ya existían.")
    # aviso de adopción: hay archivos que el repo ya posee y que sin --adopt se saltan.
    if not adopt:
        agents = root / "AGENTS.md"
        if agents.is_file() and "tramalia:gobierno" not in agents.read_text(encoding="utf-8", errors="ignore"):
            render.info("detecté un AGENTS.md existente: usa `tramalia init --adopt` para "
                        "integrar el gobierno sin pisarlo (merge por marcadores).")
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


def _interactive_ask_task():
    """Prompt de tarea solo si hay terminal interactiva (los scripts no se cuelgan)."""
    import sys
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return None
    return lambda: menu.ask_text("ID de la tarea (ver specs/tasks.md)", "TASK-001")


def _require_init() -> bool:
    """Los comandos de gobierno exigen proyecto inicializado (guard de coherencia)."""
    from tramalia.core import project
    from tramalia.i18n import t
    if project.is_initialized(Path.cwd()):
        return True
    render.err(t("close.uninit"))
    return False


def _resolver(args):
    """Aplica la cadena de defaults: posicional > --task > current-task > prompt."""
    from tramalia.core import project
    return project.resolve_close_args(
        Path.cwd(),
        getattr(args, "task_pos", None),
        getattr(args, "task", None),
        getattr(args, "agent", None),
        getattr(args, "reviewer", None),
        ask=_interactive_ask_task(),
    )


def cmd_evidence(args) -> int:
    from tramalia.core import evidence
    if not _require_init():
        return 1
    task, _, _ = _resolver(args)
    target = evidence.build_evidence(Path.cwd(), task)
    render.ok(f"evidence pack creado: {target.relative_to(Path.cwd())}")
    render.info("completa summary.md, risks.md y next-steps.md antes de cerrar.")
    if getattr(args, "engram", False):
        _engram_save(f"evidence {task}", f"Evidence pack de {task} en {target}.")
    return 0


def cmd_handoff(args) -> int:
    from tramalia.core import handoff
    if not _require_init():
        return 1
    task, agent, reviewer = _resolver(args)
    path = handoff.new_handoff(Path.cwd(), task, agent, reviewer)
    render.ok(f"handoff agregado a {path.relative_to(Path.cwd())}")
    if getattr(args, "engram", False):
        _engram_save(f"handoff {task}",
                     f"Handoff de {task}; ejecutor {agent or '?'}, revisor {reviewer or '?'}.")
    return 0


def cmd_close(args) -> int:
    from tramalia.core import governance
    if not _require_init():
        return 1
    task, agent, reviewer = _resolver(args)
    res = governance.close(
        Path.cwd(), task, agent, reviewer,
        allow_fail=getattr(args, "allow_fail", False),
        model=getattr(args, "model", None) or "",
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
    from tramalia.i18n import t
    if res.status == "no_gates":
        render.warn(t("close.done.nogates", task=task))
    else:
        render.ok(t("close.done", task=task))
    return 0


def _log_marks() -> dict:
    from tramalia.i18n import t
    return {
        "passed": t("log.passed"),
        "passed_with_exceptions": t("log.exceptions"),
        "blocked": t("log.blocked"),
        "no_gates": t("log.nogates"),
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
        mark = _log_marks().get(e.get("status"), "○ —")
        extra = f"  ·  {e['agent']}" if e.get("agent") else ""
        if e.get("model"):
            extra += f" ({e['model']})"
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
    wanted = {f.strip() for f in
              (getattr(args, "features", None) or "rules,subagents").split(",") if f.strip()}
    code = 0
    if "rules" in wanted:
        render.info(f"reglas: AGENTS.md → {targets} (rulesync)")
        code |= _run(["rulesync", "convert", "--from", "agentsmd",
                      "--to", targets, "--features", "rules"])
    if "subagents" in wanted:
        if (Path.cwd() / ".claude" / "agents").exists():
            render.info(f"subagentes: .claude/agents → {targets} (rulesync)")
            # best-effort: no todos los targets soportan subagentes; rulesync lo reporta.
            code |= _run(["rulesync", "convert", "--from", "claudecode",
                          "--to", targets, "--features", "subagents"])
        else:
            render.info("sin .claude/agents; omitiendo fan-out de subagentes.")
    return code


def _skill_state(s: dict) -> str:
    from tramalia.i18n import t
    if s["installed"]:
        return t("skills.state.installed")
    if s["enabled"]:
        return t("skills.state.declared")
    return t("skills.state.available")


def cmd_skills(args) -> int:
    from tramalia.core import skills
    from tramalia.i18n import t
    root = Path.cwd()
    action = getattr(args, "action", None) or "sync"

    if action == "list":
        propias = skills.own_skills(root)
        if propias:
            render.info(t("skills.group.own"))
            for s in propias:
                render.ok(f"{s['name']}  —  {s['description']}")
        externas = skills.catalog(root)
        if externas:
            render.info(t("skills.group.external"))
            for s in externas:
                render.ok(f"{s['name']:<22}{_skill_state(s)}  ←  {s['source']}")
        if not propias and not externas:
            render.info("no hay skills (¿corriste `tramalia init`?)")
        return 0

    if action == "add":
        url = getattr(args, "name", None)
        if not url:
            render.err(t("skills.add.needurl"))
            return 1
        ok, resultado = skills.add_skill(root, url, getattr(args, "alias", None))
        if ok:
            render.ok(t("skills.add.ok", name=resultado))
            return 0
        render.err(t(f"skills.add.{resultado}"))
        return 1

    if action in ("enable", "disable"):
        name = getattr(args, "name", None)
        if not name:
            render.err(t("skills.toggle.needname"))
            return 1
        if skills.set_enabled(root, name, action == "enable"):
            render.ok(t("skills.toggle.on" if action == "enable" else "skills.toggle.off",
                        name=name))
            return 0
        render.err(t("skills.toggle.fail", name=name))
        return 1

    results = skills.sync_skills(root)
    if not results:
        render.info("no hay skills declaradas en .tramalia/skills.toml (todas comentadas).")
        return 0
    for name, act in results:
        ok = act in ("clonada", "actualizada")
        (render.ok if ok else render.warn)(f"{act:>12}  {name}")
    return 0


def cmd_update(args) -> int:
    from tramalia.core import skills
    render.info("update = mise upgrade + skills sync (+ copier update, futuro)")
    code = 0
    if shutil.which("mise"):
        code |= _run(["mise", "upgrade"])
    else:
        render.warn("mise ausente; omitiendo `mise upgrade`.")
    results = skills.sync_skills(Path.cwd())
    if results:
        for name, act in results:
            ok = act in ("clonada", "actualizada")
            (render.ok if ok else render.warn)(f"skill {act}: {name}")
    else:
        render.info("sin skills externas declaradas que sincronizar.")
    return code


def _ofrecer_instalar(paquete: str, para: str) -> bool:
    """Ofrece instalar una dependencia opcional ahí mismo (solo con terminal).

    Devuelve True si quedó instalada. Si el entorno rechaza pip (p. ej.
    externally-managed), muestra el comando manual sin traceback — nunca cuelga
    ni rompe en scripts (sin TTY solo imprime el hint).
    """
    import subprocess
    import sys
    from tramalia.i18n import t
    render.warn(t("offer.missing", para=para, paquete=paquete))
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        render.info(t("offer.hint", paquete=paquete))
        return False
    respuesta = menu.ask_text(t("offer.ask", paquete=paquete), "S").strip().lower()
    if respuesta not in ("", "s", "si", "sí", "y", "yes"):
        render.info(t("offer.later", paquete=paquete))
        return False
    render.info(f"→ {sys.executable} -m pip install {paquete}")
    result = subprocess.run([sys.executable, "-m", "pip", "install", paquete])
    if result.returncode == 0:
        import importlib
        importlib.invalidate_caches()
        render.ok(t("offer.installed", paquete=paquete))
        return True
    render.err(t("offer.failed"))
    render.info(t("offer.manual", paquete=paquete))
    return False


def _importable(modulo: str) -> bool:
    try:
        __import__(modulo)
        return True
    except ImportError:
        return False


def cmd_mcp(args) -> int:
    if not _importable("mcp") and not (_ofrecer_instalar("mcp", "la fachada MCP")
                                       and _importable("mcp")):
        return 127
    from tramalia import mcp_server
    render.info("levantando Tramalia MCP (stdio)… Ctrl+C para detener.")
    mcp_server.run()
    return 0


def cmd_ui(args) -> int:
    if not _importable("textual") and not (_ofrecer_instalar("textual", "el dashboard TUI")
                                           and _importable("textual")):
        return 127
    from tramalia import tui
    tui.run()
    return 0


def _guided_args(command: str):
    """Prompts guiados para close/handoff/evidence desde el menú (modo novato).

    Prellena con los defaults reales del proyecto: current-task.md y config.json.
    """
    import argparse
    from tramalia.core import project
    root = Path.cwd()
    primary, rev = project.default_agents(root)
    from tramalia.i18n import t as _t
    task = menu.ask_text(_t("guided.task"),
                         project.current_task_id(root) or "TASK-001")
    agent = reviewer = ""
    if command in ("close", "handoff"):
        agent = menu.ask_text(_t("guided.agent"), primary or "codex")
        reviewer = menu.ask_text(_t("guided.reviewer"), rev or "claude")
    return argparse.Namespace(task=task, task_pos=None, agent=agent, reviewer=reviewer,
                              engram=False, allow_fail=False)


def _show_last_close(root: Path) -> None:
    from tramalia.core import governance
    entries = governance.read_log(root)
    if entries:
        last = entries[0]
        mark = _log_marks().get(last.get("status"), "○ —")
        render.info(f"último cierre: {last['id']}  ·  {mark}")


def cmd_menu(args) -> int:
    root = Path.cwd()
    while True:
        stack = detect_stack(root)
        render.header(root.name, stack, _is_initialized(root))
        _show_last_close(root)
        try:
            choice = menu.choose()
        except (KeyboardInterrupt, EOFError):
            return 0
        if choice == "quit":
            return 0
        run_args = _guided_args(choice) if choice in ("close", "handoff", "evidence") else args
        try:
            dispatch(choice, run_args)
        except (KeyboardInterrupt, EOFError):
            render.warn("acción cancelada.")
        print()


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
    "ui": cmd_ui,
    "menu": cmd_menu,
}


def dispatch(command: str, args) -> int:
    handler = _HANDLERS.get(command)
    if handler is None:
        render.err(f"comando desconocido: {command}")
        return 2
    return handler(args)
