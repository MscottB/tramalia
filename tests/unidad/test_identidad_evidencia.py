from __future__ import annotations

from datetime import UTC, datetime, timedelta, tzinfo

import pytest

from tramalia.core.errores import (
    ErrorIdentificadorInseguro,
    ErrorPersistenciaEvidencia,
)
from tramalia.core.evidencia import crear_id_paquete, validar_id_tarea


@pytest.mark.parametrize(
    "id_tarea",
    [
        "",
        "../x",
        "a/b",
        "a\\b",
        "a..b",
        ".",
        "CON",
        "con.txt",
        "PRN.log",
        "COM1",
        "lpt9.md",
        "A\nB",
        "x" * 65,
        "tarea-ñ",
        7,
        None,
    ],
)
def test_rechaza_id_inseguro_en_todas_las_plataformas(id_tarea: object) -> None:
    with pytest.raises(ErrorIdentificadorInseguro):
        validar_id_tarea(id_tarea)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "id_tarea",
    ["TASK-1", "tarea_2", "a.b-c_d", "A" * 64],
)
def test_acepta_id_ascii_portable(id_tarea: str) -> None:
    assert validar_id_tarea(id_tarea) == id_tarea


def test_dos_ids_en_el_mismo_microsegundo_son_distintos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ahora = datetime(2026, 7, 12, 20, 30, 1, 123456, tzinfo=UTC)
    sufijos = iter(["a1b2c3d4", "e5f6a7b8"])
    monkeypatch.setattr(
        "tramalia.core.evidencia.secrets.token_hex",
        lambda _: next(sufijos),
    )

    primero = crear_id_paquete(ahora)
    segundo = crear_id_paquete(ahora)

    assert primero == "20260712T203001.123456Z-a1b2c3d4"
    assert segundo == "20260712T203001.123456Z-e5f6a7b8"
    assert primero != segundo


class _ZonaSinDesfase(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


@pytest.mark.parametrize(
    "ahora",
    [datetime(2026, 7, 12), datetime(2026, 7, 12, tzinfo=_ZonaSinDesfase())],
)
def test_id_de_paquete_rechaza_instante_sin_desfase(ahora: datetime) -> None:
    with pytest.raises(ErrorPersistenciaEvidencia):
        crear_id_paquete(ahora)


def test_id_de_paquete_normaliza_desfase_no_utc(monkeypatch: pytest.MonkeyPatch) -> None:
    from datetime import timezone

    monkeypatch.setattr("tramalia.core.evidencia.secrets.token_hex", lambda _: "1234abcd")
    local = datetime(
        2026,
        7,
        12,
        17,
        30,
        1,
        123456,
        tzinfo=timezone(-timedelta(hours=3)),
    )

    assert crear_id_paquete(local) == "20260712T203001.123456Z-1234abcd"
