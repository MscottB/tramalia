"""Build canonical handoffs and best-effort documentation projections."""

from __future__ import annotations

import os
import uuid
from contextlib import suppress
from pathlib import Path

from tramalia.core.modelos import PaqueteEvidencia, ResultadoCierre


def _linea_segura(valor: str, predeterminado: str) -> str:
    texto = " ".join(valor.split()).strip()
    return texto or predeterminado


def construir_traspaso(
    resultado: ResultadoCierre,
    agente: str,
    revisor: str,
) -> bytes:
    """Render an already-computed closure result as the canonical handoff.

    Args:
        resultado: Definitive closure result; policy is never recalculated here.
        agente: Agent that performed the work.
        revisor: Human or agent responsible for the review.

    Returns:
        Deterministic UTF-8 Markdown with a final newline.
    """
    bloqueos = (
        ", ".join(_linea_segura(bloqueo, "control desconocido") for bloqueo in resultado.bloqueos)
        or "ninguno"
    )
    excepciones = (
        ", ".join(
            f"{_linea_segura(excepcion.control_afectado, 'control desconocido')} "
            f"({_linea_segura(excepcion.referencia, 'sin referencia')})"
            for excepcion in resultado.excepciones
        )
        or "ninguna"
    )
    lineas = (
        "# Traspaso canonico",
        "",
        f"- id_paquete: {resultado.id_paquete or 'no publicado'}",
        f"- id_tarea: {resultado.id_tarea}",
        f"- resultado: {resultado.estado.value}",
        f"- agente: {_linea_segura(agente, 'no declarado')}",
        f"- revisor: {_linea_segura(revisor, 'no declarado')}",
        f"- bloqueos: {bloqueos}",
        f"- excepciones: {excepciones}",
    )
    return ("\n".join(lineas) + "\n").encode()


def _ruta_fisica_local(ruta: Path, raiz: Path) -> bool:
    try:
        resuelta = ruta.resolve(strict=ruta.exists() or ruta.is_symlink())
        return resuelta.is_relative_to(raiz.resolve(strict=True))
    except (OSError, RuntimeError, ValueError):
        return False


def proyectar_traspaso(raiz: Path, paquete: PaqueteEvidencia) -> Path:
    """Atomically project the canonical handoff into project documentation.

    Projection is deliberately non-authoritative and best-effort. Expected
    filesystem or path failures leave the immutable package untouched.

    Args:
        raiz: Project root that will receive the documentation projection.
        paquete: Published package that owns the canonical ``traspaso.md``.

    Returns:
        The expected projection path, whether or not projection succeeded.
    """
    destino = raiz / "docs" / "ai" / "07-traspaso-agentes.md"
    temporal = destino.with_name(f".{destino.name}.tmp-{uuid.uuid4().hex}")
    temporal_creado = False
    try:
        raiz_resuelta = raiz.resolve(strict=True)
        base_evidencia = raiz_resuelta / ".tramalia" / "evidencia"
        if paquete.ruta.is_symlink():
            return destino
        ruta_paquete = paquete.ruta.resolve(strict=True)
        canonico_declarado = ruta_paquete / "traspaso.md"
        if canonico_declarado.is_symlink():
            return destino
        canonico = canonico_declarado.resolve(strict=True)
        if (
            not ruta_paquete.is_relative_to(base_evidencia)
            or canonico.parent != ruta_paquete
            or not canonico.is_file()
        ):
            return destino

        docs = raiz_resuelta / "docs"
        if (docs.exists() or docs.is_symlink()) and docs.resolve(strict=True) != docs:
            return destino
        padre = docs / "ai"
        if (padre.exists() or padre.is_symlink()) and padre.resolve(strict=True) != padre:
            return destino
        padre.mkdir(parents=True, exist_ok=True)
        if padre.resolve(strict=True) != padre or not _ruta_fisica_local(padre, raiz_resuelta):
            return destino

        destino_real = padre / destino.name
        temporal = padre / temporal.name
        enlace = Path(os.path.relpath(canonico, padre)).as_posix()
        relativo = canonico.relative_to(raiz_resuelta).as_posix()
        contenido = (
            "# 07 - Traspaso de agentes\n\n"
            f"- id_paquete: {paquete.id_paquete}\n"
            f"- paquete canonico: [{relativo}]({enlace})\n"
        ).encode()
        with temporal.open("xb") as archivo:
            temporal_creado = True
            archivo.write(contenido)
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(temporal, destino_real)
        temporal_creado = False
    except (OSError, RuntimeError, ValueError):
        if temporal_creado:
            with suppress(OSError):
                temporal.unlink(missing_ok=True)
    return destino
