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

## The criterion: which to mount and which to use

**N2 memory — tiebreaker** (pick **one**, don't scatter memory):

- **Engram** — the recommended default: dependency-free binary, git-sync, and `close --engram` already integrates it with the close.
- **basic-memory** — if you want the memory **readable inside the repo** as Markdown (the most repo-first); ideal when memory must travel with the code.
- **mem0** — only if you need **semantic** recall (embeddings) and accept more setup.
- If **more than one is installed**: use a single one as the active memory and write it down in `AGENTS.md` — two parallel memories diverge and neither stays reliable.
- If **none is installed**: work continues normally — N0 (repo files + git) is already memory; N2 is an accelerator, not a requirement.

**Token efficiency — order of preference:**

1. **Ponytail** first — it's *preventive*: the minimalism ruleset makes the agent generate less code and less noise from the start (zero risk, no infrastructure; `init --with-ponytail`). The cheapest token is the one never generated.
2. **caveman**, level **`lite`** — compresses the agent's *output* (~65% fewer output tokens). It has `lite` / `full` / `ultra` levels: use **`lite`** — the aggressive levels save more but lose context and clarity in the answers; `lite` keeps the balance. Code, commands and errors are preserved byte-for-byte at every level.
3. **Headroom** last — the biggest saving (60-95%, compresses *the input context*), but it operates as a proxy: explicit opt-in only (`--with-headroom`) and under the hard moat rule (it never touches raw evidence).

The three attack different things (generate less · answer shorter · compress the input), so **they can coexist** — but adopt them in that order: each next step adds savings and also complexity.

**Boundary with external knowledge:** memory stores *what YOUR project learned* (decisions, failed attempts); [notebooklm-mcp](interop-contexto.md#notebooklm-mcp-curated-external-knowledge-mcp-cloud) answers *what others documented* (library docs). Don't mix them: project decisions go to Engram/`docs/ai/`, never to a cloud service.

None touch the governance core (`close`, `log`, evidence pack). Tramalia detects them and wires them opt-in; you decide whether to mount them.
