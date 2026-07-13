<div class="tramalia-hero" markdown>
<div class="tramalia-hero__content" markdown>

<span class="tramalia-hero__eyebrow">Repo-first governance for AI agents</span>

# Repository governance for multi-agent AI projects

**Rules, gates, verifiable evidence, and clear handoffs** so your agents (Claude Code, Codex, Cursor, Antigravity…) work aligned, under control, and without losing traceability — all versioned in your repo, not in global configs.

[Get started](instalacion.md){ .md-button .md-button--primary } [See the architecture](arquitectura.md){ .md-button }

</div>
<div class="tramalia-hero__visual" markdown>
![Tramalia — repository guardian owl](assets/brand/tramalia-mark.webp)
</div>
</div>

!!! quote ""
    **Git governs human collaboration; Tramalia governs agentic collaboration.** It's the change control + audit trail for when several AI agents work on a real project: shared rules, mandatory validations, and verifiable evidence for every close.

Tramalia is a **repo-first layer** that ensures *any* agent (Claude Code, Codex, Cursor, Antigravity…) touching the project works under the same rules, runs validations, documents its decisions, leaves verifiable evidence, and hands off clearly. It does this by **orchestrating external tools** instead of reimplementing them.

<div class="grid cards" markdown>

-   :material-gavel:{ .lg .middle } __Repo-first governance__

    ---

    Shared rules (`AGENTS.md`), mandatory gates and enforcement at close. All versioned in the repo, not hidden in global configs.

    [:octicons-arrow-right-24: Architecture](arquitectura.md)

-   :material-clipboard-check:{ .lg .middle } __Evidence & audit__

    ---

    `close` leaves an evidence pack with raw outputs + `metadata.json`; `log` is the verifiable audit trail of all agentic work.

    [:octicons-arrow-right-24: Commands](comandos.md)

-   :material-puzzle:{ .lg .middle } __Orchestrates, doesn't reimplement__

    ---

    Delegates to mise, Serena, Repomix, Semgrep, rulesync… The core runs standalone with Python only; external tools are optional interop.

    [:octicons-arrow-right-24: Ecosystem](ecosistema.md)

-   :material-rocket-launch:{ .lg .middle } __Start in 3 commands__

    ---

    `pip install`, `tramalia init`, `tramalia doctor`. No Node or cloud services to govern your repo.

    [:octicons-arrow-right-24: Installation](instalacion.md)

</div>

## Get started in two minutes

```bash
pip install tramalia-cli    # Python 3.10+ only — no Node, no cloud services
tramalia init               # drops the full convention into your repo
tramalia doctor             # tells you what else is worth installing
```

From there, your agent reads `AGENTS.md` and works under the project's rules; you close each task with `tramalia close` and the evidence stays. The whole journey, step by step: [Full workflow](flujo-completo.md).

!!! tip "Keeping Tramalia up to date is TWO steps, not one"
    `pip install -U tramalia-cli` updates **the CLI** on your machine — but your already-generated repo **doesn't change on its own**. Then run **`tramalia upgrade`** in each project: it adds what's new in the convention **without overwriting anything of yours**. `tramalia update`, a different command, updates mise and rehydrates skills at their pinned SHAs; it does not move Team locks. Use `tramalia skills update [name]` to advance them. Detail: [Commands → upgrade](comandos.md#upgrade-update-an-already-initialized-repo).

## How does it fit with the other tools?

Tramalia doesn't compete with Gentle-AI, Engram, Serena or the rest: it **governs and orchestrates** them — each occupies a distinct space and Tramalia is the core that ensures control, traceability and continuity. The full ecosystem map, actor by actor, with the layers diagram: [Ecosystem](ecosistema.md).

## Start here

<div class="grid cards" markdown>

- :material-download: [__Installation & requirements__](instalacion.md)
- :material-sitemap: [__Full workflow__](flujo-completo.md)
- :material-school: [__Full example__](ejemplo-completo.md) — a real project end to end: every own option and every third-party tool in action.
- :material-robot: [__How an AI works__](como-trabaja-ia.md) — the 4 pillars (plan · divide · verify · rules); new vs. existing project.
- :material-monitor-dashboard: [__The interface (TUI)__](interfaz.md) — the bilingual (es/en) dashboard, tab by tab.
- :material-tools: [__Tools__](herramientas.md)
- :material-vector-link: [__Integrations__](interop.md)

</div>

Multi-host or a data project? See [Models & effort per host](multi-host.md) and [Analytics (Python/Databricks)](analitica.md).
