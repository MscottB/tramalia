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

!!! tip "¿Necesito Node?"
    Solo si usas `sync`, el gate `ux` o `context` con Repomix. En un proyecto sin frontend y sin `sync`, **nunca** necesitas Node. `tramalia doctor` marca esas filas como "requiere Node".

## Orden recomendado

```bash
pip install "tramalia-cli[pretty,mcp]"   # 1. Tramalia
# 2. Instala mise, git, uv (bootstrap; doctor te da el enlace)
tramalia init                            # 3. genera la convención
mise install                             #    mise instala lo declarado
mise use node@22                         # 4. solo si usarás sync / ux / repomix
tramalia doctor                          # 5. verifica que no falte nada
```
