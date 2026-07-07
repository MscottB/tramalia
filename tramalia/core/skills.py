"""Skills como referencias (no copias): se clonan/actualizan desde sus repos.

Lee el manifiesto .tramalia/skills.toml y trae cada skill bajo .tramalia/skills/<name>,
de modo que se actualicen desde su origen (`tramalia skills sync`).
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

try:
    import tomllib  # py >= 3.11
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

# bloques [[skill]] activos O comentados (el catálogo "disponible" vive comentado)
_BLOCK_RE = re.compile(r"^(#\s*)?\[\[skill\]\]\s*$")
_KV_RE = re.compile(r'^(#\s*)?(name|source|ref)\s*=\s*"([^"]*)"\s*$')


def read_skills(root: Path) -> list[dict]:
    f = root / ".tramalia" / "skills.toml"
    if not f.exists() or tomllib is None:
        return []
    try:
        data = tomllib.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data.get("skill", [])


def catalog(root: Path) -> list[dict]:
    """Catálogo COMPLETO de skills externas: activas y comentadas (disponibles).

    tomllib no ve los bloques comentados, así que se parsean a mano. Cada entrada:
    {name, source, ref, enabled, installed}.
    """
    f = root / ".tramalia" / "skills.toml"
    out: list[dict] = []
    if not f.exists():
        return out
    lines = f.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        m = _BLOCK_RE.match(lines[i])
        if not m:
            i += 1
            continue
        entry = {"name": "", "source": "", "ref": "", "enabled": m.group(1) is None}
        i += 1
        while i < len(lines):
            kv = _KV_RE.match(lines[i])
            if not kv:
                break
            entry[kv.group(2)] = kv.group(3)
            i += 1
        if entry["name"]:
            entry["installed"] = (root / ".tramalia" / "skills" / entry["name"]).is_dir()
            out.append(entry)
    return out


def set_enabled(root: Path, name: str, enabled: bool) -> bool:
    """Activa (descomenta) o desactiva (comenta) el bloque de una skill externa.

    Conservador: solo toca las líneas del bloque exacto identificado por `name`;
    si no lo reconoce con certeza, no toca nada y devuelve False. Idempotente.
    """
    f = root / ".tramalia" / "skills.toml"
    if not f.exists():
        return False
    lines = f.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        m = _BLOCK_RE.match(lines[i])
        if not m:
            i += 1
            continue
        start, j, entry_name = i, i + 1, None
        while j < len(lines) and _KV_RE.match(lines[j]):
            kv = _KV_RE.match(lines[j])
            if kv.group(2) == "name":
                entry_name = kv.group(3)
            j += 1
        if entry_name == name:
            currently = m.group(1) is None
            if currently == enabled:
                return True  # ya está como se pide
            for k in range(start, j):
                lines[k] = (re.sub(r"^#\s?", "", lines[k]) if enabled
                            else "# " + lines[k])
            f.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return True
        i = j
    return False


def own_skills(root: Path) -> list[dict]:
    """Las skills propias del proyecto (NN-*/SKILL.md) con su descripción."""
    base = root / ".tramalia" / "skills"
    out: list[dict] = []
    if not base.exists():
        return out
    for d in sorted(base.iterdir()):
        sk = d / "SKILL.md"
        if not (d.is_dir() and sk.exists() and re.match(r"^\d{2}-", d.name)):
            continue
        desc = ""
        try:
            for line in sk.read_text(encoding="utf-8").splitlines()[:6]:
                if line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip()
                    break
        except Exception:
            pass
        out.append({"name": d.name, "description": desc})
    return out


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
