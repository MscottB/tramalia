# Arquitectura

Tramalia es una **capa fina** con una regla de oro: *no implementa capacidades, las orquesta*. Solo construye lo que nadie más hace bien (gobierno, evidencia, handoff). Todo lo demás se delega.

## Principio guía: Ponytail / YAGNI

La filosofía de Tramalia es el **minimalismo**: hacer lo mínimo correcto y no reconstruir lo que ya existe. Esto sigue el principio [Ponytail](https://github.com/DietrichGebert/ponytail) (y YAGNI). No es una herramienta que se instale: es una **regla que se lee y se sigue**.

Por eso `tramalia init` lo deja escrito en el `AGENTS.md` de tu proyecto (sección *Reglas generales — Ponytail / YAGNI*), para que **cualquier agente** que trabaje el repo priorice la solución mínima, no abstraiga de más y no duplique lógica. Si lo prefieres como skill versionada, está como ejemplo en `.tramalia/skills.toml`.

## Las tres capas

```mermaid
flowchart TB
    classDef core fill:#5b4bdb,stroke:#3c3489,color:#fff;
    classDef conv fill:#eef0ff,stroke:#8a83e0,color:#26215c;
    classDef ext fill:#fff,stroke:#b4b2a9,color:#444;

    subgraph C1["Capa 1 · CLI fino (lo que ejecutas)"]
        CLI["init · doctor · close · log · evidence · handoff · gates · context · sync · mcp"]:::core
    end
    subgraph C2["Capa 2 · Convención (lo que queda en tu repo)"]
        CONV["AGENTS.md · docs/ai/ · mise.toml · .mcp.json · .tramalia/evidence"]:::conv
    end
    subgraph C3["Capa 3 · Externo (se actualiza desde sus repos)"]
        EXT["mise · Serena · Repomix · Semgrep · rulesync · Engram · Headroom · agentes"]:::ext
    end
    C1 -->|init genera| C2
    C2 -->|leen| C3
    C3 -->|corren / consultan| C1
```

1. **CLI fino** — una sola cara que hace *shell-out* transparente a las herramientas reales. Nunca esconde errores; siempre se puede saltar (llamar a `mise`/`serena` directo).
2. **Convención** — archivos versionados, fuente de verdad del proyecto. **El valor real.**
3. **Externo** — herramientas completas y los agentes, que se actualizan desde sus repos.

## Núcleo vs. interop

La distinción más importante del diseño: qué es **core** (propio, standalone, solo Python) y qué es **interop** (externo, opcional, degrada con gracia).

=== "Núcleo (core)"

    Funciona **solo con Python**, sin depender de nada externo.

    - `init` — genera la convención
    - `doctor` — diagnostica
    - `detect` — detecta el stack
    - **`close`** — el ritual de cierre con enforcement
    - **`log`** — la pista de auditoría
    - `evidence` · `handoff` — las piezas de trazabilidad
    - `mcp` — la fachada MCP

=== "Interop (opcional)"

    Delega en herramientas externas; si faltan, lo registra como excepción documentada.

    - `gates` → **mise**
    - `context` → **Repomix / Serena / codebase-memory-mcp**
    - `sync` → **rulesync**
    - `skills` → **git**
    - `update` → **mise + copier**
    - memoria N2 → **Engram**
    - compresión → **Headroom** (opt-in)

## El modelo "manifiesto + actualizador"

Tramalia no copia el código de nadie. Lo **referencia** y un comando lo mantiene al día:

```mermaid
flowchart LR
    classDef step fill:#eef0ff,stroke:#8a83e0,color:#26215c;
    U["tramalia update"]:::step --> A["mise upgrade<br/><small>tools externas</small>"]:::step
    U --> B["copier update<br/><small>la convención</small>"]:::step
    U --> C["skills sync<br/><small>skills referenciadas</small>"]:::step
```

## La fachada MCP (nivel 1)

`tramalia mcp` expone el mismo core como herramientas MCP nativas (`project_status`, `get_agent_rules`, `get_failed_attempts`, `record_handoff`, `build_evidence`…), para que un agente las use sin shell-out. Es una **fachada delgada**, no un motor nuevo. Los 3 niveles de memoria:

- **N0** — archivos + CLI (empieza aquí, sin MCP).
- **N1** — esta fachada (si quieres tool nativa).
- **N2** — montar **Engram** / basic-memory / mem0 (memoria persistente seria).

## Invariante del moat

> Los `*-output.txt` crudos y `metadata.json` son la evidencia **oficial**. Ningún artefacto derivado (compresión de Headroom, `review-summary.md`) puede modificarlos, reemplazarlos ni omitirlos — solo agregar archivos auxiliares marcados como derivados.

Esta regla está en el código (`core/governance.py`), en un test (`test_close_conserva_salidas_crudas`) y aquí. Es lo que protege la auditabilidad cuando se suma eficiencia.
