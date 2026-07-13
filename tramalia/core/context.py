"""context build: genera la memoria DERIVADA (no se escribe a mano).

- tech-stack.md  -> del detector.
- project-map.md -> árbol stdlib (y repomix si está disponible).
Serena no se invoca aquí: es navegación en vivo del agente vía MCP.
"""

from __future__ import annotations

from pathlib import Path

from tramalia.core import procesos
from tramalia.core.detect import detect_stack

_EXCLUDE = {
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


def _tree(root: Path, max_depth: int = 2) -> str:
    lines: list[str] = [root.name + "/"]

    def walk(path: Path, prefix: str, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            entries = sorted(
                [
                    e
                    for e in path.iterdir()
                    if e.name not in _EXCLUDE and not e.name.startswith(".git")
                ],
                key=lambda e: (e.is_file(), e.name.lower()),
            )
        except Exception:
            return
        for entry in entries:
            lines.append(f"{prefix}{entry.name}{'/' if entry.is_dir() else ''}")
            if entry.is_dir():
                walk(entry, prefix + "  ", depth + 1)

    walk(root, "  ", 1)
    return "\n".join(lines)


def build_context(root: Path) -> list[str]:
    out = root / ".tramalia" / "context"
    out.mkdir(parents=True, exist_ok=True)
    results: list[str] = []

    stack = detect_stack(root)
    (out / "tech-stack.md").write_text(
        "# tech-stack (generado por tramalia context build)\n\n"
        + ("\n".join(f"- {s}" for s in stack) if stack else "- (no detectado)")
        + "\n",
        encoding="utf-8",
    )
    results.append("tech-stack.md")

    (out / "project-map.md").write_text(
        "# project-map (generado por tramalia context build)\n\n```\n" + _tree(root) + "\n```\n",
        encoding="utf-8",
    )
    results.append("project-map.md")

    if procesos.encontrar("repomix"):
        resultado = procesos.ejecutar(
            ["repomix", "-o", str(out / "repomix-output.md")],
            raiz=root,
            limite_segundos=120,
        )
        if resultado.exitoso:
            results.append("repomix-output.md")

    return results
