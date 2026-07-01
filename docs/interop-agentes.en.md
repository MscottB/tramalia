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

- **What it is / scope:** a toolkit for specification-driven development (constitution/spec/plan/tasks).
- **Requires:** Python (uv).
- **Install:** `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`.
- **Tramalia uses it in:** optional; complements the `specs/` folder that `init` generates. Tramalia doesn't reimplement it.

## Gentle-AI — agent setup/onboarding (external)

- **What it is / scope:** configures *which* agents you work with (models, skills, profiles, memory, MCP). It's a "bootstrap" of your AI workstation.
- **Requires:** see its repo (Go).
- **Install:** per its official documentation.
- **Relationship with Tramalia:** **external onboarding, NOT core.** Gentle-AI gets your machine ready; Tramalia governs what those agents do *inside the repo*. They're used separately to avoid double ownership of configs/prompts.

## AI agents — the consumers

- **Who:** Claude Code, OpenAI Codex, Cursor, Antigravity, Gemini CLI, Copilot, Cline, etc.
- **Requires:** each one's official installation (Tramalia does **not** install them).
- **How they interact with Tramalia:** they **read** `AGENTS.md` + `docs/ai/` (the convention `init` drops), do the work, and on closing they use `tramalia close` (via shell or the `tramalia mcp` MCP façade). Tramalia doesn't reason or generate code: it **governs** what they do.

## In one sentence

rulesync **propagates** the rules, copier/Spec Kit **structure**, Gentle-AI **prepares** the agents, and the **agents** execute — all under the convention Tramalia maintains and audits.
