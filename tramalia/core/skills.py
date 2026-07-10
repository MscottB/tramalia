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


def add_skill(root: Path, source: str, name: str | None = None) -> tuple[bool, str]:
    """Agrega un bloque [[skill]] ACTIVO al manifiesto desde una URL git.

    Devuelve (ok, nombre|razón). El nombre se deriva del último segmento de la
    URL si no se pasa. No duplica: si ya existe en el catálogo, no toca nada.
    """
    f = root / ".tramalia" / "skills.toml"
    if not f.exists():
        return False, "sin-manifiesto"
    src = source.strip()
    if not src.startswith(("http://", "https://", "git+")):
        return False, "url-invalida"
    if not src.startswith("git+"):
        src = "git+" + src
    nombre = (name or src.rstrip("/").removesuffix(".git").rsplit("/", 1)[-1]).strip()
    if not nombre:
        return False, "url-invalida"
    if any(s["name"] == nombre for s in catalog(root)):
        return False, "duplicada"
    bloque = f'\n[[skill]]\nname   = "{nombre}"\nsource = "{src}"\nref    = "main"\n'
    with f.open("a", encoding="utf-8") as fh:
        fh.write(bloque)
    return True, nombre


_OWN_RE = re.compile(r"^\d{2}-")  # skills propias: 00-.., 01-.., ...

# .gitignore: las skills EXTERNAS se re-sincronizan desde skills.toml, no se
# commitean (pueden pesar cientos de MB). Las propias (NN-*) sí van al repo.
# El manifiesto skills.toml basta para re-hidratarlas con `tramalia skills`.
_GITIGNORE_START = "# >>> tramalia:skills-externas >>>"
_GITIGNORE_END = "# <<< tramalia:skills-externas <<<"
_GITIGNORE_BODY = (
    "# Skills EXTERNAS: referencias re-sincronizables (tramalia skills), no se\n"
    "# suben al repo. Las propias NN-* (numeradas) sí se versionan.\n"
    ".tramalia/skills/*/\n"
    "!.tramalia/skills/[0-9][0-9]-*/\n"
)


def gitignore_block() -> str:
    return f"{_GITIGNORE_START}\n{_GITIGNORE_BODY}{_GITIGNORE_END}\n"


def ensure_skills_gitignore(root: Path) -> str:
    """Crea o actualiza el bloque de skills externas en .gitignore (idempotente).

    Devuelve 'creado' | 'adaptado' | 'existe'. Nunca pisa el resto del archivo:
    inserta/reemplaza solo el bloque entre marcadores (patrón managed block).
    """
    f = root / ".gitignore"
    block = gitignore_block()
    if not f.exists():
        f.write_text(block, encoding="utf-8")
        return "creado"
    text = f.read_text(encoding="utf-8")
    if _GITIGNORE_START in text and _GITIGNORE_END in text:
        pre = text[: text.index(_GITIGNORE_START)]
        post = text[text.index(_GITIGNORE_END) + len(_GITIGNORE_END):]
        new = pre + block.rstrip("\n") + post
        if new != text:
            f.write_text(new, encoding="utf-8")
            return "adaptado"
        return "existe"
    sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
    f.write_text(text + sep + block, encoding="utf-8")
    return "adaptado"


def tracked_external_skills(root: Path) -> list[str]:
    """Skills externas que YA están rastreadas por git (el .gitignore NO las
    destrackea: hay que `git rm -r --cached`). Devuelve los nombres de carpeta
    bajo .tramalia/skills que no son propias (NN-*). Vacío si no hay git/nada."""
    if shutil.which("git") is None:
        return []
    try:
        cp = subprocess.run(["git", "-C", str(root), "ls-files", ".tramalia/skills"],
                            capture_output=True, text=True, timeout=15)
    except Exception:
        return []
    names: set[str] = set()
    for line in cp.stdout.splitlines():
        parts = line.strip().split("/")
        if len(parts) >= 3 and parts[0] == ".tramalia" and parts[1] == "skills":
            if not _OWN_RE.match(parts[2]):
                names.add(parts[2])
    return sorted(names)


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


def sync_skills(root: Path, only: str | None = None) -> list[tuple[str, str]]:
    """Clona o actualiza las skills declaradas. Con `only`, solo esa skill.

    Devuelve [(nombre, accion)] con accion en
    {clonada, actualizada, error, git-ausente, incompleta}.
    Lista vacía si no hay skills declaradas (o si `only` no está declarada).
    """
    skills = read_skills(root)
    if only is not None:
        skills = [s for s in skills if s.get("name") == only]
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


def _full_installed(root: Path, name: str) -> str | None:
    """SHA completo del commit instalado de una skill externa (o None)."""
    dest = root / ".tramalia" / "skills" / name
    if not (dest / ".git").exists():
        return None
    try:
        cp = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"],
                            capture_output=True, text=True, timeout=10)
        return cp.stdout.strip() if cp.returncode == 0 else None
    except Exception:
        return None


def _full_remote(source: str, ref: str | None) -> str | None:
    """SHA completo del ref en el remoto (git ls-remote; no modifica el repo)."""
    src = str(source).removeprefix("git+")
    if shutil.which("git") is None or not src:
        return None
    try:
        cp = subprocess.run(["git", "ls-remote", src, ref or "HEAD"],
                            capture_output=True, text=True, timeout=20)
        if cp.returncode == 0 and cp.stdout.strip():
            return cp.stdout.split()[0]
    except Exception:
        pass
    return None


def installed_ref(root: Path, name: str) -> str | None:
    """SHA corto (7) del commit instalado de una skill externa."""
    full = _full_installed(root, name)
    return full[:7] if full else None


def external_status(root: Path, check_remote: bool = False) -> list[dict]:
    """Estado de versión de cada skill externa del catálogo.

    Cada dict extiende el de `catalog()` con:
      installed_ref  — SHA corto instalado (None si no está clonada).
      available_ref  — SHA corto en el remoto (solo si check_remote=True).
      update         — True si hay una versión más nueva disponible.
    `check_remote` hace una llamada de red por skill (git ls-remote): úsalo bajo
    demanda, no en cada refresco.
    """
    out: list[dict] = []
    for s in catalog(root):
        d = {**s, "installed_ref": None, "available_ref": None, "update": False}
        if s["installed"]:
            full_local = _full_installed(root, s["name"])
            d["installed_ref"] = full_local[:7] if full_local else None
            if check_remote:
                full_remote = _full_remote(s["source"], s.get("ref"))
                d["available_ref"] = full_remote[:7] if full_remote else None
                d["update"] = bool(full_local and full_remote
                                   and full_local != full_remote)
        out.append(d)
    return out
