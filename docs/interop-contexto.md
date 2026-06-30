# Contexto e inteligencia de código

Estas herramientas ayudan al agente a **entender el código sin leerlo entero** (ahorro de tokens). Tramalia las orquesta desde `tramalia context` y/o las cablea como servidores MCP.

```mermaid
flowchart LR
    classDef s fill:#eef0ff,stroke:#8a83e0,color:#26215c;
    SR["Serena<br/><small>decide qué leer (símbolos)</small>"]:::s --> RP["Repomix / codebase-memory-mcp<br/><small>arman el mapa/grafo</small>"]:::s
    RP --> CTX[".tramalia/context/<br/><small>memoria derivada</small>"]:::s
```

## Repomix — snapshot empaquetado

- **Qué es / alcance:** empaqueta el repo en un único archivo amigable para IA (snapshot).
- **Requiere:** **Node**.
- **Instalar:** `mise use npm:repomix` · directa: `npm i -g repomix` · sin instalar: `npx repomix`.
- **Tramalia la usa en:** `context` — si está, genera el snapshot; si no, Tramalia cae a un árbol stdlib.
- **Interactúa con:** alimenta `.tramalia/context/`; complementa a Serena (snapshot vs. navegación viva).

## Serena — navegación semántica viva (MCP)

- **Qué es / alcance:** toolkit MCP que usa *language servers* (LSP) para que el agente lea solo el **símbolo exacto** que va a tocar — navegación quirúrgica, siempre fresca.
- **Requiere:** **uv** + Python (se ejecuta vía `uvx`, no requiere instalación global).
- **Instalar / cablear:** `tramalia init` ya la deja en `.mcp.json`:
  ```json
  "serena": { "command": "uvx",
    "args": ["--from","git+https://github.com/oraios/serena","serena","start-mcp-server"] }
  ```
- **Tramalia la usa en:** la cablea en `.mcp.json`; el **agente** la consume por MCP. No la invoca el CLI directamente.
- **Interactúa con:** decide *qué leer* antes de que Repomix/codebase-memory armen contexto; reduce tokens en el trabajo vivo.

## codebase-memory-mcp — grafo estructural del código (MCP)

- **Qué es / alcance:** indexa el código en un **grafo de conocimiento persistente** (158 lenguajes, LSP híbrido + tree-sitter): `get_architecture`, call graphs, análisis de impacto. ~99% menos tokens que leer archivo por archivo. Alternativa más potente a Serena/Repomix como backend de contexto.
- **Requiere:** nada (binario estático, C/C++).
- **Instalar:** binario de los *releases* del repo. **Importante:** usar `--skip-config` para que **no** configure agentes ni escriba instrucciones por fuera de Tramalia.
- **Tramalia la usa en:** backend opcional de `context` / servidor MCP de consulta.
- **Interactúa con / cuidado:** **solo sus tools de consulta**. Su `manage_adr` y su auto-configuración de agentes **no** deben usarse: los ADR viven en `docs/ai/05` y las reglas en `AGENTS.md` (gobierno de Tramalia).

## Cómo encajan los tres

- **Serena** = *qué* leer (símbolos, vivo).
- **Repomix** = *snapshot* completo cuando se necesita una foto.
- **codebase-memory-mcp** = *grafo estructural* persistente (arquitectura, impacto).

Tramalia no compite con ellos: los declara, los detecta (`doctor`) y consume su salida en `.tramalia/context/` o vía MCP. Tú eliges cuál(es) montar.
