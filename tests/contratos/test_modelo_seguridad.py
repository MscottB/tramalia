import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RUTA_MODELO = RAIZ / "docs" / "seguridad" / "modelo-amenazas.md"
RUTA_MATRIZ = RAIZ / "docs" / "seguridad" / "matriz-controles.md"

ENCABEZADOS_MODELO = (
    "## Activos protegidos",
    "## Actores y capacidades",
    "## Fronteras de confianza",
    "## Invariantes verificables",
    "## Casos de abuso",
    "## Riesgo residual y no objetivos",
)

ACTIVOS_OBLIGATORIOS = (
    "código y plantillas",
    "manifiestos y locks",
    "evidencia cruda",
    "credenciales del entorno",
    "configuración mcp",
    "historial git",
    "artefactos de release",
)

ACTORES_OBLIGATORIOS = (
    "autor del proyecto",
    "colaborador de pr",
    "repositorio git remoto",
    "autor de habilidad",
    "servidor mcp/proceso externo",
    "dependencia de build",
)

FRONTERAS_OBLIGATORIAS = (
    "entrada de repositorio a parser/configuración",
    "git remoto a cuarentena de habilidad",
    "cuarentena validada a directorio activo",
    "mcp/proceso a salida pública",
    "código de pr a runner de github actions",
    "herramienta descargada a ejecución local",
    "árbol fuente a documentación/artefacto publicado",
)

CONTROLES = {
    "TRM-SEC-001": "Confinar toda ruta y rechazar traversal/symlinks fuera de raíz",
    "TRM-SEC-002": "Ejecutar procesos sin shell, con timeout y salida acotada",
    "TRM-SEC-003": "Detectar secretos en historial y árbol de trabajo",
    "TRM-SEC-004": "Fijar y verificar herramientas/artefactos externos",
    "TRM-SEC-005": "Validar habilidades antes de hacerlas visibles",
    "TRM-SEC-006": "Evitar colisiones, scope creep y sobreexposición MCP",
    "TRM-SEC-007": "Mantener inventario, bloqueo y auditoría de cambios",
    "TRM-SEC-008": "Generar puertas locales reproducibles y fail-closed",
    "TRM-SEC-009": "Verificar accesibilidad y adaptabilidad WCAG 2.2 AA",
    "TRM-SEC-010": "Ejecutar CI de PR con privilegio mínimo y sin secretos",
}

REFERENCIAS = {
    "TRM-SEC-001": ("Top 10 2025", "ASVS 5.0.0"),
    "TRM-SEC-002": ("ASVS v5.0.0-1.2.5", "MCP05"),
    "TRM-SEC-003": ("Top 10 2025", "MCP01"),
    "TRM-SEC-004": ("Top 10 2025", "AST02/AST07", "MCP04"),
    "TRM-SEC-005": ("AST01/AST03/AST04/AST05/AST06/AST08",),
    "TRM-SEC-006": ("MCP02/MCP03/MCP07/MCP09/MCP10",),
    "TRM-SEC-007": ("AST09/AST10", "MCP08"),
    "TRM-SEC-008": ("ASVS 5.0.0", "API Security Top 10 2023"),
    "TRM-SEC-009": ("WCAG 2.2", "calidad UX/UI"),
    "TRM-SEC-010": ("Top 10 2025", "AST02", "MCP04"),
}

ESTADOS_INICIALES = {
    "TRM-SEC-001": "pendiente_bloqueante",
    "TRM-SEC-002": "parcial",
    "TRM-SEC-003": "pendiente_bloqueante",
    "TRM-SEC-004": "pendiente_bloqueante",
    "TRM-SEC-005": "pendiente_bloqueante",
    "TRM-SEC-006": "pendiente_bloqueante",
    "TRM-SEC-007": "parcial",
    "TRM-SEC-008": "pendiente_bloqueante",
    "TRM-SEC-009": "pendiente_bloqueante",
    "TRM-SEC-010": "pendiente_bloqueante",
}

LIMITACIONES_INICIALES = {
    "TRM-SEC-001": ("Task 4",),
    "TRM-SEC-002": ("Task 2", "Task 4"),
    "TRM-SEC-003": ("Task 3",),
    "TRM-SEC-004": ("Task 1", "Task 5", "Task 7"),
    "TRM-SEC-005": ("Task 4",),
    "TRM-SEC-006": ("Task 4",),
    "TRM-SEC-007": ("Task 4", "Plan 03c"),
    "TRM-SEC-008": ("Task 5",),
    "TRM-SEC-009": ("Task 6",),
    "TRM-SEC-010": ("Task 7",),
}

ESTADOS_PERMITIDOS = {
    "cubierto_por_prueba",
    "parcial",
    "no_aplica_justificado",
    "pendiente_bloqueante",
}

VERSIONES_LITERALES = (
    "OWASP Top 10 2025",
    "OWASP API Security Top 10 2023",
    "ASVS 5.0.0",
    "OWASP Agentic Skills Top 10 — revisión pública v1",
    "OWASP MCP Top 10 v0.1",
)

AFIRMACIONES_PROHIBIDAS = (
    "cumplimiento owasp",
    "certificado por owasp",
    "100% owasp",
)


def _leer_documento(ruta: Path) -> str:
    assert ruta.is_file(), f"No existe {ruta.relative_to(RAIZ)}"
    return ruta.read_text(encoding="utf-8")


def _extraer_filas_control(contenido: str) -> list[list[str]]:
    filas = []
    for linea in contenido.splitlines():
        celdas = [celda.strip() for celda in linea.strip().strip("|").split("|")]
        if celdas and re.fullmatch(r"TRM-SEC-\d{3}", celdas[0]):
            filas.append(celdas)
    return filas


def test_existen_modelo_y_matriz_de_seguridad() -> None:
    faltantes = [
        str(ruta.relative_to(RAIZ))
        for ruta in (RUTA_MODELO, RUTA_MATRIZ)
        if not ruta.is_file()
    ]

    assert not faltantes, f"Faltan documentos de seguridad: {', '.join(faltantes)}"


def test_modelo_fija_estructura_activos_actores_y_fronteras() -> None:
    contenido = _leer_documento(RUTA_MODELO)
    contenido_normalizado = contenido.casefold()

    posiciones = [contenido.index(encabezado) for encabezado in ENCABEZADOS_MODELO]
    assert posiciones == sorted(posiciones)
    assert all(contenido.count(encabezado) == 1 for encabezado in ENCABEZADOS_MODELO)

    for termino in ACTIVOS_OBLIGATORIOS + ACTORES_OBLIGATORIOS + FRONTERAS_OBLIGATORIAS:
        assert termino in contenido_normalizado, f"Falta documentar: {termino}"


def test_matriz_fija_controles_estados_y_evidencia_inicial() -> None:
    contenido = _leer_documento(RUTA_MATRIZ)
    filas = _extraer_filas_control(contenido)

    assert [fila[0] for fila in filas] == list(CONTROLES)
    for fila in filas:
        assert len(fila) == 6, f"{fila[0]} debe tener seis columnas"
        identificador, control, referencias, estado, evidencia, limitacion = fila
        assert control == CONTROLES[identificador]
        assert estado in ESTADOS_PERMITIDOS
        assert estado == ESTADOS_INICIALES[identificador]
        assert all(texto in referencias for texto in REFERENCIAS[identificador])
        assert re.search(r"`uv run --no-sync pytest [^`]+`", evidencia)
        assert all(texto in limitacion for texto in LIMITACIONES_INICIALES[identificador])


def test_cada_control_enlaza_fuentes_oficiales() -> None:
    contenido = _leer_documento(RUTA_MATRIZ)

    for fila in _extraer_filas_control(contenido):
        identificador, _, referencias, *_ = fila
        enlaces = re.findall(r"\[[^]]+\]\((https://[^)]+)\)", referencias)
        assert enlaces, f"{identificador} no enlaza una fuente oficial"
        assert all(
            enlace.startswith(
                (
                    "https://owasp.org/",
                    "https://github.com/OWASP/",
                    "https://www.w3.org/",
                )
            )
            for enlace in enlaces
        )


def test_matriz_declara_versiones_de_referencia_literales() -> None:
    contenido = _leer_documento(RUTA_MATRIZ)

    assert all(version in contenido for version in VERSIONES_LITERALES)


def test_documentos_no_declaran_certificacion_general() -> None:
    contenido = "\n".join((_leer_documento(RUTA_MODELO), _leer_documento(RUTA_MATRIZ)))
    contenido_normalizado = contenido.casefold()

    assert all(frase not in contenido_normalizado for frase in AFIRMACIONES_PROHIBIDAS)
