# Instalación y requisitos

## Para correr Tramalia: solo Python, un solo comando

Tramalia **solo requiere Python 3.10+**. No tiene ninguna dependencia Node.

```bash
pip install tramalia-cli
```

Eso es todo: incluye el CLI con colores y menú interactivo (Rich + Questionary, puras-Python y diminutas). Las dos piezas opcionales más pesadas — el **dashboard TUI** (`tramalia ui`) y la **fachada MCP** (`tramalia mcp`) — **se ofrecen a instalar solas la primera vez que las usas**:

```text
$ tramalia ui
▲ el dashboard TUI requiere 'textual' (no está instalado).
? ¿instalar 'textual' ahora? [S/n]
```

!!! note "Para expertos"
    Si prefieres todo de una: `pip install "tramalia-cli[full]"` (agrega Textual + SDK MCP).
    En entornos gestionados (Ubuntu 23+, Homebrew, pipx) donde pip directo está
    bloqueado, la oferta automática te mostrará el comando manual
    (`pipx inject tramalia-cli textual`).

!!! info "¿Vas a contribuir al proyecto?"
    Clona el repo e instala en modo editable: `pip install -e ".[dev]"`. Ver la
    [guía de contribución](https://github.com/MscottB/tramalia/blob/main/CONTRIBUTING.md).

## Para una buena experiencia: herramientas externas

Tramalia **orquesta** herramientas externas. No las necesitas todas para empezar; `tramalia doctor` te dice cuáles faltan para *tu* proyecto. Importante: **algunas son Node**, no Python.

| Herramienta | Para qué | Runtime | ¿Obligatoria? |
|---|---|---|---|
| **Python 3.10+** | correr Tramalia | — | **sí** |
| **mise** | instala/versiona el resto + corre gates | binario | recomendada |
| **git** | memoria versionada, skills, evidence | binario | recomendada |
| **uv** | instala tools Python (copier, serena) | binario | recomendada |
| **Node 18+** | `sync`, gate `ux`, `context` (repomix) | — | si usas esas features |
| rich · questionary | CLI interactiva y con color | Python | **incluidas por defecto** |
| semgrep · gitleaks | gate seguridad | Python/binario | opcional |
| sqlfluff | gate base de datos | Python | opcional |
| **repomix** | snapshot de contexto | **Node** | opcional |
| **rulesync** | fan-out de reglas (`sync`) | **Node** | opcional |
| **lighthouse · playwright** | gate UX/UI | **Node** | opcional |
| **engram** | memoria persistente N2 (`--engram`) | binario | opcional (interop) |
| **headroom** | compresión de contexto/outputs (token-saver) | — | opcional (interop) |
| **specify** (Spec Kit) | spec-driven development (`specs/`) | Python | opcional (interop) |
| **ponytail** | ruleset de minimalismo + MCP (`--with-ponytail`) | **Node** (MCP) | opcional (interop) |
| **markitdown** | ingesta: PDF/Office/imágenes → Markdown (contexto) | Python | opcional (interop) |
| **databricks CLI** | `bundle validate` en proyectos de analítica | binario | solo si detecta `databricks.yml` |

!!! tip "¿Vas a usar el idioma inglés?"
    La interfaz (`tramalia ui` y el CLI) detecta tu idioma automáticamente (locale del sistema). Para forzarlo: `TRAMALIA_LANG=en` o `"language": "en"` en `.tramalia/config.json`. Ver [La interfaz (TUI)](interfaz.md#idioma).

!!! tip "¿Necesito Node?"
    Solo si usas `sync`, el gate `ux` o `context` con Repomix. En un proyecto sin frontend y sin `sync`, **nunca** necesitas Node. `tramalia doctor` marca esas filas como "requiere Node".

!!! tip "Node y Go se pueden instalar SOLOS"
    Si una herramienta solo se automatiza con un runtime que te falta (npm → **Node**; `go install` → **Go**, p. ej. engram), el selector de instalación (tecla `i` en la TUI, o `doctor --fix`) **ofrece instalar ese runtime primero** — lo instalas, repites la instalación, y la herramienta pasa a automatizable. Node y Go son instalables por winget/brew igual que el resto. Detalle: [Ayuda → prerequisitos de runtime](ayuda.md#instalacion-y-doctor).

## Instalación automatizada por sistema

`tramalia doctor --fix` (y la tecla `i` en `tramalia ui`) **detectan tu sistema y qué gestores tienes** (winget/brew/choco/scoop, mise, uv, npm) y te dejan **seleccionar una o más** herramientas para instalar automatizado — cada una por su mejor vía disponible:

| Herramienta | Windows | macOS | Linux |
|---|---|---|---|
| **mise** | `winget install jdx.mise` ✓ verificado | `brew install mise` | `curl https://mise.run \| sh` (manual) |
| **git** | `winget install Git.Git` | `brew install git` | gestor de tu distro |
| **uv** | `winget install astral-sh.uv` | `brew install uv` | script oficial (manual) |
| **node** | `winget install OpenJS.NodeJS.LTS` | `brew install node` | `mise use node@22` |
| gates/features | vía **mise** si está; si no, **uv** (`pipx:`) o **npm** (`npm:`, solo con Node presente) | ídem | ídem |

Reglas del instalador: los `curl | sh` **nunca** se ejecutan automatizados (solo se muestran); las opciones **npm** solo aparecen si Node/npm está presente (verificador incluido); en Windows, para mise **winget es la vía verificada** — choco y scoop se listan como alternativa manual.

!!! note "Instalé con mise y doctor no la ve"
    Las herramientas que instala mise viven tras sus **shims**: hasta que actives mise (`mise activate` en tu shell) o reinicies la terminal, no están en el PATH. `doctor` ahora las detecta igual (consulta `mise which`) y te lo indica: *"instalada vía mise (shims)"*.

## Orden recomendado

```bash
pip install tramalia-cli                 # 1. Tramalia
tramalia init                            # 2. genera la convención
tramalia doctor --fix                    # 3. selecciona e instala lo que falte
mise use node@22                         # 4. solo si usarás sync / ux / repomix
tramalia doctor                          # 5. verifica que no falte nada
```

## Actualizar

- **Tramalia (el CLI):** `pip install -U tramalia-cli` — el mismo comando de instalación con `-U`. Verifica con `tramalia --version`.
- **Lo que Tramalia orquesta** (tools de mise + skills externas): `tramalia update`. Son cosas distintas: `update` no toca el propio paquete.
