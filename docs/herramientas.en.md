# Tools: internal and external

Tramalia has its **own core** (little code, what nobody else does well) and **orchestrates external tools** (invoked as separate programs via CLI or MCP). Here's everything, with its scope and license.

## Internal — Tramalia's core

Tramalia's own code (Python, Apache-2.0). Works **standalone, with the stdlib only**; Rich/Questionary are optional extras for "pretty mode".

| Command / module | What it does | Type |
|---|---|---|
| `init` (`core/scaffold.py`) | generates the idempotent convention (AGENTS.md, docs/ai, mise.toml, .mcp.json) | core |
| `doctor` (`core/doctor.py`) | diagnoses required/optional tools and how to install them | core |
| `detect` (`core/detect.py`) | detects the stack and applicable gates | core |
| **`close` (`core/governance.py`)** | **ritual: gates → evidence (raw) + `metadata.json` → handoff, with enforcement** | core ★ |
| **`log` (`core/governance.py`)** | **audit trail: reads each close's `metadata.json`** | core ★ |
| `evidence` (`core/evidence.py`) | creates the closing evidence pack | core |
| `handoff` (`core/handoff.py`) | appends a structured handover to `docs/ai/07` | core |
| `skills` (`core/skills.py`) | clones/updates skills from their repos | core (uses git) |
| `mcp` (`mcp_server.py`) | MCP façade: exposes the convention as native tools | core (+ mcp SDK) |
| `ui` (`tui.py`) | TUI dashboard: Overview · Audit · Close | core (+ `[tui]` extra) |
| `tools` (`core/tools.py`) | tool registry and presence probing | internal |
| `proc` (`core/proc.py`) | robust command execution on Windows (`.cmd` shims) | internal |
| `render` / `menu` (`cli/`) | Rich-or-plain output and interactive menu | internal |

## External — orchestrated (not reimplemented)

Each is invoked as a **separate process** (CLI/MCP). That's why **their licenses don't constrain Tramalia's**. How to install and integrate each: [Integrations](interop.md).

### Bootstrap

The **base you install by hand first** (they can't install themselves); the rest is brought by `mise install`. See [Glossary](glosario.md).

| Tool | Role / scope | Runtime | License |
|---|---|---|---|
| **mise** | tool versions + environment + gates runner | binary (Rust) | MIT |
| **git** | versioning of memory, skills, evidence | binary | GPL-2.0 |
| **uv** | installs Python tools (copier, serena…) | binary (Rust) | MIT / Apache-2.0 |

### Structure and rules

| Tool | Role / scope | Runtime | License |
|---|---|---|---|
| **copier** | scaffolding with `update` (future) | Python | MIT |
| **rulesync** | fan-out of `AGENTS.md` to other agents | Node | MIT |
| **Spec Kit** | spec-driven development (`specify`, detected by doctor) | Python | MIT |
| **Ponytail** | minimalism ruleset + its own MCP (via `tramalia skills`) | Node (MCP) | see repo |

### Context / code intelligence

| Tool | Role / scope | Runtime | License |
|---|---|---|---|
| **Repomix** | packaged repo snapshot for AI | Node | MIT |
| **Serena** | semantic navigation/editing (LSP, MCP) | Python | MIT |
| **codebase-memory-mcp** | structural code graph (158 languages) | binary (C/C++) | see repo |
| **CodeGraph** | pre-indexed graph with auto-sync (CLI + MCP) | binary | see repo |

### Security and database (gates)

| Tool | Role / scope | Runtime | License |
|---|---|---|---|
| **Semgrep** (CE) | SAST (security gate) | Python | **LGPL-2.1** |
| **Gitleaks** | secret scanning (security gate) | binary (Go) | MIT |
| **SQLFluff** | SQL lint (database gate) | Python | MIT |

### UX/UI (gates)

| Tool | Role / scope | Runtime | License |
|---|---|---|---|
| **Lighthouse CI** | performance + a11y + best practices | Node | Apache-2.0 |
| **Playwright** | visual regression + e2e | Node | Apache-2.0 |
| **axe-core** | accessibility | Node | **MPL-2.0** |
| **pa11y** | accessibility | Node | **LGPL-3.0** |
| **Storybook** | component states | Node | MIT |

### Memory and efficiency (optional interop)

| Tool | Role / scope | Runtime | License |
|---|---|---|---|
| **Engram** | N2 persistent memory across sessions | binary (Go) | see repo |
| **basic-memory / mem0** | alternative persistent memory | Python | see repo |
| **Headroom** | context/output compression (token-saver) | Python/Node | see repo |

### Tramalia's Python dependencies (the only ones installed/imported)

| Package | Use | License |
|---|---|---|
| **rich** | colored/table output (included by default) | MIT |
| **questionary** | interactive menus (included by default) | MIT |
| **mcp** | MCP façade SDK (auto-offered by `tramalia mcp` · `[full]`) | MIT |
| **textual** | TUI dashboard (auto-offered by `tramalia ui` · `[full]`) | MIT |
| **pytest** | tests (extra `dev`) | MIT |
| mkdocs-material · mkdocs-static-i18n | only to build this documentation | MIT |

!!! note "The key point"
    The **copyleft** ones in the list (Semgrep LGPL-2.1, pa11y LGPL-3.0, axe MPL-2.0, git GPL-2.0) are tools that Tramalia **invokes**, not links or redistributes. They don't affect Tramalia's license. The only ones that count —the Python dependencies— are **all MIT**.
