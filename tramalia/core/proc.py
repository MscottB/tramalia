"""Ejecución de comandos externos robusta en Windows.

En Windows las herramientas de npm son shims `.cmd`/`.bat`: `shutil.which` las
encuentra, pero `subprocess` no las ejecuta directamente (CreateProcess no corre
.cmd). Resolvemos la ruta real y, si es .cmd/.bat, la envolvemos en `cmd /c`.
"""

from __future__ import annotations

import os
import shutil
import subprocess


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def _resolve(cmd: list[str]) -> list[str]:
    exe = shutil.which(cmd[0])
    if exe is None:
        raise FileNotFoundError(cmd[0])
    args = [exe, *cmd[1:]]
    if os.name == "nt" and exe.lower().endswith((".cmd", ".bat")):
        args = ["cmd", "/c", *args]
    return args


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(_resolve(cmd), **kwargs)


def popen(cmd: list[str], **kwargs) -> subprocess.Popen:
    """Popen con el mismo manejo de shims .cmd que `run` (streaming en vivo)."""
    return subprocess.Popen(_resolve(cmd), **kwargs)
