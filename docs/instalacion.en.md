# Installation & requirements

## To run Tramalia: only Python, one command

Tramalia **only requires Python 3.10+**. It has no Node dependencies.

```bash
pip install tramalia-cli
```

That's it: it includes the CLI with colors and interactive menu (Rich + Questionary, pure-Python and tiny). The two heavier optional pieces — the **TUI dashboard** (`tramalia ui`) and the **MCP façade** (`tramalia mcp`) — **offer to install themselves the first time you use them**:

```text
$ tramalia ui
▲ the TUI dashboard requires 'textual' (not installed).
? install 'textual' now? [Y/n]
```

!!! note "For experts"
    If you'd rather get everything upfront: `pip install "tramalia-cli[full]"` (adds Textual + MCP SDK).
    In managed environments (Ubuntu 23+, Homebrew, pipx) where direct pip is blocked,
    the auto-offer will show you the manual command (`pipx inject tramalia-cli textual`).

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
| rich · questionary | interactive, colorful CLI | Python | **included by default** |
| semgrep · gitleaks | security gate | Python/binary | optional |
| sqlfluff | database gate | Python | optional |
| **repomix** | context snapshot | **Node** | optional |
| **rulesync** | rule fan-out (`sync`) | **Node** | optional |
| **lighthouse · playwright** | UX/UI gate | **Node** | optional |
| **engram** | N2 persistent memory (`--engram`) | binary | optional (interop) |
| **headroom** | context/output compression (token-saver) | — | optional (interop) |
| **specify** (Spec Kit) | spec-driven development (`specs/`) | Python | optional (interop) |
| **ponytail** | minimalism ruleset + MCP (`--with-ponytail`) | **Node** (MCP) | optional (interop) |
| **markitdown** | ingestion: PDF/Office/images → Markdown (context) | Python | optional (interop) |
| **databricks CLI** | `bundle validate` in analytics projects | binary | only if `databricks.yml` is detected |

!!! tip "Want the interface in a specific language?"
    The interface (`tramalia ui` and the CLI) detects your language automatically (system locale). To force it: `TRAMALIA_LANG=en` or `"language": "en"` in `.tramalia/config.json`. See [The interface (TUI)](interfaz.md#language).

!!! tip "Do I need Node?"
    Only if you use `sync`, the `ux` gate, or `context` with Repomix. In a project with no frontend and no `sync`, you **never** need Node. `tramalia doctor` flags those rows as "requires Node".

!!! tip "Node and Go can be installed FOR you"
    If a tool only automates with a runtime you're missing (npm → **Node**; `go install` → **Go**, e.g. engram), the install selector (`i` key in the TUI, or `doctor --fix`) **offers to install that runtime first** — install it, run the install again, and the tool becomes automatable. Node and Go are installable via winget/brew like everything else. Detail: [Help → runtime prerequisites](ayuda.md#installation-doctor).

## Automated installation per system

`tramalia doctor --fix` (and the `i` key in `tramalia ui`) **detect your OS and which managers you have** (winget/brew/choco/scoop, mise, uv, npm) and let you **select one or more** tools to install automatically — each through its best available route:

| Tool | Windows | macOS | Linux |
|---|---|---|---|
| **mise** | `winget install jdx.mise` ✓ verified | `brew install mise` | `curl https://mise.run \| sh` (manual) |
| **git** | `winget install Git.Git` | `brew install git` | your distro's manager |
| **uv** | `winget install astral-sh.uv` | `brew install uv` | official script (manual) |
| **node** | `winget install OpenJS.NodeJS.LTS` | `brew install node` | `mise use node@22` |
| gates/features | via **mise** if present; else **uv** (`pipx:`) or **npm** (`npm:`, only with Node present) | same | same |

Installer rules: `curl | sh` is **never** run automatically (display only); **npm** options only appear when Node/npm is present (checker included); on Windows, for mise **winget is the verified route** — choco and scoop are listed as manual alternatives.

!!! note "Installed via mise but doctor doesn't see it"
    Tools installed by mise live behind its **shims**: until you activate mise (`mise activate` in your shell) or restart the terminal, they're not on PATH. `doctor` now detects them anyway (it queries `mise which`) and tells you: *"installed via mise (shims)"*.

## Recommended order

```bash
pip install tramalia-cli                 # 1. Tramalia
tramalia init                            # 2. generate the convention
tramalia doctor --fix                    # 3. select and install what's missing
mise use node@22                         # 4. only if you'll use sync / ux / repomix
tramalia doctor                          # 5. verify nothing is missing
```

## Updating

- **Tramalia (the CLI):** `pip install -U tramalia-cli` — the install command with `-U`. Verify with `tramalia --version`.
- **What Tramalia orchestrates** (mise tools + external skills): `tramalia update`. They're different things: `update` doesn't touch the package itself.
