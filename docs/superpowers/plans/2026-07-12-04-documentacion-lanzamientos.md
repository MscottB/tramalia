# Documentación bilingüe y lanzamientos reproducibles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (<code>- [ ]</code>) syntax for tracking.

**Goal:** Publicar documentación conceptual ES/EN y referencia API legible, y garantizar que GitHub Release y PyPI distribuyan exactamente el wheel/sdist validados, con versión, tag, changelog y hashes coherentes.

**Architecture:** MkDocs Material sigue siendo la fuente extensa y el sistema visual; mkdocstrings genera la referencia desde docstrings ingleses estilo Google, mientras páginas Markdown paralelas explican los conceptos en ES/EN. CI conserva una única construcción del paquete en <code>validacion.yml</code>; los workflows de Pages, ZIP de documentación sin conexión, GitHub Release y PyPI son independientes y sólo coordinan artefactos inmutables, hashes y atestaciones. Release siempre prepara un borrador revisable y la publicación humana de ese borrador activa PyPI.

**Tech Stack:** Python 3.11–3.14, pytest, MkDocs Material 9.7.6, mkdocs-static-i18n 1.3.1, mkdocstrings 1.0.6, mkdocstrings-python 2.0.5, CSS, GitHub Actions, GitHub CLI y PyPI Trusted Publishing.

## Global Constraints

- Python 3.11 es la versión mínima; la matriz compatible es 3.11, 3.12, 3.13 y 3.14.
- El núcleo debe seguir funcionando sin Node, servicios cloud ni herramientas externas.
- Las integraciones opcionales pueden degradar capacidad, pero nunca ocultar un intento fallido.
- Las escrituras deben ser seguras en Windows, Linux y macOS.
- Los cambios de comportamiento se hacen con TDD: test fallando, implementación mínima y refactor.
- Las APIs públicas nuevas tienen tipos, docstring inglés estilo Google y pruebas de contrato.
- Los comentarios internos están en español; nombres propios nuevos usan español ASCII.
- Las guías explicativas tienen versiones española e inglesa; los docstrings no son bilingües.
- La referencia usa MkDocs Material y mkdocstrings-python sin reemplazar templates HTML.
- El CSS se limita a clases soportadas: <code>.doc-object</code>, <code>.doc-heading</code>, <code>.doc-signature</code> y <code>.doc-contents</code>.
- Se ocultan miembros privados y código fuente por defecto; firmas, parámetros, retornos y excepciones deben ser legibles.
- Claro, oscuro, escritorio, móvil, foco visible y movimiento reducido son criterios obligatorios.
- <code>validacion.yml</code> ya contiene <code>nucleo</code>, <code>calidad</code>, <code>paquete</code>, <code>plataformas</code> y <code>opcionales</code>; este plan sólo añade <code>documentacion</code> y el contrato reutilizable del artefacto <code>paquete</code>.
- Los módulos finales documentados son <code>tramalia/core/{errores,modelos,proyecto,configuracion,puertas_calidad,politica_cierre,evidencia,traspaso,operaciones,integraciones,procesos,habilidades,contexto,proveedor_contexto,tablero}.py</code>, <code>tramalia/cli/{comandos,renderizado}.py</code>, <code>tramalia/interfaz_terminal.py</code> y las fachadas impuestas por Python/MCP; no se reintroducen módulos ingleses eliminados por los planes 02/03.
- Los cinco workflows finales son <code>validacion.yml</code>, <code>documentacion.yml</code>, <code>documentacion-sin-conexion.yml</code>, <code>lanzamiento-github.yml</code> y <code>publicar-pypi.yml</code>.
- GitHub Release y PyPI consumen el mismo wheel/sdist del job <code>paquete</code>; PyPI nunca reconstruye.
- Sólo tags <code>v*</code> cuya versión coincide con metadata, <code>tramalia.__version__</code> y changelog pueden publicarse.
- Tanto un tag como una ejecución manual sólo crean un draft; ninguna automatización publica el GitHub Release. La publicación humana del draft activa PyPI mediante <code>release.published</code>.
- Todas las acciones GitHub se fijan por SHA con comentario de versión.

---

## File map

- Create <code>requisitos-documentacion.in</code>: dependencias documentales directas.
- Rename <code>requirements-docs.txt</code> → <code>requisitos-documentacion.txt</code>: lock transitivo con hashes, generado.
- Modify <code>mkdocs.yml</code>: mkdocstrings, traducciones y navegación Development.
- Create <code>docs/conceptos-basicos.md</code> y <code>docs/conceptos-basicos.en.md</code>: onboarding conceptual.
- Modify <code>docs/glosario.md</code> y <code>docs/glosario.en.md</code>: anclas y siete definiciones canónicas.
- Create <code>docs/desarrollo/*.md</code> y pares <code>*.en.md</code>: arquitectura, contribución y ocho áreas de API.
- Modify <code>docs/stylesheets/extra.css</code>: presentación adaptable de mkdocstrings.
- Create <code>tests/contratos/test_documentacion.py</code>: bilingüismo, nav, docstrings y drift CLI/extras.
- Create <code>tests/publicacion/test_lanzamiento.py</code>: versión/tag/changelog/hashes.
- Create <code>tests/publicacion/test_flujos_github.py</code>: separación y supply-chain de workflows.
- Create <code>scripts/verificar_lanzamiento.py</code>: validador estándar sin dependencias runtime.
- Rename <code>scripts/build_offline_docs.py</code> → <code>scripts/construir_documentacion_sin_conexion.py</code>: ZIP ordenado y repetible.
- Modify <code>.github/workflows/validacion.yml</code>: job docs y artefacto reusable.
- Replace <code>.github/workflows/docs.yml</code> y <code>docs-offline.yml</code> por los workflows documentales finales; confirmar que <code>publish.yml</code>, retirado en el plan 01, sigue ausente y crear los dos workflows separados de Release/PyPI.
- Modify <code>README.md</code>, <code>README.en.md</code>, <code>CONTRIBUTING.md</code> y <code>MANUAL_DE_USUARIO.md</code>: jerarquía documental sin duplicación.

### Task 1: Entorno documental reproducible y configuración mkdocstrings

**Files:**
- Create: <code>requisitos-documentacion.in</code>
- Rename: <code>requirements-docs.txt</code> → <code>requisitos-documentacion.txt</code>
- Modify: <code>mkdocs.yml</code>
- Create: <code>tests/contratos/test_documentacion.py</code>

**Interfaces:**
- Consumes: repositorio instalable en editable y módulos finales de planes 02/03.
- Produces: build ES/EN estricto y handler Python con rutas explícitas.

- [ ] **Step 1: Write the failing configuration contract**

~~~python
from __future__ import annotations

import argparse
import ast
import inspect
import re
import textwrap
import tomllib
from importlib import import_module
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DOCUMENTOS = RAIZ / "docs"


def test_dependencias_documentales_directas_estan_fijadas():
    lineas = (RAIZ / "requisitos-documentacion.in").read_text(encoding="utf-8").splitlines()
    assert lineas == [
        "mkdocs-material==9.7.6",
        "mkdocs-static-i18n==1.3.1",
        "mkdocs-minify-plugin==0.8.0",
        "mkdocstrings==1.0.6",
        "mkdocstrings-python==2.0.5",
    ]


def test_bloqueo_documental_tiene_hashes():
    bloqueo = (RAIZ / "requisitos-documentacion.txt").read_text(encoding="utf-8")
    assert "--hash=sha256:" in bloqueo


def test_mkdocstrings_usa_google_y_oculta_privados_y_fuente():
    configuracion = (RAIZ / "mkdocs.yml").read_text(encoding="utf-8")
    for contrato in (
        "- mkdocstrings:",
        'paths: ["."]',
        "docstring_style: google",
        "show_source: false",
        'filters: ["!^_"]',
        "separate_signature: true",
        "signature_crossrefs: true",
    ):
        assert contrato in configuracion
~~~

- [ ] **Step 2: Run the contract and verify the missing input/config fails**

Run: <code>uv run --no-sync pytest tests/contratos/test_documentacion.py -q</code>

Expected: FAIL because <code>requisitos-documentacion.in</code> and the mkdocstrings block do not exist.

- [ ] **Step 3: Add direct pins and generate the hashed lock**

Ejecutar primero <code>git mv requirements-docs.txt requisitos-documentacion.txt</code>; el archivo inglés no queda como alias.

<code>requisitos-documentacion.in</code>:

~~~text
mkdocs-material==9.7.6
mkdocs-static-i18n==1.3.1
mkdocs-minify-plugin==0.8.0
mkdocstrings==1.0.6
mkdocstrings-python==2.0.5
~~~

Run:

~~~bash
uv sync --locked --group desarrollo
uv pip compile --python-version 3.11 --generate-hashes requisitos-documentacion.in -o requisitos-documentacion.txt
uv pip install --require-hashes -r requisitos-documentacion.txt
~~~

Expected: the lock is generated with exact transitive versions and every requirement has SHA-256 hashes; installation succeeds.

- [ ] **Step 4: Configure the Python handler before i18n**

Insert after <code>- search</code> in <code>mkdocs.yml</code>:

~~~yaml
  - mkdocstrings:
      handlers:
        python:
          paths: ["."]
          options:
            docstring_style: google
            show_root_heading: true
            show_root_full_path: false
            show_object_full_path: false
            show_source: false
            show_signature_annotations: true
            separate_signature: true
            signature_crossrefs: true
            merge_init_into_class: true
            members_order: source
            inherited_members: false
            filters: ["!^_"]
~~~

- [ ] **Step 5: Verify config and strict build**

Run:

~~~bash
uv run --no-sync pytest tests/contratos/test_documentacion.py -q
uv run --no-sync mkdocs build --strict
~~~

Expected: PASS; con español como idioma predeterminado MkDocs emite <code>site/index.html</code> y la variante inglesa en <code>site/en/index.html</code>, sin crear un directorio <code>site/es</code> ni producir advertencias.

- [ ] **Step 6: Commit**

~~~bash
git add requisitos-documentacion.in requisitos-documentacion.txt mkdocs.yml tests/contratos/test_documentacion.py
git commit -m "docs: configure reproducible API reference"
~~~

### Task 2: Conceptos básicos y glosario canónico ES/EN

**Files:**
- Create: <code>docs/conceptos-basicos.md</code>
- Create: <code>docs/conceptos-basicos.en.md</code>
- Modify: <code>docs/glosario.md</code>
- Modify: <code>docs/glosario.en.md</code>
- Modify: <code>tests/contratos/test_documentacion.py</code>

**Interfaces:**
- Consumes: estados <code>EstadoIntegracion</code> y paquete de evidencia v1.
- Produces: definiciones enlazables para puerta/gate, evidencia, handoff, runner, fallback, degradación y lock.

- [ ] **Step 1: Add the failing bilingual concept contract**

~~~python
TERMINOS = {
    "conceptos-basicos.md": (
        "puerta-calidad", "paquete-evidencia", "traspaso", "ejecutor",
        "alternativa", "degradacion", "lock",
    ),
    "conceptos-basicos.en.md": (
        "quality-gate", "evidence-pack", "handoff", "runner",
        "fallback", "degradation", "lock",
    ),
}


def test_conceptos_basicos_explican_y_enlazan_los_siete_terminos():
    for pagina, anclas in TERMINOS.items():
        texto = (DOCUMENTOS / pagina).read_text(encoding="utf-8")
        for ancla in anclas:
            assert f"glosario.md#{ancla}" in texto


def test_glosarios_exponen_anclas_estables():
    for pagina, anclas in TERMINOS.items():
        glosario = "glosario.en.md" if pagina.endswith(".en.md") else "glosario.md"
        texto = (DOCUMENTOS / glosario).read_text(encoding="utf-8")
        for ancla in anclas:
            assert f'id="{ancla}"' in texto
~~~

- [ ] **Step 2: Verify it fails**

Run: <code>uv run --no-sync pytest tests/contratos/test_documentacion.py -q</code>

Expected: FAIL because both concept pages and the stable glossary anchors are absent.

- [ ] **Step 3: Create the Spanish page**

~~~markdown
# Conceptos básicos

Tramalia gobierna el cierre de trabajo sin exigir conocimiento previo de CI o auditoría.

## Puerta de calidad

Una [puerta de calidad (gate)](glosario.md#puerta-calidad) es una comprobación automática que debe aprobar antes de cerrar una tarea. Tests, lint y seguridad son ejemplos. Si no hay puertas aplicables, el cierre no se presenta como aprobado.

## Paquete de evidencia

Un [paquete de evidencia (evidence pack)](glosario.md#paquete-evidencia) es una carpeta inmutable que conserva comandos, salidas crudas, tiempos, hashes y resultado. Dos cierres crean paquetes distintos; nunca reabren uno anterior.

## Traspaso

El [traspaso (handoff)](glosario.md#traspaso) resume tarea, resultado, riesgos y siguiente paso para que otra persona o agente continúe. La copia canónica vive dentro del paquete.

## Ejecutor

El [ejecutor (runner)](glosario.md#ejecutor) es el programa que lanza las puertas configuradas. Por ejemplo, mise puede ejecutar pytest; que mise no esté disponible es un estado explícito, no una aprobación.

## Alternativa y degradación

Una [alternativa (fallback)](glosario.md#alternativa) es una vía secundaria para una integración opcional. Sólo existe [degradación](glosario.md#degradacion) válida cuando esa alternativa terminó correctamente y Tramalia explica la capacidad perdida. Si también falla, el estado es fallido.

## Lock o resolución fija

Un [lock o resolución fija](glosario.md#lock) conserva una versión o commit exacto. En Team, <code>fuente</code>, <code>referencia</code> y <code>sha_resuelto</code> permiten repetir la misma integración sin ramas flotantes ni <code>latest</code>.
~~~

- [ ] **Step 4: Create the equivalent English page**

~~~markdown
# Basic concepts

Tramalia governs work closure without assuming prior CI or audit knowledge.

## Quality gate

A [quality gate](glosario.md#quality-gate) is an automated check that must pass before a task can close. Tests, lint, and security are examples. When no gate applies, the close is not reported as approved.

## Evidence pack

An [evidence pack](glosario.md#evidence-pack) is an immutable folder containing commands, raw outputs, timings, hashes, and the result. Two closes create different packs and never reopen an older one.

## Handoff

A [handoff](glosario.md#handoff) summarizes the task, result, risks, and next step so another person or agent can continue. Its canonical copy lives inside the pack.

## Runner

A [runner](glosario.md#runner) is the program that launches configured gates. For example, mise can launch pytest; an unavailable runner is an explicit state, not an approval.

## Fallback and degradation

A [fallback](glosario.md#fallback) is a secondary route for an optional integration. A [degradation](glosario.md#degradation) is valid only when that fallback succeeds and Tramalia explains the lost capability. If it also fails, the state is failed.

## Lock

A [lock](glosario.md#lock) records an exact version or commit. In Team mode, <code>fuente</code>, <code>referencia</code>, and <code>sha_resuelto</code> reproduce the same integration without floating branches or <code>latest</code>.
~~~

- [ ] **Step 5: Replace/add the canonical glossary rows**

Spanish:

~~~markdown
| <span id="puerta-calidad"></span>**Puerta de calidad (gate)** | Comprobación automática obligatoria antes de cerrar, como tests, lint o seguridad. |
| <span id="paquete-evidencia"></span>**Paquete de evidencia (evidence pack)** | Carpeta inmutable con lo ejecutado, salidas crudas, resultado y hashes. |
| <span id="traspaso"></span>**Traspaso (handoff)** | Resumen estructurado para que otra persona o agente continúe el trabajo. |
| <span id="ejecutor"></span>**Ejecutor (runner)** | Programa que lanza las puertas configuradas. |
| <span id="alternativa"></span>**Alternativa (fallback)** | Vía secundaria que debe terminar correctamente para declarar una degradación. |
| <span id="degradacion"></span>**Degradación** | Resultado válido con menor capacidad, causa e impacto explícitos. |
| <span id="lock"></span>**Lock o resolución fija** | Versión o commit exacto que permite reproducir una integración. |
~~~

English:

~~~markdown
| <span id="quality-gate"></span>**Quality gate** | Required automated check before closing, such as tests, lint, or security. |
| <span id="evidence-pack"></span>**Evidence pack** | Immutable folder containing executed commands, raw outputs, result, and hashes. |
| <span id="handoff"></span>**Handoff** | Structured summary that lets another person or agent continue the work. |
| <span id="runner"></span>**Runner** | Program that launches configured gates. |
| <span id="fallback"></span>**Fallback** | Secondary route that must succeed before reporting degradation. |
| <span id="degradation"></span>**Degradation** | Valid result with reduced capability and explicit cause and impact. |
| <span id="lock"></span>**Lock** | Exact version or commit used to reproduce an integration. |
~~~

Remove the older duplicate Gate, Evidence pack, and Handoff rows.

- [ ] **Step 6: Run tests/build and commit**

Run: <code>uv run --no-sync pytest tests/contratos/test_documentacion.py -q && uv run --no-sync mkdocs build --strict</code>

Expected: PASS with no duplicate anchors or broken links.

~~~bash
git add docs/conceptos-basicos* docs/glosario* tests/contratos/test_documentacion.py
git commit -m "docs: explain core concepts in Spanish and English"
~~~

### Task 3: Referencia Development y docstrings ingleses

**Files:**
- Create: <code>docs/desarrollo/{index,contribuir,operaciones,puertas-modelos,evidencia-traspaso,proyecto-configuracion,integraciones,cli-mcp,servicios-tui}.md</code>
- Create: the nine corresponding <code>*.en.md</code> files
- Modify: <code>mkdocs.yml</code>
- Modify: final public modules listed in Global Constraints, only where a docstring is missing.
- Modify: <code>tests/contratos/test_documentacion.py</code>

**Interfaces:**
- Consumes: final Spanish-ASCII modules from plans 02/03.
- Produces: one generated API source; both language shells render the same English docstrings.

- [ ] **Step 1: Add failing nav/module/docstring contracts**

~~~python
MODULOS_PUBLICOS = (
    "tramalia.core.errores",
    "tramalia.core.modelos",
    "tramalia.core.proyecto",
    "tramalia.core.configuracion",
    "tramalia.core.puertas_calidad",
    "tramalia.core.politica_cierre",
    "tramalia.core.evidencia",
    "tramalia.core.traspaso",
    "tramalia.core.operaciones",
    "tramalia.core.integraciones",
    "tramalia.core.procesos",
    "tramalia.core.habilidades",
    "tramalia.core.contexto",
    "tramalia.core.proveedor_contexto",
    "tramalia.core.tablero",
    "tramalia.cli.comandos",
    "tramalia.cli.renderizado",
    "tramalia.interfaz_terminal",
    "tramalia.__main__",
    "tramalia.mcp_server",
)


def test_modulos_de_referencia_tienen_docstrings_google_en_ingles():
    encabezados_es = re.compile(r"\b(Argumentos|Devuelve|Retorna|Lanza|Ejemplos):")
    for nombre in MODULOS_PUBLICOS:
        modulo = import_module(nombre)
        assert inspect.getdoc(modulo)
        objetos = []
        for simbolo, objeto in inspect.getmembers(modulo):
            if simbolo.startswith("_") or getattr(objeto, "__module__", None) != nombre:
                continue
            if not (inspect.isclass(objeto) or inspect.isfunction(objeto)):
                continue
            objetos.append((simbolo, objeto))
            if inspect.isclass(objeto):
                for metodo, funcion in inspect.getmembers(objeto, inspect.isfunction):
                    if not metodo.startswith("_") and funcion.__qualname__.startswith(f"{objeto.__name__}."):
                        objetos.append((f"{simbolo}.{metodo}", funcion))
        for simbolo, objeto in objetos:
            documentacion = inspect.getdoc(objeto)
            assert documentacion, f"{nombre}.{simbolo} lacks a public docstring"
            assert objeto.__doc__, f"{nombre}.{simbolo} only inherits a docstring"
            assert not encabezados_es.search(documentacion), f"{nombre}.{simbolo} uses Spanish sections"
            firma = inspect.signature(objeto)
            parametros = [
                parametro
                for parametro in firma.parameters.values()
                if parametro.name not in {"self", "cls"}
            ]
            if parametros:
                assert "Args:" in documentacion, f"{nombre}.{simbolo} lacks Google Args"
            if firma.return_annotation not in {inspect.Signature.empty, None}:
                assert (
                    "Returns:" in documentacion or "Yields:" in documentacion
                ), f"{nombre}.{simbolo} lacks return docs"
            try:
                arbol = (
                    ast.parse(textwrap.dedent(inspect.getsource(objeto)))
                    if inspect.isfunction(objeto) else None
                )
            except (OSError, TypeError, IndentationError):
                arbol = None
            if arbol is not None and any(isinstance(nodo, ast.Raise) for nodo in ast.walk(arbol)):
                assert "Raises:" in documentacion, f"{nombre}.{simbolo} lacks raised errors"


def test_navegacion_desarrollo_tiene_pares_es_en():
    configuracion = (RAIZ / "mkdocs.yml").read_text(encoding="utf-8")
    assert "Desarrollo: Development" in configuracion
    paginas = re.findall(r": (desarrollo/[a-z-]+\.md)$", configuracion, re.MULTILINE)
    assert len(paginas) == 9
    for relativa in paginas:
        assert (DOCUMENTOS / relativa).is_file()
        assert (DOCUMENTOS / relativa.replace(".md", ".en.md")).is_file()
~~~

- [ ] **Step 2: Run and verify failure**

Run: <code>uv run --no-sync pytest tests/contratos/test_documentacion.py -q</code>

Expected: FAIL until all final modules have contract-oriented English docstrings and all reference pages exist.

- [ ] **Step 3: Add the nav and translation entries**

Add <code>Desarrollo: Development</code>, <code>Visión arquitectónica: Architecture overview</code>, <code>Guía para contribuir: Contributing guide</code>, <code>Operaciones: Operations</code>, <code>Puertas y modelos: Gates and models</code>, <code>Evidencia y traspaso: Evidence and handoff</code>, <code>Proyecto y configuración: Project and configuration</code>, <code>Integraciones: Integrations</code>, <code>CLI y MCP: CLI and MCP</code> and <code>Servicios TUI: TUI services</code> to <code>nav_translations</code>.

Insert before the existing Reference section:

~~~yaml
  - Desarrollo:
      - Visión arquitectónica: desarrollo/index.md
      - Guía para contribuir: desarrollo/contribuir.md
      - Operaciones: desarrollo/operaciones.md
      - Puertas y modelos: desarrollo/puertas-modelos.md
      - Evidencia y traspaso: desarrollo/evidencia-traspaso.md
      - Proyecto y configuración: desarrollo/proyecto-configuracion.md
      - Integraciones: desarrollo/integraciones.md
      - CLI y MCP: desarrollo/cli-mcp.md
      - Servicios TUI: desarrollo/servicios-tui.md
~~~

- [ ] **Step 4: Create the reference page pairs with these complete directives**

Each Spanish page starts with the Spanish heading/sentence shown; its English pair uses the English heading/sentence. The directive block is identical.

~~~markdown
# Operaciones / # Operations
Entradas mutantes compartidas por CLI, TUI y MCP. / Mutating entries shared by CLI, TUI, and MCP.
::: tramalia.core.operaciones

# Puertas y modelos / # Gates and models
Política fail-closed y modelos estables. / Fail-closed policy and stable models.
::: tramalia.core.puertas_calidad
::: tramalia.core.politica_cierre
::: tramalia.core.modelos
::: tramalia.core.errores

# Evidencia y traspaso / # Evidence and handoff
Paquete formal v1 y handoff canónico. / Formal v1 pack and canonical handoff.
::: tramalia.core.evidencia
::: tramalia.core.traspaso

# Proyecto y configuración / # Project and configuration
Inspección, guardia y configuración del proyecto gobernado. / Governed-project inspection, guard, and configuration.
::: tramalia.core.proyecto
::: tramalia.core.configuracion

# Integraciones / # Integrations
Estados completos, degradados, no disponibles y fallidos, incluida la resolución reproducible de habilidades y contexto. / Complete, degraded, unavailable, and failed states, including reproducible skill and context resolution.
::: tramalia.core.integraciones
::: tramalia.core.procesos
::: tramalia.core.habilidades
::: tramalia.core.contexto
::: tramalia.core.proveedor_contexto

# CLI y MCP
Fachadas públicas sin política duplicada. / Public façades without duplicated policy.
::: tramalia.__main__
::: tramalia.cli.comandos
::: tramalia.cli.renderizado
::: tramalia.mcp_server

# Servicios TUI / # TUI services
Instantáneas y operaciones fuera de widgets. / Snapshots and operations outside widgets.
::: tramalia.core.tablero
::: tramalia.interfaz_terminal
~~~

<code>desarrollo/index*</code> contains the architecture flow Proyecto → Operaciones → gates/evidence/handoff → CLI/TUI/MCP and links to each page. <code>desarrollo/contribuir*</code> contains the exact commands <code>uv run --no-sync pytest</code> and <code>uv run --no-sync mkdocs build --strict</code>, plus the Spanish-ASCII/comment/docstring rules and a link to <code>CONTRIBUTING.md</code>.

- [ ] **Step 5: Complete missing public docstrings without changing signatures**

Use this exact Google structure, omitting only sections that truly do not apply:

~~~python
def cerrar_proyecto(
    raiz: Path,
    id_tarea: str,
    *,
    agente: str = "",
    revisor: str = "",
    modelo: str = "",
    excepciones: Sequence[ExcepcionFallo] = (),
) -> ResultadoCierre:
    """Close a governed project with fail-closed policy.

    Runs applicable quality gates, stages and atomically publishes a formal
    evidence pack, and updates the handoff projection.

    Args:
        raiz: Governed project root.
        id_tarea: Safe task identifier stored in the evidence metadata.

    Returns:
        The same definitive result consumed by CLI, TUI, and MCP.

    Raises:
        ErrorProyectoNoGobernado: If the project markers are absent or incomplete.
        ErrorConfiguracionPuertas: If gate configuration is invalid.
        ErrorConfiguracionMetricas: If metric or threshold JSON is invalid.
        ErrorPersistenciaEvidencia: If the evidence pack cannot be published atomically.

    Examples:
        >>> resultado = cerrar_proyecto(Path("."), "TASK-123")
        >>> resultado.estado in {"aprobado", "aprobado_con_excepciones", "bloqueado"}
        True
    """
~~~

Apply equivalent contract wording to every public symbol found by the test. Comments added around invariants remain Spanish.

- [ ] **Step 6: Verify both builds and commit**

Run:

~~~bash
uv run --no-sync pytest tests/contratos/test_documentacion.py -q
uv run --no-sync mkdocs build --strict
~~~

Expected: PASS; generated reference is present in both languages and private members/source are absent.

~~~bash
git add mkdocs.yml docs/desarrollo tramalia tests/contratos/test_documentacion.py
git commit -m "docs: generate bilingual development reference"
~~~

### Task 4: CSS adaptable para la referencia

**Files:**
- Modify: <code>docs/stylesheets/extra.css</code>
- Modify: <code>tests/contratos/test_documentacion.py</code>

**Interfaces:**
- Consumes: Material color variables and supported mkdocstrings classes.
- Produces: readable signatures and symbol sections at 390px and 1440px in light/dark.

- [ ] **Step 1: Add the failing CSS contract**

~~~python
def test_css_api_cubre_selectores_y_accesibilidad():
    css = (DOCUMENTOS / "stylesheets" / "extra.css").read_text(encoding="utf-8")
    for selector in (".doc-object", ".doc-heading", ".doc-signature", ".doc-contents"):
        assert selector in css
    assert "@media screen and (max-width: 44.984rem)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "overflow-x: auto" in css
    assert ":focus-within" in css
~~~

- [ ] **Step 2: Verify failure**

Run: <code>uv run --no-sync pytest tests/contratos/test_documentacion.py::test_css_api_cubre_selectores_y_accesibilidad -q</code>

Expected: FAIL because no API reference block exists.

- [ ] **Step 3: Append the complete maintainable CSS block**

~~~css
/* ---------- Referencia API (mkdocstrings Material) ---------- */
.md-typeset .doc-object {
  margin-block: 1.75rem;
  padding: clamp(0.9rem, 2vw, 1.35rem);
  border: 1px solid var(--md-default-fg-color--lightest);
  border-radius: var(--tramalia-radius-md);
  background: var(--md-default-bg-color);
}

.md-typeset .doc-object:focus-within {
  border-color: var(--md-accent-fg-color);
  box-shadow: 0 0 0 0.15rem var(--md-accent-fg-color--transparent);
}

.md-typeset .doc-heading {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.45rem;
  margin-top: 0;
}

.md-typeset .doc-label {
  display: inline-flex;
  padding: 0.12rem 0.42rem;
  border: 1px solid var(--md-default-fg-color--lightest);
  border-radius: 999px;
  color: var(--md-default-fg-color--light);
  font-size: 0.64rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.md-typeset .doc-signature {
  display: block;
  max-width: 100%;
  margin: 0.65rem 0 1rem;
  padding: 0.75rem 0.9rem;
  border-radius: var(--tramalia-radius-sm);
  background: var(--md-code-bg-color);
  overflow-x: auto;
  overscroll-behavior-inline: contain;
  white-space: pre;
}

.md-typeset .doc-contents {
  margin-left: clamp(0rem, 2vw, 1rem);
  overflow-wrap: anywhere;
}

.md-typeset .doc-contents table {
  display: block;
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
}

.md-typeset .doc-contents dt {
  font-weight: 700;
}

.md-typeset .doc-contents dd {
  margin-inline-start: 1rem;
}

@media screen and (max-width: 44.984rem) {
  .md-typeset .doc-object {
    margin-inline: -0.35rem;
    padding: 0.75rem;
  }

  .md-typeset .doc-signature {
    font-size: 0.72rem;
  }

  .md-typeset .doc-contents {
    margin-left: 0;
  }

  .md-typeset .doc-contents th,
  .md-typeset .doc-contents td {
    min-width: 8rem;
    white-space: normal;
  }
}
~~~

- [ ] **Step 4: Verify automated and visual matrices**

Run:

~~~bash
uv run --no-sync pytest tests/contratos/test_documentacion.py -q
uv run --no-sync mkdocs build --strict
uv run --no-sync mkdocs serve --dev-addr 127.0.0.1:8000
~~~

Expected: tests/build PASS. Inspect <code>/tramalia/desarrollo/operaciones/</code> and <code>/tramalia/en/desarrollo/operaciones/</code> at 390×844 and 1440×900, in both palettes: no page-wide horizontal overflow, signatures scroll inside their card, badges remain discrete, focus is visible, and reduced-motion produces no animated transitions.

- [ ] **Step 5: Commit**

~~~bash
git add docs/stylesheets/extra.css tests/contratos/test_documentacion.py
git commit -m "style: make API reference responsive"
~~~

### Task 5: Prevención de drift y jerarquía documental

**Files:**
- Modify: <code>tests/contratos/test_documentacion.py</code>
- Modify: <code>tests/AUDITORIA.md</code>
- Modify: <code>README.md</code>, <code>README.en.md</code>, <code>CONTRIBUTING.md</code>, <code>MANUAL_DE_USUARIO.md</code>
- Modify: <code>docs/comandos.md</code>, <code>docs/comandos.en.md</code>, <code>docs/interfaz.md</code>, <code>docs/interfaz.en.md</code>
- Modify: los demás documentos activos y plantillas señalados por el inventario de vocabulario v1; se excluyen sólo <code>docs/superpowers/**</code>, <code>CHANGELOG.md</code> y el manual histórico archivado
- Rename: <code>tramalia/templates/project/docs/ai/12-deploy-release.md</code> → <code>tramalia/templates/project/docs/ai/12-despliegue-lanzamiento.md</code>
- Modify: <code>tramalia/templates/project/AGENTS.md.jinja</code>, <code>tramalia/templates/project/docs/ai/10-contexto-operativo.md</code> y <code>tests/test_v018.py</code>
- Modify: <code>tramalia/templates/project/.tramalia/habilidades/14-deploy-gate/SKILL.md</code> para enlazar el nombre español definitivo

**Interfaces:**
- Consumes: <code>tramalia.__main__.construir_parser()</code>, optional dependencies in pyproject, and final TUI bindings.
- Produces: contract failures when command/extras/bindings or language pairs drift, y una auditoría final de pruebas basada en comportamiento y riesgo, no en un conteo fijo.

- [ ] **Step 1: Add exact drift tests**

~~~python
def _comandos_parser() -> set[str]:
    from tramalia.__main__ import construir_parser

    analizador = construir_parser()
    subanalizadores = next(
        accion for accion in analizador._actions
        if isinstance(accion, argparse._SubParsersAction)
    )
    return set(subanalizadores.choices)


def _comandos_documentados(ruta: Path) -> set[str]:
    patron = re.compile(r"\|\s*(?:\*\*)?\x60tramalia ([a-z][a-z-]*)")
    return set(patron.findall(ruta.read_text(encoding="utf-8")))


def test_tablas_es_en_cubren_argparse_sin_comandos_fantasma():
    esperados = _comandos_parser()
    assert _comandos_documentados(DOCUMENTOS / "comandos.md") == esperados
    assert _comandos_documentados(DOCUMENTOS / "comandos.en.md") == esperados


def test_extras_documentados_existen_en_pyproject():
    datos = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    dependencias_opcionales = set(datos["project"]["optional-dependencies"])
    corpus = "\n".join(
        (RAIZ / ruta).read_text(encoding="utf-8")
        for ruta in ("README.md", "README.en.md", "CONTRIBUTING.md",
                     "docs/instalacion.md", "docs/instalacion.en.md")
    )
    for dependencia in re.findall(r"\[(pretty|mcp|tui|full|dev)\]", corpus):
        assert dependencia in dependencias_opcionales


def test_toda_pagina_de_nav_tiene_par_ingles():
    configuracion = (RAIZ / "mkdocs.yml").read_text(encoding="utf-8")
    for relativa in re.findall(r": ([a-z0-9_/-]+\.md)$", configuracion, re.MULTILINE):
        assert (DOCUMENTOS / relativa).is_file()
        assert (DOCUMENTOS / relativa.replace(".md", ".en.md")).is_file()


def test_manual_historico_esta_archivado():
    manual = (RAIZ / "MANUAL_DE_USUARIO.md").read_text(encoding="utf-8")
    assert "Documento histórico archivado" in manual
    assert "https://MscottB.github.io/tramalia/" in manual


def test_plantilla_no_enlaza_el_nombre_de_despliegue_retirado():
    rutas = (
        "tramalia/templates/project/AGENTS.md.jinja",
        "tramalia/templates/project/docs/ai/10-contexto-operativo.md",
        "tramalia/templates/project/.tramalia/habilidades/14-deploy-gate/SKILL.md",
    )
    corpus = "\n".join((RAIZ / ruta).read_text(encoding="utf-8") for ruta in rutas)
    assert "12-deploy-release.md" not in corpus
    assert "12-despliegue-lanzamiento.md" in corpus


def test_documentacion_activa_no_usa_vocabulario_retirado():
    extensiones = {".md", ".jinja", ".toml"}
    archivos = [
        ruta
        for ruta in DOCUMENTOS.rglob("*")
        if ruta.is_file()
        and ruta.suffix in extensiones
        and "superpowers" not in ruta.parts
    ]
    archivos.extend(
        ruta
        for ruta in (RAIZ / "tramalia" / "templates" / "project").rglob("*")
        if ruta.is_file() and ruta.suffix in extensiones
    )
    archivos.extend(
        RAIZ / nombre for nombre in ("README.md", "README.en.md", "CONTRIBUTING.md")
    )
    retirados = (
        ".tramalia/evidence",
        "metadata.json",
        "07-handoff-agentes.md",
        "09-quality-gates.md",
        "12-deploy-release.md",
        "tramalia-docs-offline.zip",
        ".mkdocs.offline.tmp.yml",
        "passed_with_exceptions",
        "no_gates",
        "tramalia.core.governance",
        "tramalia.core.evidence",
        "tramalia.core.handoff",
        "core/governance.py",
    )
    hallazgos = {
        str(ruta.relative_to(RAIZ)): [
            termino
            for termino in retirados
            if termino in ruta.read_text(encoding="utf-8")
        ]
        for ruta in archivos
    }
    assert not {ruta: terminos for ruta, terminos in hallazgos.items() if terminos}
~~~

- [ ] **Step 2: Run and verify failures identify current drift**

Run: <code>uv run --no-sync pytest tests/contratos/test_documentacion.py -q</code>

Expected: FAIL on missing archive banner and any actual CLI table mismatch; do not weaken expected sets.

- [ ] **Step 3: Make MkDocs canonical and README/manual concise**

Add at the top of <code>MANUAL_DE_USUARIO.md</code>:

~~~markdown
> **Documento histórico archivado.** Conservado para contexto de versiones anteriores.
> La fuente vigente y bilingüe es [la documentación MkDocs](https://MscottB.github.io/tramalia/).
~~~

Antes de cerrar esta tarea, ejecutar el inventario anterior y migrar todas sus coincidencias en documentación activa y plantillas a <code>.tramalia/evidencia</code>, <code>metadatos.json</code>, los estados finales y los módulos españoles. No ocultar coincidencias con exclusiones nuevas: sólo <code>docs/superpowers/**</code>, <code>CHANGELOG.md</code> y <code>MANUAL_DE_USUARIO.md</code> quedan fuera por ser diseño/historial explícito. In both READMEs replace copied long-form reference prose with links to Basic concepts, Full workflow, Commands, and Development. In CONTRIBUTING use <code>uv 0.11.28</code>, <code>uv sync --locked --group desarrollo --all-extras</code>, <code>uv pip install --require-hashes -r requisitos-documentacion.txt</code>, <code>uv run --no-sync pytest</code>, and <code>uv run --no-sync mkdocs build --strict</code>. Correct command tables from argparse and TUI shortcut tables from the final <code>AplicacionTramalia.BINDINGS</code>; do not add counts of tests.

Ejecutar <code>git mv tramalia/templates/project/docs/ai/12-deploy-release.md tramalia/templates/project/docs/ai/12-despliegue-lanzamiento.md</code> y actualizar AGENTS, contexto operativo, <code>.tramalia/habilidades/14-deploy-gate/SKILL.md</code> y la regresión histórica. Los nombres públicos de comandos GitHub/PyPI permanecen, pero el archivo propio refactorizado queda en español ASCII.

- [ ] **Step 4: Cerrar la auditoría de necesidad de pruebas después de los refactors**

Repetir los comandos de colección, cobertura con contextos y duraciones del plan 01. Actualizar `tests/AUDITORIA.md` con el conteo final medido y con la decisión realmente aplicada a cada archivo histórico: toda prueba eliminada debe apuntar al contrato canónico que la reemplazó; todo solapamiento conservado debe justificar entradas o riesgos diferentes. Confirmar que las cuatro categorías explican la colección histórica, que el delta de contratos nuevos concilia con la colección final y que no aparece ninguna frase equivalente a “mantener 250”.

- [ ] **Step 5: Verify and commit**

Run: <code>uv run --no-sync pytest tests/contratos/test_documentacion.py -q && uv run --no-sync mkdocs build --strict</code>

Expected: PASS.

~~~bash
git add README.md README.en.md CONTRIBUTING.md MANUAL_DE_USUARIO.md docs tramalia/templates/project tests/AUDITORIA.md tests/contratos/test_documentacion.py tests/test_v018.py
git commit -m "docs: guard canonical documentation against drift"
~~~

### Task 6: Validador TDD de versión, tag, changelog y hashes

**Files:**
- Create: <code>scripts/verificar_lanzamiento.py</code>
- Create: <code>tests/publicacion/test_lanzamiento.py</code>

**Interfaces:**
- Consumes: tag <code>vX.Y.Z</code>, pyproject, <code>tramalia.__version__</code>, CHANGELOG, one wheel and one sdist.
- Produces: <code>SHA256SUMS</code>, release notes, exit 0/1; never builds.

- [ ] **Step 1: Write failing behavior tests**

~~~python
import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from scripts.verificar_lanzamiento import (
    extraer_notas,
    generar_resumenes,
    validar_metadatos_distribucion,
    validar_version,
    verificar_resumenes,
)


def crear_distribuciones_falsas(raiz: Path, *, nombre: str, version: str) -> Path:
    directorio = raiz / "dist"
    directorio.mkdir(parents=True)
    normalizado = nombre.replace("-", "_")
    metadatos = f"Metadata-Version: 2.4\nName: {nombre}\nVersion: {version}\n\n".encode()
    archivo_wheel = directorio / f"{normalizado}-{version}-py3-none-any.whl"
    with zipfile.ZipFile(archivo_wheel, "w") as archivo:
        archivo.writestr(f"{normalizado}-{version}.dist-info/METADATA", metadatos)
    archivo_sdist = directorio / f"{normalizado}-{version}.tar.gz"
    with tarfile.open(archivo_sdist, "w:gz") as archivo:
        informacion = tarfile.TarInfo(f"{normalizado}-{version}/PKG-INFO")
        informacion.size = len(metadatos)
        informacion.mtime = 0
        archivo.addfile(informacion, io.BytesIO(metadatos))
    return directorio


def test_version_etiqueta_metadatos_e_historial_coinciden(tmp_path):
    archivo_proyecto = tmp_path / "pyproject.toml"
    archivo_paquete = tmp_path / "__init__.py"
    historial = tmp_path / "CHANGELOG.md"
    archivo_proyecto.write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
    archivo_paquete.write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    historial.write_text("## [1.2.3] - 2026-07-12\n\nNotas.\n", encoding="utf-8")
    assert validar_version("v1.2.3", archivo_proyecto, archivo_paquete, historial) == "1.2.3"
    assert extraer_notas(historial, "1.2.3") == "Notas."


@pytest.mark.parametrize("etiqueta", ("1.2.3", "v1.2.4", "latest", "v"))
def test_etiqueta_invalida_o_dispareja_falla(tmp_path, etiqueta):
    archivo_proyecto = tmp_path / "pyproject.toml"
    archivo_paquete = tmp_path / "__init__.py"
    historial = tmp_path / "CHANGELOG.md"
    archivo_proyecto.write_text('[project]\nversion = "1.2.3"\n', encoding="utf-8")
    archivo_paquete.write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    historial.write_text("## [1.2.3]\n\nNotas.\n", encoding="utf-8")
    with pytest.raises(ValueError):
        validar_version(etiqueta, archivo_proyecto, archivo_paquete, historial)


def test_resumenes_detectan_mutacion(tmp_path):
    directorio = tmp_path / "dist"
    directorio.mkdir()
    (directorio / "tramalia_cli-1.2.3-py3-none-any.whl").write_bytes(b"wheel")
    (directorio / "tramalia_cli-1.2.3.tar.gz").write_bytes(b"sdist")
    manifiesto = tmp_path / "SHA256SUMS"
    generar_resumenes(directorio, manifiesto)
    verificar_resumenes(directorio, manifiesto)
    (directorio / "tramalia_cli-1.2.3.tar.gz").write_bytes(b"alterado")
    with pytest.raises(ValueError, match="hash"):
        verificar_resumenes(directorio, manifiesto)


def test_distribuciones_contienen_nombre_y_version_de_etiqueta(tmp_path):
    directorio = crear_distribuciones_falsas(tmp_path, nombre="tramalia-cli", version="1.2.3")
    validar_metadatos_distribucion(directorio, "tramalia-cli", "1.2.3")
    directorio_erroneo = crear_distribuciones_falsas(
        tmp_path / "mala", nombre="tramalia-cli", version="1.2.2",
    )
    with pytest.raises(ValueError, match="metadata"):
        validar_metadatos_distribucion(directorio_erroneo, "tramalia-cli", "1.2.3")


def test_manifiesto_rechaza_nombres_duplicados(tmp_path):
    directorio = crear_distribuciones_falsas(tmp_path, nombre="tramalia-cli", version="1.2.3")
    manifiesto = tmp_path / "SHA256SUMS"
    generar_resumenes(directorio, manifiesto)
    manifiesto.write_text(manifiesto.read_text(encoding="utf-8") * 2, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicad"):
        verificar_resumenes(directorio, manifiesto)
~~~

- [ ] **Step 2: Verify import failure**

Run: <code>uv run --no-sync pytest tests/publicacion/test_lanzamiento.py -q</code>

Expected: FAIL because the verifier does not exist.

- [ ] **Step 3: Implement the complete standard-library verifier**

~~~python
"""Validate immutable release inputs without rebuilding distributions."""

from __future__ import annotations

import argparse
import hashlib
import re
import tarfile
import tomllib
import zipfile
from email.parser import Parser
from pathlib import Path


def archivos_distribucion(directorio: Path) -> list[Path]:
    """Return exactly one wheel and one source distribution."""
    distribuciones_binarias = sorted(directorio.glob("*.whl"))
    distribuciones_fuente = sorted(directorio.glob("*.tar.gz"))
    if len(distribuciones_binarias) != 1 or len(distribuciones_fuente) != 1:
        raise ValueError("se requiere exactamente un wheel y un sdist")
    return distribuciones_binarias + distribuciones_fuente


def generar_resumenes(directorio: Path, manifiesto: Path) -> None:
    """Write deterministic SHA-256 entries for release distributions."""
    lineas = []
    for ruta in archivos_distribucion(directorio):
        resumen = hashlib.sha256(ruta.read_bytes()).hexdigest()
        lineas.append(f"{resumen}  {ruta.name}\n")
    manifiesto.write_text("".join(sorted(lineas)), encoding="utf-8")


def verificar_resumenes(directorio: Path, manifiesto: Path) -> None:
    """Verify that the manifest names and hashes match all distributions."""
    esperados = {}
    for linea in manifiesto.read_text(encoding="utf-8").splitlines():
        resumen, separador, nombre = linea.partition("  ")
        if not separador or not re.fullmatch(r"[0-9a-f]{64}", resumen):
            raise ValueError("manifiesto de hashes inválido")
        if Path(nombre).name != nombre:
            raise ValueError("ruta insegura en manifiesto")
        if nombre in esperados:
            raise ValueError(f"entrada duplicada en manifiesto: {nombre}")
        esperados[nombre] = resumen
    archivos = archivos_distribucion(directorio)
    if set(esperados) != {ruta.name for ruta in archivos}:
        raise ValueError("el manifiesto no coincide con los artefactos")
    for ruta in archivos:
        actual = hashlib.sha256(ruta.read_bytes()).hexdigest()
        if actual != esperados[ruta.name]:
            raise ValueError(f"hash inválido: {ruta.name}")


def validar_metadatos_distribucion(directorio: Path, nombre: str, version: str) -> None:
    """Require wheel METADATA and sdist PKG-INFO to match the release identity."""
    distribucion_binaria, distribucion_fuente = archivos_distribucion(directorio)
    with zipfile.ZipFile(distribucion_binaria) as archivo:
        miembros = [
            nombre_miembro
            for nombre_miembro in archivo.namelist()
            if nombre_miembro.endswith(".dist-info/METADATA")
        ]
        if len(miembros) != 1:
            raise ValueError("metadata de wheel ausente o ambigua")
        metadatos_wheel = Parser().parsestr(archivo.read(miembros[0]).decode("utf-8"))
    with tarfile.open(distribucion_fuente, "r:gz") as archivo:
        miembros = [
            miembro
            for miembro in archivo.getmembers()
            if miembro.isfile() and miembro.name.endswith("/PKG-INFO")
        ]
        if len(miembros) != 1:
            raise ValueError("metadata de sdist ausente o ambigua")
        flujo = archivo.extractfile(miembros[0])
        if flujo is None:
            raise ValueError("metadata de sdist ilegible")
        metadatos_sdist = Parser().parsestr(flujo.read().decode("utf-8"))
    for etiqueta, metadatos in (("wheel", metadatos_wheel), ("sdist", metadatos_sdist)):
        if metadatos["Name"] != nombre or metadatos["Version"] != version:
            raise ValueError(f"metadata de {etiqueta} no coincide con tag: {nombre} {version}")


def extraer_notas(historial: Path, version: str) -> str:
    """Extract the non-empty changelog section for a version."""
    texto = historial.read_text(encoding="utf-8")
    patron = re.compile(
        rf"^## \[{re.escape(version)}\](?: - [^\n]+)?\n(?P<cuerpo>.*?)(?=^## \[|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    coincidencia = patron.search(texto)
    if not coincidencia or not coincidencia.group("cuerpo").strip():
        raise ValueError(f"falta changelog para {version}")
    return coincidencia.group("cuerpo").strip()


def validar_version(
    etiqueta: str,
    archivo_proyecto: Path,
    archivo_paquete: Path,
    historial: Path,
) -> str:
    """Require tag, package metadata, runtime version, and changelog to agree."""
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+(?:[a-z0-9.-]+)?", etiqueta):
        raise ValueError("el tag debe comenzar con v y contener una versión")
    version = tomllib.loads(archivo_proyecto.read_text(encoding="utf-8"))["project"]["version"]
    coincidencia = re.search(
        r'^__version__\s*=\s*["\x27]([^"\x27]+)["\x27]',
        archivo_paquete.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    if not coincidencia or coincidencia.group(1) != version or etiqueta != f"v{version}":
        raise ValueError("tag, metadata y tramalia.__version__ no coinciden")
    extraer_notas(historial, version)
    return version


def principal() -> int:
    """Run the release validation command."""
    analizador = argparse.ArgumentParser()
    subanalizadores = analizador.add_subparsers(dest="accion", required=True)
    generar = subanalizadores.add_parser("generar-resumenes")
    preparar = subanalizadores.add_parser("preparar")
    verificar = subanalizadores.add_parser("verificar")
    for comando in (generar, preparar, verificar):
        comando.add_argument("--distribuciones", type=Path, required=True)
        comando.add_argument("--manifiesto", type=Path, required=True)
    preparar.add_argument("--tag", dest="etiqueta", required=True)
    preparar.add_argument("--archivo-proyecto", type=Path, default=Path("pyproject.toml"))
    preparar.add_argument("--archivo-paquete", type=Path, default=Path("tramalia/__init__.py"))
    preparar.add_argument("--historial", type=Path, default=Path("CHANGELOG.md"))
    preparar.add_argument("--notas", type=Path, required=True)
    argumentos = analizador.parse_args()
    if argumentos.accion == "generar-resumenes":
        generar_resumenes(argumentos.distribuciones, argumentos.manifiesto)
    elif argumentos.accion == "verificar":
        verificar_resumenes(argumentos.distribuciones, argumentos.manifiesto)
    else:
        version = validar_version(
            argumentos.etiqueta,
            argumentos.archivo_proyecto,
            argumentos.archivo_paquete,
            argumentos.historial,
        )
        verificar_resumenes(argumentos.distribuciones, argumentos.manifiesto)
        validar_metadatos_distribucion(argumentos.distribuciones, "tramalia-cli", version)
        argumentos.notas.write_text(
            f"# Tramalia {version}\n\n{extraer_notas(argumentos.historial, version)}\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
~~~

- [ ] **Step 4: Verify and commit**

Run: <code>uv run --no-sync pytest tests/publicacion/test_lanzamiento.py -q</code>

Expected: PASS.

~~~bash
git add scripts/verificar_lanzamiento.py tests/publicacion/test_lanzamiento.py
git commit -m "test: enforce release version and artifact hashes"
~~~

### Task 7: Contrato documental y de artefacto en validacion.yml

**Files:**
- Modify: <code>.github/workflows/validacion.yml</code>
- Modify: <code>tests/publicacion/test_flujos_github.py</code>

**Interfaces:**
- Consumes: jobs <code>nucleo</code>, <code>calidad</code>, <code>paquete</code>, <code>plataformas</code>, <code>opcionales</code>.
- Produces: reusable workflow, strict docs job, artifact <code>paquete</code> with dist and SHA256SUMS.

- [ ] **Step 1: Write the failing workflow contract**

~~~python
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FLUJOS = RAIZ / ".github" / "workflows"


def test_validacion_expone_docs_y_paquete_con_hashes():
    texto = (FLUJOS / "validacion.yml").read_text(encoding="utf-8")
    assert "workflow_call:" in texto
    assert re.search(r"^  documentacion:", texto, re.MULTILINE)
    assert "uv run --no-sync mkdocs build --strict" in texto
    assert "python scripts/verificar_lanzamiento.py generar-resumenes" in texto
    assert texto.count("name: paquete") == 1
    assert "SHA256SUMS" in texto


def test_acciones_estan_fijadas_por_sha():
    ruta = FLUJOS / "validacion.yml"
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if "uses:" in linea and not "uses: ./.github/workflows/" in linea:
            assert re.search(r"@[0-9a-f]{40}\s+#\s+v", linea), f"{ruta}: {linea}"
~~~

- [ ] **Step 2: Verify failure**

Run: <code>uv run --no-sync pytest tests/publicacion/test_flujos_github.py -q</code>

Expected: FAIL until validation is callable and uploads the named artifact.

- [ ] **Step 3: Add workflow_call and the strict documentation job**

Preserve existing triggers/jobs and add <code>workflow_call:</code> under <code>on</code>. Add:

~~~yaml
  documentacion:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0
        with:
          python-version: "3.11"
      - uses: astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990 # v8.3.2
        with:
          version: "0.11.28"
          enable-cache: true
      - run: uv sync --locked --group desarrollo
      - run: uv pip install --require-hashes -r requisitos-documentacion.txt
      - run: uv run --no-sync pytest tests/contratos/test_documentacion.py -q
      - run: uv run --no-sync mkdocs build --strict
~~~

- [ ] **Step 4: Expose the already-built package; do not add another build**

En el job <code>paquete</code>, después del build/check/smoke, añadir la generación de hashes y **sustituir** el único paso de upload creado por el plan 01 por el siguiente bloque. No pueden coexistir dos uploads llamados <code>paquete</code>:

~~~yaml
      - name: Generar hashes
        run: python scripts/verificar_lanzamiento.py generar-resumenes --distribuciones dist --manifiesto SHA256SUMS
      - name: Conservar paquete validado
        uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: paquete
          path: |
            dist/*.whl
            dist/*.tar.gz
            SHA256SUMS
          if-no-files-found: error
          retention-days: 14
~~~

- [ ] **Step 5: Verify and commit**

Run: <code>uv run --no-sync pytest tests/publicacion/test_flujos_github.py tests/contratos/test_documentacion.py -q</code>

Expected: PASS.

~~~bash
git add .github/workflows/validacion.yml tests/publicacion/test_flujos_github.py
git commit -m "ci: expose validated package and strict docs"
~~~

### Task 8: Workflows independientes de documentación web y sin conexión

**Files:**
- Delete: <code>.github/workflows/docs.yml</code>, <code>.github/workflows/docs-offline.yml</code>
- Create: <code>.github/workflows/documentacion.yml</code>, <code>.github/workflows/documentacion-sin-conexion.yml</code>
- Rename: <code>scripts/build_offline_docs.py</code> → <code>scripts/construir_documentacion_sin_conexion.py</code>
- Create: <code>tests/publicacion/test_documentacion_sin_conexion.py</code>
- Modify: <code>.gitignore</code> para ignorar sólo <code>tramalia-documentacion-sin-conexion.zip</code> y <code>.mkdocs.sin-conexion.tmp.yml</code>, retirando sus nombres ingleses

**Interfaces:**
- Produces: Pages sólo desde <code>documentacion.yml</code>; el artefacto <code>documentacion-sin-conexion</code> sólo desde su workflow dedicado.

- [ ] **Step 1: Add a failing deterministic ZIP test**

~~~python
from pathlib import Path

from scripts.construir_documentacion_sin_conexion import ZIP_SALIDA, escribir_zip_determinista


def test_zip_documentacion_sin_conexion_es_repetible(tmp_path):
    origen = tmp_path / "site"
    origen.mkdir()
    (origen / "index.html").write_text("Tramalia", encoding="utf-8")
    uno, dos = tmp_path / "uno.zip", tmp_path / "dos.zip"
    escribir_zip_determinista(origen, uno, 315532800)
    escribir_zip_determinista(origen, dos, 315532800)
    assert uno.read_bytes() == dos.read_bytes()


def test_nombre_publicado_de_documentacion_sin_conexion_es_unico():
    assert ZIP_SALIDA.name == "tramalia-documentacion-sin-conexion.zip"


def test_gitignore_usa_nombres_documentales_espanoles():
    raiz = Path(__file__).resolve().parents[2]
    contenido = (raiz / ".gitignore").read_text(encoding="utf-8")
    assert "tramalia-documentacion-sin-conexion.zip" in contenido
    assert ".mkdocs.sin-conexion.tmp.yml" in contenido
    assert "tramalia-docs-offline.zip" not in contenido
    assert ".mkdocs.offline.tmp.yml" not in contenido
~~~

Run: <code>uv run --no-sync pytest tests/publicacion/test_documentacion_sin_conexion.py -q</code>

Expected: FAIL because the Spanish module/helper is absent. Ejecutar <code>git mv scripts/build_offline_docs.py scripts/construir_documentacion_sin_conexion.py</code>; renombrar <code>ROOT → RAIZ</code>, <code>CONFIG → CONFIGURACION</code>, <code>OUT_ZIP → ZIP_SALIDA</code>, <code>main → principal</code> y todas las variables locales propias al español ASCII. Definir <code>ZIP_SALIDA = RAIZ / "tramalia-documentacion-sin-conexion.zip"</code>, renombrar el temporal a <code>.mkdocs.sin-conexion.tmp.yml</code>, actualizar `.gitignore`, reemplazar el loop de ZIP actual por esta implementación y llamarla desde <code>principal()</code> usando <code>int(os.environ.get("SOURCE_DATE_EPOCH", "315532800"))</code>. Mantener comentarios en español y el docstring de módulo en inglés:

~~~python
def escribir_zip_determinista(origen: Path, destino: Path, marca_tiempo: int) -> None:
    """Write a byte-reproducible ZIP from a built documentation directory.

    Args:
        origen: Directory containing the rendered site.
        destino: ZIP file to create or replace.
        marca_tiempo: UTC Unix timestamp applied to every member.
    """
    instante = datetime.fromtimestamp(max(marca_tiempo, 315532800), UTC)
    fecha_zip = instante.timetuple()[:6]
    with zipfile.ZipFile(
        destino, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archivo_zip:
        for ruta in sorted(candidato for candidato in origen.rglob("*") if candidato.is_file()):
            relativa = ruta.relative_to(origen).as_posix()
            informacion = zipfile.ZipInfo(relativa, date_time=fecha_zip)
            informacion.compress_type = zipfile.ZIP_DEFLATED
            informacion.external_attr = 0o100644 << 16
            archivo_zip.writestr(informacion, ruta.read_bytes(), compresslevel=9)
~~~

Add <code>import os</code> and <code>from datetime import UTC, datetime</code>; change the module docstring to English.

- [ ] **Step 2: Create documentacion.yml**

~~~yaml
name: documentacion
on:
  workflow_run:
    workflows: [validacion]
    types: [completed]
    branches: [main]
permissions:
  contents: read
concurrency:
  group: pages
  cancel-in-progress: true
jobs:
  construir:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pages: read
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
        with:
          ref: ${{ github.event.workflow_run.head_sha }}
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0
        with:
          python-version: "3.11"
      - uses: astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990 # v8.3.2
        with:
          version: "0.11.28"
          enable-cache: true
      - run: uv sync --locked
      - run: uv pip install --require-hashes -r requisitos-documentacion.txt
      - run: uv run --no-sync mkdocs build --strict --site-dir site
      - uses: actions/configure-pages@45bfe0192ca1faeb007ade9deae92b16b8254a0d # v6.0.0
      - uses: actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9 # v5.0.0
        with:
          path: site
  desplegar:
    needs: construir
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deploy.outputs.page_url }}
    steps:
      - id: deploy
        uses: actions/deploy-pages@cd2ce8fcbc39b97be8ca5fce6e763baed58fa128 # v5.0.0
~~~

- [ ] **Step 3: Create documentacion-sin-conexion.yml**

~~~yaml
name: documentacion-sin-conexion
on:
  workflow_call:
  workflow_dispatch:
permissions:
  contents: read
jobs:
  construir:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0
        with:
          python-version: "3.11"
      - uses: astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990 # v8.3.2
        with:
          version: "0.11.28"
          enable-cache: true
      - run: uv sync --locked
      - run: uv pip install --require-hashes -r requisitos-documentacion.txt
      - name: Fijar timestamp desde el commit
        run: echo "SOURCE_DATE_EPOCH=$(git log -1 --format=%ct)" >> "$GITHUB_ENV"
      - run: uv run --no-sync python scripts/construir_documentacion_sin_conexion.py
      - uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: documentacion-sin-conexion
          path: tramalia-documentacion-sin-conexion.zip
          if-no-files-found: error
          retention-days: 14
~~~

- [ ] **Step 4: Extend workflow separation tests**

Assert old filenames are absent; <code>documentacion.yml</code> uses only <code>workflow_run</code>, has no <code>workflow_dispatch</code>, requires a successful validation and checks out exactly its validated <code>head_sha</code>. It contains deploy-pages but neither <code>gh release</code> nor PyPI, grants only <code>contents: read</code>/<code>pages: read</code> to job <code>construir</code>, and grants <code>pages: write</code>/<code>id-token: write</code> only inside job <code>desplegar</code>. El workflow sin conexión contiene <code>workflow_call</code> y upload-artifact pero no deploy-pages ni subida a Release. Expand the SHA-pin test at this point to exactly <code>validacion.yml</code>, <code>documentacion.yml</code> and <code>documentacion-sin-conexion.yml</code>; do not scan workflows already scheduled for deletion.

- [ ] **Step 5: Verify and commit**

Run:

~~~bash
uv run --no-sync pytest tests/publicacion -q
uv run --no-sync python scripts/construir_documentacion_sin_conexion.py
uv run --no-sync mkdocs build --strict
~~~

Expected: PASS and a navigable <code>tramalia-documentacion-sin-conexion.zip</code>.

~~~bash
git add .gitignore .github/workflows scripts/construir_documentacion_sin_conexion.py tests/publicacion
git commit -m "ci: separate online and offline documentation"
~~~

### Task 9: GitHub Release y PyPI sin reconstrucción

**Files:**
- Verify absent: <code>.github/workflows/publish.yml</code> (retirado en el plan 01)
- Create: <code>.github/workflows/lanzamiento-github.yml</code>
- Create: <code>.github/workflows/publicar-pypi.yml</code>
- Modify: <code>tests/publicacion/test_flujos_github.py</code>

**Interfaces:**
- Consumes: artifacts <code>paquete</code> and <code>documentacion-sin-conexion</code> from the same release run.
- Produces: un borrador de GitHub Release para revisión humana; al publicarlo manualmente se emite el evento <code>release.published</code> y PyPI consume exactamente esos activos después de verificarlos en un job sin OIDC. El job OIDC sólo descarga el artefacto interno verificado y publica.

- [ ] **Step 1: Add failing supply-chain assertions**

~~~python
def test_pypi_descarga_release_y_nunca_reconstruye():
    texto = (FLUJOS / "publicar-pypi.yml").read_text(encoding="utf-8")
    assert "types: [published]" in texto
    assert "gh release download" in texto
    assert "gh attestation verify" in texto
    assert '--signer-workflow "$GH_REPO/.github/workflows/lanzamiento-github.yml"' in texto
    assert '--source-digest "$COMMIT_TAG"' in texto
    assert '--source-ref "refs/tags/$TAG"' in texto
    assert "verificar_lanzamiento.py verificar" in texto
    assert "python -m build" not in texto
    assert "gh-action-pypi-publish@" in texto
    bloque_publicar = texto.split("  publicar:", 1)[1]
    assert texto.count("id-token: write") == 1
    assert "id-token: write" in bloque_publicar
    assert "actions/checkout@" not in bloque_publicar
    assert "verificar_lanzamiento.py" not in bloque_publicar
    assert "packages-dir: dist/" in bloque_publicar


def test_lanzamiento_reutiliza_validacion_y_documentacion_sin_conexion():
    texto = (FLUJOS / "lanzamiento-github.yml").read_text(encoding="utf-8")
    assert "uses: ./.github/workflows/validacion.yml" in texto
    assert "uses: ./.github/workflows/documentacion-sin-conexion.yml" in texto
    assert "name: paquete" in texto
    assert "name: documentacion-sin-conexion" in texto
    assert "name: lanzamiento-verificado" in texto
    assert "actions/attest@" in texto
    assert "validar_ref:" in texto
    assert '"$GITHUB_REF" == refs/tags/v*' in texto
    lineas_creacion = [linea for linea in texto.splitlines() if "gh release create" in linea]
    assert lineas_creacion and all("--draft" in linea for linea in lineas_creacion)
    assert all("--verify-tag" in linea for linea in lineas_creacion)
    assert "--prerelease" in texto
    assert "--target" not in texto
    assert "crear_borrador:" in texto
    assert texto.count("contents: write") == 1
    assert "contents: write" in texto.split("  crear_borrador:", 1)[1]
~~~

Run: <code>uv run --no-sync pytest tests/publicacion/test_flujos_github.py -q</code>

Expected: FAIL because final workflows do not exist.

- [ ] **Step 2: Create lanzamiento-github.yml**

~~~yaml
name: lanzamiento-github
on:
  push:
    tags: ["v*"]
  workflow_dispatch:
permissions:
  contents: read
jobs:
  validar_ref:
    runs-on: ubuntu-latest
    outputs:
      tag: ${{ steps.ref.outputs.tag }}
      commit: ${{ steps.ref.outputs.commit }}
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
        with:
          fetch-depth: 0
      - name: Exigir que la ejecución corresponda al tag publicado
        id: ref
        shell: bash
        run: |
          if [[ ! "$GITHUB_REF" == refs/tags/v* ]]; then
            echo "::error::Ejecuta este workflow seleccionando el tag vX.Y.Z, no una rama."
            exit 1
          fi
          TAG="${GITHUB_REF#refs/tags/}"
          COMMIT_TAG="$(git rev-parse "$TAG^{commit}")"
          if [[ "$COMMIT_TAG" != "$GITHUB_SHA" ]]; then
            echo "::error::El tag $TAG no apunta al commit ejecutado."
            exit 1
          fi
          echo "tag=$TAG" >> "$GITHUB_OUTPUT"
          echo "commit=$COMMIT_TAG" >> "$GITHUB_OUTPUT"
  validar:
    needs: validar_ref
    uses: ./.github/workflows/validacion.yml
  documentacion_sin_conexion:
    needs: validar_ref
    uses: ./.github/workflows/documentacion-sin-conexion.yml
  preparar_lanzamiento:
    needs: [validar_ref, validar, documentacion_sin_conexion]
    runs-on: ubuntu-latest
    env:
      TAG: ${{ needs.validar_ref.outputs.tag }}
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0
        with:
          python-version: "3.11"
      - uses: actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1
        with:
          name: paquete
          path: artefactos/paquete
      - uses: actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1
        with:
          name: documentacion-sin-conexion
          path: artefactos/documentacion
      - name: Validar tag, changelog y hashes
        run: >
          python scripts/verificar_lanzamiento.py preparar
          --tag "$TAG"
          --distribuciones artefactos/paquete/dist
          --manifiesto artefactos/paquete/SHA256SUMS
          --notas notas-lanzamiento.md
      - name: Reunir activos ya verificados
        shell: bash
        run: |
          mkdir -p artefactos/lanzamiento/dist
          cp artefactos/paquete/dist/*.whl artefactos/lanzamiento/dist/
          cp artefactos/paquete/dist/*.tar.gz artefactos/lanzamiento/dist/
          cp artefactos/paquete/SHA256SUMS artefactos/lanzamiento/
          cp artefactos/documentacion/tramalia-documentacion-sin-conexion.zip artefactos/lanzamiento/
          cp notas-lanzamiento.md artefactos/lanzamiento/
      - uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: lanzamiento-verificado
          path: artefactos/lanzamiento
          if-no-files-found: error

  atestiguar:
    needs: preparar_lanzamiento
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
      attestations: write
    steps:
      - uses: actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1
        with:
          name: lanzamiento-verificado
          path: artefactos/lanzamiento
      - uses: actions/attest@a1948c3f048ba23858d222213b7c278aabede763 # v4.1.1
        with:
          subject-path: artefactos/lanzamiento/dist/*

  crear_borrador:
    needs: [validar_ref, preparar_lanzamiento, atestiguar]
    runs-on: ubuntu-latest
    permissions:
      contents: write
    env:
      TAG: ${{ needs.validar_ref.outputs.tag }}
      GH_TOKEN: ${{ github.token }}
      GH_REPO: ${{ github.repository }}
    steps:
      - uses: actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1
        with:
          name: lanzamiento-verificado
          path: artefactos/lanzamiento
      - name: Crear siempre un borrador revisable
        shell: bash
        run: |
          if gh release view "$TAG" >/dev/null 2>&1; then
            echo "::error::El release $TAG ya existe; los activos publicados son inmutables."
            exit 1
          fi
          activos=(
            artefactos/lanzamiento/dist/*.whl
            artefactos/lanzamiento/dist/*.tar.gz
            artefactos/lanzamiento/SHA256SUMS
            artefactos/lanzamiento/tramalia-documentacion-sin-conexion.zip
          )
          if [[ "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(a|b|rc|dev)[0-9]+ ]]; then
            gh release create "$TAG" "${activos[@]}" --draft --verify-tag --prerelease --title "Tramalia $TAG" --notes-file artefactos/lanzamiento/notas-lanzamiento.md
          else
            gh release create "$TAG" "${activos[@]}" --draft --verify-tag --title "Tramalia $TAG" --notes-file artefactos/lanzamiento/notas-lanzamiento.md
          fi
~~~

- [ ] **Step 3: Create publicar-pypi.yml**

~~~yaml
name: publicar-pypi
on:
  release:
    types: [published]
permissions:
  contents: read
jobs:
  verificar:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    env:
      TAG: ${{ github.event.release.tag_name }}
      GH_TOKEN: ${{ github.token }}
      GH_REPO: ${{ github.repository }}
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
        with:
          ref: ${{ github.event.release.tag_name }}
          fetch-depth: 0
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0
        with:
          python-version: "3.11"
      - name: Descargar exactamente los activos del release
        shell: bash
        run: |
          mkdir dist
          gh release download "$TAG" --pattern "tramalia_cli-*.whl" --pattern "tramalia_cli-*.tar.gz" --dir dist
          gh release download "$TAG" --pattern "SHA256SUMS" --dir .
      - name: Verificar versión y hashes
        shell: bash
        run: |
          python scripts/verificar_lanzamiento.py verificar --distribuciones dist --manifiesto SHA256SUMS
          python scripts/verificar_lanzamiento.py preparar --tag "$TAG" --distribuciones dist --manifiesto SHA256SUMS --notas notas-lanzamiento.md
          COMMIT_TAG="$(git rev-parse "$TAG^{commit}")"
          for artefacto in dist/*; do
            gh attestation verify "$artefacto" \
              --repo "$GH_REPO" \
              --signer-workflow "$GH_REPO/.github/workflows/lanzamiento-github.yml" \
              --source-digest "$COMMIT_TAG" \
              --source-ref "refs/tags/$TAG"
          done
      - uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: paquete-verificado-pypi
          path: dist/
          if-no-files-found: error

  publicar:
    needs: verificar
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1
        with:
          name: paquete-verificado-pypi
          path: dist/
      - name: Publicar activos verificados mediante Trusted Publishing
        uses: pypa/gh-action-pypi-publish@cef221092ed1bacb1cc03d23a2d87d1d172e277b # v1.14.0
        with:
          packages-dir: dist/
          attestations: true
~~~

- [ ] **Step 4: Verify all workflow contracts and a local dry run**

Expandir el contrato de acciones fijadas para enumerar exactamente los cinco workflows finales. Verificar además que la ejecución manual sólo admita un <code>refs/tags/v*</code> seleccionado como referencia del workflow, que el commit resuelto del tag coincida con <code>GITHUB_SHA</code>, que todo <code>gh release create</code> incluya <code>--draft --verify-tag</code> y nunca <code>--target</code>, y que sólo <code>crear_borrador</code> tenga <code>contents: write</code>. En PyPI, exigir <code>--signer-workflow</code>, <code>--source-digest</code> y <code>--source-ref</code> para ligar cada activo al workflow, commit y tag exactos; el bloque <code>publicar</code> no debe contener checkout, shell ni scripts del repositorio. La publicación manual del borrador es deliberada: un release creado con <code>GITHUB_TOKEN</code> no debe ser la fuente de un evento recursivo de publicación.

Run:

~~~powershell
uv run --no-sync pytest tests/publicacion -q
uv build --out-dir dist/ensayo
uv run --no-sync python scripts/verificar_lanzamiento.py generar-resumenes --distribuciones dist/ensayo --manifiesto dist/SHA256SUMS-ensayo
$version_actual = uv run --no-sync python -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])'
uv run --no-sync python scripts/verificar_lanzamiento.py preparar --tag "v$version_actual" --distribuciones dist/ensayo --manifiesto dist/SHA256SUMS-ensayo --notas notas-lanzamiento.md
$archivos_ensayo = Get-ChildItem -LiteralPath dist/ensayo -File | ForEach-Object FullName
uv run --no-sync twine check $archivos_ensayo
~~~

Expected: all tests PASS; verifier produces notes from the matching changelog and validates the already-built wheel/sdist; twine reports PASSED. Do not push a tag during plan execution.

- [ ] **Step 5: Commit**

~~~bash
git add .github/workflows tests/publicacion
git commit -m "ci: publish validated release assets without rebuilding"
~~~

### Task 10: Preparar la primera BETA y ensayar el borrador remoto

**Files:**
- Modify: <code>pyproject.toml</code>, <code>tramalia/__init__.py</code>, <code>CHANGELOG.md</code> y <code>uv.lock</code> con una única versión <code>0.34.0b1</code> / tag <code>v0.34.0b1</code>
- Modify: <code>tramalia/templates/project/docs/ai/12-despliegue-lanzamiento.md</code> con la lista de comprobación externa de GitHub/PyPI

**Interfaces:**
- Consumes: los cinco workflows ya integrados en la rama principal y la configuración externa del proyecto PyPI.
- Produces: un tag nuevo que apunta al código BETA validado y un **borrador**, nunca una publicación automática de GitHub Release.

- [ ] **Step 1: Bloquear publicación hasta verificar identidades externas**

En GitHub, crear o revisar el environment <code>pypi</code> y sus revisores. En el proyecto PyPI <code>tramalia-cli</code>, reemplazar el Trusted Publisher histórico ligado a <code>publish.yml</code> por esta identidad exacta: propietario <code>MscottB</code>, repositorio <code>tramalia</code>, workflow <code>publicar-pypi.yml</code>, environment <code>pypi</code>. Registrar la comprobación en la lista <code>12-despliegue-lanzamiento.md</code>; no guardar tokens ni capturas sensibles. Esta comprobación manual es bloqueante: si cualquier campo difiere o no puede leerse, se puede crear/revisar el draft, pero no publicarlo.

Verificar por lectura la parte de GitHub cuando la sesión lo permita:

~~~bash
gh api repos/MscottB/tramalia/environments/pypi
~~~

Expected: el environment existe; la identidad de Trusted Publishing se confirma por separado en la configuración del proyecto PyPI.

- [ ] **Step 2: Preparar una versión nueva, nunca reutilizar v0.33.0**

Actualizar una sola vez <code>project.version</code>, <code>tramalia.__version__</code> y el encabezado de changelog a <code>0.34.0b1</code>. Añadir notas BETA que resuman contratos, migraciones y riesgos conocidos. Ejecutar <code>uv lock --python 3.11</code> y después <code>uv sync --locked --group desarrollo --all-extras</code> para demostrar que el lock regenerado corresponde a la versión nueva. Construir wheel/sdist nuevos **después** del bump, generar sus hashes, ejecutar Twine y validarlos contra <code>v0.34.0b1</code>; no reutilizar el ensayo 0.33.0 de Task 9:

~~~powershell
$distribuciones_beta = Join-Path "dist" ("ensayo-beta-" + [guid]::NewGuid().ToString("N"))
$manifiesto_beta = Join-Path $distribuciones_beta "SHA256SUMS"
uv build --out-dir $distribuciones_beta
uv run --no-sync python scripts/verificar_lanzamiento.py generar-resumenes --distribuciones $distribuciones_beta --manifiesto $manifiesto_beta
$archivos_beta = Get-ChildItem -LiteralPath $distribuciones_beta -File | Where-Object Name -ne "SHA256SUMS" | ForEach-Object FullName
uv run --no-sync twine check $archivos_beta
uv run --no-sync python scripts/verificar_lanzamiento.py preparar --tag v0.34.0b1 --distribuciones $distribuciones_beta --manifiesto $manifiesto_beta --notas notas-lanzamiento.md
~~~

Expected: wheel y sdist contienen metadata <code>0.34.0b1</code>, hashes y Twine pasan, y las notas salen de la sección BETA del changelog. Repetir luego la verificación final inferior.

~~~bash
git add pyproject.toml tramalia/__init__.py CHANGELOG.md uv.lock tramalia/templates/project/docs/ai/12-despliegue-lanzamiento.md
git commit -m "chore: prepare 0.34.0b1 beta"
~~~

- [ ] **Step 3: Crear el tag sólo después de integrar y validar main**

No crear el tag desde la rama de trabajo. Después de integrar los commits, actualizar <code>main</code>, confirmar que <code>validacion.yml</code> pasó para ese SHA, crear el tag anotado sobre ese mismo commit y subirlo deliberadamente:

~~~bash
git switch main
git pull --ff-only origin main
git tag -a v0.34.0b1 -m "Tramalia 0.34.0b1"
git push origin v0.34.0b1
~~~

Expected: <code>lanzamiento-github</code> crea un draft para <code>v0.34.0b1</code>. No ejecutar el workflow sobre <code>v0.33.0</code>: ese tag/release ya existe y apunta a otro commit.

- [ ] **Step 4: Leer y verificar el borrador; dejar la publicación a una persona**

~~~bash
gh release view v0.34.0b1 --json isDraft,isPrerelease,tagName,targetCommitish,assets,url
~~~

Expected: <code>isDraft=true</code> e <code>isPrerelease=true</code>; contiene exactamente un wheel, un sdist, <code>SHA256SUMS</code> y <code>tramalia-documentacion-sin-conexion.zip</code>. Descargar en un directorio temporal y verificar las atestaciones con el workflow, commit y tag exactos como hace <code>publicar-pypi.yml</code>. Una persona revisa notas, activos, lista PyPI y riesgos antes de pulsar **Publish release**; ese acto separado activa PyPI.

## Final verification

Run from a clean Python 3.11 environment:

~~~bash
uv sync --locked --group desarrollo --all-extras
uv pip install --require-hashes -r requisitos-documentacion.txt
uv run --no-sync pytest
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mkdocs build --strict
uv run --no-sync python scripts/construir_documentacion_sin_conexion.py
uv run --no-sync pytest tests/publicacion tests/contratos/test_documentacion.py -q
git diff --check
~~~

Expected: the full suite passes; ES/EN strict build passes; the ZIP sin conexión is created; workflow contracts prove separate deployment responsibilities, pinned actions, shared artifacts, provenance verification, least-privilege OIDC and no PyPI rebuild; <code>git diff --check</code> prints nothing.

El ensayo remoto no forma parte del gate local y nunca reutiliza la versión actual publicada. Se ejecuta mediante Task 10, después de integrar los workflows en <code>main</code>, con <code>v0.34.0b1</code> y la configuración externa confirmada. El resultado esperado es sólo un borrador; su publicación humana y la posterior subida a PyPI son pasos separados.
