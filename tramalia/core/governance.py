"""Gobierno del cierre de tareas: el ritual gates → evidence → handoff.

Es el núcleo diferenciador de Tramalia: trazabilidad verificable, repo-first.
Funciona standalone; si mise/gates no están disponibles, lo registra como
excepción documentada en el evidence pack (no inventa un resultado).

INVARIANTE DEL MOAT: los archivos `*-output.txt` crudos y `metadata.json` son la
evidencia OFICIAL. Ningún artefacto derivado (p. ej. la compresión de Headroom,
`review-summary.md`) puede modificarlos, reemplazarlos ni omitirlos: solo agregar
archivos auxiliares marcados como derivados.
"""

from __future__ import annotations

import datetime
import json
import tomllib
from dataclasses import dataclass
from pathlib import Path

from tramalia.core import evidence as evidence_core
from tramalia.core import handoff as handoff_core
from tramalia.core import proc

_GATE_ORDER = ["build", "test", "lint", "format", "security", "database", "bundle", "ux"]
_OUTPUT_FILE = {
    "build": "build-output.txt", "test": "test-output.txt", "lint": "lint-output.txt",
    "format": "lint-output.txt", "security": "security-output.txt",
    "database": "database-output.txt", "bundle": "bundle-output.txt",
    "ux": "ux-output.txt",
}


@dataclass
class CloseResult:
    evidence_dir: Path
    handoff_path: Path
    gates: list[tuple[str, int, str]]  # (nombre, exit, salida)
    gates_ran: bool
    failed: list[str]
    blocked: bool
    status: str = "passed"
    metadata: dict | None = None


def _rel(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(p)


def _close_status(ran: bool, failed: list[str], allow_fail: bool) -> str:
    """Estado honesto del cierre — nunca maquilla un fallo forzado como 'passed'."""
    if not ran:
        return "no_gates"
    if failed and allow_fail:
        return "passed_with_exceptions"
    if failed:
        return "blocked"
    return "passed"


def gate_tasks(root: Path) -> list[str]:
    """Lee del mise.toml del proyecto qué gates existen (sin el agregado 'gates')."""
    f = root / "mise.toml"
    if not f.exists():
        return []
    try:
        data = tomllib.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return []
    tasks = data.get("tasks", {})
    return [t for t in _GATE_ORDER if t in tasks]


def run_gates(root: Path) -> tuple[list[tuple[str, int, str]], bool]:
    """Corre cada gate con `mise run <task>` y captura salida + exit code.

    Devuelve (resultados, ran). ran=False si mise no está (no se inventa nada).
    """
    if proc.which("mise") is None:
        return [], False
    results: list[tuple[str, int, str]] = []
    for task in gate_tasks(root):
        try:
            cp = proc.run(["mise", "run", task], cwd=root,
                          capture_output=True, text=True, timeout=900)
            results.append((task, cp.returncode, (cp.stdout or "") + (cp.stderr or "")))
        except Exception as exc:
            results.append((task, 1, f"error al ejecutar: {exc}"))
    return results, True


def close(root: Path, task: str = "TASK-000", agent: str = "", reviewer: str = "",
          allow_fail: bool = False, model: str = "") -> CloseResult:
    """Ritual de cierre con enforcement: gates → evidence (con salidas) → handoff."""
    started = datetime.datetime.now().astimezone()
    gates, ran = run_gates(root)
    failed = [name for name, code, _ in gates if code != 0]

    evidence_dir = evidence_core.build_evidence(root, task)
    # salida CRUDA de cada gate — evidencia oficial, nunca derivada (ver invariante).
    for name, code, out in gates:
        fname = _OUTPUT_FILE.get(name, f"{name}-output.txt")
        (evidence_dir / fname).write_text(
            f"# gate: {name} (exit {code})\n\n{out}\n", encoding="utf-8")

    if ran:
        rows = "\n".join(
            f"| {n} | {c} | {'ok' if c == 0 else 'FALLA'} |" for n, c, _ in gates
        ) or "| (sin tasks de gate en mise.toml) | — | — |"
        gates_md = f"# Estado de gates\n\n| gate | exit | resultado |\n|---|---|---|\n{rows}\n"
    else:
        gates_md = ("# Estado de gates\n\n"
                    "> mise ausente: los gates NO se ejecutaron.\n"
                    "> Excepción documentada — instala mise para validación verificable.\n")
    (evidence_dir / "gates-status.md").write_text(gates_md, encoding="utf-8")

    handoff_path = handoff_core.new_handoff(root, task, agent, reviewer,
                                            evidence_ref=_rel(evidence_dir, root))
    blocked = bool(failed) and not allow_fail
    status = _close_status(ran, failed, allow_fail)
    closed = datetime.datetime.now().astimezone()

    metadata = {
        "task": task,
        "agent": agent or None,
        "model": model or None,
        "reviewer": reviewer or None,
        "started_at": started.isoformat(timespec="seconds"),
        "closed_at": closed.isoformat(timespec="seconds"),
        "status": status,
        "allow_fail": allow_fail,
        "gates_ran": ran,
        "gates": {
            name: {
                "status": "passed" if code == 0 else "failed",
                "exit_code": code,
                "output": _OUTPUT_FILE.get(name, f"{name}-output.txt"),
            }
            for name, code, _ in gates
        },
        "handoff": _rel(handoff_path, root),
        "evidence_dir": _rel(evidence_dir, root),
    }
    (evidence_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return CloseResult(evidence_dir, handoff_path, gates, ran, failed, blocked,
                       status=status, metadata=metadata)


def read_log(root: Path) -> list[dict]:
    """Pista de auditoría: una entrada por evidence pack, más reciente primero.

    Prefiere `metadata.json` (estructurado); cae a `gates-status.md` para packs viejos.
    """
    base = root / ".tramalia" / "evidence"
    entries: list[dict] = []
    if not base.exists():
        return entries
    for d in sorted(base.iterdir(), reverse=True):
        if not d.is_dir():
            continue

        meta_file = d / "metadata.json"
        if meta_file.exists():
            try:
                m = json.loads(meta_file.read_text(encoding="utf-8"))
                entries.append({
                    "id": d.name,
                    "status": m.get("status"),
                    "agent": m.get("agent"),
                    "model": m.get("model"),
                    "closed_at": m.get("closed_at"),
                })
                continue
            except Exception:
                pass

        # fallback: packs sin metadata.json
        status = None
        status_file = d / "gates-status.md"
        if status_file.exists():
            low = status_file.read_text(encoding="utf-8").lower()
            if "falla" in low:
                status = "blocked"
            elif "ausente" in low or "no se ejecutaron" in low:
                status = "no_gates"
            else:
                status = "passed"
        entries.append({"id": d.name, "status": status, "agent": None, "closed_at": None})
    return entries
