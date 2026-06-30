# Ejecución y gates

Estas herramientas **corren** las validaciones. Tramalia las orquesta vía `mise` (el runner) y captura su salida cruda en el evidence pack.

!!! tip "Vía recomendada"
    Casi todas se instalan **vía mise** (`mise use …`): quedan declaradas en `mise.toml` y `mise upgrade` las mantiene. La vía directa es la alternativa.

## mise — el runner (bootstrap)

- **Qué es / alcance:** gestor de versiones de herramientas + variables de entorno + **runner de tareas/gates**. Es quien instala y ejecuta casi todo el resto.
- **Requiere:** nada (binario único, Rust).
- **Instalar (bootstrap — mise no se instala a sí mismo):**
  - Linux/macOS: `curl https://mise.run | sh`
  - Windows: `winget install jdx.mise`
- **Tramalia la usa en:** `gates`, `close` (→ `mise run gates`), `doctor`/`update` (`mise install`/`mise upgrade`).
- **Interactúa con:** prácticamente todas — las instala (`mise use npm:…`, `pipx:…`, `aqua:…`) y las corre.

## git — versionado (bootstrap)

- **Qué es / alcance:** control de versiones; base de toda la memoria, skills y evidencia versionada.
- **Requiere:** nada.
- **Instalar:** `winget install Git.Git` · `brew install git` · `apt install git` ([git-scm.com](https://git-scm.com)).
- **Tramalia la usa en:** `skills` (clone/pull), `evidence` (lee `git diff`).
- **Interactúa con:** el repo entero — es la "fuente de verdad" que Tramalia gobierna.

## uv — instalador de tools Python (bootstrap)

- **Qué es / alcance:** instalador/ejecutor ultrarrápido de paquetes y herramientas Python (copier, Serena, Spec Kit).
- **Requiere:** nada (binario, Rust).
- **Instalar:**
  - Linux/macOS: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Windows: `winget install astral-sh.uv`
- **Tramalia la usa en:** indirectamente (Serena vía `uvx`, copier/Spec Kit vía `uv tool`).

## Semgrep — gate de seguridad (SAST)

- **Qué es / alcance:** análisis estático para encontrar vulnerabilidades y malas prácticas.
- **Requiere:** Python.
- **Instalar:** `mise use pipx:semgrep` · directa: `pipx install semgrep`.
- **Tramalia la usa en:** gate `security` (dentro de `gates`/`close`).
- **Interactúa con:** las reglas de `docs/ai/04-reglas-seguridad.md`; su salida cruda va al evidence pack.

## Gitleaks — gate de seguridad (secretos)

- **Qué es / alcance:** detecta secretos/credenciales filtrados en el repo.
- **Requiere:** nada (binario, Go).
- **Instalar:** `mise use aqua:gitleaks` · directa: `brew install gitleaks` o binario de releases.
- **Tramalia la usa en:** gate `security`.

## SQLFluff — gate de base de datos

- **Qué es / alcance:** linter y formateador de SQL.
- **Requiere:** Python.
- **Instalar:** `mise use pipx:sqlfluff` · directa: `pipx install sqlfluff`.
- **Tramalia la usa en:** gate `database` (si se detecta SQL/migraciones); reglas en `docs/ai/03`.

## Lighthouse CI · Playwright · axe · pa11y · Storybook — gate UX/UI

Solo aplican si hay frontend. **Todas requieren Node** (`tramalia doctor` lo marca como "requiere Node").

| Herramienta | Instalar | Rol en el gate `ux` |
|---|---|---|
| **Lighthouse CI** | `mise use npm:@lhci/cli` · `npm i -g @lhci/cli` (requiere Chrome) | rendimiento + a11y + best practices |
| **Playwright** | `mise use npm:playwright` · `npm i -D @playwright/test` + `npx playwright install` | regresión visual + e2e |
| **axe-core** | `npm i -D @axe-core/cli` (o dentro de Playwright) | accesibilidad |
| **pa11y** | `npm i -g pa11y` (requiere Chromium) | accesibilidad |
| **Storybook** | `npx storybook@latest init` (en el proyecto) | estados de componentes |

- **Tramalia las usa en:** gate `ux` (vía `mise run ux`); reglas en `docs/ai/11-reglas-ux-ui.md`.
- **Interactúan con:** el código frontend detectado; su salida cruda va al evidence pack.
