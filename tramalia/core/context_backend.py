"""Backend de navegación de código: cuál usar cuando hay varios instalados.

Serena/CodeGraph/codebase-memory-mcp/Graphify compiten por el mismo rol —
"qué leo para entender el código" — y un proyecto debe tener UNO activo para
que los agentes no alternen entre índices inconsistentes dentro del mismo repo.

Repomix (snapshot puntual) y markitdown (ingesta de documentos) NO compiten:
son utilidades que se usan cuando corresponde, no backends de navegación.
"""

from __future__ import annotations

BACKENDS: dict[str, dict[str, str]] = {
    "serena": {
        "tool": "serena",
        "label": "Serena — navegación semántica viva",
        "scope": "Lee solo el símbolo exacto que se va a tocar (LSP). Sin índice previo, sin huella en disco.",
        "ideal": "Default recomendado: cualquier proyecto, sobre todo si el código cambia seguido y no quieres mantener un índice aparte.",
    },
    "codegraph": {
        "tool": "codegraph",
        "label": "CodeGraph — grafo pre-indexado con auto-sync",
        "scope": "Índice SQLite con file-watchers; responde impacto (\"qué rompo si toco X\") en una sola llamada.",
        "ideal": "Repos grandes en un lenguaje principal (20+ soportados) donde trabajas a diario y quieres la respuesta quirúrgica de inmediato.",
    },
    "codebase-memory-mcp": {
        "tool": "codebase-memory-mcp",
        "label": "codebase-memory-mcp — grafo estructural políglota",
        "scope": "Grafo persistente vía LSP híbrido + tree-sitter (158 lenguajes); get_architecture, call graphs.",
        "ideal": "Repos políglotas o con lenguajes poco comunes, o cuando necesitas vistas de arquitectura además de impacto.",
    },
    "graphify": {
        "tool": "graphify",
        "label": "Graphify — grafo de conocimiento multi-formato",
        "scope": "Une código + docs + SQL + schemas en un grafo consultable único (CLI + MCP + skill).",
        "ideal": "Cuando el valor está en cruzar código con documentación/esquemas, no solo en analizar impacto de código puro.",
    },
}
DEFAULT = "serena"

# utilidades puntuales: no compiten por el rol de backend, coexisten con cualquiera.
UTILITIES: dict[str, dict[str, str]] = {
    "repomix": {
        "tool": "repomix",
        "label": "Repomix — snapshot empaquetado",
        "scope": "Empaqueta el repo completo en un archivo para IA. Foto puntual, no navegación continua.",
        "ideal": "Cuando necesitas dar TODO el contexto de una vez (ej. onboarding de un agente nuevo).",
    },
    "markitdown": {
        "tool": "markitdown",
        "label": "markitdown — ingesta de documentos",
        "scope": "Convierte PDF/Word/Excel/imágenes a Markdown. No navega código: trae al contexto lo que vive en documentos.",
        "ideal": "Cuando el conocimiento del proyecto vive en documentos, no en código.",
    },
}
