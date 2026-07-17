"""Generate the canonical project used to exercise local quality gates."""

from __future__ import annotations

import argparse
from pathlib import Path

from tramalia.core.detect import PATTERNS, enabled_features
from tramalia.core.errores import ErrorEntradaInsegura
from tramalia.core.scaffold import scaffold
from tramalia.core.seguridad_entradas import resolver_ruta_confinada

_FECHA_CANONICA = "2000-01-01"


def respuestas_canonicas() -> dict[str, object]:
    """Build answers that exercise every recognized stack and capability.

    Returns:
        Deterministic scaffold answers for the canonical generated project.
    """
    pilas = [*PATTERNS, "react", "sqlserver"]
    capacidades = enabled_features(pilas)
    return {
        "project_name": "proyecto-prueba-seguridad",
        "stacks": pilas,
        "features": capacidades,
        "with_notebook_exec": True,
        "matriz_completa": True,
        "incluir_engram": True,
        "primary_agent": "codex",
        "reviewer_agent": "claude",
        "fecha": _FECHA_CANONICA,
    }


def generar_proyecto(raiz: Path, salida: Path) -> Path:
    """Generate a deterministic canonical project below a trusted root.

    Args:
        raiz: Existing trusted directory that contains the output.
        salida: Relative output directory below ``raiz``.

    Returns:
        Resolved path of the generated project.

    Raises:
        ErrorEntradaInsegura: If the output escapes the root, targets the root
            itself, or already contains user files.
    """
    destino = resolver_ruta_confinada(raiz, salida, permitir_ausente=True)
    raiz_resuelta = raiz.resolve(strict=True)
    if destino == raiz_resuelta:
        raise ErrorEntradaInsegura(
            "La salida no puede ser la raiz de trabajo.",
            "Indica un subdirectorio vacio dentro de la raiz.",
        )
    if destino.exists() and (not destino.is_dir() or any(destino.iterdir())):
        raise ErrorEntradaInsegura(
            "La salida debe estar ausente o ser un directorio vacio.",
            "Usa un subdirectorio nuevo para no sobrescribir archivos del usuario.",
            ruta=destino,
        )
    destino.mkdir(parents=True, exist_ok=True)
    scaffold(destino, respuestas_canonicas())
    return destino


def main(argumentos: list[str] | None = None) -> int:
    """Run the canonical project generator from the command line.

    Args:
        argumentos: Optional command-line arguments for tests.

    Returns:
        Process exit code.
    """
    analizador = argparse.ArgumentParser(
        description="Genera un proyecto canonico para probar las puertas locales."
    )
    analizador.add_argument(
        "--salida",
        type=Path,
        required=True,
        help="Subdirectorio de salida relativo al directorio actual.",
    )
    opciones = analizador.parse_args(argumentos)
    try:
        destino = generar_proyecto(Path.cwd(), opciones.salida)
    except (ErrorEntradaInsegura, OSError) as error:
        analizador.error(str(error))
    print(destino.relative_to(Path.cwd().resolve()).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
