# Rules, skills & agents

How Tramalia propagates rules to multiple agents, scaffolding and spec-driven, and its relationship with AI agents and with external configurators like Gentle-AI.

## rulesync — rule fan-out

- **What it is / scope:** converts `AGENTS.md` to each agent's own format (Cursor, Copilot, Cline…), keeping **a single source**.
- **Requires:** **Node**.
- **Install:** `mise use npm:rulesync` · `npm i -g rulesync` · `npx rulesync`.
- **Tramalia uses it in:** `tramalia sync` → `rulesync convert --from agentsmd --to copilot,cursor,cline`.
- **Interacts with:** `AGENTS.md` (the single source). Avoids divergent copies across agents.

## copier — scaffolding with `update`

- **What it is / scope:** a project template engine; its superpower is `copier update` (re-applies template improvements without overwriting your work).
- **Requires:** Python (uv).
- **Install:** `uv tool install copier` · `pipx install copier`.
- **Tramalia uses it in:** `init` (the convention is copier-compatible) and, in the future, `update` → `copier update`.

## Spec Kit — spec-driven development (optional)

- **What it is / scope:** a toolkit for specification-driven development (constitution/spec/plan/tasks, `/speckit.*` slash-commands inside agents). **It has no MCP** (verified).
- **Requires:** Python (uv).
- **Install:** `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`.
- **Tramalia uses it in:** `doctor` detects the `specify` binary (feature `specs`, optional); it complements the `specs/` folder that `init` generates (tasks ↔ `close --task`, checklist ↔ evidence pack). Tramalia doesn't reimplement it.

## Ponytail — minimalism ruleset + its own MCP

- **What it is / scope:** the Ponytail principle (minimum necessary code) packaged as a skill/ruleset, **with its own MCP server** (`ponytail-mcp`): it exposes the `ponytail_instructions` tool and the `ponytail` prompt (lite/full/ultra modes).
- **Requires:** git (to clone it) and **Node** (for its MCP). Not on npm: used from its repo.
- **Install / wire (3 steps):**
  1. `tramalia skills` — clones it into `.tramalia/skills/ponytail/` (already declared in `skills.toml`).
  2. `npm install` inside `.tramalia/skills/ponytail/ponytail-mcp/`.
  3. `tramalia init --with-ponytail` — adds its server to `.mcp.json` (`node …/ponytail-mcp/index.js`).
- **Tramalia uses it in:** the principle already ships as a rule in `AGENTS.md` and as the `04-minimalist-engineering` skill; the full cloned ruleset stays readable for agents, and the MCP is the optional native path.
- **Interacts with:** all agents (same ruleset on any host); reinforces the quality gate.

## Gentle-AI — agent setup/onboarding (external)

- **What it is / scope:** configures *which* agents you work with (models, skills, profiles, memory, MCP). It's a "bootstrap" of your AI workstation.
- **Requires:** see its repo (Go).
- **Install:** per its official documentation.
- **Relationship with Tramalia:** **external onboarding, NOT core.** Gentle-AI gets your machine ready; Tramalia governs what those agents do *inside the repo*. They're used separately to avoid double ownership of configs/prompts.

## Role-based subagents with model routing

`tramalia init` generates `.claude/agents/` with **5 governance roles** that Claude Code reads natively; each declares its `model:` in the frontmatter:

| Agent | `model:` | Anchored to |
|---|---|---|
| `planificador` (planner) | opus | `specs/` + skill 01-spec-governance |
| `ejecutor` (executor) | **inherit** (respects YOUR app selection) | `specs/tasks.md` + `tramalia close` |
| `revisor` (reviewer) | opus | evidence pack + skill 12-multi-agent-review |
| `documentador` (documenter) | haiku | `docs/ai/` + skill 13-documentation-handoff |
| `resolutor-profundo` (deep solver) | fable (explicit invocation only) | exceptional cases + docs/ai/06 |

**How routing works:** your `/model` controls the main conversation *always*; the agent's `model:` applies only inside the delegated task (isolated context, billed at its own model's rate). Precedence: invocation override > frontmatter > `inherit`.

**Multi-host:** `tramalia sync` propagates the subagents via rulesync (`--features rules,subagents`) to Copilot, Cursor, Cline and other supported targets. It's idempotent: if you already have your own agents, `init` won't overwrite them.

**Audit:** `tramalia close --model <model>` records in `metadata.json` which model closed the task — key when you route cheap models and want to know which closes deserve a closer look.

## AI agents — the consumers

- **Who:** Claude Code, OpenAI Codex, Cursor, Antigravity, Gemini CLI, Copilot, Cline, etc.
- **Requires:** each one's official installation (Tramalia does **not** install them).
- **How they interact with Tramalia:** they **read** `AGENTS.md` + `docs/ai/` (the convention `init` drops), do the work, and on closing they use `tramalia close` (via shell or the `tramalia mcp` MCP façade). Tramalia doesn't reason or generate code: it **governs** what they do.

## In one sentence

rulesync **propagates** the rules, copier/Spec Kit **structure**, Gentle-AI **prepares** the agents, and the **agents** execute — all under the convention Tramalia maintains and audits.
