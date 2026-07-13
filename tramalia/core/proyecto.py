"""Inspect and enforce Tramalia project governance state."""

from __future__ import annotations

import json
from pathlib import Path

from tramalia.core.errores import ErrorProyectoNoGobernado
from tramalia.core.modelos import EstadoProyecto, ValorEstadoProyecto

_INICIO_GOBIERNO = "<!-- tramalia:gobierno inicio -->"
_FIN_GOBIERNO = "<!-- tramalia:gobierno fin -->"


def _inspeccionar_agentes(agentes: Path) -> tuple[list[str], list[str]]:
    problemas: list[str] = []
    herencia: list[str] = []
    if not agentes.exists():
        problemas.append("falta AGENTS.md")
        return problemas, herencia
    if not agentes.is_file():
        problemas.append("AGENTS.md invalido")
        return problemas, herencia
    try:
        texto_agentes = agentes.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        problemas.append("AGENTS.md invalido")
        return problemas, herencia

    if "tramalia close" not in texto_agentes:
        problemas.append("AGENTS.md sin contrato tramalia close")
        return problemas, herencia

    cantidad_inicios = texto_agentes.count(_INICIO_GOBIERNO)
    cantidad_fines = texto_agentes.count(_FIN_GOBIERNO)
    if cantidad_inicios == cantidad_fines == 0:
        if "tramalia:gobierno" in texto_agentes:
            problemas.append("AGENTS.md con marcador tramalia:gobierno invalido")
        else:
            # Solo una convencion anterior reconocible puede entrar a upgrade.
            herencia.append("AGENTS.md sin marcadores tramalia:gobierno")
        return problemas, herencia
    if cantidad_inicios != 1 or cantidad_fines != 1:
        problemas.append("AGENTS.md con marcadores tramalia:gobierno invalidos")
        return problemas, herencia

    indice_inicio = texto_agentes.index(_INICIO_GOBIERNO)
    indice_fin = texto_agentes.index(_FIN_GOBIERNO)
    if indice_inicio >= indice_fin:
        problemas.append("AGENTS.md con bloque tramalia:gobierno invalido")
        return problemas, herencia
    bloque_gobierno = texto_agentes[indice_inicio + len(_INICIO_GOBIERNO) : indice_fin]
    if "tramalia close" not in bloque_gobierno:
        problemas.append("AGENTS.md con bloque tramalia:gobierno invalido")
    return problemas, herencia


def _inspeccionar_configuracion(configuracion: Path) -> list[str]:
    if not configuracion.exists():
        return ["falta .tramalia/config.json"]
    if not configuracion.is_file():
        return ["config.json invalido"]
    try:
        datos_configuracion = json.loads(configuracion.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ["config.json invalido"]
    if not isinstance(datos_configuracion, dict):
        return ["config.json invalido"]
    nombre = datos_configuracion.get("projectName")
    if not isinstance(nombre, str) or not nombre.strip():
        return ["config.json sin projectName valido"]
    return []


def _inspeccionar_version(version: Path) -> tuple[list[str], list[str]]:
    if not version.exists():
        return [], ["falta .tramalia/version"]
    if not version.is_file():
        return [".tramalia/version invalido"], []
    try:
        contenido = version.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return [".tramalia/version invalido"], []
    if not contenido.strip():
        return [".tramalia/version vacio"], []
    return [], []


def inspeccionar_estado_proyecto(raiz: Path) -> EstadoProyecto:
    """Classify a repository without changing it.

    Args:
        raiz: Repository root.

    Returns:
        A typed state with repair diagnostics.
    """
    # LISTO confirma estructura; el cargador de puertas valida el contenido TOML.
    raiz = raiz.resolve()
    directorio = raiz / ".tramalia"
    agentes = raiz / "AGENTS.md"
    configuracion = directorio / "config.json"
    version = directorio / "version"
    mise = raiz / "mise.toml"
    marcadores = (
        directorio.exists(),
        agentes.exists(),
        configuracion.exists(),
        version.exists(),
        mise.exists(),
    )
    if not any(marcadores):
        return EstadoProyecto(ValorEstadoProyecto.AUSENTE, raiz, (), "tramalia init")

    problemas: list[str] = []
    herencia: list[str] = []
    if not directorio.is_dir():
        problemas.append("falta .tramalia")

    problemas_agentes, herencia_agentes = _inspeccionar_agentes(agentes)
    problemas.extend(problemas_agentes)
    herencia.extend(herencia_agentes)
    problemas.extend(_inspeccionar_configuracion(configuracion))

    if not mise.is_file():
        problemas.append("falta mise.toml")

    problemas_version, herencia_version = _inspeccionar_version(version)
    problemas.extend(problemas_version)
    herencia.extend(herencia_version)

    if problemas:
        return EstadoProyecto(
            ValorEstadoProyecto.PARCIAL,
            raiz,
            tuple(problemas),
            "tramalia init --adopt",
        )
    if herencia:
        return EstadoProyecto(
            ValorEstadoProyecto.HEREDADO,
            raiz,
            tuple(herencia),
            "tramalia upgrade",
        )
    return EstadoProyecto(ValorEstadoProyecto.LISTO, raiz)


def exigir_proyecto_gobernado(raiz: Path) -> EstadoProyecto:
    """Return a ready project or reject a mutating operation.

    Args:
        raiz: Repository root.

    Returns:
        The ready project state.

    Raises:
        ErrorProyectoNoGobernado: If governance is absent, legacy, or partial.
    """
    estado = inspeccionar_estado_proyecto(raiz)
    if estado.listo:
        return estado
    raise ErrorProyectoNoGobernado(
        f"El proyecto esta {estado.estado}; la operacion mutante fue bloqueada.",
        estado.comando_reparacion or "tramalia init",
        ruta=estado.raiz,
        detalles={"estado": estado.estado, "problemas": estado.problemas},
    )


def exigir_proyecto_actualizable(raiz: Path) -> EstadoProyecto:
    """Allow upgrade only for a ready or structurally valid legacy project.

    Args:
        raiz: Repository root.

    Returns:
        The ready or legacy project state.

    Raises:
        ErrorProyectoNoGobernado: If upgrade cannot repair the project safely.
    """
    estado = inspeccionar_estado_proyecto(raiz)
    if estado.estado in {ValorEstadoProyecto.LISTO, ValorEstadoProyecto.HEREDADO}:
        return estado
    raise ErrorProyectoNoGobernado(
        f"El proyecto esta {estado.estado}; upgrade no puede repararlo de forma segura.",
        estado.comando_reparacion or "tramalia init",
        ruta=estado.raiz,
        detalles={"estado": estado.estado, "problemas": estado.problemas},
    )
