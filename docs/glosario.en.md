# Glossary

Short definitions of the terms used across the documentation. Use the search box (top) to jump to one.

| Term | What it means |
|---|---|
| **ADR** (Architecture Decision Record) | A short document recording a technical decision, its context and consequences. In Tramalia they live in `docs/ai/05`. |
| **AGENTS.md** | Standard file (Linux Foundation) with the project rules that **all AI agents read**. Single source of truth. |
| **AI agent** | A tool that reads context, reasons, edits files and/or runs commands (Claude Code, Codex, Cursor, Antigravity…). |
| **Bootstrap** | The **base tools you install manually first** (mise, git, uv), because they can't install themselves. Once present, `mise install` brings everything else. |
| **Bundle** (Databricks Asset Bundle) | A declarative definition of Databricks jobs/pipelines (`databricks.yml`). The **`bundle`** gate validates it (`databricks bundle validate`) before deploying. See [Analytics](analitica.md). |
| **CLI** (Command-Line Interface) | A command-line interface: used by typing commands in the terminal. |
| **Copyleft** | A license type that requires derived code to stay open (GPL, LGPL, MPL). It doesn't affect Tramalia because the tools are *invoked*, not linked. |
| **Enforcement** | Tramalia **blocking** a task's close if a gate fails (unless a documented exception with `--allow-fail`). |
| **Evidence pack** | A dated folder with the **verifiable proof** of a close: commands, raw outputs, risks, rollback, next steps and `metadata.json`. |
| **Façade** | A thin layer that puts **a single interface** in front of a complex subsystem. The CLI and `tramalia mcp` are façades. |
| **Fan-out** | Propagating a single source (`AGENTS.md`) to the formats of several agents (Cursor, Copilot…), with rulesync. |
| **Gate** (quality gate) | A **mandatory validation** before closing a task: build, test, lint, security, database, UX/UI. |
| **Handoff** | A **structured handover** between agents/sessions: task → files → commands → result → risks → pending → next step. |
| **Horizon** (Horizonte) | A field in `specs/tasks.md` (now · next · later) that plans without committing: re-planning is **editing the file**; closed tasks are immutable through evidence. |
| **i18n** (internationalization) | JSON catalogs (`tramalia/i18n/{es,en}.json`) that translate the TUI and CLI. Resolution: `TRAMALIA_LANG` > `config.json → language` > system locale > English. |
| **Idempotent** | Running twice produces the **same result** without harm. `tramalia init` is idempotent: it never overwrites existing files. |
| **Ingestion** | Converting knowledge in formats the agent doesn't read well (PDF, Word, Excel) into consumable Markdown. Done by **markitdown**. |
| **Initialization guard** | `close`/`evidence`/`handoff` **block (exit 1)** in a repo without `tramalia init` — no governance without a convention. |
| **Interop** (interoperability) | **Optional** external tools that Tramalia orchestrates but does **not** require; if missing, it still governs and records the exception. |
| **LSP** (Language Server Protocol) | A protocol that provides code intelligence (definitions, references). Serena uses it to navigate symbols without reading whole files. |
| **MCP** (Model Context Protocol) | A standard protocol to connect AI agents with tools and data. Tramalia exposes an optional **MCP façade**. |
| **metadata.json** | A structured summary of each close (task, agent, timestamps, exit codes, status) that makes the **audit queryable**. |
| **Moat** | A product's defensible **differentiator**. In Tramalia: evidence pack, handoff, gates and repo-first audit. |
| **N0 / N1 / N2** (memory tiers) | N0 = files + CLI · N1 = MCP façade · N2 = real persistent memory (Engram / basic-memory / mem0). |
| **Ponytail / YAGNI** | **Minimalism** principles: do the minimum correct thing, don't rebuild what already exists, don't over-abstract. |
| **Repo-first** | Using **the repository as the source of truth**: everything important is versioned in it, not hidden in global configs. |
| **SAST** (Static Application Security Testing) | **Static** security analysis of code (done by Semgrep). |
| **Shell-out** | Tramalia **running an external command** (subprocess) and passing its output through as-is, without reimplementing it. |
| **Snapshot** | A **packaged** picture of the repo for AI consumption (done by Repomix). |
| **Stack** | The set of **technologies** in a project (Angular, .NET, PostgreSQL…). `tramalia detect` identifies it. |
| **Standalone** | Works **on its own**, without depending on anything external. Tramalia's core is standalone (Python only). |
| **Subagent** | A specialized agent the main model invokes for a delegated task, in an isolated context and with **its own `model:`** (role-based routing). Tramalia ships 5 in `.claude/agents/`. |
| **Token** | The minimal unit of text an AI model consumes. "Saving tokens" = sending less context to cut cost and latency. |
| **TUI** (Text User Interface) | An interactive interface **in the terminal** (Textual). `tramalia ui` opens it; it only reads and invokes the core, with no logic of its own. |
| **Wheel** | Python's **installable package** format (`.whl`); it's what `pip install` uses. |

Missing a term? It's a good first [contribution](https://github.com/MscottB/tramalia/blob/main/CONTRIBUTING.md).
