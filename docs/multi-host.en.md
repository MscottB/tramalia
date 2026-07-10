# Models and effort per host

Tramalia is **host-neutral**: the convention (standard `AGENTS.md`), the fan-out (`sync`) and the audit (`close --agent/--model` records any combination) work the same with any agent. But **each host controls model and effort its own way** — here's the matrix:

```mermaid
flowchart LR
    classDef s fill:#5b4bdb,stroke:#8c68d9,color:#ffffff;
    A["AGENTS.md<br/><small>single source</small>"]:::s -->|tramalia sync| B["Claude Code · Codex<br/>Antigravity · Hermes · OpenClaw…"]:::s
    B -->|each with its own model/effort| C["tramalia close --agent --model"]:::s
    C --> D["metadata.json + log<br/><small>unified audit</small>"]:::s
```

| Host | Reads AGENTS.md | Model selection | Effort / reasoning | Subagents with model |
|---|---|---|---|---|
| **Claude Code** (CLI/app) | ✅ native | `/model`, `opusplan` (Opus plans, Sonnet executes) | `ultrathink` (one turn) · `/effort ultracode` (session + auto-orchestration) | ✅ native (`.claude/agents/`, Tramalia's 5) |
| **Codex** (CLI/app) | ✅ native | `/model` + **profiles** in `config.toml` (`codex --profile`) | `model_reasoning_effort`: minimal → high, per profile | simulated via rulesync |
| **Antigravity** (CLI/IDE, absorbing Gemini CLI) | ✅ | per-session selector | model's thinking budget | `antigravity-cli` / `antigravity-ide` targets in rulesync |
| **Hermes** | via rulesync (`hermesagent` target) | gateway profile | API params per request | converted |
| **OpenClaw** and multi-model API gateways | AGENTS.md is plain Markdown: they read it if their config points to it | gateway profiles / API keys | `reasoning_effort` / thinking budget per request | manual |

!!! tip "Which agents do you have installed?"
    `tramalia doctor` (and the Overview tab of `tramalia ui`) now **detects the agent CLIs present** on your machine — claude, codex, antigravity, opencode, openclaw, hermes — with their version. Detection only: configuring them remains each agent's (or Gentle-AI's) territory.

## Desktop apps & IDEs

Everything above applies **equally** to the apps: Claude Code desktop uses the same engine as its CLI (reads `AGENTS.md`, `.mcp.json`, `.claude/agents/` and runs shell → `tramalia close` works identically); Codex desktop and Antigravity IDE read `AGENTS.md` natively and receive rules via `sync`. For GUIs without shell, the universal route is the **MCP façade** (`tramalia mcp`). That's the repo-first design paying off: governance lives in the repo, not in the host.

## The strategy in practice

1. **One source**: the rules live in `AGENTS.md`; the roles with model routing in `.claude/agents/`. `tramalia sync` propagates them to the other hosts.
2. **Each host applies its mechanism**: in Claude Code per-role routing is native; in Codex you use profiles (`--profile deep` with high effort for planning, a normal profile for execution); in Antigravity you select per session.
3. **The audit unifies**: whatever the host — `tramalia close --agent codex --model gpt-5.2-high` records in `metadata.json` *who* and *with what* closed. `tramalia log` shows the mixed history across all hosts.

## Cross-provider review

[codex-plugin-cc](https://github.com/openai/codex-plugin-cc) (official from OpenAI) brings Codex **inside** Claude Code:

```text
/plugin marketplace add openai/codex-plugin-cc
/codex:review      # Codex reviews your current work
/codex:transfer    # continue the session in Codex with the same context
```

It fits directly with Tramalia's `revisor` role: **two models from different providers reviewing the same evidence pack**, with both verdicts recorded in the handoff.

### Recipe: plan with Claude, execute with Codex

1. You plan in Claude Code (the `planificador` subagent) → the plan lands in `specs/tasks.md`.
2. `/codex:transfer` moves the session to Codex with the same context.
3. You execute the task in Codex.
4. You close with `tramalia close --agent codex --model <the-one-you-used>` — the audit
   records the cross-provider handoff; `tramalia log` shows the mixed history.

It's a **human workflow** (plugins are invoked from the conversation, not from a
subagent definition); Tramalia governs it at the close, it doesn't automate it.

## Model cap, portable across providers

The 5 subagents `init` generates ship with per-role routing (planner/reviewer →
opus, executor → inherit, documenter → haiku, deep-solver → fable). But maybe you
**don't have access to opus/fable**, or want to cut cost. The optional cap —
`tramalia agents cap <level>` — makes **no role use a model above the cap**;
anything below is kept. Example with cap `sonnet`:

| Role | No cap | Cap `sonnet` |
|---|---|---|
| planner | opus | **sonnet** |
| reviewer | opus | **sonnet** |
| deep-solver | fable | **sonnet** |
| documenter | haiku | haiku (already below) |
| executor | inherit | inherit (follows your session) |

Capability ranking: **fable > opus > sonnet > haiku**. Default: `none` (no cap, full
routing). Set it with `tramalia agents cap sonnet` or `init --model-cap sonnet`, saved
in `.tramalia/config.json → agents.model_cap`.

**How it applies per host** (enforcement where possible, convention where not):

| Host | How it receives the cap |
|---|---|
| **Claude Code** (CLI and app) | **Applied**: Tramalia rewrites the `model:` in `.claude/agents/` |
| **Codex** (CLI and app) | **Convention**: the `AGENTS.md` rule tells it to respect the cap when choosing profile/model — Tramalia does **not** write its `~/.codex/config.toml` |
| **Antigravity `agy`** | Convention, same (model per session) |
| **OpenClaw / Hermes / gateways / others** | Convention — they read plain `AGENTS.md`, so even hosts not yet contemplated are covered |

Since we don't write third-party configs (the Gentle-AI boundary), `agents cap`
**prints the equivalence by capability level** for you (or Gentle-AI) to paste:

```text
cap sonnet → standard level
  Codex: standard profile (model_reasoning_effort = medium)
  Antigravity (agy): standard model (not the deep-reasoning one)
```

It's expressed by **capability level**, not by third-party model name (which changes
often) — so services that don't exist yet map on their own.

!!! tip "The 5 agent files are yours"
    `.claude/agents/*.md` are hand-editable; `tramalia init` is idempotent and
    **never overwrites them**. `agents cap` only manages the `model:` line; the rest is yours.

## Effort equivalences (cheat sheet)

| You want… | Claude Code | Codex CLI |
|---|---|---|
| reason harder on THIS problem | `ultrathink` in the prompt | profile with `model_reasoning_effort = "high"` |
| whole session at max | `/effort ultracode` | `codex --profile deep` |
| plan expensive / execute cheap | `/model opusplan` or subagents | two profiles (plan/exec) |
| record what was used | `tramalia close --model <m>` | `tramalia close --model <m>` |
