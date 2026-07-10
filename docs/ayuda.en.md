# Help (FAQ & troubleshooting)

Answers to the most common real-world stumbles. Not covered? [Open an issue](https://github.com/MscottB/tramalia/issues).

## Installation & doctor

**When updating (`pip install -U tramalia-cli`) you see "WARNING: Ignoring invalid distribution ~ramalia-cli".**
Not a Tramalia issue — it's a pip artifact on Windows. If `tramalia ui` (or another process) had the package in use during a *previous* update, pip couldn't delete the old version and left it **renamed with `~`** in your `site-packages` folder (`~ramalia` and `~ramalia_cli-X.YY.Z.dist-info`, where `X.YY.Z` is the version that got half-removed) instead of fully deleting it. The **new install is still sound** — confirm with `tramalia --version` — the warning is just noise from those orphaned folders.

To clean it up: close any running `tramalia ui` and delete the `~ramalia*` folders from your `site-packages` (the exact path is shown in the warning itself):
```powershell
Remove-Item -Recurse -Force "<path-to-site-packages>\~ramalia"
Remove-Item -Recurse -Force "<path-to-site-packages>\~ramalia_cli-X.YY.Z.dist-info"
```
Replace `X.YY.Z` with the actual version number shown in the folder name.

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

**A tool says "requires Go" (or Node) and I can't install it automatically.**
Its only automatable route needs that runtime, which you don't have. Since v0.23 the selector (`i` key) **offers to install the runtime** (⬇ install Go → enables engram): check it together with the rest and, since **v0.27**, Tramalia installs the runtime **and chains** the tool it unblocks in the same run, **without restarting the terminal** (it refreshes the process PATH to see the freshly-installed Go/Node). In the CLI: `tramalia doctor --fix` includes the runtime in the plan. Runtimes that enable automation: **Node.js** (npm tools) and **Go** (engram).

**I installed Go but engram didn't install in the same session.**
Fixed in **v0.27**. The problem: winget adds Go to the *user* PATH, not to the running TUI process's PATH, so engram kept showing "blocked by Go" until a restart. Now, after finishing a runtime install, Tramalia adds its bin folder (`C:\Program Files\Go\bin`, `~/go/bin`, `C:\Program Files\nodejs`) to the process PATH and **chains** engram automatically. If it still fails, restart the terminal and press `i` again.

**Where do I see the Tramalia version?**
In the `tramalia ui` header title, in the `tramalia doctor`/`detect` panel, and with `tramalia --version`. Update the CLI with `pip install -U tramalia-cli`.

**CodeGraph showed as "manual only" and couldn't be automated.**
That was our mistake — it does have an npm package (`@colbymchenry/codegraph`). Since v0.24 it automates like repomix/opencode — if Node is missing, the selector offers to install it first.

**Antigravity shows as "missing" even though I installed it.**
The CLI's real binary left on PATH is called **`agy`**, not `antigravity` (Antigravity CLI replaced Gemini CLI, discontinued 2026-06-18). Detection was looking for the wrong name — fixed in v0.24. Since **v0.27** the CLI is **automated on Windows via winget** (`Google.AntigravityCLI`); on mac/linux it's still the official `curl` script, manual on purpose (we never auto-run remote scripts).

**Can I install the Antigravity IDE and Antigravity 2.0, not just the CLI?**
Yes, since **v0.27**. Antigravity has **three surfaces**: the **CLI** (`agy`), the **IDE** (a VS Code fork), and **Antigravity 2.0** (agent platform, desktop app). The doctor lists all three; on Windows they install via winget (`Google.AntigravityCLI` · `Google.AntigravityIDE` · `Google.Antigravity`). Since the IDE and 2.0 are desktop apps with no command in PATH, Tramalia **detects them with `winget list`** (not a `--version`).

**OpenClaw and Hermes: can they be automated?**
Since **v0.27**: **OpenClaw** yes — it's an npm CLI (`npm i -g openclaw`, needs Node); the later `onboard`/daemon is your config. **Hermes Agent** no: it only installs via script (`curl … | bash`), which Tramalia never auto-runs — it shows you the exact command to run yourself. Before, both just said "see documentation".

## Context: which navigation tool to use

**I have Serena, CodeGraph, codebase-memory-mcp and Graphify installed — which does the agent use?**
Whichever `.tramalia/config.json → context.backend` sets (default `serena`). It's a **per-project** value, not a decision the agent makes each time — it prevents alternating between inconsistent indexes. Change it with `tramalia context set <backend>` or the `b` key in `tramalia ui` (shows each option's scope and ideal use case before you pick). See `tramalia context list` for the full detail.

**Do Repomix and markitdown also need picking?**
No — they're point-in-time utilities (full snapshot / document ingestion), they don't compete for the active backend. They're used whenever they apply, regardless of the navigation backend.

**In the backend selector (`b`), Serena showed ○ even though I have it, and CodeGraph/Graphify showed ✓.**
Fixed in **v0.28**. The ✓/○ used `shutil.which`, which can't see **Serena** because it runs ephemerally via `uvx` (never left as a binary on PATH). It now uses the **same probe as `doctor`**, so Serena shows installed if you have `uv`. It also clearly marks which is the **active backend** ("active") and each one's installed/not state.

**I couldn't close the backend panel with ESC, only with Cancel.**
Fixed in **v0.28**: **ESC closes** the panel (same as Cancel). The same applies to the install panel (`i`).

**What if I pick a backend I don't have installed?**
It's **set anyway** — the backend is a *project preference*, not a check. Tramalia **warns** you it isn't installed and tells you how to get it (press `i` to install, or pick another). This lets you declare the project's intent even if you haven't installed it on your machine yet.

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
Yes — they read `AGENTS.md` and run shell just like their CLIs; `tramalia close` works identically (there's no "app version" and "CLI version": everything lives in the repo). See [Models & effort per host](multi-host.md).

**I only want to use Sonnet — the subagents are on opus/fable and I don't have them.**
`tramalia agents cap sonnet`: lowers everything above to sonnet (planner, reviewer, deep-solver) and **keeps what's below** (documenter stays on haiku); `executor` (inherit) follows your session. Default is `none` (no cap). `tramalia agents cap none` restores the original routing. Also `tramalia init --model-cap sonnet` from the start.

**Can I edit the 5 `.claude/agents/` files?**
Yes, they're **yours** — `tramalia init` is idempotent and never overwrites them. Edit the `model:` or the body by hand if you like; `agents cap` only manages the `model:` line of the 5 roles.

**I set the cap in Claude but I use Codex/Antigravity — is it respected?**
On those hosts there's no per-role routing Tramalia can rewrite (and we don't touch your `~/.codex/config.toml` — that's Gentle-AI's territory). The cap travels as a **rule in `AGENTS.md`** (which the agent reads) + `model_cap` in `tools.json`; and `agents cap` prints the capability-level equivalence for you to paste. See the per-host matrix in [Models & effort per host → Model cap](multi-host.md#model-cap-portable-across-providers).

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
