# Execution & gates

These tools **run** the validations. Tramalia orchestrates them via `mise` (the runner) and captures their raw output in the evidence pack.

!!! info "What is *bootstrap*?"
    The first three (**mise, git, uv**) are marked as **bootstrap**: they're the **base you install by hand first**, because they can't install themselves (mise can't install itself; git and uv are prerequisites). Once present, `mise install` brings everything else. See [Glossary](glosario.md).

!!! tip "Recommended way"
    Almost all are installed **via mise** (`mise use …`): they stay declared in `mise.toml` and `mise upgrade` maintains them. The direct way is the alternative.

## mise — the runner (bootstrap)

- **What it is / scope:** tool version manager + environment variables + **task/gate runner**. It's the one that installs and runs almost everything else.
- **Requires:** nothing (single binary, Rust).
- **Install (bootstrap — mise can't install itself):**
  - Linux/macOS: `curl https://mise.run | sh`
  - Windows: `winget install jdx.mise`
- **Tramalia uses it in:** `gates`, `close` (→ `mise run gates`), `doctor`/`update` (`mise install`/`mise upgrade`).
- **Interacts with:** practically all — it installs them (`mise use npm:…`, `pipx:…`, `aqua:…`) and runs them.

## git — versioning (bootstrap)

- **What it is / scope:** version control; the base of all versioned memory, skills and evidence.
- **Requires:** nothing.
- **Install:** `winget install Git.Git` · `brew install git` · `apt install git` ([git-scm.com](https://git-scm.com)).
- **Tramalia uses it in:** `skills` (clone/pull), `evidence` (reads `git diff`).
- **Interacts with:** the whole repo — it's the "source of truth" that Tramalia governs.

## uv — Python tools installer (bootstrap)

- **What it is / scope:** ultra-fast installer/runner of Python packages and tools (copier, Serena, Spec Kit).
- **Requires:** nothing (binary, Rust).
- **Install:**
  - Linux/macOS: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Windows: `winget install astral-sh.uv`
- **Tramalia uses it in:** indirectly (Serena via `uvx`, copier/Spec Kit via `uv tool`).

## Semgrep — security gate (SAST)

- **What it is / scope:** static analysis to find vulnerabilities and bad practices.
- **Requires:** Python.
- **Install:** `mise use pipx:semgrep` · direct: `pipx install semgrep`.
- **Tramalia uses it in:** the `security` gate (inside `gates`/`close`).
- **Interacts with:** the rules in `docs/ai/04-reglas-seguridad.md`; its raw output goes to the evidence pack.

## Gitleaks — security gate (secrets)

- **What it is / scope:** detects leaked secrets/credentials in the repo.
- **Requires:** nothing (binary, Go).
- **Install:** `mise use aqua:gitleaks` · direct: `brew install gitleaks` or a release binary.
- **Tramalia uses it in:** the `security` gate.

## SQLFluff — database gate

- **What it is / scope:** SQL linter and formatter.
- **Requires:** Python.
- **Install:** `mise use pipx:sqlfluff` · direct: `pipx install sqlfluff`.
- **Tramalia uses it in:** the `database` gate (if SQL/migrations are detected); rules in `docs/ai/03`.

## Lighthouse CI · Playwright · axe · pa11y · Storybook — UX/UI gate

They only apply if there's a frontend. **All require Node** (`tramalia doctor` flags it as "requires Node").

| Tool | Install | Role in the `ux` gate |
|---|---|---|
| **Lighthouse CI** | `mise use npm:@lhci/cli` · `npm i -g @lhci/cli` (requires Chrome) | performance + a11y + best practices |
| **Playwright** | `mise use npm:playwright` · `npm i -D @playwright/test` + `npx playwright install` | visual regression + e2e |
| **axe-core** | `npm i -D @axe-core/cli` (or inside Playwright) | accessibility |
| **pa11y** | `npm i -g pa11y` (requires Chromium) | accessibility |
| **Storybook** | `npx storybook@latest init` (in the project) | component states |

- **Tramalia uses them in:** the `ux` gate (via `mise run ux`); rules in `docs/ai/11-reglas-ux-ui.md`.
- **Interact with:** the detected frontend code; their raw output goes to the evidence pack.
