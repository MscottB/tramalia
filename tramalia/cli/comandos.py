"""Adapt public CLI arguments to shared Tramalia operations and integrations."""

from __future__ import annotations

import argparse
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from tramalia.cli import menu, renderizado
from tramalia.core import doctor as doctor_nucleo
from tramalia.core import habilidades, integraciones, procesos
from tramalia.core.contexto import construir_contexto
from tramalia.core.detect import detect_stack as detectar_tecnologias
from tramalia.core.detect import enabled_features as capacidades_habilitadas
from tramalia.core.errores import ErrorProyectoNoGobernado, ErrorTramalia
from tramalia.core.evidencia import leer_bitacora
from tramalia.core.habilidades import sincronizar_habilidades
from tramalia.core.modelos import (
    EntradaBitacora,
    ExcepcionFallo,
    ValorEstadoBitacora,
    ValorEstadoCierre,
    ValorEstadoPuertas,
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
from tramalia.core.puertas_calidad import cargar_puertas, ejecutar_puertas

_CODIGO_SALIDA_ERROR = {
    "proyecto_no_gobernado": 2,
    "configuracion_puertas_invalida": 2,
    "configuracion_metricas_invalida": 2,
    "id_tarea_inseguro": 2,
    "excepcion_invalida": 2,
    "persistencia_evidencia_fallida": 1,
}


def _ejecutar(comando: list[str]) -> int:
    """Ejecuta un comando externo mostrando exactamente su salida."""
    renderizado.informar(f"→ {' '.join(comando)}")
    resultado = procesos.ejecutar(comando)
    if resultado.codigo_salida == 127:
        renderizado.error(
            f"no se encontró '{comando[0]}'. Corre `tramalia doctor` para instalarlo."
        )
        return 127
    if resultado.salida:
        sys.stdout.write(resultado.salida)
    if resultado.error:
        sys.stderr.write(resultado.error)
    return resultado.codigo_salida


def _capturar_error(operacion: Callable[[], int]) -> int:
    """Convierte fallos esperados del núcleo en códigos de salida de la CLI."""
    try:
        return operacion()
    except ErrorTramalia as error_dominio:
        renderizado.renderizar_error(error_dominio)
        return _CODIGO_SALIDA_ERROR.get(error_dominio.codigo, 1)


# --------------------------------------------------------------------------- #


def comando_doctor(argumentos) -> int:
    report = doctor_nucleo.diagnose(Path.cwd())
    # snapshot para los agentes: qué está instalado (AGENTS.md les dice leerlo)
    doctor_nucleo.write_snapshot(report, Path.cwd())
    code = renderizado.renderizar_doctor(report)
    if not getattr(argumentos, "fix", False):
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
        renderizado.informar(t("doctor.fix.needsruntime", items=", ".join(bloqueadas)))
    if manuales_puras:
        renderizado.informar(t("doctor.fix.manual", names=", ".join(manuales_puras)))
    if not plans:
        return code
    renderizado.informar(
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
        renderizado.informar(f"{label} ← {opt.display}")
        rc, out = installer.run_install(opt)
        if rc == 0:
            renderizado.exito(label)
        else:
            renderizado.advertir(f"{label} exit {rc}")
            for line in out.strip().splitlines()[-5:]:
                renderizado.informar(f"  {line}")
    # configurar el PATH de uv si sus binarios no están accesibles
    if not report.uv_bin_on_path and installer.shutil.which("uv"):
        renderizado.informar("uv tool update-shell (PATH de uv)")
        rc, _ = installer.run_install(installer.pathfix_option())
        (renderizado.exito if rc == 0 else renderizado.advertir)(
            t("doctor.pathfix.done") if rc == 0 else "uv tool update-shell falló"
        )
    renderizado.informar("re-evaluando…")
    return renderizado.renderizar_doctor(doctor_nucleo.diagnose(Path.cwd()))


def comando_detectar(argumentos) -> int:
    root = Path.cwd()
    stack = detectar_tecnologias(root)
    feats = capacidades_habilitadas(stack)
    renderizado.cabecera(root.name, stack, inspeccionar_estado_proyecto(root).listo)
    renderizado.informar(f"gates aplicables: {', '.join(feats)}")
    return 0


def comando_inicializar(argumentos) -> int:
    from tramalia.core import scaffold
    from tramalia.core.integraciones import detectar_agentes_predeterminados

    root = Path.cwd()
    stack = detectar_tecnologias(root)
    adopt = getattr(argumentos, "adopt", False)
    primary, reviewer = detectar_agentes_predeterminados()
    answers = {
        "project_name": root.name,
        "stacks": stack,
        "features": capacidades_habilitadas(stack),
        "primary_agent": primary,
        "reviewer_agent": reviewer,
        "with_headroom": getattr(argumentos, "with_headroom", False),
        "with_ponytail": getattr(argumentos, "with_ponytail", False),
        "with_notebook_exec": getattr(argumentos, "with_notebook_exec", False),
        "adopt": adopt,
    }
    renderizado.cabecera(root.name, stack, inspeccionar_estado_proyecto(root).listo)
    renderizado.informar(
        f"agentes detectados para config.json: ejecutor={primary}, revisor={reviewer} "
        f"(editable luego en config.json o en el tab Cierre)"
    )
    results = scaffold.scaffold(root, answers)
    for rel, state in results:
        (renderizado.exito if state in ("creado", "adaptado") else renderizado.informar)(
            f"{state:>9}  {rel}"
        )
    creados = sum(1 for _, s in results if s == "creado")
    adaptados = sum(1 for _, s in results if s == "adaptado")
    extra = f", {adaptados} adaptados" if adaptados else ""
    ya = len(results) - creados - adaptados
    renderizado.exito(f"init listo: {creados} creados{extra}, {ya} ya existían.")
    # tope de modelos opcional: aplica sobre los frontmatter recién generados.
    cap = getattr(argumentos, "model_cap", None)
    if cap and cap != "none":
        from tramalia.core import configuracion
        from tramalia.core import model_cap as topes_modelos

        if configuracion.fijar_tope_modelos_agentes(root, cap):
            for role, modelo in topes_modelos.apply_to_agents(root, cap):
                renderizado.informar(f"tope {cap}: {role} → {modelo}")
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
            renderizado.informar(
                "detecté un AGENTS.md existente: usa `tramalia init --adopt` para "
                "integrar el gobierno sin pisarlo (merge por marcadores)."
            )
    renderizado.informar(
        "revisa AGENTS.md y mise.toml; instala lo que falte con `tramalia doctor`."
    )
    _sugerir_propagacion(root)
    return 0


def _sugerir_propagacion(root: Path) -> None:
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
        renderizado.informar(
            f"detecté otros agentes ({', '.join(presentes)}). Para propagar tus "
            "reglas a sus formatos (.cursor/rules, .github/…), corre `tramalia sync` "
            "(rulesync, requiere Node). Agrega tu propio agente con `tramalia sync --to <target>`."
        )


def comando_actualizar_proyecto(argumentos) -> int:
    """Actualiza un repo YA inicializado a la versión actual de Tramalia, sin pisar
    tu trabajo: agrega los archivos nuevos que falten, refresca el bloque de
    .gitignore, y registra la versión. Los archivos existentes NO se tocan."""
    from tramalia import __version__
    from tramalia.core import configuracion, scaffold

    root = Path.cwd()
    try:
        estado_proyecto = exigir_proyecto_actualizable(root)
    except ErrorProyectoNoGobernado:
        renderizado.error("este repo no está inicializado; usa `tramalia init` primero.")
        return 1
    old = configuracion.version_andamiaje(root)
    stack = detectar_tecnologias(root)
    from tramalia.core.integraciones import detectar_agentes_predeterminados

    primary, reviewer = detectar_agentes_predeterminados()
    answers = {
        "project_name": root.name,
        "stacks": stack,
        "features": capacidades_habilitadas(stack),
        "primary_agent": primary,
        "reviewer_agent": reviewer,
        "adopt": "AGENTS.md sin marcadores tramalia:gobierno" in estado_proyecto.problemas,
    }
    renderizado.cabecera(root.name, stack, True)
    results = scaffold.scaffold(root, answers)
    nuevos = [rel for rel, s in results if s in ("creado", "adaptado")]
    for rel in nuevos:
        renderizado.exito(f"  + {rel}")
    configuracion.fijar_version_andamiaje(root, __version__)
    desde = f"desde v{old} " if old else ""
    renderizado.exito(
        f"upgrade {desde}a v{__version__}: {len(nuevos)} nuevos/actualizados, "
        f"{len(results) - len(nuevos)} sin cambios (no se pisó nada existente)."
    )
    renderizado.informar(
        "los archivos que ya existían NO se tocaron. Revisa el CHANGELOG por cambios "
        "de plantilla que quizás quieras adoptar a mano: "
        "https://github.com/MscottB/tramalia/blob/main/CHANGELOG.md"
    )
    _sugerir_propagacion(root)
    return 0


def comando_puertas(argumentos) -> int:
    raiz = Path.cwd()
    ejecucion = ejecutar_puertas(raiz, cargar_puertas(raiz))
    if ejecucion.resultados:
        for puerta in ejecucion.resultados:
            mostrar = (
                renderizado.exito
                if puerta.estado is ValorResultadoPuerta.APROBADO
                else renderizado.error
            )
            mostrar(f"puerta {puerta.nombre}: {puerta.estado.value}")
    else:
        renderizado.advertir(f"puertas: {ejecucion.estado.value}")
    return 0 if ejecucion.estado is ValorEstadoPuertas.APROBADO else 1


def comando_contexto(argumentos) -> int:
    from tramalia.core import configuracion
    from tramalia.core.proveedor_contexto import (
        PROVEEDORES,
        UTILIDADES,
        proveedor_disponible,
    )
    from tramalia.i18n import t

    root = Path.cwd()
    action = getattr(argumentos, "action", None) or "build"

    if action == "list":
        actual = configuracion.proveedor_contexto(root)
        renderizado.informar(t("context.backend.current", name=actual))
        for key, meta in PROVEEDORES.items():
            marca = "→" if key == actual else " "
            estado = "✓" if proveedor_disponible(key) else "○"
            renderizado.exito(f"{marca} {estado} {key:<20}{meta['etiqueta']}")
            renderizado.informar(f"      {meta['alcance']}")
            renderizado.informar(f"      {t('context.ideal')}: {meta['ideal']}")
        renderizado.informar(t("context.util.header"))
        for key, meta in UTILIDADES.items():
            estado = "✓" if shutil.which(meta["herramienta"]) else "○"
            renderizado.exito(f"    {estado} {key:<20}{meta['etiqueta']} — {meta['ideal']}")
        return 0

    if action == "set":
        name = getattr(argumentos, "name", None)
        if not name:
            renderizado.error(t("context.set.needname"))
            return 1
        if configuracion.fijar_proveedor_contexto(root, name):
            renderizado.exito(t("context.set.ok", name=name))
            return 0
        if name not in PROVEEDORES:
            renderizado.error(t("context.set.invalid", name=name, opts=", ".join(PROVEEDORES)))
        else:
            renderizado.error(t("context.set.noconfig"))
        return 1

    resultado = construir_contexto(root)
    for ruta in resultado.archivos:
        renderizado.exito(f"generado  .tramalia/context/{ruta.name}")
    if resultado.integracion.estado == "degradado":
        renderizado.informar("repomix ausente: project-map se generó con el árbol stdlib.")
        renderizado.informar("para snapshot completo: `mise use npm:repomix`.")
    elif not resultado.integracion.exitoso:
        renderizado.error(f"repomix falló: {resultado.integracion.motivo}")
    return 0 if resultado.integracion.exitoso else 1


def comando_agentes(argumentos) -> int:
    from tramalia.core import configuracion, model_cap
    from tramalia.i18n import t

    root = Path.cwd()
    action = getattr(argumentos, "action", None) or "list"

    if action == "list":
        limite_actual = configuracion.tope_modelos_agentes(root)
        actuales = model_cap.current_agent_models(root)
        if not actuales:
            renderizado.error(t("agents.none"))
            return 1
        renderizado.informar(t("agents.cap.current", cap=limite_actual))
        for role, default in model_cap.ROLE_DEFAULTS.items():
            ahora = actuales.get(role, "?")
            extra = "" if ahora == default else f"  (default: {default})"
            renderizado.exito(f"{role:<20}{ahora}{extra}")
        if limite_actual != "none":
            renderizado.informar(t("agents.cap.equivhint"))
            for line in model_cap.equivalence_lines(limite_actual):
                renderizado.informar(f"  {line}")
        return 0

    # action == "cap"
    nombre_limite = str(getattr(argumentos, "name", "") or "")
    if not nombre_limite:
        renderizado.error(t("agents.cap.needvalue", opts=", ".join((*model_cap.CAPS, "none"))))
        return 1
    if not configuracion.fijar_tope_modelos_agentes(root, nombre_limite):
        if nombre_limite not in (*model_cap.CAPS, "none"):
            renderizado.error(
                t(
                    "agents.cap.invalid",
                    name=nombre_limite,
                    opts=", ".join((*model_cap.CAPS, "none")),
                )
            )
        else:
            renderizado.error(t("agents.cap.noconfig"))
        return 1
    resultados = model_cap.apply_to_agents(root, nombre_limite)
    renderizado.exito(t("agents.cap.set", cap=nombre_limite))
    for role, modelo in resultados:
        renderizado.exito(f"  {role:<20}→ {modelo}")
    for line in model_cap.equivalence_lines(nombre_limite):
        renderizado.informar(f"  {line}")
    return 0


def _preguntar_tarea_interactiva():
    """Prompt de tarea solo si hay terminal interactiva (los scripts no se cuelgan)."""
    import sys

    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return None
    return lambda: menu.pedir_texto("ID de la tarea (ver specs/tasks.md)", "TASK-001")


def _resolver(argumentos):
    """Aplica la cadena de defaults: posicional > --task > current-task > prompt."""
    from tramalia.core import configuracion

    return configuracion.resolver_argumentos_cierre(
        Path.cwd(),
        getattr(argumentos, "task_pos", None),
        getattr(argumentos, "task", None),
        getattr(argumentos, "agent", None),
        getattr(argumentos, "reviewer", None),
        preguntar=_preguntar_tarea_interactiva(),
    )


def construir_excepciones(
    argumentos: object,
    revisor_predeterminado: str,
) -> tuple[ExcepcionFallo, ...]:
    """Build the deprecated allow-fail alias as one fully reasoned exception.

    Args:
        argumentos: Parsed CLI arguments containing the deprecated alias fields.
        revisor_predeterminado: Reviewer used when the explicit field is empty.

    Returns:
        An empty tuple when the alias is absent, otherwise one complete waiver.

    Raises:
        ErrorExcepcionInvalida: If supplied fields lack their auditable structure.
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


def _exportar_engram_solicitado(argumentos: object, titulo: str, cuerpo: str) -> None:
    """Adapta el opt-in de CLI a la capacidad compartida de memoria.

    La funcion se llama exclusivamente despues de que la operacion primaria
    devolvio su paquete durable. La capa de integraciones normaliza todo fallo y
    esta capa solo presenta su estado, sin modificar el codigo de salida.
    """
    if not bool(getattr(argumentos, "engram", False)):
        return
    intento = integraciones.exportar_memoria_engram(titulo, cuerpo)
    renderizado.renderizar_exportacion_engram(intento.estado)


def comando_evidencia(argumentos) -> int:
    raiz = Path.cwd()
    id_tarea, agente, revisor = _resolver(argumentos)
    paquete = crear_evidencia(raiz, id_tarea, agente=agente, revisor=revisor)
    renderizado.exito(f"paquete de evidencia creado: {paquete.ruta.relative_to(raiz)}")
    _exportar_engram_solicitado(
        argumentos,
        f"evidence {id_tarea}",
        f"Paquete formal de {id_tarea}: {paquete.id_paquete}.",
    )
    return 0


def comando_traspaso(argumentos) -> int:
    raiz = Path.cwd()
    id_tarea, agente, revisor = _resolver(argumentos)
    paquete = registrar_traspaso(raiz, id_tarea, agente=agente, revisor=revisor)
    renderizado.exito(f"traspaso registrado en paquete: {paquete.id_paquete}")
    _exportar_engram_solicitado(
        argumentos,
        f"handoff {id_tarea}",
        f"Traspaso de {id_tarea}; ejecutor {agente or '?'}, revisor {revisor or '?'}.",
    )
    return 0


def comando_cerrar(argumentos) -> int:
    raiz = Path.cwd()
    id_tarea, agente, revisor = _resolver(argumentos)
    resultado = cerrar_proyecto(
        raiz,
        id_tarea,
        agente=agente,
        revisor=revisor,
        modelo=getattr(argumentos, "model", None) or "",
        excepciones=construir_excepciones(argumentos, revisor),
    )
    renderizado.resultado_cierre(resultado)
    _exportar_engram_solicitado(
        argumentos,
        f"close {id_tarea}",
        f"Cierre de {id_tarea}; estado {resultado.estado.value}; "
        f"bloqueos: {', '.join(resultado.bloqueos) or 'ninguno'}.",
    )
    return 0 if resultado.aprobado else 1


def _marcas_bitacora() -> dict[ValorEstadoCierre | None, str]:
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
    marca = _marcas_bitacora().get(entrada.resultado, "○ —")
    extra = f"  ·  {entrada.agente}" if entrada.agente else ""
    if entrada.modelo:
        extra += f" ({entrada.modelo})"
    return f"{entrada.id_paquete}  ·  {marca}{extra}"


def comando_bitacora(argumentos) -> int:
    entradas = leer_bitacora(Path.cwd())
    if not entradas:
        renderizado.informar("sin cierres registrados todavía. Usa `tramalia close`.")
        return 0
    renderizado.informar(f"pista de auditoría — {len(entradas)} paquetes (más reciente primero):")
    for entrada in entradas:
        mostrar = (
            renderizado.advertir
            if entrada.estado is ValorEstadoBitacora.INVALIDA
            else renderizado.exito
        )
        mostrar(_linea_bitacora(entrada))
    return 0


def comando_sincronizar(argumentos) -> int:
    if shutil.which("rulesync") is None:
        renderizado.error("falta 'rulesync'. Instálalo con: mise use npm:rulesync")
        return 127
    root = Path.cwd()
    try:
        exigir_proyecto_gobernado(root)
    except ErrorProyectoNoGobernado:
        renderizado.error("no hay AGENTS.md. Ejecuta `tramalia init` primero.")
        return 1
    # CLAUDE.md/Codex no se incluyen: ya leen AGENTS.md nativamente.
    # Targets válidos en rulesync v9: copilot, cursor, cline, antigravity-cli, zed, junie, warp, …
    targets = getattr(argumentos, "to", None) or "copilot,cursor,cline"
    wanted = {
        f.strip()
        for f in (getattr(argumentos, "features", None) or "rules,subagents").split(",")
        if f.strip()
    }
    code = 0
    if "rules" in wanted:
        renderizado.informar(f"reglas: AGENTS.md → {targets} (rulesync)")
        code |= _ejecutar(
            ["rulesync", "convert", "--from", "agentsmd", "--to", targets, "--features", "rules"]
        )
    if "subagents" in wanted:
        if (Path.cwd() / ".claude" / "agents").exists():
            renderizado.informar(f"subagentes: .claude/agents → {targets} (rulesync)")
            # best-effort: no todos los targets soportan subagentes; rulesync lo reporta.
            code |= _ejecutar(
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
            renderizado.informar("sin .claude/agents; omitiendo fan-out de subagentes.")
    return code


def _estado_habilidad_catalogo(habilidad) -> str:
    from tramalia.i18n import t

    if habilidad.instalada:
        return t("skills.state.installed")
    if habilidad.habilitada:
        return t("skills.state.declared")
    return t("skills.state.available")


def comando_habilidades(argumentos) -> int:
    from tramalia.i18n import t

    root = Path.cwd()
    action = getattr(argumentos, "action", None) or "sync"

    if action == "list":
        propias = habilidades.habilidades_propias(root)
        if propias:
            renderizado.informar(t("skills.group.own"))
            for habilidad_propia in propias:
                renderizado.exito(
                    f"{habilidad_propia['nombre']}  —  {habilidad_propia['descripcion']}"
                )
        externas = habilidades.catalogo_habilidades(root)
        if externas:
            renderizado.informar(t("skills.group.external"))
            for habilidad_externa in externas:
                referencia = habilidades.referencia_instalada(root, habilidad_externa.nombre)
                sufijo = f"  @{referencia}" if referencia else ""
                renderizado.exito(
                    f"{habilidad_externa.nombre:<22}"
                    f"{_estado_habilidad_catalogo(habilidad_externa)}{sufijo}  "
                    f"←  {habilidad_externa.fuente}"
                )
            pendientes = [
                habilidad_externa.nombre
                for habilidad_externa in externas
                if habilidad_externa.habilitada and not habilidad_externa.instalada
            ]
            if pendientes:
                renderizado.informar(t("skills.rehydrate", names=", ".join(pendientes)))
            renderizado.informar(t("skills.outdated.hint"))
        if not propias and not externas:
            renderizado.informar("no hay skills (¿corriste `tramalia init`?)")
        _avisar_habilidades_externas_rastreadas(habilidades, root)
        return 0

    if action == "outdated":
        renderizado.informar(t("skills.outdated.checking"))
        estados = habilidades.consultar_habilidades(root, consultar_remoto=True)
        fallidas = [
            estado
            for estado in estados
            if not estado.estado.exitoso and estado.estado.motivo != "habilidad_no_instalada"
        ]
        for estado in fallidas:
            renderizado.error(
                t(
                    "skills.outdated.fail",
                    name=estado.nombre,
                    reason=estado.estado.motivo,
                    remediation=estado.estado.remediacion,
                )
            )
        instaladas = [estado for estado in estados if estado.sha_resuelto and estado.estado.exitoso]
        if not instaladas and not fallidas:
            renderizado.informar(t("skills.outdated.none_installed"))
            return 0
        hay = False
        for estado in instaladas:
            if estado.estado.motivo == "actualizacion_disponible":
                hay = True
                renderizado.advertir(
                    t(
                        "skills.outdated.available",
                        name=estado.nombre,
                        old=(estado.sha_resuelto or "")[:7],
                        new=estado.estado.impacto,
                    )
                )
            else:
                renderizado.exito(
                    t(
                        "skills.outdated.current",
                        name=estado.nombre,
                        ref=(estado.sha_resuelto or "")[:7],
                    )
                )
        if hay:
            renderizado.informar(t("skills.outdated.update_all"))
        elif not fallidas:
            renderizado.informar(t("skills.outdated.uptodate"))
        return 1 if fallidas else 0

    if action == "add":
        url = getattr(argumentos, "name", None)
        if not url:
            renderizado.error(t("skills.add.needurl"))
            return 1
        ok, resultado_agregado = habilidades.agregar_habilidad(
            root,
            url,
            getattr(argumentos, "alias", None),
        )
        if ok:
            renderizado.exito(t("skills.add.ok", name=resultado_agregado))
            return 0
        renderizado.error(t(f"skills.add.{resultado_agregado}"))
        return 1

    if action in ("enable", "disable"):
        name = getattr(argumentos, "name", None)
        if not name:
            renderizado.error(t("skills.toggle.needname"))
            return 1
        if habilidades.fijar_habilitada(root, name, action == "enable"):
            renderizado.exito(
                t("skills.toggle.on" if action == "enable" else "skills.toggle.off", name=name)
            )
            return 0
        renderizado.error(t("skills.toggle.fail", name=name))
        return 1

    # `sync` rehidrata lo fijado; sólo `skills update` mueve el bloqueo Team.
    solo = getattr(argumentos, "name", None)
    resultado_sincronizacion = sincronizar_habilidades(
        root, solo=solo, actualizar=action == "update"
    )
    if not resultado_sincronizacion.resoluciones:
        if solo:
            renderizado.informar(t("skills.sync.notdeclared", name=solo))
        else:
            renderizado.informar(
                "no hay skills declaradas en .tramalia/habilidades.toml (todas comentadas)."
            )
        _avisar_habilidades_externas_rastreadas(habilidades, root)
        return 0
    for resolucion in resultado_sincronizacion.resoluciones:
        mostrar = renderizado.exito if resolucion.estado.exitoso else renderizado.advertir
        mostrar(f"{resolucion.accion:>12}  {resolucion.nombre}")
    _avisar_habilidades_externas_rastreadas(habilidades, root)
    return 0 if resultado_sincronizacion.estado.exitoso else 1


def _avisar_habilidades_externas_rastreadas(habilidades, raiz) -> None:
    """Avisa si hay skills externas commiteadas en git: el .gitignore no las
    destrackea, hay que sacarlas del índice a mano (git rm -r --cached)."""
    from tramalia.i18n import t

    rastreadas = habilidades.habilidades_externas_rastreadas(raiz)
    if rastreadas:
        renderizado.advertir(t("skills.tracked.warn", names=", ".join(rastreadas)))
        renderizado.informar(t("skills.tracked.fix"))


def comando_actualizar(argumentos) -> int:
    renderizado.informar(
        "update = mise upgrade + rehidratación de skills fijadas (no mueve locks Team)"
    )
    code = 0
    if shutil.which("mise"):
        code |= _ejecutar(["mise", "upgrade"])
    else:
        renderizado.advertir("mise ausente; omitiendo `mise upgrade`.")
    resultado = sincronizar_habilidades(Path.cwd())
    if resultado.resoluciones:
        for resolucion in resultado.resoluciones:
            mostrar = renderizado.exito if resolucion.estado.exitoso else renderizado.advertir
            mostrar(f"skill {resolucion.accion}: {resolucion.nombre}")
        if not resultado.estado.exitoso:
            code |= 1
    else:
        renderizado.informar("sin skills externas declaradas que sincronizar.")
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

    renderizado.advertir(t("offer.missing", para=para, paquete=paquete))
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        renderizado.informar(t("offer.hint", paquete=paquete))
        return False
    respuesta = menu.pedir_texto(t("offer.ask", paquete=paquete), "S").strip().lower()
    if respuesta not in ("", "s", "si", "sí", "y", "yes"):
        renderizado.informar(t("offer.later", paquete=paquete))
        return False
    renderizado.informar(f"→ {sys.executable} -m pip install {paquete}")
    try:
        resultado = subprocess.run(
            [sys.executable, "-m", "pip", "install", paquete], timeout=600
        )
    except subprocess.TimeoutExpired:
        renderizado.error("La instalación superó el límite de 600 segundos.")
        return False
    if resultado.returncode == 0:
        import importlib

        importlib.invalidate_caches()
        renderizado.exito(t("offer.installed", paquete=paquete))
        return True
    renderizado.error(t("offer.failed"))
    renderizado.informar(t("offer.manual", paquete=paquete))
    return False


def _es_importable(modulo: str) -> bool:
    try:
        __import__(modulo)
        return True
    except ImportError:
        return False


def comando_mcp(argumentos) -> int:
    if not _es_importable("mcp") and not (
        _ofrecer_instalar("mcp", "la fachada MCP") and _es_importable("mcp")
    ):
        return 127
    from tramalia import mcp_server as servidor_mcp

    renderizado.informar("levantando Tramalia MCP (stdio)… Ctrl+C para detener.")
    servidor_mcp.ejecutar()
    return 0


def comando_interfaz(argumentos) -> int:
    if not _es_importable("textual") and not (
        _ofrecer_instalar("textual", "el dashboard TUI") and _es_importable("textual")
    ):
        return 127
    from tramalia.interfaz_terminal import ejecutar

    ejecutar()
    return 0


def _argumentos_guiados(comando: str):
    """Prompts guiados para close/handoff/evidence desde el menú (modo novato).

    Prellena con los defaults reales del proyecto: current-task.md y config.json.
    """
    import argparse

    from tramalia.core import configuracion

    raiz = Path.cwd()
    agente_principal, revisor_predeterminado = configuracion.agentes_predeterminados(raiz)
    from tramalia.i18n import t as traducir

    tarea = menu.pedir_texto(
        traducir("guided.task"),
        configuracion.id_tarea_actual(raiz) or "TASK-001",
    )
    agente = revisor = ""
    if comando in ("close", "handoff"):
        agente = menu.pedir_texto(traducir("guided.agent"), agente_principal or "codex")
        revisor = menu.pedir_texto(
            traducir("guided.reviewer"),
            revisor_predeterminado or "claude",
        )
    return argparse.Namespace(
        task=tarea,
        task_pos=None,
        agent=agente,
        reviewer=revisor,
        engram=False,
        allow_fail=False,
    )


def _mostrar_ultimo_cierre(root: Path) -> None:
    entradas = leer_bitacora(root)
    if entradas:
        ultima = entradas[0]
        mostrar = (
            renderizado.advertir
            if ultima.estado is ValorEstadoBitacora.INVALIDA
            else renderizado.informar
        )
        mostrar(f"último paquete: {_linea_bitacora(ultima)}")


def comando_menu(argumentos) -> int:
    raiz = Path.cwd()
    while True:
        tecnologias = detectar_tecnologias(raiz)
        renderizado.cabecera(
            raiz.name,
            tecnologias,
            inspeccionar_estado_proyecto(raiz).listo,
        )
        _mostrar_ultimo_cierre(raiz)
        try:
            eleccion = menu.elegir()
        except (KeyboardInterrupt, EOFError):
            return 0
        if eleccion == "quit":
            return 0
        argumentos_ejecucion = (
            _argumentos_guiados(eleccion)
            if eleccion in ("close", "handoff", "evidence")
            else argumentos
        )
        try:
            despachar(eleccion, argumentos_ejecucion)
        except (KeyboardInterrupt, EOFError):
            renderizado.advertir("acción cancelada.")
        print()


_CONTROLADORES = {
    "doctor": comando_doctor,
    "detect": comando_detectar,
    "init": comando_inicializar,
    "upgrade": comando_actualizar_proyecto,
    "gates": comando_puertas,
    "context": comando_contexto,
    "agents": comando_agentes,
    "evidence": comando_evidencia,
    "handoff": comando_traspaso,
    "close": comando_cerrar,
    "log": comando_bitacora,
    "sync": comando_sincronizar,
    "skills": comando_habilidades,
    "update": comando_actualizar,
    "mcp": comando_mcp,
    "ui": comando_interfaz,
    "menu": comando_menu,
}


def despachar(comando: str, argumentos: argparse.Namespace) -> int:
    """Dispatch a public CLI command and translate recoverable domain failures.

    Args:
        comando: Stable public command name selected by argparse.
        argumentos: Parsed command arguments.

    Returns:
        Stable process exit code returned by the selected command.
    """
    controlador = _CONTROLADORES.get(comando)
    if controlador is None:
        renderizado.error(f"comando desconocido: {comando}")
        return 2
    return _capturar_error(lambda: controlador(argumentos))
