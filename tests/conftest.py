import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tramalia import __version__
from tramalia.core.evidencia import crear_id_paquete
from tramalia.core.modelos import (
    EjecucionPuertas,
    EstadoGit,
    MetadatosPaqueteEvidencia,
    ValorEstadoCierre,
    ValorEstadoPuertas,
)


@pytest.fixture
def raiz_proyecto() -> Path:
    """Return the repository root used by contract and release tests."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def fabrica_metadatos_v1():
    def fabricar() -> MetadatosPaqueteEvidencia:
        ahora = datetime.now(UTC)
        return MetadatosPaqueteEvidencia(
            version_esquema=1,
            id_paquete=crear_id_paquete(ahora),
            id_tarea="TASK-1",
            operacion="cierre",
            inicio_utc=ahora,
            fin_utc=ahora,
            version_tramalia=__version__,
            version_python="3.11.9",
            sistema_operativo="test",
            cadena_herramientas={"mise": "test"},
            git=EstadoGit(None, None, None, None),
            ejecucion=EjecucionPuertas(ValorEstadoPuertas.SIN_CONFIGURAR),
            estado_cierre=ValorEstadoCierre.BLOQUEADO,
            agente="codex",
            modelo="test",
            metricas={},
            umbrales={},
            errores_validacion=("puertas",),
            excepciones=(),
            vinculo_traspaso="traspaso.md",
        )

    return fabricar


@pytest.fixture
def metadatos_v1(fabrica_metadatos_v1) -> MetadatosPaqueteEvidencia:
    return fabrica_metadatos_v1()


@pytest.fixture
def paquete_v1(tmp_path: Path, metadatos_v1: MetadatosPaqueteEvidencia):
    # La importacion diferida permite que Task 5 defina el contrato antes del writer.
    from tramalia.core.evidencia import publicar_paquete

    traspaso = (
        f"id_paquete: {metadatos_v1.id_paquete}\n"
        f"id_tarea: {metadatos_v1.id_tarea}\n"
        f"resultado: {metadatos_v1.estado_cierre.value}\n"
    ).encode()
    return publicar_paquete(tmp_path, metadatos_v1, {"traspaso.md": traspaso})


@pytest.fixture
def proyecto_listo(tmp_path: Path) -> Path:
    directorio = tmp_path / ".tramalia"
    directorio.mkdir()
    (directorio / "config.json").write_text(
        json.dumps({"projectName": "demo"}),
        encoding="utf-8",
    )
    (directorio / "version").write_text(f"{__version__}\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(
        "<!-- tramalia:gobierno inicio -->\ntramalia close\n<!-- tramalia:gobierno fin -->\n",
        encoding="utf-8",
    )
    (tmp_path / "mise.toml").write_text(
        "[tasks.test]\nrun = 'pytest'\n",
        encoding="utf-8",
    )
    return tmp_path
