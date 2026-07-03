# Installation & requirements

## To run Tramalia: only Python

Tramalia **only requires Python 3.10+**. It has no Node dependencies.

```bash
pip install tramalia-cli                    # base (basic terminal, stdlib only)
pip install "tramalia-cli[pretty]"          # pretty mode: Rich + Questionary (recommended)
pip install "tramalia-cli[tui]"             # TUI dashboard (tramalia ui, Textual)
pip install "tramalia-cli[mcp]"             # MCP façade
pip install "tramalia-cli[pretty,tui,mcp]"  # everything together
```

!!! info "Contributing to the project?"
    Clone the repo and install in editable mode: `pip install -e ".[dev]"`. See the
    [contributing guide](https://github.com/MscottB/tramalia/blob/main/CONTRIBUTING.md).

## For a good experience: external tools

Tramalia **orchestrates** external tools. You don't need them all to start; `tramalia doctor` tells you which are missing for *your* project. Important: **some are Node**, not Python.

| Tool | What for | Runtime | Required? |
|---|---|---|---|
| **Python 3.10+** | run Tramalia | — | **yes** |
| **mise** | installs/versions the rest + runs gates | binary | recommended |
| **git** | versioned memory, skills, evidence | binary | recommended |
| **uv** | installs Python tools (copier, serena) | binary | recommended |
| **Node 18+** | `sync`, `ux` gate, `context` (repomix) | — | if you use those features |
| rich · questionary | interactive, colorful CLI | Python | optional |
| semgrep · gitleaks | security gate | Python/binary | optional |
| sqlfluff | database gate | Python | optional |
| **repomix** | context snapshot | **Node** | optional |
| **rulesync** | rule fan-out (`sync`) | **Node** | optional |
| **lighthouse · playwright** | UX/UI gate | **Node** | optional |
| **engram** | N2 persistent memory (`--engram`) | binary | optional (interop) |
| **headroom** | context/output compression (token-saver) | — | optional (interop) |
| **specify** (Spec Kit) | spec-driven development (`specs/`) | Python | optional (interop) |
| **ponytail** | minimalism ruleset + MCP (`--with-ponytail`) | **Node** (MCP) | optional (interop) |

!!! tip "Do I need Node?"
    Only if you use `sync`, the `ux` gate, or `context` with Repomix. In a project with no frontend and no `sync`, you **never** need Node. `tramalia doctor` flags those rows as "requires Node".

## Recommended order

```bash
pip install "tramalia-cli[pretty,mcp]"   # 1. Tramalia
# 2. Install mise, git, uv (bootstrap; doctor gives you the link)
tramalia init                            # 3. generate the convention
mise install                             #    mise installs what's declared
mise use node@22                         # 4. only if you'll use sync / ux / repomix
tramalia doctor                          # 5. verify nothing is missing
```
