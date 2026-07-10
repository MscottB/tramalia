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
    auto, manual, runtime_offers = installer.plan_for(faltantes)
    # plans: [(label, opt)] — automatizables + runtimes que desbloquean otras tools
    plans = list(auto)
    for name, opt, enables in runtime_offers:
        plans.append((t("tui.install.runtime", rt=name, tools=", ".join(enables)), opt))
    bloqueadas = [f"{cmd} → {installer._RUNTIME_NAME.get(rt, rt)}"
                  for cmd, _d, rt in manual if rt]
    manuales_puras = [cmd for cmd, _d, rt in manual if not rt]
    if bloqueadas:
        render.info(t("doctor.fix.needsruntime", items=", ".join(bloqueadas)))
    if manuales_puras:
        render.info(t("doctor.fix.manual", names=", ".join(manuales_puras)))
    if not plans:
        return code
    render.info(t("doctor.fix.plan",
                  names=", ".join(f"{lbl} ({opt.method})" for lbl, opt in plans)))
    # selección múltiple si hay terminal + questionary; si no, todas las auto.
    elegidas = plans
    if sys.stdin.isatty() and sys.stdout.isatty():
        try:
            import questionary
            marcadas = questionary.checkbox(
                t("doctor.fix.pick"),
                choices=[questionary.Choice(f"{lbl} — {opt.display}",
                                            value=i, checked=True)
                         for i, (lbl, opt) in enumerate(plans)],
            ).ask()
            if marcadas is None:
                return code
            elegidas = [plans[i] for i in marcadas]
        except ImportError:
            pass
    for label, opt in elegidas:
        render.info(f"{label} ← {opt.display}")
        rc, out = installer.run_install(opt)
        if rc == 0:
            render.ok(label)
        else:
            render.warn(f"{label} exit {rc}")
            for line in out.strip().splitlines()[-5:]:
                render.info(f"  {line}")
    # configurar el PATH de uv si sus binarios no están accesibles
    if not report.uv_bin_on_path and installer.shutil.which("uv"):
        render.info("uv tool update-shell (PATH de uv)")
        rc, _ = installer.run_install(installer.pathfix_option())
        (render.ok if rc == 0 else render.warn)(t("doctor.pathfix.done") if rc == 0
                                                else "uv tool update-shell falló")
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
    # tope de modelos opcional: aplica sobre los frontmatter recién generados.
    cap = getattr(args, "model_cap", None)
    if cap and cap != "none":
        from tramalia.core import model_cap as mc
        from tramalia.core import project as proj
        if proj.set_agents_model_cap(root, cap):
            for role, modelo in mc.apply_to_agents(root, cap):
                render.info(f"tope {cap}: {role} → {modelo}")
    # registra la versión con la que se generó (la usa `tramalia upgrade`).
    from tramalia import __version__
    from tramalia.core import project as _proj
    _proj.set_scaffolded_version(root, __version__)
    # aviso de adopción: hay archivos que el repo ya posee y que sin --adopt se saltan.
    if not adopt:
        agents = root / "AGENTS.md"
        if agents.is_file() and "tramalia:gobierno" not in agents.read_text(encoding="utf-8", errors="ignore"):
            render.info("detecté un AGENTS.md existente: usa `tramalia init --adopt` para "
                        "integrar el gobierno sin pisarlo (merge por marcadores).")
    render.info("revisa AGENTS.md y mise.toml; instala lo que falte con `tramalia doctor`.")
    _suggest_fanout(root)
    return 0


def _suggest_fanout(root: Path) -> None:
    """Si hay agentes/hosts CLI instalados además de Claude Code, sugiere propagar
    las reglas a sus formatos con `tramalia sync` (rulesync). `init` solo deja
    `.claude/` nativo; el resto consume AGENTS.md vía fan-out (no carpetas
    hand-rolled) — AGENTS.md es la fuente única."""
    from tramalia.core import tools
    skip = {"claude", "antigravity-ide", "antigravity-2"}  # nativo / apps de escritorio
    presentes = [tl.cmd for tl in tools.REGISTRY
                 if tl.category == "agent" and tl.key not in skip
                 and tools.probe(tl).present]
    if presentes:
        render.info(f"detecté otros agentes ({', '.join(presentes)}). Para propagar tus "
                    "reglas a sus formatos (.cursor/rules, .github/…), corre `tramalia sync` "
                    "(rulesync, requiere Node). Agrega tu propio agente con `tramalia sync --to <target>`.")


def cmd_upgrade(args) -> int:
    """Actualiza un repo YA inicializado a la versión actual de Tramalia, sin pisar
    tu trabajo: agrega los archivos nuevos que falten, refresca el bloque de
    .gitignore, y registra la versión. Los archivos existentes NO se tocan."""
    from tramalia import __version__
    from tramalia.core import project, scaffold
    root = Path.cwd()
    if not project.is_initialized(root):
        render.err("este repo no está inicializado; usa `tramalia init` primero.")
        return 1
    old = project.scaffolded_version(root)
    stack = detect_stack(root)
    answers = {
        "project_name": root.name, "stacks": stack,
        "features": enabled_features(stack),
        "primary_agent": "codex", "reviewer_agent": "claude",
    }
    render.header(root.name, stack, True)
    results = scaffold.scaffold(root, answers)
    nuevos = [rel for rel, s in results if s in ("creado", "adaptado")]
    for rel in nuevos:
        render.ok(f"  + {rel}")
    project.set_scaffolded_version(root, __version__)
    desde = f"desde v{old} " if old else ""
    render.ok(f"upgrade {desde}a v{__version__}: {len(nuevos)} nuevos/actualizados, "
              f"{len(results) - len(nuevos)} sin cambios (no se pisó nada existente).")
    render.info("los archivos que ya existían NO se tocaron. Revisa el CHANGELOG por cambios "
                "de plantilla que quizás quieras adoptar a mano: "
                "https://github.com/MscottB/tramalia/blob/main/CHANGELOG.md")
    _suggest_fanout(root)
    return 0


def cmd_gates(args) -> int:
    if shutil.which("mise") is None:
        render.err("falta 'mise'. Corre `tramalia doctor` para los pasos de instalación.")
        return 127
    return _run(["mise", "run", "gates"])


def cmd_context(args) -> int:
    from tramalia.core import project
    from tramalia.core.context_backend import BACKENDS, UTILITIES
    from tramalia.i18n import t
    root = Path.cwd()
    action = getattr(args, "action", None) or "build"

    if action == "list":
        actual = project.context_backend(root)
        render.info(t("context.backend.current", name=actual))
        for key, meta in BACKENDS.items():
            marca = "→" if key == actual else " "
            estado = "✓" if shutil.which(meta["tool"]) else "○"
            render.ok(f"{marca} {estado} {key:<20}{meta['label']}")
            render.info(f"      {meta['scope']}")
            render.info(f"      {t('context.ideal')}: {meta['ideal']}")
        render.info(t("context.util.header"))
        for key, meta in UTILITIES.items():
            estado = "✓" if shutil.which(meta["tool"]) else "○"
            render.ok(f"    {estado} {key:<20}{meta['label']} — {meta['ideal']}")
        return 0

    if action == "set":
        name = getattr(args, "name", None)
        if not name:
            render.err(t("context.set.needname"))
            return 1
        if project.set_context_backend(root, name):
            render.ok(t("context.set.ok", name=name))
            return 0
        if name not in BACKENDS:
            render.err(t("context.set.invalid", name=name,
                         opts=", ".join(BACKENDS)))
        else:
            render.err(t("context.set.noconfig"))
        return 1

    from tramalia.core import context
    results = context.build_context(root)
    for rel in results:
        render.ok(f"generado  .tramalia/context/{rel}")
    if shutil.which("repomix") is None:
        render.info("repomix ausente: project-map se generó con el árbol stdlib.")
        render.info("para snapshot completo: `mise use npm:repomix`.")
    return 0


def cmd_agents(args) -> int:
    from tramalia.core import model_cap, project
    from tramalia.i18n import t
    root = Path.cwd()
    action = getattr(args, "action", None) or "list"

    if action == "list":
        cap = project.agents_model_cap(root)
        actuales = model_cap.current_agent_models(root)
        if not actuales:
            render.err(t("agents.none"))
            return 1
        render.info(t("agents.cap.current", cap=cap))
        for role, default in model_cap.ROLE_DEFAULTS.items():
            ahora = actuales.get(role, "?")
            extra = "" if ahora == default else f"  (default: {default})"
            render.ok(f"{role:<20}{ahora}{extra}")
        if cap != "none":
            render.info(t("agents.cap.equivhint"))
            for line in model_cap.equivalence_lines(cap):
                render.info(f"  {line}")
        return 0

    # action == "cap"
    cap = getattr(args, "name", None)
    if not cap:
        render.err(t("agents.cap.needvalue", opts=", ".join((*model_cap.CAPS, "none"))))
        return 1
    if not project.set_agents_model_cap(root, cap):
        if cap not in (*model_cap.CAPS, "none"):
            render.err(t("agents.cap.invalid", name=cap,
                         opts=", ".join((*model_cap.CAPS, "none"))))
        else:
            render.err(t("agents.cap.noconfig"))
        return 1
    resultados = model_cap.apply_to_agents(root, cap)
    render.ok(t("agents.cap.set", cap=cap))
    for role, modelo in resultados:
        render.ok(f"  {role:<20}→ {modelo}")
    for line in model_cap.equivalence_lines(cap):
        render.info(f"  {line}")
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
            pendientes = [s["name"] for s in externas if s["enabled"] and not s["installed"]]
            if pendientes:
                render.info(t("skills.rehydrate", names=", ".join(pendientes)))
        if not propias and not externas:
            render.info("no hay skills (¿corriste `tramalia init`?)")
        _warn_tracked_external(skills, root)
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
        _warn_tracked_external(skills, root)
        return 0
    for name, act in results:
        ok = act in ("clonada", "actualizada")
        (render.ok if ok else render.warn)(f"{act:>12}  {name}")
    _warn_tracked_external(skills, root)
    return 0


def _warn_tracked_external(skills, root) -> None:
    """Avisa si hay skills externas commiteadas en git: el .gitignore no las
    destrackea, hay que sacarlas del índice a mano (git rm -r --cached)."""
    from tramalia.i18n import t
    tracked = skills.tracked_external_skills(root)
    if tracked:
        render.warn(t("skills.tracked.warn", names=", ".join(tracked)))
        render.info(t("skills.tracked.fix"))


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
    _warn_tracked_external(skills, Path.cwd())
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
    "upgrade": cmd_upgrade,
    "gates": cmd_gates,
    "context": cmd_context,
    "agents": cmd_agents,
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
