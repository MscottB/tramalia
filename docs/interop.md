# Integraciones: cómo encaja todo

Tramalia **no reimplementa** las herramientas del ecosistema: las **detecta, cablea e invoca** como programas separados. Esta sección explica, herramienta por herramienta, **qué es, cómo se instala, qué requiere y cómo interactúa** con Tramalia y con las demás.

## Qué requiere Tramalia (y qué requiere cada herramienta)

| | Requisito | Notas |
|---|---|---|
| **Tramalia (núcleo)** | **solo Python 3.10+** | `init`, `doctor`, `close`, `log`, `evidence`, `handoff` corren sin nada más |
| Modo bonito | `rich`, `questionary` | extra `pip install ".[pretty]"` |
| Fachada MCP | `mcp` (SDK) | extra `pip install ".[mcp]"` |
| **Cada herramienta externa** | su propio runtime | binario, Python o **Node** — `doctor` te lo dice por proyecto |

> Regla de oro: el **núcleo gobierna con solo Python**. Las herramientas externas son **interop opcional**; si faltan, Tramalia sigue gobernando y lo registra como excepción documentada.

## El modelo de integración en 4 pasos

```mermaid
flowchart LR
    classDef s fill:#eef0ff,stroke:#8a83e0,color:#26215c;
    D["1 · tramalia detect<br/><small>qué stack hay</small>"]:::s --> O["2 · tramalia doctor<br/><small>qué falta y cómo instalarlo</small>"]:::s
    O --> I["3 · mise install<br/><small>trae lo declarado</small>"]:::s
    I --> C["4 · cableado<br/><small>mise.toml · .mcp.json</small>"]:::s
```

1. **`detect`** identifica el stack → decide qué gates/herramientas aplican.
2. **`doctor`** clasifica cada herramienta (**bootstrap** / **stack** / **feature**) y muestra el comando exacto de instalación.
3. **`mise install`** trae todo lo declarado en `mise.toml` (la mayoría).
4. Tramalia las **cablea**: comandos en `mise.toml` (gates), servidores en `.mcp.json` (Serena/Engram/…).

## Cómo se instala cada herramienta (dos vías)

La mayoría se instala de **dos formas equivalentes**: directa (su instalador oficial) o **vía mise** (recomendado, queda declarado y se auto-actualiza):

- **Vía mise (recomendado):** `mise use npm:repomix`, `mise use pipx:semgrep`, etc. Queda en `mise.toml` y `mise upgrade` la mantiene.
- **Directa:** el instalador oficial de cada una (npm, pip, brew, binario…).

`tramalia doctor` siempre muestra la vía recomendada para *tu* proyecto.

## Cómo interactúan entre sí (a través de Tramalia)

```mermaid
flowchart TB
    classDef core fill:#5b4bdb,stroke:#3c3489,color:#fff;
    classDef ext fill:#fff,stroke:#b4b2a9,color:#444;

    AG["🤖 Agente IA"]:::ext
    SR["Serena<br/><small>decide qué leer</small>"]:::ext
    RP["Repomix / codebase-memory-mcp<br/><small>arma el mapa</small>"]:::ext
    HR["Headroom<br/><small>comprime lo leído</small>"]:::ext
    MI["mise<br/><small>corre los gates</small>"]:::ext
    EN["Engram<br/><small>recuerda</small>"]:::ext
    T["🧩 TRAMALIA<br/><small>registra qué se hizo, qué se validó, qué evidencia queda</small>"]:::core

    AG -->|navega| SR
    SR -->|símbolos| RP
    RP -->|contexto| HR
    HR -->|menos tokens| AG
    AG -->|cierra tarea| T
    T -->|mise run gates| MI
    MI -->|salida cruda| T
    T -->|export opt-in| EN
```

En palabras: **Serena** decide qué leer, **Repomix/codebase-memory-mcp** arman el mapa, **Headroom** comprime, **mise** corre los gates, **Engram** recuerda — y **Tramalia** registra qué se hizo, qué se validó y qué evidencia queda. Cada actor hace lo suyo; Tramalia los gobierna.

## Las páginas de detalle

- [Ejecución y gates](interop-ejecucion.md) — mise, git, uv, Semgrep, Gitleaks, SQLFluff, Lighthouse, Playwright, axe.
- [Contexto e inteligencia de código](interop-contexto.md) — Repomix, Serena, codebase-memory-mcp.
- [Memoria y eficiencia](interop-memoria.md) — Engram, basic-memory, mem0, Headroom.
- [Reglas, skills y agentes](interop-agentes.md) — rulesync, copier, Spec Kit, Gentle-AI, agentes IA.
