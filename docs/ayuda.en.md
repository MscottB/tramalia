# Help (FAQ & troubleshooting)

Answers to the most common real-world stumbles. Not covered? [Open an issue](https://github.com/MscottB/tramalia/issues).

## Installation & doctor

**I installed a tool with uv and it still shows as "missing", even after restarting the terminal.**
`uv tool install` puts binaries in `~/.local/bin`, which on Windows **never enters PATH** (even after a restart) unless you run `uv tool update-shell`. Since v0.20 the doctor checks that folder directly and marks it *"installed via uv"*; to use it from your shell, run `uv tool update-shell` once.

**Installed via mise and `doctor` didn't see it.**
mise tools live behind *shims*, off PATH until `mise activate` or a terminal restart. The doctor detects them anyway (`mise which`) and tells you.

**An install gets stuck (e.g. headroom-ai).**
In the TUI the output streams live: if it stalls, **`c` cancels it** and moves on to the next; each tool also has a time limit. If the error mentions access denied, run from an **administrator terminal**.

**winget/choco fails with an 0x8… error.**
Almost always elevation: administrator terminal and retry. The install panel warns you when it detects it.

**Serena shows "no install needed" — is that a bug?**
No: Serena runs via `uvx` (ephemeral). With uv present, it's ready — `init` already wired it in `.mcp.json`.

**Can engram be installed on Windows? / it wasn't showing in the selector.**
Yes. brew is macOS-only, but engram installs on **any OS with `go install github.com/Gentleman-Programming/engram/cmd/engram@latest`** — since v0.22.1 the selector (`i` key) offers it automated if you have **Go** installed (otherwise it shows the manual route: binary from its *releases*). The binary lands in `~/go/bin`; the doctor detects it there even if it's not on your PATH (`installed via go`). If your shell can't find it, add `~/go/bin` to PATH.

**Some tools (engram, codegraph, hermes…) weren't showing in the install selector (`i`).**
Since v0.22 the selector shows **all** missing tools: the automatable ones as selectable and the manual-only ones listed separately with their command. Before, those without an automatic installer on your system were silently omitted.

**A tool says "○ not installed (optional)": is it there or not?**
It's not installed. "Optional" only means you don't need it unless you use its gate/feature. The status always says it explicitly: `✓ installed` · `○ not installed (optional)` · `✗ not installed (required)`.

## Close & gates

**`close` exits 1 with "project not initialized".**
That's the [initialization guard](arquitectura.md#the-initialization-invariant): no governance without a convention. Run `tramalia init` (or `--adopt` if you already have your own `AGENTS.md`).

**It closed "with a documented EXCEPTION" instead of ✓.**
mise is missing: the gates **didn't run** and the honest status is `no_gates`. Install mise (`tramalia doctor --fix`) for real validation.

**A gate fails and I need to close anyway.**
`--allow-fail` — but it's recorded as `passed_with_exceptions` with the reason in `risks.md`, never as `passed`. The audit is not glossed over.

**The close was blocked by metrics.**
You defined `.tramalia/thresholds.json` and a metric in `.tramalia/metrics.json` violates it (or is missing). See [Analytics](analitica.md#metrics-and-thresholds-in-the-evidence-mlanalytics).

## Agents

**My agent keeps calling tools that aren't installed.**
Run `tramalia doctor`: it generates `.tramalia/context/tools.json`, and the `AGENTS.md` rule tells the agent to consult it before invoking — if `installed` is false, use the alternative or continue without it.

**Does it work with Claude Code desktop / Codex desktop / Antigravity IDE?**
Yes — they read `AGENTS.md` and run shell just like their CLIs; `tramalia close` works identically. See [Models & effort per host](multi-host.md).

## Interface & language

**The TUI comes up in the wrong language.**
Resolution: `TRAMALIA_LANG` > `config.json → language` > system locale. Force with `TRAMALIA_LANG=en tramalia ui`.

**How do I update Tramalia?**
`pip install -U tramalia-cli` (the CLI). `tramalia update` updates *what's orchestrated* (mise tools + skills), not the package.

## Skills

**I added a skill by URL and it isn't cloned.**
`add` only declares it in the manifest; clone it with `tramalia skills` (or the `s` key in the TUI).

**Enter on a skill does nothing.**
Only **external** ones toggle; the own skills (01–16) are always installed. If the TOML block was hand-edited into another shape, the conservative toggle won't touch it — adjust it manually.
