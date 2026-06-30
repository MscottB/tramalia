"""Skills como referencias (no copias): se clonan/actualizan desde sus repos.

Lee el manifiesto .tramalia/skills.toml y trae cada skill bajo .tramalia/skills/<name>,
de modo que se actualicen desde su origen (`tramalia skills sync`).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

try:
    import tomllib  # py >= 3.11
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


def read_skills(root: Path) -> list[dict]:
    f = root / ".tramalia" / "skills.toml"
    if not f.exists() or tomllib is None:
        return []
    try:
        data = tomllib.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data.get("skill", [])


def sync_skills(root: Path) -> list[tuple[str, str]]:
    """Clona o actualiza cada skill declarada.

    Devuelve [(nombre, accion)] con accion en
    {clonada, actualizada, error, git-ausente, incompleta}.
    Lista vacía si no hay skills declaradas.
    """
    skills = read_skills(root)
    if not skills:
        return []
    if shutil.which("git") is None:
        return [(s.get("name", "?"), "git-ausente") for s in skills]

    base = root / ".tramalia" / "skills"
    base.mkdir(parents=True, exist_ok=True)
    results: list[tuple[str, str]] = []
    for s in skills:
        name = s.get("name")
        source = str(s.get("source", "")).removeprefix("git+")
        ref = s.get("ref")
        if not name or not source:
            results.append((name or "?", "incompleta"))
            continue
        dest = base / name
        try:
            if dest.exists():
                subprocess.run(["git", "-C", str(dest), "pull", "--ff-only"],
                               capture_output=True, text=True, timeout=120)
                results.append((name, "actualizada"))
            else:
                cmd = ["git", "clone", "--depth", "1"]
                if ref:
                    cmd += ["--branch", str(ref)]
                cmd += [source, str(dest)]
                subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                results.append((name, "clonada" if dest.exists() else "error"))
        except Exception:
            results.append((name, "error"))
    return results
