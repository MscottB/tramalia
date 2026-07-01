# Memory & efficiency

Persistent memory across sessions (**N2**) and token compression. Both are **optional interop**: Tramalia's core already has file-based memory (N0) and the MCP façade (N1).

## The 3 memory tiers

| Tier | What it is | Tool |
|---|---|---|
| **N0** | repo files (`AGENTS.md`, `docs/ai/`) + CLI | Tramalia's core |
| **N1** | Tramalia's MCP façade | `tramalia mcp` |
| **N2** | real persistent memory (graph/semantic) | **Engram** · basic-memory · mem0 |

## Engram — N2 persistent memory (recommended)

- **What it is / scope:** recall across sessions (decisions, observations) in SQLite, with MCP, CLI, TUI and git-sync.
- **Requires:** nothing (binary, Go).
- **Install:** `brew install gentleman-programming/tap/engram` (other OSes: see repo).
- **Tramalia uses it in:** `doctor` detects it; `init` wires it into `.mcp.json` **if installed**; `close`/`handoff --engram` export the close (opt-in).
- **Interacts with / rule:** **opt-in** export, never secrets by default. It doesn't replace the repo's evidence; it complements it with cross-session recall.

## basic-memory — N2 memory in local Markdown

- **What it is / scope:** persistent memory as local Markdown files, via MCP. Fits the repo-first philosophy.
- **Requires:** Python (uv).
- **Install:** `uvx basic-memory` · `pip install basic-memory`.
- **Tramalia uses it in:** an alternative to Engram in `.mcp.json` (not by default).

## mem0 — semantic N2 memory

- **What it is / scope:** a semantic memory layer for agents.
- **Requires:** Python.
- **Install:** `pip install mem0ai`.
- **Tramalia uses it in:** an N2 alternative (not by default).

## Headroom — token compression / efficiency

- **What it is / scope:** compresses tool outputs, logs and context before they reach the LLM (60-95% fewer tokens). Library, proxy, wrapper and MCP modes.
- **Requires:** Python (or Node).
- **Install:** `pip install "headroom-ai[all]"` · MCP: `headroom mcp install`.
- **Tramalia uses it in:** **only with `tramalia init --with-headroom`** (opt-in; because of its proxy mode, never by default). `doctor` detects it.
- **Interacts with / HARD MOAT RULE:** *compression ≠ evidence*. The raw output (`*-output.txt`) and `metadata.json` are always kept in `.tramalia/evidence/`. Headroom **never** modifies, replaces or omits them — it only generates derived views (`review-summary.md`). Its `headroom learn` must be redirected to `docs/ai/06-intentos-fallidos.md`, not write freely.

## How they fit together

**Engram/basic-memory/mem0** remember *across sessions*; **Headroom** makes *the context* cheaper. None touch the governance core (`close`, `log`, evidence pack). Tramalia detects them and wires them opt-in; you decide whether to mount them.
