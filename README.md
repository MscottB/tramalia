<div align="center">

# 🧩 Tramalia

**Governance and verifiable evidence for building with multiple AI agents. Repo-first.**

*Define the project rules, orchestrate collaboration between agents, validate every change, and leave a verifiable record — versioned in the repo.*

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)
![Tests](https://img.shields.io/badge/tests-171%20passing-brightgreen.svg)

[Español](README.es.md) · **English** · [📚 Docs](https://MscottB.github.io/tramalia/)

</div>

---

> **Git governs human collaboration; Tramalia governs agentic collaboration.** It's the change control + audit trail for when several AI agents work on a real project: shared rules, mandatory validations, and verifiable evidence for every close.

## Table of contents

- [What is it?](#what-is-it)
- [Definition](#definition)
- [Features](#features)
- [Quick start](#quick-start)
- [Usage](#usage)
- [Tramalia alone or with your tools](#tramalia-alone-or-with-your-tools)
- [How it works](#how-it-works)
- [Comparison with the ecosystem](#comparison-with-the-ecosystem)
- [Requirements](#requirements)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## What is it?

When you work on a project with several AI agents (Claude Code, Codex, Cursor, Antigravity…), each one loses context between sessions, uses its own rules, and **leaves no evidence of what it did**. Tramalia fixes this by using **the repository as the source of truth**: it drops a versioned convention that *any* agent reads, and ensures the work is done in a **controlled, traceable and consistent** way.

Its focus is **not** to configure your agents (that's Gentle-AI and the like) nor to be a memory engine (that's Engram). Its focus is to **govern the repo**: rules, gates, evidence and handoff.

## Definition

> **Tramalia is a repo-first governance and evidence layer for development with multiple AI agents.** Its goal is not to configure agents nor to replace memory engines, but to ensure that any agent touching a project works under the same rules, runs validations, documents its decisions, leaves verifiable evidence, and hands off clearly to the next session or reviewer.

It does this by **orchestrating external tools** instead of reimplementing them.

## Features

- **Governed close (`close`)** — runs the gates, writes their output into the **evidence pack** and generates the (linked) **handoff** in one step; **blocks the close if a gate fails** (unless a documented exception).
- **Audit trail (`log`)** — verifiable history of closes: which task, which gates passed, what evidence.
- **TUI dashboard (`ui`)** — terminal panel with Overview, browsable Audit and guided Close (extra `[tui]`, Textual).
- **Quality gates** — build, test, lint, security, database and UX/UI.
- **Complete convention** — single `AGENTS.md` + `docs/ai/` 00–11 + `specs/` + **13 numbered skills** anchored to the workflow + failed attempts + typed handoff.
- **Role-based subagents with model routing** — `.claude/agents/` ships 5 governance roles (planner→opus, executor→inherit, reviewer→opus, documenter→haiku, deep-solver→fable); `sync` fans them out to other hosts, and `close --model` records which model closed each task.
- **`doctor`** — diagnoses which tools *your* project needs and how to install them (includes Spec Kit).
- **Token saving** *(interop)* — derived context (Repomix) + semantic navigation (Serena).
- **Rule fan-out** *(interop)* — propagates `AGENTS.md` to Cursor/Copilot/… with rulesync.
- **MCP façade** + **optional N2 memory** (Engram) — exposes/persists without reinventing.

## Quick start

```bash
pip install tramalia-cli    # only requires Python 3.10+ — one command, everything included
tramalia init                        # generate the convention in your repo
tramalia doctor                      # tells you what else to install
```

## Usage

Commands are designed to be short: `close` takes the task as a positional argument, and agent/reviewer default from `.tramalia/config.json` (`agents.primary`/`agents.reviewer`). If you omit the task, it's read from `.tramalia/current-task.md` — so the everyday close is just **two words**.

| Command | What it does | Simple example |
|---|---|---|
| `menu` | looping interactive menu with guided prompts | `tramalia menu` |
| `ui` | TUI dashboard: Overview · Audit · Close (extra `[tui]`) | `tramalia ui` |
| `init` | generate the full convention (AGENTS.md, docs/ai 00-11, specs, 13 skills, 5 subagents) | `tramalia init` |
| `doctor` | diagnose which tools are missing and how to install them | `tramalia doctor` |
| `detect` | detect the stack and applicable gates | `tramalia detect` |
| **`close`** | **close a task: gates → evidence → handoff, with enforcement** | `tramalia close` · `tramalia close TASK-001` |
| `log` | audit trail: task · agent · model · honest status | `tramalia log` |
| `evidence` | create just the evidence pack | `tramalia evidence TASK-001` |
| `handoff` | append just the handover entry | `tramalia handoff TASK-001` |
| `gates` | run the quality gates (via mise) | `tramalia gates` |
| `context` | refresh derived context (token saving) | `tramalia context` |
| `sync` | propagate rules **and subagents** to other hosts (rulesync) | `tramalia sync` |
| `skills` | clone/update referenced skills from their repos | `tramalia skills` |
| `update` | update everything (mise + skills) | `tramalia update` |
| `mcp` | start the MCP façade (extra `[mcp]`) | `tramalia mcp` |

Advanced flags (overrides): `close --task --agent --reviewer --model --allow-fail --engram` · `init --with-headroom --with-ponytail` · `sync --to --features`. Full reference: [Commands](docs/comandos.md).

## Tramalia alone or with your tools

The **governance core works standalone**, with Python only: `init`, `doctor`, `close`, `log`, `evidence`, `handoff` and the rules/`docs/ai`. It needs nothing else to govern the repo.

External tools are **optional interoperability**, not requirements: `mise` (runs the gates), Repomix/Serena/codebase-memory-mcp (context), rulesync (fan-out), **Engram** (N2 memory), **Headroom** (compression). If they're missing, Tramalia still governs and records it as a documented exception.

## How it works

Three layers:

1. **The thin CLI** (what you run) — a single face that shells out to the real tools.
2. **The convention** (what stays in your repo) — `AGENTS.md`, `docs/ai/`, `mise.toml`… The real value.
3. **The external tools** (updated from their repos) — mise, Serena, Repomix, Semgrep, rulesync, the agents.

## Comparison with the ecosystem

They don't compete head-on; they complement each other. Each occupies a different space:

| Project | Role |
|---|---|
| **Gentle-AI** | prepares the agent ecosystem: models, skills, memory, profiles, config |
| **Engram** | provides persistent memory across sessions |
| **Headroom** | compresses context and outputs to save tokens |
| **Serena · Repomix · codebase-memory-mcp** | code intelligence / context (navigation, snapshot, structural graph) |
| **Tramalia** | **governs the work inside the repo: rules, gates, evidence, handoff, audit and failed attempts** |

Together: **Gentle-AI** enables *which* agents to work with, **Engram** helps *remember*, **Headroom** makes context *cheaper*, **Serena/Repomix/codebase-memory-mcp** provide *code intelligence*, and **Tramalia** keeps the repo **controlled, traceable and consistent**. All are optional interop; none touch Tramalia's core (`close`, `log`, evidence pack, handoff). Details in the [ecosystem page](docs/ecosistema.md).

## Requirements

- **Tramalia: only Python 3.10+** (no Node dependencies).
- **Recommended:** `mise`, `git`, `uv` (bootstrap that installs the rest).
- **Node 18+** only if you use `sync`, the `ux` gate, or `context` with Repomix. `tramalia doctor` flags it as "requires Node".

## Documentation

- **Site (ES/EN):** https://MscottB.github.io/tramalia/ — visual, with diagrams
  - **[Full example](docs/ejemplo-completo.md)** — a real project end to end, showing every option and every third-party tool in action
  - [Ecosystem](docs/ecosistema.md) · [Full workflow](docs/flujo-completo.md) · [Architecture](docs/arquitectura.md) · [Integrations](docs/interop.md) · [Tools](docs/herramientas.md)
- [User manual (Spanish)](MANUAL_DE_USUARIO.md)
- [Consolidated design document (Spanish)](Tramalia_Diseno_Consolidado_v0_6.md)

## Contributing

Contributions are welcome. Read the [contributing guide](CONTRIBUTING.md): open an issue to discuss large changes; for small ones, send a PR. Run the tests with `pip install -e ".[dev]" && pytest`.

## License

**Apache-2.0** © 2026 Michael Jim Scott Bravo — see [`LICENSE`](LICENSE). Ecosystem license analysis (and why the copyleft of external tools doesn't affect Tramalia): [`LICENSES.md`](LICENSES.md).
