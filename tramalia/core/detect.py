"""Detección básica de stack por patrones de archivos.

Es deliberadamente liviana: solo identifica qué ecosistemas hay para decidir
qué herramientas y gates aplican. El detalle real del código lo aporta Serena.
"""

from __future__ import annotations

from pathlib import Path

# stack -> globs (relativos a la raíz; se evita ** para no recorrer todo el repo)
PATTERNS: dict[str, list[str]] = {
    "node": ["package.json"],
    "angular": ["angular.json"],
    "next": ["next.config.js", "next.config.mjs", "next.config.ts", "next.config.cjs"],
    "nest": ["nest-cli.json"],
    "vue": ["vue.config.js", "vue.config.ts", "nuxt.config.*"],
    "svelte": ["svelte.config.js", "svelte.config.ts"],
    "tailwind": [
        "tailwind.config.js",
        "tailwind.config.ts",
        "tailwind.config.cjs",
        "tailwind.config.mjs",
    ],
    "dotnet": ["*.sln", "*.csproj", "src/*.csproj"],
    "java": ["pom.xml", "build.gradle"],
    "maven": ["pom.xml"],
    "gradle": ["build.gradle", "build.gradle.kts"],
    "python": ["pyproject.toml", "requirements.txt"],
    "go": ["go.mod"],
    "rust": ["Cargo.toml"],
    "postgres": ["*.sql", "database/migrations", "db/migrations"],
    "docker": ["Dockerfile", "compose.yaml", "compose.yml", "docker-compose.yml"],
    # analítica: Databricks Asset Bundles y notebooks Jupyter
    "databricks": ["databricks.yml", "databricks.yaml"],
    "notebooks": ["*.ipynb", "notebooks/*.ipynb"],
}

# stacks que implican "hay frontend" -> activa el gate UX/UI
_FRONTEND = {"node", "angular", "react", "next", "vue", "svelte"}


def detect_stack(root: Path) -> list[str]:
    found: list[str] = []
    for name, globs in PATTERNS.items():
        for pattern in globs:
            try:
                if next(root.glob(pattern), None) is not None:
                    found.append(name)
                    break
            except Exception:
                continue
    # React no tiene archivo propio: se infiere de package.json
    pkg = root / "package.json"
    if pkg.is_file():
        try:
            if "react" in pkg.read_text(encoding="utf-8", errors="ignore").lower():
                found.append("react")
        except Exception:
            pass
    # SQL Server: señal fuerte en algún .csproj (driver SqlClient) — no se puede
    # inferir del dialecto SQL a ojo, así que se usa la dependencia como marcador.
    for csproj in (*root.glob("*.csproj"), *root.glob("src/*.csproj")):
        try:
            if "sqlclient" in csproj.read_text(encoding="utf-8", errors="ignore").lower():
                found.append("sqlserver")
                break
        except Exception:
            continue
    return found


def enabled_features(stack: list[str]) -> tuple[str, ...]:
    """Decide qué features/gates aplican según el stack detectado."""
    # "memory" y "specs" siempre presentes: doctor surface Engram y Spec Kit (opcionales).
    features = {"init", "context", "security", "sync", "memory", "specs"}
    if any(s in stack for s in ("postgres", "sqlserver", "java", "dotnet", "python")):
        features.add("database")
    if "databricks" in stack:
        features.add("databricks")
    if any(s in stack for s in _FRONTEND):
        features.add("ux")
    return tuple(sorted(features))
