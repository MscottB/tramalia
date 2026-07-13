"""Implementación de cada comando. La mayoría hace *shell-out* transparente a la
herramienta real (regla de diseño: el façade muestra el comando, pasa la salida
tal cual y nunca esconde errores). doctor/detect son lógica propia.
"""

from __future__ import annotations

import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from tramalia.cli import menu, render
from tramalia.core import doctor as doctor_core
from tramalia.core import procesos
from tramalia.core.detect import detect_stack, enabled_features
from tramalia.core.errores import ErrorProyectoNoGobernado, ErrorTramalia
from tramalia.core.evidencia import leer_bitacora
from tramalia.core.modelos import (
    EntradaBitacora,
    ExcepcionFallo,
    ValorEstadoBitacora,
    ValorEstadoCierre,
    ValorResultadoPuerta,
)
from tramalia.core.operaciones import (
    cerrar_proyecto,
    construir_excepciones_fallo,
    crear_evidencia,
    registrar_traspaso,
)
from tramalia.core.proyecto import (
    exigir_proyecto_actualizable,
    exigir_proyecto_gobernado,
    inspeccionar_estado_proyecto,
)


def _run(cmd: list[str]) -> int:
    """Ejecuta un comando externo mostrando exactamente su salida."""
    render.info(f"→ {' '.join(cmd)}")
    resultado = procesos.ejecutar(cmd)
    if resultado.codigo_salida == 127:
        render.err(f"no se encontró '{cmd[0]}'. Corre `tramalia doctor` para instalarlo.")
        return 127
    if resultado.salida:
        sys.stdout.write(resultado.salida)
    if resultado.error:
        sys.stderr.write(resultado.error)
    return resultado.codigo_salida


_CODIGOS_ERROR = {
    "proyecto_no_gobernado": 2,
    "configuracion_puertas_invalida": 2,
    "configuracion_metricas_invalida": 2,
    "id_tarea_inseguro": 2,
    "excepcion_invalida": 2,
    "persistencia_evidencia_fallida": 1,
}


def _mostrar_error(error: ErrorTramalia) -> int:
    """Renderiza un error de dominio estable sin exponer un traceback."""
    render.err(f"[{error.codigo}] {error.mensaje}")
    render.info(error.sugerencia)
    if error.ruta is not None:
        render.info(f"ruta: {error.ruta}")
    return _CODIGOS_ERROR.get(error.codigo, 1)


def _capturar_error(operacion: Callable[[], int]) -> int:
    """Convierte fallos esperados del núcleo en códigos de salida de la CLI."""
    try:
        return operacion()
    except ErrorTramalia as error:
        return _mostrar_error(error)


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

    faltantes = [estado.herramienta for estado in report.statuses if not estado.presente]
    auto, manual, runtime_offers = installer.plan_for(faltantes)
    # plans: [(label, opt)] — automatizables + runtimes que desbloquean otras tools
    plans = list(auto)
    for name, opt, enables in runtime_offers:
        plans.append((t("tui.install.runtime", rt=name, tools=", ".join(enables)), opt))
    bloqueadas = [f"{cmd} → {installer._RUNTIME_NAME.get(rt, rt)}" for cmd, _d, rt in manual if rt]
    manuales_puras = [cmd for cmd, _d, rt in manual if not rt]
    if bloqueadas:
        render.info(t("doctor.fix.needsruntime", items=", ".join(bloqueadas)))
    if manuales_puras:
        render.info(t("doctor.fix.manual", names=", ".join(manuales_puras)))
    if not plans:
        return code
    render.info(
        t("doctor.fix.plan", names=", ".join(f"{lbl} ({opt.method})" for lbl, opt in plans))
    )
    # selección múltiple si hay terminal + questionary; si no, todas las auto.
    elegidas = plans
    if sys.stdin.isatty() and sys.stdout.isatty():
        try:
            import questionary

            marcadas = questionary.checkbox(
                t("doctor.fix.pick"),
                choices=[
                    questionary.Choice(f"{lbl} — {opt.display}", value=i, checked=True)
                    for i, (lbl, opt) in enumerate(plans)
                ],
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
        (render.ok if rc == 0 else render.warn)(
            t("doctor.pathfix.done") if rc == 0 else "uv tool update-shell falló"
        )
    render.info("re-evaluando…")
    return render.doctor(doctor_core.diagnose(Path.cwd()))


def cmd_detect(args) -> int:
    root = Path.cwd()
    stack = detect_stack(root)
    feats = enabled_features(stack)
    render.header(root.name, stack, inspeccionar_estado_proyecto(root).listo)
    render.info(f"gates aplicables: {', '.join(feats)}")
    return 0


def cmd_init(args) -> int:
    from tramalia.core import scaffold
    from tramalia.core.integraciones import detectar_agentes_predeterminados

    root = Path.cwd()
    stack = detect_stack(root)
    adopt = getattr(args, "adopt", False)
    primary, reviewer = detectar_agentes_predeterminados()
    answers = {
        "project_name": root.name,
        "stacks": stack,
        "features": enabled_features(stack),
        "primary_agent": primary,
        "reviewer_agent": reviewer,
        "with_headroom": getattr(args, "with_headroom", False),
        "with_ponytail": getattr(args, "with_ponytail", False),
        "with_notebook_exec": getattr(args, "with_notebook_exec", False),
        "adopt": adopt,
    }
    render.header(root.name, stack, inspeccionar_estado_proyecto(root).listo)
    render.info(
        f"agentes detectados para config.json: ejecutor={primary}, revisor={reviewer} "
        f"(editable luego en config.json o en el tab Cierre)"
    )
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
        from tramalia.core import configuracion
        from tramalia.core import model_cap as mc

        if configuracion.fijar_tope_modelos_agentes(root, cap):
            for role, modelo in mc.apply_to_agents(root, cap):
                render.info(f"tope {cap}: {role} → {modelo}")
    # registra la versión con la que se generó (la usa `tramalia upgrade`).
    from tramalia import __version__
    from tramalia.core import configuracion

    configuracion.fijar_version_andamiaje(root, __version__)
    # aviso de adopción: hay archivos que el repo ya posee y que sin --adopt se saltan.
    if not adopt:
        agents = root / "AGENTS.md"
        if agents.is_file() and "tramalia:gobierno" not in agents.read_text(
            encoding="utf-8", errors="ignore"
        ):
            render.info(
                "detecté un AGENTS.md existente: usa `tramalia init --adopt` para "
                "integrar el gobierno sin pisarlo (merge por marcadores)."
            )
    render.info("revisa AGENTS.md y mise.toml; instala lo que falte con `tramalia doctor`.")
    _suggest_fanout(root)
    return 0


def _suggest_fanout(root: Path) -> None:
    """Si hay agentes/hosts CLI instalados además de Claude Code, sugiere propagar
    las reglas a sus formatos con `tramalia sync` (rulesync). `init` solo deja
    `.claude/` nativo; el resto consume AGENTS.md vía fan-out (no carpetas
    hand-rolled) — AGENTS.md es la fuente única."""
    from tramalia.core import integraciones

    skip = {"claude", "antigravity-ide", "antigravity-2"}  # nativo / apps de escritorio
    presentes = [
        herramienta.comando
        for herramienta in integraciones.REGISTRO
        if herramienta.categoria == "agent"
        and herramienta.clave not in skip
        and integraciones.sondear(herramienta).presente
    ]
    if presentes:
        render.info(
            f"detecté otros agentes ({', '.join(presentes)}). Para propagar tus "
            "reglas a sus formatos (.cursor/rules, .github/…), corre `tramalia sync` "
            "(rulesync, requiere Node). Agrega tu propio agente con `tramalia sync --to <target>`."
        )


def cmd_upgrade(args) -> int:
    """Actualiza un repo YA inicializado a la versión actual de Tramalia, sin pisar
    tu trabajo: agrega los archivos nuevos que falten, refresca el bloque de
    .gitignore, y registra la versión. Los archivos existentes NO se tocan."""
    from tramalia import __version__
    from tramalia.core import configuracion, scaffold

    root = Path.cwd()
    try:
        estado_proyecto = exigir_proyecto_actualizable(root)
    except ErrorProyectoNoGobernado:
        render.err("este repo no está inicializado; usa `tramalia init` primero.")
        return 1
    old = configuracion.version_andamiaje(root)
    stack = detect_stack(root)
    from tramalia.core.integraciones import detectar_agentes_predeterminados

    primary, reviewer = detectar_agentes_predeterminados()
    answers = {
        "project_name": root.name,
        "stacks": stack,
        "features": enabled_features(stack),
        "primary_agent": primary,
        "reviewer_agent": reviewer,
        "adopt": "AGENTS.md sin marcadores tramalia:gobierno" in estado_proyecto.problemas,
    }
    render.header(root.name, stack, True)
    results = scaffold.scaffold(root, answers)
    nuevos = [rel for rel, s in results if s in ("creado", "adaptado")]
    for rel in nuevos:
        render.ok(f"  + {rel}")
    configuracion.fijar_version_andamiaje(root, __version__)
    desde = f"desde v{old} " if old else ""
    render.ok(
        f"upgrade {desde}a v{__version__}: {len(nuevos)} nuevos/actualizados, "
        f"{len(results) - len(nuevos)} sin cambios (no se pisó nada existente)."
    )
    render.info(
        "los archivos que ya existían NO se tocaron. Revisa el CHANGELOG por cambios "
        "de plantilla que quizás quieras adoptar a mano: "
        "https://github.com/MscottB/tramalia/blob/main/CHANGELOG.md"
    )
    _suggest_fanout(root)
    return 0


def cmd_gates(args) -> int:
    if shutil.which("mise") is None:
        render.err("falta 'mise'. Corre `tramalia doctor` para los pasos de instalación.")
        return 127
    return _run(["mise", "run", "gates"])


def cmd_context(args) -> int:
    from tramalia.core import configuracion
    from tramalia.core.proveedor_contexto import (
        PROVEEDORES,
        UTILIDADES,
        proveedor_disponible,
    )
    from tramalia.i18n import t

    root = Path.cwd()
    action = getattr(args, "action", None) or "build"

    if action == "list":
        actual = configuracion.proveedor_contexto(root)
        render.info(t("context.backend.current", name=actual))
        for key, meta in PROVEEDORES.items():
            marca = "→" if key == actual else " "
            estado = "✓" if proveedor_disponible(key) else "○"
            render.ok(f"{marca} {estado} {key:<20}{meta['etiqueta']}")
            render.info(f"      {meta['alcance']}")
            render.info(f"      {t('context.ideal')}: {meta['ideal']}")
        render.info(t("context.util.header"))
        for key, meta in UTILIDADES.items():
            estado = "✓" if shutil.which(meta["herramienta"]) else "○"
            render.ok(f"    {estado} {key:<20}{meta['etiqueta']} — {meta['ideal']}")
        return 0

    if action == "set":
        name = getattr(args, "name", None)
        if not name:
            render.err(t("context.set.needname"))
            return 1
        if configuracion.fijar_proveedor_contexto(root, name):
            render.ok(t("context.set.ok", name=name))
            return 0
        if name not in PROVEEDORES:
            render.err(t("context.set.invalid", name=name, opts=", ".join(PROVEEDORES)))
        else:
            render.err(t("context.set.noconfig"))
        return 1

    from tramalia.core import contexto

    resultado = contexto.construir_contexto(root)
    for ruta in resultado.archivos:
        render.ok(f"generado  .tramalia/context/{ruta.name}")
    if resultado.integracion.estado == "degradado":
        render.info("repomix ausente: project-map se generó con el árbol stdlib.")
        render.info("para snapshot completo: `mise use npm:repomix`.")
    elif not resultado.integracion.exitoso:
        render.err(f"repomix falló: {resultado.integracion.motivo}")
    return 0 if resultado.integracion.exitoso else 1


def cmd_agents(args) -> int:
    from tramalia.core import configuracion, model_cap
    from tramalia.i18n import t

    root = Path.cwd()
    action = getattr(args, "action", None) or "list"

    if action == "list":
        limite_actual = configuracion.tope_modelos_agentes(root)
        actuales = model_cap.current_agent_models(root)
        if not actuales:
            render.err(t("agents.none"))
            return 1
        render.info(t("agents.cap.current", cap=limite_actual))
        for role, default in model_cap.ROLE_DEFAULTS.items():
            ahora = actuales.get(role, "?")
            extra = "" if ahora == default else f"  (default: {default})"
            render.ok(f"{role:<20}{ahora}{extra}")
        if limite_actual != "none":
            render.info(t("agents.cap.equivhint"))
            for line in model_cap.equivalence_lines(limite_actual):
                render.info(f"  {line}")
        return 0

    # action == "cap"
    nombre_limite = str(getattr(args, "name", "") or "")
    if not nombre_limite:
        render.err(t("agents.cap.needvalue", opts=", ".join((*model_cap.CAPS, "none"))))
        return 1
    if not configuracion.fijar_tope_modelos_agentes(root, nombre_limite):
        if nombre_limite not in (*model_cap.CAPS, "none"):
            render.err(
                t(
                    "agents.cap.invalid",
                    name=nombre_limite,
                    opts=", ".join((*model_cap.CAPS, "none")),
                )
            )
        else:
            render.err(t("agents.cap.noconfig"))
        return 1
    resultados = model_cap.apply_to_agents(root, nombre_limite)
    render.ok(t("agents.cap.set", cap=nombre_limite))
    for role, modelo in resultados:
        render.ok(f"  {role:<20}→ {modelo}")
    for line in model_cap.equivalence_lines(nombre_limite):
        render.info(f"  {line}")
    return 0


def _engram_save(title: str, body: str) -> None:
    """Export opt-in a Engram (memoria persistente N2). Nunca automático."""
    try:
        if shutil.which("engram") is None:
            render.warn("engram no está instalado; se omite el export a memoria persistente.")
            return
        if _run(["engram", "save", title, body]) == 0:
            render.ok("exportado a Engram (memoria persistente N2).")
        else:
            render.warn("Engram rechazó el export; el paquete publicado sigue siendo válido.")
    except Exception:
        # Engram es una copia opcional posterior. Nunca puede convertir un paquete
        # durable en un falso fallo de CLI que invite a repetir la operación.
        render.warn("no se pudo exportar a Engram; el paquete publicado sigue siendo válido.")


def _interactive_ask_task():
    """Prompt de tarea solo si hay terminal interactiva (los scripts no se cuelgan)."""
    import sys

    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return None
    return lambda: menu.ask_text("ID de la tarea (ver specs/tasks.md)", "TASK-001")


def _resolver(args):
    """Aplica la cadena de defaults: posicional > --task > current-task > prompt."""
    from tramalia.core import configuracion

    return configuracion.resolver_argumentos_cierre(
        Path.cwd(),
        getattr(args, "task_pos", None),
        getattr(args, "task", None),
        getattr(args, "agent", None),
        getattr(args, "reviewer", None),
        preguntar=_interactive_ask_task(),
    )


def _construir_excepciones(
    argumentos: object,
    revisor_predeterminado: str,
) -> tuple[ExcepcionFallo, ...]:
    """Convierte ``--allow-fail`` en una excepción razonada y completa.

    El alias se conserva por compatibilidad, pero nunca vuelve a ser un bypass
    booleano: sin los campos requeridos y una vigencia o remediación, la
    operación no llega al núcleo.
    """
    return construir_excepciones_fallo(
        permitir_fallo=bool(getattr(argumentos, "allow_fail", False)),
        razon=getattr(argumentos, "razon_excepcion", "") or "",
        riesgo_aceptado=getattr(argumentos, "riesgo_aceptado", "") or "",
        control_afectado=getattr(argumentos, "control_afectado", "") or "",
        referencia=getattr(argumentos, "referencia_excepcion", "") or "",
        revisor_excepcion=getattr(argumentos, "revisor_excepcion", "") or "",
        revisor_predeterminado=revisor_predeterminado,
        expira_en=getattr(argumentos, "expira_en", "") or "",
        condicion_remediacion=getattr(argumentos, "condicion_remediacion", "") or "",
    )


def cmd_evidence(args) -> int:
    def ejecutar() -> int:
        raiz = Path.cwd()
        id_tarea, agente, revisor = _resolver(args)
        paquete = crear_evidencia(
            raiz,
            id_tarea,
            agente=agente,
            revisor=revisor,
        )
        render.ok(f"paquete de evidencia creado: {paquete.ruta.relative_to(raiz)}")
        if getattr(args, "engram", False):
            _engram_save(
                f"evidence {id_tarea}",
                f"Paquete formal de {id_tarea}: {paquete.id_paquete}.",
            )
        return 0

    return _capturar_error(ejecutar)


def cmd_handoff(args) -> int:
    def ejecutar() -> int:
        raiz = Path.cwd()
        id_tarea, agente, revisor = _resolver(args)
        paquete = registrar_traspaso(
            raiz,
            id_tarea,
            agente=agente,
            revisor=revisor,
        )
        render.ok(f"traspaso registrado en paquete: {paquete.id_paquete}")
        if getattr(args, "engram", False):
            _engram_save(
                f"handoff {id_tarea}",
                f"Traspaso de {id_tarea}; ejecutor {agente or '?'}, revisor {revisor or '?'}.",
            )
        return 0

    return _capturar_error(ejecutar)


def cmd_close(args) -> int:
    def ejecutar() -> int:
        raiz = Path.cwd()
        id_tarea, agente, revisor = _resolver(args)
        resultado = cerrar_proyecto(
            raiz,
            id_tarea,
            agente=agente,
            revisor=revisor,
            modelo=getattr(args, "model", None) or "",
            excepciones=_construir_excepciones(args, revisor),
        )

        if resultado.ejecucion.resultados:
            for puerta in resultado.ejecucion.resultados:
                if puerta.estado is ValorResultadoPuerta.APROBADO:
                    mostrar = render.ok
                elif puerta.estado is ValorResultadoPuerta.OMITIDO:
                    mostrar = render.warn
                else:
                    mostrar = render.err
                mostrar(f"puerta {puerta.nombre}: {puerta.estado.value}")
        else:
            render.warn(f"puertas: {resultado.ejecucion.estado.value}")

        if resultado.ruta_paquete is not None:
            ruta_paquete = resultado.ruta_paquete.relative_to(raiz)
            render.ok(f"evidencia: {ruta_paquete}  (estado: {resultado.estado.value})")
            render.info(f"metadatos: {ruta_paquete / 'metadatos.json'}")
        if resultado.ruta_traspaso is not None:
            render.ok(f"traspaso: {resultado.ruta_traspaso.relative_to(raiz)}")

        if getattr(args, "engram", False):
            _engram_save(
                f"close {id_tarea}",
                f"Cierre de {id_tarea}; estado {resultado.estado.value}; "
                f"bloqueos: {', '.join(resultado.bloqueos) or 'ninguno'}.",
            )

        if resultado.aprobado:
            render.ok(f"cierre completado: {id_tarea} ({resultado.estado.value})")
        else:
            render.err(
                f"cierre bloqueado: {', '.join(resultado.bloqueos) or 'sin causa declarada'}"
            )
        return 0 if resultado.aprobado else 1

    return _capturar_error(ejecutar)


def _log_marks() -> dict[ValorEstadoCierre | None, str]:
    from tramalia.i18n import t

    return {
        ValorEstadoCierre.APROBADO: t("log.passed"),
        ValorEstadoCierre.APROBADO_CON_EXCEPCIONES: t("log.exceptions"),
        ValorEstadoCierre.BLOQUEADO: t("log.blocked"),
        None: "○ —",
    }


def _linea_bitacora(entrada: EntradaBitacora) -> str:
    if entrada.estado is ValorEstadoBitacora.INVALIDA:
        return f"{entrada.id_paquete}  ·  inválida  ·  {entrada.error or 'error no declarado'}"
    marca = _log_marks().get(entrada.resultado, "○ —")
    extra = f"  ·  {entrada.agente}" if entrada.agente else ""
    if entrada.modelo:
        extra += f" ({entrada.modelo})"
    return f"{entrada.id_paquete}  ·  {marca}{extra}"


def cmd_log(args) -> int:
    entradas = leer_bitacora(Path.cwd())
    if not entradas:
        render.info("sin cierres registrados todavía. Usa `tramalia close`.")
        return 0
    render.info(f"pista de auditoría — {len(entradas)} paquetes (más reciente primero):")
    for entrada in entradas:
        mostrar = render.warn if entrada.estado is ValorEstadoBitacora.INVALIDA else render.ok
        mostrar(_linea_bitacora(entrada))
    return 0


def cmd_sync(args) -> int:
    if shutil.which("rulesync") is None:
        render.err("falta 'rulesync'. Instálalo con: mise use npm:rulesync")
        return 127
    root = Path.cwd()
    try:
        exigir_proyecto_gobernado(root)
    except ErrorProyectoNoGobernado:
        render.err("no hay AGENTS.md. Ejecuta `tramalia init` primero.")
        return 1
    # CLAUDE.md/Codex no se incluyen: ya leen AGENTS.md nativamente.
    # Targets válidos en rulesync v9: copilot, cursor, cline, antigravity-cli, zed, junie, warp, …
    targets = getattr(args, "to", None) or "copilot,cursor,cline"
    wanted = {
        f.strip()
        for f in (getattr(args, "features", None) or "rules,subagents").split(",")
        if f.strip()
    }
    code = 0
    if "rules" in wanted:
        render.info(f"reglas: AGENTS.md → {targets} (rulesync)")
        code |= _run(
            ["rulesync", "convert", "--from", "agentsmd", "--to", targets, "--features", "rules"]
        )
    if "subagents" in wanted:
        if (Path.cwd() / ".claude" / "agents").exists():
            render.info(f"subagentes: .claude/agents → {targets} (rulesync)")
            # best-effort: no todos los targets soportan subagentes; rulesync lo reporta.
            code |= _run(
                [
                    "rulesync",
                    "convert",
                    "--from",
                    "claudecode",
                    "--to",
                    targets,
                    "--features",
                    "subagents",
                ]
            )
        else:
            render.info("sin .claude/agents; omitiendo fan-out de subagentes.")
    return code


def _estado_habilidad_catalogo(habilidad) -> str:
    from tramalia.i18n import t

    if habilidad.instalada:
        return t("skills.state.installed")
    if habilidad.habilitada:
        return t("skills.state.declared")
    return t("skills.state.available")


def cmd_skills(args) -> int:
    from tramalia.core import habilidades
    from tramalia.i18n import t

    root = Path.cwd()
    action = getattr(args, "action", None) or "sync"

    if action == "list":
        propias = habilidades.habilidades_propias(root)
        if propias:
            render.info(t("skills.group.own"))
            for habilidad in propias:
                render.ok(f"{habilidad['nombre']}  —  {habilidad['descripcion']}")
        externas = habilidades.catalogo_habilidades(root)
        if externas:
            render.info(t("skills.group.external"))
            for habilidad in externas:
                referencia = habilidades.referencia_instalada(root, habilidad.nombre)
                sufijo = f"  @{referencia}" if referencia else ""
                render.ok(
                    f"{habilidad.nombre:<22}"
                    f"{_estado_habilidad_catalogo(habilidad)}{sufijo}  ←  {habilidad.fuente}"
                )
            pendientes = [
                habilidad.nombre
                for habilidad in externas
                if habilidad.habilitada and not habilidad.instalada
            ]
            if pendientes:
                render.info(t("skills.rehydrate", names=", ".join(pendientes)))
            render.info(t("skills.outdated.hint"))
        if not propias and not externas:
            render.info("no hay skills (¿corriste `tramalia init`?)")
        _avisar_habilidades_externas_rastreadas(habilidades, root)
        return 0

    if action == "outdated":
        render.info(t("skills.outdated.checking"))
        estados = habilidades.consultar_habilidades(root, consultar_remoto=True)
        fallidas = [estado for estado in estados if estado.accion == "fallida"]
        for estado in fallidas:
            render.err(
                t(
                    "skills.outdated.fail",
                    name=estado.nombre,
                    reason=estado.estado.motivo,
                )
            )
        instaladas = [
            estado for estado in estados if estado.sha_resuelto and estado.accion != "fallida"
        ]
        if not instaladas and not fallidas:
            render.info(t("skills.outdated.none_installed"))
            return 0
        hay = False
        for estado in instaladas:
            if estado.estado.motivo == "actualizacion_disponible":
                hay = True
                render.warn(
                    t(
                        "skills.outdated.available",
                        name=estado.nombre,
                        old=(estado.sha_resuelto or "")[:7],
                        new=estado.estado.impacto,
                    )
                )
            else:
                render.ok(
                    t(
                        "skills.outdated.current",
                        name=estado.nombre,
                        ref=(estado.sha_resuelto or "")[:7],
                    )
                )
        if hay:
            render.info(t("skills.outdated.update_all"))
        elif not fallidas:
            render.info(t("skills.outdated.uptodate"))
        return 1 if fallidas else 0

    if action == "add":
        url = getattr(args, "name", None)
        if not url:
            render.err(t("skills.add.needurl"))
            return 1
        ok, resultado = habilidades.agregar_habilidad(root, url, getattr(args, "alias", None))
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
        if habilidades.fijar_habilitada(root, name, action == "enable"):
            render.ok(
                t("skills.toggle.on" if action == "enable" else "skills.toggle.off", name=name)
            )
            return 0
        render.err(t("skills.toggle.fail", name=name))
        return 1

    # `sync` rehidrata lo fijado; sólo `skills update` mueve el bloqueo Team.
    solo = getattr(args, "name", None)
    resultado = habilidades.sincronizar_habilidades(root, solo=solo, actualizar=action == "update")
    if not resultado.resoluciones:
        if solo:
            render.info(t("skills.sync.notdeclared", name=solo))
        else:
            render.info(
                "no hay skills declaradas en .tramalia/habilidades.toml (todas comentadas)."
            )
        _avisar_habilidades_externas_rastreadas(habilidades, root)
        return 0
    for resolucion in resultado.resoluciones:
        mostrar = render.ok if resolucion.estado.exitoso else render.warn
        mostrar(f"{resolucion.accion:>12}  {resolucion.nombre}")
    _avisar_habilidades_externas_rastreadas(habilidades, root)
    return 0 if resultado.estado.exitoso else 1


def _avisar_habilidades_externas_rastreadas(habilidades, raiz) -> None:
    """Avisa si hay skills externas commiteadas en git: el .gitignore no las
    destrackea, hay que sacarlas del índice a mano (git rm -r --cached)."""
    from tramalia.i18n import t

    rastreadas = habilidades.habilidades_externas_rastreadas(raiz)
    if rastreadas:
        render.warn(t("skills.tracked.warn", names=", ".join(rastreadas)))
        render.info(t("skills.tracked.fix"))


def cmd_update(args) -> int:
    from tramalia.core import habilidades

    render.info("update = mise upgrade + rehidratación de skills fijadas (no mueve locks Team)")
    code = 0
    if shutil.which("mise"):
        code |= _run(["mise", "upgrade"])
    else:
        render.warn("mise ausente; omitiendo `mise upgrade`.")
    resultado = habilidades.sincronizar_habilidades(Path.cwd())
    if resultado.resoluciones:
        for resolucion in resultado.resoluciones:
            mostrar = render.ok if resolucion.estado.exitoso else render.warn
            mostrar(f"skill {resolucion.accion}: {resolucion.nombre}")
        if not resultado.estado.exitoso:
            code |= 1
    else:
        render.info("sin skills externas declaradas que sincronizar.")
    _avisar_habilidades_externas_rastreadas(habilidades, Path.cwd())
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
    if not _importable("mcp") and not (
        _ofrecer_instalar("mcp", "la fachada MCP") and _importable("mcp")
    ):
        return 127
    from tramalia import mcp_server

    render.info("levantando Tramalia MCP (stdio)… Ctrl+C para detener.")
    mcp_server.run()
    return 0


def cmd_ui(args) -> int:
    if not _importable("textual") and not (
        _ofrecer_instalar("textual", "el dashboard TUI") and _importable("textual")
    ):
        return 127
    from tramalia import tui

    tui.run()
    return 0


def _guided_args(command: str):
    """Prompts guiados para close/handoff/evidence desde el menú (modo novato).

    Prellena con los defaults reales del proyecto: current-task.md y config.json.
    """
    import argparse

    from tramalia.core import configuracion

    root = Path.cwd()
    primary, rev = configuracion.agentes_predeterminados(root)
    from tramalia.i18n import t as _t

    task = menu.ask_text(_t("guided.task"), configuracion.id_tarea_actual(root) or "TASK-001")
    agent = reviewer = ""
    if command in ("close", "handoff"):
        agent = menu.ask_text(_t("guided.agent"), primary or "codex")
        reviewer = menu.ask_text(_t("guided.reviewer"), rev or "claude")
    return argparse.Namespace(
        task=task, task_pos=None, agent=agent, reviewer=reviewer, engram=False, allow_fail=False
    )


def _show_last_close(root: Path) -> None:
    entradas = leer_bitacora(root)
    if entradas:
        ultima = entradas[0]
        mostrar = render.warn if ultima.estado is ValorEstadoBitacora.INVALIDA else render.info
        mostrar(f"último paquete: {_linea_bitacora(ultima)}")


def cmd_menu(args) -> int:
    root = Path.cwd()
    while True:
        stack = detect_stack(root)
        render.header(root.name, stack, inspeccionar_estado_proyecto(root).listo)
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
