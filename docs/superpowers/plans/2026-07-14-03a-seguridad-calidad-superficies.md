# Seguridad, secretos y calidad UX/UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Incorporar una base reproducible de seguridad y calidad de experiencia antes del rediseño funcional de habilidades y de la CLI/TUI: Tramalia, sus habilidades, MCP y proyectos generados deben fallar de forma cerrada ante entradas inseguras; Semgrep y Gitleaks deben quedar instalables, fijados, probados y ejecutados en CI; y la documentación web debe verificarse con Playwright, axe y Lighthouse.

**Architecture:** Las herramientas externas siguen siendo procesos separados y no dependencias de ejecución de `tramalia-cli`. Un modelo de amenazas y una matriz versionada de controles gobiernan las decisiones sin presentar OWASP como certificación; el núcleo confina y publica de forma transaccional habilidades externas, y el adaptador MCP limita lectura, colisiones y salida antes de que Plan 03c añada perfiles/activación y Plan 03b los presente. Semgrep vive en el grupo de desarrollo `seguridad`, Gitleaks se obtiene desde un release fijo mediante un instalador que valida SHA-256 y límites de extracción, y las reglas/configuraciones permanecen versionadas en el repositorio. La calidad web usa un `package-lock.json` independiente y audita el sitio MkDocs ya construido. `tramalia.core.versiones_herramientas` será la fuente única para las versiones que el `doctor`, el instalador y el scaffold comunican a proyectos generados.

**Tech Stack:** Python 3.11–3.14, uv 0.11.28 en CI, Semgrep 1.169.0, Gitleaks 8.30.1, Node 24, `@playwright/test` 1.61.1, `@axe-core/playwright` 4.12.1, `@lhci/cli` 0.15.1, MkDocs Material, OWASP Top 10 2025, OWASP API Security Top 10 2023, ASVS 5.0.0, OWASP Agentic Skills Top 10 en revisión pública, OWASP MCP Top 10 v0.1, pytest y GitHub Actions fijadas por SHA.

## Global Constraints

- Ejecutar este plan después de Plan 03 Tasks 1–4. La secuencia bloqueante posterior es **03a → 03c → 03b**: 03c define perfiles, activación, permisos y contenido de habilidades; 03b consume esas interfaces y no las reimplementa.
- No añadir Semgrep, Gitleaks, Playwright, axe ni Lighthouse a las dependencias de ejecución del wheel.
- No usar `latest`, rangos flotantes, configuraciones Semgrep remotas ni `npx --yes` en puertas reproducibles.
- Gitleaks debe usar la interfaz moderna `gitleaks git`; no `detect`.
- Los escáneres deben ejecutarse tanto sobre Tramalia como sobre las plantillas y configuraciones que Tramalia genera.
- Una exclusión de seguridad requiere alcance mínimo, razón documentada y prueba que evite ampliarla accidentalmente.
- Los secretos reales encontrados se revocan y eliminan; nunca se resuelven con una allowlist.
- Los datos de ejemplo no deben parecer credenciales válidas si una forma claramente ficticia cubre el contrato.
- Lighthouse y axe validan la documentación web; la TUI se valida con Pilot y snapshots Textual en el plan 03b.
- Los nombres propios nuevos se escriben en español ASCII. Se conservan nombres impuestos como `package.json`, `package-lock.json`, `.gitleaks.toml`, GitHub Actions y comandos públicos de terceros.
- Los comentarios internos explican decisiones, límites o riesgos en español. **Excepción aprobada y deliberada:** las APIs públicas nuevas usan docstrings en inglés estilo Google para alimentar una referencia técnica estable con mkdocstrings; esta excepción no autoriza nombres propios ingleses nuevos.
- Cada cambio de comportamiento sigue TDD: prueba fallando, implementación mínima, refactor y regresión.
- OWASP se usa como catálogo de riesgos y requisitos versionados. Ningún documento, badge, gate o mensaje puede afirmar “cumplimiento OWASP”, “certificado” o equivalentes sólo porque pasen herramientas automáticas.
- Toda entrada proveniente de un repositorio, habilidad, Git remoto, MCP, archivo generado o proceso externo se trata como datos no confiables: se confina, valida, limita y sanea antes de publicarse o mostrarse.

---

## Estado comprobado al 16 de julio de 2026

```text
semgrep: no instalado en PATH
gitleaks: no instalado en PATH
node:    24.15.0
npm:     11.13.0
uv:      0.11.7 local; CI fijará 0.11.28
docker:  no instalado en PATH
mise:    no instalado en PATH
```

Plan 03 Tasks 1–4 está implementado hasta `3f0b8d5`; este plan 03a todavía no tiene implementación. Al no existir Docker local, los cuatro snapshots canónicos se generan y revisan desde el job Linux fijado de GitHub Actions; una máquina local puede ejecutar las pruebas funcionales, pero no aprobar baselines visuales.

Fuentes de versiones fijadas:

- Semgrep 1.169.0: `https://pypi.org/project/semgrep/`
- Gitleaks 8.30.1 y digests de activos: `https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1`
- Playwright 1.61.1: `https://www.npmjs.com/package/@playwright/test`
- axe para Playwright 4.12.1: `https://www.npmjs.com/package/@axe-core/playwright`
- Lighthouse CI 0.15.1: `https://www.npmjs.com/package/@lhci/cli`

Referencias de control fijadas para la matriz:

- OWASP Top 10 2025: `https://owasp.org/www-project-top-ten/`
- OWASP API Security Top 10 2023: `https://owasp.org/www-project-api-security/`
- OWASP ASVS 5.0.0: `https://owasp.org/www-project-application-security-verification-standard/`
- OWASP Agentic Skills Top 10, revisión pública v1: `https://owasp.org/www-project-agentic-skills-top-10/`
- OWASP MCP Top 10 v0.1: `https://owasp.org/www-project-mcp-top-10/`

## File map

| Ruta | Acción | Responsabilidad única |
|---|---|---|
| `docs/seguridad/modelo-amenazas.md` | Crear | Activos, actores, fronteras, invariantes, abusos y límites de la BETA. |
| `docs/seguridad/matriz-controles.md` | Crear | Aplicabilidad y evidencia versionada OWASP/ASVS/API/Agentic Skills/MCP, sin declarar certificación. |
| `tramalia/core/versiones_herramientas.py` | Crear | Versiones auditadas y especificaciones de instalación para seguridad y UX/UI. |
| `scripts/instalar_gitleaks.py` | Crear | Descargar el activo correcto, verificar SHA-256 y publicar el binario localmente de forma atómica. |
| `configuracion/semgrep/seguridad-python.yml` | Crear | Reglas Semgrep locales, revisables y sin red. |
| `tramalia/templates/project/.tramalia/configuracion/semgrep/seguridad-python.yml` | Crear | Copia local generada por Tramalia; la puerta de un proyecto nunca resuelve reglas remotas. |
| `.gitleaks.toml` | Crear | Extender reglas predeterminadas y acotar rutas generadas/artefactos, no hallazgos reales. |
| `.gitleaksignore` | Crear sólo si hay falsos positivos validados | Fingerprints individuales con justificación trazable. |
| `docs/seguridad/excepciones-gitleaks.md` | Crear | Registro de fingerprints históricos permitidos y su evidencia. |
| `package.json`, `package-lock.json` | Crear | Dependencias Node exactas y comandos UX/UI reproducibles. |
| `requirements-docs.txt` | Modificar temporalmente | Fijar las tres dependencias documentales directas hasta que Plan 04 genere el lock transitivo con hashes y nombre español. |
| `configuracion/playwright.mjs` | Crear | Navegador, servidor local, tamaños y artefactos de prueba. |
| `configuracion/lighthouse.cjs` | Crear | Tres mediciones locales y umbrales estables del sitio MkDocs. |
| `pruebas/ux/documentacion.spec.mjs` | Crear | Accesibilidad, teclado, adaptabilidad y snapshots web representativos. |
| `tramalia/core/integraciones.py` | Modificar | Mostrar sugerencias con versiones fijas desde la fuente única. |
| `tramalia/core/installer.py` | Modificar | Conservar versiones `@X` al derivar opciones mise/uv/npm. |
| `tramalia/core/scaffold.py` | Modificar | Generar herramientas fijadas y `gitleaks git`. |
| `tramalia/core/seguridad_entradas.py` | Crear | Confinamiento de nombres/rutas, fuentes HTTPS, árboles de habilidades y texto externo acotado. |
| `tramalia/core/habilidades.py` | Modificar | Manifiesto fail-closed, cuarentena, validación y publicación transaccional de checkouts. |
| `tramalia/mcp_server.py` | Modificar | Lecturas confinadas, salidas saneadas/acotadas y transporte stdio sin rutas absolutas. |
| `pyproject.toml`, `uv.lock` | Modificar | Grupo `seguridad`; ningún cambio en dependencias runtime del wheel. |
| `.github/workflows/validacion.yml` | Modificar | Jobs `seguridad` y `experiencia_web`, y dependencia del artefacto final. |
| `tests/unidad/test_instalador_gitleaks.py` | Crear | Selección de activo, digest, extracción y publicación atómica. |
| `tests/contratos/test_seguridad_estatica.py` | Crear | Contratos de versiones, reglas, configuración y CI. |
| `tests/contratos/test_modelo_seguridad.py` | Crear | Versiones, estados y evidencia mínima de la matriz de controles. |
| `tests/contratos/test_puertas_generadas.py` | Crear | Herramientas fijas y comandos modernos en proyectos generados. |
| `tests/unidad/test_seguridad_entradas.py` | Crear | Traversal, HTTPS, symlinks/reparse points, límites y saneamiento. |
| `tests/integracion/test_habilidades_seguras.py` | Crear | TOML inválido, staging, rollback y publicación transaccional. |
| `tests/integracion/test_mcp_seguridad.py` | Crear | Colisiones, symlinks fuera de raíz, límites y ausencia de filtraciones por MCP. |
| `tests/recursos/semgrep/inseguro.py` | Crear | Casos positivos y negativos deliberados para probar las reglas locales. |
| `tests/AUDITORIA.md` | Modificar | Registrar nuevos contratos por riesgo, sin convertir el conteo en meta. |

## Interfaces producidas y consumidas

```python
# tramalia/core/versiones_herramientas.py
VERSION_SEMGREP = "1.169.0"
VERSION_GITLEAKS = "8.30.1"
VERSION_LIGHTHOUSE_CI = "0.15.1"
VERSION_PLAYWRIGHT = "1.61.1"
VERSION_AXE_PLAYWRIGHT = "4.12.1"
VERSION_ACTIONLINT = "1.7.12"
VERSION_ACTIONLINT_PY = "1.7.12.24"

ESPECIFICACION_SEMGREP_MISE = f"pipx:semgrep@{VERSION_SEMGREP}"
ESPECIFICACION_GITLEAKS_MISE = f"aqua:gitleaks/gitleaks@{VERSION_GITLEAKS}"
ESPECIFICACION_LIGHTHOUSE_MISE = f"npm:@lhci/cli@{VERSION_LIGHTHOUSE_CI}"
ESPECIFICACION_PLAYWRIGHT_MISE = f"npm:playwright@{VERSION_PLAYWRIGHT}"
```

```python
# scripts/instalar_gitleaks.py
@dataclass(frozen=True, slots=True)
class ArtefactoGitleaks:
    sistema: str
    arquitectura: str
    nombre: str
    sha256: str

def resolver_artefacto(sistema: str, arquitectura: str) -> ArtefactoGitleaks: ...
def instalar(destino: Path, *, sistema: str | None = None,
             arquitectura: str | None = None) -> Path: ...
def main(argumentos: Sequence[str] | None = None) -> int: ...
```

El instalador soporta exactamente estas plataformas de CI/desarrollo:

| Sistema/arquitectura | Activo | SHA-256 |
|---|---|---|
| Windows x86_64 | `gitleaks_8.30.1_windows_x64.zip` | `d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e` |
| Windows arm64 | `gitleaks_8.30.1_windows_arm64.zip` | `b95f5e4f5c425cedca7ee203d9afd29597e692c4924a12ed42f970537c72cc0f` |
| Linux x86_64 | `gitleaks_8.30.1_linux_x64.tar.gz` | `551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb` |
| Linux arm64 | `gitleaks_8.30.1_linux_arm64.tar.gz` | `e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080` |
| macOS x86_64 | `gitleaks_8.30.1_darwin_x64.tar.gz` | `dfe101a4db2255fc85120ac7f3d25e4342c3c20cf749f2c20a18081af1952709` |
| macOS arm64 | `gitleaks_8.30.1_darwin_arm64.tar.gz` | `b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5` |

No se expone un descargador genérico. La URL siempre se deriva de versión + nombre permitidos. La descarga se escribe en un directorio temporal dentro del destino, se verifica antes de extraer y se publica con `os.replace`; nunca se ejecuta contenido sin verificar.

---

### Task 0: Fijar el modelo de amenazas y la matriz de controles verificables

**Files:**
- Create: `docs/seguridad/modelo-amenazas.md`
- Create: `docs/seguridad/matriz-controles.md`
- Create: `tests/contratos/test_modelo_seguridad.py`

**Interfaces:**
- Consumes: arquitectura implementada por Plan 03 Tasks 1–4 y referencias oficiales versionadas.
- Produces: IDs `TRM-SEC-001` a `TRM-SEC-010`, estados permitidos y evidencia que las Tasks 1–7 deben actualizar sin afirmar cumplimiento general.

- [ ] **Step 1: Escribir el contrato fallido del modelo y la matriz**

El test carga ambos Markdown como UTF-8 y exige estos encabezados exactos en el modelo:

```python
ENCABEZADOS_MODELO = (
    "## Activos protegidos",
    "## Actores y capacidades",
    "## Fronteras de confianza",
    "## Invariantes verificables",
    "## Casos de abuso",
    "## Riesgo residual y no objetivos",
)
```

La matriz usa una fila por ID `TRM-SEC-001` a `TRM-SEC-010` y sólo admite
`cubierto_por_prueba`, `parcial`, `no_aplica_justificado` y
`pendiente_bloqueante`. Debe contener las versiones literales `OWASP Top 10
2025`, `OWASP API Security Top 10 2023`, `ASVS 5.0.0`, `OWASP Agentic Skills
Top 10 — revisión pública v1` y `OWASP MCP Top 10 v0.1`. El contrato rechaza,
sin distinguir mayúsculas, `cumplimiento owasp`, `certificado por owasp` y
`100% owasp`.

- [ ] **Step 2: Ejecutar y observar documentos ausentes**

Run: `uv run --no-sync pytest tests/contratos/test_modelo_seguridad.py -q`

Expected: FAIL porque los dos documentos no existen.

- [ ] **Step 3: Documentar fronteras e invariantes concretos**

El modelo define como activos: código/plantillas, manifiestos y locks, evidencia
cruda, credenciales del entorno, configuración MCP, historial Git y artefactos
de release. Los actores son autor del proyecto, colaborador de PR, repositorio
Git remoto, autor de habilidad, servidor MCP/proceso externo y dependencia de
build. Las fronteras obligatorias son:

1. entrada de repositorio a parser/configuración;
2. Git remoto a cuarentena de habilidad;
3. cuarentena validada a directorio activo;
4. MCP/proceso a salida pública;
5. código de PR a runner de GitHub Actions;
6. herramienta descargada a ejecución local;
7. árbol fuente a documentación/artefacto publicado.

La matriz contiene exactamente estos controles propios y evidencia inicial:

| ID | Control | Referencias principales | Estado al crear la matriz |
|---|---|---|---|
| `TRM-SEC-001` | Confinar toda ruta y rechazar traversal/symlinks fuera de raíz | Top 10 2025; ASVS 5.0.0 | `pendiente_bloqueante` → Task 4 |
| `TRM-SEC-002` | Ejecutar procesos sin shell, con timeout y salida acotada | `ASVS v5.0.0-1.2.5`; MCP05 | `parcial` → Tasks 2 y 4 |
| `TRM-SEC-003` | Detectar secretos en historial y árbol de trabajo | Top 10 2025; MCP01 | `pendiente_bloqueante` → Task 3 |
| `TRM-SEC-004` | Fijar y verificar herramientas/artefactos externos | Top 10 2025; AST02/AST07; MCP04 | `pendiente_bloqueante` → Tasks 1, 5 y 7 |
| `TRM-SEC-005` | Validar habilidades antes de hacerlas visibles | AST01/AST03/AST04/AST05/AST06/AST08 | `pendiente_bloqueante` → Task 4 |
| `TRM-SEC-006` | Evitar colisiones, scope creep y sobreexposición MCP | MCP02/MCP03/MCP07/MCP09/MCP10 | `pendiente_bloqueante` → Task 4 |
| `TRM-SEC-007` | Mantener inventario, bloqueo y auditoría de cambios | AST09/AST10; MCP08 | `parcial` → Task 4 y Plan 03c |
| `TRM-SEC-008` | Generar puertas locales reproducibles y fail-closed | ASVS 5.0.0; API Security Top 10 2023 | `pendiente_bloqueante` → Task 5 |
| `TRM-SEC-009` | Verificar accesibilidad y adaptabilidad WCAG 2.2 AA | WCAG 2.2; calidad UX/UI | `pendiente_bloqueante` → Task 6 |
| `TRM-SEC-010` | Ejecutar CI de PR con privilegio mínimo y sin secretos | Top 10 2025; AST02; MCP04 | `pendiente_bloqueante` → Task 7 |

Cada fila enlaza una fuente oficial, una prueba/comando concreto y una columna
de limitación. Cuando una Task pasa, se puede cambiar su fila a
`cubierto_por_prueba` sólo si se enlaza la prueba exacta; una herramienta por sí
sola no basta.

- [ ] **Step 4: Verificar y commit**

Run: `uv run --no-sync pytest tests/contratos/test_modelo_seguridad.py -q`

Expected: PASS; no aparece ninguna afirmación de certificación.

```bash
git add docs/seguridad/modelo-amenazas.md docs/seguridad/matriz-controles.md tests/contratos/test_modelo_seguridad.py
git commit -m "docs: fijar modelo de amenazas y controles"
```

### Task 1: Fijar versiones e instalar Semgrep/Gitleaks de forma verificable

**Files:**
- Create: `tramalia/core/versiones_herramientas.py`
- Create: `scripts/instalar_gitleaks.py`
- Create: `tests/unidad/test_instalador_gitleaks.py`
- Modify: `pyproject.toml`
- Modify: `uv.lock`

**Interfaces:**
- Consumes: PyPI Semgrep 1.169.0 y activos oficiales Gitleaks 8.30.1.
- Produces: grupo uv `seguridad`, binario local verificado y constantes reutilizables.

- [ ] **Step 1: Escribir pruebas fallidas de resolución y seguridad del instalador**

Probar como mínimo:

```python
def test_resuelve_windows_x64_con_digest_oficial() -> None:
    artefacto = resolver_artefacto("windows", "x86_64")
    assert artefacto.nombre == "gitleaks_8.30.1_windows_x64.zip"
    assert artefacto.sha256 == "d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e"


def test_rechaza_plataforma_no_auditada() -> None:
    with pytest.raises(ValueError, match="plataforma no soportada"):
        resolver_artefacto("plan9", "x86_64")


def test_digest_incorrecto_no_publica_binario(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(instalador, "_descargar", lambda *_: b"contenido alterado")
    with pytest.raises(ErrorInstalacionGitleaks, match="SHA-256"):
        instalar(tmp_path, sistema="windows", arquitectura="x86_64")
    assert not (tmp_path / "gitleaks.exe").exists()
```

Añadir pruebas de archivo con ruta `../`, ZIP con más de un ejecutable, miembro
symlink/hardlink, permisos POSIX y sustitución atómica de una versión anterior.
Construir además ZIP y TAR sintéticos que declaren un miembro de más de 128 MiB,
una suma descomprimida de más de 160 MiB o más de 64 miembros: los tres casos
fallan antes de publicar y limpian el temporal. Inyectar `_descargar` en pruebas;
no acceder a red.

- [ ] **Step 2: Ejecutar y observar el fallo esperado**

Run: `uv run --no-sync pytest tests/unidad/test_instalador_gitleaks.py -q`

Expected: FAIL por módulos/símbolos ausentes.

- [ ] **Step 3: Implementar fuente única e instalador mínimo**

Añadir a `pyproject.toml` sin tocar `[project.dependencies]`:

```toml
[dependency-groups]
seguridad = [
    "actionlint-py==1.7.12.24",
    "semgrep==1.169.0",
]
```

El instalador usa `urllib.request.urlopen` con timeout 30 s, tamaño máximo de
descarga de 32 MiB, `zipfile`/`tarfile` de stdlib y estas constantes:

```python
MAXIMO_MIEMBROS_ARCHIVO = 64
MAXIMO_BYTES_MIEMBRO = 128 * 1024 * 1024
MAXIMO_BYTES_EXTRAIDOS = 160 * 1024 * 1024
```

Valida el tamaño declarado antes de abrir un miembro y vuelve a contabilizar los
bytes mientras copia por bloques de 1 MiB, por lo que una cabecera mentirosa
también falla. Sólo acepta archivos regulares, valida el nombre exacto del
ejecutable y rechaza symlinks, hardlinks, dispositivos y rutas absolutas o con
`..`. No invoca shell, PowerShell, `curl` ni el binario descargado durante la
instalación.

- [ ] **Step 4: Regenerar lock y probar instalación local real**

Run:

```powershell
uv lock --python 3.11
uv sync --locked --group desarrollo --group seguridad
uv tool install semgrep==1.169.0
$bin_uv = uv tool dir --bin
$nombre_semgrep = if ($IsWindows) { "semgrep.exe" } else { "semgrep" }
$ejecutable_semgrep = Join-Path $bin_uv $nombre_semgrep
& $ejecutable_semgrep --version
$ruta_gitleaks = uv run --no-sync python scripts/instalar_gitleaks.py --destino "$HOME/.local/bin" | Select-Object -Last 1
& $ruta_gitleaks version
```

`main()` imprime como última y única línea de stdout la ruta absoluta publicada;
diagnósticos van a stderr. En POSIX el nombre de Semgrep no lleva `.exe`; la
prueba de instalación resuelve el nombre según `os.name` y nunca presupone que
`$HOME/.local/bin` ya esté en PATH.

Ejecutar además `uv run --no-sync actionlint -version` y exigir que el binario
envuelto sea 1.7.12. `actionlint-py` queda fijado en 1.7.12.24 dentro del lock;
no se usa una action flotante ni un script `curl | sh`.

Expected: Semgrep `1.169.0`; Gitleaks `8.30.1`; Actionlint `1.7.12`; los binarios instalados y
ejecutables por su ruta verificada, sin modificar archivos del proyecto fuera de
`uv.lock`.

- [ ] **Step 5: Ejecutar pruebas y commit**

Run: `uv run --no-sync pytest tests/unidad/test_instalador_gitleaks.py -q`

Expected: PASS.

```bash
git add pyproject.toml uv.lock tramalia/core/versiones_herramientas.py scripts/instalar_gitleaks.py tests/unidad/test_instalador_gitleaks.py
git commit -m "build: fijar herramientas de seguridad"
```

### Task 2: Añadir reglas Semgrep locales, probadas y sin telemetría

**Files:**
- Create: `configuracion/semgrep/seguridad-python.yml`
- Create: `tramalia/templates/project/.tramalia/configuracion/semgrep/seguridad-python.yml`
- Create: `tests/recursos/semgrep/inseguro.py`
- Create: `tests/contratos/test_seguridad_estatica.py`

**Interfaces:**
- Consumes: código Python de `tramalia`, `scripts` y `tests`, excluyendo recursos deliberadamente inseguros.
- Produces: fallos CI por construcciones peligrosas con identificadores estables `tramalia.*`.

- [ ] **Step 1: Escribir el fixture Semgrep y contrato de configuración**

El fixture contiene pares `# ruleid:` / `# ok:` para:

- `eval` y `exec` sobre entrada no literal;
- `subprocess` con `shell=True`;
- `os.system` y `os.popen`;
- `subprocess.run`/`Popen` sin timeout en código de producción;
- `pickle.load` / `pickle.loads`;
- `yaml.load` sin cargador seguro;
- `tempfile.mktemp`;
- `requests` con `verify=False`;
- `requests`/`urllib.request.urlopen` sin timeout;
- `tarfile.extractall`/`zipfile.extractall` sin una frontera segura propia;
- `print()` directo dentro de una tool MCP, porque contamina o filtra por stdout.

El contrato Python debe exigir que los IDs sean exactamente:

```python
IDS_REQUERIDOS = {
    "tramalia.python.eval-exec",
    "tramalia.python.subprocess-shell",
    "tramalia.python.sistema-shell",
    "tramalia.python.proceso-sin-timeout",
    "tramalia.python.pickle-inseguro",
    "tramalia.python.yaml-inseguro",
    "tramalia.python.mktemp-inseguro",
    "tramalia.python.tls-sin-verificar",
    "tramalia.python.red-sin-timeout",
    "tramalia.python.extraccion-insegura",
    "tramalia.python.mcp-stdout-directo",
}
```

También debe fallar si aparece `p/python`, `auto`, una URL remota, `metrics: on`
o una exclusión de `tramalia/`. El contrato compara byte por byte la configuración
raíz y la copia empaquetada para proyectos generados; cambiar una exige actualizar
la otra en el mismo commit. Las únicas exclusiones por regla admitidas son tests
deliberadamente herméticos para `proceso-sin-timeout`; la prueba exige razón
`tests invocan procesos falsos o efimeros` y prohíbe excluir `tramalia/` o
`scripts/`.

- [ ] **Step 2: Ejecutar tests y confirmar que faltan las reglas**

Run: `uv run --no-sync pytest tests/contratos/test_seguridad_estatica.py -q`

Expected: FAIL por configuración ausente.

- [ ] **Step 3: Implementar reglas locales específicas**

Cada regla incluye `message` en español, `severity: ERROR`, `languages: [python]`, metadatos `categoria`, `cwe`, `tecnologia`, `control_tramalia` y `referencia`, y patrones suficientemente estrechos para que los `# ok:` no coincidan. Las reglas de procesos/red exigen el argumento nombrado `timeout`; la de extracción sólo permite el helper propio validado por Task 1/4. La regla MCP se limita a funciones decoradas con `@servidor.tool(...)`. No silenciar usos mediante comentarios Semgrep dentro de código de producción; si un uso es legítimo, refactorizarlo o acotar la regla con evidencia.

- [ ] **Step 4: Validar reglas y escanear el repositorio**

Run:

```powershell
uv run --no-sync semgrep --test --config configuracion/semgrep/seguridad-python.yml tests/recursos/semgrep
uv run --no-sync semgrep scan --config configuracion/semgrep/seguridad-python.yml --error --metrics=off --disable-version-check --exclude tests/recursos/semgrep tramalia scripts tests
```

Expected: las pruebas de reglas pasan y el código real no tiene hallazgos. Un hallazgo real se corrige mediante TDD antes de continuar; no se añade una exclusión general.

- [ ] **Step 5: Commit**

```bash
git add configuracion/semgrep tramalia/templates/project/.tramalia/configuracion/semgrep tests/recursos/semgrep tests/contratos/test_seguridad_estatica.py
git commit -m "test: incorporar analisis semgrep reproducible"
```

### Task 3: Escanear secretos del historial con Gitleaks moderno

**Files:**
- Create: `.gitleaks.toml`
- Create: `docs/seguridad/excepciones-gitleaks.md`
- Create if justified: `.gitleaksignore`
- Modify: `tests/contratos/test_seguridad_estatica.py`

**Interfaces:**
- Consumes: historial Git completo y árbol de trabajo.
- Produces: código 1 ante secretos; fingerprints individuales sólo para falsos positivos históricos validados.

- [ ] **Step 1: Añadir contratos fallidos para configuración e historial**

El test debe exigir `useDefault = true`, rechazar regex allowlist que cubra
`.env`, claves privadas, tokens o cualquier ruta fuente completa como `tramalia`,
`scripts`, `tests`, `docs` o `.github`, y verificar que cualquier línea no
comentada de `.gitleaksignore` aparezca además en
`docs/seguridad/excepciones-gitleaks.md` con ruta, regla, razón y revisión.

La única allowlist estructural de rutas admite exactamente directorios generados:

```toml
[[allowlists]]
description = "Directorios generados y dependencias; el código fuente no se excluye"
paths = [
  '''(^|/)(\.git|\.venv|node_modules|site|\.artefactos|dist|build|\.pytest_cache|\.mypy_cache|\.ruff_cache|__pycache__)(/|$)''',
]
```

El contrato compara el conjunto exacto y falla si se agrega otra ruta sin cambiar
la prueba y la matriz `TRM-SEC-003`. También exige
`--max-target-megabytes 10` en todos los comandos `gitleaks dir` propios y
generados; archivos fuente mayores se revisan explícitamente en vez de consumir
memoria sin límite.

- [ ] **Step 2: Ejecutar los baselines antes de crear excepciones**

Run:

```powershell
$nombre_gitleaks = if ($IsWindows) { "gitleaks.exe" } else { "gitleaks" }
$ruta_gitleaks = Join-Path "$HOME/.local/bin" $nombre_gitleaks
& $ruta_gitleaks git --redact --no-banner --exit-code 1
& $ruta_gitleaks dir . --redact --no-banner --max-target-megabytes 10 --exit-code 1
```

Expected: PASS o hallazgos concretos. Este baseline local puede encontrar entornos
ya creados, que quedan cubiertos sólo por la allowlist exacta anterior. En CI,
Task 7 ejecuta ambos comandos inmediatamente después del checkout y antes de uv,
npm, MkDocs, Playwright o cualquier script del repositorio. Para cada hallazgo:
determinar si es secreto real, ejemplo inseguro o falso positivo.
Revocar/eliminar secretos reales incluso si son históricos. Reescribir ejemplos
inseguros. Sólo un falso positivo histórico no sensible puede obtener un
fingerprint individual.

- [ ] **Step 3: Implementar configuración mínima y registro**

La configuración extiende las reglas predeterminadas con `[extend] useDefault = true` y contiene únicamente la allowlist estructural exacta de directorios generados. No excluye `tramalia/`, `scripts/`, `tests/`, `docs/`, `.github/`, plantillas ni historial. El documento explica que `gitleaks git` inspecciona commits y que `gitleaks dir .` inspecciona por separado el árbol de trabajo, incluidos archivos todavía no confirmados; ambos son obligatorios y ninguno sustituye al otro.

- [ ] **Step 4: Verificar contratos y escaneo completo**

Run:

```powershell
uv run --no-sync pytest tests/contratos/test_seguridad_estatica.py -q
$nombre_gitleaks = if ($IsWindows) { "gitleaks.exe" } else { "gitleaks" }
$ruta_gitleaks = Join-Path "$HOME/.local/bin" $nombre_gitleaks
& $ruta_gitleaks git --redact --no-banner --config .gitleaks.toml --exit-code 1
& $ruta_gitleaks dir . --redact --no-banner --config .gitleaks.toml --max-target-megabytes 10 --exit-code 1
```

Expected: PASS y cero secretos no justificados.

- [ ] **Step 5: Commit**

```bash
git add .gitleaks.toml .gitleaksignore docs/seguridad/excepciones-gitleaks.md tests/contratos/test_seguridad_estatica.py
git commit -m "test: bloquear secretos con gitleaks"
```

Si `.gitleaksignore` no fue necesaria, no crearla ni incluirla en `git add`.

### Task 4: Endurecer habilidades y MCP antes de ampliar su administración

**Files:**
- Create: `tramalia/core/seguridad_entradas.py`
- Modify: `tramalia/core/errores.py`
- Modify: `tramalia/core/habilidades.py`
- Modify: `tramalia/core/scaffold.py`
- Modify: `tramalia/core/versiones_herramientas.py`
- Modify: `tramalia/mcp_server.py`
- Modify: `.gitignore`
- Create: `tests/unidad/test_seguridad_entradas.py`
- Create: `tests/integracion/test_habilidades_seguras.py`
- Create: `tests/integracion/test_mcp_seguridad.py`
- Modify: `tests/integracion/test_habilidades_git.py`
- Modify: `tests/test_tools_and_skills.py`
- Modify: `tests/test_v014.py`
- Modify: `tests/test_engram.py`

**Interfaces:**
- Consumes: locks SHA implementados por Plan 03 y `TRM-SEC-001`, `TRM-SEC-005`, `TRM-SEC-006` y `TRM-SEC-007`.
- Produces: validadores fail-closed, publicación transaccional de habilidades y MCP stdio con lecturas/salidas confinadas. Plan 03c amplía metadatos/perfiles sin relajar estas fronteras.

```python
# tramalia/core/seguridad_entradas.py
@dataclass(frozen=True, slots=True)
class ResumenArbolHabilidad:
    archivos: int
    bytes_totales: int

def validar_nombre_habilidad(nombre: str) -> str: ...
def validar_fuente_git(fuente: str) -> str: ...
def resolver_ruta_confinada(raiz: Path, relativa: Path, *, permitir_ausente: bool = False) -> Path: ...
def validar_arbol_habilidad(ruta: Path) -> ResumenArbolHabilidad: ...
def leer_texto_confinado(raiz: Path, relativa: Path, *, maximo_bytes: int = 131_072) -> str: ...
def sanear_texto_externo(valor: object, *, maximo_bytes: int = 131_072,
                         maximo_linea: int = 8_192) -> str: ...
```

Los docstrings de estas APIs públicas son inglés estilo Google por la excepción
global aprobada; nombres, errores, variables y comentarios propios permanecen en
español ASCII.

- [ ] **Step 1: Escribir pruebas RED de entradas, árboles y manifiestos**

`tests/unidad/test_seguridad_entradas.py` cubre como mínimo:

```python
@pytest.mark.parametrize("nombre", ("../escape", "..\\escape", "/tmp/x", "C:\\x", "CON", "a/b", "a\\b", ""))
def test_nombre_habilidad_rechaza_rutas_y_dispositivos(nombre: str) -> None:
    with pytest.raises(ErrorEntradaInsegura, match="nombre de habilidad"):
        validar_nombre_habilidad(nombre)

@pytest.mark.parametrize("fuente", ("http://example.com/x.git", "git+http://example.com/x.git", "file:///tmp/x", "ssh://host/x"))
def test_fuente_habilidad_exige_https(fuente: str) -> None:
    with pytest.raises(ErrorEntradaInsegura, match="HTTPS"):
        validar_fuente_git(fuente)
```

El patrón válido exacto es `[a-z0-9](?:[a-z0-9._-]{0,62}[a-z0-9])?`; se
rechazan `CON`, `PRN`, `AUX`, `NUL`, `COM1`–`COM9` y `LPT1`–`LPT9` sin distinguir
mayúsculas. Se aceptan únicamente `https://...` y `git+https://...`, que se
normalizan a `git+https://...`.

Crear casos de symlink de archivo/directorio y, en Windows, reparse point
simulado mediante `st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT`.
`validar_arbol_habilidad` rechaza enlaces, `.gitmodules`, entradas Git modo
`120000`/`160000`, más de 2.000 archivos, un archivo mayor de 4 MiB o total mayor
de 64 MiB. `resolver_ruta_confinada` compara `resolve(strict=False)` con la raíz
y nunca usa prefijos de string.

En integración, escribir `.tramalia/habilidades.toml` inválido y exigir
`ErrorConfiguracionHabilidades`; nunca se traduce a catálogo vacío. Añadir un
nombre `../../escape` explícito y demostrar que no se crea ningún archivo fuera
de `.tramalia`.

- [ ] **Step 2: Ejecutar las pruebas de seguridad y observar fallos**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_seguridad_entradas.py tests/integracion/test_habilidades_seguras.py -q
```

Expected: FAIL por módulo/errores ausentes y porque el parser actual devuelve
`()` ante TOML inválido.

- [ ] **Step 3: Implementar validadores fail-closed y límites exactos**

Añadir `ErrorEntradaInsegura` (`codigo = "entrada_insegura"`) y
`ErrorConfiguracionHabilidades` (`codigo = "configuracion_habilidades_invalida"`)
a `errores.py`. `_datos_manifiesto()` deja de capturar
`tomllib.TOMLDecodeError`; lo convierte al error tipado con ruta relativa y sin
incluir los bytes del manifiesto. Validar nombre/fuente tanto al leer como al
agregar; una declaración insegura invalida el manifiesto completo.

`sanear_texto_externo` elimina ANSI/OSC, NUL y controles C0 salvo `\n`/`\t`,
trunca cada línea a 8.192 bytes y el total a 131.072 bytes agregando
`\n[TRUNCADO: <n> bytes omitidos]`. Redacta valores de asignaciones cuyo nombre
contenga `token`, `secret`, `password`, `contrasena`, `api_key` o
`authorization`; nunca llama a `repr()` de objetos arbitrarios.

- [ ] **Step 4: Hacer transaccional la sincronización de habilidades**

Antes de tocar un checkout visible, `sincronizar_habilidades()`:

1. valida todo el manifiesto y su lock;
2. crea `.tramalia/.cuarentena-habilidades/<uuid>/` en el mismo volumen;
3. clona cada habilidad con `--no-checkout --no-recurse-submodules` y fuente HTTPS;
4. usa `git ls-tree -r` para rechazar modos `120000` y `160000` antes del checkout;
5. hace checkout detached del SHA esperado dentro de la cuarentena;
6. ejecuta `validar_arbol_habilidad` sin seguir enlaces;
7. prepara el lock nuevo y todos los reemplazos;
8. mueve cada destino anterior a un backup hermano, publica cada staging con
   `Path.replace()` y publica el lock al final;
9. si cualquier reemplazo falla, restaura todos los backups en orden inverso y
   conserva byte por byte el lock anterior;
10. elimina cuarentena/backups tanto al completar como al fallar.

Una prueba con dos repositorios locales fuerza fallo al publicar el segundo y
exige que contenido, SHA visible y lock de ambos sean idénticos al estado
anterior. Otra interrumpe después de staging y comprueba que ningún archivo no
validado aparece bajo `.tramalia/habilidades/`. El directorio de cuarentena se
añade al bloque administrado de `.gitignore`.

- [ ] **Step 5: Fijar MCP y cerrar lectura/salida**

Añadir a `versiones_herramientas.py`:

```python
VERSION_SERENA = "1.6.0"
SHA_SERENA = "93b9544ea9def8e93cb6a90f8ea67befe3c8fee4"
FUENTE_SERENA = f"git+https://github.com/oraios/serena.git@{SHA_SERENA}"
```

El scaffold usa `FUENTE_SERENA`; ningún `git+https` generado queda sin
`@<sha-completo>`. Reemplazar `_merge_mcp()` por un resultado tipado con estados
`sin_cambios`, `fusionado`, `json_invalido` y `conflicto`. Si un nombre existente
tiene comando/argumentos diferentes, `adopt` conserva bytes y devuelve
`conflicto`; nunca acepta silenciosamente un servidor homónimo.

En `mcp_server.py`, `_leer` llama `leer_texto_confinado` y rechaza un archivo
symlink cuyo destino salga del repositorio. `_valor_publico(Path)` sólo devuelve
rutas POSIX relativas confinadas; fuera de raíz devuelve
`[RUTA_FUERA_DEL_PROYECTO]`. Toda salida de herramienta y error pasa por
`sanear_texto_externo`; tools de lectura tienen máximo 128 KiB. El servidor
continúa exclusivamente en stdio, no añade HTTP/SSE ni autenticación aparente.

`tests/integracion/test_mcp_seguridad.py` prueba AGENTS symlink hacia un secreto,
servidor `serena` homónimo, texto con ANSI/OSC, una línea de 20 KiB, total de
200 KiB, `authorization=valor-real` y un `Path` externo. Ningún resultado puede
contener el secreto, la ruta absoluta, el escape o más de 132 KiB serializados.

- [ ] **Step 6: Ejecutar regresión y escáneres locales**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_seguridad_entradas.py tests/integracion/test_habilidades_seguras.py tests/integracion/test_habilidades_git.py tests/integracion/test_mcp_seguridad.py tests/integracion/test_mcp_operaciones.py tests/test_tools_and_skills.py tests/test_v014.py tests/test_engram.py -q
uv run --no-sync semgrep scan --config configuracion/semgrep/seguridad-python.yml --error --metrics=off --disable-version-check --exclude tests/recursos/semgrep tramalia scripts tests
```

Expected: PASS; no actualización parcial, lectura fuera de raíz, fuente HTTP,
salida MCP no acotada ni configuración Serena flotante.

- [ ] **Step 7: Actualizar matriz y commit**

Cambiar `TRM-SEC-001`, `TRM-SEC-005` y `TRM-SEC-006` a
`cubierto_por_prueba`; mantener `TRM-SEC-007` en `parcial` porque perfiles,
permisos, activación y gobernanza completa pertenecen a Plan 03c.

```bash
git add tramalia/core/seguridad_entradas.py tramalia/core/errores.py tramalia/core/habilidades.py tramalia/core/scaffold.py tramalia/core/versiones_herramientas.py tramalia/mcp_server.py .gitignore tests docs/seguridad/matriz-controles.md
git commit -m "fix: confinar habilidades y transporte mcp"
```

### Task 5: Corregir las herramientas y puertas que genera Tramalia

**Files:**
- Modify: `tramalia/core/integraciones.py`
- Modify: `tramalia/core/installer.py`
- Modify: `tramalia/core/scaffold.py`
- Create: `scripts/generar_proyecto_prueba_seguridad.py`
- Create: `tests/contratos/test_puertas_generadas.py`
- Modify: `tests/test_v017.py`
- Modify: `tests/test_tools_and_skills.py`

**Interfaces:**
- Consumes: constantes de `versiones_herramientas.py`.
- Produces: `mise.toml` sin `latest`, configuración Semgrep local empaquetada, sugerencias instalables y puertas públicas compatibles `security`/`ux` modernas. Esos dos IDs se conservan por compatibilidad pública; toda API interna nueva usa español ASCII.

- [ ] **Step 1: Escribir contratos fallidos de proyecto generado**

```python
def test_seguridad_generada_fija_versiones_y_usa_gitleaks_git() -> None:
    contenido = build_mise_toml({"stacks": ["python"], "features": ["security"]})
    assert '"pipx:semgrep" = "1.169.0"' in contenido
    assert '"aqua:gitleaks/gitleaks" = "8.30.1"' in contenido
    assert "gitleaks git --redact --no-banner" in contenido
    assert "gitleaks dir . --redact --no-banner --max-target-megabytes 10" in contenido
    assert "semgrep scan --config .tramalia/configuracion/semgrep/seguridad-python.yml" in contenido
    assert "gitleaks detect" not in contenido
    assert '"latest"' not in contenido


def test_ux_generada_fija_lighthouse_y_playwright() -> None:
    contenido = build_mise_toml({"stacks": ["react"], "features": ["ux"]})
    assert '"npm:@lhci/cli" = "0.15.1"' in contenido
    assert '"npm:playwright" = "1.61.1"' in contenido
    assert "lhci autorun" in contenido
    assert "playwright test" in contenido
```

Añadir paridad entre sugerencias del registro, opciones derivadas del instalador y versiones del scaffold. Verificar que `uv tool install semgrep==1.169.0` y `npm install -g @lhci/cli@0.15.1` conservan el pin. Una integración, omitida sólo si `mise` no está disponible, ejecuta `mise ls-remote aqua:gitleaks/gitleaks` y `mise use --dry-run aqua:gitleaks/gitleaks@8.30.1` (o el modo equivalente sin escritura de la versión fijada) para demostrar que el backend oficial resuelve realmente; comparar un string no basta. El script español genera en una raíz indicada el proyecto canónico máximo (stacks/features combinados) mediante el scaffold real, sin copiar fixtures manuales; su contrato comprueba rutas confinadas, salida determinista y que la configuración Semgrep generada es byte por byte la copia local auditada.

- [ ] **Step 2: Ejecutar y observar drift actual**

Run: `uv run --no-sync pytest tests/contratos/test_puertas_generadas.py tests/test_v017.py tests/test_tools_and_skills.py -q`

Expected: FAIL por `latest`, `gitleaks detect` y sugerencias sin versión.

- [ ] **Step 3: Centralizar versiones y corregir comandos**

`integraciones.py` importa constantes; no copia literales. `installer._from_hint()` conserva `@version` al traducir `mise use pipx:...`, `mise use npm:...` y `mise use aqua:...`. La puerta `security` ejecuta `gitleaks git`, `gitleaks dir . --max-target-megabytes 10` y Semgrep con `--config .tramalia/configuracion/semgrep/seguridad-python.yml --metrics=off --disable-version-check`, de forma secuencial y fail-closed. La puerta `ux` no instala navegadores ni dependencias durante el gate: informa cómo preparar el proyecto si faltan.

- [ ] **Step 4: Ejecutar regresión de scaffold/instalación**

Run:

```powershell
uv run --no-sync pytest tests/contratos/test_puertas_generadas.py tests/test_v017.py tests/test_v022.py tests/test_doctor.py tests/test_tools_and_skills.py tests/test_instalacion_unificada.py -q
uv run --no-sync python scripts/generar_proyecto_prueba_seguridad.py --salida .artefactos/seguridad/proyecto-generado
uv run --no-sync semgrep scan --config .artefactos/seguridad/proyecto-generado/.tramalia/configuracion/semgrep/seguridad-python.yml --error --metrics=off --disable-version-check .artefactos/seguridad/proyecto-generado
$nombre_gitleaks = if ($IsWindows) { "gitleaks.exe" } else { "gitleaks" }
$ruta_gitleaks = Join-Path "$HOME/.local/bin" $nombre_gitleaks
& $ruta_gitleaks dir .artefactos/seguridad/proyecto-generado --redact --no-banner --config .gitleaks.toml --max-target-megabytes 10 --exit-code 1
```

Expected: PASS; ningún test espera versiones flotantes.

- [ ] **Step 5: Commit**

```bash
git add tramalia/core/versiones_herramientas.py tramalia/core/integraciones.py tramalia/core/installer.py tramalia/core/scaffold.py scripts/generar_proyecto_prueba_seguridad.py tests
git commit -m "fix: generar puertas de seguridad reproducibles"
```

### Task 6: Auditar MkDocs con Playwright, axe y Lighthouse

**Files:**
- Create: `package.json`
- Create: `package-lock.json`
- Create: `configuracion/playwright.mjs`
- Create: `configuracion/lighthouse.cjs`
- Create: `pruebas/ux/documentacion.spec.mjs`
- Create: `pruebas/ux/entorno_capturas.test.mjs`
- Create: `scripts/verificar_aprobacion_capturas_ux.mjs`
- Create: `scripts/servir_documentacion.mjs`
- Create: `pruebas/ux/servidor_documentacion.test.mjs`
- Modify: `.gitignore`
- Modify: `requirements-docs.txt`

**Interfaces:**
- Consumes: `site/` construido por `mkdocs build --strict`.
- Produces: resultados Playwright, snapshots web y reportes Lighthouse bajo `.artefactos/ux/`.

- [ ] **Step 1: Crear manifiesto Node exacto y lock**

```json
{
  "name": "tramalia-pruebas-ux",
  "private": true,
  "engines": {"node": ">=24 <25"},
  "scripts": {
    "instalar:navegador:ux": "playwright install chromium",
    "instalar:navegador:ci": "playwright install --with-deps chromium",
    "prueba:ux": "playwright test --config configuracion/playwright.mjs",
    "prueba:lighthouse": "lhci autorun --config=configuracion/lighthouse.cjs",
    "prueba:guardia-capturas": "node --test pruebas/ux/entorno_capturas.test.mjs",
    "prueba:servidor-documentacion": "node --test pruebas/ux/servidor_documentacion.test.mjs",
    "aprobar:capturas:ux": "node scripts/verificar_aprobacion_capturas_ux.mjs && playwright test --config configuracion/playwright.mjs --update-snapshots"
  },
  "devDependencies": {
    "@axe-core/playwright": "4.12.1",
    "@lhci/cli": "0.15.1",
    "@playwright/test": "1.61.1"
  }
}
```

Run: `npm install --package-lock-only --ignore-scripts`

Expected: `package-lock.json` fija todas las dependencias y `npm ci --ignore-scripts` es reproducible.

Fijar también las entradas documentales actuales, sin adelantar todavía el lock transitivo de Plan 04:

```text
mkdocs-material==9.7.6
mkdocs-static-i18n==1.3.1
mkdocs-minify-plugin==0.8.0
```

- [ ] **Step 2: Escribir pruebas de experiencia antes de configurar el servidor**

`documentacion.spec.mjs` debe recorrer `/`, `/en/`, `/interfaz/` y `/en/interfaz/` y comprobar:

- cero violaciones axe con tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa` y `best-practice`;
- `html[lang]`, un `h1`, enlace de salto y landmarks principales;
- navegación completa sólo con teclado, orden lógico y foco visible con al menos 2 px de indicador no recortado;
- ausencia de overflow horizontal a 320×800, 390×844, 768×1024 y 1440×900;
- reflow sin scroll bidimensional al inyectar `html { font-size: 200% }` sobre un viewport 1280×900;
- temas claro y oscuro por separado, ambos con axe y contraste automatizado;
- `prefers-reduced-motion: reduce`: transiciones/animaciones no esenciales quedan en `0s` o `0.01ms` y la navegación sigue operativa;
- capturas visuales sólo de inicio e interfaz, a 390×844 y 1440×900, cuando `process.platform === "linux"` y `TRAMALIA_COMPARAR_CAPTURAS=1`; en el resto de ejecuciones esas cuatro aserciones se omiten de forma explícita, pero axe, teclado, contraste y overflow sí se ejecutan.

No excluir reglas axe por ID en el test. Una limitación demostrada se documenta y corrige en HTML/CSS; no se convierte en exclusión silenciosa. El test de 200 % aumenta texto, no `deviceScaleFactor`: densidad de píxeles no demuestra reflow.

`entorno_capturas.test.mjs` importa la función sin lanzar procesos y cubre Linux
con marcador exacto, Linux sin/marcador distinto y Windows/macOS. El helper usa
este contrato explícito:

```javascript
export function validarEntornoAprobacion(plataforma, marcador) {
  if (plataforma !== "linux" || marcador !== "1.61.1-noble") {
    throw new Error("Los snapshots solo se aprueban en Playwright 1.61.1 noble.");
  }
}
```

Al ejecutarse como CLI llama esa función con `process.platform` y
`process.env.TRAMALIA_IMAGEN_PLAYWRIGHT`; importar el módulo no tiene efectos.
Este marcador es una guardia contra errores, no una atestación imposible de
suplantar: la reproducibilidad se demuestra porque comandos/CI ejecutan realmente
la imagen Docker fijada y las capturas se revisan manualmente.

- [ ] **Step 3: Ejecutar y observar el fallo de configuración ausente**

Run:

```powershell
uv pip install -r requirements-docs.txt
uv run --no-sync mkdocs build --strict
npm ci --ignore-scripts
npm run prueba:guardia-capturas
npm run prueba:servidor-documentacion
npm run instalar:navegador:ux
npm run prueba:ux
```

Expected: FAIL hasta que existan configuración, servidor y snapshots revisados.

- [ ] **Step 4: Implementar configuración Playwright y Lighthouse**

`configuracion/playwright.mjs` usa un único worker en CI, `baseURL=http://127.0.0.1:8765`, `webServer.command="node scripts/servir_documentacion.mjs --raiz site --puerto 8765 --host 127.0.0.1"`, conserva trace y screenshot sólo al fallar y escribe todo bajo `.artefactos/ux/playwright`. El servidor usa sólo módulos Node stdlib, confina/decodifica rutas, sirve `index.html` para directorios, rechaza traversal y enlaza únicamente loopback; su prueba Node levanta un temporal y cubre 200/404/403, tipos MIME y cierre limpio. No depender de Python ni `npx http-server`, porque la imagen canónica no los garantiza.

`configuracion/lighthouse.cjs` importa `chromium` desde el paquete `playwright` fijado transitivamente por `@playwright/test` y configura la propiedad directa `ci.collect.chromePath = chromium.executablePath()` (no dentro de `settings`). Así LHCI usa exactamente el Chromium instalado por Playwright 1.61.1, nunca Chrome flotante del runner. Usa además `staticDistDir: "./site"`, `numberOfRuns: 3`, carga `/`, `/en/`, `/interfaz/` y exige:

```javascript
assertions: {
  "categories:accessibility": ["error", {minScore: 0.95}],
  "categories:best-practices": ["error", {minScore: 0.90}],
  "categories:performance": ["error", {minScore: 0.85}],
  "categories:seo": ["error", {minScore: 0.90}]
}
```

No subir reportes a almacenamiento temporal público; `upload.target` es `filesystem` bajo `.artefactos/ux/lighthouse`.

- [ ] **Step 5: Corregir hallazgos reales y aprobar snapshots sólo en Linux fijado**

Cada corrección de HTML/CSS se realiza en el archivo fuente MkDocs correspondiente. `snapshotPathTemplate` no incorpora el sistema anfitrión y las pruebas visuales exigen además `TRAMALIA_COMPARAR_CAPTURAS=1`. `verificar_aprobacion_capturas_ux.mjs` exporta una función pura probada y, como CLI, exige Linux y `TRAMALIA_IMAGEN_PLAYWRIGHT=1.61.1-noble`; falla en Windows/macOS o con marcador distinto. La aprobación canónica se ejecuta mediante `mcr.microsoft.com/playwright:v1.61.1-noble`, con la misma versión de Playwright del lock. Revisar visualmente los cuatro PNG generados antes de guardarlos. CI compara en la misma imagen y nunca actualiza snapshots.

Run:

```powershell
npm run prueba:ux
npm run prueba:guardia-capturas
npm run prueba:servidor-documentacion
docker run --rm --ipc=host --env CI=1 --env TRAMALIA_COMPARAR_CAPTURAS=1 --volume "${PWD}:/trabajo" --workdir /trabajo mcr.microsoft.com/playwright:v1.61.1-noble@sha256:5b8f294aff9041b7191c34a4bab3ac270157a28774d4b0660e9743297b697e48 bash -lc "npm ci --ignore-scripts && npm run prueba:ux"
```

Expected en el primer ciclo RED: la comparación canónica Linux falla únicamente
porque faltan o divergen los cuatro baselines; las pruebas funcionales/servidor
ya pasan. Revisar ese fallo antes de aprobar. Luego ejecutar:

```powershell
docker run --rm --ipc=host --env CI=1 --env TRAMALIA_IMAGEN_PLAYWRIGHT=1.61.1-noble --env TRAMALIA_COMPARAR_CAPTURAS=1 --volume "${PWD}:/trabajo" --workdir /trabajo mcr.microsoft.com/playwright:v1.61.1-noble@sha256:5b8f294aff9041b7191c34a4bab3ac270157a28774d4b0660e9743297b697e48 bash -lc "npm ci --ignore-scripts && npm run aprobar:capturas:ux"
docker run --rm --ipc=host --env CI=1 --env TRAMALIA_COMPARAR_CAPTURAS=1 --volume "${PWD}:/trabajo" --workdir /trabajo mcr.microsoft.com/playwright:v1.61.1-noble@sha256:5b8f294aff9041b7191c34a4bab3ac270157a28774d4b0660e9743297b697e48 bash -lc "npm ci --ignore-scripts && npm run prueba:ux"
npm run prueba:lighthouse
```

Expected: las pruebas funcionales locales, Playwright Linux y Lighthouse pasan; los reportes quedan ignorados por Git y sólo los cuatro snapshots Linux revisados quedan versionados. Como Docker no está disponible en el entorno local comprobado, la primera aprobación usa un `workflow_dispatch` temporal de la misma rama que ejecuta la imagen fijada, sube únicamente los cuatro candidatos durante 3 días y exige revisión visual humana antes de incorporarlos; el workflow temporal se elimina en el mismo commit de aprobación. Nunca aprobar rasters Windows como canónicos.

- [ ] **Step 6: Commit**

```bash
git add package.json package-lock.json requirements-docs.txt configuracion pruebas/ux scripts/verificar_aprobacion_capturas_ux.mjs scripts/servir_documentacion.mjs .gitignore docs mkdocs.yml
git commit -m "test: auditar experiencia de documentacion web"
```

### Task 7: Integrar seguridad y UX/UI en CI sin privilegios excesivos

**Files:**
- Modify: `.github/workflows/validacion.yml`
- Modify: `tests/contratos/test_seguridad_estatica.py`
- Modify: `tests/contratos/test_flujo_validacion.py`
- Modify: `tests/AUDITORIA.md`
- Modify: `docs/seguridad/matriz-controles.md`

**Interfaces:**
- Consumes: lock uv, lock npm, reglas locales, instalador Gitleaks y sitio MkDocs.
- Produces: jobs bloqueantes `seguridad` y `experiencia_web`; `paquete` espera ambos.

- [ ] **Step 1: Escribir contratos CI fallidos**

Exigir por parseo YAML/texto estructural:

- el workflow no contiene `pull_request_target`, `permissions: write-all`, secretos en `env`/`with` ni interpolaciones `${{ secrets.`; todo checkout de validación declara `persist-credentials: false` y el workflow parte de `permissions: {}`;
- `seguridad` usa `fetch-depth: 0`, permisos `contents: read`, grupo uv `seguridad`, Actionlint 1.7.12 sobre todos los workflows, Semgrep local, `gitleaks git` y `gitleaks dir . --max-target-megabytes 10` con la misma configuración;
- el binario Gitleaks procede de `scripts/instalar_gitleaks.py`, no de `curl | sh`, tag flotante o action no fijada;
- `experiencia_web` usa `actions/setup-node@820762786026740c76f36085b0efc47a31fe5020` (`v7.0.0`) con `node-version: "24.18.0"`, comprueba `node --version` igual a `v24.18.0`, ejecuta `npm ci --ignore-scripts`, `npm run prueba:guardia-capturas` y `npm run prueba:servidor-documentacion`, instala sólo Chromium, exige `ci.collect.chromePath: chromium.executablePath()` para LHCI y construye MkDocs estricto antes de UX; las pruebas funcionales corren en el runner y la comparación visual corre además dentro de `mcr.microsoft.com/playwright:v1.61.1-noble@sha256:5b8f294aff9041b7191c34a4bab3ac270157a28774d4b0660e9743297b697e48` con `CI=1` y `TRAMALIA_COMPARAR_CAPTURAS=1`;
- ningún job de validación despliega Pages, publica reportes externamente ni obtiene permisos de escritura;
- los artefactos UX de fallo tienen `retention-days: 3` y nunca incluyen cookies, storage state, variables de entorno ni el directorio `.git`;
- `paquete.needs` incluye `seguridad` y `experiencia_web`.

- [ ] **Step 2: Ejecutar contratos y observar jobs ausentes**

Run: `uv run --no-sync pytest tests/contratos/test_seguridad_estatica.py tests/contratos/test_flujo_validacion.py -q`

Expected: FAIL por jobs ausentes.

- [ ] **Step 3: Implementar jobs y artefactos sólo al fallar**

`seguridad` ejecuta:

```yaml
- run: python scripts/instalar_gitleaks.py --destino "$RUNNER_TEMP/herramientas"
- run: $RUNNER_TEMP/herramientas/gitleaks git --redact --no-banner --config .gitleaks.toml --exit-code 1
- run: $RUNNER_TEMP/herramientas/gitleaks dir . --redact --no-banner --config .gitleaks.toml --max-target-megabytes 10 --exit-code 1
- run: uv sync --locked --group desarrollo --group seguridad
- run: uv run --no-sync actionlint
- run: uv run --no-sync semgrep --test --config configuracion/semgrep/seguridad-python.yml tests/recursos/semgrep
- run: uv run --no-sync semgrep scan --config configuracion/semgrep/seguridad-python.yml --error --metrics=off --disable-version-check --exclude tests/recursos/semgrep tramalia scripts tests
- run: uv run --no-sync python scripts/generar_proyecto_prueba_seguridad.py --salida .artefactos/seguridad/proyecto-generado
- run: uv run --no-sync semgrep scan --config .artefactos/seguridad/proyecto-generado/.tramalia/configuracion/semgrep/seguridad-python.yml --error --metrics=off --disable-version-check .artefactos/seguridad/proyecto-generado
- run: $RUNNER_TEMP/herramientas/gitleaks dir .artefactos/seguridad/proyecto-generado --redact --no-banner --config .gitleaks.toml --max-target-megabytes 10 --exit-code 1
```

En Windows local el ejecutable lleva `.exe`; el workflow de seguridad corre en Ubuntu y usa la ruta mostrada. Gitleaks se instala en `RUNNER_TEMP` mediante el único script permitido antes del escaneo y revisa el checkout limpio antes de crear `.venv`, `node_modules`, `site`, artefactos o ejecutar cualquier otro script del repositorio. Las pruebas unitarias cubren las demás plataformas.

`experiencia_web` fija Node 24.18.0 mediante el bloque `with` de setup-node y lo verifica antes de instalar. Instala las tres dependencias directas exactas de `requirements-docs.txt`, ejecuta `npm ci`, ambas pruebas Node de soporte, `npm run instalar:navegador:ci`, build estricto, Playwright funcional y Lighthouse en el runner. Después monta el checkout/sitio en `mcr.microsoft.com/playwright:v1.61.1-noble@sha256:5b8f294aff9041b7191c34a4bab3ac270157a28774d4b0660e9743297b697e48`, repite `npm ci --ignore-scripts` y la suite con comparación canónica activa, `CI=1` y `TRAMALIA_COMPARAR_CAPTURAS=1`; no usa `--update-snapshots`. El lock transitivo con hashes y el nombre `requisitos-documentacion.txt` se crean en Plan 04; 03a no puede consumir un archivo futuro. Sólo sube `.artefactos/ux` con `if: failure()`, `retention-days: 3` y rutas explícitas de reportes mediante la misma versión fijada de `actions/upload-artifact` ya aprobada por el proyecto.

- [ ] **Step 4: Ejecutar toda la base local relevante**

Run:

```powershell
uv run --no-sync pytest tests/unidad/test_instalador_gitleaks.py tests/contratos/test_seguridad_estatica.py tests/contratos/test_puertas_generadas.py tests/contratos/test_flujo_validacion.py -q
uv run --no-sync actionlint
uv run --no-sync semgrep scan --config configuracion/semgrep/seguridad-python.yml --error --metrics=off --disable-version-check --exclude tests/recursos/semgrep tramalia scripts tests
$nombre_gitleaks = if ($IsWindows) { "gitleaks.exe" } else { "gitleaks" }
$ruta_gitleaks = Join-Path "$HOME/.local/bin" $nombre_gitleaks
& $ruta_gitleaks git --redact --no-banner --config .gitleaks.toml --exit-code 1
& $ruta_gitleaks dir . --redact --no-banner --config .gitleaks.toml --max-target-megabytes 10 --exit-code 1
uv run --no-sync python scripts/generar_proyecto_prueba_seguridad.py --salida .artefactos/seguridad/proyecto-generado
uv run --no-sync semgrep scan --config .artefactos/seguridad/proyecto-generado/.tramalia/configuracion/semgrep/seguridad-python.yml --error --metrics=off --disable-version-check .artefactos/seguridad/proyecto-generado
& $ruta_gitleaks dir .artefactos/seguridad/proyecto-generado --redact --no-banner --config .gitleaks.toml --max-target-megabytes 10 --exit-code 1
uv run --no-sync mkdocs build --strict
npm run prueba:ux
npm run prueba:lighthouse
```

Expected: todo PASS.

- [ ] **Step 5: Actualizar auditoría por riesgo y ejecutar suite completa**

Documentar en `tests/AUDITORIA.md` que estos contratos cubren SAST, secretos históricos, accesibilidad, teclado, adaptabilidad y rendimiento. Registrar el conteo medido sólo como observación; no establecer una cifra objetivo ni conservar duplicados para acercarse a 250/662. Actualizar `docs/seguridad/matriz-controles.md` con las pruebas/comandos exactos de cada control: `TRM-SEC-007` permanece `parcial` hasta Plan 03c y ningún control pasa a `cubierto_por_prueba` sin evidencia ejecutada.

Run:

```powershell
uv run --no-sync pytest -q
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy tramalia
git diff --check
```

Expected: PASS y `git diff --check` sin salida.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/validacion.yml tests/contratos tests/AUDITORIA.md docs/seguridad/matriz-controles.md
git commit -m "ci: bloquear seguridad y regresiones ux"
```

## Final verification

```powershell
uv sync --locked --group desarrollo --group seguridad --all-extras
uv run --no-sync semgrep --version
$nombre_gitleaks = if ($IsWindows) { "gitleaks.exe" } else { "gitleaks" }
$ruta_gitleaks = Join-Path "$HOME/.local/bin" $nombre_gitleaks
& $ruta_gitleaks version
uv run --no-sync pytest
uv run --no-sync actionlint
uv run --no-sync semgrep --test --config configuracion/semgrep/seguridad-python.yml tests/recursos/semgrep
uv run --no-sync semgrep scan --config configuracion/semgrep/seguridad-python.yml --error --metrics=off --disable-version-check --exclude tests/recursos/semgrep tramalia scripts tests
& $ruta_gitleaks git --redact --no-banner --config .gitleaks.toml --exit-code 1
& $ruta_gitleaks dir . --redact --no-banner --config .gitleaks.toml --max-target-megabytes 10 --exit-code 1
uv run --no-sync python scripts/generar_proyecto_prueba_seguridad.py --salida .artefactos/seguridad/proyecto-generado
uv run --no-sync semgrep scan --config .artefactos/seguridad/proyecto-generado/.tramalia/configuracion/semgrep/seguridad-python.yml --error --metrics=off --disable-version-check .artefactos/seguridad/proyecto-generado
& $ruta_gitleaks dir .artefactos/seguridad/proyecto-generado --redact --no-banner --config .gitleaks.toml --max-target-megabytes 10 --exit-code 1
uv pip install -r requirements-docs.txt
uv run --no-sync mkdocs build --strict
npm ci --ignore-scripts
npm run prueba:guardia-capturas
npm run prueba:servidor-documentacion
npm run instalar:navegador:ux
npm run prueba:ux
docker run --rm --ipc=host --env CI=1 --env TRAMALIA_COMPARAR_CAPTURAS=1 --volume "${PWD}:/trabajo" --workdir /trabajo mcr.microsoft.com/playwright:v1.61.1-noble@sha256:5b8f294aff9041b7191c34a4bab3ac270157a28774d4b0660e9743297b697e48 bash -lc "npm ci --ignore-scripts && npm run prueba:ux"
npm run prueba:lighthouse
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy tramalia
git diff --check
```

Expected: Semgrep 1.169.0 y Gitleaks 8.30.1 están disponibles; todos los gates pasan; no hay secretos, configuraciones remotas, versiones `latest`, despliegues desde validación ni drift entre herramientas registradas y proyectos generados.
