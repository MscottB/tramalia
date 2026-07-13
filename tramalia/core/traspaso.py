"""Build canonical handoffs and best-effort documentation projections."""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from contextlib import contextmanager, suppress
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


def _misma_identidad(ruta: Path, esperada: os.stat_result) -> bool:
    try:
        return os.path.samestat(ruta.stat(follow_symlinks=False), esperada)
    except (OSError, ValueError):
        return False


def _misma_identidad_relativa(
    descriptor_directorio: int,
    nombre: str,
    esperada: os.stat_result,
) -> bool:
    try:
        actual = os.stat(
            nombre,
            dir_fd=descriptor_directorio,
            follow_symlinks=False,
        )
        return os.path.samestat(actual, esperada)
    except (OSError, ValueError):
        return False


@contextmanager
def _proteger_directorio_publicacion(
    raiz: Path,
    padre: Path,
) -> Iterator[int | None]:
    """Keep publication anchored while a relative atomic rename is in flight."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        crear_archivo = kernel32.CreateFileW
        crear_archivo.argtypes = (
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        )
        crear_archivo.restype = wintypes.HANDLE
        cerrar_manejador = kernel32.CloseHandle
        cerrar_manejador.argtypes = (wintypes.HANDLE,)
        cerrar_manejador.restype = wintypes.BOOL
        compartir_lectura_escritura = 0x00000001 | 0x00000002
        abrir_existente = 3
        directorio_para_respaldo = 0x02000000
        manejador_invalido = ctypes.c_void_p(-1).value
        manejadores: list[int] = []
        try:
            # Excluir FILE_SHARE_DELETE impide renombrar cualquier ancestro protegido.
            for ruta in (raiz, padre.parent, padre):
                manejador = crear_archivo(
                    str(ruta),
                    0,
                    compartir_lectura_escritura,
                    None,
                    abrir_existente,
                    directorio_para_respaldo,
                    None,
                )
                if manejador == manejador_invalido:
                    raise OSError(ctypes.get_last_error(), "no se pudo proteger el directorio")
                manejadores.append(manejador)
            yield None
        finally:
            for manejador in reversed(manejadores):
                cerrar_manejador(manejador)
        return

    if (
        not hasattr(os, "O_DIRECTORY")
        or os.open not in os.supports_dir_fd
        or os.rename not in os.supports_dir_fd
    ):
        raise OSError("el sistema no soporta rename relativo a directorio")
    descriptor = os.open(padre, os.O_RDONLY | os.O_DIRECTORY)
    try:
        if not os.path.samestat(os.fstat(descriptor), padre.stat(follow_symlinks=False)):
            raise OSError("el directorio cambio antes de publicar")
        yield descriptor
    finally:
        os.close(descriptor)


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
    identidad_temporal: os.stat_result | None = None
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
        identidad_padre = padre.stat(follow_symlinks=False)

        destino_real = padre / destino.name
        temporal = padre / temporal.name
        enlace = Path(os.path.relpath(canonico, padre)).as_posix()
        relativo = canonico.relative_to(raiz_resuelta).as_posix()
        contenido = (
            "# 07 - Traspaso de agentes\n\n"
            f"- id_paquete: {paquete.id_paquete}\n"
            f"- paquete canonico: [{relativo}]({enlace})\n"
        ).encode()
        with _proteger_directorio_publicacion(
            raiz_resuelta,
            padre,
        ) as descriptor_padre:
            try:
                if descriptor_padre is None:
                    descriptor_temporal = os.open(
                        temporal,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                        0o600,
                    )
                else:
                    descriptor_temporal = os.open(
                        temporal.name,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                        0o600,
                        dir_fd=descriptor_padre,
                    )
                temporal_creado = True
                with os.fdopen(descriptor_temporal, "wb") as archivo:
                    identidad_temporal = os.fstat(archivo.fileno())
                    archivo.write(contenido)
                    archivo.flush()
                    os.fsync(archivo.fileno())

                temporal_estable = identidad_temporal is not None and (
                    _misma_identidad(temporal, identidad_temporal)
                    if descriptor_padre is None
                    else _misma_identidad_relativa(
                        descriptor_padre,
                        temporal.name,
                        identidad_temporal,
                    )
                )
                if (
                    padre.resolve(strict=True) != padre
                    or not _misma_identidad(padre, identidad_padre)
                    or not temporal_estable
                ):
                    raise ValueError("la proyeccion cambio de ubicacion")

                if descriptor_padre is None:
                    os.replace(temporal, destino_real)
                else:
                    os.replace(
                        temporal.name,
                        destino_real.name,
                        src_dir_fd=descriptor_padre,
                        dst_dir_fd=descriptor_padre,
                    )
                temporal_creado = False

                destino_estable = identidad_temporal is not None and (
                    _misma_identidad(destino_real, identidad_temporal)
                    if descriptor_padre is None
                    else _misma_identidad_relativa(
                        descriptor_padre,
                        destino_real.name,
                        identidad_temporal,
                    )
                )
                if (
                    padre.resolve(strict=True) != padre
                    or not _misma_identidad(padre, identidad_padre)
                    or not destino_estable
                ):
                    if destino_estable:
                        with suppress(OSError):
                            if descriptor_padre is None:
                                destino_real.unlink(missing_ok=True)
                            else:
                                os.unlink(destino_real.name, dir_fd=descriptor_padre)
                    raise ValueError("la proyeccion cambio de ubicacion")
            except (OSError, RuntimeError, ValueError):
                if temporal_creado and identidad_temporal is not None:
                    with suppress(OSError):
                        if descriptor_padre is None and _misma_identidad(
                            temporal,
                            identidad_temporal,
                        ):
                            temporal.unlink(missing_ok=True)
                        elif descriptor_padre is not None and _misma_identidad_relativa(
                            descriptor_padre,
                            temporal.name,
                            identidad_temporal,
                        ):
                            os.unlink(temporal.name, dir_fd=descriptor_padre)
                temporal_creado = False
                raise
    except (OSError, RuntimeError, ValueError):
        if (
            temporal_creado
            and identidad_temporal is not None
            and _misma_identidad(temporal, identidad_temporal)
        ):
            with suppress(OSError):
                temporal.unlink(missing_ok=True)
    return destino
