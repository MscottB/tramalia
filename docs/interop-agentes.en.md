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

**No opus/fable access, or want to cut cost?** The 5 files are **yours** (editable; `init` won't overwrite them), and there's an **optional cap**: `tramalia agents cap sonnet` lowers everything above to sonnet and keeps what's below (haiku), without touching `inherit`. It's portable to other hosts as a convention — see [Models & effort per host → Model cap](multi-host.md#model-cap-portable-across-providers).

**Multi-host:** `tramalia sync` propagates the subagents via rulesync (`--features rules,subagents`) to Copilot, Cursor, Cline and other supported targets. It's idempotent: if you already have your own agents, `init` won't overwrite them.

**Audit:** `tramalia close --model <model>` records in `metadata.json` which model closed the task — key when you route cheap models and want to know which closes deserve a closer look.

## External skills catalog (vetted)

Besides the 13 own skills, `skills.toml` ships a **commented catalog** of external sources in the standard SKILL.md format — uncomment the ones you want and `tramalia skills` clones them:

| Source | What it brings | Fits with |
|---|---|---|
| [anthropics/skills](https://github.com/anthropics/skills) (official) | document skills (PDF/DOCX/XLSX), creative, technical | general use |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | react-best-practices (40+ rules) · **web-design-guidelines (100+ a11y/UX rules)** · writing-guidelines | **ux gate** + docs |
| [superpowers](https://github.com/obra/superpowers) | TDD, systematic debugging, planning | skills 05/08 |
| [mattpocock/skills](https://github.com/mattpocock/skills) | advanced TypeScript (includes **grill-me**: rigorous questioning before implementing) | TS projects + skill 01 |
| [caveman](https://github.com/JuliusBrussee/caveman) | cuts ~65-75% of output tokens — use the **`lite`** level (aggressive ones lose context); Ponytail comes first: [efficiency criterion](interop-memoria.md#the-criterion-which-to-mount-and-which-to-use) | skill 03 (token-saver) |
| [Ponytail](https://github.com/DietrichGebert/ponytail) (enabled by default) | minimalism + its own MCP | skill 04 |

Other design/UX sources you can reference the same way: [impeccable](https://github.com/pbakaus/impeccable), [ui-ux-pro-max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill), [emilkowalski/skills](https://github.com/emilkowalski/skills) (animation/UI). Claude Code's official plugin marketplace is [claude-plugins-official](https://github.com/anthropics/claude-plugins-official). [gstack](https://github.com/garrytan/gstack) is a pack of 31 skills that simulate a full team (CEO, Designer, QA, Security OWASP+STRIDE, Release) — same spirit as Tramalia's subagents, at a different scale; a useful reference, not installed as a dependency.

## Cross-provider review

[codex-plugin-cc](https://github.com/openai/codex-plugin-cc) (official from OpenAI) lets you invoke **Codex from inside Claude Code** for review or delegation (`/codex:review`, `/codex:transfer`). It fits directly with Tramalia's `revisor` role: two different models reviewing the same evidence pack.

## Personal memory vs. project memory

[ai-second-brain](https://github.com/charlie947/ai-second-brain) builds a searchable personal memory from your chat history (ChatGPT/Claude). It's a **different** angle from Engram/N2: Engram remembers *project decisions* across closes; ai-second-brain remembers *your* conversation history. They don't overlap; they can coexist.

## Multi-agent orchestration (external)

Tramalia does **not** launch agents in parallel — that's a separate ecosystem slot. If you need it: [Multica](https://github.com/multica-ai/multica) (agents as "teammates": you assign issues and they execute with a local daemon + dashboard), Vibe Kanban or Conductor. They coexist well: the orchestrator distributes the work, **Tramalia audits every close** (`close`/`log` with agent and model).

### The Ralph loop pattern

[Ralph](https://ghuntley.com/ralph/) (Geoffrey Huntley) is a pattern, not a tool you install: a bash loop that re-feeds the same prompt to an agent, iteration after iteration, until a PRD is complete. The key is that **progress lives in files and git, not in the context window** — each round starts with a clean context.

It fits almost literally with Tramalia's structure:

- **`specs/tasks.md`** = the PRD Ralph needs as its source of truth.
- **The 5 subagents** = the "main context is a scheduler, delegate the expensive work" pattern Ralph recommends.
- **`.tramalia/evidence/`** = the state that persists outside the context window between iterations.
- **`tramalia close`** = the natural "handoff" point at the end of each loop round.

If you run Tramalia in a Ralph-style loop, each iteration would be: read `specs/tasks.md` → work the next task with the `ejecutor` → `tramalia close --task <ID>` → the loop continues with the next task, without context growing unchecked.

## Tips for Claude Code (the most common host)

- **`/model opusplan`** — Opus for planning, Sonnet for execution: pairs perfectly with the subagents above.
- **"ultrathink"** in the prompt — triggers maximum extended reasoning **for a single turn**, without changing the session (useful before delegating to `resolutor-profundo`).
- **`ultracode` / `/effort ultracode`** — unlike ultrathink, this is a **whole-session** mode: it pins xhigh effort and auto-orchestrates parallel subagents for every substantive task. Reserve it for big work (several `specs/tasks.md` tasks at once); it's expensive for routine edits.
- **`/compact`** — compacts the conversation when context grows; do it after a `tramalia close` (the evidence pack already preserves what matters).

## AI agents — the consumers

- **Who:** Claude Code, OpenAI Codex, Cursor, Antigravity, Gemini CLI, Copilot, Cline, etc.
- **Requires:** each one's official installation (Tramalia does **not** install them).
- **How they interact with Tramalia:** they **read** `AGENTS.md` + `docs/ai/` (the convention `init` drops), do the work, and on closing they use `tramalia close` (via shell or the `tramalia mcp` MCP façade). Tramalia doesn't reason or generate code: it **governs** what they do.
- **Which ones do you have installed?** `tramalia doctor` (and the Overview tab of `tramalia ui`) **detects the agent CLIs present** on your machine — informational only, never configures them. Model/effort matrix per host: [Models & effort per host](multi-host.md).

## In one sentence

rulesync **propagates** the rules, copier/Spec Kit **structure**, Gentle-AI **prepares** the agents, and the **agents** execute — all under the convention Tramalia maintains and audits.
