"""Describe providers that compete for the code-navigation capability."""

from __future__ import annotations

from tramalia.core.integraciones import REGISTRO, sondear
from tramalia.core.procesos import encontrar

PROVEEDORES: dict[str, dict[str, str]] = {
    "serena": {
        "herramienta": "serena",
        "etiqueta": "Serena — navegación semántica viva",
        "alcance": "Lee el símbolo exacto mediante LSP, sin índice persistente.",
        "ideal": "Proyectos que cambian seguido y no mantienen un índice separado.",
        "capacidad": "navegacion_codigo",
    },
    "codegraph": {
        "herramienta": "codegraph",
        "etiqueta": "CodeGraph — grafo pre-indexado",
        "alcance": "Índice SQLite con impacto y relaciones de código.",
        "ideal": "Repos grandes de un lenguaje principal usados a diario.",
        "capacidad": "navegacion_codigo",
    },
    "codebase-memory-mcp": {
        "herramienta": "codebase-memory-mcp",
        "etiqueta": "codebase-memory-mcp — grafo estructural políglota",
        "alcance": "Grafo persistente con LSP y tree-sitter.",
        "ideal": "Repos políglotas que requieren vistas de arquitectura.",
        "capacidad": "navegacion_codigo",
    },
    "graphify": {
        "herramienta": "graphify",
        "etiqueta": "Graphify — grafo multi-formato",
        "alcance": "Relaciona código, documentación, SQL y schemas.",
        "ideal": "Proyectos cuyo contexto cruza código y documentos.",
        "capacidad": "navegacion_codigo",
    },
}
PREDETERMINADO = "serena"
UTILIDADES: dict[str, dict[str, str]] = {
    "repomix": {
        "herramienta": "repomix",
        "etiqueta": "Repomix — snapshot empaquetado",
        "alcance": "Empaqueta el repositorio para una entrega puntual de contexto.",
        "ideal": "Onboarding o análisis que necesita el repositorio completo.",
    },
    "markitdown": {
        "herramienta": "markitdown",
        "etiqueta": "markitdown — ingesta documental",
        "alcance": "Convierte PDF, Office e imágenes a Markdown.",
        "ideal": "Conocimiento del proyecto que vive fuera del código.",
    },
}


def proveedor_disponible(nombre: str) -> bool:
    """Return whether a context provider can supply code navigation."""
    metadatos = PROVEEDORES.get(nombre)
    if metadatos is None:
        return False
    herramienta = next(
        (candidata for candidata in REGISTRO if candidata.clave == metadatos["herramienta"]),
        None,
    )
    return (
        sondear(herramienta).presente
        if herramienta
        else encontrar(metadatos["herramienta"]) is not None
    )
