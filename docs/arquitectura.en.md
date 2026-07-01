# Architecture

Tramalia is a **thin layer** with a golden rule: *it doesn't implement capabilities, it orchestrates them*. It only builds what nobody else does well (governance, evidence, handoff). Everything else is delegated.

## Guiding principle: Ponytail / YAGNI

Tramalia's philosophy is **minimalism**: do the minimum correct thing and don't rebuild what already exists. This follows the [Ponytail](https://github.com/DietrichGebert/ponytail) principle (and YAGNI). It's not a tool you install: it's a **rule that is read and followed**.

That's why `tramalia init` writes it into your project's `AGENTS.md` (*General rules — Ponytail / YAGNI* section), so that **any agent** working the repo prioritizes the minimal solution, doesn't over-abstract and doesn't duplicate logic. If you prefer it as a versioned skill, it's included as an example in `.tramalia/skills.toml`.

## The three layers

```mermaid
flowchart TB
    classDef core fill:#5b4bdb,stroke:#4335b0,color:#ffffff;
    classDef conv fill:#e7f3d8,stroke:#7cb342,color:#2e4d13;
    classDef ext fill:#eef1ff,stroke:#9a92e8,color:#2a2160;

    subgraph C1["Layer 1 · Thin CLI (what you run)"]
        CLI["init · doctor · close · log · evidence · handoff · gates · context · sync · mcp"]:::core
    end
    subgraph C2["Layer 2 · Convention (what stays in your repo)"]
        CONV["AGENTS.md · docs/ai/ · mise.toml · .mcp.json · .tramalia/evidence"]:::conv
    end
    subgraph C3["Layer 3 · External (updated from their repos)"]
        EXT["mise · Serena · Repomix · Semgrep · rulesync · Engram · Headroom · agents"]:::ext
    end
    C1 -->|init generates| C2
    C2 -->|read| C3
    C3 -->|run / query| C1
```

1. **Thin CLI** — a single face that does transparent *shell-out* to the real tools. It never hides errors; you can always bypass it (call `mise`/`serena` directly).
2. **Convention** — versioned files, the project's source of truth. **The real value.**
3. **External** — full tools and the agents, updated from their repos.

## Core vs. interop

The most important design distinction: what is **core** (own, standalone, Python only) and what is **interop** (external, optional, degrades gracefully).

=== "Core"

    Works **with Python only**, without depending on anything external.

    - `init` — generates the convention
    - `doctor` — diagnoses
    - `detect` — detects the stack
    - **`close`** — the closing ritual with enforcement
    - **`log`** — the audit trail
    - `evidence` · `handoff` — the traceability pieces
    - `mcp` — the MCP façade

=== "Interop (optional)"

    Delegates to external tools; if missing, records it as a documented exception.

    - `gates` → **mise**
    - `context` → **Repomix / Serena / codebase-memory-mcp**
    - `sync` → **rulesync**
    - `skills` → **git**
    - `update` → **mise + copier**
    - N2 memory → **Engram**
    - compression → **Headroom** (opt-in)

## The "manifest + updater" model

Tramalia doesn't copy anyone's code. It **references** it and one command keeps it up to date:

```mermaid
flowchart LR
    classDef step fill:#eef1ff,stroke:#9a92e8,color:#2a2160;
    U["tramalia update"]:::step --> A["mise upgrade<br/><small>external tools</small>"]:::step
    U --> B["copier update<br/><small>the convention</small>"]:::step
    U --> C["skills sync<br/><small>referenced skills</small>"]:::step
```

## The MCP façade (level 1)

`tramalia mcp` exposes the same core as native MCP tools (`project_status`, `get_agent_rules`, `get_failed_attempts`, `record_handoff`, `build_evidence`…), so an agent can use them without shelling out. It's a **thin façade**, not a new engine. The 3 memory tiers:

- **N0** — files + CLI (start here, no MCP).
- **N1** — this façade (if you want a native tool).
- **N2** — mount **Engram** / basic-memory / mem0 (serious persistent memory).

## The moat invariant

> The raw `*-output.txt` files and `metadata.json` are the **official** evidence. No derived artifact (Headroom compression, `review-summary.md`) may modify, replace or omit them — only add auxiliary files marked as derived.

This rule lives in the code (`core/governance.py`), in a test (`test_close_conserva_salidas_crudas`) and here. It's what protects auditability when efficiency is added.
