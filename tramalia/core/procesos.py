"""Run external processes with explicit cross-platform outcomes."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ResultadoProceso:
    """Describe one external process without hiding failure states."""

    comando: tuple[str, ...]
    codigo_salida: int
    salida: str
    error: str
    agotado_tiempo: bool = False
    cancelado: bool = False

    @property
    def exitoso(self) -> bool:
        """Return whether the process completed successfully."""
        return self.codigo_salida == 0 and not self.agotado_tiempo and not self.cancelado


def encontrar(comando: str) -> str | None:
    """Locate an executable using the current process PATH."""
    return shutil.which(comando)


def _resolver(comando: Sequence[str]) -> list[str]:
    ejecutable = shutil.which(comando[0])
    if ejecutable is None:
        raise FileNotFoundError(comando[0])
    argumentos = [ejecutable, *comando[1:]]
    if os.name == "nt" and ejecutable.lower().endswith((".cmd", ".bat")):
        return ["cmd", "/c", *argumentos]
    return argumentos


def ejecutar(
    comando: Sequence[str],
    *,
    raiz: Path | None = None,
    limite_segundos: float = 60.0,
) -> ResultadoProceso:
    """Run a command and normalize absence, timeout, output and exit status.

    Args:
        comando: Executable and arguments without shell interpolation.
        raiz: Working directory for the child process.
        limite_segundos: Maximum runtime before termination.

    Returns:
        A stable result. Missing executables use exit 127 and timeouts use 124.
    """
    original = tuple(str(parte) for parte in comando)
    try:
        completado = subprocess.run(
            _resolver(original),
            cwd=raiz,
            capture_output=True,
            text=True,
            timeout=limite_segundos,
            check=False,
        )
    except FileNotFoundError as error:
        return ResultadoProceso(original, 127, "", str(error))
    except subprocess.TimeoutExpired as error:
        salida = (
            error.stdout.decode(errors="replace")
            if isinstance(error.stdout, bytes)
            else (error.stdout or "")
        )
        salida_error = (
            error.stderr.decode(errors="replace")
            if isinstance(error.stderr, bytes)
            else (error.stderr or "")
        )
        return ResultadoProceso(original, 124, salida, salida_error, agotado_tiempo=True)
    return ResultadoProceso(
        comando=original,
        codigo_salida=completado.returncode,
        salida=completado.stdout or "",
        error=completado.stderr or "",
    )
