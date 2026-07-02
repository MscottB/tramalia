# Command reference

The **governance core** (`init`, `doctor`, `close`, `log`, `evidence`, `handoff`) is own logic and works **standalone, with Python only**. The rest does a transparent *shell-out* to external tools (optional interop) and shows their output without hiding errors.

| Command | What it does | Type |
|---|---|---|
| `tramalia menu` | **looping** interactive menu with guided prompts | core |
| `tramalia ui` | **TUI dashboard** (Overview · Audit · Close) | core (+ `[tui]` extra) |
| `tramalia init [--with-headroom --with-ponytail]` | generate the full convention (idempotent) | core |
| `tramalia doctor [--fix]` | diagnose tools and how to install them | core |
| `tramalia detect` | detect the stack and applicable gates | core |
| **`tramalia close [--task --agent --reviewer --allow-fail --engram]`** | **closing ritual: gates → evidence → handoff (enforcement)** | **core ★** |
| **`tramalia log`** | **audit trail of closes** | **core ★** |
| `tramalia evidence [--task --engram]` | create the closing evidence pack | core |
| `tramalia handoff [--task --agent --reviewer --engram]` | multi-agent handoff | core |
| `tramalia gates` | run the quality gates | interop (mise) |
| `tramalia context` | generate derived memory (token-saver) | interop (repomix + stdlib) |
| `tramalia sync [--to ...]` | propagate AGENTS.md to other agents | interop (rulesync) |
| `tramalia skills [sync\|list]` | clone/update skills from their repos | interop (git) |
| `tramalia update` | update everything | interop (mise + copier + skills) |
| `tramalia mcp` | start the MCP façade | core (+ mcp SDK) |

## close — the governance ritual

The flagship command. In one step: it runs each gate (`mise run <gate>`), **writes their output into the evidence pack**, generates the handoff, and **blocks the close if a gate fails** (unless you pass `--allow-fail` with the exception noted in `risks.md`).

```bash
tramalia close --task TASK-001 --agent codex --reviewer claude
```

It works **standalone**: if `mise` is missing, it does not invent a result — it records in the pack that the gates did not run as a **documented exception**, and still leaves evidence + handoff.

Each close writes **`metadata.json`** (task, agent, reviewer, timestamps, exit codes and an honest `status`: `passed` / `blocked` / `passed_with_exceptions` / `no_gates`). The raw `*-output.txt` files are the official evidence; no derived artifact (e.g. Headroom compression) may replace them.

## log — the audit trail

Reads each close's `metadata.json` and lists the closes (newest first) with their `status` and agent. It's the verifiable history of agentic work on the repo.

## doctor

Classifies requirements into **bootstrap** (mise/git/uv), **stack** (node/dotnet…) and **feature/gate** (semgrep/sqlfluff/lighthouse…), bothering you only with what applies to your project. `--fix` delegates to `mise install` when mise is present.

## init

Generates idempotently (never overwrites existing files): a single `AGENTS.md`, `CLAUDE.md` (`@AGENTS.md`), the **full `docs/ai/` 00–11**, **`specs/`** (constitution/specification/plan/tasks/checklist, integrated with `close`), **13 numbered skills** in `.tramalia/skills/`, a stack-tailored `mise.toml`, `.mcp.json` with Serena, and `.tramalia/` (config, current-task, skills.toml).

Opt-in flags: `--with-headroom` (compression) and `--with-ponytail` (the minimalism ruleset's MCP; requires `tramalia skills` + Node).

## ui — the TUI dashboard

`tramalia ui` opens a terminal panel (Textual, extra `pip install "tramalia-cli[tui]"`) with three views: **Overview** (live doctor + applicable gates), **Audit** (the closes from `log`, browsable; Enter shows the `metadata.json`) and **Close** (task/agent/reviewer form + gates output). It only reads and invokes the core — zero new logic.

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
