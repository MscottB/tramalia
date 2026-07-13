"""Build derived project context with explicit optional-integration state."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tramalia.core import procesos
from tramalia.core.detect import detect_stack
from tramalia.core.integraciones import AdaptadorCapacidad, ejecutar_integracion
from tramalia.core.modelos import EstadoIntegracion, ValorEstadoIntegracion
from tramalia.core.procesos import ResultadoProceso

_EXCLUIR = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "__pycache__",
    "bin",
    "obj",
    ".tramalia",
    ".idea",
    ".vs",
    ".pytest_cache",
    ".mypy_cache",
}


@dataclass(frozen=True, slots=True)
class ResultadoContexto:
    """Return generated context files and optional adapter state."""

    archivos: tuple[Path, ...]
    integracion: EstadoIntegracion


def _arbol(raiz: Path, profundidad_maxima: int = 2) -> str:
    lineas: list[str] = [raiz.name + "/"]

    def recorrer(ruta: Path, prefijo: str, profundidad: int) -> None:
        if profundidad > profundidad_maxima:
            return
        try:
            entradas = sorted(
                [
                    entrada
                    for entrada in ruta.iterdir()
                    if entrada.name not in _EXCLUIR and not entrada.name.startswith(".git")
                ],
                key=lambda entrada: (entrada.is_file(), entrada.name.lower()),
            )
        except OSError:
            return
        for entrada in entradas:
            lineas.append(f"{prefijo}{entrada.name}{'/' if entrada.is_dir() else ''}")
            if entrada.is_dir():
                recorrer(entrada, prefijo + "  ", profundidad + 1)

    recorrer(raiz, "  ", 1)
    return "\n".join(lineas)


def construir_contexto(raiz: Path) -> ResultadoContexto:
    """Build local context and report whether Repomix completed or fell back."""
    salida = raiz / ".tramalia" / "context"
    salida.mkdir(parents=True, exist_ok=True)
    ruta_tecnologias = salida / "tech-stack.md"
    ruta_mapa = salida / "project-map.md"
    ruta_repomix = salida / "repomix-output.md"
    ruta_repomix.unlink(missing_ok=True)

    tecnologias = detect_stack(raiz)
    ruta_tecnologias.write_text(
        "# tech-stack (generado por tramalia context build)\n\n"
        + (
            "\n".join(f"- {tecnologia}" for tecnologia in tecnologias)
            if tecnologias
            else "- (no detectado)"
        )
        + "\n",
        encoding="utf-8",
    )
    ruta_mapa.write_text(
        "# project-map (generado por tramalia context build)\n\n```\n" + _arbol(raiz) + "\n```\n",
        encoding="utf-8",
    )
    archivos = [ruta_tecnologias, ruta_mapa]

    adaptadores = (
        AdaptadorCapacidad(
            "repomix",
            frozenset({"contexto_repositorio"}),
            lambda: procesos.encontrar("repomix") is not None,
        ),
        AdaptadorCapacidad("arbol_stdlib", frozenset({"contexto_repositorio"}), lambda: True),
    )

    def ejecutar_adaptador(nombre: str) -> ResultadoProceso:
        if nombre == "arbol_stdlib":
            return ResultadoProceso(("arbol_stdlib",), 0, "", "")
        return procesos.ejecutar(
            ["repomix", "-o", str(ruta_repomix)],
            raiz=raiz,
            limite_segundos=120,
        )

    intento = ejecutar_integracion(
        capacidad="contexto_repositorio",
        solicitado="repomix",
        adaptadores=adaptadores,
        operacion=ejecutar_adaptador,
        impacto_degradado="El contexto usa el mapa local sin snapshot empaquetado.",
        remediacion="Instala Repomix si necesitas el snapshot completo.",
    )
    integracion = intento.estado
    if integracion.estado is ValorEstadoIntegracion.COMPLETO:
        if ruta_repomix.exists():
            archivos.append(ruta_repomix)
        else:
            integracion = EstadoIntegracion(
                ValorEstadoIntegracion.FALLIDO,
                "contexto_repositorio",
                "repomix",
                "repomix",
                "salida_no_generada",
                "Repomix no publico el archivo de contexto solicitado.",
                "Revisa la salida de Repomix y vuelve a ejecutar el comando.",
            )
    elif integracion.estado is ValorEstadoIntegracion.FALLIDO:
        ruta_repomix.unlink(missing_ok=True)
    return ResultadoContexto(tuple(archivos), integracion)
