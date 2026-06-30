<div align="center">

# 🧩 Tramalia

**Gobierno y evidencia verificable para desarrollar con múltiples agentes IA. Repo-first.**

*Define las reglas del proyecto, ordena la colaboración entre agentes, valida cada cambio y deja un registro verificable — versionado en el repo.*

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-34%20passing-brightgreen.svg)](#estado-y-roadmap)
[![Status](https://img.shields.io/badge/status-v0.6%20preview-orange.svg)](#estado-y-roadmap)
[![Sponsor](https://img.shields.io/badge/%E2%9D%A4-Sponsor-ea4aaa.svg)](.github/FUNDING.yml)

**Español** · [English](README.en.md) · [📚 Documentación](https://MscottB.github.io/tramalia/)

</div>

---

> **Git gobierna la colaboración humana; Tramalia gobierna la colaboración agéntica.** Es el control de cambios + pista de auditoría para cuando varios agentes IA trabajan un proyecto real: reglas comunes, validaciones obligatorias y evidencia verificable de cada cierre.

## ¿Qué es?

Cuando trabajas un proyecto con varios agentes IA (Claude Code, Codex, Cursor, Antigravity…), cada uno pierde contexto entre sesiones, usa sus propias reglas y **no deja evidencia de lo que hizo**. Tramalia resuelve esto usando **el repositorio como fuente de verdad**: deja una convención versionada que *cualquier* agente lee, y asegura que el trabajo se haga de forma **controlada, trazable y consistente**.

Su foco **no** es configurar tus agentes (eso lo hacen Gentle-AI y similares) ni ser un motor de memoria (eso es Engram). Su foco es **gobernar el repo**: reglas, gates, evidencia y handoff.

## ✨ Características

- 🏛️ **Cierre gobernado (`close`)** — corre los gates, escribe sus salidas en el **evidence pack** y genera el **handoff** en un solo paso; **bloquea el cierre si un gate falla** (salvo excepción documentada).
- 🧾 **Pista de auditoría (`log`)** — historial verificable de cierres: qué tarea, qué gates pasaron, qué evidencia.
- ✅ **Quality gates** — build, test, lint, seguridad, base de datos y **UX/UI**.
- 🧠 **Memoria del proyecto** — `AGENTS.md` único + `docs/ai/` + intentos fallidos + handoff tipado.
- 🩺 **`doctor`** — diagnostica qué herramientas necesita *tu* proyecto y cómo instalarlas.
- 🪙 **Ahorro de tokens** *(interop)* — contexto derivado (Repomix) + navegación semántica (Serena).
- 🔀 **Fan-out de reglas** *(interop)* — propaga `AGENTS.md` a Cursor/Copilot/… con rulesync.
- 🔌 **Fachada MCP** + **memoria N2 opcional** (Engram) — expone/persiste sin reinventar.

## 🚀 Instalación rápida

```bash
pip install -e ".[pretty]"   # solo requiere Python 3.10+
tramalia init                # genera la convención en tu repo
tramalia doctor              # te dice qué más instalar
```

## 🧭 Uso

```bash
tramalia menu        # menú interactivo
tramalia init        # genera la convención (AGENTS.md, docs/ai, mise.toml…)
tramalia doctor      # diagnostica herramientas (y cómo instalarlas)
tramalia close       # ★ cierra una tarea: gates → evidence → handoff (con enforcement)
tramalia log         # pista de auditoría de los cierres
tramalia gates       # corre los quality gates
tramalia sync        # propaga AGENTS.md a otros agentes (interop, rulesync)
tramalia update      # actualiza todo (mise + copier + skills)
```

## 🔌 Solo Tramalia, o con tus herramientas

El **núcleo de gobierno funciona standalone**, solo con Python: `init`, `doctor`, `close`, `log`, `evidence`, `handoff` y las reglas/`docs/ai`. No necesita nada más para gobernar el repo.

Las herramientas externas son **interoperabilidad opcional**, no requisitos: `mise` (corre los gates), Repomix/Serena/codebase-memory-mcp (contexto), rulesync (fan-out), **Engram** (memoria N2), **Headroom** (compresión). Si no están, Tramalia sigue gobernando y lo registra como excepción documentada. Así puedes trabajar **solo con Tramalia** o **combinándola** con todo el ecosistema.

## 🧱 Cómo funciona (3 capas)

1. **El CLI fino** (lo que ejecutas) — una cara única que hace *shell-out* a las herramientas reales.
2. **La convención** (lo que queda en tu repo) — `AGENTS.md`, `docs/ai/`, `mise.toml`… El valor real.
3. **Lo externo** (se actualiza desde sus repos) — mise, Serena, Repomix, Semgrep, rulesync, los agentes.

## 📋 Requisitos

- **Tramalia: solo Python 3.10+** (sin dependencias Node).
- **Recomendado:** `mise`, `git`, `uv` (bootstrap que instala el resto).
- **Node 18+** solo si usas `sync`, el gate `ux` o `context` con Repomix. `tramalia doctor` lo marca como "requiere Node".

Tabla completa en el [Manual de usuario](MANUAL_DE_USUARIO.md#parte-2--instalación-y-requisitos).

## 📚 Documentación

- 🌐 **Sitio (ES/EN):** https://MscottB.github.io/tramalia/ — visual, con diagramas
  - [Ecosistema](docs/ecosistema.md) (Tramalia en el centro) · [Flujo completo](docs/flujo-completo.md) · [Arquitectura](docs/arquitectura.md) · [Integraciones](docs/interop.md) · [Herramientas](docs/herramientas.md)
- 📖 [Manual de usuario](MANUAL_DE_USUARIO.md)
- 🧠 [Documento de diseño consolidado](Tramalia_Diseno_Consolidado_v0_6.md)

## 🎯 Definición

> **Tramalia es una capa repo-first de gobierno y evidencia para desarrollo con múltiples agentes IA.** Su objetivo no es configurar agentes ni reemplazar motores de memoria, sino asegurar que cualquier agente que intervenga un proyecto trabaje bajo las mismas reglas, ejecute validaciones, documente sus decisiones, deje evidencia verificable y entregue un handoff claro para la siguiente sesión o revisor.

Lo hace **orquestando herramientas externas** en vez de reimplementarlas.

## 🆚 Tramalia vs Gentle-AI / Engram / Headroom

No compiten de frente; se complementan. Cada uno ocupa un espacio distinto:

| Proyecto | Rol |
|---|---|
| **Gentle-AI** | prepara el ecosistema de agentes: modelos, skills, memoria, perfiles, configuración |
| **Engram** | aporta memoria persistente entre sesiones |
| **Headroom** | comprime contexto y outputs para ahorrar tokens |
| **Serena · Repomix · codebase-memory-mcp** | inteligencia de código / contexto (navegación, snapshot, grafo estructural) |
| **Tramalia** | **gobierna el trabajo dentro del repo: reglas, gates, evidencia, handoff, auditoría e intentos fallidos** |

En conjunto: **Gentle-AI** habilita *con qué* agentes trabajar, **Engram** ayuda a *recordar*, **Headroom** *abarata* el contexto, **Serena/Repomix/codebase-memory-mcp** dan *inteligencia de código*, y **Tramalia** asegura que el repo se mantenga **controlado, trazable y consistente**. Todas son interop opcional; ninguna toca el núcleo de Tramalia (`close`, `log`, evidence pack, handoff). En particular, **Headroom nunca reemplaza la evidencia**: el output crudo siempre se conserva en `.tramalia/evidence/`. Detalle en la [página de ecosistema](docs/ecosistema.md).

## 🗺️ Estado y roadmap

**Implementado en preview (v0.6)** — verificado con 34 tests de pytest:
`init`, `doctor`, `detect`, **`close`** (gates → evidence + `metadata.json` → handoff, con `status` honesto), **`log`**, `evidence`, `handoff`, `gates`, `context`, `sync`, `skills`, `update`, `mcp`, `menu`. Plantilla empaquetada en el wheel; sitio de docs bilingüe con diagramas; memoria N2 opcional vía **Engram**; `--with-headroom` opt-in.

**Siguiente / diseñado:** publicar `tramalia-template` para `copier update`; interop con **Headroom** (vista comprimida `review-summary.md` junto al output crudo, sin sustituir evidencia); comando `tramalia learn` para importar aprendizajes a `docs/ai/06-intentos-fallidos.md`.

## 🤝 Contribuir

Las contribuciones son bienvenidas. Abre un issue para discutir cambios grandes; para cambios chicos, un PR directo. Ejecuta los tests con `pip install -e ".[dev]" && pytest`.

## ❤ Licencia y donaciones

Licencia: **[Apache-2.0](LICENSE)** © 2026 Michael Jim Scott Bravo — permisiva, con concesión explícita de patentes. Las dependencias de Tramalia son todas MIT, plenamente compatibles.

**Donaciones:** se aceptan con cualquier licencia, vía GitHub Sponsors (configurable en [`.github/FUNDING.yml`](.github/FUNDING.yml)).

Análisis completo de licencias del ecosistema y por qué las copyleft de las tools externas no afectan a Tramalia: [LICENSES.md](LICENSES.md).
