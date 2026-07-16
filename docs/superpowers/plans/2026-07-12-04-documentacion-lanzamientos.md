# Documentación bilingüe y lanzamientos reproducibles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (<code>- [ ]</code>) syntax for tracking.

**Goal:** Sanear el repositorio, aplicar el corte de licencia comercial aprobado para versiones futuras, publicar documentación conceptual ES/EN y referencia API legible, y garantizar que GitHub Release y PyPI distribuyan exactamente el wheel/sdist validados, con versión, tag, changelog y hashes coherentes.

**Architecture:** MkDocs Material sigue siendo la fuente extensa y el sistema visual; mkdocstrings genera la referencia desde docstrings ingleses estilo Google, mientras páginas Markdown paralelas explican los conceptos en ES/EN. CI conserva una única construcción del paquete en <code>validacion.yml</code>; los workflows de Pages, ZIP de documentación sin conexión, GitHub Release y PyPI son independientes y sólo coordinan artefactos inmutables, hashes y atestaciones. Release siempre prepara un borrador revisable y la publicación humana de ese borrador activa PyPI.

**Tech Stack:** Python 3.11–3.14, pytest, MkDocs Material 9.7.6, mkdocs-static-i18n 1.3.1, mkdocstrings 1.0.6, mkdocstrings-python 2.0.5, CSS, Node/Playwright/axe/Lighthouse fijados por el plan 03a, PolyForm Noncommercial 1.0.0, PEP 639, GitHub Actions, GitHub CLI y PyPI Trusted Publishing.

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
- El CSS se limita a clases soportadas: <code>.doc-object</code>, <code>.doc-heading</code>, <code>.doc-signature</code>, <code>.doc-contents</code> y <code>.doc-label</code> para etiquetas generadas por mkdocstrings.
- Se ocultan miembros privados y código fuente por defecto; firmas, parámetros, retornos y excepciones deben ser legibles.
- Claro, oscuro, escritorio, móvil, foco visible y movimiento reducido son criterios obligatorios.
- Los diagramas de procesos se mantienen en Mermaid, con runtime local fijado —nunca CDN—, pares ES/EN, títulos y descripciones accesibles, colores derivados de las variables de MkDocs Material y presentación usable a 390 px y 1440 px.
- Este plan se ejecuta sólo después de completar, en este orden, los planes 03a, 03c y 03b. <code>validacion.yml</code> ya contendrá <code>nucleo</code>, <code>calidad</code>, <code>seguridad</code>, <code>experiencia_web</code>, <code>plataformas</code> y <code>opcionales</code>; este plan añade <code>documentacion</code> y ajusta el contrato reutilizable del artefacto <code>paquete</code>.
- Los módulos finales documentados se derivan de <code>docs/desarrollo/inventario_api.toml</code> e incluyen las APIs públicas de 03c —modelos, catálogo, configuración, perfiles, resolución, materialización, auditoría y servicio de habilidades— y de 03b —incluido <code>tramalia.interfaz.canal_eventos</code>— además del núcleo, CLI, TUI y fachadas Python/MCP. Cada entrada se reconcilia contra código importable; no se documenta <code>tramalia.core.installer</code> inglés y no se reintroducen módulos ingleses eliminados por los planes 02/03.
- Los cinco workflows finales son <code>validacion.yml</code>, <code>documentacion.yml</code>, <code>documentacion-sin-conexion.yml</code>, <code>lanzamiento-github.yml</code> y <code>publicar-pypi.yml</code>.
- GitHub Release y PyPI consumen el mismo wheel/sdist del job <code>paquete</code>; PyPI nunca reconstruye.
- Sólo tags <code>v*</code> cuya versión coincide con metadata, <code>tramalia.__version__</code> y changelog pueden publicarse.
- Tanto un tag como una ejecución manual sólo crean un draft; ninguna automatización publica el GitHub Release. La publicación humana del draft activa PyPI mediante <code>release.published</code>.
- Todas las acciones GitHub se fijan por SHA con comentario de versión.
- El repositorio público <code>MscottB/tramalia</code> se sanea en el lugar: este plan no lo elimina, renombra ni recrea, no reescribe su historia y no borra tags, releases ni la rama heredada <code>gh-pages</code> durante esta BETA.
- Las versiones <code>v0.33.0</code> y anteriores conservan Apache-2.0 de forma irrevocable. El corte de licencia sólo afecta archivos/versiones posteriores al commit que lo declara.
- El motor futuro se ofrece bajo PolyForm Noncommercial 1.0.0 y acuerdos comerciales separados; las plantillas destinadas a proyectos de clientes conservan Apache-2.0 para no contaminar los derechos comerciales sobre los proyectos generados.
- <code>LICENCIA_COMERCIAL.md</code> informa modalidades y contacto, pero no pretende sustituir un contrato firmado ni concede derechos comerciales por sí solo.
- La publicación BETA queda bloqueada si la auditoría de titularidad encuentra contribuciones externas sin derecho de relicenciamiento o si wheel/sdist no expresan de forma inequívoca las licencias por archivo.

---

## File map

- Create <code>requisitos-documentacion.in</code>: dependencias documentales directas.
- Replace <code>LICENSE</code> with the unmodified PolyForm Noncommercial 1.0.0 text; preserve Apache as <code>LICENSE-APACHE-2.0</code> for historical versions and templates.
- Create <code>LICENCIA_COMERCIAL.md</code>, <code>POLITICA_MARCAS.md</code> and <code>docs/licencia*.md</code>: commercial route, trademark rules and plain-language scope.
- Create <code>tests/publicacion/test_licencia.py</code>: ownership cut, package metadata and license-file contract.
- Rename <code>requirements-docs.txt</code> → <code>requisitos-documentacion.txt</code>: lock transitivo con hashes, generado.
- Modify <code>mkdocs.yml</code>: mkdocstrings, traducciones y navegación Development.
- Create <code>docs/conceptos-basicos.md</code> y <code>docs/conceptos-basicos.en.md</code>: onboarding conceptual.
- Modify <code>docs/glosario.md</code> y <code>docs/glosario.en.md</code>: anclas y siete definiciones canónicas.
- Create <code>docs/desarrollo/inventario_api.toml</code> y las páginas ES/EN derivadas de sus datos: arquitectura, contribución y áreas de API determinadas por el inventario, sin conteos codificados a mano.
- Modify <code>docs/stylesheets/extra.css</code>: presentación adaptable de mkdocstrings.
- Modify <code>mkdocs.yml</code>, <code>package.json</code> y <code>package-lock.json</code>; create <code>docs/javascripts/configurar_mermaid.js</code>, <code>docs/assets/vendor/mermaid.min.js</code> y <code>docs/assets/vendor/LICENCIA_MERMAID.txt</code>: diagramas locales, reproducibles, accesibles y compatibles con las dos paletas Material.
- Create <code>tests/contratos/test_documentacion.py</code>: bilingüismo, nav, docstrings y drift CLI/extras.
- Create <code>tests/publicacion/test_lanzamiento.py</code>: versión/tag/changelog/hashes.
- Create <code>tests/publicacion/test_flujos_github.py</code>: separación y supply-chain de workflows.
- Create <code>scripts/verificar_lanzamiento.py</code>: validador estándar sin dependencias runtime.
- Rename <code>scripts/build_offline_docs.py</code> → <code>scripts/construir_documentacion_sin_conexion.py</code>: ZIP ordenado y repetible.
- Modify <code>.github/workflows/validacion.yml</code>: job docs y artefacto reusable.
- Replace <code>.github/workflows/docs.yml</code> y <code>docs-offline.yml</code> por los workflows documentales finales; confirmar que <code>publish.yml</code>, retirado en el plan 01, sigue ausente y crear los dos workflows separados de Release/PyPI.
- Modify <code>README.md</code>, <code>README.en.md</code> y <code>CONTRIBUTING.md</code>: jerarquía documental sin duplicación y licencia vigente.
- Delete <code>.claude/launch.json</code> después de migrar contenido vigente; rename <code>MANUAL_DE_USUARIO.md</code> → <code>docs/archivo/manual-de-usuario-historico.md</code> y <code>Tramalia_Diseno_Consolidado_v0_6.md</code> → <code>docs/archivo/diseno-consolidado-v0.6.md</code> como fuentes históricas claramente no vigentes y fuera de la navegación principal.
- Rename los tres PNG maestros de <code>assets/images/</code> a <code>presentacion_readme_es.png</code>, <code>presentacion_readme_en.png</code> y <code>presentacion_documentacion.png</code>; conservar sus derivados WebP usados por GitHub y MkDocs.
- Create <code>assets/images/MANIFIESTO_ACTIVOS.md</code>: relación verificable maestro PNG → derivado WebP → consumidor, dimensiones y texto alternativo ES/EN.

### Task 0: Corte de licencia, titularidad y ruta comercial

**Files:**
- Replace: <code>LICENSE</code> con el texto oficial sin modificaciones de PolyForm Noncommercial 1.0.0
- Create: <code>LICENSE-APACHE-2.0</code>
- Modify: <code>NOTICE</code>, <code>LICENSES.md</code>
- Create: <code>LICENCIA_COMERCIAL.md</code>, <code>POLITICA_MARCAS.md</code>
- Create: <code>docs/licencia.md</code>, <code>docs/licencia.en.md</code>
- Create: <code>tramalia/templates/project/LICENSE</code>
- Create: <code>tramalia/templates/project/NOTICE</code>
- Modify: <code>.gitattributes</code> para fijar LF en textos legales que deben conservar bytes canónicos también en Windows
- Modify: <code>pyproject.toml</code>, <code>tramalia/__init__.py</code>, <code>CHANGELOG.md</code>, <code>uv.lock</code>, <code>README.md</code>, <code>README.en.md</code>, <code>CONTRIBUTING.md</code>, <code>mkdocs.yml</code>
- Create: <code>tests/publicacion/test_licencia.py</code>

**Interfaces:**
- Consumes: historial Git completo, tags Apache existentes, texto oficial PolyForm y metadata PEP 639.
- Produces: corte atómico en 1.0.0.dev0 después de 0.33.0, uso no comercial por defecto, vía comercial separada y plantillas Apache para proyectos generados.

- [ ] **Step 1: Escribir contratos fallidos de licencia y paquete**

~~~python
import hashlib


def test_versiones_historicas_conservan_declaracion_apache():
    texto = (RAIZ / "LICENSES.md").read_text(encoding="utf-8")
    assert "v0.33.0 y anteriores" in texto
    assert "Apache-2.0" in texto


def test_metadata_declara_componentes_no_comercial_y_plantillas_apache():
    from packaging.version import Version

    datos = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    assert Version(datos["project"]["version"]) >= Version("1.0.0.dev0")
    assert datos["project"]["license"] == (
        "PolyForm-Noncommercial-1.0.0 AND Apache-2.0"
    )
    assert set(datos["project"]["license-files"]) == {
        "LICENSE",
        "LICENSE-APACHE-2.0",
        "NOTICE",
        "LICENSES.md",
        "tramalia/templates/project/LICENSE",
        "tramalia/templates/project/NOTICE",
    }


def test_runtime_declara_el_mismo_corte_legal():
    import tramalia

    datos = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    assert tramalia.__version__ == datos["project"]["version"]
    assert tramalia.__license__ == "PolyForm-Noncommercial-1.0.0"


def test_apache_historica_y_plantilla_son_el_blob_publicado():
    historica = subprocess.run(
        ["git", "show", "v0.33.0:LICENSE"],
        cwd=RAIZ,
        check=True,
        capture_output=True,
    ).stdout
    assert (RAIZ / "LICENSE-APACHE-2.0").read_bytes() == historica
    assert (RAIZ / "tramalia/templates/project/LICENSE").read_bytes() == historica


def test_polyform_es_el_texto_oficial_fijado():
    assert hashlib.sha256((RAIZ / "LICENSE").read_bytes()).hexdigest() == (
        "c0ea4a896d2c8c394b29f9427589996db826cd501c512279ff0ed3ef48fabbe5"
    )


def test_textos_legales_canonicos_se_extraen_con_lf():
    atributos = (RAIZ / ".gitattributes").read_text(encoding="utf-8")
    for patron in (
        "LICENSE text eol=lf",
        "LICENSE-* text eol=lf",
        "NOTICE text eol=lf",
        "tramalia/templates/project/LICENSE text eol=lf",
        "tramalia/templates/project/NOTICE text eol=lf",
    ):
        assert patron in atributos


def test_inventario_legal_no_conserva_la_decision_apache_retirada():
    texto = (RAIZ / "LICENSES.md").read_text(encoding="utf-8")
    for retirado in (
        "Tramalia usa **Apache-2.0**",
        "se eligió **Apache-2.0**",
        "← elegida",
    ):
        assert retirado not in texto
    for dependencia in ("rich", "questionary", "textual", "mcp"):
        assert dependencia in texto.lower()


def test_aviso_comercial_no_concede_licencia_por_si_solo():
    texto = (RAIZ / "LICENCIA_COMERCIAL.md").read_text(encoding="utf-8")
    assert "no concede derechos comerciales" in texto.lower()
    assert "acuerdo firmado" in texto.lower()
~~~

Añadir pruebas que construyen wheel/sdist y derivan la versión vigente de
<code>pyproject.toml</code>; exigen que sea al menos <code>1.0.0.dev0</code> y que
coincida exactamente con metadata, nombres de artefacto y
<code>tramalia.__version__</code>. Leer <code>License-Expression</code>,
<code>License-File</code> y los archivos reales bajo
<code>.dist-info/licenses/</code>. Importar el wheel en un proceso aislado y
verificar <code>__version__</code> y que <code>__license__</code> representa sólo
la licencia PolyForm del motor, mientras <code>License-Expression</code> usa
<code>PolyForm-Noncommercial-1.0.0 AND Apache-2.0</code> porque la distribución
también contiene plantillas Apache. Verificar que las
plantillas incluidas contienen su Apache local y que ninguna página dice que las
nuevas versiones son open source. Debe ser imposible construir un artefacto
llamado/versionado 0.33.0 con PolyForm. El contrato no fija para siempre
<code>.dev0</code>: Task 10 lo ejecuta sin editarlo contra <code>1.0.0b1</code>.
Derivar además el catálogo propio desde los directorios reales bajo
<code>tramalia/catalogo/habilidades_propias/</code>: cada habilidad encontrada debe
aportar <code>habilidad.toml</code> y <code>SKILL.md</code> tanto al wheel como al
sdist. <code>LICENSES.md</code> declara expresamente que esos dos archivos propios
quedan bajo PolyForm como parte del motor, mientras las copias que el scaffold
emite bajo <code>tramalia/templates/project/</code> conservan Apache-2.0. La prueba
compara los miembros reales de ambos artefactos y sus <code>License-Expression</code>/<code>License-File</code>; no codifica un número de habilidades.

- [ ] **Step 2: Auditar titularidad antes de relicenciar**

~~~powershell
git shortlog -sne HEAD
git log HEAD --format='%aN <%aE>' | Sort-Object -Unique
git log HEAD --format='%an <%ae> | %cn <%ce>' | Sort-Object -Unique
git log HEAD --format='%H | %(trailers:key=Co-authored-by,separator=%x7C) | %(trailers:key=Signed-off-by,separator=%x7C)' | Where-Object { $_ -notmatch '^\S+ \|  \| $' }
git log --all --not HEAD --format='%H | %aN <%aE> | %s'
rg -n "SPDX-License-Identifier|Copyright|copied from|vendored" tramalia scripts tests docs
~~~

`HEAD` representa el linaje fuente y excluye ramas huérfanas de publicación como
`gh-pages`; el segundo inventario clasifica por separado esos commits generados y
confirma que no se fusionaron de vuelta al código fuente. No asumir que
nombre/email de autor demuestra titularidad: agrupar alias conocidos, inspeccionar
los parches/origen de toda identidad no confirmada y buscar material copiado,
vendorizado, generado o sujeto a términos externos. Inventariar también trailers
<code>Co-authored-by</code>, <code>Signed-off-by</code> y equivalentes por commit:
el historial actual contiene trailers de herramientas asistidas que no aparecen
como autor/committer. Para cada grupo, mapear commits y archivos, distinguir una
herramienta de una persona contribuyente y documentar origen/términos aplicables;
un trailer de IA no bloquea automáticamente ni prueba titularidad, pero tampoco
puede omitirse de la resolución. Registrar el resultado y la evidencia local en
`.artefactos/legal/` (sin publicar correos personales).

Expected: el titular puede justificar la autoría o derecho de relicenciamiento de
cada archivo fuente; dependencias de terceros sólo se consumen como
procesos/paquetes o están inventariadas bajo términos compatibles. Si aparece una
contribución o material externo no resuelto, detener exclusivamente el
corte/publicación, identificar archivos y obtener consentimiento/CLA o mantener
ese material bajo términos compatibles. El trabajo técnico restante puede
continuar, pero no se cambia la licencia ni se crea el tag BETA.

- [ ] **Step 3: Aplicar el corte con textos estándar y alcance por directorio**

Descargar literalmente
<code>https://raw.githubusercontent.com/polyformproject/polyform-licenses/1.0.0/PolyForm-Noncommercial-1.0.0.md</code>
a <code>LICENSE</code> y exigir antes de reemplazar el archivo que su SHA-256 sea
<code>c0ea4a896d2c8c394b29f9427589996db826cd501c512279ff0ed3ef48fabbe5</code>.
La URL está fijada al tag oficial 1.0.0 y corresponde al texto publicado en
<code>https://polyformproject.org/licenses/noncommercial/1.0.0</code>. Copiar la
Apache-2.0 histórica actual a <code>LICENSE-APACHE-2.0</code> y a
<code>tramalia/templates/project/LICENSE</code>. No redactar una variante propia
de PolyForm ni normalizar sus bytes después de verificar el hash.

Antes de crear esos archivos, añadir a <code>.gitattributes</code> exactamente
<code>LICENSE text eol=lf</code>, <code>LICENSE-* text eol=lf</code>,
<code>NOTICE text eol=lf</code>,
<code>tramalia/templates/project/LICENSE text eol=lf</code> y
<code>tramalia/templates/project/NOTICE text eol=lf</code>. Obtener Apache con
<code>git show v0.33.0:LICENSE</code> en modo binario y escribir esos mismos bytes,
sin pasar por una API de texto que traduzca saltos de línea. Esto hace que la
igualdad de bytes del contrato sea real incluso con <code>core.autocrlf=true</code>.

Usar en <code>NOTICE</code>:

~~~text
Required Notice: Copyright 2026 Michael Jim Scott Bravo (https://mscottb.github.io/tramalia/)

Tramalia v0.33.0 and earlier were released under Apache-2.0.
The files under tramalia/templates/project/ remain Apache-2.0 so generated
customer projects may be used commercially without inheriting Tramalia's
noncommercial engine license.
~~~

Actualizar PEP 639:

~~~toml
license = "PolyForm-Noncommercial-1.0.0 AND Apache-2.0"
license-files = [
    "LICENSE",
    "LICENSE-APACHE-2.0",
    "NOTICE",
    "LICENSES.md",
    "tramalia/templates/project/LICENSE",
    "tramalia/templates/project/NOTICE",
]
~~~

No incluir una licencia comercial privada dentro de la expresión: sólo existe cuando una organización firma ese acuerdo separado. Reescribir `LICENSES.md` como inventario vigente: motor PolyForm, historia <=v0.33.0 Apache, plantillas Apache y dependencias runtime/dev reales (incluida Textual); retirar toda frase que presente Apache como licencia elegida del motor futuro.

Crear `tramalia/templates/project/NOTICE` con la atribución Apache aplicable sólo
a los archivos de plantilla generados. El scaffold copia `LICENSE` y `NOTICE` al
proyecto nuevo, y el contrato comprueba ambos en el resultado; así el permiso
comercial de las plantillas conserva también el aviso exigible sin atribuir a
Tramalia el código posterior del cliente.

En el mismo cambio, antes de construir cualquier distribución, actualizar
<code>project.version</code> y <code>tramalia.__version__</code> de 0.33.0 a
<code>1.0.0.dev0</code>, fijar <code>tramalia.__license__</code> a
<code>PolyForm-Noncommercial-1.0.0</code>, mantener la expresión PEP 639
<code>PolyForm-Noncommercial-1.0.0 AND Apache-2.0</code> en la metadata de la
distribución, abrir la sección 1.0.0.dev0 en <code>CHANGELOG.md</code> y
regenerar <code>uv.lock</code>. El commit constituye el límite legal: nunca debe
existir un estado confirmable o artefacto 0.33.0 con la licencia nueva.

- [ ] **Step 4: Documentar ruta comercial, marcas y contribuciones**

<code>LICENCIA_COMERCIAL.md</code> explica, sin precios inventados, que requieren acuerdo: uso interno empresarial, consultoría para clientes, redistribución/OEM, inclusión en productos, derivados comerciales, SaaS/servicio gestionado y modalidad sin marca. Indica canal de contacto oficial, que los términos se cotizan por organización/uso y que el archivo no es una concesión.

<code>POLITICA_MARCAS.md</code> permite referencia nominativa, pero reserva “Tramalia”, logotipo, dominios y apariencia de producto oficial; forks no pueden presentarse como oficiales.

<code>CONTRIBUTING.md</code> acepta por ahora sólo issues, reportes y feedback no incorporable. No integra pull requests, parches ni aportes externos de código, documentación, pruebas, plantillas, ejemplos, diseño o activos hasta disponer de un acuerdo de contribución individual/corporativo revisado que permita sublicenciar y relicenciar todo material aportado. DCO por sí solo no satisface el modelo dual. Las correcciones sugeridas en un issue deben ser reimplementadas de forma independiente por el titular salvo acuerdo firmado.

Las páginas ES/EN explican claramente:

- qué versiones son Apache históricas;
- qué usos permite PolyForm Noncommercial;
- que proyectos generados y plantillas tienen alcance Apache separado;
- cómo solicitar licencia comercial;
- que una licencia comercial no transfiere la marca salvo pacto expreso.

- [ ] **Step 5: Preparar resguardo registral externo sin fingir automatización**

Añadir a <code>docs/licencia.md</code> una lista no bloqueante para inscripción del software en DDI Chile y solicitud de marca en INAPI: titular, versión/depósito, clases de marca a revisar, archivos, fecha, comprobantes y renovación. Estos trámites son externos y no se representan como gates pasados hasta recibir comprobante real.

El contrato comercial definitivo, el CLA y la estrategia tributaria se revisan con abogado/contador en Chile antes de firmar con clientes. El repositorio sólo contiene política y aviso, no un contrato generado automáticamente.

- [ ] **Step 6: Construir y verificar metadata legal**

Run:

~~~powershell
uv run --no-sync pytest tests/publicacion/test_licencia.py -q
$salida = Join-Path "dist" ("licencia-" + [guid]::NewGuid().ToString("N"))
uv build --out-dir $salida
uv run --no-sync twine check (Get-ChildItem $salida -File | ForEach-Object FullName)
~~~

Expected: PASS; wheel/sdist 1.0.0.dev0 contienen todos los textos, expresión PEP 639 exacta y README ya no muestra badge Apache para el motor futuro. No existe ningún wheel/sdist 0.33.0 generado después del corte.

- [ ] **Step 7: Commit**

~~~bash
git add .gitattributes LICENSE LICENSE-APACHE-2.0 NOTICE LICENSES.md LICENCIA_COMERCIAL.md POLITICA_MARCAS.md tramalia/templates/project/LICENSE tramalia/templates/project/NOTICE pyproject.toml tramalia/__init__.py CHANGELOG.md uv.lock README.md README.en.md CONTRIBUTING.md docs/licencia.md docs/licencia.en.md mkdocs.yml tests/publicacion/test_licencia.py
git commit -m "legal: definir licencia no comercial y via comercial"
~~~

### Task 1: Entorno documental reproducible y configuración mkdocstrings

**Files:**
- Create: <code>requisitos-documentacion.in</code>
- Rename: <code>requirements-docs.txt</code> → <code>requisitos-documentacion.txt</code>
- Modify: <code>mkdocs.yml</code>
- Modify atomically: every workflow, script, test and active guide that consumes <code>requirements-docs.txt</code>, including <code>.github/workflows/validacion.yml</code> from Plan 03a
- Create: <code>tests/contratos/test_documentacion.py</code>

**Interfaces:**
- Consumes: repositorio instalable en editable y módulos finales de planes 02/03.
- Produces: build ES/EN estricto y handler Python con rutas explícitas.

- [ ] **Step 1: Write the failing configuration contract**

~~~python
from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import re
import struct
import subprocess
import tarfile
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
    assert any("--universal" in linea for linea in bloqueo.splitlines()[1:12])


def test_nombre_documental_espanol_se_migra_atomicamente():
    nombre_retirado = "requirements-" + "docs.txt"
    assert not (RAIZ / nombre_retirado).exists()
    consumidores = subprocess.run(
        ["git", "grep", "-n", nombre_retirado, "--", ":(exclude)docs/superpowers/**"],
        cwd=RAIZ,
        text=True,
        capture_output=True,
        check=False,
    )
    assert consumidores.returncode == 1, consumidores.stdout


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

Ejecutar primero <code>git mv requirements-docs.txt requisitos-documentacion.txt</code>; el archivo inglés no queda como alias. En el mismo commit, usar <code>rg -n "requirements-docs\.txt"</code> y migrar todos los consumidores creados por 03a o existentes en workflows, scripts, pruebas y guías. No dejar ningún commit intermedio con CI apuntando al nombre retirado.

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
uv sync --locked --group desarrollo --group seguridad --all-extras
uv pip compile --python-version 3.11 --universal --generate-hashes requisitos-documentacion.in -o requisitos-documentacion.txt
uv pip install --require-hashes -r requisitos-documentacion.txt
~~~

Expected: the universal lock contains all platform marker branches, exact transitive versions and SHA-256 hashes; installation succeeds locally. Add the same <code>uv pip install --require-hashes -r requisitos-documentacion.txt</code> step to the existing <code>plataformas</code> matrix so Ubuntu, Windows and macOS validate the one lock before integration tests.

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
git add requisitos-documentacion.in requisitos-documentacion.txt mkdocs.yml .github/workflows/validacion.yml tests/contratos/test_documentacion.py
# Añadir también cada consumidor activo que revele el inventario rg; el contrato impide omitir alguno.
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
- Create: <code>docs/desarrollo/inventario_api.toml</code>
- Create from the inventory: <code>docs/desarrollo/{index,contribuir,operaciones,puertas-modelos,evidencia-traspaso,proyecto-configuracion,integraciones,cli-mcp,servicios-tui,interfaz-terminal}.md</code> y todos sus pares <code>*.en.md</code>
- Modify: <code>mkdocs.yml</code>
- Modify: final public modules reconciled from plans 03c/03b, wherever a public docstring is missing, is not English, does not follow Google style or no longer describes the real contract.
- Modify: <code>tests/contratos/test_documentacion.py</code>

**Interfaces:**
- Consumes: final Spanish-ASCII modules from plans 02, 03a, 03c and 03b.
- Produces: an explicit machine-readable API inventory reconciled against importable code; navigation, directives and both language shells derive from it and render the same reviewed English docstrings.

- [ ] **Step 1: Add failing nav/module/docstring contracts**

~~~python
RUTA_INVENTARIO_API = DOCUMENTOS / "desarrollo" / "inventario_api.toml"
MODULOS_REQUERIDOS_PLANES = {
    "tramalia.core.seguridad_entradas",
    "tramalia.core.versiones_herramientas",
    "tramalia.core.instalador",
    "tramalia.core.modelos_habilidades",
    "tramalia.core.auditoria_habilidades",
    "tramalia.core.servicio_habilidades",
    "tramalia.interfaz.canal_eventos",
}
MARCADORES_ESPANOLES = re.compile(
    r"[áéíóúñ¿¡]|\b(el|la|los|las|un|una|para|con|sin|desde|hasta|que|"
    r"devuelve|retorna|lanza|crea|ejecuta|proyecto|habilidad|auditoría)\b",
    re.IGNORECASE,
)
MARCADORES_INGLES = re.compile(
    r"\b(the|a|an|to|from|with|without|return|returns|raise|raises|create|"
    r"run|project|skill|audit|event|service|model|result|configuration|"
    r"operation|screen|component|state|error|path|value|data)\b",
    re.IGNORECASE,
)


def cargar_inventario_api() -> tuple[list[dict[str, object]], tuple[str, ...]]:
    datos = tomllib.loads(RUTA_INVENTARIO_API.read_text(encoding="utf-8"))
    paginas = datos["pagina"]
    rutas = [pagina["ruta"] for pagina in paginas]
    assert len(rutas) == len(set(rutas)), "duplicate API page route"
    modulos = tuple(
        nombre
        for pagina in paginas
        for nombre in pagina.get("modulos", [])
    )
    assert len(modulos) == len(set(modulos)), "a public module has multiple owners"
    assert MODULOS_REQUERIDOS_PLANES <= set(modulos)
    assert "tramalia.core.installer" not in modulos
    return paginas, modulos


def exigir_docstring_ingles(documentacion: str, contexto: str) -> None:
    resumen = documentacion.split("\n\n", 1)[0]
    assert MARCADORES_INGLES.search(resumen), f"{contexto} lacks an English summary"
    assert not MARCADORES_ESPANOLES.search(documentacion), f"{contexto} contains Spanish prose"


def test_modulos_de_referencia_tienen_docstrings_google_en_ingles():
    encabezados_es = re.compile(r"\b(Argumentos|Devuelve|Retorna|Lanza|Ejemplos):")
    _, modulos_publicos = cargar_inventario_api()
    for nombre in modulos_publicos:
        modulo = import_module(nombre)
        documentacion_modulo = inspect.getdoc(modulo)
        assert documentacion_modulo
        exigir_docstring_ingles(documentacion_modulo, nombre)
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
            exigir_docstring_ingles(documentacion, f"{nombre}.{simbolo}")
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
    paginas_inventario, _ = cargar_inventario_api()
    configuracion = (RAIZ / "mkdocs.yml").read_text(encoding="utf-8")
    assert "Desarrollo: Development" in configuracion
    paginas = re.findall(r": (desarrollo/[a-z-]+\.md)$", configuracion, re.MULTILINE)
    esperadas = {f"desarrollo/{pagina['ruta']}.md" for pagina in paginas_inventario}
    assert set(paginas) == esperadas
    for relativa in paginas:
        assert (DOCUMENTOS / relativa).is_file()
        assert (DOCUMENTOS / relativa.replace(".md", ".en.md")).is_file()
~~~

- [ ] **Step 2: Run and verify failure**

Run: <code>uv run --no-sync pytest tests/contratos/test_documentacion.py -q</code>

Expected: FAIL until all final modules have contract-oriented English docstrings and all reference pages exist.

- [ ] **Step 3: Add the nav and translation entries**

Add <code>Desarrollo: Development</code>, <code>Visión arquitectónica: Architecture overview</code>, <code>Guía para contribuir: Contributing guide</code>, <code>Operaciones: Operations</code>, <code>Puertas y modelos: Gates and models</code>, <code>Evidencia y traspaso: Evidence and handoff</code>, <code>Proyecto y configuración: Project and configuration</code>, <code>Integraciones: Integrations</code>, <code>CLI y MCP: CLI and MCP</code>, <code>Servicios TUI: TUI services</code> and <code>Interfaz terminal: Terminal interface</code> to <code>nav_translations</code>.

Guardar primero <code>docs/desarrollo/inventario_api.toml</code> como la fuente
explícita de rutas, títulos y módulos. El inventario inicial posterior a 03c/03b
es éste; si la reconciliación del paso siguiente demuestra que un módulo cambió
de visibilidad o nombre, se corrige aquí antes de generar páginas, nunca en una
segunda lista Python o mediante un conteo fijo:

~~~toml
[[pagina]]
ruta = "index"
titulo_es = "Visión arquitectónica"
titulo_en = "Architecture overview"
modulos = []

[[pagina]]
ruta = "contribuir"
titulo_es = "Guía para contribuir"
titulo_en = "Contributing guide"
modulos = []

[[pagina]]
ruta = "operaciones"
titulo_es = "Operaciones"
titulo_en = "Operations"
modulos = ["tramalia.core.operaciones", "tramalia.core.cancelacion", "tramalia.core.modelos_operacion"]

[[pagina]]
ruta = "puertas-modelos"
titulo_es = "Puertas y modelos"
titulo_en = "Gates and models"
modulos = ["tramalia.core.puertas_calidad", "tramalia.core.politica_cierre", "tramalia.core.modelos", "tramalia.core.errores"]

[[pagina]]
ruta = "evidencia-traspaso"
titulo_es = "Evidencia y traspaso"
titulo_en = "Evidence and handoff"
modulos = ["tramalia.core.evidencia", "tramalia.core.traspaso"]

[[pagina]]
ruta = "proyecto-configuracion"
titulo_es = "Proyecto y configuración"
titulo_en = "Project and configuration"
modulos = ["tramalia.core.proyecto", "tramalia.core.configuracion", "tramalia.core.preparacion_proyecto"]

[[pagina]]
ruta = "integraciones"
titulo_es = "Integraciones"
titulo_en = "Integrations"
modulos = [
  "tramalia.core.integraciones",
  "tramalia.core.procesos",
  "tramalia.core.seguridad_entradas",
  "tramalia.core.versiones_herramientas",
  "tramalia.core.instalador",
  "tramalia.core.habilidades",
  "tramalia.core.modelos_habilidades",
  "tramalia.core.catalogo_habilidades",
  "tramalia.core.configuracion_habilidades",
  "tramalia.core.perfiles_habilidades",
  "tramalia.core.resolucion_habilidades",
  "tramalia.core.materializacion_habilidades",
  "tramalia.core.auditoria_habilidades",
  "tramalia.core.servicio_habilidades",
  "tramalia.core.contexto",
  "tramalia.core.proveedor_contexto",
]

[[pagina]]
ruta = "cli-mcp"
titulo_es = "CLI y MCP"
titulo_en = "CLI and MCP"
modulos = ["tramalia.__main__", "tramalia.cli.catalogo_comandos", "tramalia.cli.comandos", "tramalia.cli.ayuda", "tramalia.cli.tema", "tramalia.cli.salida_estructurada", "tramalia.cli.renderizado", "tramalia.mcp_server"]

[[pagina]]
ruta = "servicios-tui"
titulo_es = "Servicios TUI"
titulo_en = "TUI services"
modulos = ["tramalia.core.tablero", "tramalia.presentacion.variables_tema", "tramalia.interfaz.aplicacion", "tramalia.interfaz.adaptabilidad", "tramalia.interfaz.acciones", "tramalia.interfaz.coordinador_operaciones", "tramalia.interfaz.canal_eventos", "tramalia.interfaz.texto_seguro", "tramalia.interfaz.presentadores", "tramalia.interfaz.tema", "tramalia.interfaz_terminal"]

[[pagina]]
ruta = "interfaz-terminal"
titulo_es = "Interfaz terminal"
titulo_en = "Terminal interface"
modulos = [
  "tramalia.interfaz.componentes.cabecera_proyecto",
  "tramalia.interfaz.componentes.tarjeta_estado",
  "tramalia.interfaz.componentes.estado_vacio",
  "tramalia.interfaz.componentes.barra_acciones",
  "tramalia.interfaz.componentes.detalle_lateral",
  "tramalia.interfaz.componentes.formulario_campo",
  "tramalia.interfaz.componentes.registro_proceso",
  "tramalia.interfaz.componentes.selector_seccion",
  "tramalia.interfaz.componentes.confirmacion_plan",
  "tramalia.interfaz.componentes.aviso_tamano_minimo",
  "tramalia.interfaz.pantallas.resumen",
  "tramalia.interfaz.pantallas.inicializacion",
  "tramalia.interfaz.pantallas.herramientas",
  "tramalia.interfaz.pantallas.habilidades",
  "tramalia.interfaz.pantallas.auditoria",
  "tramalia.interfaz.pantallas.proveedor_contexto",
  "tramalia.interfaz.pantallas.cierre",
]
~~~

Reconciliar este inventario contra los archivos realmente resultantes de 03c/03b:
cada entrada debe importar desde su ruta fuente esperada, todos los módulos que
03c/03b declaren públicos deben tener propietario de página y ningún módulo
interno puede aparecer. <code>tramalia.core.installer</code> queda fuera: si 03b
lo conserva, es sólo shim/interno. El módulo público canónico
<code>tramalia.core.instalador</code>, junto con
<code>tramalia.core.seguridad_entradas</code> y
<code>tramalia.core.versiones_herramientas</code>, debe existir, importar y
permanecer en el inventario. Registrar esta reconciliación
en la prueba de inventario y revisar el diff del inventario antes de continuar.

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
      - Interfaz terminal: desarrollo/interfaz-terminal.md
~~~

- [ ] **Step 4: Create the reference page pairs with these complete directives**

Each Spanish page starts with the Spanish heading/sentence shown; its English pair uses the English heading/sentence. The directive block is identical.

~~~markdown
# Operaciones / # Operations
Entradas mutantes compartidas por CLI, TUI y MCP. / Mutating entries shared by CLI, TUI, and MCP.
::: tramalia.core.operaciones
::: tramalia.core.cancelacion
::: tramalia.core.modelos_operacion

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
::: tramalia.core.preparacion_proyecto

# Integraciones / # Integrations
Estados completos, degradados, no disponibles y fallidos, incluida la resolución reproducible de habilidades y contexto. / Complete, degraded, unavailable, and failed states, including reproducible skill and context resolution.
::: tramalia.core.integraciones
::: tramalia.core.procesos
::: tramalia.core.habilidades
::: tramalia.core.modelos_habilidades
::: tramalia.core.catalogo_habilidades
::: tramalia.core.configuracion_habilidades
::: tramalia.core.perfiles_habilidades
::: tramalia.core.resolucion_habilidades
::: tramalia.core.materializacion_habilidades
::: tramalia.core.auditoria_habilidades
::: tramalia.core.servicio_habilidades
::: tramalia.core.contexto
::: tramalia.core.proveedor_contexto

# CLI y MCP
Fachadas públicas sin política duplicada. / Public façades without duplicated policy.
::: tramalia.__main__
::: tramalia.cli.catalogo_comandos
::: tramalia.cli.comandos
::: tramalia.cli.ayuda
::: tramalia.cli.tema
::: tramalia.cli.salida_estructurada
::: tramalia.cli.renderizado
::: tramalia.mcp_server

# Servicios TUI / # TUI services
Instantáneas y operaciones fuera de widgets. / Snapshots and operations outside widgets.
::: tramalia.core.tablero
::: tramalia.presentacion.variables_tema
::: tramalia.interfaz.aplicacion
::: tramalia.interfaz.adaptabilidad
::: tramalia.interfaz.acciones
::: tramalia.interfaz.coordinador_operaciones
::: tramalia.interfaz.canal_eventos
::: tramalia.interfaz.texto_seguro
::: tramalia.interfaz.presentadores
::: tramalia.interfaz.tema
::: tramalia.interfaz_terminal

# Interfaz terminal / # Terminal interface
Pantallas y componentes interactivos adaptables. / Responsive interactive screens and components.
::: tramalia.interfaz.componentes.cabecera_proyecto
::: tramalia.interfaz.componentes.tarjeta_estado
::: tramalia.interfaz.componentes.estado_vacio
::: tramalia.interfaz.componentes.barra_acciones
::: tramalia.interfaz.componentes.detalle_lateral
::: tramalia.interfaz.componentes.formulario_campo
::: tramalia.interfaz.componentes.registro_proceso
::: tramalia.interfaz.componentes.selector_seccion
::: tramalia.interfaz.componentes.confirmacion_plan
::: tramalia.interfaz.componentes.aviso_tamano_minimo
::: tramalia.interfaz.pantallas.resumen
::: tramalia.interfaz.pantallas.inicializacion
::: tramalia.interfaz.pantallas.herramientas
::: tramalia.interfaz.pantallas.habilidades
::: tramalia.interfaz.pantallas.auditoria
::: tramalia.interfaz.pantallas.proveedor_contexto
::: tramalia.interfaz.pantallas.cierre
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

Aplicar redacción contractual equivalente a **todo** símbolo público encontrado
por el inventario: módulo, clase, función, método de instancia, método estático,
método de clase y propiedad definidos por Tramalia. No basta con añadir secciones
<code>Args:</code>/<code>Returns:</code> ni con eliminar encabezados españoles: el
resumen y toda la prosa deben estar en inglés natural, describir el comportamiento
real y seguir Google style. Revisar manualmente el HTML de mkdocstrings para cada
página inventariada y registrar que no quedan docstrings heredados, españoles,
vacíos, obsoletos o meramente tautológicos. Los comentarios internos añadidos
alrededor de invariantes permanecen en español.

- [ ] **Step 6: Verify both builds and commit**

Run:

~~~bash
uv run --no-sync pytest tests/contratos/test_documentacion.py -q
uv run --no-sync mkdocs build --strict
~~~

Expected: PASS; generated reference is present in both languages and private members/source are absent.

~~~bash
git add mkdocs.yml docs/desarrollo/inventario_api.toml docs/desarrollo tramalia tests/contratos/test_documentacion.py
git commit -m "docs: generate bilingual development reference"
~~~

### Task 4: Presentación adaptable de referencia y diagramas Mermaid

**Files:**
- Modify: <code>docs/stylesheets/extra.css</code>
- Modify: <code>mkdocs.yml</code>, <code>package.json</code>, <code>package-lock.json</code> y las páginas ES/EN que contienen Mermaid
- Create: <code>docs/javascripts/configurar_mermaid.js</code>
- Create from pinned dependency: <code>docs/assets/vendor/mermaid.min.js</code>, <code>docs/assets/vendor/LICENCIA_MERMAID.txt</code>
- Modify: <code>tests/contratos/test_documentacion.py</code>

**Interfaces:**
- Consumes: Material color variables, supported mkdocstrings classes, Mermaid 11.16.0 and the ES/EN page pairs.
- Produces: readable signatures, symbol sections and accessible process diagrams at 390px and 1440px in light/dark, without a CDN or page-wide overflow.

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


def _bloques_mermaid(ruta: Path) -> list[str]:
    return re.findall(
        r"```mermaid\s*\n(.*?)```",
        ruta.read_text(encoding="utf-8"),
        re.DOTALL,
    )


def _tipos_mermaid(ruta: Path) -> list[str]:
    patron = re.compile(
        r"^\s*(flowchart|graph|sequenceDiagram|stateDiagram-v2|"
        r"classDiagram|erDiagram|journey|gantt|pie|mindmap|timeline)\b",
        re.MULTILINE,
    )
    return [patron.search(bloque).group(1) for bloque in _bloques_mermaid(ruta)]


def test_mermaid_es_local_tematico_bilingue_y_accesible():
    configuracion = (RAIZ / "mkdocs.yml").read_text(encoding="utf-8")
    assert "assets/vendor/mermaid.min.js" in configuracion
    assert "javascripts/configurar_mermaid.js" in configuracion
    assert "unpkg.com" not in configuracion
    assert "cdn.jsdelivr.net" not in configuracion

    paquete = json.loads((RAIZ / "package.json").read_text(encoding="utf-8"))
    assert paquete["devDependencies"]["mermaid"] == "11.16.0"
    javascript = (
        DOCUMENTOS / "javascripts" / "configurar_mermaid.js"
    ).read_text(encoding="utf-8")
    for contrato in (
        'securityLevel: "strict"',
        'theme: "base"',
        "--md-primary-fg-color",
        "--md-accent-fg-color",
        "--md-default-bg-color",
        "document$",
        "data-md-component=\"palette\"",
    ):
        assert contrato in javascript

    paginas = [
        ruta
        for ruta in DOCUMENTOS.rglob("*.md")
        if "superpowers" not in ruta.parts and _bloques_mermaid(ruta)
    ]
    assert paginas
    for pagina in paginas:
        for bloque in _bloques_mermaid(pagina):
            assert "accTitle:" in bloque
            assert "accDescr:" in bloque
        if not pagina.name.endswith(".en.md"):
            inglesa = pagina.with_name(f"{pagina.stem}.en.md")
            assert inglesa.is_file()
            assert _tipos_mermaid(pagina) == _tipos_mermaid(inglesa)
~~~

- [ ] **Step 2: Verify failure**

Run: <code>uv run --no-sync pytest tests/contratos/test_documentacion.py::test_css_api_cubre_selectores_y_accesibilidad -q</code>

Expected: FAIL because no API reference block, local Mermaid runtime or complete accessible diagram contract exists.

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

.md-typeset .mermaid {
  max-width: 100%;
  padding: clamp(0.65rem, 2vw, 1rem);
  border: 1px solid var(--md-default-fg-color--lightest);
  border-radius: var(--tramalia-radius-md);
  background: var(--md-default-bg-color);
  overflow-x: auto;
  overscroll-behavior-inline: contain;
}

.md-typeset .mermaid svg {
  display: block;
  width: auto;
  max-width: 100%;
  height: auto;
  margin-inline: auto;
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

  .md-typeset .mermaid svg {
    min-width: 38rem;
  }
}
~~~

Fijar el runtime local y su licencia con estos comandos; los dos archivos
vendorizados quedan rastreados para que Pages y el ZIP sin conexión representen
diagramas aun sin acceso a red:

~~~powershell
npm install --save-dev --save-exact mermaid@11.16.0
New-Item -ItemType Directory -Force docs/assets/vendor | Out-Null
Copy-Item -LiteralPath node_modules/mermaid/dist/mermaid.min.js -Destination docs/assets/vendor/mermaid.min.js
Copy-Item -LiteralPath node_modules/mermaid/LICENSE -Destination docs/assets/vendor/LICENCIA_MERMAID.txt
if ((Get-FileHash node_modules/mermaid/dist/mermaid.min.js -Algorithm SHA256).Hash -ne (Get-FileHash docs/assets/vendor/mermaid.min.js -Algorithm SHA256).Hash) { throw 'El runtime Mermaid vendorizado no coincide con el lock.' }
if ((Get-FileHash node_modules/mermaid/LICENSE -Algorithm SHA256).Hash -ne (Get-FileHash docs/assets/vendor/LICENCIA_MERMAID.txt -Algorithm SHA256).Hash) { throw 'La licencia Mermaid vendorizada no coincide con el paquete.' }
~~~

Añadir a <code>mkdocs.yml</code>, en este orden:

~~~yaml
extra_javascript:
  - assets/vendor/mermaid.min.js
  - javascripts/configurar_mermaid.js
~~~

Crear <code>docs/javascripts/configurar_mermaid.js</code> con esta implementación;
conserva la fuente para volver a dibujar al cambiar de paleta y usa únicamente
variables visuales públicas de Material:

~~~javascript
const fuentesMermaid = new WeakMap();

function valorTema(nombre) {
  return getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
}

async function renderizarDiagramas() {
  const nodos = [...document.querySelectorAll(".mermaid")];
  for (const nodo of nodos) {
    if (!fuentesMermaid.has(nodo)) {
      fuentesMermaid.set(nodo, nodo.textContent);
    } else {
      nodo.textContent = fuentesMermaid.get(nodo);
      nodo.removeAttribute("data-processed");
    }
  }
  if (!nodos.length) return;
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "strict",
    theme: "base",
    themeVariables: {
      background: valorTema("--md-default-bg-color"),
      primaryColor: valorTema("--md-primary-fg-color"),
      primaryBorderColor: valorTema("--md-accent-fg-color"),
      primaryTextColor: valorTema("--md-primary-bg-color"),
      secondaryColor: valorTema("--md-code-bg-color"),
      tertiaryColor: valorTema("--md-default-bg-color"),
      lineColor: valorTema("--md-default-fg-color--light"),
      textColor: valorTema("--md-default-fg-color"),
      fontFamily: getComputedStyle(document.body).fontFamily,
    },
  });
  await mermaid.run({ nodes: nodos });
}

document$.subscribe(() => {
  void renderizarDiagramas();
  const selector = document.querySelector('[data-md-component="palette"]');
  if (selector && selector.dataset.mermaidConfigurado !== "true") {
    selector.dataset.mermaidConfigurado = "true";
    selector.addEventListener("change", () => {
      requestAnimationFrame(() => void renderizarDiagramas());
    });
  }
});
~~~

Auditar cada bloque Mermaid activo, excluyendo <code>docs/superpowers/**</code>:
añadir <code>accTitle:</code> y <code>accDescr:</code> traducidos, conservar la misma
cantidad y tipo de diagramas en cada par ES/EN, reemplazar colores hexadecimales
embebidos por la configuración temática anterior y evitar textos que sólo se
distingan por color. El contenido funcional de ambos idiomas debe representar el
mismo proceso aunque sus etiquetas estén traducidas.

- [ ] **Step 4: Verify automated and visual matrices**

Run:

~~~bash
npm ci --ignore-scripts
uv run --no-sync pytest tests/contratos/test_documentacion.py -q
uv run --no-sync mkdocs build --strict
uv run --no-sync mkdocs serve --dev-addr 127.0.0.1:8000
~~~

Expected: tests/build PASS. Inspect <code>/tramalia/desarrollo/operaciones/</code>, <code>/tramalia/en/desarrollo/operaciones/</code> and at least one page with every Mermaid diagram type at 390×844 and 1440×900, in both palettes: no page-wide horizontal overflow, signatures and wide diagrams scroll only inside their card, badges remain discrete, diagram titles/descriptions reach the accessibility tree, focus is visible, palette changes redraw legibly and reduced-motion produces no animated transitions.

- [ ] **Step 5: Commit**

~~~bash
git add mkdocs.yml package.json package-lock.json docs/stylesheets/extra.css docs/javascripts/configurar_mermaid.js docs/assets/vendor docs tests/contratos/test_documentacion.py
git commit -m "style: make API reference responsive"
~~~

### Task 5: Saneamiento del repositorio, prevención de drift y jerarquía documental

**Files:**
- Modify: <code>tests/contratos/test_documentacion.py</code>
- Modify: <code>tests/AUDITORIA.md</code>
- Modify: <code>README.md</code>, <code>README.en.md</code>, <code>CONTRIBUTING.md</code>, <code>pyproject.toml</code>, <code>mkdocs.yml</code>, <code>.gitignore</code>
- Delete: <code>.claude/launch.json</code>
- Rename: <code>MANUAL_DE_USUARIO.md</code> → <code>docs/archivo/manual-de-usuario-historico.md</code>
- Rename: <code>Tramalia_Diseno_Consolidado_v0_6.md</code> → <code>docs/archivo/diseno-consolidado-v0.6.md</code>
- Rename: <code>assets/images/banner  tramalia-espanol.png</code> → <code>assets/images/presentacion_readme_es.png</code>
- Rename: <code>assets/images/logo tramalia-espanol.png</code> → <code>assets/images/presentacion_readme_en.png</code>
- Rename: <code>assets/images/icono tramalia-espanol.png</code> → <code>assets/images/presentacion_documentacion.png</code>
- Create: <code>assets/images/MANIFIESTO_ACTIVOS.md</code>; preserve <code>docs/assets/brand/tramalia-banner.webp</code>, <code>tramalia-logo.webp</code> y <code>tramalia-mark.webp</code>
- Modify: <code>tramalia/templates/project/.tramalia/config.json.jinja</code> para reemplazar la versión de producto histórica por <code>version_esquema = 1</code>
- Modify: <code>docs/comandos.md</code>, <code>docs/comandos.en.md</code>, <code>docs/interfaz.md</code>, <code>docs/interfaz.en.md</code>
- Verify/consume: <code>scripts/generar_capturas_tui.py</code>, <code>docs/assets/tui/*.svg</code> y <code>tests/contratos/test_capturas_tui.py</code> creados por el plan 03b
- Modify: los demás documentos activos y plantillas señalados por el inventario de vocabulario v1; se excluyen sólo <code>docs/superpowers/**</code> y <code>CHANGELOG.md</code>
- Rename: <code>tramalia/templates/project/docs/ai/12-deploy-release.md</code> → <code>tramalia/templates/project/docs/ai/12-despliegue-lanzamiento.md</code>
- Modify: <code>tramalia/templates/project/AGENTS.md.jinja</code>, <code>tramalia/templates/project/docs/ai/10-contexto-operativo.md</code> y <code>tests/test_v018.py</code>
- Modify: <code>tramalia/catalogo/habilidades_propias/14-despliegue-lanzamiento/SKILL.md</code> para enlazar el nombre español definitivo

**Interfaces:**
- Consumes: <code>tramalia.__main__.construir_parser()</code>, optional dependencies in pyproject, and final TUI bindings.
- Produces: contract failures when command/extras/bindings, language pairs, root contents, package contents, capturas TUI deterministas or schema language drift, y una auditoría final de pruebas basada en comportamiento y riesgo, no en un conteo fijo.

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


def test_documentos_historicos_y_configuracion_local_no_siguen_en_raiz():
    retirados = (
        "MANUAL_DE_USUARIO.md",
        "Tramalia_Diseno_Consolidado_v0_6.md",
        ".claude/launch.json",
    )
    assert all(not (RAIZ / ruta).exists() for ruta in retirados)
    archivos_historicos = {
        "archivo/diseno-consolidado-v0.6.md":
            "# Archivo histórico — diseño consolidado v0.6",
        "archivo/manual-de-usuario-historico.md":
            "# Archivo histórico — manual de usuario anterior a 1.0",
    }
    for relativa, titulo in archivos_historicos.items():
        contenido_archivado = (DOCUMENTOS / relativa).read_text(encoding="utf-8")
        assert contenido_archivado.startswith(titulo)
        assert "no describe la versión vigente" in contenido_archivado
    configuracion = (RAIZ / "mkdocs.yml").read_text(encoding="utf-8")
    assert all(relativa not in configuracion for relativa in archivos_historicos)


def _dimensiones_png(ruta: Path) -> tuple[int, int]:
    contenido = ruta.read_bytes()
    if contenido[:8] != b"\x89PNG\r\n\x1a\n" or contenido[12:16] != b"IHDR":
        raise AssertionError(f"PNG inválido: {ruta}")
    return struct.unpack(">II", contenido[16:24])


def _dimensiones_webp(ruta: Path) -> tuple[int, int]:
    contenido = ruta.read_bytes()
    if contenido[:4] != b"RIFF" or contenido[8:12] != b"WEBP":
        raise AssertionError(f"WebP inválido: {ruta}")
    tipo = contenido[12:16]
    if tipo == b"VP8 ":
        ancho, alto = struct.unpack_from("<HH", contenido, 26)
        return ancho & 0x3FFF, alto & 0x3FFF
    if tipo == b"VP8L":
        bits = struct.unpack_from("<I", contenido, 21)[0]
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if tipo == b"VP8X":
        ancho = int.from_bytes(contenido[24:27], "little") + 1
        alto = int.from_bytes(contenido[27:30], "little") + 1
        return ancho, alto
    raise AssertionError(f"Variante WebP no soportada: {tipo!r}")


def test_activos_de_presentacion_conservan_maestro_derivado_y_consumidor():
    casos = (
        (
            "assets/images/presentacion_readme_es.png",
            "docs/assets/brand/tramalia-banner.webp",
            (1672, 941),
            {
                "README.md": (
                    "Tramalia — gobierno repo-first para proyectos de IA multi-agente",
                    "docs/assets/brand/tramalia-banner.webp",
                ),
            },
        ),
        (
            "assets/images/presentacion_readme_en.png",
            "docs/assets/brand/tramalia-logo.webp",
            (1672, 941),
            {
                "README.en.md": (
                    "Tramalia — repo-first governance for multi-agent AI projects",
                    "docs/assets/brand/tramalia-logo.webp",
                ),
            },
        ),
        (
            "assets/images/presentacion_documentacion.png",
            "docs/assets/brand/tramalia-mark.webp",
            (1254, 1254),
            {
                "docs/index.md": (
                    "Tramalia — búho guardián del repositorio",
                    "assets/brand/tramalia-mark.webp",
                ),
                "docs/index.en.md": (
                    "Tramalia — repository guardian owl",
                    "assets/brand/tramalia-mark.webp",
                ),
            },
        ),
    )
    manifiesto = (RAIZ / "assets/images/MANIFIESTO_ACTIVOS.md").read_text(
        encoding="utf-8"
    )
    for maestro, derivado, dimensiones, consumidores in casos:
        assert _dimensiones_png(RAIZ / maestro) == dimensiones
        assert _dimensiones_webp(RAIZ / derivado) == dimensiones
        resumen_maestro = hashlib.sha256((RAIZ / maestro).read_bytes()).hexdigest()
        resumen_derivado = hashlib.sha256((RAIZ / derivado).read_bytes()).hexdigest()
        assert (
            f"| `{maestro}` | `{derivado}` | `{dimensiones[0]}x{dimensiones[1]}` | "
            f"`{resumen_maestro}` | `{resumen_derivado}` |"
        ) in manifiesto
        for consumidor, (alternativo, referencia) in consumidores.items():
            contenido = (RAIZ / consumidor).read_text(encoding="utf-8")
            assert f"![{alternativo}]({referencia})" in contenido
            assert f"`{consumidor}`" in manifiesto
            assert alternativo in manifiesto


def test_configuracion_generada_versiona_esquema_no_producto():
    plantilla = (
        RAIZ / "tramalia/templates/project/.tramalia/config.json.jinja"
    ).read_text(encoding="utf-8")
    assert '"version_esquema": 1' in plantilla
    assert '"version": "0.6"' not in plantilla


def test_mkdocs_excluye_planes_internos_del_sitio_publico():
    configuracion = (RAIZ / "mkdocs.yml").read_text(encoding="utf-8")
    assert "exclude_docs:" in configuracion
    assert "superpowers/" in configuracion


def test_raiz_y_sdist_tienen_contenido_deliberado():
    permitidos_raiz = {
        ".gitattributes", ".gitignore", ".gitleaks.toml", ".gitleaksignore",
        "CHANGELOG.md", "CONTRIBUTING.md", "LICENSE", "LICENSE-APACHE-2.0", "LICENSES.md",
        "LICENCIA_COMERCIAL.md", "NOTICE", "POLITICA_MARCAS.md",
        "README.md", "README.en.md", "mkdocs.yml", "package.json",
        "package-lock.json", "pyproject.toml", "requisitos-documentacion.in",
        "requisitos-documentacion.txt", "uv.lock",
    }
    rastreados = subprocess.run(
        ["git", "ls-files", "-z"], cwd=RAIZ, check=True, capture_output=True
    ).stdout.decode("utf-8").split("\0")
    archivos_raiz = {ruta for ruta in rastreados if ruta and "/" not in ruta}
    obligatorios_raiz = {
        ".gitattributes", ".gitignore", ".gitleaks.toml", "CHANGELOG.md",
        "CONTRIBUTING.md", "LICENSE",
        "LICENSE-APACHE-2.0", "LICENSES.md", "LICENCIA_COMERCIAL.md",
        "NOTICE", "POLITICA_MARCAS.md", "README.md", "README.en.md",
        "mkdocs.yml", "package.json", "package-lock.json", "pyproject.toml",
        "requisitos-documentacion.in", "requisitos-documentacion.txt", "uv.lock",
    }
    assert obligatorios_raiz <= archivos_raiz
    assert archivos_raiz <= permitidos_raiz

    datos = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    incluidos = set(datos["tool"]["hatch"]["build"]["targets"]["sdist"]["include"])
    assert "Tramalia_Diseno_Consolidado_v0_6.md" not in incluidos
    assert "docs/superpowers" not in incluidos


def test_sdist_construido_no_reintroduce_residuos(tmp_path):
    subprocess.run(
        ["uv", "build", "--sdist", "--out-dir", str(tmp_path)],
        cwd=RAIZ,
        check=True,
    )
    archivo = next(tmp_path.glob("*.tar.gz"))
    with tarfile.open(archivo, "r:gz") as paquete:
        miembros = {
            "/".join(nombre.split("/")[1:])
            for nombre in paquete.getnames()
            if "/" in nombre
        }
    for requerido in (
        "pyproject.toml", "tramalia/__init__.py", "README.md", "LICENSE",
        "LICENSE-APACHE-2.0", "NOTICE", "LICENSES.md",
        "tramalia/templates/project/LICENSE",
        "tramalia/templates/project/NOTICE",
    ):
        assert requerido in miembros
    catalogo = RAIZ / "tramalia" / "catalogo" / "habilidades_propias"
    habilidades = sorted(
        directorio
        for directorio in catalogo.iterdir()
        if directorio.is_dir() and (directorio / "habilidad.toml").is_file()
    )
    assert habilidades
    for habilidad in habilidades:
        relativa = habilidad.relative_to(RAIZ).as_posix()
        assert f"{relativa}/habilidad.toml" in miembros
        assert f"{relativa}/SKILL.md" in miembros
    for retirado in (
        "docs/superpowers/", "docs/archivo/", "MANUAL_DE_USUARIO.md",
        "Tramalia_Diseno_Consolidado_v0_6.md", ".claude/",
    ):
        assert not any(nombre == retirado or nombre.startswith(retirado) for nombre in miembros)


def test_plantilla_no_enlaza_el_nombre_de_despliegue_retirado():
    rutas = (
        "tramalia/templates/project/AGENTS.md.jinja",
        "tramalia/templates/project/docs/ai/10-contexto-operativo.md",
        "tramalia/catalogo/habilidades_propias/14-despliegue-lanzamiento/SKILL.md",
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

Expected: FAIL porque los documentos históricos/configuración local aún existen, los maestros todavía conservan nombres ambiguos, falta su manifiesto, la raíz/sdist contienen residuos y cualquier tabla CLI/TUI diverge del catálogo final; no debilitar los conjuntos esperados.

- [ ] **Step 3: Hacer MkDocs canónico y retirar residuos históricos/locales**

Antes de retirar el manual y archivar el diseño, comparar ambos contra las páginas MkDocs vigentes. Migrar únicamente conceptos que sigan siendo ciertos y no estén documentados; no copiar instrucciones 0.6, Python 3.10, comandos retirados ni conteos estáticos. Después ejecutar:

~~~powershell
git rm -- .claude/launch.json
New-Item -ItemType Directory -Force docs/archivo | Out-Null
git mv -- MANUAL_DE_USUARIO.md docs/archivo/manual-de-usuario-historico.md
git mv -- Tramalia_Diseno_Consolidado_v0_6.md docs/archivo/diseno-consolidado-v0.6.md
git mv -- "assets/images/banner  tramalia-espanol.png" assets/images/presentacion_readme_es.png
git mv -- "assets/images/logo tramalia-espanol.png" assets/images/presentacion_readme_en.png
git mv -- "assets/images/icono tramalia-espanol.png" assets/images/presentacion_documentacion.png
~~~

Anteponer a cada archivo movido, antes de su contenido histórico, el título
correspondiente y esta advertencia. El diseño usa el título inferior; el manual
usa `# Archivo histórico — manual de usuario anterior a 1.0`:

~~~markdown
# Archivo histórico — diseño consolidado v0.6

!!! warning "Documento histórico no vigente"
    Esta fuente se conserva para trazabilidad y no describe la versión vigente de Tramalia. Para instalación, arquitectura, comandos y API actuales, usa la navegación principal de MkDocs.
~~~

No añadir ningún archivo de <code>docs/archivo/</code> a <code>nav</code> ni enlazarlo como guía vigente. El contenido útil ya migrado debe enlazar su página canónica actual, sin reescribir el texto histórico restante.

Añadir <code>.claude/launch.json</code>, <code>site/</code>, <code>dist/</code> y <code>.artefactos/</code> a ignorados si aún no están cubiertos. No sustituir el launch local por otra ruta absoluta. Git conserva los documentos retirados; los PNG se mantienen como maestros rastreados y no se crea una carpeta histórica pública.

En <code>mkdocs.yml</code> usar <code>exclude_docs: superpowers/</code> para que planes/especificaciones internas no se publiquen aunque vivan bajo <code>docs/</code>. Mantener los assets WebP realmente usados en <code>docs/assets/brand/</code>. Crear <code>assets/images/MANIFIESTO_ACTIVOS.md</code> con esta tabla canónica:

~~~markdown
# Manifiesto de activos de marca

Los PNG son los maestros editables y los WebP son los derivados optimizados de publicación. Ningún maestro se elimina por no estar enlazado directamente desde Markdown.

| Maestro PNG | Derivado WebP | Dimensiones | SHA-256 maestro | SHA-256 derivado | Consumidores | Texto alternativo ES | Texto alternativo EN |
|---|---|---:|---|---|---|---|---|
| `assets/images/presentacion_readme_es.png` | `docs/assets/brand/tramalia-banner.webp` | `1672x941` | `84fae00052c6219cbff5e89ce68cb5295262fe0c2837f3e73a9376938520acc8` | `7c3b20538dcdd3fa1f24dc2cec04c849760c0e2932eb35b3af70e0a380ed36f4` | `README.md` | Tramalia — gobierno repo-first para proyectos de IA multi-agente | No aplica |
| `assets/images/presentacion_readme_en.png` | `docs/assets/brand/tramalia-logo.webp` | `1672x941` | `135af3f86c241c34c8dfa81b56c5203585bc93a49801691ffd203d0dac0084b7` | `b2fbe864b5f670a7c3326db5461385fe5aedb8597298ec0b20f186497dafc4d5` | `README.en.md` | No aplica | Tramalia — repo-first governance for multi-agent AI projects |
| `assets/images/presentacion_documentacion.png` | `docs/assets/brand/tramalia-mark.webp` | `1254x1254` | `6a232dadf386247933315592c737a422e8b0ffd8875af05109b015c61d8bb454` | `dc274a363d73d5975975133fefeebe736bb29bb12889c66d8021dbe883f3e1a2` | `docs/index.md`, `docs/index.en.md`, `mkdocs.yml` | Tramalia — búho guardián del repositorio | Tramalia — repository guardian owl |
~~~

Calcular siempre ambos resúmenes desde los bytes con <code>Get-FileHash -Algorithm SHA256</code> inmediatamente después de cada conversión o renombre; convertirlos a minúsculas y actualizar la misma fila. No copiar hashes de una release anterior. Actualizar los cuatro consumidores Markdown con los textos alternativos exactos de la tabla. <code>mkdocs.yml</code> mantiene <code>assets/brand/tramalia-mark.webp</code> como logo; el contrato recalcula los hashes y valida además que los bytes PNG/WebP declaran las mismas dimensiones.

Regenerar las capturas reales de la TUI en un directorio temporal mediante
<code>scripts/generar_capturas_tui.py --salida &lt;temporal&gt;</code>, comparar bytes y
nombres con <code>docs/assets/tui/</code> y ejecutar
<code>tests/contratos/test_capturas_tui.py</code>. Las páginas
<code>interfaz*.md</code> deben referenciar exactamente esos SVG y sus textos
alternativos bilingües; nunca se dibuja una pantalla manual ni se reutiliza una
captura obsoleta del diseño anterior.

Antes de cerrar esta tarea, ejecutar el inventario anterior y migrar todas sus coincidencias en documentación activa y plantillas a <code>.tramalia/evidencia</code>, <code>metadatos.json</code>, los estados finales y los módulos españoles. No ocultar coincidencias con exclusiones nuevas: sólo <code>docs/superpowers/**</code> y <code>CHANGELOG.md</code> quedan fuera por ser diseño/historial explícito. Reemplazar <code>"version": "0.6"</code> de la configuración generada por el entero <code>"version_esquema": 1</code> y mantener lectura compatible de proyectos existentes sin volver a escribir 0.6. Corregir toda referencia activa de Python 3.10 a la mínima 3.11. In both READMEs replace copied long-form reference prose with links to Basic concepts, Full workflow, Commands, and Development. In CONTRIBUTING use <code>uv 0.11.28</code>, <code>uv sync --locked --group desarrollo --all-extras</code>, <code>uv pip install --require-hashes -r requisitos-documentacion.txt</code>, <code>uv run --no-sync pytest</code>, and <code>uv run --no-sync mkdocs build --strict</code>. Correct command tables from the final command catalog and TUI shortcut tables from <code>AplicacionTramalia.BINDINGS</code>; do not add counts of tests or skills.

Ejecutar <code>git mv tramalia/templates/project/docs/ai/12-deploy-release.md tramalia/templates/project/docs/ai/12-despliegue-lanzamiento.md</code> y actualizar AGENTS, contexto operativo, <code>tramalia/catalogo/habilidades_propias/14-despliegue-lanzamiento/SKILL.md</code> y la regresión histórica. Los nombres públicos de comandos GitHub/PyPI permanecen, pero el archivo propio refactorizado queda en español ASCII.

- [ ] **Step 4: Cerrar la auditoría de necesidad de pruebas después de los refactors**

Repetir los comandos de colección, cobertura con contextos y duraciones del plan 01. Actualizar `tests/AUDITORIA.md` con el conteo final medido y con la decisión realmente aplicada a cada archivo histórico: toda prueba eliminada debe apuntar al contrato canónico que la reemplazó; todo solapamiento conservado debe justificar entradas o riesgos diferentes. Confirmar que las cuatro categorías explican la colección histórica, que el delta de contratos nuevos concilia con la colección final y que no aparece ninguna frase equivalente a “mantener 250”.

- [ ] **Step 5: Verify and commit**

Run: <code>uv run --no-sync python scripts/generar_capturas_tui.py --salida .artefactos/capturas-tui-documentacion &amp;&amp; uv run --no-sync pytest tests/contratos/test_capturas_tui.py tests/contratos/test_documentacion.py -q &amp;&amp; uv run --no-sync mkdocs build --strict</code>

Expected: PASS.

~~~bash
git add README.md README.en.md CONTRIBUTING.md pyproject.toml mkdocs.yml .gitignore assets/images docs tramalia/templates/project tests/AUDITORIA.md tests/contratos/test_documentacion.py tests/test_v018.py
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


def test_distribuciones_rechazan_nombres_de_archivo_ambiguos(tmp_path):
    directorio = crear_distribuciones_falsas(tmp_path, nombre="tramalia-cli", version="1.2.3")
    wheel = next(directorio.glob("*.whl"))
    wheel.rename(directorio / "paquete-1.2.3-py3-none-any.whl")
    with pytest.raises(ValueError, match="nombre de archivo"):
        validar_metadatos_distribucion(directorio, "tramalia-cli", "1.2.3")


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
    normalizado = re.sub(r"[-_.]+", "_", nombre).lower()
    esperado_wheel = f"{normalizado}-{version}-py3-none-any.whl"
    esperado_sdist = f"{normalizado}-{version}.tar.gz"
    if distribucion_binaria.name != esperado_wheel or distribucion_fuente.name != esperado_sdist:
        raise ValueError(
            "nombre de archivo de distribución no coincide: "
            f"se esperaban {esperado_wheel} y {esperado_sdist}"
        )
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
    assert "uv sync --locked --group desarrollo --group seguridad --all-extras" in texto
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
      - run: uv sync --locked --group desarrollo --group seguridad --all-extras
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
- Modify: <code>.gitignore</code> para ignorar sólo <code>tramalia-documentacion-sin-conexion.zip</code>, su compañero <code>.zip.sha256</code> y <code>.mkdocs.sin-conexion.tmp.yml</code>, retirando sus nombres ingleses

**Interfaces:**
- Produces: Pages sólo desde <code>documentacion.yml</code>; el artefacto <code>documentacion-sin-conexion</code> sólo desde su workflow dedicado, con ZIP reproducible y resumen SHA-256 independiente.

- [ ] **Step 1: Add a failing deterministic ZIP test**

~~~python
import hashlib
from pathlib import Path

from scripts.construir_documentacion_sin_conexion import (
    RESUMEN_ZIP_SALIDA,
    ZIP_SALIDA,
    escribir_resumen_zip,
    escribir_zip_determinista,
)


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
    assert RESUMEN_ZIP_SALIDA.name == "tramalia-documentacion-sin-conexion.zip.sha256"


def test_resumen_identifica_bytes_y_nombre_exacto(tmp_path):
    archivo = tmp_path / ZIP_SALIDA.name
    archivo.write_bytes(b"documentacion")
    resumen = tmp_path / RESUMEN_ZIP_SALIDA.name
    escribir_resumen_zip(archivo, resumen)
    assert resumen.read_text(encoding="ascii") == (
        f"{hashlib.sha256(archivo.read_bytes()).hexdigest()}  {ZIP_SALIDA.name}\n"
    )


def test_gitignore_usa_nombres_documentales_espanoles():
    raiz = Path(__file__).resolve().parents[2]
    contenido = (raiz / ".gitignore").read_text(encoding="utf-8")
    assert "tramalia-documentacion-sin-conexion.zip" in contenido
    assert "tramalia-documentacion-sin-conexion.zip.sha256" in contenido
    assert ".mkdocs.sin-conexion.tmp.yml" in contenido
    assert "tramalia-docs-offline.zip" not in contenido
    assert ".mkdocs.offline.tmp.yml" not in contenido
~~~

Run: <code>uv run --no-sync pytest tests/publicacion/test_documentacion_sin_conexion.py -q</code>

Expected: FAIL because the Spanish module/helper is absent. Ejecutar <code>git mv scripts/build_offline_docs.py scripts/construir_documentacion_sin_conexion.py</code>; renombrar <code>ROOT → RAIZ</code>, <code>CONFIG → CONFIGURACION</code>, <code>OUT_ZIP → ZIP_SALIDA</code>, <code>main → principal</code> y todas las variables locales propias al español ASCII. Definir <code>ZIP_SALIDA = RAIZ / "tramalia-documentacion-sin-conexion.zip"</code> y <code>RESUMEN_ZIP_SALIDA = RAIZ / "tramalia-documentacion-sin-conexion.zip.sha256"</code>, renombrar el temporal a <code>.mkdocs.sin-conexion.tmp.yml</code>, actualizar `.gitignore`, reemplazar el loop de ZIP actual por esta implementación y llamarla desde <code>principal()</code> usando <code>int(os.environ.get("SOURCE_DATE_EPOCH", "315532800"))</code>. <code>principal</code> acepta <code>--salida</code> y deriva su compañero añadiendo <code>.sha256</code>; cada invocación construye MkDocs en un temporal nuevo y no reutiliza <code>site/</code>. Mantener comentarios en español y el docstring de módulo en inglés:

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
            informacion.create_system = 3
            informacion.compress_type = zipfile.ZIP_DEFLATED
            informacion.external_attr = 0o100644 << 16
            archivo_zip.writestr(informacion, ruta.read_bytes(), compresslevel=9)


def escribir_resumen_zip(origen: Path, destino: Path) -> None:
    """Write the SHA-256 companion file for an offline documentation ZIP."""
    resumen = hashlib.sha256(origen.read_bytes()).hexdigest()
    destino.write_text(f"{resumen}  {origen.name}\n", encoding="ascii", newline="\n")
~~~

Add <code>import argparse</code>, <code>hashlib</code>, <code>os</code> and <code>from datetime import UTC, datetime</code>; change the module docstring to English. La prueba abre el ZIP y exige <code>create_system == 3</code>, modo 0644, orden lexicográfico y timestamp fijo para cada miembro. Una prueba de integración invoca el script dos veces, con el mismo <code>SOURCE_DATE_EPOCH</code> pero temporales de construcción distintos, y compara bytes y SHA de ambos ZIP; no basta archivar dos veces el mismo árbol <code>site/</code>. Así se demuestra reproducibilidad del build completo y que la metadata no depende de Windows/Linux.

- [ ] **Step 2: Preparar la migración reversible de GitHub Pages**

Estado externo comprobado el 14 de julio de 2026: la API de Pages devuelve
<code>build_type: legacy</code> con fuente <code>gh-pages:/</code>, y el environment
<code>github-pages</code> usa políticas personalizadas cuya única rama es
<code>gh-pages</code>. <code>actions/configure-pages</code> no cambia esas dos
decisiones administrativas. Antes del primer despliegue desde <code>main</code>,
guardar las tres respuestas sin datos sensibles bajo
<code>.artefactos/publicacion/pages-antes/</code>:

~~~powershell
New-Item -ItemType Directory -Force .artefactos/publicacion/pages-antes | Out-Null
gh api repos/MscottB/tramalia/pages | Set-Content -Encoding utf8 .artefactos/publicacion/pages-antes/pages.json
gh api repos/MscottB/tramalia/environments/github-pages | Set-Content -Encoding utf8 .artefactos/publicacion/pages-antes/environment.json
gh api repos/MscottB/tramalia/environments/github-pages/deployment-branch-policies | Set-Content -Encoding utf8 .artefactos/publicacion/pages-antes/politicas.json
~~~

La migración se ejecuta en Task 10 sólo después de integrar y subir el candidato
a <code>main</code> y de que <code>validacion.yml</code> pase para su SHA exacto.
<code>documentacion.yml</code> ya existe entonces en la rama predeterminada: después
del cambio administrativo se ejecuta o reejecuta su run asociado a ese mismo SHA
y se verifica antes del tag. Actualizar por API la política
existente de rama de <code>gh-pages</code> a <code>main</code> y luego Pages a
<code>build_type=workflow</code>. Reconsultar y exigir exactamente
<code>workflow</code> y una única policy de tipo <code>branch</code> llamada
<code>main</code>. Si falta permiso administrativo, la alternativa equivalente es
Settings → Environments → github-pages y Settings → Pages → Source → GitHub
Actions; hasta verificar ambos valores el despliegue y el tag quedan bloqueados.

Conservar en la bitácora operativa los comandos inversos: restaurar
<code>build_type=legacy</code> con fuente <code>gh-pages:/</code> y renombrar la
policy a <code>gh-pages</code>. Si el primer despliegue falla, ejecutar ese rollback
antes de retirar la publicación heredada y comprobar que el sitio anterior sigue
sirviendo. No borrar la rama <code>gh-pages</code> en esta BETA.

- [ ] **Step 3: Create documentacion.yml**

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
    if: >-
      ${{ github.event.workflow_run.conclusion == 'success' &&
          github.event.workflow_run.event == 'push' &&
          github.event.workflow_run.head_branch == 'main' &&
          github.event.workflow_run.head_repository.full_name == github.repository }}
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
      - run: uv sync --locked --all-extras
      - run: uv pip install --require-hashes -r requisitos-documentacion.txt
      - run: uv run --no-sync mkdocs build --strict --site-dir site
      - name: Impedir despliegue de una validación antigua
        env:
          GH_TOKEN: ${{ github.token }}
          HEAD_VALIDADO: ${{ github.event.workflow_run.head_sha }}
        shell: bash
        run: |
          HEAD_ACTUAL="$(gh api "repos/$GITHUB_REPOSITORY/git/ref/heads/main" --jq .object.sha)"
          test "$HEAD_VALIDADO" = "$HEAD_ACTUAL"
      - uses: actions/configure-pages@45bfe0192ca1faeb007ade9deae92b16b8254a0d # v6.0.0
      - uses: actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9 # v5.0.0
        with:
          path: site
  desplegar:
    needs: construir
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deploy.outputs.page_url }}
    steps:
      - name: Revalidar HEAD inmediatamente antes de desplegar
        env:
          GH_TOKEN: ${{ github.token }}
          HEAD_VALIDADO: ${{ github.event.workflow_run.head_sha }}
        shell: bash
        run: |
          HEAD_ACTUAL="$(gh api "repos/$GITHUB_REPOSITORY/git/ref/heads/main" --jq .object.sha)"
          test "$HEAD_VALIDADO" = "$HEAD_ACTUAL"
      - id: deploy
        uses: actions/deploy-pages@cd2ce8fcbc39b97be8ca5fce6e763baed58fa128 # v5.0.0
~~~

- [ ] **Step 4: Create documentacion-sin-conexion.yml**

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
      - run: uv sync --locked --all-extras
      - run: uv pip install --require-hashes -r requisitos-documentacion.txt
      - name: Fijar timestamp desde el commit
        run: echo "SOURCE_DATE_EPOCH=$(git log -1 --format=%ct)" >> "$GITHUB_ENV"
      - run: uv run --no-sync python scripts/construir_documentacion_sin_conexion.py
      - uses: actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1
        with:
          name: documentacion-sin-conexion
          path: |
            tramalia-documentacion-sin-conexion.zip
            tramalia-documentacion-sin-conexion.zip.sha256
          if-no-files-found: error
          retention-days: 14
~~~

- [ ] **Step 5: Extend workflow separation tests**

Assert old filenames are absent; <code>documentacion.yml</code> uses only <code>workflow_run</code>, has no <code>workflow_dispatch</code>, requires a successful validation propia originada por <code>push</code> de <code>main</code> y checks out exactly its validated <code>head_sha</code>. Antes de upload y otra vez inmediatamente antes de deploy consulta <code>refs/heads/main</code> y exige igualdad con <code>head_sha</code>; una validación A antigua que termine después de B no puede retroceder Pages. It contains deploy-pages but neither <code>gh release</code> nor PyPI, grants only <code>contents: read</code>/<code>pages: read</code> to job <code>construir</code>, and grants <code>contents: read</code>/<code>pages: write</code>/<code>id-token: write</code> only inside job <code>desplegar</code> (el read es necesario para `gh api`; ningún job obtiene write adicional). El workflow sin conexión contiene <code>workflow_call</code>, sube exactamente el ZIP y su <code>.zip.sha256</code>, y no contiene deploy-pages ni subida a Release. Expand the SHA-pin test at this point to exactly <code>validacion.yml</code>, <code>documentacion.yml</code> and <code>documentacion-sin-conexion.yml</code>; do not scan workflows already scheduled for deletion. Además de los contratos semánticos, Actionlint 1.7.12 fijado por 03a debe aceptar cada YAML: búsquedas de texto no sustituyen validación sintáctica/de expresiones.

- [ ] **Step 6: Verify and commit**

Run:

~~~bash
uv run --no-sync actionlint
uv run --no-sync pytest tests/publicacion -q
uv run --no-sync python scripts/construir_documentacion_sin_conexion.py
uv run --no-sync mkdocs build --strict
~~~

Expected: PASS and a navigable <code>tramalia-documentacion-sin-conexion.zip</code> cuyo compañero <code>.zip.sha256</code> valida exactamente sus bytes.

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
    assert texto.count("actions/attest@") == 2
    assert "tramalia-documentacion-sin-conexion.zip.sha256" in texto
    assert "sha256sum --check tramalia-documentacion-sin-conexion.zip.sha256" in texto
    assert "Version(sys.argv[1]).is_prerelease" in texto
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
      - uses: astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990 # v8.3.2
        with:
          version: "0.11.28"
          enable-cache: true
      - run: uv sync --locked --group desarrollo --group seguridad
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
          --notas artefactos/notas-lanzamiento.md
      - name: Reunir activos ya verificados
        shell: bash
        run: |
          (cd artefactos/documentacion && sha256sum --check tramalia-documentacion-sin-conexion.zip.sha256)
          mkdir -p artefactos/lanzamiento/dist
          uv run --no-sync python -c 'import sys; from packaging.version import Version; print("1" if Version(sys.argv[1]).is_prerelease else "0")' "${TAG#v}" > artefactos/lanzamiento/es-prelanzamiento.txt
          cp artefactos/paquete/dist/*.whl artefactos/lanzamiento/dist/
          cp artefactos/paquete/dist/*.tar.gz artefactos/lanzamiento/dist/
          cp artefactos/paquete/SHA256SUMS artefactos/lanzamiento/
          cp artefactos/documentacion/tramalia-documentacion-sin-conexion.zip artefactos/lanzamiento/
          cp artefactos/documentacion/tramalia-documentacion-sin-conexion.zip.sha256 artefactos/lanzamiento/
          cp artefactos/notas-lanzamiento.md artefactos/lanzamiento/
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
      - uses: actions/attest@a1948c3f048ba23858d222213b7c278aabede763 # v4.1.1
        with:
          subject-path: artefactos/lanzamiento/tramalia-documentacion-sin-conexion.zip

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
            artefactos/lanzamiento/tramalia-documentacion-sin-conexion.zip.sha256
          )
          ES_PRELANZAMIENTO="$(<artefactos/lanzamiento/es-prelanzamiento.txt)"
          if [[ "$ES_PRELANZAMIENTO" == "1" ]]; then
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
          python scripts/verificar_lanzamiento.py preparar --tag "$TAG" --distribuciones dist --manifiesto SHA256SUMS --notas "$RUNNER_TEMP/notas-lanzamiento.md"
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

Expandir el contrato de acciones fijadas para enumerar exactamente los cinco workflows finales y ejecutar Actionlint 1.7.12 sobre todos ellos. Verificar además que la ejecución manual sólo admita un <code>refs/tags/v*</code> seleccionado como referencia del workflow, que el commit resuelto del tag coincida con <code>GITHUB_SHA</code>, que todo <code>gh release create</code> incluya <code>--draft --verify-tag</code> y nunca <code>--target</code>, y que sólo <code>crear_borrador</code> tenga <code>contents: write</code>. La clasificación prerelease usa <code>packaging.version.Version.is_prerelease</code> dentro del job que sincronizó el lock, por lo que reconoce tanto <code>1.0.0b1</code> como <code>1.0.0.dev0</code> y no depende de una regex parcial. Exigir dos atestaciones: una para wheel/sdist y otra para el ZIP sin conexión; el compañero SHA debe verificarse antes de crear el artefacto de lanzamiento. En PyPI, exigir <code>--signer-workflow</code>, <code>--source-digest</code> y <code>--source-ref</code> para ligar cada wheel/sdist al workflow, commit y tag exactos; el bloque <code>publicar</code> no debe contener checkout, shell ni scripts del repositorio. La publicación manual del borrador es deliberada: un release creado con <code>GITHUB_TOKEN</code> no debe ser la fuente de un evento recursivo de publicación.

Run:

~~~powershell
uv run --no-sync actionlint
uv run --no-sync pytest tests/publicacion -q
uv build --out-dir dist/ensayo
uv run --no-sync python scripts/verificar_lanzamiento.py generar-resumenes --distribuciones dist/ensayo --manifiesto dist/SHA256SUMS-ensayo
$version_actual = uv run --no-sync python -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])'
uv run --no-sync python scripts/verificar_lanzamiento.py preparar --tag "v$version_actual" --distribuciones dist/ensayo --manifiesto dist/SHA256SUMS-ensayo --notas dist/ensayo/notas-lanzamiento.md
$archivos_ensayo = Get-ChildItem -LiteralPath dist/ensayo -File | Where-Object { $_.Name -like '*.whl' -or $_.Name -like '*.tar.gz' } | ForEach-Object FullName
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
- Modify: <code>pyproject.toml</code>, <code>tramalia/__init__.py</code>, <code>CHANGELOG.md</code> y <code>uv.lock</code> con una única versión <code>1.0.0b1</code> / tag <code>v1.0.0b1</code>
- Create: <code>.github/LISTA_DESPLIEGUE_TRAMALIA.md</code> con la lista propia y verificable de GitHub/PyPI
- Verify generic: <code>tramalia/templates/project/docs/ai/12-despliegue-lanzamiento.md</code> no contiene <code>MscottB</code>, <code>tramalia-cli</code> ni identidades externas del producto Tramalia

**Interfaces:**
- Consumes: los cinco workflows ya integrados en la rama principal y la configuración externa del proyecto PyPI.
- Produces: un tag nuevo que apunta al código BETA validado y un **borrador**, nunca una publicación automática de GitHub Release.

Precondición bloqueante: Task 0 debe estar completada, la auditoría de titularidad no puede tener contribuciones sin resolver y el artefacto debe declarar <code>PolyForm-Noncommercial-1.0.0 AND Apache-2.0</code> con sus archivos de licencia. Si no se cumple, no se cambia versión, no se crea tag y no se publica draft.

- [ ] **Step 1: Bloquear publicación hasta verificar identidades externas**

En GitHub, crear o revisar el environment <code>pypi</code> y exigir una regla
<code>required_reviewers</code> explícita; que el environment simplemente exista no
es suficiente (el estado observado inicialmente tiene
<code>protection_rules: []</code>). En el proyecto PyPI <code>tramalia-cli</code>,
reemplazar el Trusted Publisher histórico ligado a <code>publish.yml</code> por esta
identidad exacta: propietario <code>MscottB</code>, repositorio
<code>tramalia</code>, workflow <code>publicar-pypi.yml</code>, environment
<code>pypi</code>. Registrar la comprobación en la lista propia
<code>.github/LISTA_DESPLIEGUE_TRAMALIA.md</code>; no guardar tokens ni capturas
sensibles. La plantilla que Tramalia entrega a proyectos de clientes conserva
sólo placeholders/instrucciones genéricas. Esta comprobación es bloqueante: si
cualquier campo difiere o no puede leerse, se puede crear/revisar el draft, pero
no publicarlo.

Verificar por lectura la parte de GitHub cuando la sesión lo permita:

~~~bash
gh api repos/MscottB/tramalia/environments/pypi
gh api repos/MscottB/tramalia/environments/pypi --jq '.protection_rules[] | select(.type == "required_reviewers")'
~~~

Expected: el environment existe y devuelve al menos un revisor requerido; la identidad de Trusted Publishing se confirma por separado en la configuración del proyecto PyPI. Si falta la regla, configurarla mediante Settings → Environments o el endpoint administrativo oficial, reconsultar y registrar sólo el resultado no sensible. Mientras Tramalia tenga un único mantenedor autorizado, no activar <code>prevent_self_review</code> sin registrar antes otro revisor con acceso: esa combinación bloquearía permanentemente el job OIDC. Si se incorpora un segundo mantenedor, activar la prevención de autoaprobación y verificar que esa persona puede aprobar el environment antes del tag.

- [ ] **Step 2: Preparar y confirmar el candidato inmutable 1.0.0b1**

Actualizar una sola vez <code>project.version</code> y <code>tramalia.__version__</code> de <code>1.0.0.dev0</code> a <code>1.0.0b1</code>, conservando la expresión legal ya aplicada, y convertir el encabezado dev en la sección BETA del changelog. Añadir notas BETA que resuman contratos, migraciones y riesgos conocidos. Ejecutar <code>uv lock --python 3.11</code> y después <code>uv sync --locked --group desarrollo --group seguridad --all-extras</code> para demostrar que el lock regenerado corresponde a la versión nueva sin podar Actionlint/Semgrep. Construir wheel/sdist nuevos **después** del bump, generar sus hashes, ejecutar Twine y validarlos contra <code>v1.0.0b1</code>; no reutilizar el ensayo 1.0.0.dev0 de Task 9:

~~~powershell
$distribuciones_beta = Join-Path "dist" ("ensayo-beta-" + [guid]::NewGuid().ToString("N"))
$manifiesto_beta = Join-Path $distribuciones_beta "SHA256SUMS"
$notas_beta = Join-Path $distribuciones_beta "notas-lanzamiento.md"
uv build --out-dir $distribuciones_beta
uv run --no-sync python scripts/verificar_lanzamiento.py generar-resumenes --distribuciones $distribuciones_beta --manifiesto $manifiesto_beta
$archivos_beta = Get-ChildItem -LiteralPath $distribuciones_beta -File | Where-Object { $_.Name -like '*.whl' -or $_.Name -like '*.tar.gz' } | ForEach-Object FullName
uv run --no-sync twine check $archivos_beta
uv run --no-sync python scripts/verificar_lanzamiento.py preparar --tag v1.0.0b1 --distribuciones $distribuciones_beta --manifiesto $manifiesto_beta --notas $notas_beta
~~~

Expected: wheel y sdist contienen metadata <code>1.0.0b1</code>, hashes y Twine pasan, y las notas salen de la sección BETA del changelog. Repetir luego la verificación final inferior.

Ejecutar ahora la suite completa de <code>Final verification</code>, todavía sobre
la rama candidata, y exigir todos sus gates verdes. Sólo después crear el commit
candidato; ese commit incluye el bump, lock, changelog y lista de despliegue:

~~~bash
git add pyproject.toml tramalia/__init__.py CHANGELOG.md uv.lock .github/LISTA_DESPLIEGUE_TRAMALIA.md tramalia/templates/project/docs/ai/12-despliegue-lanzamiento.md
git commit -m "chore: preparar candidato inmutable 1.0.0b1"
git status --porcelain
~~~

Expected: el estado está limpio. Desde este commit candidato hasta crear el tag
no se modifica, genera, formatea ni confirma ningún archivo rastreado; cualquier
cambio obliga a crear un commit candidato nuevo y repetir suite, CI y Pages.

- [ ] **Step 3: Integrar el candidato en main y validar su SHA exacto**

Integrar y subir el candidato sin crear todavía el tag. Registrar el SHA remoto y
esperar la ejecución <code>validacion.yml</code> originada por ese push:

~~~powershell
git switch main
git pull --ff-only origin main
git merge --ff-only codex/beta-implementation
git push origin main
$shaCandidato = git rev-parse HEAD
$shaRemoto = git rev-parse origin/main
if ($shaCandidato -ne $shaRemoto) { throw 'main remoto no coincide con el candidato.' }
$idValidacion = gh run list --workflow validacion.yml --branch main --commit $shaCandidato --event push --limit 20 --json databaseId,headSha --jq ".[] | select(.headSha == \"$shaCandidato\") | .databaseId" | Select-Object -First 1
if (-not $idValidacion) { throw 'No existe validación remota para el SHA candidato.' }
gh run watch $idValidacion --exit-status
if (git status --porcelain) { throw 'El árbol cambió después de validar el candidato.' }
if ((git rev-parse HEAD) -ne $shaCandidato -or (git rev-parse origin/main) -ne $shaCandidato) { throw 'El SHA cambió después de CI.' }
~~~

Expected: <code>validacion.yml</code> concluye correctamente con
<code>headSha == $shaCandidato</code>. Un run verde de otro SHA no sirve.

- [ ] **Step 4: Migrar Pages y desplegar documentación del mismo SHA**

Sólo después de CI verde guardar las tres respuestas indicadas en Task 8,
resolver la policy heredada, cambiarla a <code>main</code> y activar Pages mediante
Actions. La rama <code>gh-pages</code> no se elimina:

~~~powershell
$rutaPoliticas = 'repos/MscottB/tramalia/environments/github-pages/deployment-branch-policies'
$idPolitica = gh api $rutaPoliticas --jq '.branch_policies[] | select(.name == "gh-pages" and .type == "branch") | .id'
if (-not $idPolitica) { throw 'No se encontró la policy heredada gh-pages.' }
gh api --method PUT "$rutaPoliticas/$idPolitica" -f name=main
gh api --method PUT repos/MscottB/tramalia/pages -f build_type=workflow
$tipoConstruccion = gh api repos/MscottB/tramalia/pages --jq .build_type
$politicas = gh api $rutaPoliticas --jq '[.branch_policies[] | {name,type}]'
if ($tipoConstruccion -ne 'workflow') { throw 'Pages no quedó en modo workflow.' }
if ($politicas -ne '[{"name":"main","type":"branch"}]') { throw "Policy inesperada: $politicas" }
$idDocumentacion = gh run list --workflow documentacion.yml --branch main --commit $shaCandidato --limit 20 --json databaseId,headSha --jq ".[] | select(.headSha == \"$shaCandidato\") | .databaseId" | Select-Object -First 1
if (-not $idDocumentacion) { throw 'No existe ejecución documental para el SHA validado.' }
gh run rerun $idDocumentacion
gh run watch $idDocumentacion --exit-status
$shaDocumentacion = gh run view $idDocumentacion --json headSha --jq .headSha
if ($shaDocumentacion -ne $shaCandidato) { throw 'Pages no desplegó el SHA candidato.' }
if ((git rev-parse HEAD) -ne $shaCandidato -or (git rev-parse origin/main) -ne $shaCandidato -or (git status --porcelain)) { throw 'El candidato cambió durante Pages.' }
~~~

Comprobar el sitio público ES/EN y el workflow. Si falla, restaurar
<code>build_type=legacy</code> con <code>source[branch]=gh-pages</code> y
<code>source[path]=/</code>, devolver la policy a <code>gh-pages</code> y no crear
el tag. Cualquier corrección de archivos reinicia desde Step 2.

- [ ] **Step 5: Crear y subir el tag sobre el SHA ya validado y desplegado**

~~~powershell
if ((git rev-parse HEAD) -ne $shaCandidato -or (git rev-parse origin/main) -ne $shaCandidato -or (git status --porcelain)) { throw 'El candidato dejó de ser inmutable.' }
git tag -a v1.0.0b1 $shaCandidato -m "Tramalia 1.0.0b1"
if ((git rev-list -n 1 v1.0.0b1) -ne $shaCandidato) { throw 'El tag no apunta al candidato validado.' }
git push origin v1.0.0b1
~~~

Expected: <code>lanzamiento-github</code> recibe exactamente el mismo SHA y crea
un draft para <code>v1.0.0b1</code>. No ejecutar el workflow sobre
<code>v0.33.0</code>, que ya apunta a otro commit.

- [ ] **Step 6: Leer y verificar el borrador; dejar la publicación a una persona**

~~~bash
gh release view v1.0.0b1 --json isDraft,isPrerelease,tagName,targetCommitish,assets,url
~~~

Expected: <code>isDraft=true</code>, <code>isPrerelease=true</code> y
<code>targetCommitish</code> resuelve a <code>$shaCandidato</code>; contiene un wheel,
un sdist, <code>SHA256SUMS</code>, el ZIP sin conexión y su compañero SHA. Descargar
todo en un temporal, validar ambos manifiestos y verificar atestaciones contra el
workflow, commit y tag exactos. Una persona revisa notas, activos, lista PyPI y
riesgos antes de pulsar **Publish release**; ese acto separado activa PyPI.

## Final verification

Run from a clean Python 3.11 environment:

~~~powershell
uv sync --locked --group desarrollo --group seguridad --all-extras
uv pip install --require-hashes -r requisitos-documentacion.txt
uv run --no-sync pytest
uv run --no-sync pytest tests/publicacion/test_licencia.py -q
uv run --no-sync actionlint
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync mypy tramalia
uv run --no-sync semgrep --test --config configuracion/semgrep/seguridad-python.yml tests/recursos/semgrep
uv run --no-sync semgrep scan --config configuracion/semgrep/seguridad-python.yml --error --metrics=off --disable-version-check --exclude tests/recursos/semgrep tramalia scripts tests
$ruta_gitleaks = uv run --no-sync python scripts/instalar_gitleaks.py --destino "$HOME/.local/bin" | Select-Object -Last 1
& $ruta_gitleaks git --redact --no-banner --config .gitleaks.toml --exit-code 1
& $ruta_gitleaks dir . --redact --no-banner --config .gitleaks.toml --exit-code 1
uv run --no-sync python scripts/generar_proyecto_prueba_seguridad.py --salida .artefactos/seguridad/proyecto-generado
uv run --no-sync semgrep scan --config configuracion/semgrep/seguridad-python.yml --error --metrics=off --disable-version-check .artefactos/seguridad/proyecto-generado
& $ruta_gitleaks dir .artefactos/seguridad/proyecto-generado --redact --no-banner --config .gitleaks.toml --exit-code 1
uv run --no-sync mkdocs build --strict
uv run --no-sync python scripts/construir_documentacion_sin_conexion.py
uv run --no-sync pytest tests/publicacion tests/contratos/test_documentacion.py -q
uv run --no-sync python scripts/generar_capturas_tui.py --salida .artefactos/capturas-tui-final
uv run --no-sync pytest tests/contratos/test_capturas_tui.py -q
npm ci --ignore-scripts
npm run prueba:guardia-capturas
npm run prueba:servidor-documentacion
npx playwright install chromium
npm run prueba:ux
docker run --rm --ipc=host --env CI=1 --env TRAMALIA_COMPARAR_CAPTURAS=1 --volume "${PWD}:/trabajo" --workdir /trabajo mcr.microsoft.com/playwright:v1.61.1-noble@sha256:5b8f294aff9041b7191c34a4bab3ac270157a28774d4b0660e9743297b697e48 bash -lc "npm ci --ignore-scripts && npm run prueba:ux"
npm run prueba:lighthouse
git diff --check
~~~

Expected: the full suite, mypy, license contract, Semgrep, Gitleaks, ES/EN strict build, TUI capture contract, Node server/snapshot guards, functional Playwright/axe, canonical Linux snapshot comparison and Lighthouse pass; the ZIP sin conexión and its valid SHA companion are created; workflow contracts prove separate deployment responsibilities, pinned actions, shared artifacts, provenance verification, least-privilege OIDC and no PyPI rebuild; <code>git diff --check</code> prints nothing.

El ensayo remoto no forma parte del gate local y nunca reutiliza la versión actual publicada. Se ejecuta mediante Task 10, después de integrar los workflows en <code>main</code>, con <code>v1.0.0b1</code> y la configuración externa confirmada. El resultado esperado es sólo un borrador; su publicación humana y la posterior subida a PyPI son pasos separados.
