# Tramalia

**Gobierno y evidencia verificable para desarrollar con múltiples agentes IA. Repo-first.**

!!! quote ""
    **Git gobierna la colaboración humana; Tramalia gobierna la colaboración agéntica.** Es el control de cambios + pista de auditoría para cuando varios agentes IA trabajan un proyecto real: reglas comunes, validaciones obligatorias y evidencia verificable de cada cierre.

Tramalia es una **capa repo-first** que asegura que *cualquier* agente (Claude Code, Codex, Cursor, Antigravity…) que intervenga el proyecto trabaje bajo las mismas reglas, ejecute validaciones, documente sus decisiones, deje evidencia verificable y entregue un handoff claro. Lo hace **orquestando herramientas externas** en vez de reimplementarlas.

<div class="grid cards" markdown>

-   :material-gavel:{ .lg .middle } __Gobierno repo-first__

    ---

    Reglas comunes (`AGENTS.md`), gates obligatorios y enforcement en el cierre. Todo versionado en el repo, no escondido en configs globales.

    [:octicons-arrow-right-24: Arquitectura](arquitectura.md)

-   :material-clipboard-check:{ .lg .middle } __Evidencia y auditoría__

    ---

    `close` deja un evidence pack con salidas crudas + `metadata.json`; `log` es la pista de auditoría verificable de todo el trabajo agéntico.

    [:octicons-arrow-right-24: Comandos](comandos.md)

-   :material-puzzle:{ .lg .middle } __Orquesta, no reimplementa__

    ---

    Delega en mise, Serena, Repomix, Semgrep, rulesync… El núcleo funciona standalone con solo Python; lo externo es interop opcional.

    [:octicons-arrow-right-24: Ecosistema](ecosistema.md)

-   :material-rocket-launch:{ .lg .middle } __Empieza en 3 comandos__

    ---

    `pip install`, `tramalia init`, `tramalia doctor`. Sin Node ni servicios cloud para gobernar tu repo.

    [:octicons-arrow-right-24: Instalación](instalacion.md)

</div>

## Tramalia en el centro del ecosistema

Tramalia no compite con las demás herramientas IA: las **gobierna y orquesta**. Cada una ocupa un espacio distinto; Tramalia es el núcleo que asegura control, trazabilidad y continuidad.

```mermaid
flowchart TD
    classDef core fill:#5b4bdb,stroke:#3c3489,color:#fff,stroke-width:2px;
    classDef sat fill:#eef0ff,stroke:#8a83e0,color:#26215c;
    classDef repo fill:#eaf0e0,stroke:#639922,color:#173404;

    T["🧩 TRAMALIA<br/><small>gobierno · gates · evidence · handoff · auditoría</small>"]:::core

    GA["Gentle-AI<br/><small>setup de agentes</small>"]:::sat
    EN["Engram<br/><small>memoria N2</small>"]:::sat
    HR["Headroom<br/><small>compresión</small>"]:::sat
    SR["Serena<br/><small>navegación semántica</small>"]:::sat
    RP["Repomix<br/><small>snapshot</small>"]:::sat
    CM["codebase-memory-mcp<br/><small>grafo de código</small>"]:::sat
    MI["mise<br/><small>tools + gates</small>"]:::sat
    RU["rulesync<br/><small>fan-out de reglas</small>"]:::sat

    GA -.onboarding.-> T
    EN -.memoria.-> T
    HR -.eficiencia.-> T
    SR -.contexto.-> T
    RP -.contexto.-> T
    CM -.contexto.-> T
    MI -.ejecución.-> T
    RU -.interop.-> T

    T ==> R["📁 Repo<br/><small>AGENTS.md · docs/ai · .tramalia/evidence</small>"]:::repo
    AG["🤖 Agentes IA<br/><small>Claude · Codex · Cursor · Antigravity</small>"]:::sat
    AG ==lee/escribe==> R
```

En una frase: **Gentle-AI** habilita *con qué* agentes trabajar, **Engram** ayuda a *recordar*, **Headroom** *abarata* el contexto, **Serena/Repomix/codebase-memory-mcp** dan *inteligencia de código*, y **Tramalia** asegura que el repo se mantenga **controlado, trazable y consistente**.

## Empieza aquí

<div class="grid cards" markdown>

- :material-download: [__Instalación y requisitos__](instalacion.md) — qué instalar y por qué (incluido cuándo necesitas Node).
- :material-sitemap: [__Flujo completo__](flujo-completo.md) — de `init` a `close`, paso a paso con ejemplos.
- :material-tools: [__Herramientas__](herramientas.md) — cada pieza interna y externa, su alcance y licencia.
- :material-vector-link: [__Integraciones__](interop.md) — cómo instalar e integrar cada herramienta con Tramalia.

</div>
