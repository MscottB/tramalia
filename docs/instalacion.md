# Instalación y requisitos

## Para correr Tramalia: solo Python

Tramalia **solo requiere Python 3.10+**. No tiene ninguna dependencia Node.

```bash
pip install -e .              # base (terminal básica, solo stdlib)
pip install -e ".[pretty]"    # modo bonito: Rich + Questionary (recomendado)
pip install -e ".[mcp]"       # fachada MCP
pip install -e ".[dev]"       # desarrollo (tests)
```

## Para una buena experiencia: herramientas externas

Tramalia **orquesta** herramientas externas. No las necesitas todas para empezar; `tramalia doctor` te dice cuáles faltan para *tu* proyecto. Importante: **algunas son Node**, no Python.

| Herramienta | Para qué | Runtime | ¿Obligatoria? |
|---|---|---|---|
| **Python 3.10+** | correr Tramalia | — | **sí** |
| **mise** | instala/versiona el resto + corre gates | binario | recomendada |
| **git** | memoria versionada, skills, evidence | binario | recomendada |
| **uv** | instala tools Python (copier, serena) | binario | recomendada |
| **Node 18+** | `sync`, gate `ux`, `context` (repomix) | — | si usas esas features |
| rich · questionary | CLI interactiva y con color | Python | opcional |
| semgrep · gitleaks | gate seguridad | Python/binario | opcional |
| sqlfluff | gate base de datos | Python | opcional |
| **repomix** | snapshot de contexto | **Node** | opcional |
| **rulesync** | fan-out de reglas (`sync`) | **Node** | opcional |
| **lighthouse · playwright** | gate UX/UI | **Node** | opcional |
| **engram** | memoria persistente N2 (`--engram`) | binario | opcional (interop) |
| **headroom** | compresión de contexto/outputs (token-saver) | — | opcional (interop) |

!!! tip "¿Necesito Node?"
    Solo si usas `sync`, el gate `ux` o `context` con Repomix. En un proyecto sin frontend y sin `sync`, **nunca** necesitas Node. `tramalia doctor` marca esas filas como "requiere Node".

## Orden recomendado

```bash
pip install -e ".[pretty,mcp]"   # 1. Tramalia
# 2. Instala mise, git, uv (bootstrap; doctor te da el enlace)
tramalia init                    # 3. genera la convención
mise install                     #    mise instala lo declarado
mise use node@22                 # 4. solo si usarás sync / ux / repomix
tramalia doctor                  # 5. verifica que no falte nada
```
