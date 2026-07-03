<div align="center">

# 🧩 Tramalia

**Gobierno y evidencia verificable para desarrollar con múltiples agentes IA. Repo-first.**

*Define las reglas del proyecto, ordena la colaboración entre agentes, valida cada cambio y deja un registro verificable — versionado en el repo.*

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)
![Tests](https://img.shields.io/badge/tests-52%20passing-brightgreen.svg)

**Español** · [English](README.md) · [📚 Documentación](https://MscottB.github.io/tramalia/)

</div>

---

> **Git gobierna la colaboración humana; Tramalia gobierna la colaboración agéntica.** Es el control de cambios + pista de auditoría para cuando varios agentes IA trabajan un proyecto real: reglas comunes, validaciones obligatorias y evidencia verificable de cada cierre.

## Tabla de contenidos

- [¿Qué es?](#qué-es)
- [Definición](#definición)
- [Características](#características)
- [Instalación rápida](#instalación-rápida)
- [Uso](#uso)
- [Tramalia sola o con tus herramientas](#tramalia-sola-o-con-tus-herramientas)
- [Cómo funciona](#cómo-funciona)
- [Comparación con el ecosistema](#comparación-con-el-ecosistema)
- [Requisitos](#requisitos)
- [Documentación](#documentación)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

## ¿Qué es?

Cuando trabajas un proyecto con varios agentes IA (Claude Code, Codex, Cursor, Antigravity…), cada uno pierde contexto entre sesiones, usa sus propias reglas y **no deja evidencia de lo que hizo**. Tramalia resuelve esto usando **el repositorio como fuente de verdad**: deja una convención versionada que *cualquier* agente lee, y asegura que el trabajo se haga de forma **controlada, trazable y consistente**.

Su foco **no** es configurar tus agentes (eso lo hacen Gentle-AI y similares) ni ser un motor de memoria (eso es Engram). Su foco es **gobernar el repo**: reglas, gates, evidencia y handoff.

## Definición

> **Tramalia es una capa repo-first de gobierno y evidencia para desarrollo con múltiples agentes IA.** Su objetivo no es configurar agentes ni reemplazar motores de memoria, sino asegurar que cualquier agente que intervenga un proyecto trabaje bajo las mismas reglas, ejecute validaciones, documente sus decisiones, deje evidencia verificable y entregue un handoff claro para la siguiente sesión o revisor.

Lo hace **orquestando herramientas externas** en vez de reimplementarlas.

## Características

- **Cierre gobernado (`close`)** — corre los gates, escribe sus salidas en el **evidence pack** y genera el **handoff** (enlazado) en un solo paso; **bloquea el cierre si un gate falla** (salvo excepción documentada).
- **Pista de auditoría (`log`)** — historial verificable de cierres: qué tarea, qué gates pasaron, qué evidencia.
- **Dashboard TUI (`ui`)** — panel en terminal con Resumen, Auditoría navegable y Cierre guiado (extra `[tui]`, Textual).
- **Quality gates** — build, test, lint, seguridad, base de datos y UX/UI.
- **Convención completa** — `AGENTS.md` único + `docs/ai/` 00–11 + `specs/` + **13 skills** numeradas ancladas al flujo + intentos fallidos + handoff tipado.
- **Subagentes por rol con ruteo de modelo** — `.claude/agents/` trae 5 roles de gobierno (planificador→opus, ejecutor→inherit, revisor→opus, documentador→haiku, resolutor-profundo→fable); `sync` los propaga a otros hosts y `close --model` registra qué modelo cerró cada tarea.
- **`doctor`** — diagnostica qué herramientas necesita *tu* proyecto y cómo instalarlas (incluye Spec Kit).
- **Ahorro de tokens** *(interop)* — contexto derivado (Repomix) + navegación semántica (Serena).
- **Fan-out de reglas** *(interop)* — propaga `AGENTS.md` a Cursor/Copilot/… con rulesync.
- **Fachada MCP** + **memoria N2 opcional** (Engram) — expone/persiste sin reinventar.

## Instalación rápida

```bash
pip install -e ".[pretty]"   # solo requiere Python 3.10+
tramalia init                # genera la convención en tu repo
tramalia doctor              # te dice qué más instalar
```

## Uso

```bash
tramalia menu        # menú interactivo en bucle, con prompts guiados
tramalia ui          # dashboard TUI (Resumen · Auditoría · Cierre)
tramalia init        # genera la convención (AGENTS.md, docs/ai 00-11, specs, 13 skills…)
tramalia doctor      # diagnostica herramientas (y cómo instalarlas)
tramalia close       # cierra una tarea: gates → evidence → handoff (con enforcement)
tramalia log         # pista de auditoría de los cierres
tramalia gates       # corre los quality gates
tramalia sync        # propaga AGENTS.md a otros agentes (interop, rulesync)
tramalia update      # actualiza todo (mise + skills)
```

Extras opcionales de `init`: `--with-headroom` (compresión) y `--with-ponytail` (MCP del ruleset de minimalismo, tras `tramalia skills`).

## Tramalia sola o con tus herramientas

El **núcleo de gobierno funciona standalone**, solo con Python: `init`, `doctor`, `close`, `log`, `evidence`, `handoff` y las reglas/`docs/ai`. No necesita nada más para gobernar el repo.

Las herramientas externas son **interoperabilidad opcional**, no requisitos: `mise` (corre los gates), Repomix/Serena/codebase-memory-mcp (contexto), rulesync (fan-out), **Engram** (memoria N2), **Headroom** (compresión). Si no están, Tramalia sigue gobernando y lo registra como excepción documentada.

## Cómo funciona

Tres capas:

1. **El CLI fino** (lo que ejecutas) — una cara única que hace *shell-out* a las herramientas reales.
2. **La convención** (lo que queda en tu repo) — `AGENTS.md`, `docs/ai/`, `mise.toml`… El valor real.
3. **Lo externo** (se actualiza desde sus repos) — mise, Serena, Repomix, Semgrep, rulesync, los agentes.

## Comparación con el ecosistema

No compiten de frente; se complementan. Cada uno ocupa un espacio distinto:

| Proyecto | Rol |
|---|---|
| **Gentle-AI** | prepara el ecosistema de agentes: modelos, skills, memoria, perfiles, configuración |
| **Engram** | aporta memoria persistente entre sesiones |
| **Headroom** | comprime contexto y outputs para ahorrar tokens |
| **Serena · Repomix · codebase-memory-mcp** | inteligencia de código / contexto (navegación, snapshot, grafo estructural) |
| **Tramalia** | **gobierna el trabajo dentro del repo: reglas, gates, evidencia, handoff, auditoría e intentos fallidos** |

En conjunto: **Gentle-AI** habilita *con qué* agentes trabajar, **Engram** ayuda a *recordar*, **Headroom** *abarata* el contexto, **Serena/Repomix/codebase-memory-mcp** dan *inteligencia de código*, y **Tramalia** asegura que el repo se mantenga **controlado, trazable y consistente**. Todas son interop opcional; ninguna toca el núcleo de Tramalia (`close`, `log`, evidence pack, handoff). Detalle en la [página de ecosistema](docs/ecosistema.md).

## Requisitos

- **Tramalia: solo Python 3.10+** (sin dependencias Node).
- **Recomendado:** `mise`, `git`, `uv` (bootstrap que instala el resto).
- **Node 18+** solo si usas `sync`, el gate `ux` o `context` con Repomix. `tramalia doctor` lo marca como "requiere Node".

Tabla completa en el [Manual de usuario](MANUAL_DE_USUARIO.md#parte-2--instalación-y-requisitos).

## Documentación

- **Sitio (ES/EN):** https://MscottB.github.io/tramalia/ — visual, con diagramas
  - **[Ejemplo completo](docs/ejemplo-completo.md)** — un proyecto real de punta a punta, con cada opción y cada herramienta de terceros en acción
  - [Ecosistema](docs/ecosistema.md) · [Flujo completo](docs/flujo-completo.md) · [Arquitectura](docs/arquitectura.md) · [Integraciones](docs/interop.md) · [Herramientas](docs/herramientas.md)
- [Manual de usuario](MANUAL_DE_USUARIO.md)
- [Documento de diseño consolidado](Tramalia_Diseno_Consolidado_v0_6.md)

## Contribuir

Las contribuciones son bienvenidas. Lee la [guía de contribución](CONTRIBUTING.md): abre un issue para cambios grandes; para cambios chicos, un PR directo. Ejecuta los tests con `pip install -e ".[dev]" && pytest`.

## Licencia

**Apache-2.0** © 2026 Michael Jim Scott Bravo — ver [`LICENSE`](LICENSE). Análisis de licencias del ecosistema (y por qué las copyleft de las tools externas no afectan a Tramalia): [`LICENSES.md`](LICENSES.md).
