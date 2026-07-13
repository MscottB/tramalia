# Command reference

Public command names such as `close`, `evidence`, and `handoff` remain available
for compatibility. Documentation, domain models, and the v1 schema use the
Spanish concepts **cierre**, **evidencia**, and **traspaso**, the filename
`metadatos.json`, and stable Spanish ASCII state values.

The governance core runs with Python. Integrations transparently invoke external
tools and return explicit states; they never hide errors or turn an unavailable
capability into approval.

> **Pre-BETA transition:** this page describes the formal contract already
> provided by the new core modules. Public CLI, TUI, and MCP adapters are still
> being migrated on this branch and may emit the legacy format. Do not treat
> their output as v1 evidence until that unification is complete; this warning
> will be removed before the BETA is published.

## Summary

| Command | Purpose | Type |
|---|---|---|
| `tramalia menu` | looping interactive menu | core |
| `tramalia ui` | overview, skills, audit, and close TUI | core + `[tui]` extra |
| `tramalia init` | generate the convention idempotently | core |
| `tramalia upgrade` | add new convention files without overwriting | core |
| `tramalia doctor [--fix]` | diagnose or install selected tools | core |
| `tramalia detect` | detect the stack and applicable quality gates | core |
| **`tramalia close [TASK]`** | **evaluate gates and publish a formal close** | **core** |
| **`tramalia log`** | **read the structured v1 audit log** | **core** |
| `tramalia evidence [TASK]` | create an evidence package | core |
| `tramalia handoff [TASK]` | record a transfer; compatible public alias | core |
| `tramalia gates` | run quality gates directly | `mise` integration |
| `tramalia context [build\|list\|set <backend>]` | build context and select its backend | integration |
| `tramalia agents [list\|cap <level>]` | inspect or cap subagent models | core |
| `tramalia sync [--to --features]` | propagate compatible rules and subagents | `rulesync` integration |
| `tramalia skills [sync [<n>]\|list\|outdated\|enable\|disable\|add]` | manage the skill catalog | Git integration |
| `tramalia update` | update orchestrated tools and skills | integration |
| `tramalia mcp` | start the MCP façade | core + MCP SDK |

## close — governed close

A **quality gate** is an automated command that verifies a required condition:
build, tests, lint, security, database, UX, or another domain check. `close`
discovers gates declared in `mise.toml`, executes their exact commands, and
records results and outputs.

```bash
tramalia close              # current task; agent/reviewer from config.json
tramalia close TASK-001     # explicit safe ID
```

Resolution chain:

| Value | 1st | 2nd | 3rd | Final fallback |
|---|---|---|---|---|
| task | positional argument | `--task` | `.tramalia/current-task.md` | interactive prompt or `TASK-000` in scripts |
| agent | `--agent` | `config.json → agents.primary` | — | empty value |
| reviewer | `--reviewer` | `config.json → agents.reviewer` | — | empty value |
| model | `--model` | — | — | `null` in formal data |

Declared identity is audit information, not a signature. `close` does not invoke
the named agent: it runs gates, evaluates policy, and persists the same result
consumed by the CLI, TUI, and MCP surfaces.

### Formal states

Aggregate gate states are:

- `aprobado`
- `fallido`
- `ejecutor_no_disponible`
- `sin_configurar`
- `configuracion_invalida`
- `error_ejecucion`

The close is limited to `aprobado`, `aprobado_con_excepciones`, or `bloqueado`.
In particular, missing `mise` produces `ejecutor_no_disponible` and blocks the
close; skipping gate execution never implies approval.

### Exceptions

A complete exception declares a reason, accepted risk, affected control,
reference, reviewer, and either expiry or remediation condition. Each exception
covers only its named control; any uncovered failure keeps the close `bloqueado`.

`--allow-fail` remains a compatibility alias, but it cannot accept an empty
exception or automatically turn failure into success. When every failure is
covered by a complete and current exception, the result is
`aprobado_con_excepciones`.

### Persisted result

The package is atomically published under a unique identity:

```text
.tramalia/evidencia/20260713T183012.123456Z-a1b2c3d4/
├── metadatos.json
├── traspaso.md
├── build-salida.txt
└── test-salida.txt
```

The v1 `metadatos.json` contract includes these stable keys:

```json
{
  "version_esquema": 1,
  "id_paquete": "20260713T183012.123456Z-a1b2c3d4",
  "id_tarea": "TASK-001",
  "operacion": "cierre",
  "inicio_utc": "2026-07-13T18:30:12.123456Z",
  "fin_utc": "2026-07-13T18:30:18.123456Z",
  "entorno": {"tramalia": "0.34.0b1", "python": "3.13.5", "sistema_operativo": "Windows-11", "cadena_herramientas": {}},
  "git": {"commit": null, "rama": null, "limpio": null, "base_comparacion": null, "rastreados": [], "preparados": [], "no_rastreados": [], "renombrados": [], "eliminados": []},
  "comandos": [],
  "puertas": {"estado": "sin_configurar", "descubiertas": [], "ejecutadas": [], "omitidas": [], "fallidas": [], "errores_validacion": []},
  "estado_cierre": "bloqueado",
  "agente": "codex",
  "modelo": null,
  "metricas": {},
  "umbrales": {},
  "errores_validacion": [],
  "excepciones": [],
  "vinculo_traspaso": "traspaso.md"
}
```

Raw outputs stay outside JSON and are bound from each command with
`archivo_salida` and `hash_salida`. Timestamps are UTC; unsafe paths, invalid
hashes, and non-finite numbers are rejected before publication.

### Metrics and thresholds

When `.tramalia/metrics.json` exists, its values are included under `metricas`.
When `.tramalia/thresholds.json` also exists, limits are recorded under
`umbrales`. A missing or out-of-range metric blocks like a failed gate. Invalid
JSON or an invalid schema is a configuration error and never publishes false
approval.

## log — structured audit log

```bash
tramalia log
```

It reads only `.tramalia/evidencia/*/metadatos.json`, ignores staging
directories, and sorts packages by descending ID. It validates the full schema,
directory identity, timestamps, enums, commands, hashes, output files,
exceptions, and `vinculo_traspaso`.

A correct package is `valida`. A corrupt package is `invalida` with a safe
error, and does not prevent other entries from being listed. `log` never infers
an outcome from historical Markdown.

## evidence and handoff — evidence and transfer

The command names remain available so existing automation does not break:

```bash
tramalia evidence TASK-001
tramalia handoff TASK-001
```

- `evidence` creates a formal package under
  `.tramalia/evidencia/<id_paquete>/`.
- `handoff` records the concept named **traspaso**. Its canonical source is the
  package's `traspaso.md`.
- `docs/ai/07-traspaso-agentes.md` is only a projection of the latest transfer,
  linked with a relative path. Projection failure never changes or invalidates
  the package.

## doctor

`tramalia doctor` groups requirements into base, stack, context, memory,
security, database, UX/UI, analytics, convention, and agent CLI domains. It
distinguishes installed, missing optional, and missing required tools and gives
operating-system-specific instructions.

`tramalia doctor --fix` builds an install plan and lets you select automatable
tools. Manual steps remain visible separately.

## init and upgrade

`tramalia init` idempotently generates `AGENTS.md`, `CLAUDE.md`, `docs/ai/`,
`specs/`, subagents, skills, `mise.toml`, `.mcp.json`, and `.tramalia/`. With
`--adopt`, it integrates the governance block through markers and preserves user
content.

After updating the package:

```bash
pip install -U tramalia-cli
tramalia upgrade
```

`upgrade` adds missing new files, refreshes the managed `.gitignore` block, and
records the version. It never overwrites an existing customized document.

## ui

`tramalia ui` opens four views: **Overview**, **Skills**, **Audit**, and
**Close**. Audit shows the formal log and `metadatos.json`; Close invokes the
same core and presents its final state. The TUI has no parallel policy engine.

## agents

`tramalia agents list` shows subagents, models, and the current cap.
`tramalia agents cap <fable|opus|sonnet|haiku|none>` sets a portable maximum;
lower roles remain unchanged and `inherit` is preserved.

## context

- `tramalia context` or `tramalia context build` generates
  `.tramalia/context/`.
- `tramalia context list` compares supported backends.
- `tramalia context set <backend>` stores one active backend in project
  configuration.

Context is derived, regenerable memory. It does not replace formal evidence or
participate in close policy.

## sync, skills, and update

- `sync` propagates `AGENTS.md` and compatible formats through `rulesync`.
- `skills` manages skill sources, versions, activation, and updates.
- `update` updates orchestrated tools and skills; it neither installs a new PyPI
  package version nor publishes documentation.

## mcp — level-1 façade

`tramalia mcp` exposes tools such as `project_status`, `get_agent_rules`,
`get_failed_attempts`, `get_current_task`, `doctor`, `record_handoff`,
`build_evidence`, and `build_context`:

```json
{
  "mcpServers": {
    "tramalia": {"command": "tramalia", "args": ["mcp"]}
  }
}
```

`record_handoff` keeps its interoperable name but records a canonical transfer
and projects `docs/ai/07-traspaso-agentes.md`.
