# Base reproducible, pruebas y CI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establecer Python 3.11 como mínimo, un entorno reproducible con `uv`, una suite verificable y un workflow de validación que impida construir paquetes sin pruebas.

**Architecture:** Este plan no cambia todavía la semántica de cierre. Primero crea un baseline ejecutable, registra contratos de metadatos y CI, normaliza formato/lint y deja la estructura de pruebas en español preparada para los planes de núcleo, integraciones y documentación.

**Tech Stack:** Python 3.11–3.14, pytest, uv, Ruff, Hatchling, GitHub Actions, build y twine.

## Global Constraints

- Python 3.11 será la versión mínima de la BETA.
- La compatibilidad objetivo será Python 3.11, 3.12, 3.13 y 3.14.
- Los nombres nuevos propios de archivos, módulos, clases, funciones, métodos, variables, auxiliares de pytest y marcadores se escribirán en español ASCII; `ñ` se representa como `n`.
- Los docstrings públicos se escribirán en inglés con estilo Google; los comentarios internos serán español y explicarán motivos, no sintaxis.
- No se cambia la semántica de gates/evidence en este plan; los P0 de gobierno se implementan en el plan 02.
- Todos los cambios de comportamiento siguen RED → GREEN → REFACTOR.
- El runner y los colaboradores usan <code>uv 0.11.28</code>; el SHA de <code>setup-uv</code> y la versión instalada se fijan por separado.
- `AGENTS.md` es un archivo local preexistente y no debe añadirse a ningún commit.

---

### Task 1: Declarar Python 3.11 y el entorno de desarrollo reproducible

**Files:**
- Create: `tests/contratos/test_metadatos_proyecto.py`
- Modify: `pyproject.toml:1-61`
- Create: `uv.lock`

**Interfaces:**
- Consumes: metadata PEP 621 actual de `pyproject.toml`.
- Produces: `requires-python = ">=3.11"`, classifiers 3.11–3.14 y grupo `desarrollo` instalable mediante `uv sync --group desarrollo`.

- [ ] **Step 1: Write the failing metadata contract**

```python
from pathlib import Path
import tomllib


RAIZ = Path(__file__).resolve().parents[2]


def cargar_proyecto() -> dict[str, object]:
    with (RAIZ / "pyproject.toml").open("rb") as archivo:
        return tomllib.load(archivo)


def test_python_minimo_y_clasificadores_beta() -> None:
    proyecto = cargar_proyecto()["project"]
    assert proyecto["requires-python"] == ">=3.11"
    clasificadores = set(proyecto["classifiers"])
    assert "Programming Language :: Python :: 3.10" not in clasificadores
    for version in ("3.11", "3.12", "3.13", "3.14"):
        assert f"Programming Language :: Python :: {version}" in clasificadores


def test_grupo_desarrollo_contiene_herramientas_obligatorias() -> None:
    grupos = cargar_proyecto()["dependency-groups"]
    nombres = {dependencia.split(">=")[0] for dependencia in grupos["desarrollo"]}
    assert {
        "pytest",
        "pytest-cov",
        "pytest-timeout",
        "pytest-repeat",
        "ruff",
        "mypy",
        "build",
        "twine",
    } <= nombres


def test_motor_de_construccion_esta_fijado() -> None:
    assert cargar_proyecto()["build-system"]["requires"] == ["hatchling==1.31.0"]
```

- [ ] **Step 2: Run the contract and verify RED**

Run: `uv run --with pytest pytest tests/contratos/test_metadatos_proyecto.py -v`

Expected: FAIL because `requires-python` is still `>=3.10` and `dependency-groups.desarrollo` does not exist.

- [ ] **Step 3: Update project metadata**

Edit the existing keys in `pyproject.toml` and append the dependency group exactly as follows:

```toml
requires-python = ">=3.11"

classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Topic :: Software Development :: Build Tools",
    "Topic :: Software Development :: Quality Assurance",
]

[dependency-groups]
desarrollo = [
    "pytest>=8",
    "pytest-cov>=6",
    "pytest-timeout>=2",
    "pytest-repeat>=0.9",
    "ruff>=0.12",
    "mypy>=1.16",
    "build>=1.2",
    "twine>=6",
]

[build-system]
requires = ["hatchling==1.31.0"]
build-backend = "hatchling.build"
```

Editar el bloque `[build-system]` existente en su ubicación actual; no crear una segunda tabla TOML.

Keep the public extras `mcp`, `tui`, `full` and the established compatibility aliases unchanged in this task.

- [ ] **Step 4: Resolve and synchronize the environment**

Run:

```powershell
uv lock --python 3.11
uv sync --locked --group desarrollo --all-extras
```

Expected: `uv.lock` is created and synchronization finishes with exit code 0.

- [ ] **Step 5: Verify GREEN**

Run: `uv run pytest tests/contratos/test_metadatos_proyecto.py -v`

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock tests/contratos/test_metadatos_proyecto.py
git commit -m "build: require Python 3.11 and lock development tools"
```

### Task 2: Registrar el baseline y la arquitectura de pruebas

**Files:**
- Modify: `pyproject.toml:60-61`
- Create: `tests/README.md`
- Create: `tests/AUDITORIA.md`
- Create: `tests/conftest.py`
- Modify: `.gitignore`
- Modify: `tests/contratos/test_metadatos_proyecto.py`

**Interfaces:**
- Consumes: entorno `desarrollo` del Task 1, las 250 pruebas históricas observadas antes del plan y los contratos añadidos en Task 1.
- Produces: una auditoría medible de necesidad/solapamiento/costo, marcadores registrados, directorios de pruebas aceptados y el auxiliar `raiz_proyecto` para planes posteriores.

- [ ] **Step 1: Establish the executable baseline**

Run: `uv run pytest -q -p no:cacheprovider`

Expected: toda la colección real pasa; debe incluir las 250 pruebas históricas más los contratos ya añadidos, sin exigir un total fijo. If any test fails, stop this task and invoke `superpowers:systematic-debugging`; do not reorganize files until the baseline is green.

- [ ] **Step 2: Medir colección, cobertura por contexto y duración sin convertir 250 en objetivo**

Run:

```powershell
New-Item -ItemType Directory -Force .artefactos | Out-Null
uv run pytest --collect-only -q | Tee-Object .artefactos/pruebas-colectadas.txt
uv run pytest --cov=tramalia --cov-branch --cov-context=test --cov-report=term-missing --cov-report=json:.artefactos/cobertura.json --durations=0
uv run coverage json --show-contexts -o .artefactos/cobertura-contextos.json
```

Expected: la colección real y todas las pruebas pasan; los dos JSON permiten ver qué líneas/ramas protege cada test y la salida de duraciones identifica el costo. Añadir `.artefactos/` a `.gitignore`; estos datos son diagnósticos regenerables, no artefactos del paquete.

- [ ] **Step 3: Documentar la decisión sobre las 250 pruebas existentes**

Crear `tests/AUDITORIA.md` con los valores medidos, sin copiar un número esperado desde el badge, y estas secciones exactas:

```markdown
# Auditoría de pruebas

## Baseline medido
## Matriz comportamiento-riesgo
| Comportamiento observable | Riesgo | Pruebas que lo protegen | Decisión | Reemplazo canónico |
## Solapamientos candidatos
## Pruebas lentas
## Decisiones por archivo histórico
## Criterio de actualización
```

Clasificar cada archivo actual y cada grupo candidato como `conservar`, `consolidar`, `reemplazar` o `eliminar`. La igualdad de líneas cubiertas sólo crea un candidato: revisar entradas, assertions y regresión antes de decidir. Toda consolidación/eliminación debe indicar el test canónico que conserva el comportamiento y la tarea de los planes 02/03 que hará la migración. En este plan no borrar regresiones; el objetivo es reducir duplicación sólo con trazabilidad, no conservar 250 por costumbre ni reducir el número por sí mismo.

- [ ] **Step 4: Extend the failing metadata contract**

Append to `tests/contratos/test_metadatos_proyecto.py`:

```python
def test_marcadores_de_pruebas_estan_registrados() -> None:
    configuracion_pytest = cargar_proyecto()["tool"]["pytest"]["ini_options"]
    marcadores = "\n".join(configuracion_pytest["markers"])
    for marcador in (
        "unidad",
        "contrato",
        "integracion",
        "interfaz",
        "opcional",
        "publicacion",
    ):
        assert f"{marcador}:" in marcadores
```

- [ ] **Step 5: Run and verify RED**

Run: `uv run pytest tests/contratos/test_metadatos_proyecto.py::test_marcadores_de_pruebas_estan_registrados -v`

Expected: FAIL with `KeyError: 'markers'`.

- [ ] **Step 6: Registrar marcadores y rutas de pruebas**

Replace `[tool.pytest.ini_options]` in `pyproject.toml` with:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--strict-markers", "--strict-config"]
timeout = 60
timeout_method = "thread"
markers = [
    "unidad: logica pura y rapida",
    "contrato: formatos, scaffold y superficies publicas",
    "integracion: filesystem, Git, procesos y cierre",
    "interfaz: flujos publicos de Textual",
    "opcional: requiere extras TUI o MCP",
    "publicacion: wheel, metadata y smoke de release",
]
```

Create `tests/conftest.py`:

```python
from pathlib import Path

import pytest


@pytest.fixture
def raiz_proyecto() -> Path:
    """Return the repository root used by contract and release tests."""
    return Path(__file__).resolve().parents[1]
```

Create `tests/README.md`:

```markdown
# Arquitectura de pruebas

La suite se organiza por comportamiento, no por número de versión.

- `unidad/`: lógica pura.
- `contratos/`: formatos y APIs públicas.
- `integracion/`: filesystem, Git y procesos.
- `interfaz/`: flujos públicos de Textual.
- `publicacion/`: wheel y lanzamiento.

Los archivos históricos `test_v*.py` se migran cuando el plan del subsistema
correspondiente refactoriza ese comportamiento. Ningún plan elimina una regresión
sin reemplazarla por un contrato observable y registrar la decisión en
`tests/AUDITORIA.md`.
```

- [ ] **Step 7: Verify GREEN and the audited baseline**

Run:

```powershell
uv run pytest tests/contratos/test_metadatos_proyecto.py -v
uv run pytest -q -p no:cacheprovider
```

Expected: el contrato de metadata y toda la colección medida pasan. El conteo puede crecer por contratos nuevos y sólo puede bajar después de una decisión trazable; no existe un número objetivo permanente.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml .gitignore tests/README.md tests/AUDITORIA.md tests/conftest.py tests/contratos/test_metadatos_proyecto.py
git commit -m "test: define behavior-based test architecture"
```

### Task 3: Normalizar formato y eliminar errores Ruff existentes

**Files:**
- Modify: `pyproject.toml`
- Modify: `scripts/build_offline_docs.py`
- Modify: `tramalia/core/installer.py`
- Modify: `tramalia/core/scaffold.py`
- Modify: `tramalia/core/tools.py`
- Modify: `tests/test_v017.py`
- Modify: `tests/test_v027.py`
- Modify: `tests/test_v029.py`
- Modify: Python files reformatted by Ruff

**Interfaces:**
- Consumes: baseline auditado y verde de Task 2.
- Produces: `ruff check .` y `ruff format --check .` con exit code 0, sin cambio de comportamiento.

- [ ] **Step 1: Add Ruff configuration**

Append to `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py311"
line-length = 100
extend-exclude = ["site", ".worktrees"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]
ignore = ["E501"]  # El formateador aplica 100 columnas; no rompe URLs ni mensajes largos.
```

- [ ] **Step 2: Confirm the known RED baseline**

Run: `uv run ruff check . --output-format concise`

Expected: FAIL with the existing unused imports, undefined `Path` in `installer.py` and E702 semicolon findings in `scaffold.py`.

- [ ] **Step 3: Apply safe automatic fixes and formatting**

Run:

```powershell
uv run ruff check . --fix
uv run ruff format .
```

Expected: unused imports and formatting-only findings are updated; Ruff still reports any semantic finding that requires a manual edit.

- [ ] **Step 4: Fix the `Path` annotation without a local import**

Add `from pathlib import Path` with the other imports in `tramalia/core/installer.py` and replace `uv_bin_dir` with:

```python
def uv_bin_dir() -> Path:
    """Return the directory where uv installs user-level executables."""
    return Path.home() / ".local" / "bin"
```

- [ ] **Step 5: Expand the semicolon statements in scaffold**

Replace the command accumulation block in `tramalia/core/scaffold.py` with:

```text
    comandos_construccion: list[str] = []
    comandos_prueba: list[str] = []
    comandos_lint: list[str] = []
    if "angular" in stacks:
        comandos_construccion.append("ng build")
        comandos_prueba.append("ng test --watch=false")
        comandos_lint.append("ng lint")
    elif any(tecnologia in stacks for tecnologia in ("node", "react", "next", "vue", "svelte")):
        # Nest y otras API Node usan los scripts declarados por el proyecto.
        comandos_construccion.append("npm run build")
        comandos_prueba.append("npm test")
        comandos_lint.append("npm run lint")
    if "dotnet" in stacks:
        comandos_construccion.append("dotnet build")
        comandos_prueba.append("dotnet test")
    if "maven" in stacks:
        comandos_construccion.append("mvn -B compile")
        comandos_prueba.append("mvn -B test")
    elif "gradle" in stacks:
        comandos_construccion.append("gradle build -x test")
        comandos_prueba.append("gradle test")
    if "go" in stacks:
        comandos_construccion.append("go build ./...")
        comandos_prueba.append("go test ./...")
    if "rust" in stacks:
        comandos_construccion.append("cargo build")
        comandos_prueba.append("cargo test")
    if "python" in stacks:
        comandos_prueba.append("pytest")
        comandos_lint.append("ruff check")
    if "notebooks" in stacks:
        # Los outputs sucios rompen diffs y auditoria; esta puerta verifica limpieza.
        comandos_lint.append("uvx nbstripout --verify .")

    # Conservar los nombres externos de las tareas mise, no los identificadores internos.
    emit("build", comandos_construccion)
    emit("test", comandos_prueba)
    emit("lint", comandos_lint)
```

Eliminar las declaraciones y las tres llamadas históricas que usaban `build_cmds`, `test_cmds` y `lint_cmds`; no deben coexistir dos acumuladores ni dos emisiones de la misma tarea.

- [ ] **Step 6: Verify GREEN after the mechanical refactor**

Run:

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pytest -q -p no:cacheprovider
```

Expected: Ruff commands exit 0 and toda la colección auditada pasa; el total no es un criterio de aceptación.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml scripts tests tramalia
git commit -m "style: establish Ruff baseline"
```

### Task 4: Crear el workflow obligatorio de validación

**Files:**
- Create: `tests/contratos/test_flujo_validacion.py`
- Create: `.github/workflows/validacion.yml`
- Delete: `.github/workflows/publish.yml` (reconstruye fuera de la validación y queda retirado hasta que el plan 04 instale Release/PyPI por artefacto)

**Interfaces:**
- Consumes: `uv.lock`, grupo `desarrollo`, suite verde y Ruff limpio.
- Produces: jobs `nucleo`, `calidad` y `paquete`; el plan 03 añadirá `plataformas` y `opcionales`, y el plan 04 añadirá `documentacion` y consumidores del artefacto.

- [ ] **Step 1: Write the failing workflow contract**

```python
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]
FLUJO_VALIDACION = RAIZ / ".github" / "workflows" / "validacion.yml"


def test_validacion_ejecuta_matriz_calidad_y_paquete() -> None:
    contenido = FLUJO_VALIDACION.read_text(encoding="utf-8")
    for version in ("3.11", "3.12", "3.13", "3.14"):
        assert f'"{version}"' in contenido
    for trabajo in ("nucleo:", "calidad:", "paquete:"):
        assert trabajo in contenido
    assert "uv run --no-sync pytest -q" in contenido
    assert "uv run --no-sync ruff check ." in contenido
    assert "uv run --no-sync ruff format --check ." in contenido
    assert "uv run --no-sync twine check dist/*.whl dist/*.tar.gz" in contenido
    assert "SOURCE_DATE_EPOCH" in contenido
    assert "dist/segunda" in contenido


def test_acciones_estan_fijadas_por_sha() -> None:
    contenido = FLUJO_VALIDACION.read_text(encoding="utf-8")
    assert "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0" in contenido
    assert "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1" in contenido
    assert "astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990" in contenido
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in contenido
    assert 'version: "0.11.28"' in contenido


def test_no_queda_publicacion_que_reconstruya_fuera_de_validacion() -> None:
    assert not (RAIZ / ".github" / "workflows" / "publish.yml").exists()
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/contratos/test_flujo_validacion.py -v`

Expected: FAIL with `FileNotFoundError` for `validacion.yml`.

- [ ] **Step 3: Create `.github/workflows/validacion.yml` and retire the unsafe publisher**

```yaml
name: validacion

on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  nucleo:
    name: Python ${{ matrix.python }}
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python: ["3.11", "3.12", "3.13", "3.14"]
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0
        with:
          python-version: ${{ matrix.python }}
      - uses: astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990 # v8.3.2
        with:
          version: "0.11.28"
          enable-cache: true
      - run: uv sync --locked --group desarrollo
      - run: uv run --no-sync pytest -q

  calidad:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0
        with:
          python-version: "3.14"
      - uses: astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990 # v8.3.2
        with:
          version: "0.11.28"
          enable-cache: true
      - run: uv sync --locked --group desarrollo
      - run: uv run --no-sync ruff check .
      - run: uv run --no-sync ruff format --check .

  paquete:
    needs: [nucleo, calidad]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0
        with:
          python-version: "3.13"
      - uses: astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990 # v8.3.2
        with:
          version: "0.11.28"
          enable-cache: true
      - run: uv sync --locked --group desarrollo
      - name: Fijar timestamp reproducible desde el commit
        run: echo "SOURCE_DATE_EPOCH=$(git log -1 --format=%ct)" >> "$GITHUB_ENV"
      - run: uv build --out-dir dist/primera
      - run: uv build --out-dir dist/segunda
      - name: Verificar build byte a byte y conservar una sola copia
        shell: bash
        run: |
          diff <(cd dist/primera && sha256sum *) <(cd dist/segunda && sha256sum *)
          cp dist/primera/*.whl dist/
          cp dist/primera/*.tar.gz dist/
      - run: uv run --no-sync twine check dist/*.whl dist/*.tar.gz
      - run: uv export --locked --no-dev --no-emit-project --no-hashes --format requirements.txt --output-file restricciones-ejecucion.txt
      - run: python -m venv .prueba-instalacion
      - run: .prueba-instalacion/bin/python -m pip install --constraint restricciones-ejecucion.txt dist/*.whl
      - run: .prueba-instalacion/bin/tramalia --version
      - uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: paquete
          path: |
            dist/*.whl
            dist/*.tar.gz
          if-no-files-found: error
```

Eliminar `.github/workflows/publish.yml` en esta misma tarea. Es preferible que la rama de estabilización no publique temporalmente a que conserve una segunda construcción no validada; el plan 04 restituye GitHub Release y PyPI como flujos separados que consumen este artefacto.

- [ ] **Step 4: Verify GREEN**

Run: `uv run pytest tests/contratos/test_flujo_validacion.py -v`

Expected: 3 passed.

- [ ] **Step 5: Run local equivalents**

Run:

```powershell
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv build
uv run twine check dist/*
```

Expected: every command exits 0 and `dist/` contains one wheel and one sdist.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/validacion.yml tests/contratos/test_flujo_validacion.py
git rm .github/workflows/publish.yml
git commit -m "ci: require tests quality checks and package smoke"
```

### Task 5: Sustituir el badge estático de tests por evidencia real

**Files:**
- Create: `tests/contratos/test_readme_estado.py`
- Modify: `README.md:1-15`
- Modify: `README.en.md:1-15`

**Interfaces:**
- Consumes: workflow `validacion.yml` del Task 4.
- Produces: badge enlazado a GitHub Actions y elimina la afirmación fija `250 passing`.

- [ ] **Step 1: Write the failing README contract**

```python
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]


def test_readmes_muestran_validacion_real_y_no_un_conteo_estatico() -> None:
    for nombre in ("README.md", "README.en.md"):
        contenido = (RAIZ / nombre).read_text(encoding="utf-8")
        assert "tests-250%20passing" not in contenido
        assert "actions/workflows/validacion.yml/badge.svg" in contenido
        assert "actions/workflows/validacion.yml" in contenido
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/contratos/test_readme_estado.py -v`

Expected: FAIL because both README files still contain the static badge.

- [ ] **Step 3: Replace the badge in both README files**

Use this Markdown in the badge block:

```markdown
[![Validación](https://github.com/MscottB/tramalia/actions/workflows/validacion.yml/badge.svg)](https://github.com/MscottB/tramalia/actions/workflows/validacion.yml)
```

In `README.en.md`, use `Validation` as the alt text but keep the same URLs.

- [ ] **Step 4: Verify GREEN and final baseline**

Run:

```powershell
uv run pytest tests/contratos/test_readme_estado.py -v
uv run pytest -q -p no:cacheprovider
uv run ruff check .
uv run ruff format --check .
git diff --check
```

Expected: README contract passes, the full suite passes, Ruff passes and Git reports no whitespace errors.

- [ ] **Step 5: Commit**

```bash
git add README.md README.en.md tests/contratos/test_readme_estado.py
git commit -m "docs: link test status to real validation"
```

## Plan 01 completion gate

Run:

```powershell
uv sync --locked --group desarrollo --all-extras
uv run pytest -q -p no:cacheprovider
uv run ruff check .
uv run ruff format --check .
uv build
uv run twine check dist/*
git status --short
```

Expected:

- all tests pass on the local Python runtime;
- Ruff and package checks exit 0;
- `uv sync --locked` confirma que `uv.lock` está actualizado y no lo modifica;
- sólo el `AGENTS.md` del usuario, no rastreado, permanece fuera de los commits.
