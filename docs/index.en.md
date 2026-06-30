# Tramalia

**Governance and verifiable evidence for building with multiple AI agents. Repo-first.**

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

## Tramalia at the center of the ecosystem

Tramalia doesn't compete with the other AI tools: it **governs and orchestrates** them. Each occupies a distinct space; Tramalia is the core that ensures control, traceability and continuity.

```mermaid
flowchart TD
    classDef core fill:#5b4bdb,stroke:#3c3489,color:#fff,stroke-width:2px;
    classDef sat fill:#eef0ff,stroke:#8a83e0,color:#26215c;
    classDef repo fill:#eaf0e0,stroke:#639922,color:#173404;

    T["🧩 TRAMALIA<br/><small>governance · gates · evidence · handoff · audit</small>"]:::core

    GA["Gentle-AI<br/><small>agent setup</small>"]:::sat
    EN["Engram<br/><small>N2 memory</small>"]:::sat
    HR["Headroom<br/><small>compression</small>"]:::sat
    SR["Serena<br/><small>semantic navigation</small>"]:::sat
    RP["Repomix<br/><small>snapshot</small>"]:::sat
    CM["codebase-memory-mcp<br/><small>code graph</small>"]:::sat
    MI["mise<br/><small>tools + gates</small>"]:::sat
    RU["rulesync<br/><small>rule fan-out</small>"]:::sat

    GA -.onboarding.-> T
    EN -.memory.-> T
    HR -.efficiency.-> T
    SR -.context.-> T
    RP -.context.-> T
    CM -.context.-> T
    MI -.execution.-> T
    RU -.interop.-> T

    T ==> R["📁 Repo<br/><small>AGENTS.md · docs/ai · .tramalia/evidence</small>"]:::repo
    AG["🤖 AI agents<br/><small>Claude · Codex · Cursor · Antigravity</small>"]:::sat
    AG ==reads/writes==> R
```

In one line: **Gentle-AI** enables *which* agents to use, **Engram** helps *remember*, **Headroom** makes context *cheaper*, **Serena/Repomix/codebase-memory-mcp** provide *code intelligence*, and **Tramalia** keeps the repo **controlled, traceable and consistent**.

## Start here

<div class="grid cards" markdown>

- :material-download: [__Installation & requirements__](instalacion.md)
- :material-sitemap: [__Full workflow__](flujo-completo.md)
- :material-tools: [__Tools__](herramientas.md)
- :material-vector-link: [__Integrations__](interop.md)

</div>
