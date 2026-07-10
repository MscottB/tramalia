# Command reference

The **governance core** (`init`, `doctor`, `close`, `log`, `evidence`, `handoff`) is own logic and works **standalone, with Python only**. The rest does a transparent *shell-out* to external tools (optional interop) and shows their output without hiding errors.

| Command | What it does | Type |
|---|---|---|
| `tramalia menu` | **looping** interactive menu with guided prompts | core |
| `tramalia ui` | **TUI dashboard** (Overview · Audit · Close) | core (+ `[tui]` extra) |
| `tramalia init [--with-headroom --with-ponytail]` | generate the full convention (idempotent) | core |
| `tramalia doctor [--fix]` | diagnose tools and how to install them | core |
| `tramalia detect` | detect the stack and applicable gates | core |
| **`tramalia close [TASK]`** | **closing ritual: gates → evidence → handoff (enforcement)** | **core ★** |
| **`tramalia log`** | **audit trail of closes** | **core ★** |
| `tramalia evidence [TASK]` | create the closing evidence pack | core |
| `tramalia handoff [TASK]` | multi-agent handoff | core |
| `tramalia gates` | run the quality gates | interop (mise) |
| `tramalia context [build\|list\|set <backend>]` | generate derived memory; view or set the active navigation backend | interop (repomix + stdlib) |
| `tramalia agents [list\|cap <level>]` | view or set the subagents' model cap | core |
| `tramalia sync [--to --features]` | propagate AGENTS.md **and subagents** to other agents | interop (rulesync) |
| `tramalia skills [sync [<n>]\|list\|outdated\|enable\|disable\|add]` | manage skills: catalog with states and version, update one or all, see which are outdated | interop (git) |
| `tramalia update` | update everything | interop (mise + copier + skills) |
| `tramalia mcp` | start the MCP façade | core (+ mcp SDK) |

## close — the governance ritual

The flagship command. In one step: it runs each gate (`mise run <gate>`), **writes their output into the evidence pack**, generates the handoff, and **blocks the close if a gate fails** (unless you pass `--allow-fail` with the exception noted in `risks.md`).

**Simple form — the everyday close is two words:**

```bash
tramalia close              # task from .tramalia/current-task.md; agents from config.json
tramalia close TASK-001     # explicit task (positional)
```

**Resolution chain** (each value is looked up in order):

| Value | 1st | 2nd | 3rd | 4th |
|---|---|---|---|---|
| task | positional | `--task` | ID in `.tramalia/current-task.md` | prompt if interactive; `TASK-000` in scripts |
| agent | `--agent` | `config.json → agents.primary` | — | — |
| reviewer | `--reviewer` | `config.json → agents.reviewer` | — | — |

Advanced flags (overrides): `--task · --agent · --reviewer · --model · --allow-fail · --engram`.

It works **standalone**: if `mise` is missing, it does not invent a result — it records in the pack that the gates did not run as a **documented exception**, and still leaves evidence + handoff.

Each close writes **`metadata.json`** (task, agent, reviewer, timestamps, exit codes and an honest `status`: `passed` / `blocked` / `passed_with_exceptions` / `no_gates`). The raw `*-output.txt` files are the official evidence; no derived artifact (e.g. Headroom compression) may replace them.

**Domain metrics (ML/analytics):** if `.tramalia/metrics.json` exists, `close` copies it raw into the pack and embeds it in `metadata.json`; if `.tramalia/thresholds.json` is also present, a violated threshold **blocks the close** like a failed gate. See [Analytics](analitica.md#metrics-and-thresholds-in-the-evidence-mlanalytics).

## log — the audit trail

Reads each close's `metadata.json` and lists the closes (newest first) with their `status` and agent. It's the verifiable history of agentic work on the repo.

## doctor

Classifies requirements and the table comes out **grouped by domain** — base (bootstrap) · stack · **context · memory · security · database · UX/UI · analytics** · convention · agent CLIs — bothering you only with what applies to your project. The status clearly says **installed or not** (`✓ installed` / `○ not installed (optional)` / `✗ not installed (required)`). Install hints are **per operating system** (winget/brew/choco…) and per available manager; it also warns if the uv PATH needs `uv tool update-shell`.

`--fix` builds the automated install plan (best route per tool: winget/brew, `mise use`, `uv tool`, `npm` only with Node), lets you **select one or more** before running, and configures the uv PATH if needed. In the TUI (`i` key), the selector shows **all** missing tools — the automatable ones selectable and the manual ones listed separately. Detail: [Installation](instalacion.md#automated-installation-per-system).

## init

Generates idempotently (never overwrites existing files): a single `AGENTS.md`, `CLAUDE.md` (`@AGENTS.md`), the **full `docs/ai/` 00–13** (incl. deploy & analytics), **`specs/`** (constitution/specification/plan/tasks/checklist, integrated with `close`), **16 numbered skills** in `.tramalia/skills/` (see [Skills](skills-guia.md)), **5 subagents with model routing** in `.claude/agents/` (see [Integrations → agents](interop-agentes.md)), a stack-tailored `mise.toml`, `.mcp.json` with Serena, and `.tramalia/` (config, current-task, skills.toml).

Opt-in flags: `--with-headroom` (compression) and `--with-ponytail` (the minimalism ruleset's MCP; requires `tramalia skills` + Node).

**`--adopt`** — for repos that **already have an agent**: it integrates governance into an existing `AGENTS.md`/`.mcp.json`/`CLAUDE.md` with a non-destructive marker-based merge instead of skipping them. Without `--adopt`, a normal `init` that detects an `AGENTS.md` without governance tells you how. Detail: [Adopting an existing repo](adopcion.md).

When it finishes, `init` records the version in `.tramalia/version` and — if it detects other agent CLIs installed — suggests `tramalia sync` to propagate your rules to their formats (see [`sync`](#sync) and [why only `.claude/` is generated](interop-agentes.md#why-init-only-generates-claude)).

## upgrade — update an already-initialized repo

When you update Tramalia (`pip install -U tramalia-cli`), your already-generated repos **don't change on their own**. `tramalia upgrade` brings them up to date **without overwriting your work**:

- **Adds** the new files that are missing (skills, `docs/ai/` pages, etc. that your version didn't have) and refreshes the `.gitignore` block.
- **Doesn't touch** any file that already exists — it never overwrites your edits.
- Records the version in `.tramalia/version` and reports the balance (`N new, M unchanged`), pointing to the CHANGELOG for template changes you may want to adopt by hand.

It's idempotent: run it after each CLI update. For a 3-way merge of edited content (`copier update` style) it'll lean on copier in the future; for now, template changes to files you edited are reviewed by hand with the CHANGELOG as a guide.

## ui — the TUI dashboard

`tramalia ui` opens a terminal panel (Textual; if missing, `tramalia ui` **offers to install it** right there) with four views: **Overview** (live doctor + applicable gates + context backend), **Skills** (manage own and external), **Audit** (the closes from `log`, browsable; Enter shows the `metadata.json`) and **Close** (task/agent/reviewer form + gates output). It only reads and invokes the core — zero new logic. Full interface guide: [The interface (TUI)](interfaz.md).

## agents

`tramalia agents list` shows the 5 subagents with their current model (and each role's default) plus the active cap. `tramalia agents cap <fable\|opus\|sonnet\|haiku\|none>` sets a **cap**: no role uses a model above it; anything below is kept (`inherit` untouched). It's saved in `.tramalia/config.json → agents.model_cap`, applied to the Claude Code frontmatters, and it prints the per-level equivalence for Codex/Antigravity (which Tramalia doesn't configure). Default `none`. Detail and per-host matrix: [Models & effort per host](multi-host.md#model-cap-portable-across-providers).

## context

`tramalia context` (no argument, or `build`) generates `.tramalia/context/` (project-map, tech-stack) — full snapshot if Repomix is present, stdlib tree otherwise. It also manages the project's **active code-navigation backend**:

- **`tramalia context list`** — the 4 options competing for that role (Serena, CodeGraph, codebase-memory-mcp, Graphify) with their scope, ideal use case, which is installed and which is active.
- **`tramalia context set <backend>`** — sets it in `.tramalia/config.json → context.backend` (default `serena`); also lands in `tools.json` so agents can read it.

Why it matters: with several installed, an agent alternating between them task to task leaves the indexes inconsistent. See [Context & code intelligence](interop-contexto.md#with-several-installed-which-does-the-agent-use-contextbackend).

## evidence and handoff

Tramalia's two own pieces for traceability:

- **`evidence`** creates `.tramalia/evidence/<date>-<task>/` with `summary`, `files-changed` (reads `git diff`), `commands`, each gate's output, `risks`, `rollback` and `next-steps`.
- **`handoff`** appends a structured entry to `docs/ai/07-handoff-agentes.md`.

## sync

`rulesync convert --from agentsmd --to copilot,cursor,cline --features rules`. It excludes Claude/Codex (they already read `AGENTS.md` natively). Configurable with `--to`.

## mcp — the façade (level 1)

Exposes the convention as native MCP tools: `project_status`, `get_agent_rules`, `get_failed_attempts`, `get_current_task`, `doctor`, `record_handoff`, `build_evidence`, `build_context`. Wire it in `.mcp.json`:

```json
{
  "mcpServers": {
    "tramalia": { "command": "tramalia", "args": ["mcp"] }
  }
}
```
