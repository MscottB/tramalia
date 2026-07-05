# Full example: a real project, step by step

This is the journey of a fictional but realistic project — **`clinica-web`** (Angular + .NET + PostgreSQL) — showing **what Tramalia does to the project** with each of its own options and what **each third-party tool** contributes along the way.

## Day 0 · Install and govern the repo

```bash
cd clinica-web
pip install tramalia-cli     # Python 3.10+ only (the TUI auto-offers itself on `tramalia ui`)
tramalia init
```

`init` detects the stack (`node · angular · dotnet · postgres`) and drops **37 files**. What changes in your project, piece by piece:

| What appears | Effect on the project |
|---|---|
| `AGENTS.md` | **All** agents (Claude, Codex, Cursor…) read the same rules: reading order, Ponytail/YAGNI, prohibitions, closing with `close` |
| `CLAUDE.md` (`@AGENTS.md`) | Claude Code aligned without duplicating rules |
| `docs/ai/00–11` | The project's memory: architecture, code/DB/security/UX rules, ADR, **failed attempts**, handoff |
| `specs/` | Every feature is born as a task with an ID in `tasks.md`, with `Estado` and `Horizonte` (now·next·later) — that ID is what `close` audits |
| `.tramalia/skills/01…13` | 13 workflows telling the agent *how work is done here* |
| `.claude/agents/` | **5 subagents with model routing**: planner→opus, executor→inherit, reviewer→opus, documenter→haiku, deep-solver→fable |
| `mise.toml` | The detected stack's gates: `ng build`, `dotnet test`, `sqlfluff`, `semgrep`, `lhci`… |
| `.mcp.json` | Serena wired (semantic navigation); Engram if installed |

```bash
tramalia doctor      # what's missing and how to install it
mise install         # ← mise (3rd-party) installs EVERYTHING declared: repomix, semgrep, sqlfluff…
```

**Third-party tools already acting:** `mise` installs and versions the toolchain; `git` versions the memory.

## Day 0.5 · Propagate to all agents

```bash
tramalia sync
```

Two **rulesync** (3rd-party) passes: the rules (`AGENTS.md` → `.cursor/rules/`, `.github/copilot-instructions.md`, `.clinerules/`) and **the 5 subagents** (→ 15 files converted for Copilot/Cursor/Cline). Effect: no matter which agent opens the repo — same rules, same roles.

## Day 1 · A full feature: TASK-001

**Request:** "patient registration: table, endpoint and screen".

### 1. Plan (subagent `planificador` → Opus)

In Claude Code you ask *"plan the patient registration"*. The main model delegates to the **planner** (runs on Opus even if your session is on Sonnet), which applies the `01-spec-governance` skill and leaves in `specs/tasks.md`:

```markdown
## TASK-001 — Patient registration
- Applicable gates: build · test · lint · security · database · ux
- Acceptance criteria: patient creation with valid ID…
```

### 2. Implement (subagent `ejecutor` → inherit: your model)

The executor works with third-party help, without wasting context:

- **Serena** (MCP): reads *only* the `PacienteController` symbol it's about to touch — not the whole file.
- **Repomix** via `tramalia context`: refreshes `project-map.md` and `tech-stack.md`.
- Before inventing, it reads `docs/ai/06-intentos-fallidos.md` (what was already discarded lives here).

### 3. Close with enforcement

```bash
tramalia close TASK-001 --model sonnet   # agent and reviewer come from config.json
```

And here **all the third-party gates act at once** (via mise):

| Gate | Tool (3rd-party) | What it validates in clinica-web |
|---|---|---|
| build | ng + dotnet | front and back compile |
| test | ng test + dotnet test | the patient logic |
| lint | eslint + dotnet format | style |
| security | **Semgrep + Gitleaks** | unvalidated inputs, leaked secrets |
| database | **SQLFluff** | the `create table pacientes` migration (PK? rollback?) |
| ux | **Lighthouse + Playwright + axe** | the screen's accessibility and performance |

Suppose SQLFluff finds a problem:

```text
✗ gate database: FAILS
✗ close BLOCKED by failing gates: database.
```

**That's the governance**: the task *cannot* be declared done. The executor fixes the migration and retries — now everything passes and the **evidence pack** remains:

```text
.tramalia/evidence/2026-07-03-1015-TASK-001/
├── metadata.json         ← task, agent, MODEL (sonnet), gates, status: passed
├── database-output.txt   ← RAW SQLFluff output (official, immutable)
├── security-output.txt   ← RAW Semgrep/Gitleaks output
└── … build/test/lint/ux + risks + rollback + next-steps
```

…and the **handoff** in `docs/ai/07` is linked to the pack.

### 4. Review (subagent `revisor` → Opus) and audit

The reviewer reads the pack (raw + metadata) and records its verdict. You look at the history:

```bash
tramalia log
✓ 2026-07-03-1015-TASK-001  ·  ✓ passed  ·  claude-code (sonnet)
```

Or in the **dashboard**: `tramalia ui` → Audit tab; Enter on the close shows its `metadata.json`.

!!! note "If TASK-001 is closed before `init`"
    `close` **blocks (exit 1)** with a clear message — there's no convention to govern. This applies the same in the CLI and the TUI (Close tab shows "⚙ Initialize now"). See [Architecture → the initialization invariant](arquitectura.md#the-initialization-invariant).

## Optional extras (when you want them)

| You enable | Tool (3rd-party) | Effect on the project |
|---|---|---|
| `close --engram` | **Engram** | the close persists in cross-session memory (N2) |
| `init --with-headroom` | **Headroom** | compresses context/outputs for agents — **never** the raw evidence |
| `tramalia skills` + `init --with-ponytail` | **Ponytail** | clones its ruleset to `.tramalia/skills/ponytail/` and wires its MCP (`ponytail_instructions`) |
| `/speckit.specify` | **Spec Kit** | supercharges the `specs/` folder Tramalia already generated (doctor detects it) |
| query MCP server | **codebase-memory-mcp** / **CodeGraph** | structural code graph as context backend (install with `--skip-config`) — [criterion for which one](interop-contexto.md#the-criterion-which-to-mount-and-which-to-use) |
| `markitdown requirements.docx -o docs/ai/09-*.md` | **markitdown** | ingests the PRD or manual in `.docx`/`.pdf` into Markdown context |

## Before and after

| Without Tramalia | With Tramalia |
|---|---|
| Each agent with its own rules; context lost between sessions | One versioned convention everyone reads; typed handoff |
| "It works" — no proof | `close` blocks without green gates; raw evidence + `metadata.json` |
| Who did this and with what? | `log`: task · agent · **model** · honest status |
| 10 loose tools to learn one by one | `doctor` diagnoses them, `mise` installs them, Tramalia orchestrates them |

!!! tip "To reproduce it"
    Everything above works in any repo: `pip install tramalia-cli`, `tramalia init`, `tramalia doctor` — and from there the [Full workflow](flujo-completo.md).
